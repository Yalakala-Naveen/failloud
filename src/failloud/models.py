"""Core data model for FailLoud.

A *finding* is one concrete, located problem in an agent output document.
A *check* is a detector for one class of silent failure; it produces zero or
more findings. A :class:`CheckResult` aggregates every check's outcome into
a single verdict:

- ``FAIL`` — at least one error-severity finding. The output should not be
  trusted or shipped downstream.
- ``PASS WITH WARNINGS`` — no errors, but warning-severity findings exist.
- ``PASS`` — nothing found.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class Severity(str, enum.Enum):
    """How much a finding should hurt."""

    ERROR = "error"
    WARNING = "warning"


@dataclass
class Finding:
    """One located problem in an agent output document."""

    check_id: str  # e.g. "FL001"
    code: str  # machine-readable slug, e.g. "placeholder_shipped"
    severity: Severity
    path: str  # JSON path, e.g. "$.output.body"
    message: str  # human-readable, written for the failure report
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "code": self.code,
            "severity": self.severity.value,
            "path": self.path,
            "message": self.message,
            "detail": self.detail,
        }


@dataclass
class CheckOutcome:
    """The result of running a single check."""

    check_id: str
    name: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(f.severity is Severity.ERROR for f in self.findings):
            return "fail"
        if self.findings:
            return "warn"
        return "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "status": self.status,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class CheckResult:
    """Aggregate result of running every selected check over one document."""

    outcomes: list[CheckOutcome]

    @property
    def findings(self) -> list[Finding]:
        return [f for outcome in self.outcomes for f in outcome.findings]

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARNING]

    @property
    def verdict(self) -> str:
        if self.errors:
            return "FAIL"
        if self.warnings:
            return "PASS WITH WARNINGS"
        return "PASS"

    @property
    def passed(self) -> bool:
        return not self.errors

    def outcome_for(self, check_id: str) -> CheckOutcome | None:
        for outcome in self.outcomes:
            if outcome.check_id == check_id:
                return outcome
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "passed": self.passed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "checks": [o.to_dict() for o in self.outcomes],
        }


@dataclass
class CheckConfig:
    """Tunables shared by the checks. Every knob has a production-derived
    default; override per call, per CLI flag, or per MCP tool argument."""

    #: State older than this (relative to the run's reference time) is stale.
    max_state_age_hours: float = 24.0
    #: In a segmented deliverable, a gap longer than this is a dead stretch.
    max_segment_gap_seconds: float = 2.0
    #: Dotted paths that must exist and be non-empty, e.g. ("output.url",).
    required_paths: tuple[str, ...] = ()
    #: Optional JSON Schema (subset: ``required``/``properties``/``items``).
    schema: dict[str, Any] | None = None
    #: Restrict the run to these check ids, e.g. ("FL001", "FL004").
    only: tuple[str, ...] | None = None
    #: Reference "now" for staleness. Overrides the document's own
    #: ``generated_at`` when set; exists so tests and replays are
    #: deterministic.
    now: datetime | None = None
