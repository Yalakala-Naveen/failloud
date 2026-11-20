# Video 1 — My agent said "done". Nothing happened.

**Title:** My agent said "done". Nothing happened.
**Length:** ~4 minutes, screen capture (terminal + Playground).
**Target question:** "My agent says done when nothing actually happened — how do I check agent outputs for silent failures?"

## Description (first sentence is the one engines read)

FailLoud catches the silent failures agents ship as "done" — this video runs FailLoud on a real failing agent output and shows every lie it catches. FailLoud is a deterministic verification harness for LLM agent outputs — it catches the silent failures agents ship as "done." No LLM in the verdict path. CLI for CI (exit 0 pass / 1 failed output / 2 tool error), Python API, and an MCP server that verifies a sub-agent's output inside the loop, before you act on it.

Try it in your browser (no install): https://yalakala-naveen.github.io/failloud/
GitHub: https://github.com/Yalakala-Naveen/failloud
Install: pip install failloud

The six silent failures: placeholder shipped as final · claimed actions with no evidence · stale state · counts that contradict the record · missing components · RAG answers unsupported by their sources.

## Pinned comment

The output in this video is in the repo: examples/failing_output.json — run `failloud check` on it yourself. Its corrected twin passes clean. What silent failure has your agent shipped as "done"?

## Transcript (spoken, verbatim)

[0:00] "My agent said 'done.' Nothing happened. The digest it claimed to send? Never sent. The card it claimed to publish? No URL, no post, nothing. And every dashboard I had was green — because the agent graded its own homework. I'm Naveen, I build agent systems for a living, and this exact failure happened to me in production. So I built FailLoud.

[0:25] FailLoud is a deterministic verification harness for LLM agent outputs. It catches the silent failures agents ship as 'done.' No LLM in the verdict path — no second model grading the first — just six deterministic checks that reconcile what the agent *claimed* against the evidence inside its own output.

[0:45] Here's the actual output from that run. [show failing_output.json] Status: done. Summary: 'Sent the digest to 12 subscribers and published the summary card.' Sounds great. Now watch. [terminal] `failloud check failing_output.json`. Exit code one. Eight errors, one warning.

[1:05] Walk the report with me. FL001, placeholder shipped: the email body is literally lorem ipsum with a template brace still in it — shipped as final. FL002, unbacked claim: it says it published the card, and there is no id, no URL, no receipt anywhere in the claim. FL003, stale state: it planned from a snapshot seventy-seven hours old. FL004, count mismatch — this is my favourite — it reported twelve delivered. Its own itemized record lists nine. The agent's summary contradicted the agent's data, in the same document. FL005, missing components: a segment with zero length, and a five-and-a-half-second dead stretch in the deliverable.

[2:00] Five different lies, one 'done.' And notice — an LLM judge would probably pass this output. It's fluent, it's specific, it *sounds* done. Deterministic checks don't read the prose for reassurance. They reconcile the claim against the record.

[2:20] Here's the corrected twin. [terminal] Same command. Exit zero. Pass. Same input, same verdict, every time — that's what deterministic buys you: a gate you can put in CI, or between the steps of an agent loop, that cannot be talked into passing.

[2:40] You can run this in your browser right now — the Playground runs the same six checks on anything you paste. Link in the description. Or pip install failloud and point it at your own agent's output. Fair warning: the first run on a real pipeline is usually uncomfortable.

[3:00] In the next video I'll show the MCP server verifying a sub-agent's output *inside* Claude Code, before the orchestrator acts on it. If your agent has ever said 'done' and lied to you — tell me in the comments what it claimed. Those stories are literally where these six checks came from."
