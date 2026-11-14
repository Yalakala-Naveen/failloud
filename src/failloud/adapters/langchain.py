"""LangChain adapter: verify LangChain outputs in the loop.

Until now FailLoud verified files: an agent wrote JSON somewhere, and
``failloud check`` / ``watch`` read it back. LangChain agents rarely work
that way — their outputs live in memory as message objects, ``LLMResult``s,
and chain result dicts, and by the time anyone serializes them the run is
already over and the "done" has already propagated.

This adapter closes that gap with the smallest surface that proves the
pattern:

- :func:`to_failloud_doc` normalizes the shapes LangChain actually
  returns — a bare string, a message (dict or object), a list/dict of
  messages, an ``LLMResult``-like object with ``generations``, a chain
  result dict (``output`` / ``text`` / ``result`` / ``answer`` keys), an
  agent-finish object — into the FailLoud envelope, so the five checks
  run on it unchanged.
- :func:`verify` is the one-call version: normalize, then check.
- :class:`FailLoudCallbackHandler` plugs into LangChain's callback
  system (``on_llm_end`` / ``on_chain_end`` / ``on_agent_finish``), so
  every completed step is verified as it finishes, inside the loop,
  before the next step acts on it.

Zero-dependency, like the core: nothing here imports LangChain. Messages
and results are read by duck typing (``content``, ``type``, ``generations``,
class names), so the adapter works with any LangChain version — and with
plain dicts/strings in tests and other frameworks that mimic the shapes.
When ``langchain_core`` *is* installed, the handler additionally
subclasses its ``BaseCallbackHandler`` so LangChain's callback manager
accepts it everywhere a built-in handler is accepted.
"""

from __future__ import annotations

from typing import Any, Callable

from ..engine import run_checks
from ..models import CheckConfig, CheckResult

try:  # Optional: subclass the real base class when LangChain is present.
    from langchain_core.callbacks import BaseCallbackHandler as _Base
except Exception:  # pragma: no cover - exercised only without langchain
    _Base = object  # type: ignore[assignment,misc]


class FailLoudVerificationError(RuntimeError):
    """Raised by the callback handler (``raise_on_fail=True``) when a
    LangChain step's output fails verification. Carries the full
    :class:`~failloud.models.CheckResult` on ``.result``."""

    def __init__(self, result: CheckResult) -> None:
        self.result = result
        summary = "; ".join(
            f"{f.check_id} {f.path}: {f.message}" for f in result.errors
        )
        super().__init__(f"FailLoud verification failed: {summary}")


