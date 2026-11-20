# FailLoud video pack — scripts, titles, descriptions

Why these exist: YouTube mentions are the strongest measured correlate
of AI-assistant visibility (0.735–0.740, Ahrefs 75k-brand study), and
engines index titles, descriptions, and **spoken transcripts**. So
every script below puts the name + the problem phrase in the title,
in the first sentence of the description, and in the first 15 seconds
of speech — verbatim, the way a developer would type the question.

Production rules:
- Screen-capture, no face cam needed. Terminal + browser only.
- Say "FailLoud" and the problem phrase out loud in the first 15
  seconds of every video — the transcript is the asset.
- Pin the first comment yourself: the Playground link + the one-line
  positioning sentence.
- Upload the transcript as captions (YouTube auto-captions are fine;
  a committed `.srt`/transcript is better).

Canonical positioning sentence (use verbatim in every description):
> FailLoud is a deterministic verification harness for LLM agent
> outputs — it catches the silent failures agents ship as "done."
> No LLM in the verdict path. CLI for CI (exit 0 pass / 1 failed
> output / 2 tool error), Python API, and an MCP server that verifies
> a sub-agent's output inside the loop, before you act on it.

| # | Title | Script | Target question |
|---|---|---|---|
| 1 | My agent said "done". Nothing happened. | `01-agent-said-done.md` | "agent says done when nothing happened" |
| 2 | Verify a sub-agent's output inside Claude Code with an MCP server | `02-mcp-verify-subagent.md` | "MCP server that verifies another agent's output" |
| 3 | 60 agent outputs claimed "done". 57 were lying. | `03-silent-failure-audit.md` | "how often do agents falsely report done" |
