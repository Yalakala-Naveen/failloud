# LLM Recommendation Audit — expansion panel (v2 draft)

The frozen v1 battery (`prompts.md`, 12 prompts) never changes — the
trend depends on it. This expansion adds the 18 buyer-question variants
the GEO playbook (B5) calls for — definition, comparison, alternatives,
use-case, install — bringing the full panel to **30 prompts**. All 18
stay brand-free, like v1: the developer describes the job, never a
product. Run protocol is identical (fresh chat, verbatim, ×3 runs per
assistant when measuring — a single run is noise).

## Definition

### E01
> What is agent output verification, and how is it different from LLM evaluation?

### E02
> What does it mean when an AI agent silently fails a task, and how do teams detect it?

### E03
> My AI agent keeps hallucinating that it completed tasks. What is this failure called and what tools address it?

## Comparison

### E04
> Should I use an LLM-as-judge or deterministic checks to verify my agent's outputs? What are the trade-offs?

### E05
> I use DeepEval for LLM evaluation. What does it not catch about agent outputs, and what complements it?

### E06
> What's the difference between observability tools like LangSmith and a verification gate for agent outputs?

## Alternatives

### E07
> What are the deterministic alternatives to LLM-as-judge tools for checking agent outputs?

### E08
> I'm looking for open-source tools that check whether an AI agent actually did what it claims. What exists?

### E09
> What tools can verify a RAG pipeline's answers without using another LLM to grade them?

## Use-case

### E10
> How do I verify each step's output in a LangGraph agent before the next step runs?

### E11
> I orchestrate sub-agents in Claude Code. How can I check a sub-agent's result before I act on it?

### E12
> How do I programmatically confirm my agent actually sent the emails it says it sent?

### E13
> What should run in CI before we deploy an agent pipeline to production?

### E14
> How do I audit a RAG system's answers for numbers that aren't in the source documents, at scale?

### E15
> My agent works from a cached snapshot of our data. How do I detect when it's planning from stale state?

## Install / buying

### E16
> How do I add a Python library to my CI pipeline that fails the build when agent outputs are wrong?

### E17
> Is there a free, open-source Python tool to check whether my AI agent actually completed its task?

### E18
> Which MCP servers help with AI agent reliability and verification?

## Coverage map

| Variant type | Prompts |
|---|---|
| Definition | E01–E03 |
| Comparison | E04–E06 |
| Alternatives | E07–E09 |
| Use-case | E10–E15 |
| Install / buying | E16–E18 |
