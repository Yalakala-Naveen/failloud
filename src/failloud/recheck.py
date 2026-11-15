"""Second-pass verification: provisional verdicts, checked against reality.

The five checks verify an output against *itself* — its claims against its
own evidence fields, its counts against its own lists. That catches a lot,
but it has a hole a launch-thread reviewer (Linkrra, Nov 12, 2026) named
exactly: an output can be *consistently wrong*. The agent reports "9 sent",
its items list has 9 entries, every claim carries an id — and one of those
messages bounced an hour later. At completion time the output was, by every
internal measure, a PASS. The world disagreed afterwards.

So a passing verdict is **provisional**. It means "nothing in this document
contradicts itself", not "this happened". The second pass is the check
against the world: take the original output and a later snapshot from the
system of record — a provider delivery export, a database extract, the
receiving system's own log, in the same shape-tolerant JSON style as
everything else here — and re-ask the only questions that matter now:

- Does the record still stand behind each claim's evidence, or does the
  evidence now appear in a failure context (bounced, rejected, failed…)?
- Do the numbers the agent reported match the numbers the record shows?

Each claim and each reported count comes back as ``confirmed``,
``contradicted``, or ``unverifiable``. *Unverifiable* is a first-class
outcome, not a quiet pass: a record that never mentions a claim's evidence
has not confirmed it, and this module never upgrades silence into a PASS —
the same honest-scope rule the checks themselves follow. A first-pass FAIL
is not provisional and is never resurrected: the second pass reports it as
final and still shows what the record says, for the failure report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .checks.counts import COUNT_CONTAINER_KEYS
from .checks.evidence import CLAIM_LIST_KEYS, EVIDENCE_KEYS
from .engine import run_checks
from .models import CheckConfig, CheckResult
from .util import has_content, iter_nodes, key_tokens, normalize_key

#: Per-item outcomes of a second pass.
CONFIRMED = "confirmed"
CONTRADICTED = "contradicted"
UNVERIFIABLE = "unverifiable"

#: Key names that mark a subtree of the record as *failure* context: an
#: evidence value found only under one of these keys is a claim the world
#: has since contradicted, however clean the original output looked.
FAILURE_KEY_TOKENS = {
    "bounced",
    "bounce",
    "bounces",
    "failed",
    "failure",
    "failures",
    "undelivered",
    "rejected",
    "rejection",
    "rejections",
    "returned",
    "cancelled",
    "canceled",
    "deadletter",
    "blocked",
    "spam",
    "errors",
    "error",
}

#: Status/state values that mark the record entry carrying them as failed.
FAILURE_STATUSES = {
    "bounced",
    "failed",
    "failure",
    "error",
    "errored",
    "undelivered",
    "notdelivered",
    "rejected",
    "cancelled",
    "canceled",
    "returned",
    "blocked",
    "spam",
}

#: Claim statuses that assert nothing happened (mirrors FL002's rule: an
#: honestly failed or planned claim is not a completion claim).
NON_CLAIM_STATUSES = {"failed", "error", "skipped", "pending", "planned", "cancelled"}

_URL_RE = re.compile(r"https?://[^\s)\]]+")

_COUNT_KEY_RES = (
    re.compile(r"^(.+?)_count$"),
    re.compile(r"^count_(.+)$"),
    re.compile(r"^total_(.+)$"),
    re.compile(r"^num_(.+)$"),
)


def provisional_label(result: CheckResult) -> str:
    """The honest name for a first-pass verdict.

    A FAIL is final — the document contradicts itself and no later record
    can un-fail it. A pass, with or without warnings, is *provisional*
    until a second pass checks it against the system of record.
    """
    if not result.passed:
        return "FAIL"
    if result.warnings:
        return "PROVISIONAL PASS WITH WARNINGS"
    return "PROVISIONAL PASS"


# -- extraction --------------------------------------------------------------


def _scalar_values(value: Any) -> list[str]:
    """Every scalar leaf under *value*, as matchable strings.

    Single-character values and booleans are skipped: they are too
    generic to identify a claim in a record. Everything else an agent
    put in an evidence field is treated as an identifier worth looking
    for — short ids (``"m1"``) are real ids.
    """
    found: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            found.extend(_scalar_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_scalar_values(item))
    elif isinstance(value, str):
        text = value.strip()
        if len(text) >= 2:
            found.append(text)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        found.append(str(value))
    return found


def _claim_evidence_values(claim: dict[str, Any]) -> list[str]:
    """The evidence identifiers a claim carries: every scalar under an
    evidence-named field (FL002's key set), plus any URL anywhere in the
    claim. Deduplicated, order preserved."""
    values: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                if normalize_key(key) in EVIDENCE_KEYS and has_content(item):
                    values.extend(_scalar_values(item))
                else:
                    walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            values.extend(_URL_RE.findall(node))

    walk(claim)
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _claim_action(claim: dict[str, Any]) -> str | None:
    """The asserted action name, or ``None`` when the claim does not
    assert a completion (planned / pending / honestly failed)."""
    status = claim.get("status") or claim.get("state")
    if isinstance(status, str) and status.strip().lower() in NON_CLAIM_STATUSES:
        return None
    for key in ("action", "type", "verb", "did", "name", "operation"):
        value = claim.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if claim.get("done") is True or claim.get("completed") is True:
        return "completed action"
    if isinstance(status, str) and status.strip().lower() in {
        "done",
        "complete",
        "completed",
        "success",
        "succeeded",
        "ok",
    }:
        return "completed action"
    return None


@dataclass
class _RecordIndex:
    """Every scalar in the record, split by the context it was found in."""

    positive: set[str] = field(default_factory=set)
    failure: set[str] = field(default_factory=set)


def _index_record(record: Any) -> _RecordIndex:
    """Walk the record once, remembering for each scalar whether it was
    seen in a neutral/positive context, a failure context, or both.

    Failure context comes from the key path (``bounced``, ``failed``, …)
    or from a sibling status field marking its entry as failed — a
    delivery export that lists ``{"message_id": …, "status": "bounced"}``
    under a neutral key still contradicts the claim.
    """
    index = _RecordIndex()

    def walk(node: Any, in_failure: bool) -> None:
        if isinstance(node, dict):
            entry_failed = in_failure
            for key in ("status", "state", "outcome", "result"):
                value = node.get(key)
                if isinstance(value, str) and value.strip().lower() in FAILURE_STATUSES:
                    entry_failed = True
            for key, item in node.items():
                key_failed = entry_failed or bool(
                    key_tokens(key) & FAILURE_KEY_TOKENS
                )
                walk(item, key_failed)
        elif isinstance(node, list):
            for item in node:
                walk(item, in_failure)
        else:
            for text in _scalar_values(node):
                (index.failure if in_failure else index.positive).add(text)

    walk(record, False)
    return index


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _metric_of_count_key(key: str) -> str | None:
    for pattern in _COUNT_KEY_RES:
        match = pattern.match(key.lower())
        if match:
            return match.group(1)
    return None


def _reported_counts(doc: Any) -> dict[str, tuple[str, float]]:
    """Counts a document *reports*: normalized metric -> (key, value).

    Same sources FL004 reads: numbers inside counts/stats blocks, plus
    ``*_count`` / ``total_*`` style keys anywhere.
    """
    reported: dict[str, tuple[str, float]] = {}
    if not isinstance(doc, (dict, list)):
        return reported
    for path, value in iter_nodes(doc):
        if not isinstance(value, dict):
            continue
        parent_key = normalize_key(path.rsplit(".", 1)[-1]) if path != "$" else ""
        for key, item in value.items():
            if not _is_number(item):
                continue
            if parent_key in COUNT_CONTAINER_KEYS:
                reported.setdefault(normalize_key(key), (key, float(item)))
            else:
                metric = _metric_of_count_key(key)
                if metric is not None:
                    reported.setdefault(normalize_key(metric), (key, float(item)))
    return reported


def _record_truth(record: Any) -> dict[str, tuple[float, str]]:
    """What the record *shows* per metric: normalized metric -> (value,
    where it came from). Itemized list lengths override reported numbers
    — FL004's doctrine: the list is the only part that was ever true."""
    truth: dict[str, tuple[float, str]] = {}
    for metric, (_key, value) in _reported_counts(record).items():
        truth[metric] = (value, "the record's reported count")
    if isinstance(record, (dict, list)):
        for path, value in iter_nodes(record):
            if isinstance(value, list) and path != "$":
                metric = path.rsplit(".", 1)[-1]
                if metric.startswith("$"):
                    continue
                truth[normalize_key(metric)] = (float(len(value)), f"the record's list at {path}")
    return truth


def _names_match(a: str, b: str) -> bool:
    """Normalized metric-name match, FL004-style (exact, plural-tolerant,
    or token-subset). Inputs are already normalized keys."""
    if a == b:
        return True
    if a.rstrip("s") == b.rstrip("s") and a.rstrip("s"):
        return True
    tokens_a = {t for t in re.split(r"(?<=[a-z])(?=[0-9])|_", a) if t}
    tokens_b = {t for t in re.split(r"(?<=[a-z])(?=[0-9])|_", b) if t}
    return bool(tokens_a and tokens_b and (tokens_a <= tokens_b or tokens_b <= tokens_a))


# -- results -------------------------------------------------------------------


@dataclass
class ClaimRecheck:
    """One claim, re-judged against the record."""

    action: str
    target: str | None
    path: str
    evidence: list[str]
    status: str  # CONFIRMED / CONTRADICTED / UNVERIFIABLE
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "path": self.path,
            "evidence": self.evidence,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class CountRecheck:
    """One reported count, re-judged against the record."""

    metric: str
    claimed: float
    record_value: float | None
    status: str  # CONFIRMED / CONTRADICTED / UNVERIFIABLE
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "claimed": self.claimed,
            "record_value": self.record_value,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class SecondPassResult:
    """The second pass's whole judgement: first verdict, per-claim and
    per-count outcomes, and the final verdict they add up to."""

    first_verdict: str
    claims: list[ClaimRecheck] = field(default_factory=list)
    counts: list[CountRecheck] = field(default_factory=list)

    @property
    def provisional(self) -> bool:
        """True when the first pass passed — its verdict was provisional."""
        return self.first_verdict != "FAIL"

    @property
    def verdict(self) -> str:
        if self.first_verdict == "FAIL":
            return "FAIL"  # final at first pass; never resurrected
        items = [c.status for c in self.claims] + [c.status for c in self.counts]
        if any(status == CONTRADICTED for status in items):
            return "CONTRADICTED"
        if items and all(status == CONFIRMED for status in items):
            return "CONFIRMED"
        return "UNVERIFIABLE"

    @property
    def confirmed(self) -> bool:
        return self.verdict == "CONFIRMED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_verdict": self.first_verdict,
            "provisional": self.provisional,
            "verdict": self.verdict,
            "confirmed": self.confirmed,
            "claims": [c.to_dict() for c in self.claims],
            "counts": [c.to_dict() for c in self.counts],
        }


