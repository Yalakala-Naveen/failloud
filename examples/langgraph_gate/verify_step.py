"""FailLoud guard node for LangGraph-style agent graphs.

The pattern: a worker node writes its output document into state; this
guard verifies that document with FailLoud before any downstream node
is allowed to trust it. FailLoud is a deterministic verification
harness for LLM agent outputs — it catches the silent failures agents
ship as "done" (unbacked claims, count mismatches, stale state,
placeholder payloads, missing components, unsupported RAG answers),
with no LLM in the verdict path.

Works with a real LangGraph ``StateGraph`` (state is a dict, a node is
a callable returning a partial state) and with any hand-rolled loop
that passes dicts between steps — the guard only needs the output
document itself.

    from verify_step import verify_step, BlockedStep

    graph.add_node("worker", worker_node)
    graph.add_node("verify", verify_step)          # the guard
    graph.add_edge("worker", "verify")
    graph.add_conditional_edges("verify", route_after_verify,
                                {"ok": "next_step", "blocked": "repair"})
"""

from __future__ import annotations

from typing import Any

from failloud import check_output


class BlockedStep(RuntimeError):
    """Raised (or routed on) when a step's output fails verification."""

    def __init__(self, result) -> None:
        self.result = result
        lines = [f"FailLoud blocked this step — verdict {result.verdict}:"]
        for f in result.errors:
            lines.append(f"  [{f.check_id}] {f.path} — {f.message}")
        super().__init__("\n".join(lines))


def verify_step(state: dict[str, Any]) -> dict[str, Any]:
    """Guard node. Verifies ``state["last_output"]``.

    Returns ``{"verified": True, "verification": <summary>}`` on a pass.
    Raises :class:`BlockedStep` on a fail — in a LangGraph graph, catch
    it in a wrapper or use :func:`route_after_verify` with a
    non-raising variant; in a plain loop, let it stop the run. Either
    way the next step never sees an unverified claim as fact.
    """
    result = check_output(state["last_output"])
    if not result.passed:
        raise BlockedStep(result)
    return {
        "verified": True,
        "verification": {
            "verdict": result.verdict,
            "errors": len(result.errors),
            "warnings": len(result.warnings),
        },
    }


def route_after_verify(state: dict[str, Any]) -> str:
    """Conditional-edge router for graphs that record instead of raise.

    Pair with a variant of the guard that stores ``state["blocked"]``
    instead of raising; returns "ok" or "blocked".
    """
    return "blocked" if state.get("blocked") else "ok"