def _content_text(content: Any) -> str:
    """Flatten a message ``content`` value to plain text.

    Content is a string in the common case; multimodal messages carry a
    list of blocks (``{"type": "text", "text": ...}``) — text blocks are
    joined, non-text blocks contribute nothing (they carry no claim the
    text checks can judge, and inventing text for them would be worse).
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return str(content)


def message_text(message: Any) -> str:
    """Extract the text of one message, dict- or object-shaped."""
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        return _content_text(message.get("content", message.get("text", "")))
    return _content_text(getattr(message, "content", ""))


def _message_role(message: Any) -> str:
    """Best-effort role/type of a message, dict- or object-shaped."""
    if isinstance(message, dict):
        return str(message.get("type") or message.get("role") or "message")
    return str(
        getattr(message, "type", None)
        or type(message).__name__.replace("Message", "").lower()
        or "message"
    )


def _is_assistant(message: Any) -> bool:
    return _message_role(message) in ("ai", "assistant", "aimessage", "chat")


def _tool_calls_of(message: Any) -> list[Any]:
    if isinstance(message, dict):
        calls = message.get("tool_calls") or message.get("additional_kwargs", {}).get(
            "tool_calls"
        )
    else:
        calls = getattr(message, "tool_calls", None)
    return list(calls) if calls else []


def _generations_text(raw: Any) -> str | None:
    """Text of the first generation of an LLMResult-like object/dict."""
    generations = (
        raw.get("generations") if isinstance(raw, dict) else getattr(raw, "generations", None)
    )
    if not generations:
        return None
    first = generations[0]
    if isinstance(first, (list, tuple)):
        if not first:
            return ""
        first = first[0]
    if isinstance(first, dict):
        if first.get("message") is not None:
            return message_text(first["message"])
        return _content_text(first.get("text", ""))
    text = getattr(first, "text", None)
    if isinstance(text, str):
        return text
    message = getattr(first, "message", None)
    return message_text(message) if message is not None else ""


def to_failloud_doc(
    raw: Any,
    *,
    task: str | None = None,
    status: str = "done",
) -> dict[str, Any]:
    """Normalize a LangChain output into a FailLoud envelope document.

    The envelope always carries ``status`` and ``output.body`` (the final
    assistant text — the payload the placeholder/completeness checks
    judge), plus ``framework: "langchain"``. A message transcript also
    yields ``counts.messages`` + ``items.messages`` (roles + text), which
    the count check can cross-verify, and any tool calls are preserved
    verbatim under ``tool_calls`` for inspection — they are *not* turned
    into claims: a tool call is an intention, not evidence, and FailLoud
    does not invent evidence for it.

    A dict that already is a FailLoud envelope (it has an ``output``,
    ``claims``, or ``counts`` key of its own) passes through with its own
    fields winning; the adapter only fills in what is missing.
    """
    doc: dict[str, Any] = {"status": status, "framework": "langchain"}
    if task is not None:
        doc["task"] = task

    # Already an envelope (or a chain dict carrying one): respect it.
    if isinstance(raw, dict) and any(k in raw for k in ("output", "claims", "counts")):
        merged = dict(raw)
        for key, value in doc.items():
            merged.setdefault(key, value)
        if isinstance(merged.get("output"), str):
            merged["output"] = {"body": merged["output"]}
        return merged

    # A bare string is a complete (if minimal) agent output.
    if isinstance(raw, str):
        doc["output"] = {"body": raw}
        return doc

    # LLMResult-like: generations decide.
    generations_text = _generations_text(raw)
    if generations_text is not None:
        doc["output"] = {"body": generations_text}
        return doc

    # Message transcript: dict with messages, a list, or an object with
    # a .messages attribute (several chain/agent result shapes).
    messages: Any = None
    if isinstance(raw, dict):
        messages = raw.get("messages")
    elif isinstance(raw, (list, tuple)):
        messages = raw
    else:
        messages = getattr(raw, "messages", None)
    if messages:
        messages = list(messages)
        items = [
            {"role": _message_role(m), "text": message_text(m)} for m in messages
        ]
        body = ""
        for message in reversed(messages):
            if _is_assistant(message) and message_text(message):
                body = message_text(message)
                break
        if not body and messages:
            body = message_text(messages[-1])
        doc["output"] = {"body": body}
        doc["counts"] = {"messages": len(messages)}
        doc["items"] = {"messages": items}
        tool_calls = [call for m in messages for call in _tool_calls_of(m)]
        if tool_calls:
            doc["tool_calls"] = tool_calls
        return doc

    # A single message object.
    if not isinstance(raw, dict) and (
        hasattr(raw, "content") or hasattr(raw, "return_values")
    ):
        if hasattr(raw, "return_values"):  # AgentFinish-like
            values = raw.return_values or {}
            text = values.get("output", "") if isinstance(values, dict) else ""
            doc["output"] = {"body": _content_text(text)}
            return doc
        doc["output"] = {"body": message_text(raw)}
        return doc

    # Chain result dicts: output / text / result / answer keys.
    if isinstance(raw, dict):
        for key in ("output", "text", "result", "answer"):
            if isinstance(raw.get(key), str):
                doc["output"] = {"body": raw[key]}
                return doc
        doc["output"] = {"body": ""}
        return doc

    doc["output"] = {"body": _content_text(raw)}
    return doc


def verify(raw: Any, config: CheckConfig | None = None, **doc_kwargs: Any) -> CheckResult:
    """Normalize *raw* and run every FailLoud check over it."""
    return run_checks(to_failloud_doc(raw, **doc_kwargs), config)


class FailLoudCallbackHandler(_Base):  # type: ignore[valid-type,misc]
    """LangChain callback handler that verifies each finished step.

    Usage::

        handler = FailLoudCallbackHandler()
        chain.invoke(inputs, config={"callbacks": [handler]})
        handler.last_result.verdict        # "PASS" / "FAIL" / ...
        handler.results                    # every verdict, in order

    With ``raise_on_fail=True`` a failing step raises
    :class:`FailLoudVerificationError` from inside the callback, so the
    chain stops instead of building on a silent failure. ``on_result``,
    when given, is called with each :class:`CheckResult` as it lands.
    """

    def __init__(
        self,
        config: CheckConfig | None = None,
        *,
        raise_on_fail: bool = False,
        on_result: Callable[[CheckResult], None] | None = None,
    ) -> None:
        try:
            super().__init__()
        except Exception:
            pass
        self.config = config
        self.raise_on_fail = raise_on_fail
        self.on_result = on_result
        self.results: list[CheckResult] = []
        self.last_doc: dict[str, Any] | None = None

    @property
    def last_result(self) -> CheckResult | None:
        return self.results[-1] if self.results else None

    def _record(self, raw: Any) -> CheckResult:
        doc = to_failloud_doc(raw)
        result = run_checks(doc, self.config)
        self.last_doc = doc
        self.results.append(result)
        if self.on_result is not None:
            self.on_result(result)
        if self.raise_on_fail and not result.passed:
            raise FailLoudVerificationError(result)
        return result

    # -- LangChain callback surface ------------------------------------
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        self._record(response)

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        self._record(outputs)

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        self._record(finish)
