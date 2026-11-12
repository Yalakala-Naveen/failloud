"""Small shared helpers: JSON walking, emptiness, key/timestamp parsing.

Everything here is deliberately conservative. FailLoud inspects documents it
did not produce, in shapes it cannot fully predict, so every helper treats
unexpected shapes as "not applicable" rather than as an error.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterator

#: Keys that describe the run itself rather than the work product. Used when
#: a document has no explicit payload field and we must infer one.
META_KEYS = {
    "task",
    "status",
    "state",
    "claims",
    "counts",
    "stats",
    "summary",
    "generated_at",
    "completed_at",
    "created_at",
    "started_at",
    "run_id",
    "agent",
    "model",
    "version",
}


def iter_nodes(node: Any, path: str = "$") -> Iterator[tuple[str, Any]]:
    """Yield ``(json_path, value)`` for *node* and every descendant."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from iter_nodes(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_nodes(value, f"{path}[{index}]")


def is_empty(value: Any) -> bool:
    """True for ``None``, blank strings, and empty containers.

    Numbers (including ``0``) and booleans are real content: an agent that
    reports a count of zero has said something; an agent that reports ``""``
    has not.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def has_content(value: Any) -> bool:
    """True if *value* contains at least one non-empty leaf anywhere."""
    if isinstance(value, dict):
        return any(has_content(v) for v in value.values())
    if isinstance(value, list):
        return any(has_content(v) for v in value)
    return not is_empty(value)


def normalize_key(key: str) -> str:
    """Lowercase a key and strip separators, for shape-tolerant matching."""
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def key_tokens(key: str) -> set[str]:
    """Split a key into word tokens: ``emails_sent`` -> ``{"emails", "sent"}``."""
    return {t for t in re.split(r"[^a-z0-9]+", str(key).lower()) if t}


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 string or epoch number into an aware datetime.

    Returns ``None`` for anything unparseable — an unreadable timestamp is
    the caller's problem to report, not this function's to guess at.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        # Epoch seconds, or milliseconds when the value is implausibly large.
        seconds = float(value)
        if seconds > 1e12:
            seconds /= 1000.0
        if seconds < 1:
            return None
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        return parse_timestamp(int(text))
    candidate = text.replace("Z", "+00:00") if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def reference_time(doc: Any, override: datetime | None) -> datetime:
    """The moment a run is evaluated against.

    Priority: an explicit override (tests, replays), then the document's own
    completion/generation timestamp, then the wall clock. Staleness is always
    measured against when the work claims to have happened, not when we
    happen to inspect it.
    """
    if override is not None:
        return override
    if isinstance(doc, dict):
        for key in ("generated_at", "completed_at", "finished_at", "created_at"):
            parsed = parse_timestamp(doc.get(key))
            if parsed is not None:
                return parsed
    return datetime.now(timezone.utc)


def resolve_path(doc: Any, dotted: str) -> tuple[bool, Any]:
    """Resolve a dotted path like ``output.archive_url`` against *doc*.

    Returns ``(found, value)``. Numeric components index into lists.
    """
    current = doc
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current
