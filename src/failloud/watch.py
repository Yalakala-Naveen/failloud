"""Watch mode: re-verify agent outputs as they change.

``failloud check`` verifies one document once. Real agent pipelines do not
work that way — outputs land in a directory over time, a runner overwrites
the same file as it retries, and an orchestrator needs the verdict for the
*latest* version, not a snapshot someone remembered to check by hand.

Watch mode closes that gap with polling, stdlib only:

- Point it at a single JSON file or at a directory of ``*.json`` outputs.
- It checks every target on the first poll, then re-checks a target only
  when its content actually changes (SHA-256 of the bytes, so a touch that
  changes nothing does not produce a duplicate verdict).
- New files appearing in a watched directory are picked up on the next
  poll; deleted files are forgotten silently.
- With a receipt file, every successful check is sealed into the
  hash-chained receipt chain automatically — the watcher builds the audit
  trail as it goes, with no extra step to forget.
- A file that is mid-write or temporarily invalid JSON produces an error
  event and is retried on the next poll; one bad file never kills the
  watcher or hides the verdicts for the others.

Polling, not a filesystem-events dependency, is deliberate: the core stays
zero-dependency, the behaviour is identical on Linux, macOS, and Windows,
and a 1-second default interval is far faster than the agent runs it
watches. Callers that need deterministic behaviour (tests, CI) drive
:meth:`Watcher.poll_once` directly or run :func:`watch` with
``once=True`` / ``max_polls``.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .engine import run_checks
from .models import CheckConfig, CheckResult
from .receipts import Receipt, seal_to_chain


def file_signature(path: str | Path) -> str | None:
    """SHA-256 hex digest of a file's bytes, or ``None`` if unreadable.

    Content, not mtime, decides "changed": mtime granularity and editors
    that rewrite identical bytes would otherwise produce phantom
    re-checks and duplicate receipts for an unchanged verdict.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def discover_targets(
    target: str | Path,
    pattern: str = "*.json",
    recursive: bool = False,
) -> list[Path]:
    """Resolve a watch target to the concrete files it covers right now.

    A file target covers exactly itself (``pattern`` is ignored). A
    directory target covers its ``pattern`` matches, sorted by path so
    poll order — and therefore receipt order — is deterministic. A
    missing target covers nothing; callers distinguish "missing" from
    "empty directory" by checking existence themselves (the CLI does).
    """
    root = Path(target)
    if root.is_file():
        return [root]
    if root.is_dir():
        matches = root.rglob(pattern) if recursive else root.glob(pattern)
        return sorted(p for p in matches if p.is_file())
    return []


@dataclass
class WatchEvent:
    """One poll outcome for one file.

    Exactly one of ``result`` / ``error`` is set: ``result`` when the file
    was read and verified (pass or fail — a FAIL verdict is a result, not
    a watcher error), ``error`` when the file could not be read or parsed
    at all. ``receipt`` is set only when the event was also sealed to a
    receipt chain.
    """

    path: Path
    result: CheckResult | None = None
    error: str | None = None
    receipt: Receipt | None = None

    @property
    def passed(self) -> bool:
        return self.result is not None and self.result.passed

    @property
    def failed(self) -> bool:
        return self.result is not None and not self.result.passed


@dataclass
class WatchSummary:
    """Aggregate counts for one :func:`watch` run."""

    checks: int = 0  # files successfully verified
    failures: int = 0  # verified files whose verdict was FAIL
    errors: int = 0  # files that could not be read/parsed
    receipts: int = 0  # receipts sealed during the run
    events: list[WatchEvent] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when nothing failed and nothing errored."""
        return self.failures == 0 and self.errors == 0


class Watcher:
    """Polling watcher over one file or one directory of outputs.

    State is just the last-seen content signature per path. Each
    :meth:`poll_once` re-discovers the targets (so arrivals and removals
    in a directory are handled), checks the new and changed ones, seals
    receipts when configured, and returns the events in sorted path
    order. The watcher itself never sleeps and never loops — pacing is
    the caller's job (see :func:`watch`).
    """

    def __init__(
        self,
        target: str | Path,
        config: CheckConfig | None = None,
        receipt_out: str | Path | None = None,
        pattern: str = "*.json",
        recursive: bool = False,
    ) -> None:
        self.target = Path(target)
        self.config = config or CheckConfig()
        self.receipt_out = Path(receipt_out) if receipt_out is not None else None
        self.pattern = pattern
        self.recursive = recursive
        self._signatures: dict[Path, str | None] = {}

    def poll_once(self) -> list[WatchEvent]:
        """Check every new or changed target once. Returns the events."""
        current = discover_targets(self.target, self.pattern, self.recursive)
        # Forget deleted files so a later file reusing the path is new.
        live = set(current)
        for known in list(self._signatures):
            if known not in live:
                del self._signatures[known]

        events: list[WatchEvent] = []
        for path in current:
            signature = file_signature(path)
            if path in self._signatures and self._signatures[path] == signature:
                continue
            # Record the signature even on a read error: an unchanged
            # broken file should not re-report every poll. It re-checks
            # as soon as its bytes change — which is exactly when a
            # writer finishes fixing or finishing it.
            self._signatures[path] = signature
            events.append(self._check_one(path))
        return events

    def _check_one(self, path: Path) -> WatchEvent:
        try:
            doc: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return WatchEvent(path=path, error=str(exc))
        try:
            result = run_checks(doc, self.config)
        except ValueError as exc:  # e.g. an unknown --only check id
            return WatchEvent(path=path, error=str(exc))
        receipt: Receipt | None = None
        if self.receipt_out is not None:
            try:
                receipt = seal_to_chain(
                    self.receipt_out, result, source=str(path)
                )
            except (OSError, ValueError, KeyError) as exc:
                return WatchEvent(path=path, result=result, error=f"receipt: {exc}")
        return WatchEvent(path=path, result=result, receipt=receipt)


def watch(
    target: str | Path,
    config: CheckConfig | None = None,
    receipt_out: str | Path | None = None,
    interval: float = 1.0,
    once: bool = False,
    max_polls: int | None = None,
    pattern: str = "*.json",
    recursive: bool = False,
    on_event: Callable[[WatchEvent], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> WatchSummary:
    """Watch *target*, verifying outputs as they change.

    With ``once=True`` (or ``max_polls=1``) this is a single sweep — the
    directory-scan mode a CI step wants. Otherwise it polls every
    ``interval`` seconds until ``max_polls`` is reached or the caller
    interrupts it (``KeyboardInterrupt`` propagates; the CLI turns it
    into a clean exit). ``sleep`` is injectable so tests never wait on a
    real clock. Every event is passed to ``on_event`` as it happens and
    also collected into the returned summary.
    """
    watcher = Watcher(
        target,
        config=config,
        receipt_out=receipt_out,
        pattern=pattern,
        recursive=recursive,
    )
    summary = WatchSummary()
    polls = 0
    while True:
        for event in watcher.poll_once():
            summary.events.append(event)
            if event.result is not None:
                summary.checks += 1
                if not event.result.passed:
                    summary.failures += 1
            if event.error is not None:
                summary.errors += 1
            if event.receipt is not None:
                summary.receipts += 1
            if on_event is not None:
                on_event(event)
        polls += 1
        if once or (max_polls is not None and polls >= max_polls):
            return summary
        sleep(interval)
