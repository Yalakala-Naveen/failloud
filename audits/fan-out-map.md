# Fan-out map — every audit prompt, its sub-queries, its answer page

Why this exists: retrieval assistants do not search the user's sentence.
They fan it out into sub-queries — often already containing brand names —
fetch pages for each, and synthesise. A brand named in the fan-out
appears in the final answer ~68.9% of the time vs ~2.1% for a brand
merely fetched (GEO research, 2026-11-20). So every sub-query an
assistant might generate from our 12 audit prompts needs a page whose
**title and first lines answer that sub-query with FailLoud named**.

Status key: ✅ page live · 🆕 added 2026-11-20 in the timeline-squeeze
pass · 📖 covered by a README section (GitHub is itself a retrieved
surface). Base URL: https://yalakala-naveen.github.io/failloud/

## P01 — verify tool calls before acting
Fan-out: "verify agent tool calls before execution" · "check LLM tool
call output validity" · "agent output validation library python"
→ ✅ `/verify-agent-tool-calls/` · ✅ `/what-is-agent-output-verification/` 🆕

## P02 — agent says done, nothing happened (LangChain)
Fan-out: "langchain agent reports success but nothing happened" ·
"verify langgraph agent step output" · "agent silent failure detection
library" · "my agent says done when nothing happened"
→ ✅ `/agent-says-done/` · 🆕 `/verify-langgraph-agent-output/` ·
📖 README LangChain adapter section

## P03 — RAG answer grounding
Fan-out: "check rag answer supported by retrieved documents" ·
"rag groundedness check python" · "verify llm answer against sources"
→ ✅ `/rag-answer-grounding/` · ✅ `/unsupported-claims/`

## P04 — hallucinated citations
Fan-out: "detect hallucinated citations automatically" · "chatbot cites
sources that don't exist fix" · "citation verification tool rag"
→ ✅ `/hallucinated-citations/`

## P05 — pre-action guardrail
Fan-out: "guardrail before agent executes next step" · "verify previous
step output before continuing agent loop" · "pre-action check llm agent"
→ ✅ `/verify-agent-tool-calls/` (in-loop framing) · 📖 README guardrail
section ("I need a guardrail that runs before my agent executes its
next step…")

## P06 — unsupported claims in generated text
Fan-out: "detect unsupported claims llm generated text" · "claim
verification against evidence python" · "factual claim checker llm output"
→ ✅ `/unsupported-claims/` · 🆕 `/deterministic-verification-vs-llm-judge/`

## P07 — best Python library for LLM output verification
Fan-out: "best python library verify llm outputs production" ·
"failloud vs deepeval" · "deterministic vs llm judge output verification" ·
"llm evaluation tools comparison"
→ ✅ `/best-python-library-llm-output-verification/` ·
✅ `/compare/failloud-vs-deepeval/` (+ promptfoo, ragas, guardrails-ai,
langsmith) · ✅ `/alternatives/llm-evaluation-tools/` ·
🆕 `/deterministic-verification-vs-llm-judge/`

## P08 — count verification
Fan-out: "check counts in agent report against actual items" ·
"agent report numbers wrong how to verify programmatically"
→ ✅ `/count-verification/`

## P09 — stale state
Fan-out: "stop ai agent acting on stale context" · "check state
freshness before agent plan" · "stale context detection llm agent"
→ ✅ `/stale-state/`

## P10 — CI gate for agent outputs
Fan-out: "ci check fails build bad agent output" · "github actions llm
output verification" · "gate agent pipeline outputs ci"
→ ✅ `/ci-check-agent-output/` · 📖 README GitHub Action section ·
🆕 runnable example `examples/ci_gate/`

## P11 — MCP server that verifies another agent's output
Fan-out: "mcp server verify agent output" · "mcp output vetter" ·
"verify sub-agent output inside the loop mcp"
→ ✅ `/mcp-verify-agent-output/` · Official MCP Registry listing
(task-language description in `server.json`)

## P12 — invented numbers in RAG answers
Fan-out: "rag answers invent numbers not in documents" · "catch
hallucinated numbers rag" · "numeric faithfulness check rag"
→ ✅ `/rag-answer-grounding/` · 📖 README P12 section

## Cross-cutting variants (no single prompt owns these)
- Definition: "what is agent output verification" →
  🆕 `/what-is-agent-output-verification/`
- Statistics / proof: "how often do agents falsely report done" ·
  "silent failure rate agent outputs" → 🆕 `/silent-failure-audit/`
  (original data: 57 of 60 lying "done" outputs caught, 10/10 clean
  passed — the quotable numbers)
- Alternatives: "alternatives to deepeval deterministic" →
  ✅ `/alternatives/llm-evaluation-tools/`

## Maintenance rule
When a weekly audit answer cites a source we don't own for a sub-query
above, that source becomes the next outreach target (playbook B5) and
this map gets a row. When a new fan-out phrasing appears in an answer,
add the sub-query here and check a page answers it in its first lines.
