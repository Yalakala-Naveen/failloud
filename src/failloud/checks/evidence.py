"""FL002 — unbacked_claim.

Catches claims of completed real-world actions that carry no evidence: the
agent says it sent, posted, published, updated, deployed — and nothing in
the output (no message id, no URL, no receipt, no artifact) backs the claim.

Production origin: a run reported a batch of messages as sent. One address
had bounced; the report never knew, because "sent" was asserted by the same
component that performed the send and nothing downstream demanded proof.
The rule that came out of it: a claim without evidence is a rumor.

Two passes:

1. Structured claims — every entry in a ``claims``/``actions`` list that
   asserts a completed action must carry at least one evidence field.
2. Narrative claims — if a ``summary``/``message`` field asserts completed
   actions in prose while the *entire document* contains no evidence at
   all, the narrative is flagged once per field.
"""

from __future__ import annotations

import re
from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import has_content, is_empty, iter_nodes, normalize_key
from .placeholder import COMPLETION_VALUES

CHECK_ID = "FL002"
NAME = "unbacked_claim"
DESCRIPTION = (
    "A claimed action (sent, posted, published, updated…) with no evidence "
    "— no id, URL, receipt, or artifact — anywhere to back it."
)

#: Keys whose non-empty value counts as evidence for a claim.
EVIDENCE_KEYS = {
    "evidence",
    "proof",
    "artifact",
    "artifacts",
    "url",
    "urls",
    "link",
    "links",
    "id",
    "messageid",
    "recordid",
    "receipt",
    "receiptid",
    "confirmation",
    "confirmationid",
    "externalid",
    "path",
    "file",
    "hash",
    "sha",
    "permalink",
    "reference",
    "ticket",
    "postid",
    "threadid",
}

#: Document keys that conventionally hold the list of claimed actions.
CLAIM_LIST_KEYS = {"claims", "actions", "actionstaken", "steps", "completedactions"}

#: Past-tense action verbs that assert something happened in the world.
CLAIM_VERB_RE = re.compile(
    r"\b(sent|posted|published|emailed|uploaded|deployed|updated|created|"
    r"deleted|booked|charged|notified|delivered|filed|submitted|released|"
    r"merged|announced)\b",
    re.IGNORECASE,
)

URL_RE = re.compile(r"https?://[^\s)\]]+")

#: Free-text fields where narrative claims usually live.
TEXT_CLAIM_KEYS = {"summary", "message", "report", "description", "notes", "result"}


def _value_has_evidence(value: Any) -> bool:
    """True if *value* contains, at any depth, an evidence-named field
    holding actual content. An ``evidence`` object whose fields are all
    empty is a container, not evidence, and does not count."""
    if isinstance(value, dict):
        for key, item in value.items():
            if normalize_key(key) in EVIDENCE_KEYS and has_content(item):
                return True
            if _value_has_evidence(item):
                return True
        return False
    if isinstance(value, list):
        return any(_value_has_evidence(item) for item in value)
    return False


def _claim_asserts_completion(claim: dict[str, Any]) -> str | None:
    """Return the asserted action name if *claim* says something was done,
    else None (planned, in-progress, or honestly failed claims pass)."""
    status = claim.get("status") or claim.get("state")
    if isinstance(status, str):
        lowered = status.strip().lower()
        if lowered in {"failed", "error", "skipped", "pending", "planned", "cancelled"}:
            return None
    for key in ("action", "type", "verb", "did", "name", "operation"):
        value = claim.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if claim.get("done") is True or claim.get("completed") is True:
        return "completed action"
    if isinstance(status, str) and status.strip().lower() in COMPLETION_VALUES:
        return "completed action"
    return None


def _document_has_evidence(doc: Any) -> bool:
    for _, value in iter_nodes(doc):
        if isinstance(value, dict):
            for key, item in value.items():
                if normalize_key(key) in EVIDENCE_KEYS and not is_empty(item):
                    return True
        if isinstance(value, str) and URL_RE.search(value):
            return True
    return False


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(doc, (dict, list)):
        return findings

    # Pass 1: structured claims.
    for path, value in iter_nodes(doc):
        key = path.rsplit(".", 1)[-1]
        if normalize_key(key) not in CLAIM_LIST_KEYS or not isinstance(value, list):
            continue
        for index, claim in enumerate(value):
            if not isinstance(claim, dict):
                continue
            action = _claim_asserts_completion(claim)
            if action is None:
                continue
            if not _value_has_evidence(claim):
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="unbacked_claim",
                        severity=Severity.ERROR,
                        path=f"{path}[{index}]",
                        message=(
                            f"Claimed action {action!r} has no evidence — no "
                            "id, URL, receipt, or artifact in the claim "
                            "backs that it happened."
                        ),
                        detail={"action": action},
                    )
                )

    # Pass 2: narrative claims with zero evidence in the whole document.
    if isinstance(doc, dict) and not _document_has_evidence(doc):
        for key, value in doc.items():
            if normalize_key(key) in {normalize_key(k) for k in TEXT_CLAIM_KEYS}:
                if isinstance(value, str) and CLAIM_VERB_RE.search(value):
                    verbs = sorted({m.lower() for m in CLAIM_VERB_RE.findall(value)})
                    findings.append(
                        Finding(
                            check_id=CHECK_ID,
                            code="unbacked_claim",
                            severity=Severity.ERROR,
                            path=f"$.{key}",
                            message=(
                                "Narrative claims completed actions "
                                f"({', '.join(verbs)}) but the document "
                                "contains no evidence — no id, URL, receipt, "
                                "or artifact — anywhere."
                            ),
                            detail={"verbs": verbs},
                        )
                    )
    return findings
