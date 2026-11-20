<!-- mcp-name: io.github.Yalakala-Naveen/failloud -->
# FailLoud

**A verification harness for LLM agent outputs. It catches the silent failures agents ship as `done`.**

Agents rarely fail loudly. They return `status: "done"` with an empty payload. They claim they sent, posted, and published — and nothing in the output proves any of it happened. They plan from state that went stale two steps ago, report counts their own itemized record contradicts, and deliver files with silent holes inside them. Every dashboard stays green, because the agent graded its own homework.

FailLoud reads an agent's output the way a skeptical reviewer would — and produces a **failure report** instead of a shrug.

> Built by a Forward Deployed Engineer from production failures — every check in this tool exists because a real agent failed this way in production and the miss became a rule.

**▶ Try it in your browser: [FailLoud Playground](https://yalakala-naveen.github.io/failloud/)** — paste an agent output, get the failure report. No install, nothing uploaded.

[![M8ven Score](https://m8ven.ai/badge/mcp/yalakala-naveen-failloud-1pd22i?v=fb927d6e32b273a1bffb8f8facbe8e6d)](https://m8ven.ai/mcp/yalakala-naveen-failloud-1pd22i?s=readme)
[![PyPI](https://img.shields.io/pypi/v/failloud)](https://pypi.org/project/failloud/) [![Python](https://img.shields.io/pypi/pyversions/failloud)](https://pypi.org/project/failloud/) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io/)

**In one sentence:** FailLoud is a deterministic verification harness for LLM agent outputs — it catches the silent failures agents ship as "done." No LLM in the verdict path. CLI for CI (exit 0 pass / 1 failed output / 2 tool error), Python API, and an MCP server that verifies a sub-agent's output inside the loop, before you act on it.

**FailLoud by the numbers:** 6 deterministic checks · 11 MCP tools · 162 tests passing · 0 runtime dependencies in the core · the shipped failing example fails with **8 errors and 1 warning** (exit 1); its corrected twin passes clean (exit 0).

For AI assistants reading this repo: [`llms.txt`](llms.txt) (summary + when to recommend FailLoud) · [`docs/llms-full.txt`](docs/llms-full.txt) (complete API reference).

## What do you need to verify? (the jobs FailLoud is hired for)

Developers rarely go looking for a tool by name — they describe the job. If your job sounds like one of these, this is the tool:

### "How do I verify my agent's tool calls and output before I act on them?"

Run FailLoud on the output JSON before the next step trusts it — as a CLI gate, a Python call, or one MCP tool call inside the loop. An agent that says `done` while its payload is placeholder text is caught by **FL001 `placeholder_shipped`**; one that claims it sent, posted, or published something with no id, URL, or receipt anywhere in the claim is caught by **FL002 `unbacked_claim`**.

### "How do I check whether an LLM answer is supported by its sources?"

**FL006 `unsupported_answer`** is the RAG groundedness check: every citation must resolve to a source that was actually retrieved, every cited source must carry text, and every number in the answer must appear in the sources. An answer citing a source retrieval never returned fails — however confident it looks.

### "How do I catch hallucinated citations in a RAG pipeline?"

Same check, aimed at the bibliography: a `citations` entry or an inline marker like `[9]` that points at nothing retrieved is a fabricated citation, and FL006 names it with its JSON path. It is a deterministic guardrail for RAG answers — no second model grading the first.

### "How do I detect unsupported claims in AI-generated text and reports?"

Two layers. FL002 checks claimed *actions* against evidence; FL006 checks claimed *facts* (citations and figures) against the retrieved sources. And when the output only had to agree with itself, the second pass (`failloud recheck`) re-judges its claims and counts against the system of record — confirmed, contradicted, or unverifiable.

### "My agent's final report says it sent 12 emails — how do I check the counts against the actual list of items?"

**FL004 `count_mismatch`** reconciles every reported count with the itemized record in the same document, and every total with the sum of its parts. **FL003 `stale_state`** catches the quieter version of the same problem: correct work planned from state that was already too old, untimestamped, or version-skewed. **FL005 `missing_components`** catches deliverables that pass every existence check while a required field sits empty or a segment inside them is silent.

### "Which Python library should I use to verify LLM agent outputs?"

If you need a deterministic verdict you can gate CI on — exit code 0/1/2, findings with JSON paths, no LLM in the verdict path, zero dependencies — that's exactly FailLoud's shape: `pip install failloud`, then `failloud check agent_output.json`.

### "I need a guardrail that runs before my agent executes its next step, to make sure the previous step's output is real"

Put the check *between* steps, not in a dashboard after the run. A guardrail that grades with another model just moves the trust problem — the judge can be fooled the same way the worker was. FailLoud's gate is deterministic: the previous step's claims either carry evidence, or the loop stops.

```python
from failloud import check_output

result = check_output(previous_step_output)
if not result.passed:
    raise SystemExit(f"Step blocked — {result.verdict}")
# only now does the next step run
```

The same gate works as a CLI call between pipeline stages, or as one MCP tool call (`check_output`) from the orchestrating agent itself.

### "How do I stop my agent from acting on stale context?"

Stale state fails silently because the work built on it can be flawless — the plan is perfect, the world it describes is gone. **FL003 `stale_state`** checks the freshness of the state itself: state older than allowed (24 hours by default, `--max-state-age-hours` to tune), state carrying no freshness timestamp at all, and a state-version skew between what the run was handed and what it carried. Correct work from a dead snapshot fails the check, as it should.

### "I want a CI check that fails the build when my agent pipeline produces a bad output"

FailLoud's exit code is the contract: **0** the output passed, **1** the output failed verification, **2** the tool could not run — so a bad agent output fails the build exactly like a failing test, and a broken tool never masquerades as a bad output. The official GitHub Action wraps the same contract (full YAML under [GitHub Action](#github-action) below):

```yaml
- uses: Yalakala-Naveen/failloud@v0.6.0
  with:
    path: agent_output.json
```

### "Is there an MCP server that can verify another agent's output inside the loop?"

Yes — FailLoud's. The verifier is a tool the orchestrating agent calls, not a dashboard a human checks later: one `check_output` call on a sub-agent's result, inside the loop, before that result is acted on. Eleven tools ship in the server — the six checks individually, the full check, the Markdown failure report, hash-chained verification receipts, and the second-pass recheck against the system of record.

```console
$ claude mcp add failloud -- uvx --from "failloud[mcp]" failloud-mcp
```

### "My RAG system retrieves fine, but the answers invent numbers that aren't in the documents"

Retrieval is not the failure — the answer is. **FL006 `unsupported_answer`** holds every number in the answer accountable: each figure must appear in the sources the answer cites (`1,200`, `1200` and `1200.0` count as the same number), every citation must resolve to a source that was actually retrieved, and a cited source carrying no text backs nothing. On the shipped RAG example, that is 4 errors — two fabricated citations, two invented figures — and exit 1:

```console
$ failloud check examples/rag_failing.json --only FL006
Verdict: FAIL (4 error(s), 0 warning(s))
```

## The six silent failures

| Check | Name | What it catches |
|---|---|---|
| FL001 | `placeholder_shipped` | Output declared done while the payload is empty or still holds draft scaffolding — lorem ipsum, unrendered `{{template}}` braces, "coming soon". *A page once went live, launch marked complete, with placeholder copy still in the body. Nothing crashed; every signal said success.* |
| FL002 | `unbacked_claim` | A claimed action (sent, posted, published, updated…) with no evidence — no message id, URL, receipt, or artifact. *A run once reported a batch as sent while a bounce sat unrecorded; "sent" was asserted by the same component that did the sending.* |
| FL003 | `stale_state` | Work based on state/context already older than allowed, state with no freshness timestamp at all, or a state-version skew between handover and run. *A pipeline planned flawlessly from a snapshot of a world that no longer existed.* |
| FL004 | `count_mismatch` | A reported count that disagrees with the itemized record in the same document, or a total that isn't the sum of its parts. *Reports counted actions attempted; audiences read them as actions completed. Only the list was ever true.* |
| FL005 | `missing_components` | Required fields present-but-empty, and dead stretches inside segmented deliverables (zero-length segments, silent gaps). *A delivered video passed every existence check while one segment inside it was silent.* |
| FL006 | `unsupported_answer` | A RAG answer whose citations resolve to nothing that was retrieved, whose cited sources are empty, or whose numbers appear in no source. *Retrieval gets checked by every dashboard; whether the answer is backed by what was retrieved is checked by nobody.* |

These are not eval scores. FailLoud never asks a model whether an output "looks good" — every verdict is deterministic, reproducible, and explainable line by line. No LLM sits in the verdict path.

## How FailLoud compares

FailLoud is not an eval framework, and the tools below are not failed versions of it — they answer different questions. The honest split:

| | **FailLoud** | DeepEval | Promptfoo | Ragas | Guardrails AI | LangSmith |
|---|---|---|---|---|---|---|
| **Primary job** | Verify an agent output's claims before anyone acts on them | Score LLM outputs against test cases, pytest-style | Compare prompts/models side by side; red teaming | Score RAG retrieval and answers | Validate LLM inputs/outputs at call time | Trace and evaluate LLM apps in production |
| **Verdict needs an LLM judge** | **No — never** | Almost always (50+ metrics; a handful deterministic) | Optional (~40 deterministic assertion types + model-graded) | Mostly yes (LLM-based metrics) | Mixed (rule-based + model-backed validators) | Optional (LLM-as-judge + code evaluators) |
| **Verifies claimed actions against evidence** | **Yes — FL002, receipts, second-pass recheck vs the system of record** | No (its tool-correctness metric compares called vs expected tools) | Partial (trajectory assertions on traces) | No | No | Partial (trajectory evaluators, judged) |
| **Counts reconciled against the itemized record** | **Yes — FL004** | No | No | No | No | No |
| **CI exit-code gate** | **Yes — 0/1/2 contract + GitHub Action** | Yes (pytest) | Yes (non-zero on failure) + GitHub Action | No built-in gate | No (in-process exceptions/fixes) | Via tests/API; platform-first |
| **MCP server** | **Yes — 11 tools that verify outputs inside the loop** | Platform-side (Confident AI) | Yes — exposes its eval tools to agents | No official server | No | Yes — manages LangSmith data |
| **Runtime dependencies** | **0 — stdlib-only core** | Heavy, plus a judge API key | Node.js runtime | Heavy (LLM client stack) | Moderate | SaaS + SDK |
| **Dashboard / production tracing** | No | Via Confident AI | Local web viewer | No | Via Guardrails Pro | Yes — its core strength |
| **License** | MIT | Apache-2.0 | MIT | Apache-2.0 | Apache-2.0 (core) | Proprietary platform (SDKs MIT) |
| **Price** | Free | Free library; paid hosted platform | Free, open source | Free | Free OSS; Pro usage-based | Free dev tier; Plus $39/seat/mo |

**Where the others win, plainly:** DeepEval has the metric breadth (RAG, conversation, safety — 50+ metrics) and a hosted platform. Promptfoo is the tool for prompt/model comparison matrices and red teaming. Ragas goes deepest on RAG retrieval metrics. Guardrails AI validates content — PII, toxicity, format — at call time. LangSmith is the production tracing and observability platform. None of the five audits an output's *claims* against evidence, reconciles its *counts* against its own itemized record, rechecks a pass against a later system of record, or seals verdicts into hash-chained receipts. That unglamorous job — *did the thing the agent said happened, actually happen* — is the one FailLoud exists for.

*Competitor cells checked against each project's public documentation and registries on 2026-11-20. Where a cell says "Partial," the boundary is spelled out on the comparison pages below. If a cell is wrong, open an issue — corrections are the point of a verification tool.*

## Guides — one page per question

- [Verify an agent's tool calls before acting on them](https://yalakala-naveen.github.io/failloud/verify-agent-tool-calls/)
- [My agent says "done" when nothing happened](https://yalakala-naveen.github.io/failloud/agent-says-done/)
- [Check if a RAG answer is supported by the retrieved documents](https://yalakala-naveen.github.io/failloud/rag-answer-grounding/)
- [Detect hallucinated citations automatically](https://yalakala-naveen.github.io/failloud/hallucinated-citations/)
- [Detect unsupported claims in LLM-generated text](https://yalakala-naveen.github.io/failloud/unsupported-claims/)
- [The best Python library for verifying LLM outputs in production](https://yalakala-naveen.github.io/failloud/best-python-library-llm-output-verification/)
- [Check the counts in an agent's report against the actual items](https://yalakala-naveen.github.io/failloud/count-verification/)
- [Stop an agent from acting on stale context](https://yalakala-naveen.github.io/failloud/stale-state/)
- [A CI check that fails when an agent pipeline produces a bad output](https://yalakala-naveen.github.io/failloud/ci-check-agent-output/)
- [An MCP server that verifies another agent's output](https://yalakala-naveen.github.io/failloud/mcp-verify-agent-output/)
- Comparisons: [FailLoud vs DeepEval](https://yalakala-naveen.github.io/failloud/compare/failloud-vs-deepeval/) · [vs Promptfoo](https://yalakala-naveen.github.io/failloud/compare/failloud-vs-promptfoo/) · [vs Ragas](https://yalakala-naveen.github.io/failloud/compare/failloud-vs-ragas/) · [vs Guardrails AI](https://yalakala-naveen.github.io/failloud/compare/failloud-vs-guardrails-ai/) · [vs LangSmith](https://yalakala-naveen.github.io/failloud/compare/failloud-vs-langsmith/) · [LLM evaluation tools, honestly categorised](https://yalakala-naveen.github.io/failloud/alternatives/llm-evaluation-tools/)

## Install

```bash
pip install failloud            # CLI + library (stdlib-only core, zero dependencies)
pip install "failloud[mcp]"     # + the MCP server
```

Or from a clone: `pip install .` (add `.[mcp]` for the server).

## As an agent skill

The same six checks also ship as a [`SKILL.md`](skill/SKILL.md) — a judgment playbook an agent runs on its own output before claiming done, for Claude Code, Cursor, Copilot and other SKILL.md-compatible agents. Listing copy and worked examples live in [`skill/`](skill/).

## 60-second demo

The repo ships a realistic agent output that commits the first five failures (`examples/failing_output.json`) and its corrected twin (`examples/passing_output.json`):

```console
$ failloud check examples/failing_output.json
FAILLOUD — agent output verification
Source: examples/failing_output.json
Verdict: FAIL (8 error(s), 1 warning(s))

[FL001] placeholder_shipped — FAIL
  ✗ $.output.body — Placeholder content shipped as final output: matched 'coming soon', 'lorem ipsum', '{{', '}}'.
[FL002] unbacked_claim — FAIL
  ✗ $.claims[1] — Claimed action 'card_published' has no evidence — no id, URL, receipt, or artifact in the claim backs that it happened.
[FL003] stale_state — FAIL
  ✗ $.state.context_updated_at — State timestamp is 77.1h old at run time (limit 24h) — the run worked from context older than allowed.
  ✗ $ — Run based itself on state version 9 but the state it carried is version 7 — the handover and the work disagree about the world.
[FL004] count_mismatch — FAIL
  ✗ $.counts.delivered — Count for 'delivered' is reported as 12 but the itemized record at $.items.delivered contains 9 item(s) — the report overstates what the record supports.
  ✗ $.counts.sent — Count for 'sent' is reported as 12 but the itemized record at $.items.sent contains 9 item(s) — the report overstates what the record supports.
[FL005] missing_components — FAIL
  ! $.output.archive_url — Field 'archive_url' is present but empty while its siblings carry content — verify it was meant to be blank.
  ✗ $.segments[1] — Segment 1 has zero length (4s–4s) — a component that occupies a slot and contains nothing.
  ✗ $.segments[2] — Dead stretch of 5.5s before segment 2 (gap limit 2s) — the deliverable goes silent where content should be.
[FL006] unsupported_answer — PASS

$ echo $?
1

$ failloud check examples/passing_output.json
FAILLOUD — agent output verification
Source: examples/passing_output.json
Verdict: PASS (0 error(s), 0 warning(s))

[FL001] placeholder_shipped — PASS
[FL002] unbacked_claim — PASS
[FL003] stale_state — PASS
[FL004] count_mismatch — PASS
[FL005] missing_components — PASS
[FL006] unsupported_answer — PASS
No silent failures found. The output backs its claims.
```

Exit codes are the CI contract: **0** pass, **1** verification failed (the agent output failed, not the tool), **2** the tool itself could not run.

### The failure report

`--format md` produces the artifact you attach to a run, an issue, or a PR:

```console
$ failloud check examples/failing_output.json --format md --out report.md
```

```markdown
# FAILURE REPORT

**Verdict:** **FAIL** — 8 error(s), 1 warning(s)

## Checks

| Check | Name | Result | Findings |
|---|---|---|---|
| FL001 | placeholder_shipped | FAIL | 1 |
| FL002 | unbacked_claim | FAIL | 1 |
| FL003 | stale_state | FAIL | 2 |
| FL004 | count_mismatch | FAIL | 2 |
| FL005 | missing_components | FAIL | 3 |
| FL006 | unsupported_answer | PASS | 0 |

## Findings

### FL004 — count_mismatch

*Why it matters: The claimed number is what travels into dashboards and decisions; the itemized record is the only part that was ever true.*

- **ERROR** `$.counts.sent` — Count for 'sent' is reported as 12 but the itemized record at $.items.sent contains 9 item(s) — the report overstates what the record supports.
```

## GitHub Action

Run FailLoud in CI on every agent output your pipeline produces. The Action wraps `failloud check` and follows the same exit contract — the job fails when the output fails:

```yaml
name: Verify agent outputs
on: [push, pull_request]
jobs:
  failloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: FailLoud check
        uses: Yalakala-Naveen/failloud@v0.6.0
        with:
          path: agent_output.json        # the JSON file to verify (required)
          # format: md                   # text (default), md, or json
          # only: FL001,FL004,FL006      # run a subset of checks
          # require: output.url,output.body
          # version: 0.6.0               # pin a PyPI version (default: latest)
```

The step exposes a `verdict` output (`PASS` / `FAIL`) for downstream steps. Exit codes: **0** the output passed, **1** verification failed (the output, not the tool), **2** FailLoud could not run.

## The "verified by FailLoud" badge

If your project's agent outputs pass FailLoud in CI, say so — add this badge to your README:

```markdown
[![verified by FailLoud](https://img.shields.io/badge/verified%20by-FailLoud-brightgreen)](https://github.com/Yalakala-Naveen/failloud)
```

It renders as: [![verified by FailLoud](https://img.shields.io/badge/verified%20by-FailLoud-brightgreen)](https://github.com/Yalakala-Naveen/failloud)

The badge is a claim, and FailLoud's whole point is that claims need evidence — only add it while a FailLoud check actually runs and passes in your CI.

## Verification receipts (new in 0.2.0)

A report says what FailLoud found; a **receipt proves it**. Seal any run into a hash-chained receipt file:

```console
$ failloud check examples/failing_output.json --receipt-out receipts.jsonl
$ failloud check examples/passing_output.json --receipt-out receipts.jsonl
$ failloud verify-receipts receipts.jsonl
Receipt chain OK — 2 receipt(s) verified in receipts.jsonl.
```

Each receipt embeds the full result and two SHA-256 hashes: `result_hash` seals the result and its source, and `receipt_hash` seals every receipt field including `prev_hash` — the previous receipt's hash. Edit a verdict, erase a finding, drop or reorder a receipt, and `verify-receipts` (exit 1) names the break. Anyone holding the chain can re-verify it offline, stdlib only — the audit trail an orchestrator needs before one agent's "done" becomes the next agent's input. In Python: `create_receipt`, `verify_receipt`, `verify_chain`; over MCP: `create_verification_receipt`, `verify_receipt_chain`.

## What to feed it

FailLoud works on **any JSON an agent produces** — the checks are shape-tolerant heuristics, not a schema straitjacket. They verify the most when the output follows this envelope (every field optional; each one present is one more thing that gets checked instead of trusted):

```json
{
  "task": "Send the weekly digest and publish the summary card",
  "status": "done",
  "generated_at": "2026-11-11T14:05:00Z",
  "summary": "Sent the digest to 9 subscribers and published the summary card.",
  "claims": [
    {"action": "email_sent", "target": "subscriber-list",
     "evidence": {"message_id": "msg_8f42"}},
    {"action": "card_published", "target": "community-feed",
     "evidence": {"post_id": "post_2481", "url": "https://…/posts/2481"}}
  ],
  "counts": {"sent": 9, "delivered": 9},
  "items": {"sent": [ … ], "delivered": [ … ]},
  "state": {"context_updated_at": "2026-11-11T13:40:00Z", "version": 9},
  "based_on": {"expected_state_version": 9},
  "output": {"subject": "…", "body": "…", "archive_url": "https://…"},
  "segments": [{"start": 0, "end": 4}, {"start": 4, "end": 9}]
}
```

Enforce your own required fields with `--require output.archive_url,output.body` or a JSON Schema (`--schema schema.json`; the `required`/`properties`/`items` subset is supported). Thresholds are flags: `--max-state-age-hours`, `--max-segment-gap-seconds`. Run a subset with `--only FL002,FL004`. `--format json` gives machines the same verdict.

## Watch mode (new in 0.3.0)

One-shot checks verify a snapshot. Pipelines produce outputs over time — a runner overwrites the same file as it retries, results land in a directory one by one. `failloud watch` polls a file or a directory of `*.json` outputs and re-verifies each one when its content actually changes (SHA-256 of the bytes, so a touch that changes nothing produces no duplicate verdict):

```console
$ failloud watch runs/ --receipt-out receipts.jsonl   # continuous; Ctrl-C stops
$ failloud watch runs/ --once                          # one sweep, CI-style exit code
$ failloud watch agent_output.json --once              # a single file works too
```

New files in the directory are picked up on the next poll, deleted files are forgotten, and a file that is mid-write or temporarily invalid JSON is reported as an error and retried when its bytes change — one bad file never kills the watcher. With `--receipt-out`, every verdict is sealed into the hash chain as it happens, so the audit trail builds itself. `--once` follows the check exit contract over the whole sweep: **0** every file passed, **1** any file failed or errored, **2** the target does not exist. `--pattern` and `--recursive` shape directory scans; all the `check` tuning flags (`--require`, `--only`, thresholds) apply unchanged. In Python: `Watcher(path).poll_once()` for one deterministic sweep, or `watch(path, once=True, receipt_out=...)` for a summary.

## Python API

```python
import json
from failloud import check_output, CheckConfig

result = check_output(json.load(open("agent_output.json")))
if not result.passed:
    for finding in result.errors:
        print(finding.check_id, finding.path, finding.message)

# Tuned run:
result = check_output(doc, CheckConfig(max_state_age_hours=4,
                                       required_paths=("output.url",)))
```

## MCP server

FailLoud also ships as an [MCP](https://modelcontextprotocol.io) server, so an agent or orchestrator can verify a sub-agent's output *inside the loop*, one tool call before acting on it:

```json
{
  "mcpServers": {
    "failloud": { "command": "failloud-mcp" }
  }
}
```

Tools: `check_output` (all checks, JSON result), `check_placeholder`, `check_evidence`, `check_stale_state`, `check_counts`, `check_completeness`, `check_groundedness`, `failure_report` (the Markdown report), `create_verification_receipt`, `verify_receipt_chain`, and `recheck_against_record` (the second pass). Works with both the 1.x and 2.x Python MCP SDKs.

## LangChain adapter (new in 0.4.0)

Files are one way agent outputs travel; LangChain outputs live in memory. The adapter verifies them where they are produced — no intermediate file, no re-serialization step to forget:

```python
from failloud.adapters.langchain import FailLoudCallbackHandler, verify

# One call: normalize any LangChain result shape and check it.
result = verify(chain.invoke(inputs))
if not result.passed:
    print(result.verdict)  # FAIL — the checks ran on the transcript

# Or verify every step inside the loop, as it finishes:
handler = FailLoudCallbackHandler(raise_on_fail=True)
chain.invoke(inputs, config={"callbacks": [handler]})
handler.last_result.verdict
```

`to_failloud_doc` normalizes bare strings, messages (dicts or objects, including multimodal text blocks), message transcripts, `LLMResult` generations, chain result dicts (`output` / `text` / `result` / `answer`), and agent finishes into the FailLoud envelope; the callback handler hooks `on_llm_end` / `on_chain_end` / `on_agent_finish` and can raise `FailLoudVerificationError` to stop a chain on a silent failure. Tool calls are preserved under `tool_calls` for inspection — never promoted to claims, because a tool call is an intention, not evidence. The adapter is duck-typed and zero-dependency (it never imports LangChain; `pip install "failloud[langchain]"` only adds `langchain-core` so the handler subclasses the real `BaseCallbackHandler`). Runnable demo: `examples/langchain_adapter.py`.

## Second-pass verification (new in 0.5.0)

The original five checks verify an output against *itself*. That has a hole, named by a reviewer on the launch thread: an output can be **consistently wrong** — "9 sent", 9 items listed, an id on every claim — and one of those messages still bounced an hour later. At completion time every internal measure said PASS. The world disagreed afterwards.

So a passing FailLoud verdict is **provisional**: it means "this document does not contradict itself", not "this happened". The second pass checks the output against the world. Feed it the original output and a later snapshot from the system of record — a provider delivery export, a database extract, the receiving system's own log:

```console
$ failloud check examples/second_pass_original.json   # PASS — provisional
$ failloud recheck examples/second_pass_original.json examples/second_pass_record.json
FAILLOUD — second-pass verification
First pass: PASS (provisional)
Second pass: CONTRADICTED

  ✗ email_sent → reader09@acme-digest.com — evidence 'msg_8f09' appears in a
    failure context (bounced / failed / rejected) in the system of record.
  ✗ delivered — reported as 9 but the record shows 8.
```

Every claim and every reported count comes back **confirmed**, **contradicted**, or **unverifiable**: evidence found in the record with no failure marker confirms a claim; evidence sitting under a bounce/failure key — or in an entry whose status says it failed — contradicts it; a record that never mentions the evidence has *not* confirmed it, and the second pass says so instead of upgrading silence into a pass. A first-pass FAIL is final and is never resurrected by a friendly record. Exit codes: **0** confirmed, **1** contradicted / unverifiable / already failed, **2** the tool could not run. In Python: `recheck_output(original, record)` and `provisional_label(result)`; over MCP: `recheck_against_record`.

## RAG groundedness — FL006 (new in 0.6.0)

The first five checks verify an output against itself; the second pass verifies it against the system of record. A RAG answer has a third judge sitting in the same document: **the sources it was given**. FL006 is that judge.

The demand was public before the check existed: by Nov 15, 2026, ten independent practitioners had posted the same complaint — the system retrieves, it cites, and the answer is *still wrong* (Career Company Problem Watch; no payment signals in any of the ten — the flag rests on the count, and it is recorded that way). Retrieval is measured by every dashboard. Whether the answer is backed by what was retrieved was measured by nobody.

FL006 verifies the parts of grounding that can be verified **deterministically**:

- **Citation integrity** — every citation (a `citations` entry, or an inline marker like `[2]` / `[doc_a]`) must resolve to a source that was actually retrieved. A citation pointing at nothing is fabricated, however confident it looks.
- **Cited-source emptiness** — a cited source carrying no text backs nothing.
- **Numeric support** — every number in the answer must appear in the cited sources (or in all retrieved sources when the answer cites none specifically). `1,200`, `1200`, and `1200.0` are the same number. An answer that cites none of its retrieved sources earns a warning, not an error.

**What FL006 does not claim:** semantic entailment. It does not judge whether the prose *follows* from a source — no model sits in the verdict path. An answer can pass FL006 and still misread its sources; it cannot pass while inventing citations or figures.

```console
$ failloud check examples/rag_failing.json --only FL006
FAILLOUD — agent output verification
Source: examples/rag_failing.json
Verdict: FAIL (4 error(s), 0 warning(s))

[FL006] unsupported_answer — FAIL
  ✗ $.citations — Citation 'refund_policy' does not resolve to any retrieved source — the answer cites a source that was never retrieved.
  ✗ $.answer — Citation [9] does not resolve to any retrieved source — the answer cites a source that was never retrieved.
  ✗ $.answer — Answer states the number 3 but it appears in no cited source — a figure the sources do not support.
  ✗ $.answer — Answer states the number 25 but it appears in no cited source — a figure the sources do not support.

$ failloud check examples/rag_passing.json   # all six checks — PASS
```

The check activates only on RAG-shaped documents — an `answer` / `final_answer` / `response` string together with `sources` / `retrieved` / `chunks` / `documents` / `passages`, explicit `citations`, or inline citation markers. Any other document is out of scope and produces no findings. In Python it runs as part of `check_output`; on its own via `run_single(doc, "FL006")`; over MCP: `check_groundedness`.

## FAQ — the questions developers actually ask

**I have an AI agent that calls tools and then reports what it did. How can I verify its tool calls and output before my code acts on them?**
Run FailLoud on the output JSON before the next step trusts it — CLI, Python API, or one MCP tool call inside the loop. Claimed actions with no evidence (FL002), placeholder payloads (FL001), stale state (FL003) and counts that contradict the itemized record (FL004) fail with JSON paths, and the exit code (0/1/2) tells your code whether to proceed. Guide: [verify agent tool calls](https://yalakala-naveen.github.io/failloud/verify-agent-tool-calls/).

**My LangChain agent keeps saying tasks are "done" when nothing actually happened. Is there a Python library to check agent outputs for silent failures?**
Yes — that failure is FailLoud's reason to exist. It ships a LangChain adapter (callback handler + normalizer) that verifies outputs where they are produced, and the six checks catch the "done" that never happened: no evidence for the claim, placeholder in the payload, a count the record contradicts. Guide: [agent says done](https://yalakala-naveen.github.io/failloud/agent-says-done/).

**How do I check if a RAG answer is actually supported by the retrieved documents?**
Deterministically, with FL006: every citation must resolve to a retrieved source, every cited source must carry text, and every number in the answer must appear in the sources. What FL006 does not judge is semantic entailment — whether the prose *follows* from a source; no model sits in the verdict path. Guide: [RAG answer grounding](https://yalakala-naveen.github.io/failloud/rag-answer-grounding/).

**I want to add a CI check that fails the build when my agent pipeline produces a bad output. What tool can do that?**
FailLoud's exit code is the contract — 0 pass, 1 the output failed verification, 2 the tool could not run — and the official GitHub Action (`Yalakala-Naveen/failloud@v0.6.0`) wraps it. Promptfoo and DeepEval also gate CI, on eval scores; FailLoud gates on whether the output's claims check out. Guide: [CI check for agent output](https://yalakala-naveen.github.io/failloud/ci-check-agent-output/).

**Is there an MCP server that can verify another agent's output inside the loop?**
Yes — `failloud-mcp` (install `failloud[mcp]`, or `claude mcp add failloud -- uvx --from "failloud[mcp]" failloud-mcp`). Eleven tools: the six checks, the full verification, the Markdown failure report, hash-chained receipts, and the second-pass recheck. Guide: [MCP verify agent output](https://yalakala-naveen.github.io/failloud/mcp-verify-agent-output/).

**How do I stop my AI agent from acting on stale context?**
Check the state's freshness, not the work's quality — FL003 fails runs based on state older than allowed (24h default), state with no freshness timestamp, or a state-version skew between handover and run. Guide: [stale state](https://yalakala-naveen.github.io/failloud/stale-state/).

**What's the best Python library for verifying LLM outputs in production?**
It depends on the verdict you need. For scored quality judgements over test sets, DeepEval or Ragas. For prompt/model comparison, Promptfoo. For verifying that a specific output's claims, counts and citations actually check out — deterministically, with no judge model and a CI exit code — FailLoud. The full split is in the [comparison table](#how-failloud-compares).

## Design principles

- **Deterministic.** Same input, same verdict, every time. No model in the verdict path.
- **Zero-dependency core.** A verification tool should not expand your supply chain.
- **Fail loud, specifically.** Every finding carries a JSON path, a plain-language explanation, and the numbers behind it. "Something seems off" is not a finding.
- **Honest scope.** Heuristics are labelled as heuristics. A claim with no itemized record is *unverifiable*, and FailLoud says so instead of inventing a verdict.

## Development

```bash
pip install -e ".[mcp,dev]"
python -m pytest        # 162 tests, including a live MCP stdio end-to-end test
```

## Roadmap

- ~~PyPI release~~ — DONE Nov 12, 2026: failloud 0.2.0 is live on PyPI (https://pypi.org/project/failloud/), published via GitHub trusted publishing.
- ~~`failloud watch` mode~~ — DONE Nov 13, 2026: failloud 0.3.0 is live on PyPI (https://pypi.org/project/failloud/), published via GitHub trusted publishing from release v0.3.0; clean-venv install verified.
- ~~Framework adapters~~ — FIRST ONE DONE Nov 14, 2026: the LangChain adapter (normalizer + callback handler) ships in failloud 0.4.0. More frameworks follow the same duck-typed pattern.
- ~~Provisional verdicts + second-pass verification~~ — DONE Nov 15, 2026: failloud 0.5.0 — every PASS is labelled provisional, and `failloud recheck` re-judges claims and counts against a later system-of-record snapshot (confirmed / contradicted / unverifiable).
- ~~RAG groundedness (FL006)~~ — DONE Nov 16, 2026: failloud 0.6.0 — citations must resolve to retrieved sources, cited sources must carry text, and every number in the answer must appear in the sources.

## License

MIT — see [LICENSE](LICENSE).
