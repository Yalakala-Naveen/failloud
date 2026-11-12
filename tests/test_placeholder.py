"""FL001 — placeholder_shipped."""

from failloud import CheckConfig, run_single


def run(doc):
    return run_single(doc, "FL001", CheckConfig()).findings


def test_clean_completed_output_passes():
    doc = {"status": "done", "output": {"body": "Real, finished content."}}
    assert run(doc) == []


def test_lorem_ipsum_in_completed_output_fails():
    doc = {"status": "done", "output": {"body": "Lorem ipsum dolor sit amet."}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "placeholder_shipped"
    assert findings[0].path == "$.output.body"


def test_unrendered_template_braces_fail():
    doc = {"status": "done", "output": {"body": "Hello {{first_name}}, welcome."}}
    findings = run(doc)
    assert len(findings) == 1
    assert "{{" in findings[0].detail["matched"]


def test_empty_payload_with_done_status_fails():
    doc = {"status": "done", "output": {}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "empty_payload"


def test_no_payload_at_all_with_done_status_fails():
    doc = {"status": "done", "summary": "All finished."}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "empty_payload"


def test_payload_of_empty_fields_fails():
    doc = {"status": "done", "output": {"title": "", "body": None}}
    findings = run(doc)
    assert findings[0].code == "empty_payload"


def test_draft_is_allowed_placeholders():
    doc = {"status": "draft", "output": {"body": "{{first_name}} — TBD"}}
    assert run(doc) == []


def test_unlabelled_document_is_judged_as_final():
    doc = {"output": {"body": "Your page is coming soon."}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "placeholder_shipped"


def test_whole_value_placeholder_token_fails():
    doc = {"status": "done", "output": {"headline": "TBD", "body": "Real body."}}
    findings = run(doc)
    assert any(f.path == "$.output.headline" for f in findings)


def test_word_todo_inside_real_sentence_passes():
    # Only whole-value or scaffolding patterns count; honest prose is fine.
    doc = {"status": "done", "output": {"body": "We shipped the todo list feature."}}
    assert run(doc) == []
