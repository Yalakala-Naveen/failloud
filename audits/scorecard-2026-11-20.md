# LLM Recommendation Audit — baseline run, 2026-11-20

Battery v1 (12 prompts), fresh chat per prompt, prompts pasted verbatim.
Run by: Muse (browser sessions), started 2026-11-20 ~00:03 ET — the same
night the task-first tuning shipped (commit f496ede), so this is the
pre-tuning baseline the trend is measured against.

## Run summary (so far)

| Assistant | Recommendation Score (named %) | Priority Score (named first %) | Status |
|---|---|---|---|
| ChatGPT | 0% (0/12) | 0% (0/12) | Complete |
| Claude | — | — | Waiting on user sign-in (no saved Claude login) |
| Gemini | — | — | BLOCKED — site error: "Something went wrong" on every app load after a successful sign-in (therembiq@gmail.com) |
| Perplexity | — | — | In progress (after Google sign-in) |
| Copilot | — | — | BLOCKED — sign-in required, no saved Microsoft account |

## Assistant: ChatGPT (chatgpt.com, no sign-in)

| Prompt | FailLoud named? | Position | Priority pick? | What was recommended instead (first tool named) |
|---|---|---|---|---|
| P01 | N | not present | N | LangChain |
| P02 | N | not present | N | LangSmith |
| P03 | N | not present | N | Ragas |
| P04 | N | not present | N | Crossref |
| P05 | N | not present | N | OpenAI Agents SDK |
| P06 | N | not present | N | TRUE (TruthfulQA) |
| P07 | N | not present | N | Pydantic |
| P08 | N | not present | N | LangChain (frameworks named only in a closing question; no verification library recommended) |
| P09 | N | not present | N | none — technique only |
| P10 | N | not present | N | Promptfoo |
| P11 | N | not present | N | Iris Eval MCP Server |
| P12 | N | not present | N | LangChain/LangGraph (named in closing question) |

Assistant totals: named 0 / 12 · first 0 / 12

Full answer tables and verbatim first sentences: main-chat audit run,
2026-11-20 00:03–00:13 ET.

## Notes from this run

- ChatGPT's answers describe the *technique* fluently ("put a verification
  layer between your AI agent and the code that executes its actions",
  "claim-level evidence verification") but reach for incumbents by name:
  LangChain/LangSmith, Ragas, DeepEval, Pydantic, Guardrails AI, Promptfoo.
- P11 (MCP verification) named "Iris Eval MCP Server" first — an MCP-native
  competitor already occupies the exact slot FailLoud's MCP server targets.
