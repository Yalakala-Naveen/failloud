# FailLoud

**A verification harness for LLM agent outputs. It catches the silent failures agents ship as `done`.**

Agents rarely fail loudly. They return `status: "done"` with an empty payload. They claim they sent, posted, and published — and nothing in the output proves any of it happened. They plan from state that went stale two steps ago, report counts their own itemized record contradicts, and deliver files with silent holes inside them. Every dashboard stays green, because the agent graded its own homework.

FailLoud reads an agent's output the way a skeptical reviewer would — and produces a **failure report** instead of a shrug.

> Built by a Forward Deployed Engineer from production failures — every check in this tool exists because a real agent failed this way in production and the miss became a rule.

**▶ Try it in your browser: [FailLoud Playground](https://yalakala-naveen.github.io/failloud/)** — paste an agent output, get the failure report. No install, nothing uploaded.

## The five silent failures

| Check | Name | What it catches |
|---|---|---|
| FL001 | `placeholder_shipped` | Output declared done while the payload is empty or still holds draft scaffolding — lorem ipsum, unrendered `{{template}}` braces, "coming soon". *A page once went live, launch marked complete, with placeholder copy still in the body. Nothing crashed; every signal said success.* |
| FL002 | `unbacked_claim` | A claimed action (sent, posted, published, updated…) with no evidence — no message id, URL, receipt, or artifact. *A run once reported a batch as sent while a bounce sat unrecorded; "sent" was asserted by the same component that did the sending.* |
| FL003 | `stale_state` | Work based on state/context already older than allowed, state with no freshness timestamp at all, or a state-version skew between handover and run. *A pipeline planned flawlessly from a snapshot of a world that no longer existed.* |
| FL004 | `count_mismatch` | A reported count that disagrees with the itemized record in the same document, or a total that isn't the sum of its parts. *Reports counted actions attempted; audiences read them as actions completed. Only the list was ever true.* |
| FL005 | `missing_components` | Required fields present-but-empty, and dead stretches inside segmented deliverables (zero-length segments, silent gaps). *A delivered video passed every existence check while one segment inside it was silent.* |

These are not eval scores. FailLoud never asks a model whether an output "looks good" — every verdict is deterministic, reproducible, and explainable line by line. No LLM sits in the verdict path.

## Install

```bash
pip install failloud            # CLI + library (stdlib-only core, zero dependencies)
pip install "failloud[mcp]"     # + the MCP server
```

Or from a clone: `pip install .` (add `.[mcp]` for the server).

## 60-second demo

The repo ships a realistic agent output that commits all five failures (`examples/failing_output.json`) and its corrected twin (`examples/passing_output.json`):

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

## Findings

### FL004 — count_mismatch

*Why it matters: The claimed number is what travels into dashboards and decisions; the itemized record is the only part that was ever true.*

- **ERROR** `$.counts.sent` — Count for 'sent' is reported as 12 but the itemized record at $.items.sent contains 9 item(s) — the report overstates what the record supports.
```

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

Tools: `check_output` (all checks, JSON result), `check_placeholder`, `check_evidence`, `check_stale_state`, `check_counts`, `check_completeness`, and `failure_report` (the Markdown report). Works with both the 1.x and 2.x Python MCP SDKs.

## Design principles

- **Deterministic.** Same input, same verdict, every time. No model in the verdict path.
- **Zero-dependency core.** A verification tool should not expand your supply chain.
- **Fail loud, specifically.** Every finding carries a JSON path, a plain-language explanation, and the numbers behind it. "Something seems off" is not a finding.
- **Honest scope.** Heuristics are labelled as heuristics. A claim with no itemized record is *unverifiable*, and FailLoud says so instead of inventing a verdict.

## Development

```bash
pip install -e ".[mcp,dev]"
python -m pytest        # 68 tests, including a live MCP stdio end-to-end test
```

## Roadmap

- PyPI release and a public GitHub home (this repo is release-ready; publishing is a maintainer decision, not a code gap).
- Framework adapters that capture outputs directly from popular agent frameworks instead of reading files.
- Signed, hash-chained verification receipts for audit trails.
- A `failloud watch` mode for streaming/runner integration.

## License

MIT — see [LICENSE](LICENSE).
