"""FL004 — count_mismatch."""

from failloud import CheckConfig, run_single


def run(doc):
    return run_single(doc, "FL004", CheckConfig()).findings


def test_matching_count_passes():
    doc = {"counts": {"sent": 3}, "items": {"sent": ["a", "b", "c"]}}
    assert run(doc) == []


def test_inflated_count_fails():
    doc = {"counts": {"sent": 12}, "items": {"sent": ["a", "b", "c"]}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "count_mismatch"
    assert findings[0].detail["claimed"] == 12
    assert findings[0].detail["actual"] == 3
    assert findings[0].detail["inflated"] is True


def test_understated_count_also_fails():
    doc = {"counts": {"sent": 2}, "items": {"sent": ["a", "b", "c"]}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].detail["inflated"] is False


def test_count_suffix_key_style():
    doc = {"emails_sent_count": 5, "emails_sent": ["a", "b"]}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].detail["claimed"] == 5
    assert findings[0].detail["actual"] == 2


def test_claim_without_itemization_is_unverifiable_not_wrong():
    doc = {"counts": {"sent": 12}}
    assert run(doc) == []


def test_total_must_equal_sum_of_parts():
    doc = {"counts": {"total": 30, "sent": 10, "delivered": 12}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "count_total_mismatch"
    assert findings[0].detail["sum_of_parts"] == 22


def test_total_matching_parts_passes():
    doc = {"counts": {"total": 22, "sent": 10, "delivered": 12}}
    assert run(doc) == []


def test_plural_and_token_variants_match():
    doc = {"counts": {"messages": 4}, "items": {"message": ["a", "b", "c", "d"]}}
    assert run(doc) == []


def test_boolean_is_not_a_count():
    doc = {"counts": {"sent": True}, "items": {"sent": ["a"]}}
    assert run(doc) == []
