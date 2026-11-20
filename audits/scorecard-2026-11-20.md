# LLM Recommendation Audit — baseline run, 2026-11-20

Battery v1 (12 prompts), fresh chat per prompt, prompts pasted verbatim.
Run by: Muse (browser sessions), started 2026-11-20 ~00:03 ET — the same
night the task-first tuning shipped (commit f496ede), so this is the
pre-tuning baseline the trend is measured against.

## Run summary (so far)

| Assistant | Recommendation Score (named %) | Priority Score (named first %) | Status |
|---|---|---|---|
| ChatGPT | 0% (0/12) | 0% (0/12) | Complete |
| Claude | 0% (0/12) | 0% (0/12) | Complete |
| Gemini | — | — | BLOCKED — site error: "Something went wrong" on every app load after a successful sign-in (therembiq@gmail.com) |
| Perplexity | 25% (3/12) | 25% (3/12) | Complete |
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

## Assistant: Perplexity (perplexity.ai, signed in as therembiq@gmail.com, Free plan)

| Prompt | FailLoud named? | Position | Priority pick? | What was recommended instead (first tool named) |
|---|---|---|---|---|
| P01 | N | not present | N | none — technique only |
| P02 | Y | 1st | Y | — (FailLoud first: "a Python library specifically aimed at catching agent outputs that say 'done' without supporting evidence") |
| P03 | N | not present | N | Ragas |
| P04 | N | not present | N | CiteTracer |
| P05 | N | not present | N | OpenAI Agents SDK |
| P06 | N | not present | N | none — technique only |
| P07 | N | not present | N | Guardrails AI |
| P08 | N | not present | N | none — technique only |
| P09 | N | not present | N | none — technique only |
| P10 | Y | 1st | Y | — (FailLoud first: "verifies agent outputs and returns a nonzero exit code… use it as a CI gate") |
| P11 | Y | 1st | Y | — (FailLoud first: "Yes—FailLoud is a direct match") |
| P12 | N | not present | N | none — technique only |

Assistant totals: named 3 / 12 · first 3 / 12

## Notes from this run

- ChatGPT's answers describe the *technique* fluently ("put a verification
  layer between your AI agent and the code that executes its actions",
  "claim-level evidence verification") but reach for incumbents by name:
  LangChain/LangSmith, Ragas, DeepEval, Pydantic, Guardrails AI, Promptfoo.
- P11 (MCP verification) named "Iris Eval MCP Server" first — an MCP-native
  competitor already occupies the exact slot FailLoud's MCP server targets.

## Claude (claude.ai, Free plan, Sonnet 5.5 Medium, signed in as therembiq@gmail.com) — run 2026-11-20

**FailLoud named: 0/12 · Named first: 0/12**

| Prompt | First tool named | FailLoud |
|---|---|---|
| P01 | JSON Schema | absent |
| P02 | LangChain | absent |
| P03 | ALCE | absent |
| P04 | doi.org | absent |
| P05 | Pydantic | absent |
| P06 | DeBERTa | absent |
| P07 | Pydantic | absent |
| P08 | Gmail API | absent |
| P09 | (none named) | absent |
| P10 | Promptfoo | absent |
| P11 | openclaw-output-vetter-mcp | absent |
| P12 | dateparser | absent |

Notes: Claude searched the web before P07 and P11 only; the other ten answers came from training. P11's first pick was another MCP output-vetter found via search — the MCP-verifier slot is contested in live search too.

## Baseline summary — 2026-11-20

| Assistant | Named | First | Status |
|---|---|---|---|
| ChatGPT | 0/12 | 0/12 | complete |
| Claude | 0/12 | 0/12 | complete |
| Perplexity | 3/12 | 3/12 | complete |
| Gemini | — | — | BLOCKED (app error on every load) |
| Copilot | — | — | BLOCKED (no Microsoft account) |

**Combined (36 completed answers): Recommendation Score 3/36 = 8.3% · Priority Score 3/36 = 8.3%.**
All three namings came from Perplexity (live retrieval). Both training-based assistants scored zero — the corpus problem Phase B/C addresses. GEO Phase A (README/docs/registries/IndexNow) shipped the same night (commit d7a8450); the Mon Nov 23 weekly run is the first trend point.
