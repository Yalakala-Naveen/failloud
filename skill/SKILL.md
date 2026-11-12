---
name: failloud-verify
description: Verifies an AI agent's own output before the agent claims the work is done. Use when an agent is about to report a task as done, complete, successful, sent, posted, published, or delivered — or before handing an output document to a downstream step or a human — to catch five silent failures: placeholder content shipped as final, claimed actions with no evidence, work based on stale state, counts that disagree with the itemized record, and required components that are missing or silently empty. Produces a failure report the agent must fix or honestly report instead of an unbacked "done".
---

# FailLoud Verify — the done-check

Agents rarely fail loudly. They report `done` with an empty payload, claim
they sent things nothing proves, plan from state that went stale, and quote
counts their own records contradict. This skill is the gate that runs
**before** any of that is reported: five checks, executed on the agent's own
output, in order. Every check below is a procedure with a pass rule, a fail
rule, and a required action on fail.

**Honest scope.** This skill is the *judgment playbook*: it teaches you to
inspect your output the way the FailLoud tool does. A deterministic version
exists — `pip install failloud` (CLI + MCP server, zero-dependency core,
same five checks, same finding messages, exit codes 0/1/2) — and wherever a
machine can run it, prefer it: its verdict is reproducible and no model
sits in the path. Use this skill where the tool cannot run, and to shape
outputs so the tool can verify them later.

## When to run it

Run all five checks, in order, at these moments:

- Before you report a task as done / complete / success / shipped /
  published / delivered — in a status field, a summary, or a message to a
  human or another agent.
- Before a downstream step consumes your output as fact.
- Whenever you produce a JSON output document describing work performed.

If the output is explicitly a draft (`status: draft`, `in_progress`,
`pending`, `partial`, `blocked`, …), FL001 is exempt — placeholders are
honest in drafts. The other four checks still apply.

## The envelope that verifies best

Checks verify the most when the output carries this shape (every field
optional; each one present is one more thing checked instead of trusted):

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

## FL001 — placeholder_shipped

*Why it matters: a placeholder that ships is indistinguishable from
finished work until a human reads it — by then it is public.*

**Inspect.** The payload: the first of `output`, `payload`, `deliverable`,
`result_content`, `content`, `body` that exists; if none exists, the whole
document minus run metadata. This check applies when the document claims
completion (status is one of done, complete, completed, success,
successful, succeeded, ok, shipped, published, live, delivered, finished,
ready) **or carries no status at all** — an unlabelled document handed
downstream is a final output. Skip only for an explicitly non-final status.

**Fail (error) if any of these holds:**

- The payload is empty — nothing was actually produced.
- Any string in the document is exactly (case-insensitive, trimmed) one of:
  `tbd`, `tba`, `todo`, `to do`, `placeholder`, `dummy`, `lorem ipsum`,
  `coming soon`, `n/a`, `xxx`, `...`
- Any string contains: `lorem ipsum`, `coming soon`, `<insert`, `[insert`,
  `{{`, `}}`, `placeholder text`, `sample text`, `your text here`,
  `insert text here`, `dummy content`, `mock data`, `example.com`,
  `example.org`, `todo:`

**Pass.** Payload carries real content and no pattern matches anywhere.

**On fail.** Replace the scaffolding with the real content, or change the
status to `draft` and say plainly that it is a draft. Never report done.

## FL002 — unbacked_claim

*Why it matters: a claim without evidence is the producing system grading
its own homework; downstream steps build on it as if it were fact.*

**Inspect.** Every entry in `claims`, `actions`, `actions_taken`, `steps`,
or `completed_actions`. A claim *asserts completion* when it names an
action (via `action` / `type` / `verb` / `did` / `name` / `operation`), has
`done: true` / `completed: true`, or carries a completion status. A claim
whose status is `failed`, `error`, `skipped`, `pending`, `planned`, or
`cancelled` asserts nothing — it passes; honesty is not a finding.

