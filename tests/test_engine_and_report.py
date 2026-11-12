"""Engine aggregation, verdict logic, and report rendering."""

import json

import pytest

from failloud import CheckConfig, check_output, run_checks
from failloud.report import render_json, render_markdown, render_text

FAILING_DOC = {
    "status": "done",
    "output": {"body": "Lorem ipsum, coming soon."},
    "counts": {"sent": 5},
    "items": {"sent": ["a"]},
}


def test_all_five_checks_run_by_default():
    result = check_output(FAILING_DOC)
    assert [o.check_id for o in result.outcomes] == [
        "FL001",
        "FL002",
        "FL003",
        "FL004",
        "FL005",
    ]


def test_verdict_fail_when_errors_exist():
    result = check_output(FAILING_DOC)
    assert result.verdict == "FAIL"
    assert result.passed is False
    assert len(result.errors) >= 2


def test_verdict_pass_for_clean_doc():
    result = check_output({"status": "done", "output": {"body": "Finished work."}})
    assert result.verdict == "PASS"
    assert result.passed is True


def test_warnings_only_doc_passes_with_warnings():
    # ``output.url`` is empty while its sibling is filled: a warning, and
    # the state block has no timestamp: another warning. No errors.
    doc = {
        "status": "done",
        "output": {"title": "Hi", "url": ""},
        "state": {"snapshot": {"users": 3}},
    }
    result = check_output(doc)
    assert result.verdict == "PASS WITH WARNINGS"
    assert result.passed is True
    assert len(result.warnings) >= 1
    assert result.errors == []


def test_only_filter_restricts_checks():
    result = run_checks(FAILING_DOC, CheckConfig(only=("FL004",)))
    assert [o.check_id for o in result.outcomes] == ["FL004"]


def test_unknown_check_id_raises():
    with pytest.raises(ValueError):
        run_checks(FAILING_DOC, CheckConfig(only=("FL099",)))


def test_result_serializes_to_json():
    result = check_output(FAILING_DOC)
    payload = json.loads(render_json(result, source="test"))
    assert payload["verdict"] == "FAIL"
    assert payload["source"] == "test"
    assert payload["error_count"] == len(result.errors)


def test_text_report_shape():
    text = render_text(check_output(FAILING_DOC), source="doc.json")
    assert "FAILLOUD" in text
    assert "Verdict: FAIL" in text
    assert "FL001" in text


def test_markdown_report_is_the_failure_report():
    md = render_markdown(check_output(FAILING_DOC), source="doc.json")
    assert md.startswith("# FAILURE REPORT")
    assert "| FL004 | count_mismatch | FAIL |" in md
    assert "Why it matters" in md


def test_markdown_report_for_passing_doc():
    md = render_markdown(check_output({"output": {"body": "Real work."}}))
    assert md.startswith("# VERIFICATION REPORT")
    assert "No silent failures found" in md
