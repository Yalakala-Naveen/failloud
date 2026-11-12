"""FL005 — missing_components.

Catches deliverables that are structurally present but silently incomplete:
a required field that exists on paper and is empty in fact, and — for
segmented media — stretches where a component should be and nothing is.

Production origin: a delivered video passed every existence check — right
file, right length, right format — while one segment inside it was silent.
Existence is not completeness. The check that exists because of that miss
measures the inside of the deliverable, not just its outline.

Three passes:

1. Required paths (``--require output.url`` / config) and JSON Schema
   ``required`` fields: missing *or* empty is an error.
2. Heuristic emptiness: fields inside the payload that are present but
   empty while their siblings carry content are warnings — often benign,
   always worth a look.
3. Segment integrity: zero-length segments and gaps between segments
   longer than ``max_segment_gap_seconds`` are dead stretches, and are
   errors.
"""

from __future__ import annotations

from typing import Any

from ..models import CheckConfig, Finding, Severity
from ..util import is_empty, normalize_key, resolve_path

CHECK_ID = "FL005"
NAME = "missing_components"
DESCRIPTION = (
    "Required components missing or silently empty, and dead stretches "
    "inside segmented deliverables."
)

#: Fields that are legitimately empty in healthy outputs.
ALLOW_EMPTY_KEYS = {"error", "errors", "warnings", "cc", "bcc", "metadata", "parentid"}

SEGMENT_LIST_KEYS = {"segments", "scenes", "tracks", "clips", "chapters", "shots"}
START_KEYS = ("start", "start_sec", "start_time", "begin", "from")
END_KEYS = ("end", "end_sec", "end_time", "to")
DURATION_KEYS = ("duration", "duration_sec", "length", "duration_seconds")


def _first_number(node: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    lowered = {normalize_key(k): v for k, v in node.items()}
    for key in keys:
        value = lowered.get(normalize_key(key))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _segment_span(segment: dict[str, Any]) -> tuple[float, float] | None:
    start = _first_number(segment, START_KEYS)
    end = _first_number(segment, END_KEYS)
    duration = _first_number(segment, DURATION_KEYS)
    if start is None and duration is None:
        return None
    start = start if start is not None else 0.0
    if end is None and duration is not None:
        end = start + duration
    if end is None:
        return None
    return start, end


def _check_segments(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    from ..util import iter_nodes

    for path, value in iter_nodes(doc):
        key = path.rsplit(".", 1)[-1]
        if normalize_key(key) not in SEGMENT_LIST_KEYS or not isinstance(value, list):
            continue
        spans: list[tuple[float, float, int]] = []
        for index, segment in enumerate(value):
            if not isinstance(segment, dict):
                continue
            span = _segment_span(segment)
            if span is None:
                continue
            start, end = span
            spans.append((start, end, index))
            if end - start <= 0:
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="zero_length_segment",
                        severity=Severity.ERROR,
                        path=f"{path}[{index}]",
                        message=(
                            f"Segment {index} has zero length "
                            f"({start:g}s–{end:g}s) — a component that "
                            "occupies a slot and contains nothing."
                        ),
                        detail={"start": start, "end": end},
                    )
                )
        spans.sort()
        for (prev_start, prev_end, _), (start, end, index) in zip(spans, spans[1:]):
            gap = start - prev_end
            if gap > config.max_segment_gap_seconds:
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="dead_stretch",
                        severity=Severity.ERROR,
                        path=f"{path}[{index}]",
                        message=(
                            f"Dead stretch of {gap:.1f}s before segment "
                            f"{index} (gap limit "
                            f"{config.max_segment_gap_seconds:g}s) — the "
                            "deliverable goes silent where content should be."
                        ),
                        detail={"gap_seconds": round(gap, 3), "before_segment": index},
                    )
                )
    return findings


def _check_schema(node: Any, schema: dict[str, Any], path: str) -> list[Finding]:
    """Walk the supported JSON Schema subset: ``required`` + ``properties``
    on objects, ``items`` on arrays."""
    findings: list[Finding] = []
    if not isinstance(schema, dict):
        return findings
    required = schema.get("required")
    if isinstance(required, list) and isinstance(node, dict):
        for key in required:
            if key not in node:
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="missing_component",
                        severity=Severity.ERROR,
                        path=f"{path}.{key}",
                        message=f"Required component {key!r} is missing entirely.",
                        detail={"required_by": "schema"},
                    )
                )
            elif is_empty(node[key]):
                findings.append(
                    Finding(
                        check_id=CHECK_ID,
                        code="empty_component",
                        severity=Severity.ERROR,
                        path=f"{path}.{key}",
                        message=(
                            f"Required component {key!r} is present but "
                            "empty — it satisfies the shape and delivers "
                            "nothing."
                        ),
                        detail={"required_by": "schema"},
                    )
                )
    properties = schema.get("properties")
    if isinstance(properties, dict) and isinstance(node, dict):
        for key, subschema in properties.items():
            if key in node:
                findings.extend(_check_schema(node[key], subschema, f"{path}.{key}"))
    items = schema.get("items")
    if isinstance(items, dict) and isinstance(node, list):
        for index, item in enumerate(node):
            findings.extend(_check_schema(item, items, f"{path}[{index}]"))
    return findings


def check(doc: Any, config: CheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(doc, dict):
        return findings

    # Pass 1a: explicitly required dotted paths.
    for dotted in config.required_paths:
        found, value = resolve_path(doc, dotted)
        if not found:
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="missing_component",
                    severity=Severity.ERROR,
                    path=f"$.{dotted}",
                    message=f"Required component {dotted!r} is missing entirely.",
                    detail={"required_by": "required_paths"},
                )
            )
        elif is_empty(value):
            findings.append(
                Finding(
                    check_id=CHECK_ID,
                    code="empty_component",
                    severity=Severity.ERROR,
                    path=f"$.{dotted}",
                    message=(
                        f"Required component {dotted!r} is present but empty "
                        "— it satisfies the shape and delivers nothing."
                    ),
                    detail={"required_by": "required_paths"},
                )
            )

    # Pass 1b: JSON Schema subset.
    if config.schema:
        findings.extend(_check_schema(doc, config.schema, "$"))

    # Pass 2: heuristic emptiness inside the payload.
    payload: Any = doc.get("output", doc)
    if isinstance(payload, dict):
        from ..util import iter_nodes

        for path, value in iter_nodes(payload, "$.output" if "output" in doc else "$"):
            if not isinstance(value, dict):
                continue
            populated = [k for k, v in value.items() if not is_empty(v)]
            if not populated:
                continue
            for key, item in value.items():
                if normalize_key(key) in ALLOW_EMPTY_KEYS:
                    continue
                if is_empty(item):
                    findings.append(
                        Finding(
                            check_id=CHECK_ID,
                            code="empty_field",
                            severity=Severity.WARNING,
                            path=f"{path}.{key}",
                            message=(
                                f"Field {key!r} is present but empty while "
                                "its siblings carry content — verify it was "
                                "meant to be blank."
                            ),
                            detail={},
                        )
                    )

    # Pass 3: segment integrity.
    findings.extend(_check_segments(doc, config))
    return findings
