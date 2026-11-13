"""Command-line interface.

    failloud check output.json [--format text|md|json] [--out REPORT]
                               [--require output.url,output.body]
                               [--schema schema.json]
                               [--max-state-age-hours 24]
                               [--max-segment-gap-seconds 2.0]
                               [--only FL001,FL004]
                               [--receipt-out receipts.jsonl]
    failloud watch PATH        # re-verify a file or a directory of
                               # outputs as they change; --once sweeps
                               # once, --receipt-out seals every verdict
    failloud checks            # list the checks and what they catch
    failloud verify-receipts receipts.jsonl
                               # verify a hash-chained receipt file

Exit codes: ``0`` the output passed, ``1`` verification failed (the agent
output, not the tool), ``2`` the tool itself could not run (bad input,
bad arguments). ``verify-receipts`` uses the same contract: ``0`` the
chain verifies, ``1`` it does not, ``2`` the file could not be read.
``watch --once`` follows the check contract over the whole sweep: ``0``
every file passed, ``1`` any file failed or errored, ``2`` the target
does not exist. Continuous ``watch`` runs until Ctrl-C and exits ``0``.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pathlib import Path

from .checks import MODULES
from .engine import run_checks
from .models import CheckConfig
from .receipts import read_chain, seal_to_chain, verify_chain
from .report import render_json, render_markdown, render_text
from .watch import WatchEvent, watch as run_watch


def _load_json(source: str) -> Any:
    if source == "-":
        raw = sys.stdin.read()
    else:
        with open(source, encoding="utf-8") as handle:
            raw = handle.read()
    return json.loads(raw)


def _build_config(args: argparse.Namespace) -> CheckConfig:
    required: tuple[str, ...] = ()
    if args.require:
        required = tuple(p.strip() for p in args.require.split(",") if p.strip())
    schema = None
    if args.schema:
        with open(args.schema, encoding="utf-8") as handle:
            schema = json.load(handle)
    only = None
    if args.only:
        only = tuple(c.strip().upper() for c in args.only.split(",") if c.strip())
    return CheckConfig(
        max_state_age_hours=args.max_state_age_hours,
        max_segment_gap_seconds=args.max_segment_gap_seconds,
        required_paths=required,
        schema=schema,
        only=only,
    )


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        doc = _load_json(args.file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failloud: cannot read input: {exc}", file=sys.stderr)
        return 2
    try:
        config = _build_config(args)
        result = run_checks(doc, config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"failloud: {exc}", file=sys.stderr)
        return 2

    renderers = {"text": render_text, "md": render_markdown, "json": render_json}
    rendered = renderers[args.format](result, source=args.file)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        print(
            f"Verdict: {result.verdict} "
            f"({len(result.errors)} error(s), {len(result.warnings)} warning(s)) "
            f"— report written to {args.out}"
        )
    else:
        sys.stdout.write(rendered)
    if args.receipt_out:
        try:
            receipt = seal_to_chain(args.receipt_out, result, source=args.file)
        except (OSError, ValueError, KeyError) as exc:
            print(f"failloud: cannot write receipt: {exc}", file=sys.stderr)
            return 2
        # Stderr, so a `--format json` report on stdout stays machine-clean.
        print(
            f"Receipt {receipt.receipt_hash[:16]}… sealed to {args.receipt_out}",
            file=sys.stderr,
        )
    return 0 if result.passed else 1


def _cmd_watch(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"failloud: watch target does not exist: {args.path}", file=sys.stderr)
        return 2
    try:
        config = _build_config(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"failloud: {exc}", file=sys.stderr)
        return 2

    renderers = {"text": render_text, "md": render_markdown, "json": render_json}

    def _emit(event: WatchEvent) -> None:
        if event.error is not None and event.result is None:
            print(f"failloud watch: {event.path}: error: {event.error}", file=sys.stderr)
            return
        assert event.result is not None
        sys.stdout.write(renderers[args.format](event.result, source=str(event.path)))
        sys.stdout.flush()  # keep report ahead of the stderr receipt note in pipes
        if event.receipt is not None:
            # Stderr, so a `--format json` stream on stdout stays parseable
            # per-file only in --once sweeps; the receipt note never
            # pollutes the report itself.
            print(
                f"Receipt {event.receipt.receipt_hash[:16]}… sealed for {event.path}",
                file=sys.stderr,
            )
        if event.error is not None:  # verdict rendered, receipt failed
            print(f"failloud watch: {event.path}: {event.error}", file=sys.stderr)
        sys.stdout.flush()

    if not args.once:
        print(
            f"Watching {args.path} every {args.interval:g}s — Ctrl-C to stop.",
            file=sys.stderr,
        )
    try:
        summary = run_watch(
            target,
            config=config,
            receipt_out=args.receipt_out,
            interval=args.interval,
            once=args.once,
            pattern=args.pattern,
            recursive=args.recursive,
            on_event=_emit,
        )
    except KeyboardInterrupt:
        print("\nWatch stopped.", file=sys.stderr)
        return 0
    if args.once:
        print(
            f"Watch sweep: {summary.checks} checked, "
            f"{summary.failures} failed, {summary.errors} error(s), "
            f"{summary.receipts} receipt(s) sealed.",
            file=sys.stderr,
        )
        return 0 if summary.ok else 1
    return 0


def _cmd_checks(_args: argparse.Namespace) -> int:
    for module in MODULES:
        print(f"{module.CHECK_ID}  {module.NAME}")
        print(f"      {module.DESCRIPTION}")
    return 0


def _cmd_verify_receipts(args: argparse.Namespace) -> int:
    try:
        chain = read_chain(args.file)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"failloud: cannot read receipts: {exc}", file=sys.stderr)
        return 2
    problems = verify_chain(chain)
    if problems:
        print(f"RECEIPT CHAIN INVALID — {len(problems)} problem(s) in {args.file}:")
        for problem in problems:
            print(f"  ✗ {problem}")
        return 1
    print(f"Receipt chain OK — {len(chain)} receipt(s) verified in {args.file}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="failloud",
        description=(
            "Verify an LLM agent's output for the silent failures agents "
            "ship as 'done': placeholders, unbacked claims, stale state, "
            "inflated counts, missing components."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Verify one agent output JSON document.")
    check.add_argument("file", help="Path to the output JSON, or '-' for stdin.")
    check.add_argument(
        "--format",
        choices=("text", "md", "json"),
        default="text",
        help="Report format (default: text).",
    )
    check.add_argument("--out", help="Write the report to this file instead of stdout.")
    check.add_argument(
        "--require",
        help="Comma-separated dotted paths that must exist and be non-empty, "
        "e.g. 'output.url,output.body'.",
    )
    check.add_argument("--schema", help="Path to a JSON Schema file (subset supported).")
    check.add_argument(
        "--max-state-age-hours",
        type=float,
        default=24.0,
        help="State older than this is stale (default: 24).",
    )
    check.add_argument(
        "--max-segment-gap-seconds",
        type=float,
        default=2.0,
        help="Segment gap longer than this is a dead stretch (default: 2.0).",
    )
    check.add_argument("--only", help="Comma-separated check ids to run, e.g. 'FL001,FL004'.")
    check.add_argument(
        "--receipt-out",
        help="Append a hash-chained verification receipt for this run to this "
        "JSONL file (created if needed), so the verdict can be re-verified "
        "later with 'failloud verify-receipts'.",
    )
    check.set_defaults(func=_cmd_check)

    watch_parser = sub.add_parser(
        "watch",
        help="Re-verify a file or a directory of outputs as they change.",
    )
    watch_parser.add_argument(
        "path", help="A JSON file, or a directory of JSON outputs to watch."
    )
    watch_parser.add_argument(
        "--once",
        action="store_true",
        help="Sweep once and exit (0 all passed, 1 any failed/errored, "
        "2 target missing) instead of watching continuously.",
    )
    watch_parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Poll interval in seconds for continuous watch (default: 1.0).",
    )
    watch_parser.add_argument(
        "--pattern",
        default="*.json",
        help="Glob for directory targets (default: '*.json').",
    )
    watch_parser.add_argument(
        "--recursive",
        action="store_true",
        help="For directory targets, also watch subdirectories.",
    )
    watch_parser.add_argument(
        "--format",
        choices=("text", "md", "json"),
        default="text",
        help="Report format per check (default: text).",
    )
    watch_parser.add_argument(
        "--require",
        help="Comma-separated dotted paths that must exist and be non-empty.",
    )
    watch_parser.add_argument("--schema", help="Path to a JSON Schema file (subset supported).")
    watch_parser.add_argument(
        "--max-state-age-hours",
        type=float,
        default=24.0,
        help="State older than this is stale (default: 24).",
    )
    watch_parser.add_argument(
        "--max-segment-gap-seconds",
        type=float,
        default=2.0,
        help="Segment gap longer than this is a dead stretch (default: 2.0).",
    )
    watch_parser.add_argument(
        "--only", help="Comma-separated check ids to run, e.g. 'FL001,FL004'."
    )
    watch_parser.add_argument(
        "--receipt-out",
        help="Append a hash-chained verification receipt for every check to "
        "this JSONL file, verifiable with 'failloud verify-receipts'.",
    )
    watch_parser.set_defaults(func=_cmd_watch)

    checks = sub.add_parser("checks", help="List the checks and what they catch.")
    checks.set_defaults(func=_cmd_checks)

    verify = sub.add_parser(
        "verify-receipts",
        help="Verify a receipt chain file written by --receipt-out.",
    )
    verify.add_argument("file", help="Path to the receipts JSONL file.")
    verify.set_defaults(func=_cmd_verify_receipts)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
