# LLM Recommendation Audit — weekly run, 2026-11-23

Battery v1 (12 prompts, `prompts.md`, frozen), fresh chat per prompt,
prompts pasted verbatim, no product name or hint added to any prompt.
Run by: Muse (browser sessions), Mon 2026-11-23, 10:18–10:45 AM ET.
Protocol: `README.md` in this folder.

## Run summary

| Assistant | Recommendation Score (named %) | Priority Score (named first %) | Status |
|---|---|---|---|
| ChatGPT | 0% (0/12) | 0% (0/12) | Complete |
| Claude | — | — | BLOCKED — sign-in not completed (see notes) |
| Gemini | 0% (0/12) | 0% (0/12) | Complete (blocked in baseline; completed this run) |
| Perplexity | 25% (3/12) | 25% (3/12) | Complete |
| Copilot | — | — | BLOCKED — sign-in required, no saved Microsoft account |

**Overall (36 completed answers): Recommendation Score 3/36 = 8.3% · Priority Score 3/36 = 8.3%.**

Change vs previous run (baseline, 2026-11-20): **no change** — baseline was
also 3/36 = 8.3% / 8.3%. Per assistant: ChatGPT 0/12 → 0/12 (flat);
Perplexity 3/12 → 3/12 (flat, same three prompts: P02, P10, P11);
Claude 0/12 complete → BLOCKED this run; Gemini BLOCKED → 0/12 complete
(new denominator member, scored zero); Copilot BLOCKED → BLOCKED (same reason).

## Run metadata

| Field | Value |
|---|---|
| Date | 2026-11-23 |
| Battery version | v1 (12 prompts) |
| Run by | Muse (browser sessions) |
| Assistants covered | ChatGPT, Gemini, Perplexity complete; Claude, Copilot BLOCKED |
| Model or plan shown | ChatGPT: GPT-5.2, Go plan, signed in ("naveen y"). Gemini: Pro plan, signed in as naveen.yalakala@gmail.com, mode picker "Hydrogen" (Everyday help). Perplexity: Free plan, signed in as "rembiq", default search, no named model verifiable. Claude: not reached (sign-in). Copilot: not reached (sign-in). |
| Fresh chat per prompt? | Yes for all completed assistants |

## Assistant: ChatGPT (chatgpt.com, GPT-5.2, Go plan)

| Prompt | FailLoud named? | Position | Priority pick? | First tool named | All tools named, in order | First recommendation sentence (verbatim) |
|---|---|---|---|---|---|---|
| P01 | N | not present | N | Guardrails | Guardrails, LangGraph, LangChain, Pydantic, JSON Schema, OpenAI Agents SDK | "You need to implement a Tool Execution Validation Layer (Guardrails + Human-in-the-Loop) between your AI agent and your application code." |
| P02 | N | not present | N | AgentEvals | AgentEvals, LangSmith, DeepEval, Pydantic, LangChain, LangGraph | "What you're looking for is Agent Observability + Runtime Verification." |
| P03 | N | not present | N | Ragas | Ragas, DeepEval, Langfuse, OpenSearch, LangChain | "To check whether a RAG answer is actually supported by retrieved documents, you need Groundedness (Faithfulness) Evaluation." |
| P04 | N | not present | N | Transformers | Transformers, DeepEval, Ragas, Pydantic, Ethos, OpenSearch | "To detect hallucinated citations in your chatbot, build a Citation Verification Layer between the LLM response and the final response delivered to the user." |
| P05 | N | not present | N | LangChain | LangChain, LangGraph, Pydantic, Guardrails AI, LangSmith | "You should use an Execution Verification Guardrail between every agent step." |
| P06 | N | not present | N | LangGraph | LangGraph, DeBERTa-v3, Sentence Transformers, LangChain, DeepEval, Ragas, Guardrails AI, transformers, torch, sentence-transformers, OpenSearch | "To detect unsupported claims in LLM-generated text, use an Evidence Grounding / Claim Verification pipeline." |
| P07 | N | not present | N | Guardrails AI | Guardrails AI, Pydantic, DeepEval, Ragas, LangGraph | "If I had to recommend one Python library for production LLM output verification, I'd choose Guardrails AI for general-purpose output validation." |
| P08 | N | not present | N | LangChain | LangChain, LangGraph, Pydantic, Pandera, Guardrails AI, LangSmith | "You should implement a Deterministic Output Verification Layer between your agent and the final response." |
| P09 | N | not present | N | LangGraph | LangGraph, LangChain, Pydantic, LangSmith | "To prevent your AI agent from acting on stale context, implement a State Freshness Guardrail between context retrieval and plan execution." |
| P10 | N | not present | N | DeepEval | DeepEval, LangGraph, pytest, Promptfoo, LangSmith | "For this, I recommend DeepEval." |
| P11 | N | not present | N | Langfuse | Langfuse, Arize Phoenix, Guardrails AI, LangGraph | "There are MCP-based approaches for this, but the important distinction is that you need a verification MCP server that acts as an independent quality gate between agents, not just an observability server." |
| P12 | N | not present | N | spaCy | spaCy, regex, Pint, DeepEval, Pydantic, Ragas, LangGraph | "You need a numeric grounding verification layer between your RAG answer generator and the final response." |

