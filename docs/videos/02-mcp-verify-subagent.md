# Video 2 — Verify a sub-agent's output inside Claude Code with an MCP server

**Title:** Verify a sub-agent's output inside Claude Code with an MCP server
**Length:** ~4 minutes, screen capture (Claude Code session).
**Target question:** "Is there an MCP server that can verify another agent's output inside the loop?"

## Description (first sentence is the one engines read)

FailLoud's MCP server verifies another agent's output inside the loop — before your orchestrator acts on a sub-agent's claim, FailLoud checks it deterministically: no evidence, no pass. FailLoud is a deterministic verification harness for LLM agent outputs — it catches the silent failures agents ship as "done." No LLM in the verdict path. CLI for CI (exit 0 pass / 1 failed output / 2 tool error), Python API, and an MCP server that verifies a sub-agent's output inside the loop, before you act on it.

Add it to Claude Code: `claude mcp add failloud -- uvx --from "failloud[mcp]" failloud-mcp`
GitHub: https://github.com/Yalakala-Naveen/failloud
Playground: https://yalakala-naveen.github.io/failloud/

11 MCP tools: the full check, one tool per silent failure, the Markdown failure report, hash-chained verification receipts, and a second-pass recheck against the system of record.

## Pinned comment

The rule I give my own agents (it's in the repo's agent/ folder as a Claude Code / Cursor / Copilot snippet): before you report done, and before you act on another agent's output, run the check. What do you let your sub-agents get away with today?

## Transcript (spoken, verbatim)

[0:00] "Is there an MCP server that can verify another agent's output inside the loop? There is now — it's called FailLoud, and in the next four minutes I'll wire it into Claude Code and watch it stop a sub-agent's lie before the orchestrator acts on it.

[0:20] The problem first. Multi-agent setups run on trust handovers: a worker agent reports 'done,' the orchestrator believes it, and the next step builds on a claim nothing ever proved. The worker said it sent twelve emails; its own record lists nine. The worker said it published; there's no URL anywhere. By the time a human looks, the lie has three layers of real work built on top of it.

[0:45] FailLoud is a deterministic verification harness for LLM agent outputs — it catches the silent failures agents ship as 'done.' It ships three ways: a CLI for CI, a Python API, and this MCP server, which exposes eleven tools — the full check, one per failure type, the failure report, even hash-chained verification receipts.

[1:05] Installing it is one line. [terminal] `claude mcp add failloud -- uvx --from failloud[mcp] failloud-mcp`. Done. No server to host — it runs locally over stdio, straight from PyPI. The same config works in Cursor and VS Code; it's in the README.

[1:25] Now the demo. I have a sub-agent that just reported its step complete — here's its output. [show JSON] Status done, summary confident. I ask Claude Code to verify it with FailLoud before continuing. [Claude Code calls check_output] And there's the failure report, inside the session: FL002 — the publish claim has no evidence. FL004 — reported twelve, record says nine.

[1:55] Watch what matters: the orchestrator *stops*. It doesn't summarise the lie into the next step; it sends the step back with the findings attached. The verdict is deterministic — same input, same verdict, every time — because no LLM sits in the verdict path. A judge model can be persuaded by a confident sub-agent. A count reconciliation cannot.

[2:20] Two more tools worth knowing. `create_verification_receipt` seals a passing verdict into a hash-chained receipt, so a later step can prove the output was verified, not just claim it. And `recheck_against_record` re-judges a provisional pass against a later system-of-record snapshot — confirmed, contradicted, or unverifiable.

[2:45] The snippet I run in my own projects is in the repo under agent/ — one paragraph for Claude Code, Cursor, or Copilot that says: before you report done, and before you act on another agent's output, run the check. Steal it.

[3:05] FailLoud is on PyPI and the official MCP Registry — links below. Next video: I ran it over sixty agent outputs that all claimed 'done.' Fifty-seven were lying. The dataset is published — bring your scepticism."
