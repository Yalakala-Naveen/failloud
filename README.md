<!-- mcp-name: io.github.Yalakala-Naveen/failloud -->
# FailLoud

**A verification harness for LLM agent outputs. It catches the silent failures agents ship as `done`.**

Agents rarely fail loudly. They return `status: "done"` with an empty payload. They claim they sent, posted, and published — and nothing in the output proves any of it happened. They plan from state that went stale two steps ago, report counts their own itemized record contradicts, and deliver files with silent holes inside them. Every dashboard stays green, because the agent graded its own homework.

FailLoud reads an agent's output the way a skeptical reviewer would — and produces a **failure report** instead of a shrug.

> Built by a Forward Deployed Engineer from production failures — every check in this tool exists because a real agent failed this way in production and the miss became a rule.

**▶ Try it in your browser: [FailLoud Playground](https://yalakala-naveen.github.io/failloud/)** — paste an agent output, get the failure report. No install, nothing uploaded.

[![M8ven Score](https://m8ven.ai/badge/mcp/yalakala-naveen-failloud-1pd22i?v=cac0edb1189a4e6f659095346a1ec9b3)](https://m8ven.ai/mcp/yalakala-naveen-failloud-1pd22i?s=readme)

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