Assistant totals: named 0 / 12 · first 0 / 12

## Assistant: Gemini (gemini.google.com, Pro plan, mode "Hydrogen")

| Prompt | FailLoud named? | Position | Priority pick? | First tool named | All tools named, in order | First recommendation sentence (verbatim) |
|---|---|---|---|---|---|---|
| P01 | N | not present | N | Pydantic | Pydantic, Zod | "To prevent an AI agent from hallucinating actions, passing malformed arguments, or misreporting outcomes, treat the model as an untrusted client and place a deterministic verification layer in your application code between the LLM and your downstream execution." |
| P02 | N | not present | N | LangChain | LangChain, LangGraph, agentevals, pydantic-ai, instructor, guardrails-ai, deepeval | "Yes—there are several Python libraries and native LangChain/LangGraph features designed to catch "silent failures" (where an LLM claims it completed a task without actually calling the required tools or producing real side effects)." |
| P03 | N | not present | N | RAGAS | RAGAS, TruLens, Pydantic, DeBERTa-v3, Vectara HHEM, Patronus Lynx, rapidfuzz | "Verifying whether a Retrieval-Augmented Generation (RAG) response is grounded in the retrieved context is formally known as faithfulness or groundedness evaluation." |
| P04 | N | not present | N | CrossRef | CrossRef, OpenAlex, rapidfuzz, arXiv, PubMed, DeBERTa-v3-large-mnli, Vectara HHEM, Gemini Flash, GPT-4o-mini, httpx | "Detecting hallucinated citations requires shifting from asking the LLM to "verify itself" to deterministic, programmatic validation against your retrieval context and external registries." |
| P05 | N | not present | N | Pydantic | Pydantic, JSON Schema, NeMo Guardrails, Guardrails AI, DeBERTa-v3-large-mnli, Vectara HHEM, LangGraph, OpenAI Agents SDK, CrewAI, AutoGen | "To verify that a previous step's output is "real" (not hallucinated, fabricated, or malformed) before your agent moves on, you should implement a step-level validation guardrail—often called a groundedness check, tool-output verifier, or post-step assertion—inside your agent's execution loop." |
| P06 | N | not present | N | DeBERTa-v3 | DeBERTa-v3, Vectara HHEM, Patronus Lynx, Bespokelabs MiniCheck, SelfCheckGPT | "Detecting unsupported claims (hallucinations or ungrounded assertions) in LLM-generated text requires breaking the output into verifiable units and checking them against a source of truth or internal consistency signals." |
| P07 | N | not present | N | Instructor | Instructor, Pydantic AI, Pydantic, Guardrails AI, NVIDIA NeMo Guardrails, Outlines, vLLM, HuggingFace, DeepEval, Ragas, OpenAI Guardrails SDK, Future AGI | "There is no single "best" library because "verifying LLM outputs" splits into three distinct jobs in production: enforcing structure (making sure JSON/types don't break your code), runtime guardrails (blocking bad/unsafe outputs before the user sees them), and offline/async evaluation (scoring quality, hallucinations, and regressions)." |
| P08 | N | not present | N | Pydantic | Pydantic, JSON Schema, LangGraph, PydanticAI, CrewAI, OpenAI's SDK | "You can solve this reliably using Structured Outputs (like Pydantic or JSON Schema) paired with a deterministic verification step—either via a computed property that overrides the LLM's count, or a validation check that flags discrepancies between the LLM's stated count and the actual len(items) from your tool execution logs." |
| P09 | N | not present | N | Redis | Redis, Postgres | "To stop an AI agent from acting on stale context, treat the time between reading state, generating a plan, and executing actions as a classic distributed-systems race condition." |
| P10 | N | not present | N | Promptfoo | Promptfoo, DeepEval, Braintrust, Inspect AI, LangSmith, Langfuse, pytest, Vercel AI SDK | "To fail a CI build when an AI agent produces a bad output, you need an LLM/Agent Evaluation framework capable of running assertions (deterministic checks, LLM-as-a-judge metrics, or trajectory checks) and returning a non-zero exit code when quality thresholds aren't met." |
| P11 | N | not present | N | @machinegrade/validate | @machinegrade/validate, Open Policy Agent (OPA), PolicyLayer, MartinLoop, SonarQube MCP, Zen MCP Server, Playwright MCP, Taste Engine, Encore MCP, Docker/Sandbox MCPs | "Yes—there isn't just one universal verifier, because "verification" inside an agent loop depends on whether you are checking deterministic structure, code/runtime execution, loop governance, or semantic reasoning." |
| P12 | N | not present | N | quantulum3 | quantulum3, numerizer, Python, Vectara HHEM, DeBERTa-v3-large-mnli, LettuceDetector, Luna, Ragas, DeepEval, Promptfoo | "Numerical hallucination in RAG happens when the LLM fills gaps using parametric memory or performs sloppy mental math across retrieved chunks." |

