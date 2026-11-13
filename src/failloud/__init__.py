"""FailLoud — a verification harness for LLM agent outputs.

Agents rarely fail loudly. They return ``status: done`` with an empty
payload, claim an action no artifact backs, plan from state that went stale
two steps ago, report counts their own itemized record contradicts, and
ship deliverables with silent holes in them. FailLoud reads the output the
way a skeptical reviewer would and produces a failure report instead of a
shrug.

Quick start::

    import json
    from failloud import check_output

    result = check_output(json.load(open("agent_output.json")))
    if not result.passed:
        print(result.verdict)  # "FAIL"
        for finding in result.errors:
            print(finding.check_id, finding.path, finding.message)
"""

from __future__ import annotations

from typing import Any

from .engine import run_checks, run_single
from .models import CheckConfig, CheckOutcome, CheckResult, Finding, Severity
from .receipts import Receipt, create_receipt, verify_chain, verify_receipt
from .watch import WatchEvent, Watcher, WatchSummary, watch

__version__ = "0.3.0"

__all__ = [
    "check_output",
    "run_checks",
    "run_single",
    "CheckConfig",
    "CheckOutcome",
    "CheckResult",
    "Finding",
    "Severity",
    "Receipt",
    "create_receipt",
    "verify_receipt",
    "verify_chain",
    "WatchEvent",
    "Watcher",
    "WatchSummary",
    "watch",
    "__version__",
]


def check_output(doc: Any, config: CheckConfig | None = None) -> CheckResult:
    """Verify one agent output document. The main entry point."""
    return run_checks(doc, config)
