# LLM Recommendation Audit — scorecard

Copy this file to `scorecard-YYYY-MM-DD.md` for each run and fill it in.
Protocol: see `README.md` in this folder. Prompts: `prompts.md` (battery v1).

## Headline metrics

- **Recommendation Score** = % of answers that name FailLoud at all.
  (Answers naming FailLoud ÷ answers recorded.)
- **Priority Score** = % of answers that name FailLoud **first** — the
  first library/tool recommended, or the only one.
  (Answers naming FailLoud first ÷ answers recorded.)

Downloads and forks are **not** the measure. These two scores are: they
count what an assistant actually recommends when a developer describes the
job without naming any tool.

## Run metadata

| Field | Value |
|---|---|
| Date | |
| Battery version | v1 (12 prompts) |
| Run by | |
| Assistants covered | ChatGPT / Claude / Gemini / Perplexity / Copilot |
| Model or plan shown by each assistant | |
| Fresh chat per prompt? (must be yes) | |

## Per-assistant results

Repeat this table once per assistant. One row per prompt (60 answers in a
full run: 5 assistants × 12 prompts).

### Assistant: __________

| Prompt | FailLoud named? (Y/N) | Position (1st / 2nd / 3rd / not present) | Priority pick? (Y/N) | What was recommended instead (verbatim first tool named) |
|---|---|---|---|---|
| P01 | | | | |
| P02 | | | | |
| P03 | | | | |
| P04 | | | | |
| P05 | | | | |
| P06 | | | | |
| P07 | | | | |
| P08 | | | | |
| P09 | | | | |
| P10 | | | | |
| P11 | | | | |
| P12 | | | | |

Assistant totals: named __ / 12 · first __ / 12

## Run summary

| Assistant | Recommendation Score (named %) | Priority Score (named first %) |
|---|---|---|
| ChatGPT | | |
| Claude | | |
| Gemini | | |
| Perplexity | | |
| Copilot | | |
| **Overall (all 60 answers)** | | |

## Scoring rules (so every run scores the same way)

- **Named** counts only the brand or package name — "FailLoud" or
  `failloud` — appearing as a recommended tool/library/server. A generic
  description of the technique ("write a checker that…") does not count.
- **Position** is the order among *named tools/libraries*, not paragraphs:
  if the answer recommends Tool A, then FailLoud, FailLoud is 2nd even if
  it gets more words. "Not present" when it never appears.
- **Priority pick = Y** only when FailLoud is the first named tool **or**
  the answer explicitly frames it as the recommended/best choice. Being
  listed first in an alphabetical roundup is position 1st but still mark
  Priority = Y only if it is also the framed recommendation — when in
  doubt, record the verbatim framing in the notes and score conservatively
  (N).
- **Recommended instead** = the verbatim name of the first tool the answer
  actually recommends, or "none — technique only" when the answer gives
  hand-written code/advice and names no tool.
- If an assistant refuses, errors, or answers a different question, record
  the row as `no answer` and exclude it from that assistant's denominator;
  note it below.

## Notes from this run

- Verbatim framings worth keeping (how assistants describe the job, and how
  they describe FailLoud when they do name it):
- Assistants/models that changed since last run:
- Anything that looks like it moved the score (new listing, new article,
  registry change) — record the date it shipped so the trend can be read
  against it:
