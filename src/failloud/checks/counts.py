"""FL004 — count_mismatch.

Catches reported numbers that disagree with the itemized record in the
same document: the summary claims 12, the list contains 9. The claimed
number is the one that travels — into dashboards, digests, and decisions —
while the list is the only part that was ever true.

Production origin: a report counted actions *attempted* while its audience
read them as actions *completed*. Attempted and completed differed by the
failures nobody itemized. The rule that came out of it: any count a reader
will repeat must reconcile with a list a reader can count.

What is verified (structured data only — prose numbers are out of scope):

- A numeric claim (``counts.sent``, ``emails_sent_count``, ``total_sent``)
  whose metric has an itemized list in the document must equal the list's
  length.
- A ``total`` inside a counts block must equal the sum of its siblings.
"""

from __future__ import annotations

import re
from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import iter_nodes, key_tokens, normalize_key

CHECK_ID = "FL004"
NAME = "count_mismatch"
DESCRIPTION = (
    "A reported count that does not match the itemized record in the same "
    "document (or a total that does not match its own parts)."
)

COUNT_CONTAINER_KEYS = {"counts", "stats", "summarycounts", "totals", "metrics"}
COUNT_KEY_RES = (
    re.compile(r"^(.+?)_count$"),
    re.compile(r"^count_(.+)$"),
    re.compile(r"^total_(.+)$"),
    re.compile(r"^num_(.+)$"),
)


def _metric_of_count_key(key: str) -> str | None:
    for pattern in COUNT_KEY_RES:
        match = pattern.match(key.lower())
        if match:
            return match.group(1)
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _names_match(claim_metric: str, array_metric: str) -> bool:
    a, b = normalize_key(claim_metric), normalize_key(array_metric)
    if a == b:
        return True
    if a.rstrip("s") == b.rstrip("s") and a.rstrip("s"):
        return True
    tokens_a, tokens_b = key_tokens(claim_metric), key_tokens(array_metric)
    if tokens_a and tokens_b and (tokens_a <= tokens_b or tokens_b <= tokens_a):
        return True
    return False


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(doc, (dict, list)):
        return findings

    # Collect itemized lists: (metric name, path, length).
    arrays: list[tuple[str, str, int]] = []
    for path, value in iter_nodes(doc):
        if isinstance(value, list) and path != "$":
            metric = path.rsplit(".", 1)[-1]
            if metric.startswith("$"):
                continue
            arrays.append((metric, path, len(value)))

    # Collect numeric claims: (metric name, path, claimed value).
    claims: list[tuple[str, str, float]] = []
    seen: set[tuple[str, float]] = set()

    def add_claim(metric: str, path: str, value: float) -> None:
        dedupe_key = (normalize_key(metric), float(value))
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)
        claims.append((metric, path, value))

    for path, value in iter_nodes(doc):
        if not isinstance(value, dict):
            continue
        parent_key = normalize_key(path.rsplit(".", 1)[-1]) if path != "$" else ""
        for key, item in value.items():
            if not _is_number(item):
                continue
            item_path = f"{path}.{key}"
            if parent_key in COUNT_CONTAINER_KEYS:
                add_claim(key, item_path, float(item))
            else:
                metric = _metric_of_count_key(key)
                if metric is not None:
                    add_claim(metric, item_path, float(item))

    # A "total" must equal the sum of the siblings it totals.
    for path, value in iter_nodes(doc):
        if not isinstance(value, dict):
            continue
        parent_key = normalize_key(path.rsplit(".", 1)[-1]) if path != "$" else ""
        if parent_key not in COUNT_CONTAINER_KEYS:
            continue
        numeric = {k: v for k, v in value.items() if _is_number(v)}
        for key, total in numeric.items():
            if normalize_key(key) in {"total", "grandtotal", "count"} and len(numeric) >= 3:
                parts = sum(v for k, v in numeric.items() if k != key)
                if float(total) != float(parts):
                    findings.append(
                        Finding(
                            check_id=CHECK_ID,
                            code="count_total_mismatch",
                            severity=Severity.ERROR,
                            path=f"{path}.{key}",
                            message=(
                                f"Reported total {total:g} does not equal "
                                f"the sum of its parts ({parts:g})."
                            ),
                            detail={"claimed": total, "sum_of_parts": parts},
                        )
                    )

    # Every claim with an itemized list must reconcile with it.
    for metric, path, claimed in claims:
        matching = [a for a in arrays if _names_match(metric, a[0])]
        if not matching:
            continue  # Nothing itemized: the claim is unverifiable, not wrong.
        # Prefer the longest list among name matches — the fullest record.
        array_metric, array_path, actual = max(matching, key=lambda a: a[2])
        if float(actual) != claimed:
            inflated = claimed > actual
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="count_mismatch",
                    severity=Severity.ERROR,
                    path=path,
                    message=(
                        f"Count for {metric!r} is reported as {claimed:g} "
                        f"but the itemized record at {array_path} contains "
                        f"{actual} item(s) — "
                        + (
                            "the report overstates what the record supports."
                            if inflated
                            else "the report understates its own record."
                        )
                    ),
                    detail={
                        "metric": metric,
                        "claimed": claimed,
                        "actual": actual,
                        "inflated": inflated,
                        "items_path": array_path,
                    },
                )
            )
    return findings
