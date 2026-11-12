"""Hash-chained verification receipts.

A failure report says what FailLoud found. A *receipt* proves it: a small
JSON record of one verification run — the full result, the verdict, and two
SHA-256 hashes:

- ``result_hash`` — a hash of the canonical result payload and its source.
  Change one character of any finding and this hash no longer matches.
- ``receipt_hash`` — a hash of every other receipt field, including
  ``prev_hash``, the previous receipt's ``receipt_hash``.

Linking each receipt to the previous one makes a chain (one JSON object per
line in a ``.jsonl`` file). Rewriting history then requires rewriting every
later receipt too — and anyone holding an earlier ``receipt_hash`` can prove
the rewrite happened. That is the audit trail an orchestrator needs before it
lets one agent's "done" become the next agent's input: not "trust me, it was
checked", but a chain a third party can re-verify offline, with the stdlib
only.

Receipts are evidence about a *verification run*, not about the work itself:
a receipt proves FailLoud produced this verdict for this result at this
time, in this order. It does not prove the underlying claims in the checked
document were true — that distinction is the whole point of the tool.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import CheckResult

#: Receipt format version. Bump only on a breaking field change; verifiers
#: reject versions they do not understand instead of guessing.
RECEIPT_VERSION = 1

_HASH_HEX_LEN = 64  # SHA-256 hex digest length


def _canonical(payload: Any) -> bytes:
    """Canonical bytes for hashing: sorted keys, compact separators, UTF-8.

    Two runs over equal payloads must hash identically on any machine, so
    the encoding leaves nothing to locale, dict order, or float formatting
    choices made elsewhere.
    """
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _tool_version() -> str:
    # Lazy import: failloud/__init__ imports this module's public API.
    from . import __version__

    return __version__


def result_hash_for(result_payload: dict[str, Any], source: str) -> str:
    """Hash binding a result payload to the source it was produced from."""
    return _sha256({"result": result_payload, "source": source})


@dataclass
class Receipt:
    """One verification run, sealed into a hash chain.

    ``result`` is the full :meth:`CheckResult.to_dict` payload, embedded so
    a verifier can recompute ``result_hash`` without the original document.
    The verdict fields are denormalized copies of the result's own fields —
    convenient to scan, and cross-checked by :func:`verify_receipt`.
    """

    source: str
    result: dict[str, Any]
    created_at: str  # ISO-8601 UTC, e.g. "2026-11-12T14:05:00Z"
    verdict: str
    passed: bool
    error_count: int
    warning_count: int
    result_hash: str
    prev_hash: str | None
    receipt_hash: str
    receipt_version: int = RECEIPT_VERSION
    tool: str = "failloud"
    tool_version: str = field(default_factory=_tool_version)

    def unsigned_dict(self) -> dict[str, Any]:
        """Every field except ``receipt_hash`` — the hash's input."""
        payload = self.to_dict()
        del payload["receipt_hash"]
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_version": self.receipt_version,
            "tool": self.tool,
            "tool_version": self.tool_version,
            "created_at": self.created_at,
            "source": self.source,
            "verdict": self.verdict,
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "result": self.result,
            "result_hash": self.result_hash,
            "prev_hash": self.prev_hash,
            "receipt_hash": self.receipt_hash,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Receipt":
        return cls(
            receipt_version=payload["receipt_version"],
            tool=payload["tool"],
            tool_version=payload["tool_version"],
            created_at=payload["created_at"],
            source=payload["source"],
            verdict=payload["verdict"],
            passed=payload["passed"],
            error_count=payload["error_count"],
            warning_count=payload["warning_count"],
            result=payload["result"],
            result_hash=payload["result_hash"],
            prev_hash=payload["prev_hash"],
            receipt_hash=payload["receipt_hash"],
        )


def compute_receipt_hash(receipt: Receipt) -> str:
    """Recompute a receipt's seal from its unsigned fields."""
    return _sha256(receipt.unsigned_dict())


def create_receipt(
    result: CheckResult,
    source: str = "<document>",
    prev_hash: str | None = None,
    created_at: datetime | None = None,
) -> Receipt:
    """Seal *result* into a receipt, chained after *prev_hash*.

    ``created_at`` exists so tests and replays are deterministic; production
    callers leave it ``None`` and get the wall clock.
    """
    moment = created_at or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    payload = result.to_dict()
    receipt = Receipt(
        source=source,
        result=payload,
        created_at=moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        verdict=result.verdict,
        passed=result.passed,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
        result_hash=result_hash_for(payload, source),
        prev_hash=prev_hash,
        receipt_hash="",  # sealed below, once every other field is final
    )
    receipt.receipt_hash = compute_receipt_hash(receipt)
    return receipt


