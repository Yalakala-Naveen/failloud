"""FL002 — unbacked_claim."""

from failloud import CheckConfig, run_single


def run(doc):
    return run_single(doc, "FL002", CheckConfig()).findings


def test_claim_with_message_id_passes():
    doc = {"claims": [{"action": "email_sent", "evidence": {"message_id": "m-1"}}]}
    assert run(doc) == []


def test_claim_with_url_evidence_passes():
    doc = {"claims": [{"action": "card_published", "url": "https://x.co/p/1"}]}
    assert run(doc) == []


def test_claim_without_evidence_fails():
    doc = {"claims": [{"action": "email_sent", "target": "ops-list"}]}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "unbacked_claim"
    assert findings[0].path == "$.claims[0]"
    assert findings[0].detail["action"] == "email_sent"


def test_claim_with_null_evidence_fails():
    doc = {"claims": [{"action": "email_sent", "evidence": None}]}
    assert len(run(doc)) == 1


def test_claim_with_empty_evidence_dict_fails():
    doc = {"claims": [{"action": "email_sent", "evidence": {"message_id": ""}}]}
    assert len(run(doc)) == 1


def test_honestly_failed_claim_is_not_flagged():
    doc = {"claims": [{"action": "email_sent", "status": "failed", "error": "bounce"}]}
    assert run(doc) == []


def test_only_the_unbacked_claim_is_flagged():
    doc = {
        "claims": [
            {"action": "email_sent", "evidence": {"message_id": "m-1"}},
            {"action": "card_published", "target": "feed"},
        ]
    }
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].path == "$.claims[1]"


def test_narrative_claim_with_no_evidence_anywhere_fails():
    doc = {"summary": "Sent the report and published the dashboard."}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].path == "$.summary"
    assert "sent" in findings[0].detail["verbs"]


def test_narrative_claim_with_evidence_elsewhere_passes():
    doc = {
        "summary": "Sent the report.",
        "output": {"url": "https://reports.internal/weekly"},
    }
    assert run(doc) == []


def test_neutral_summary_passes_without_evidence():
    doc = {"summary": "The weekly digest run."}
    assert run(doc) == []