# -- the second pass -----------------------------------------------------------


def _recheck_claims(original: Any, index: _RecordIndex) -> list[ClaimRecheck]:
    results: list[ClaimRecheck] = []
    if not isinstance(original, (dict, list)):
        return results
    for path, value in iter_nodes(original):
        key = path.rsplit(".", 1)[-1]
        if normalize_key(key) not in CLAIM_LIST_KEYS or not isinstance(value, list):
            continue
        for position, claim in enumerate(value):
            if not isinstance(claim, dict):
                continue
            action = _claim_action(claim)
            if action is None:
                continue
            evidence = _claim_evidence_values(claim)
            target = claim.get("target")
            label = f"Claimed action {action!r}"
            if not evidence:
                status, reason = (
                    UNVERIFIABLE,
                    f"{label} carries no evidence identifiers, so there is "
                    "nothing for the record to confirm — unverifiable, not confirmed.",
                )
            else:
                failed = [v for v in evidence if v in index.failure]
                present = [v for v in evidence if v in index.positive]
                if failed:
                    status, reason = (
                        CONTRADICTED,
                        f"{label} is contradicted by the record: evidence "
                        f"{failed[0]!r} appears in a failure context "
                        "(bounced / failed / rejected) in the system of record.",
                    )
                elif present:
                    status, reason = (
                        CONFIRMED,
                        f"{label} is confirmed: evidence {present[0]!r} "
                        "appears in the system of record with no failure marker.",
                    )
                else:
                    status, reason = (
                        UNVERIFIABLE,
                        f"{label} cannot be confirmed: none of its evidence "
                        "appears in the system of record — silence is not a confirmation.",
                    )
            results.append(
                ClaimRecheck(
                    action=action,
                    target=target if isinstance(target, str) else None,
                    path=f"{path}[{position}]",
                    evidence=evidence,
                    status=status,
                    reason=reason,
                )
            )
    return results