**Evidence** means at least one field *inside the claim* holding actual
content: `evidence`, `proof`, `artifact`(s), `url`(s), `link`(s), `id`,
`message_id`, `record_id`, `receipt`, `confirmation` / `confirmation_id`,
`external_id`, `path`, `file`, `hash` / `sha`, `permalink`, `reference`,
`ticket`, `post_id`, `thread_id`. An `evidence` object whose fields are
all empty is a container, not evidence — it does not count.

**Fail (error).** An asserting claim with no evidence field carrying
content. Also fail when a narrative field (`summary`, `message`, `report`,
`description`, `notes`, `result`) asserts completed actions in prose —
past-tense verbs such as sent, posted, published, emailed, uploaded,
deployed, updated, created, deleted, booked, charged, notified, delivered,
filed, submitted, released, merged, announced — while the *entire
document* contains no evidence anywhere (no evidence key, no URL).

**Pass.** Every asserted claim carries non-empty evidence.

**On fail.** Get the receipt: re-query the system of record for the id,
URL, or confirmation and put it in the claim. If it cannot be produced,
downgrade the wording to what is proven ("attempted", "queued") or report
the action as unverified. Never leave a bare assertion in place.

## FL003 — stale_state

*Why it matters: correct work on stale state is wrong work with extra
confidence — the plan is flawless for a world that no longer exists.*

**Inspect.** State blocks: `state`, `context`, `handoff`, `memory`,
`input_state`, `working_state`. The run's reference time is its
`generated_at` (or now).

**Fail (error) if any of these holds:**

- **Age.** A timestamp inside a state block (keys like
  `context_updated_at`, `state_updated_at`, `as_of`, `snapshot_at`,
  `retrieved_at`, `updated_at`, `last_updated`, `valid_as_of`,
  `captured_at`, `observed_at`) is older than **24 hours** (default limit)
  at run time. State the age in the finding: "State timestamp is 77.1h old
  at run time (limit 24h)".
- **Version skew.** The state block's version (`version`, `state_version`,
  `revision`) differs from the version the run declares it based itself on
  (`based_on.expected_state_version`, or `based_on_version`,
  `expected_version`, `assumed_state_version`).

**Warn (warning).** A state block carries real data but no timestamp
anywhere — its age cannot be verified, so staleness would be invisible.

**Pass.** Every state timestamp is within the age limit and versions agree.

**On fail.** Re-fetch the state and redo any work planned from the stale
parts. Never fix this by re-dating the timestamp.

## FL004 — count_mismatch

*Why it matters: the claimed number is what travels into dashboards and
decisions; the itemized record is the only part that was ever true.*

**Inspect.** Numeric claims: every number inside a `counts`, `stats`,
`summary_counts`, `totals`, or `metrics` block, plus any key shaped
`<metric>_count`, `count_<metric>`, `total_<metric>`, `num_<metric>`
anywhere in the document. Itemized records: every list in the document,
matched to a metric by name (exact, singular/plural, or token overlap).

**Fail (error) if any of these holds:**

- A claimed count differs from the length of its matching itemized list —
  in either direction ("the report overstates what the record supports" /
  "the report understates its own record").
- A `total` / `grand_total` inside a counts block does not equal the sum
  of its sibling numbers.

**Not a fail.** A claim with *no* itemized list anywhere is **unverifiable,
not wrong** — say exactly that, and if a reader will repeat the number,
itemize it so it can be checked. Numbers in prose are out of scope.

**Pass.** Every claim reconciles with its list; every total equals its
parts.

**On fail.** Correct the number to the record, or fix the record to the
truth. Never ship the bigger number.

## FL005 — missing_components

*Why it matters: existence is not completeness — a deliverable can pass
every outline check while a component inside it is silently absent.*

**Inspect three things:**

1. **Required components** — every field the task, the recipient, or a
   declared schema requires. Missing entirely → **error**. Present but
   empty → **error**: "present but empty — it satisfies the shape and
   delivers nothing."
