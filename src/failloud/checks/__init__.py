"""The check registry.

Each module in this package detects one class of silent failure and exposes
``CHECK_ID``, ``NAME``, ``DESCRIPTION`` and ``check(doc, config)``.
"""

from __future__ import annotations

from types import ModuleType

from . import completeness, counts, evidence, placeholder, stale

MODULES: list[ModuleType] = [placeholder, evidence, stale, counts, completeness]

BY_ID: dict[str, ModuleType] = {m.CHECK_ID: m for m in MODULES}

__all__ = ["MODULES", "BY_ID"]