def verify_receipt(receipt: Receipt | dict[str, Any]) -> list[str]:
    """Check one receipt's internal consistency.

    Returns a list of problems; an empty list means the receipt is intact —
    its embedded result hashes to ``result_hash``, its denormalized verdict
    fields agree with that result, and every field seals to
    ``receipt_hash``. Linkage to neighbours is :func:`verify_chain`'s job.
    """
    if isinstance(receipt, dict):
        try:
            receipt = Receipt.from_dict(receipt)
        except (KeyError, TypeError) as exc:
            return [f"receipt is missing or mistyping a required field: {exc}"]
    problems: list[str] = []
    if receipt.receipt_version != RECEIPT_VERSION:
        problems.append(
            f"unsupported receipt_version {receipt.receipt_version!r} "
            f"(this FailLoud verifies version {RECEIPT_VERSION})"
        )
    if len(receipt.receipt_hash) != _HASH_HEX_LEN or len(receipt.result_hash) != _HASH_HEX_LEN:
        problems.append("a hash field is not a SHA-256 hex digest")
        return problems  # further comparisons would only repeat this
    expected_result_hash = result_hash_for(receipt.result, receipt.source)
    if expected_result_hash != receipt.result_hash:
        problems.append(
            "result_hash mismatch — the embedded result or source was "
            "altered after the receipt was sealed"
        )
    result = receipt.result
    for field_name, embedded_key in (
        ("verdict", "verdict"),
        ("passed", "passed"),
        ("error_count", "error_count"),
        ("warning_count", "warning_count"),
    ):
        if result.get(embedded_key) != getattr(receipt, field_name):
            problems.append(
                f"{field_name} disagrees with the embedded result "
                f"({getattr(receipt, field_name)!r} != {result.get(embedded_key)!r})"
            )
    if compute_receipt_hash(receipt) != receipt.receipt_hash:
        problems.append(
            "receipt_hash mismatch — a receipt field was altered after sealing"
        )
    return problems


def verify_chain(receipts: Iterable[Receipt | dict[str, Any]]) -> list[str]:
    """Verify a whole chain: every receipt intact, every link in order.

    The first receipt must start the chain (``prev_hash`` is ``None``) and
    each later receipt must name its predecessor's ``receipt_hash``.
    Dropping, reordering, or editing any receipt breaks a check here.
    Returns a list of problems; empty means the chain verifies.
    """
    chain = list(receipts)
    problems: list[str] = []
    if not chain:
        return ["chain is empty — nothing to verify"]
    previous_hash: str | None = None
    for index, item in enumerate(chain):
        label = f"receipt {index}"
        receipt = item
        if isinstance(item, dict):
            try:
                receipt = Receipt.from_dict(item)
            except (KeyError, TypeError) as exc:
                problems.append(f"{label}: unreadable receipt: {exc}")
                previous_hash = None
                continue
        for problem in verify_receipt(receipt):
            problems.append(f"{label}: {problem}")
        if receipt.prev_hash != previous_hash:
            if index == 0:
                problems.append(
                    f"{label}: first receipt must start the chain "
                    f"(prev_hash is {receipt.prev_hash!r}, expected None)"
                )
            else:
                problems.append(
                    f"{label}: prev_hash does not match receipt {index - 1}'s "
                    "receipt_hash — a receipt was dropped, reordered, or replaced"
                )
        previous_hash = receipt.receipt_hash
    return problems


def read_chain(path: str | Path) -> list[Receipt]:
    """Read a receipt chain file.

    The canonical format is JSON Lines — one receipt object per line, in
    chain order. A file holding a single pretty-printed receipt object is
    also accepted, as a chain of one.
    """
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        single = json.loads(text)
    except json.JSONDecodeError:
        single = None
    if isinstance(single, dict) and "receipt_hash" in single:
        return [Receipt.from_dict(single)]
    receipts = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            receipts.append(Receipt.from_dict(json.loads(line)))
    return receipts


def last_hash(path: str | Path) -> str | None:
    """The ``receipt_hash`` a new receipt at *path* should chain after."""
    chain_path = Path(path)
    if not chain_path.exists():
        return None
    chain = read_chain(chain_path)
    return chain[-1].receipt_hash if chain else None


def append_receipt(path: str | Path, receipt: Receipt) -> None:
    """Append *receipt* to the chain file at *path* as one JSON line.

    The caller is responsible for having created the receipt with
    ``prev_hash=last_hash(path)`` — see :func:`seal_to_chain`, which does
    both halves together.
    """
    line = json.dumps(receipt.to_dict(), ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)


def seal_to_chain(
    path: str | Path,
    result: CheckResult,
    source: str = "<document>",
    created_at: datetime | None = None,
) -> Receipt:
    """Create a receipt for *result* chained onto the file at *path*.

    Reads the current tail, seals the new receipt after it, appends one
    line, and returns the receipt. This is the one-call path the CLI uses.
    """
    receipt = create_receipt(
        result, source=source, prev_hash=last_hash(path), created_at=created_at
    )
    append_receipt(path, receipt)
    return receipt