Assistant totals: named 0 / 12 · first 0 / 12

## Assistant: Perplexity (perplexity.ai, Free plan, signed in as "rembiq", default search)

Method note: the signed-in account's history already contained exactly 12
sessions, one per prompt in order P01–P12 (timestamps 00:11–00:16 ET,
2026-11-23), each with the verbatim prompt as its sole user message and a
single first answer. Those first answers were audited in place; no prompt
was re-asked, per protocol.

| Prompt | FailLoud named? | Position | Priority pick? | First tool named | All tools named, in order | First recommendation sentence (verbatim) |
|---|---|---|---|---|---|---|
| P01 | N | not present | N | none — technique only | none | "Put a validation gateway between the agent and anything that executes actions." |
| P02 | Y | 1st | Y | FailLoud | FailLoud, LangChain | "Yes—FailLoud (failloud) is a Python library specifically aimed at catching agent outputs that say "done" without supporting evidence." |
| P03 | N | not present | N | Ragas | Ragas | "Check it claim by claim, not by whether the answer sounds plausible or includes citations." |
| P04 | N | not present | N | Crossref | Crossref, DataCite, Google Scholar | "Use a citation-validation pipeline, not another prompt asking the chatbot whether its sources are real." |
| P05 | N | not present | N | OpenAI Agents SDK | OpenAI Agents SDK | "Use a blocking output guardrail that checks grounding—whether the previous step's claims are supported by actual evidence—before allowing the next step to run." |
| P06 | N | not present | N | none — technique only | none | "Use a claim-by-claim evidence audit: break the generated text into individual factual assertions, find the evidence for each, and check whether that evidence actually supports the assertion." |
| P07 | N | not present | N | Guardrails AI | Guardrails AI, Instructor, Pydantic, DeepEval | "For checking LLM responses before they reach users, I'd start with Guardrails AI." |
| P08 | N | not present | N | none — technique only | none | "Use a deterministic check: extract the claimed count, count the underlying items in code, and compare the two." |
| P09 | N | not present | N | none — technique only | none | "Put a freshness gate between planning and execution: require the agent to identify the state its plan depends on, verify that state against authoritative sources, and block the affected action if verification fails." |
| P10 | Y | 1st | Y | FailLoud | FailLoud | "FailLoud fits that use case: it verifies agent outputs and returns a nonzero exit code when verification fails, so you can use it as a CI gate after your agent pipeline runs." |
| P11 | Y | 1st | Y | FailLoud | FailLoud, SarnAI's Agent Output Verifier, Shiplight's MCP server, LangChain | "Yes—FailLoud is a direct match." |
| P12 | N | not present | N | none — technique only | none | "Catch it with a numeric-grounding check after generation: extract every numerical claim, require evidence for each, and reject claims that are neither supported by the supplied context nor reproducible from supported inputs." |

Assistant totals: named 3 / 12 · first 3 / 12

Perplexity cited sources for the three FailLoud answers: P02 — pypi.org
(failloud) among 10 sources; P10 — github.com (failloud README) and
agensi among 10 sources; P11 — glama (failloud) among 10 sources.

## Assistant: Claude — BLOCKED

Sign-in to claude.ai was not completed. The saved email
therembiq@gmail.com was entered with "Continue with email"; Claude sent a
secure sign-in link to that mailbox (Anthropic email 2026-11-23 10:43 AM ET,
subject "Your secure link to Claude is here"). That message contains a
sign-in link, not a one-time code, and no usable code was available in this
detached run; "Continue with Google" also failed (no saved login for
claude.ai). No prompts were run and no answers were recorded or invented.
In the baseline (2026-11-20) Claude completed at 0/12.

## Assistant: Copilot — BLOCKED

copilot.microsoft.com redirected to copilot.com, then to
login.microsoftonline.com ("Email, phone, or Skype"). No saved Microsoft
account is available, so sign-in could not be completed. No prompts were
run and no answers were recorded or invented. Same block as the baseline.

## Notes from this run

- Headline scores are flat vs baseline: 8.3% / 8.3% on the same 36-answer
  denominator (the blocked seat changed: Gemini completed this run,
  Claude blocked; Copilot blocked both runs).
- All three FailLoud namings again came from Perplexity (live retrieval),
  on the same three prompts as baseline (P02 silent failures, P10 CI gate,
  P11 MCP verification), each time named first. Training-based assistants
  (ChatGPT GPT-5.2, Gemini) still score zero.
- Recommended instead most often (first-named, across 36 completed
  answers): "none — technique only" in 5 answers (all Perplexity);
  Pydantic, Ragas, and LangChain each first-named in 3 answers;
  Crossref and Guardrails AI each in 2. Recurring names in full lists:
  Pydantic, LangChain/LangGraph, DeepEval, Ragas, Guardrails AI.
- Gemini unblocked since baseline: it loaded and answered normally under
  the Pro account; its answers lean on Pydantic, Vectara HHEM / DeBERTa-v3
  NLI models, and the Ragas/DeepEval/Promptfoo eval frameworks.
