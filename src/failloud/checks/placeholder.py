"""FL001 — placeholder_shipped.

Catches the output that was declared *done* while its payload was still
empty or still contained draft scaffolding: lorem ipsum, unrendered
``{{template}}`` braces, "coming soon", dead example domains.

Production origin: a page went live — URL public, launch marked complete —
with placeholder copy still in the body. Nothing crashed. Every automated
signal said success. The failure was only visible to a human who actually
read the page, which is exactly the reading this check automates.

Scope rule: the check fires when the document claims completion, or when it
carries no status at all (an unlabelled document handed downstream *is* a
final output). A document explicitly marked as a draft is left alone —
placeholders are legitimate in drafts; the failure is shipping them.
"""

from __future__ import annotations

from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import META_KEYS, has_content, is_empty, iter_nodes

CHECK_ID = "FL001"
NAME = "placeholder_shipped"
DESCRIPTION = (
    "Output declared done while its payload is empty or still contains "
    "placeholder/template scaffolding."
)

#: Status values that mean "this is final; judge it as shipped work".
COMPLETION_VALUES = {
    "done",
    "complete",
    "completed",
    "success",
    "successful",
    "succeeded",
    "ok",
    "shipped",
    "published",
    "live",
    "delivered",
    "finished",
    "ready",
}

#: Status values that mean "not final" — placeholders are allowed to exist.
NON_FINAL_VALUES = {
    "draft",
    "in_progress",
    "in-progress",
    "pending",
    "working",
    "queued",
    "running",
    "failed",
    "error",
    "cancelled",
    "canceled",
    "partial",
    "blocked",
}

#: Whole-value matches (after strip/lowercase): the field *is* a placeholder.
EXACT_PLACEHOLDERS = {
    "tbd",
    "tba",
    "todo",
    "to do",
    "placeholder",
    "dummy",
    "lorem ipsum",
    "coming soon",
    "n/a",
    "xxx",
    "...",
}

#: Substring matches: unambiguous draft scaffolding inside longer text.
SUBSTRING_PLACEHOLDERS = (
    "lorem ipsum",
    "coming soon",
    "<insert",
    "[insert",
    "{{",
    "}}",
    "placeholder text",
    "sample text",
    "your text here",
    "insert text here",
    "dummy content",
    "mock data",
    "example.com",
    "example.org",
    "todo:",
)

#: Fields, in priority order, that hold the actual work product.
PAYLOAD_KEYS = ("output", "payload", "deliverable", "result_content", "content", "body")


def _completion_state(doc: dict[str, Any]) -> bool | None:
    """True if the doc claims completion, False if explicitly non-final,
    None if it says nothing either way."""
    for key in ("status", "state", "result_status", "outcome"):
        value = doc.get(key)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in NON_FINAL_VALUES:
                return False
            if lowered in COMPLETION_VALUES:
                return True
    return None


def _payload(doc: dict[str, Any]) -> tuple[str, Any]:
    """Locate the work product: an explicit payload field, or the document
    minus its run-metadata keys."""
    for key in PAYLOAD_KEYS:
        if key in doc:
            return f"$.{key}", doc[key]
    inferred = {k: v for k, v in doc.items() if k not in META_KEYS}
    return "$", inferred


def _placeholder_matches(text: str) -> list[str]:
    lowered = text.strip().lower()
    matches: list[str] = []
    if lowered in EXACT_PLACEHOLDERS:
        matches.append(lowered)
    for pattern in SUBSTRING_PLACEHOLDERS:
        if pattern in lowered and pattern not in matches:
            matches.append(pattern)
    return matches


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    if not isinstance(doc, dict):
        return []
    if _completion_state(doc) is False:
        return []  # Explicitly a draft: placeholders are honest there.

    findings: list[Finding] = []

    payload_path, payload = _payload(doc)
    if not has_content(payload):
        findings.append(
            Finding(
                check_id=CHECK_ID,
                code="empty_payload",
                severity=Severity.ERROR,
                path=payload_path,
                message=(
                    "Output is marked complete but its payload is empty — "
                    "nothing was actually produced."
                ),
                detail={"payload_path": payload_path},
            )
        )
        return findings

    # Group every placeholder hit per field so the report reads as one
    # problem per location, not a pile of pattern matches.
    by_path: dict[str, list[str]] = {}
    for path, value in iter_nodes(doc):
        if isinstance(value, str) and not is_empty(value):
            matches = _placeholder_matches(value)
            if matches:
                by_path.setdefault(path, []).extend(matches)
    for path, matches in sorted(by_path.items()):
        unique = sorted(set(matches))
        findings.append(
            Finding(
                check_id=CHECK_ID,
                code="placeholder_shipped",
                severity=Severity.ERROR,
                path=path,
                message=(
                    "Placeholder content shipped as final output: "
                    f"matched {', '.join(repr(m) for m in unique)}."
                ),
                detail={"matched": unique},
            )
        )
    return findings
