# FailLoud — MCP registry & directory submissions

Status board and ready-to-submit copy for every MCP registry/directory.
Rule from the GEO playbook (§5 A5): **identical name, identical one-line
description, same install command, link back to GitHub — everywhere.**
Last swept: 2026-11-20.

## Canonical listing copy (use verbatim)

- **Name:** FailLoud
- **Registry name:** `io.github.Yalakala-Naveen/failloud`
- **One-line description (from server.json):**
  "Verify an AI agent's answer or tool call before you act on it: FailLoud deterministically checks agent outputs for placeholder content shipped as done, claimed actions with no evidence, stale state, counts that contradict the record, missing components, and RAG answers unsupported by their sources."
- **Short description (for character-limited forms):**
  "Deterministic verification harness for LLM agent outputs. Catches the silent failures agents ship as 'done' — no LLM in the verdict path. CLI, Python API, and an MCP server that verifies a sub-agent's output inside the loop."
- **Long description:**
  "FailLoud is a deterministic verification harness for LLM agent outputs — it catches the silent failures agents ship as 'done.' Six checks: FL001 placeholder_shipped (done declared over placeholder payload), FL002 unbacked_claim (a claimed action with no id, URL, receipt or artifact), FL003 stale_state (work planned from state older than allowed, untimestamped, or version-skewed), FL004 count_mismatch (reported counts contradicting the itemized record), FL005 missing_components (present-but-empty fields, silent segments), FL006 unsupported_answer (RAG citations resolving to nothing retrieved, numbers appearing in no source). No LLM sits in the verdict path: same input, same verdict, every time. Ships as a CLI with a CI exit-code contract (0 pass / 1 failed output / 2 tool error), a zero-dependency Python library, a GitHub Action, and this MCP server — 11 tools including the full check, per-check tools, the Markdown failure report, hash-chained verification receipts, and a second-pass recheck that judges a provisional pass against a later system-of-record snapshot. 162 tests. MIT."
- **Install (stdio):** `uvx --from "failloud[mcp]" failloud-mcp`
- **Claude Code one-liner:** `claude mcp add failloud -- uvx --from "failloud[mcp]" failloud-mcp`
- **Repository:** https://github.com/Yalakala-Naveen/failloud
- **Website / docs:** https://yalakala-naveen.github.io/failloud/
- **PyPI:** https://pypi.org/project/failloud/
- **License:** MIT
- **Author:** Naveen Yalakala (Forward Deployed Engineer)
- **Categories/tags:** developer-tools, verification, evaluation, agents, agent-output, ci, quality, testing
- **Tools (11):** check_output, check_placeholder, check_evidence, check_stale_state, check_counts, check_completeness, check_groundedness, failure_report, create_verification_receipt, verify_receipt_chain, recheck_against_record

## Status per platform

| Platform | Status | Repo-side artifact | Remaining step |
|---|---|---|---|
| Official MCP Registry | **LIVE** — `io.github.Yalakala-Naveen/failloud`, v0.6.0 | `server.json` (current) | Re-publish on each version bump (commands below) — account step |
| GitHub MCP Registry (github.com/mcp) | Not yet listed — curated (~740 servers) | `server.json` | Submit via GitHub's registry onboarding with the canonical copy — platform step |
| Claude Connectors Directory | Not yet submitted | This file | Submit Anthropic's directory form — platform step. Caveat: the directory is remote-server-first; FailLoud is a local stdio server, so expect the Community/desktop path rather than a hosted connector slot |
| Cursor Marketplace | Not yet submitted | This file | Submit the publish form at cursor.com/marketplace with the canonical copy — platform step |
| cursor.directory | Not yet submitted | This file | Submit via cursor.directory (community directory) — platform step |
| Smithery | **Changed** — acquired by Arcade (Aug 2026); proxy/hosting shut down 2026-10-31; self-serve publish closed; directory now curated | `smithery.yaml` (in repo) | No form exists today; request inclusion if/when Arcade reopens submissions — platform step |
| Glama | **Listed + claimed** (Nov 2026); Glama also imports the official registry | `glama.json` (maintainers) | Refresh the listing description to the canonical copy on glama.ai — account step |
| PulseMCP | **Submissions paused** — PulseMCP is not taking new servers; it ingests the official registry | — (registry entry is the feed) | None possible; FailLoud's live registry entry is the pickup source when ingestion resumes |
| mcp.so | Not yet submitted | This file | Submit the form at mcp.so/submit with the canonical copy — platform step |
| MCP Market (mcpmarket.com) | Not yet submitted | This file | Submit form / registry import — platform step |
| Docker MCP Catalog | Not yet submitted — needs a Docker image + PR to docker/mcp-registry | Dockerfile copy below (prepared, untested — no Docker in the build environment) | Build/push the image, open the catalog PR — platform step |
| awesome-mcp-servers (punkpeye) | **PR #19633 ALREADY OPEN** — "Add FailLoud MCP server" (Developer Tools section). Do not duplicate | — | Optional: author updates the PR body, which cites registry v0.5.1, to v0.6.0 — account step |
| Agensi (SKILL.md listing) | **LIVE** — "FailLoud Verify: The Done-Check for AI Agent Output" | `skill/SKILL.md`, `skill/LISTING.md` | None |

## Official MCP Registry — re-publish commands (account step)

Run from the repo root (where `server.json` lives) on each version bump.
Requires interactive GitHub authentication as Yalakala-Naveen:

```console
$ mcp-publisher login github
$ mcp-publisher publish
```

## Docker MCP Catalog — prepared Dockerfile (platform step)

Untested in the build environment (no Docker available there); verify
with `docker build` before submitting the catalog PR:

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir "failloud[mcp]==0.6.0"
ENTRYPOINT ["failloud-mcp"]
```

Catalog submission is a PR adding a server entry under
`docker/mcp-registry` pointing at the published image, with the canonical
one-line description above.
