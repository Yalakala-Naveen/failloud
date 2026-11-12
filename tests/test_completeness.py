"""FL005 — missing_components."""

from failloud import CheckConfig, run_single


def run(doc, **config_kwargs):
    return run_single(doc, "FL005", CheckConfig(**config_kwargs)).findings


def codes(findings):
    return {f.code for f in findings}


def test_required_path_present_and_filled_passes():
    doc = {"output": {"url": "https://x.co/1", "body": "text"}}
    assert run(doc, required_paths=("output.url",)) == []


def test_required_path_missing_fails():
    doc = {"output": {"body": "text"}}
    findings = run(doc, required_paths=("output.url",))
    assert "missing_component" in codes(findings)
    assert any(f.severity.value == "error" for f in findings)


def test_required_path_empty_fails():
    doc = {"output": {"url": "", "body": "text"}}
    findings = run(doc, required_paths=("output.url",))
    assert "empty_component" in codes(findings)


def test_schema_required_fields_enforced_recursively():
    schema = {
        "required": ["output"],
        "properties": {"output": {"required": ["url", "body"]}},
    }
    doc = {"output": {"body": "text"}}
    findings = run(doc, schema=schema)
    assert "missing_component" in codes(findings)
    assert any(f.path == "$.output.url" for f in findings)


def test_schema_satisfied_passes():
    schema = {"properties": {"output": {"required": ["url"]}}}
    doc = {"output": {"url": "https://x.co/1"}}
    assert run(doc, schema=schema) == []


def test_empty_sibling_field_warns():
    doc = {"output": {"title": "Hi", "url": ""}}
    findings = run(doc)
    assert len(findings) == 1
    assert findings[0].code == "empty_field"
    assert findings[0].severity.value == "warning"


def test_legitimately_empty_fields_do_not_warn():
    doc = {"output": {"title": "Hi", "cc": [], "errors": []}}
    assert run(doc) == []


def test_zero_length_segment_fails():
    doc = {"segments": [{"start": 0, "end": 4}, {"start": 4, "end": 4}]}
    findings = run(doc)
    assert codes(findings) == {"zero_length_segment"}


def test_dead_stretch_fails():
    doc = {"segments": [{"start": 0, "end": 4}, {"start": 9, "end": 12}]}
    findings = run(doc)
    assert codes(findings) == {"dead_stretch"}
    assert findings[0].detail["gap_seconds"] == 5.0


def test_contiguous_segments_pass():
    doc = {"segments": [{"start": 0, "end": 4}, {"start": 4, "end": 9}, {"start": 9, "end": 12}]}
    assert run(doc) == []


def test_gap_threshold_is_configurable():
    doc = {"segments": [{"start": 0, "end": 4}, {"start": 5, "end": 8}]}
    assert run(doc) == []  # 1s gap, default limit 2s
    findings = run(doc, max_segment_gap_seconds=0.5)
    assert codes(findings) == {"dead_stretch"}


def test_duration_style_segments_supported():
    doc = {"segments": [{"start": 0, "duration": 4}, {"start": 4, "duration": 0}]}
    findings = run(doc)
    assert codes(findings) == {"zero_length_segment"}
