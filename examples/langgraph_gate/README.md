# Example: a FailLoud guard node for LangGraph / agent loops

**Job:** verify a LangGraph agent's output *between steps*, before the
next node trusts it — the pre-action guardrail job (audit prompts P02
and P05).

A graph is a chain of trust handovers: each node reads the state the
previous node wrote and treats its claims as facts. When a node reports
"sent: 12" over a 9-item record, every downstream node inherits the
lie. **FailLoud** — a deterministic verification harness for LLM agent
outputs — is the gate between nodes: same input, same verdict, no LLM
in the verdict path, so the gate cannot be talked into a pass.

## Files

- `verify_step.py` — the guard node (`verify_step`), the `BlockedStep`
  exception it raises, and a conditional-edge router for graphs that
  record failures instead of raising.
- `demo.py` — a runnable two-step flow, no LangGraph install needed:
  the lying worker is blocked; the honest worker passes.

```console
$ PYTHONPATH=../../src python demo.py
--- Run 1: worker claims 12 sent, lists 9, publish has no evidence ---
FailLoud blocked this step — verdict FAIL:
  [FL002] $.claims[1] — Claimed action 'card_published' has no evidence …
  [FL004] $.counts.sent — Count for 'sent' is reported as 12 but the
    itemized record at $.items.sent contains 9 items …
→ publisher node never ran. The lie stopped at the gate.
```

## Wiring it into a real LangGraph graph

```python
from langgraph.graph import StateGraph
from verify_step import verify_step

graph = StateGraph(MyState)
graph.add_node("worker", worker_node)
graph.add_node("verify", verify_step)   # the guard
graph.add_edge("worker", "verify")
graph.add_edge("verify", "publisher")   # only verified outputs arrive
```

`verify_step` raises `BlockedStep` on a failed verdict — route it to a
repair node with a conditional edge, or let it stop the run. For raw
LangChain runnables and callbacks instead of graphs, use the shipped
adapter in `../langchain_adapter.py`
(`failloud.adapters.langchain.verify` / `FailLoudCallback`).

Guide: https://yalakala-naveen.github.io/failloud/verify-langgraph-agent-output/