2. **Sibling emptiness** — inside the payload (`output`), a field that is
   present but empty while its siblings carry content → **warning**:
   "verify it was meant to be blank." Legitimately-empty fields are exempt:
   `error`, `errors`, `warnings`, `cc`, `bcc`, `metadata`, `parent_id`.
   (A field *required* under rule 1 that is empty is an error, not this
   warning.)
3. **Segments** — lists named `segments`, `scenes`, `tracks`, `clips`,
   `chapters`, or `shots`, each with `start`/`end` (or `start` +
   `duration`). Zero length (end ≤ start) → **error**. A gap between one
   segment's end and the next segment's start longer than **2 seconds**
   (default limit) → **error**: a dead stretch where content should be.

**Pass.** Nothing required is missing or empty; no zero-length segments;
no dead stretches.

**On fail.** Produce the missing component, or remove the empty field and
state plainly what was not delivered. For segments: fill the hole or
re-cut — never ship a deliverable with a silent stretch inside it.

## The verdict

- **FAIL** — at least one error finding. The output must not be reported as
  done and must not flow downstream as fact.
- **PASS WITH WARNINGS** — no errors; warnings exist. They do not block,
  but they must be surfaced with the output, never silently dropped.
- **PASS** — no findings.

On FAIL, exactly two moves are allowed: **fix** the output and re-run the
checks, or **report honestly** — restate the status as failed/partial and
narrow every claim to what the evidence supports. Softening a finding,
deleting a claim from the report while leaving it in the summary, or
re-wording a fail into a pass is itself the failure this skill exists to
catch.

## Worked example

`examples/failing_output.json` in this skill (and in the FailLoud repo) is
a digest run that reports `status: done`. Running the checks:

- **FL001 ✗** `$.output.body` — "Lorem ipsum dolor sit amet,
  {{first_name}}, your digest is coming soon." matched 'coming soon',
  'lorem ipsum', '{{', '}}'.
- **FL002 ✗** `$.claims[1]` — claimed action 'card_published' has no
  evidence. (Claim 0 passes: its `message_id` is real evidence.)
- **FL003 ✗** `$.state.context_updated_at` — timestamp is 77.1h old at run
  time (limit 24h); and the run based itself on state version 9 while the
  state it carried is version 7.
- **FL004 ✗** `$.counts.sent` and `$.counts.delivered` — both reported as
  12; each itemized list at `$.items.*` contains 9.
- **FL005 !** `$.output.archive_url` — present but empty while siblings
  carry content (warning); **✗** `$.segments[1]` — zero length (4s–4s);
  **✗** `$.segments[2]` — dead stretch of 5.5s before it (gap limit 2s).

**Verdict: FAIL — 8 errors, 1 warning.** Its corrected twin
(`examples/passing_output.json`) — counts 9/9 matching the lists, evidence
with `post_id` + URL on both claims, real body copy, state 25 minutes old
at version 9, segments 0–4 / 4–9 / 9–12 with no gaps — passes all five
checks with zero findings.

## The failure report

When checks fail, emit the report in this format (it is the FailLoud
tool's Markdown report format, so skill reports and tool reports read the
same):

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

*Why it matters: The claimed number is what travels into dashboards and
decisions; the itemized record is the only part that was ever true.*

- **ERROR** `$.counts.sent` — Count for 'sent' is reported as 12 but the
  itemized record at $.items.sent contains 9 item(s) — the report
  overstates what the record supports.
```

Every finding carries its check id, a JSON path, a severity, and the
numbers behind it. "Something seems off" is not a finding.

## The deterministic version

This skill is one half of FailLoud. The other half is free and open source
(MIT): the `failloud` Python package — CLI, library, and an MCP server
(`failloud-mcp`, tools: `check_output`, one per check, `failure_report`) —
runs these exact checks deterministically, with tunable thresholds
(`--max-state-age-hours`, `--max-segment-gap-seconds`, `--require`,
`--schema`), and exit codes a CI pipeline can gate on. Repo:
https://github.com/Yalakala-Naveen/failloud — also home of this skill, the
worked examples, and a browser playground that runs the same checks.
