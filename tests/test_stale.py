"""FL003 — stale_state."""

from datetime import datetime, timezone

from failloud import CheckConfig, run_single

GENERATED = "2026-11-11T14:00:00Z"


def run(doc, **config_kwargs):
    return run_single(doc, "FL003", CheckConfig(**config_kwargs)).findings


def test_fresh_state_passes():
    doc = {
        "generated_at": GENERATED,
        "state": {"context_updated_at": "2026-11-11T13:00:00Z", "audience": "subs"},
    }
    assert run(doc) == []


def test_stale_state_fails_with_age():
    doc = {
        "generated_at": GENERATED,
        "state": {"context_updated_at": "2026-11-08T14:00:00Z", "audience": "subs"},
    }
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "stale_state"
    assert findings[0].detail["age_hours"] == 72.0


def test_custom_threshold():
    doc = {
        "generated_at": GENERATED,
        "state": {"context_updated_at": "2026-11-11T10:00:00Z"},
    }
    assert run(doc) == []  # 4h old, default limit 24h
    findings = run(doc, max_state_age_hours=2.0)
    assert len(findings) == 1


def test_state_without_any_timestamp_warns():
    doc = {"generated_at": GENERATED, "state": {"snapshot": {"users": 3}}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "state_without_freshness"
    assert findings[0].severity.value == "warning"


def test_version_skew_fails():
    doc = {
        "generated_at": GENERATED,
        "state": {"version": 3, "updated_at": "2026-11-11T13:30:00Z"},
        "based_on": {"expected_state_version": 5},
    }
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "state_version_skew"
    assert findings[0].detail["state_version"] == 3
    assert findings[0].detail["based_on_version"] == 5


def test_matching_versions_pass():
    doc = {
        "generated_at": GENERATED,
        "state": {"version": 5, "updated_at": "2026-11-11T13:30:00Z"},
        "based_on": {"expected_state_version": 5},
    }
    assert run(doc) == []


def test_injected_now_makes_replay_deterministic():
    doc = {"state": {"context_updated_at": "2026-11-01T00:00:00Z", "x": 1}}
    findings = run(doc, now=datetime(2026, 11, 11, tzinfo=timezone.utc))
    assert any(f.code == "stale_state" for f in findings)


def test_timestamps_outside_state_are_ignored():
    # A delivered_at inside an items list is history, not carried state.
    doc = {
        "generated_at": GENERATED,
        "items": [{"delivered_at": "2020-01-01T00:00:00Z"}],
    }
    assert run(doc) == []
