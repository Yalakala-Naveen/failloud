"""LangChain adapter: normalization, in-loop verification, callback handler.

The adapter is duck-typed, so the tests use plain dicts and small stand-in
objects with the same attribute shapes LangChain produces (``content`` /
``type`` on messages, ``generations`` on LLM results, ``return_values``
on agent finishes) — no LangChain install required, which is itself the
zero-dependency property under test.

Properties under test:
- Every common LangChain output shape normalizes to an envelope whose
  ``output.body`` is the final assistant text.
- Silent failures are caught *through* the adapter: a placeholder final
  message FAILs exactly as the same text in a file would.
- Tool calls are preserved for inspection, never promoted to claims.
- The callback handler records a verdict per finished step and, with
  ``raise_on_fail``, stops the chain on a failing step.
"""

import pytest

from failloud.adapters.langchain import (
    FailLoudCallbackHandler,
    FailLoudVerificationError,
    message_text,
    to_failloud_doc,
    verify,
)


class FakeMessage:
    """Stand-in for a LangChain BaseMessage (attribute-shaped)."""

    def __init__(self, content, type="ai", tool_calls=None):
        self.content = content
        self.type = type
        self.tool_calls = tool_calls or []


class FakeGeneration:
    def __init__(self, text=None, message=None):
        self.text = text
        self.message = message


class FakeLLMResult:
    def __init__(self, generations):
        self.generations = generations


class FakeAgentFinish:
    def __init__(self, output):
        self.return_values = {"output": output}


# -- message_text ------------------------------------------------------------


def test_message_text_from_dict_and_object_and_blocks():
    assert message_text({"content": "hello"}) == "hello"
    assert message_text(FakeMessage("world")) == "world"
    blocks = {"content": [{"type": "text", "text": "a"}, {"type": "image"}]}
    assert message_text(blocks) == "a"
    assert message_text("plain") == "plain"


# -- to_failloud_doc ---------------------------------------------------------


def test_bare_string_becomes_body():
    doc = to_failloud_doc("Finished the report.")
    assert doc["output"]["body"] == "Finished the report."
    assert doc["status"] == "done" and doc["framework"] == "langchain"


def test_transcript_dict_uses_last_assistant_message():
    raw = {
        "messages": [
            {"type": "human", "content": "Summarize the run."},
            {"type": "ai", "content": "The run sent 9 emails."},
        ]
    }
    doc = to_failloud_doc(raw)
    assert doc["output"]["body"] == "The run sent 9 emails."
    assert doc["counts"]["messages"] == 2
    assert [m["role"] for m in doc["items"]["messages"]] == ["human", "ai"]


def test_transcript_of_message_objects():
    raw = [FakeMessage("Do it.", type="human"), FakeMessage("Done, for real.")]
    doc = to_failloud_doc(raw)
    assert doc["output"]["body"] == "Done, for real."
    assert doc["counts"]["messages"] == 2


def test_tool_calls_preserved_not_promoted_to_claims():
    call = {"name": "send_email", "args": {"to": "a@b.c"}, "id": "call_1"}
    raw = {"messages": [FakeMessage("", tool_calls=[call])]}
    doc = to_failloud_doc(raw)
    assert doc["tool_calls"] == [call]
    assert "claims" not in doc  # an intention is not evidence


def test_llm_result_generations_normalized():
    result = FakeLLMResult([[FakeGeneration(text="Generated answer.")]])
    assert to_failloud_doc(result)["output"]["body"] == "Generated answer."
    by_message = FakeLLMResult([[FakeGeneration(message=FakeMessage("Via message."))]])
    assert to_failloud_doc(by_message)["output"]["body"] == "Via message."


def test_chain_result_dict_keys():
    for key in ("output", "text", "result", "answer"):
        assert to_failloud_doc({key: "chain text"})["output"]["body"] == "chain text"


def test_agent_finish_return_values():
    doc = to_failloud_doc(FakeAgentFinish("Final answer."))
    assert doc["output"]["body"] == "Final answer."


def test_existing_envelope_passes_through_with_its_own_fields():
    envelope = {
        "status": "done",
        "output": {"body": "Real body."},
        "claims": [{"action": "email_sent", "evidence": {"message_id": "m1"}}],
    }
    doc = to_failloud_doc(envelope)
    assert doc["claims"] == envelope["claims"]
    assert doc["output"]["body"] == "Real body."


def test_task_label_is_carried_when_given():
    assert to_failloud_doc("x", task="weekly digest")["task"] == "weekly digest"


# -- verify -------------------------------------------------------------------


def test_verify_passes_a_real_answer():
    result = verify({"messages": [{"type": "ai", "content": "All 9 sent."}]})
    assert result.passed


def test_verify_catches_placeholder_shipped_through_langchain():
    raw = {"messages": [{"type": "ai", "content": "Coming soon — lorem ipsum."}]}
    result = verify(raw)
    assert not result.passed
    assert result.outcome_for("FL001").status == "fail"


def test_verify_catches_empty_final_message():
    result = verify([FakeMessage("prompt", type="human"), FakeMessage("")])
    assert not result.passed


# -- callback handler -----------------------------------------------------------


def test_handler_records_llm_and_chain_verdicts():
    handler = FailLoudCallbackHandler()
    handler.on_llm_end(FakeLLMResult([[FakeGeneration(text="Solid answer.")]]))
    handler.on_chain_end({"output": "Coming soon."})
    assert len(handler.results) == 2
    assert handler.results[0].passed
    assert not handler.results[1].passed
    assert handler.last_result is handler.results[1]
    assert handler.last_doc["framework"] == "langchain"


def test_handler_agent_finish():
    handler = FailLoudCallbackHandler()
    handler.on_agent_finish(FakeAgentFinish("Wrapped up, with receipts."))
    assert handler.last_result.passed


def test_handler_on_result_callback_fires():
    seen = []
    handler = FailLoudCallbackHandler(on_result=seen.append)
    handler.on_chain_end({"text": "ok, real"})
    assert len(seen) == 1 and seen[0] is handler.last_result


def test_handler_raise_on_fail_stops_the_chain():
    handler = FailLoudCallbackHandler(raise_on_fail=True)
    with pytest.raises(FailLoudVerificationError) as excinfo:
        handler.on_llm_end(FakeLLMResult([[FakeGeneration(text="Lorem ipsum.")]]))
    assert excinfo.value.result.outcome_for("FL001").status == "fail"
    assert len(handler.results) == 1  # the verdict is still recorded
