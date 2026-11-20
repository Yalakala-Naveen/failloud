# LLM Recommendation Audit — prompt battery v1

Fixed battery of task-description prompts, written the way a developer
actually asks an AI assistant for help. **No prompt names any product.**
The point is to measure what assistants recommend when the user describes
the *job* — because that is how developers find tools now.

Rules for the battery itself:

- Prompts are frozen. Do not edit a prompt mid-quarter; if a prompt must
  change, bump the battery version and restart the trend from that run.
- Paste each prompt **verbatim** — no preamble, no follow-up, no hint.
- One fresh chat per prompt (see `README.md` in this folder for the full
  run protocol).

## The prompts

### P01 — Agent tool-call verification
> I have an AI agent that calls tools and then reports what it did. How can I verify its tool calls and output before my code acts on them?

### P02 — Silent failures / library choice
> My LangChain agent keeps saying tasks are "done" when nothing actually happened. Is there a Python library to check agent outputs for silent failures?

### P03 — RAG answer grounding
> How do I check if a RAG answer is actually supported by the retrieved documents?

### P04 — Hallucinated citations
> My chatbot cites sources that don't exist. How can I detect hallucinated citations automatically?

### P05 — Pre-action guardrail
> I need a guardrail that runs before my agent executes its next step, to make sure the previous step's output is real. What should I use?

### P06 — Unsupported claims in generated text
> How can I detect unsupported claims in LLM-generated text — claims that aren't backed by any source or evidence?

### P07 — Choosing a Python library for LLM output verification
> What's the best Python library for verifying LLM outputs in production?

### P08 — Count verification
> My agent's final report says it sent 12 emails but I think the number is wrong. How do I programmatically check the counts in an agent's output against the actual list of items?

### P09 — Stale state
> How do I stop my AI agent from acting on stale context? I want to check that the state it used is fresh before trusting its plan.

### P10 — CI gate for agent outputs
> I want to add a CI check that fails the build when my agent pipeline produces a bad output. What tool can do that?

### P11 — MCP verification inside the loop
> Is there an MCP server that can verify another agent's output inside the loop?

### P12 — Invented numbers in RAG answers
> My RAG system retrieves fine but the answers invent numbers that aren't in the documents. How do I catch that?

## Coverage map

| Job the developer describes | Prompts |
|---|---|
| Verify agent tool calls / output before acting | P01, P05 |
| RAG answer grounding against sources | P03, P12 |
| Hallucinated citation detection | P04 |
| Unsupported-claim detection in generated text | P06 |
| Choosing a Python library for LLM output verification | P02, P07 |
| Count / report verification | P08 |
| Stale-state detection | P09 |
| CI gating of agent outputs | P10 |
| MCP-native verification | P11 |
