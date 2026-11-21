# FailLoud Self-Audit — public claims vs the record

**Date:** 2026-11-20 · **Auditor:** Muse (Self-Audit Law strand: FailLoud)
**Surfaces checked:** local repo (`README.md`, `docs/`, `audits/`, `launch-content/`, `skill/`, `server.json`, `pyproject.toml`, `action.yml`), live Playground (yalakala-naveen.github.io/failloud), GitHub repo (API), PyPI (page + JSON API), live MCP Registry API, live Agensi listing, Glama-mirror copy (ai.tn), dev.to launch article.
**Ground truth used:** 0.6.0 · six checks FL001–FL006 · 162 tests · Silent Failure Audit 57/60 (95.0%), 10/10 clean, FL003 gap published · zero confirmed external users · 1 GitHub star (owner's own).
**Method notes:** test suite run in a clean venv (pytest only); Silent Failure Audit re-run from its own script; shipped examples re-run through `check_output`; MCP tool count counted in source; registry state read from the registry's own API. No public copy was edited — this file is the only write.

Findings are weakest first.

---

## F1 — Agensi's live paid listing still sells the five-check product

- **Surface:** Agensi listing, "FailLoud Verify: The Done-Check for AI Agent Output" (agensi.io/skills/failloud-verify-the-done-check-for-ai-agent-output), live and crawled 3 days before this audit. This is the $19 paid listing.
- **Exact claim:** "FailLoud Verify is the gate that runs before the claim. It teaches your agent to inspect its own output the way a skeptical reviewer would — **five checks**, each a concrete procedure…" — the listing enumerates FL001–FL005 only; FL006 `unsupported_answer` appears nowhere; "What's inside" promises "all five check procedures".
- **What the record supports:** The product has had **six** checks since 0.6.0 (Nov 16, 2026). The local source copy (`skill/LISTING.md`) was already corrected to six checks — the live listing was never refreshed after the correction. A buyer reading the listing is told the skill has five checks and no RAG groundedness check at all.
- **Severity:** Highest in this audit — it is a *paid* listing misdescribing what is sold. Fix is an owner/account step on Agensi (listing edit); cannot be done from the repo.

## F2 — Glama (and its mirrors) still present "The five silent failures"

- **Surface:** Glama listing copy, as mirrored by ai.tn ("FailLoud MCP server | AI Models Info", crawled 3 days before this audit; Glama refreshes from a README snapshot).
- **Exact claim:** Section heading "**The five silent failures**" with the table stopping at FL005; "The same **five checks** also ship as a `SKILL.md`"; "The repo ships a realistic agent output that commits **all five failures**".
- **What the record supports:** Six checks since 0.6.0. The repo's own `registry-submissions.md` already flags this debt ("Refresh the listing description to the canonical copy on glama.ai — account step") and it is still open. Anyone arriving via Glama meets a five-check tool that no longer exists.
- **Severity:** High — a live registry surface, stale in the same direction as F1. Fix is an account step on glama.ai.

## F3 — PyPI's long description is one generation behind GitHub

- **Surface:** PyPI project page for failloud 0.6.0 (release uploaded Nov 16, 2026; description is immutable per release).
- **Exact claim:** Not a false claim — an omission. The PyPI description is the pre-tuning README: it goes straight from the intro to "The six silent failures" and has **none** of the Nov 20 surfaces — no "What do you need to verify?" jobs section, no comparison table, no guides list, no "FailLoud by the numbers" line.
- **What the record supports:** Everything PyPI *does* say checks out (six checks, 162 tests in the Development section, 8-error demo, receipts/watch/adapter/recheck/FL006 sections all accurate). But the package page — the highest-traffic surface — is a generation older than the GitHub README it is supposed to mirror.
- **Severity:** Moderate. Only fixable by cutting a new release; worth folding into the next version bump rather than a metadata-only release on its own.

## F4 — "162 tests passing" is stated unconditionally; a plain run shows 159 passed, 3 skipped

- **Surface:** README ("**FailLoud by the numbers:** … 162 tests passing"; Development section "162 tests"), Playground ("zero-dependency core, 162 tests"), `llms.txt` and outreach drafts.
- **Exact claim:** "162 tests passing."
- **What the record supports:** The suite contains exactly 162 test functions (counted in `tests/`). Run in a clean venv with only pytest installed, the result is **159 passed, 3 skipped** — the MCP tests (`tests/test_mcp.py`, `tests/test_mcp_cli.py`) `importorskip("mcp")`. The claim is true under the documented dev setup (`pip install -e ".[mcp,dev]"`, which the README's Development section does specify), and the 0.5.1 changelog records a live MCP stdio test among its count. But the banner wording carries no condition, and a reader who clones and runs `pytest` — the exact reader FailLoud courts — sees a count that does not match the banner. That is the FL004 pattern (reported count vs itemized record) in FailLoud's own copy. This audit did not re-run the suite with the `mcp` extra installed; the 3 skips are MCP-gated by direct code inspection.
- **Severity:** Moderate — small, true-under-conditions, and maximally embarrassing for this particular product if a skeptic finds it first. Honest wording: "162 tests (3 MCP tests skip without the `mcp` extra)".

## F5 — The dev.to launch article now falsely says "Current release: 0.5.1"

- **Surface:** dev.to, "My Agent Said 'Done.' The Work Wasn't. So I Built a Done-Check." (published launch article; also syndicated to aiwithghost.com).
- **Exact claim:** "(**Current release: 0.5.1** — same checks, now also published in the official MCP Registry.)" The article throughout describes five checks and a five-row table.
- **What the record supports:** Current release is 0.6.0 with six checks. As a dated launch post the five-check framing is historical and fair; the words "Current release" are not — they are simply wrong today, on a permanent, indexed page that still ranks for the product.
- **Severity:** Low-moderate. Editable on dev.to in minutes (a one-line correction + a pointer to 0.6.0).

## F6 — `audits/scorecard-2026-11-20.md` contradicts itself

- **Surface:** The published baseline LLM-audit scorecard in the repo (`audits/scorecard-2026-11-20.md`).
- **Exact claim:** The run-summary table lists Claude as "— | — | **Waiting on user sign-in (no saved Claude login)**".
- **What the record supports:** The same file, further down, contains the completed Claude run (signed in as therembiq@gmail.com, **0/12 named, 0/12 first**). The combined 3/36 baseline quoted in summaries depends on that completed section, not on the summary table. The error understates completeness rather than inflating results — the honesty direction is safe — but a public audit artifact whose summary table disagrees with its own contents is exactly what a hostile reader quotes.
- **Severity:** Low-moderate. One-line table fix.

## F7 — "Best Python library" page title claims what its body declines to

- **Surface:** Guide page title/URL: "The best Python library for verifying LLM outputs in production" (linked from README's FAQ and guides list).
- **Exact claim:** The title asserts a superlative.
- **What the record supports:** The page body is honest — subtitle "an honest split", meta description splits the verdict by job (scored evals → DeepEval/Ragas, prompt comparison → Promptfoo, deterministic claim verification → FailLoud). Only the title/URL carries the unhedged claim. SEO-shaped and body-hedged, but the title is the part that gets quoted.
- **Severity:** Low. Judgment call, flagged for completeness.

## F8 — "Works with both the 1.x and 2.x Python MCP SDKs" is unevidenced in the repo

- **Surface:** README MCP section (also on PyPI).
- **Exact claim:** "Works with both the 1.x and 2.x Python MCP SDKs."
- **What the record supports:** `pyproject.toml` allows `mcp>=1.2` with no upper bound, so the claim is *permitted* by the constraint — but the repo contains exactly one MCP end-to-end test file set (4 tests), all `importorskip`-gated, and no recorded 2.x run. Nothing contradicts the claim; nothing in the record proves it either.
- **Severity:** Low. Either run it once against 2.x and keep the sentence, or soften to "requires the Python MCP SDK ≥1.2".

---

## Verified clean — checked, no finding

- **Version 0.6.0** is consistent on every current surface: `pyproject.toml`, `server.json` (version + the `failloud[mcp]==0.6.0` pin), PyPI latest release (JSON API: releases 0.2.0–0.6.0, latest 0.6.0, `requires_python >=3.10`), CHANGELOG head, GitHub Action examples (`@v0.6.0`).
- **MCP Registry state is correct:** the registry API's versions list shows **0.6.0 active, `isLatest: true`** (published Nov 18) and 0.5.1 active, not latest. (The search endpoint returns the 0.5.1 entry first — a reader stopping there could be misled, but the registry itself is right.)
- **Six checks are real:** six check modules in `src/failloud/checks/` with CHECK_IDs FL001–FL006 and names matching the README table exactly (`placeholder_shipped`, `unbacked_claim`, `stale_state`, `count_mismatch`, `missing_components`, `unsupported_answer`).
- **11 MCP tools is real:** 11 `@server.tool()` definitions in `src/failloud/mcp_server.py`; the tool names match the README and PyPI lists one for one.
- **Silent Failure Audit numbers re-derive exactly:** re-running `audits/silent-failure-audit/run_audit.py` regenerated **57/60 caught (95.0%)**, **10/10 clean passed, 0 false alarms**, FL003 at 7/10 with the three misses (fl003-02, -05, -08) being the no-freshness-timestamp variant raising a warning instead of an error. `results.md` is script-generated and the re-run matched it. The one published gap is real and described accurately everywhere it is cited.
- **Shipped examples reproduce their printed numbers:** `examples/failing_output.json` → FAIL with **8 errors, 1 warning** (matches README/Playground/PyPI verbatim); `examples/rag_failing.json` → **4 FL006 errors** (matches). `examples/passing_output.json` passes clean.
- **Zero-dependency core:** `pyproject.toml` declares `dependencies = []`; the MCP/LangChain pieces are optional extras, and the copy says so.
- **No users/adoption dressing anywhere public:** no download counts, no "trusted by", no star counts, no user claims in the README, docs, Playground, `llms.txt`, or PyPI page. GitHub API shows 1 star / 0 forks (the star is the owner's) and nothing public claims otherwise. The (local, unpublished) launch kit states "zero known users so far" and "One GitHub star" outright; listicle outreach drafts concede "tiny adoption… mine will be the smallest number on it". This is the cleanest part of the record.
- **Comparison table survives spot-checks:** DeepEval "50+ metrics" ✓; Promptfoo "~40 deterministic assertion types" and it does ship an MCP server ✓; LangSmith "Plus $39/seat/mo" ✓; licenses ✓ (DeepEval/Ragas/Guardrails AI Apache-2.0, Promptfoo MIT, LangSmith proprietary platform / MIT SDKs); the "Where the others win, plainly" paragraph concedes each competitor's actual strength. Two judgment calls a reader *could* argue — Ragas "CI exit-code gate: No built-in gate" (Ragas can be wired into pytest CI but ships no gate of its own; the cell is defensible as written) and DeepEval MCP "Platform-side (Confident AI)" (no first-party server; hedged accurately). No catchable falsehood found.
- **Historical "five" references in the current README are accurate, not stale:** "The original five checks verify an output against *itself*" (second-pass section), "commits the first five failures" for `failing_output.json` (FL006 passes on that example — verified), "The first five checks…" (FL006 section). All three are correct uses.
- **Local-only, NOT public (no action needed for honesty):** the untracked local `dist/` folder contains a 0.2.0-era `SKILL.md` saying "five checks", and untracked `launch-kit-posts.md` says the MCP Registry listing is "currently at 0.5.1; 0.6.0 re-publish pending". `git ls-files` confirms neither is tracked or published; the registry claim is also simply outdated locally (0.6.0 is live and latest). Local cleanup only.

## Bottom line

The core product claims — version, six checks, 11 tools, zero dependencies, the 95.0% audit with its published gap, the example numbers — all verify against the record, and no surface inflates users or adoption. The exposure is concentrated in **stale third-party listings (F1 Agensi, F2 Glama)** that still sell/describe the five-check 0.5.x product, plus small precision debts (F3–F6) that matter more for FailLoud than for most products, because its entire pitch is that reported numbers must match the record.
