"""FL003 — stale_state.

Catches work performed on top of context that was already old when the run
started: a handover snapshot from days ago, a "current" state whose version
the world has since moved past.

Production origin: a multi-step pipeline where step two planned from the
context snapshot step one had captured — except the snapshot was from an
earlier run entirely. Every step executed correctly. The plan was flawless
for a world that no longer existed.

Three detectors:

1. Age — timestamps inside a state/context block older than
   ``max_state_age_hours`` relative to the run's reference time.
2. Freshness — a state block carrying real data but no timestamp at all:
   its age is unknowable, which is reported as a warning, not an error.
3. Version skew — the run declares the state version it based itself on,
   and the state block itself reports a different version.
"""

from __future__ import annotations

from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import is_empty, normalize_key, parse_timestamp, reference_time

CHECK_ID = "FL003"
NAME = "stale_state"
DESCRIPTION = (
    "Work based on state/context that was already stale — or carries no "
    "freshness timestamp at all — when the run used it."
)

#: Keys whose dict/list values count as "carried state".
STATE_CONTAINER_KEYS = {"state", "context", "handoff", "memory", "inputstate", "workingstate"}

#: Timestamp key names that describe when state was captured.
TIMESTAMP_KEYS = {
    "contextupdatedat",
    "stateupdatedat",
    "asof",
    "contextasof",
    "dataasof",
    "snapshotat",
    "retrievedat",
    "updatedat",
    "lastupdated",
    "validasof",
    "capturedat",
    "observedat",
}

VERSION_KEYS = {"version", "stateversion", "revision"}
EXPECTED_VERSION_KEYS = {
    "basedonversion",
    "expectedstateversion",
    "expectedversion",
    "assumedstateversion",
    "assumedversion",
}


def _walk_state(
    node: Any, path: str, in_state: bool
) -> list[tuple[str, Any, bool]]:
    """Walk the document tracking whether each node sits inside a state
    container. Returns ``(path, node, in_state)`` triples."""
    out: list[tuple[str, Any, bool]] = [(path, node, in_state)]
    if isinstance(node, dict):
        for key, value in node.items():
            child_in_state = in_state or normalize_key(key) in STATE_CONTAINER_KEYS
            out.extend(_walk_state(value, f"{path}.{key}", child_in_state))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.extend(_walk_state(value, f"{path}[{index}]", in_state))
    return out


def _is_timestamp_key(key: str) -> bool:
    normalized = normalize_key(key)
    return normalized in TIMESTAMP_KEYS or normalized.endswith("at")


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(doc, dict):
        return findings

    ref = reference_time(doc, config.now)
    nodes = _walk_state(doc, "$", False)

    # --- Age -------------------------------------------------------------
    state_containers: list[tuple[str, dict[str, Any]]] = []
    for path, node, in_state in nodes:
        if isinstance(node, dict) and path != "$":
            key = path.rsplit(".", 1)[-1]
            if normalize_key(key) in STATE_CONTAINER_KEYS and not is_empty(node):
                state_containers.append((path, node))
        if not in_state or not isinstance(node, dict):
            continue
        for key, value in node.items():
            if not _is_timestamp_key(key):
                continue
            parsed = parse_timestamp(value)
            if parsed is None:
                continue
            age_hours = (ref - parsed).total_seconds() / 3600.0
            if age_hours > config.max_state_age_hours:
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="stale_state",
                        severity=Severity.ERROR,
                        path=f"{path}.{key}",
                        message=(
                            f"State timestamp is {age_hours:.1f}h old at run "
                            f"time (limit {config.max_state_age_hours:g}h) — "
                            "the run worked from context older than allowed."
                        ),
                        detail={
                            "timestamp": value if isinstance(value, str) else str(value),
                            "age_hours": round(age_hours, 2),
                            "max_age_hours": config.max_state_age_hours,
                        },
                    )
                )

    # --- Freshness -------------------------------------------------------
    for path, container in state_containers:
        has_timestamp = any(
            _is_timestamp_key(k) and parse_timestamp(v) is not None
            for _, node, in_state in _walk_state(container, path, True)
            if isinstance(node, dict)
            for k, v in node.items()
        )
        if not has_timestamp:
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="state_without_freshness",
                    severity=Severity.WARNING,
                    path=path,
                    message=(
                        "State is handed over with no freshness timestamp — "
                        "its age cannot be verified, so staleness would be "
                        "invisible."
                    ),
                    detail={},
                )
            )

    # --- Version skew ----------------------------------------------------
    state_versions: list[Any] = []
    expected_versions: list[Any] = []
    for path, node, in_state in nodes:
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            normalized = normalize_key(key)
            if in_state and normalized in VERSION_KEYS and isinstance(value, (int, str)):
                state_versions.append(value)
            if normalized in EXPECTED_VERSION_KEYS and isinstance(value, (int, str)):
                expected_versions.append(value)
    if state_versions and expected_versions:
        actual = state_versions[0]
        expected = expected_versions[0]
        if str(actual) != str(expected):
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="state_version_skew",
                    severity=Severity.ERROR,
                    path="$",
                    message=(
                        f"Run based itself on state version {expected!r} but "
                        f"the state it carried is version {actual!r} — the "
                        "handover and the work disagree about the world."
                    ),
                    detail={"state_version": actual, "based_on_version": expected},
                )
            )
    return findings
