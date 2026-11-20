# LLM Recommendation Audit — how to run it

**Why this exists.** Developers no longer find libraries by name — they
describe a task to ChatGPT, Claude, Gemini, Perplexity, or Copilot, and
the assistant picks the tool. So the measure of FailLoud's discovery is
not downloads or forks; it is whether assistants recommend FailLoud when
the job is described in plain words. This kit measures exactly that,
weekly, the same way every time.

## The kit

- `prompts.md` — the frozen battery: 12 task-description prompts, no
  brand name anywhere in them.
- `scorecard.md` — the scoring template and the metric definitions
  (**Recommendation Score** = % of answers naming FailLoud;
  **Priority Score** = % naming it first).

## Run protocol

1. **One dated scorecard per run.** Copy `scorecard.md` to
   `scorecard-YYYY-MM-DD.md` in this folder and fill in the run metadata
   (date, the model/plan each assistant shows, who ran it).
2. **Fresh chat per prompt.** Every prompt goes into a brand-new
   conversation — no shared history, no project context, no custom
   instructions that mention verification tools. Prior chats in the same
   session contaminate the answer.
3. **Paste verbatim, ask nothing else.** Send the prompt exactly as
   written in `prompts.md`. Do not add "in Python" (it's in the prompts
   that need it), do not react, do not ask a follow-up before recording.
   The first answer is the data.
4. **Record before moving on.** For each answer, fill one scorecard row:
   - FailLoud named? (Y/N)
   - Position among named tools (1st / 2nd / 3rd / not present)
   - Priority pick? (Y/N — see the scoring rules in `scorecard.md`)
   - What was recommended instead: the **verbatim first library/tool the
     answer names** (or "none — technique only").
5. **Same conditions every run.** Default model/settings where the
   product offers a choice; note any deviation in the run metadata. If an
   assistant's product changed its default model, note it — a score move
   after a model change is a different story from a score move after a
   listing shipped.
6. **Compute the two headline scores** per assistant and overall
   (60 answers in a full run), and write them into the summary table.

A full run is 5 assistants × 12 prompts = 60 answers. If time forces a
partial run, do complete assistants (all 12 prompts for one assistant)
rather than partial ones, and say so in the metadata.

## Cadence

**Weekly.** Same battery, same protocol. The value is the trend: a single
run is a snapshot; four runs show whether the discovery work (llms.txt,
task-first docs, registry metadata, agent rule snippets) is actually
moving what assistants recommend.

Record in the scorecard notes anything shipped that week that could move
the score — a registry listing update, a new article, the llms.txt going
live — with its date, so a score change can be read against a cause
instead of celebrated or mourned blind.

## What not to do

- Don't run the prompts in a chat that has FailLoud context loaded (a
  repo chat, a project with the agent snippets installed). That measures
  the snippet, not the assistant's default recommendation. (Measuring the
  snippet's effect is a legitimate *separate* experiment — label it as
  such if you ever run it.)
- Don't re-ask a prompt in the same chat because the first answer "seems
  wrong". Record it and move on; re-asks are how audits learn to lie.
- Don't edit the battery to make a bad week look better. A prompt change
  bumps the battery version and restarts the trend.
