"""The checking engine: run checks over a parsed document."""

from __future__ import annotations

from typing import Any

from .checks import BY_ID, MODULES
from .models import CheckConfig, CheckOutcome, CheckResult


def run_checks(doc: Any, config: CheckConfig | None = None) -> CheckResult:
    """Run every selected check over *doc* and aggregate the verdict."""
    config = config or CheckConfig()
    selected = MODULES
    if config.only:
        wanted = {check_id.upper() for check_id in config.only}
        selected = [m for m in MODULES if m.CHECK_ID in wanted]
        unknown = wanted - {m.CHECK_ID for m in MODULES}
        if unknown:
            raise ValueError(f"Unknown check id(s): {', '.join(sorted(unknown))}")
    outcomes = [
        CheckOutcome(
            check_id=module.CHECK_ID,
            name=module.NAME,
            findings=module.check(doc, config),
        )
        for module in selected
    ]
    return CheckResult(outcomes=outcomes)


def run_single(doc: Any, check_id: str, config: CheckConfig | None = None) -> CheckOutcome:
    """Run exactly one check by id (``FL001``…``FL005``)."""
    module = BY_ID.get(check_id.upper())
    if module is None:
        raise ValueError(
            f"Unknown check id {check_id!r}. Known: {', '.join(sorted(BY_ID))}"
        )
    config = config or CheckConfig()
    return CheckOutcome(
        check_id=module.CHECK_ID,
        name=module.NAME,
        findings=module.check(doc, config),
    )