def _recheck_counts(original: Any, record: Any) -> list[CountRecheck]:
    results: list[CountRecheck] = []
    truth = _record_truth(record)
    for metric, (key, claimed) in sorted(_reported_counts(original).items()):
        match = next((m for m in truth if _names_match(metric, m)), None)
        if match is None:
            results.append(
                CountRecheck(
                    metric=key,
                    claimed=claimed,
                    record_value=None,
                    status=UNVERIFIABLE,
                    reason=(
                        f"Count for {key!r} is reported as {claimed:g} but the "
                        "record shows nothing for this metric — unverifiable, "
                        "not confirmed."
                    ),
                )
            )
            continue
        actual, source = truth[match]
        if actual == claimed:
            status, reason = (
                CONFIRMED,
                f"Count for {key!r} confirmed: the record shows {actual:g} "
                f"(from {source}), matching the reported {claimed:g}.",
            )
        else:
            status, reason = (
                CONTRADICTED,
                f"Count for {key!r} is contradicted: reported as {claimed:g} "
                f"but the record shows {actual:g} (from {source}) — the "
                "world moved after the report, or the report was wrong.",
            )
        results.append(
            CountRecheck(
                metric=key, claimed=claimed, record_value=actual,
                status=status, reason=reason,
            )
        )
    return results


def recheck_output(
    original: Any,
    record: Any,
    config: CheckConfig | None = None,
    first_result: CheckResult | None = None,
) -> SecondPassResult:
    """Run the second pass: *original* re-judged against *record*.

    ``first_result`` may carry a verdict the caller already computed;
    otherwise the first pass runs here over *original* with *config*.
    The record is never itself "checked" — it is treated as the system of
    record, the closest thing to ground truth the caller has.
    """
    if first_result is None:
        first_result = run_checks(original, config)
    index = _index_record(record)
    return SecondPassResult(
        first_verdict=first_result.verdict,
        claims=_recheck_claims(original, index),
        counts=_recheck_counts(original, record),
    )
