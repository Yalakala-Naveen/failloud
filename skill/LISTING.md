# Agensi listing — FailLoud Verify

## Title (51 chars)

FailLoud Verify: The Done-Check for AI Agent Output

## Short description

Five verification checks your agent runs on its own output before it
claims done — catching placeholder content shipped as final, claims with
no evidence, stale state, counts that contradict the record, and silently
missing components. Ends in a failure report, not an unbacked "done".

## Full description

Your agent said "done." Was it?

Agents rarely fail loudly. They return status: done with an empty payload.
They report "sent, posted, published" with nothing in the output that
proves any of it happened. They plan from state that went stale two steps
ago, quote counts their own itemized records contradict, and deliver files
with silent holes inside them. Every dashboard stays green, because the
agent graded its own homework.

FailLoud Verify is the gate that runs before the claim. It teaches your
agent to inspect its own output the way a skeptical reviewer would —
five checks, each a concrete procedure with a pass rule, a fail rule, and
a required action on fail:

- **FL001 placeholder_shipped** — output declared done while the payload is
  empty or still holds draft scaffolding: lorem ipsum, unrendered
  {{template}} braces, "coming soon", TODO/TBD/N-A values, example domains.
  (Explicit drafts are exempt — placeholders are honest there.)
- **FL002 unbacked_claim** — every claimed action (sent, posted,
  published, deployed…) must carry real evidence inside the claim: a
  message id, URL, receipt, artifact, hash. An evidence object whose
  fields are all empty does not count. Narrative claims in a summary with
  zero evidence anywhere in the document are flagged too. Honestly failed
  or planned claims pass.
- **FL003 stale_state** — state/context the run based itself on that is
  older than the allowed age (default 24h), carries no freshness timestamp
  at all, or disagrees with the state version the run declared.
- **FL004 count_mismatch** — reported counts that disagree with the
  itemized record in the same document, and totals that are not the sum of
  their parts. A count with no itemized record is reported as
  *unverifiable, not wrong* — the skill says so instead of inventing a
  verdict.
- **FL005 missing_components** — required fields missing or present but
  empty, and dead stretches inside segmented deliverables (zero-length
  segments, silent gaps over the limit).

On any error the agent gets exactly two moves: fix the output and re-run,
or report honestly — status restated as failed/partial, claims narrowed
to what the evidence supports. Findings are emitted in the FailLoud
failure-report format: check id, JSON path, severity, and the numbers
behind every finding.

**Who it's for.** Anyone running agents whose output other people or
systems act on — multi-agent pipelines, coding agents filing completion
reports, content/publishing automation, ops agents sending and posting on
a human's behalf. If a wrong "done" costs you money, trust, or a
downstream cascade, this is the checklist that catches it first.

**What's inside.** One SKILL.md (installs into Claude Code, Cursor,
Copilot and 20+ agents) with: the trigger rules for when to run the gate,
the output envelope that verifies best, all five check procedures with
exact patterns, thresholds and evidence rules, the verdict rules, a
worked example (a failing agent output walked through all five checks,
plus its corrected passing twin — both JSON files included), and the
failure-report template.

**The companion tool is free.** FailLoud is also an open-source Python
package (MIT) that runs these exact checks *deterministically* — CLI,
library, and an MCP server your orchestrator can call inside the loop,
with exit codes CI can gate on. The skill is the judgment playbook your
agent carries everywhere; the tool is the reproducible verdict. Get it at
github.com/Yalakala-Naveen/failloud (a browser playground runs the same
checks — no install).

Built by a Forward Deployed Engineer from production failures: every
check in this skill exists because a real agent failed this way in
production and the miss became a rule.

## Suggested price

**$19 one-time.**

Rationale: priced as a reusable production gate with worked examples, not
a one-shot prompt pack — and one caught silent failure (a placeholder page
shipped, a "sent" that never happened) costs more than the listing.

## Category suggestion

Development — Testing & QA / Agent Reliability (primary);
AI Agents — Workflows (secondary).

## Search keywords

- agent output verification
- ai agent done check
- agent testing checklist
- llm agent reliability
- silent failures agents
- claude code verification skill
- agent evals pre-ship
- verify agent claims evidence
