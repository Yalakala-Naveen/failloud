"""Command-line interface.

    failloud check output.json [--format text|md|json] [--out REPORT]
                               [--require output.url,output.body]
                               [--schema schema.json]
                               [--max-state-age-hours 24]
                               [--max-segment-gap-seconds 2.0]
                               [--only FL001,FL004]
    failloud checks            # list the checks and what they catch

Exit codes: ``0`` the output passed, ``1`` verification failed (the agent
output, not the tool), ``2`` the tool itself could not run (bad input,
bad arguments).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .checks import MODULES
from .engine import run_checks
from .models import CheckConfig
from .report import render_json, render_markdown, render_text


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
    return 0 if result.passed else 1


def _cmd_checks(_args: argparse.Namespace) -> int:
    for module in MODULES:
        print(f"{module.CHECK_ID}  {module.NAME}")
        print(f"      {module.DESCRIPTION}")
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
    check.set_defaults(func=_cmd_check)

    checks = sub.add_parser("checks", help="List the checks and what they catch.")
    checks.set_defaults(func=_cmd_checks)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
