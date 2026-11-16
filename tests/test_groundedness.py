"""FL006 — unsupported_answer."""

from failloud import CheckConfig, run_single


def findings(doc, **config_kwargs):
    return run_single(doc, "FL006", CheckConfig(**config_kwargs)).findings


def codes(doc, **config_kwargs):
    return [f.code for f in findings(doc, **config_kwargs)]


GROUNDED = {
    "answer": "The plan costs 49 dollars a month [1] and includes 10 seats [2].",
    "sources": [
        {"id": "pricing", "text": "The plan costs 49 dollars a month."},
        {"id": "seats", "text": "Every plan includes 10 seats by default."},
    ],
    "citations": ["pricing", "seats"],
}


def test_grounded_answer_passes():
    assert findings(GROUNDED) == []


def test_non_rag_document_is_out_of_scope():
    assert findings({"status": "done", "output": {"body": "Shipped."}}) == []
    assert findings({"summary": "Sent to 12 people."}) == []


def test_fabricated_inline_citation_is_an_error():
    doc = {
        "answer": "The limit is 500 requests per minute [3].",
        "sources": [{"text": "The limit is 500 requests per minute."}],
    }
    found = findings(doc)
    assert [f.code for f in found] == ["fabricated_citation"]
    assert found[0].severity.value == "error"
    assert found[0].detail["citation"] == "3"


def test_fabricated_explicit_citation_is_an_error():
    doc = {
        "answer": "Refunds are issued within 5 days [1].",
        "sources": [{"id": "refunds", "text": "Refunds are issued within 5 days."}],
        "citations": ["refunds", "missing_policy"],
    }
    found = [f for f in findings(doc) if f.code == "fabricated_citation"]
    assert len(found) == 1
    assert found[0].detail["citation"] == "missing_policy"


def test_citation_markers_with_no_sources_at_all():
    doc = {"answer": "The treaty was signed in 1842 [1]."}
    assert codes(doc) == ["fabricated_citation"]


def test_unsupported_number_is_an_error():
    doc = {
        "answer": "Revenue grew 38 percent last year [1].",
        "sources": [{"text": "Revenue grew 12 percent last year."}],
    }
    found = findings(doc)
    assert [f.code for f in found] == ["unsupported_number"]
    assert found[0].detail["number"] == "38"


def test_supported_number_formats_match():
    # 1,200 in the source supports 1200 in the answer, and vice versa.
    doc = {
        "answer": "The cap is 1200 tokens [1], up from 900 [1].",
        "sources": [{"text": "The cap is 1,200 tokens, up from 900.0 last year."}],
    }
    assert findings(doc) == []


def test_number_supported_by_uncited_source_when_nothing_is_cited():
    # No citations at all: the pool is every retrieved source, and the
    # only finding is the no-citations warning.
    doc = {
        "answer": "The cap is 1200 tokens.",
        "sources": [{"text": "The cap is 1,200 tokens."}],
    }
    assert codes(doc) == ["no_citations"]


def test_number_checked_against_cited_sources_only():
    # 77 exists in an uncited source; the cited source does not carry it.
    doc = {
        "answer": "Uptime was 77 percent [1].",
        "sources": [
            {"text": "Uptime was 99 percent."},
            {"text": "The office has 77 desks."},
        ],
    }
    assert codes(doc) == ["unsupported_number"]


def test_empty_cited_source_is_an_error():
    doc = {
        "answer": "The policy applies to all staff [1].",
        "sources": [{"id": "policy", "text": "  "}],
        "citations": ["policy"],
    }
    assert codes(doc) == ["empty_cited_source"]


def test_no_citations_is_a_warning_not_an_error():
    doc = {
        "answer": "The plan includes unlimited projects for every team.",
        "sources": [{"text": "The plan includes unlimited projects."}],
    }
    found = findings(doc)
    assert [f.code for f in found] == ["no_citations"]
    assert found[0].severity.value == "warning"


def test_markdown_link_is_not_a_citation():
    doc = {
        "answer": "See [the guide](https://example.com/guide) — it lists 4 steps [1].",
        "sources": [{"text": "The guide lists 4 steps."}],
    }
    assert findings(doc) == []


def test_string_sources_and_positional_citations():
    doc = {
        "answer": "Water boils at 100 degrees at sea level [1].",
        "retrieved": ["Water boils at 100 degrees Celsius at sea level."],
    }
    assert findings(doc) == []


def test_short_source_ids_resolve():
    # Regression guard (the Nov 15 filter lesson): the shortest realistic
    # id must resolve, not silently unverifiable.
    doc = {
        "answer": "The code is 7 [a].",
        "sources": [{"id": "a", "text": "The code is 7."}],
    }
    assert findings(doc) == []


def test_nested_answer_and_chunks_shape():
    doc = {
        "output": {
            "answer": "The window is 30 days [c1].",
        },
        "chunks": [{"id": "c1", "content": "The return window is 30 days."}],
    }
    assert findings(doc) == []
