# Changelog

## 0.3.0 — 2026-11-13

Watch mode: verification that keeps up with a running pipeline.

- New `watch` module: `Watcher.poll_once()` checks every new or changed
  target in one deterministic sweep; `watch()` drives polling with
  `once` / `max_polls` / injectable sleep. Change detection is the
  SHA-256 of the file bytes — rewriting identical bytes never produces a
  duplicate verdict or receipt.
- CLI: `failloud watch PATH [--once] [--interval S] [--pattern GLOB]
  [--recursive] [--receipt-out receipts.jsonl]` watches a single JSON
  file or a directory of outputs. New files are picked up, deleted files
  forgotten, and a mid-write or invalid file reports an error and is
  retried when its bytes change — it never kills the watcher.
  `--once` follows the check exit contract over the whole sweep
  (0 all passed, 1 any failed/errored, 2 target missing); continuous
  watch runs until Ctrl-C and exits 0.
- With `--receipt-out`, every verdict is sealed into the hash-chained
  receipt chain as it happens — the audit trail builds itself.
- All `check` tuning flags (`--require`, `--schema`, `--only`,
  thresholds, `--format`) apply to watch unchanged. Core stays
  stdlib-only: polling, not a filesystem-events dependency, so behaviour
  is identical on Linux, macOS, and Windows.
- 109 tests (19 new), covering discovery, change detection, error
  isolation, receipt chaining, and the CLI exit contract.

## 0.2.0 — 2026-11-12

Hash-chained verification receipts: proof, not just reports.

- New `receipts` module: `create_receipt` seals a check result into a
  receipt carrying the full result plus two SHA-256 hashes — `result_hash`
  over the result and its source, `receipt_hash` over every receipt field
  including `prev_hash`, chaining each receipt to the one before it.
  `verify_receipt` / `verify_chain` detect any edited verdict or finding,
  dropped receipt, or reordering.
- CLI: `failloud check --receipt-out receipts.jsonl` appends a sealed
  receipt per run (the check's exit code still reflects the verdict alone);
  `failloud verify-receipts receipts.jsonl` re-verifies a chain file
  (0 valid, 1 invalid, 2 unreadable).
- MCP server: two new tools — `create_verification_receipt` and
  `verify_receipt_chain` — so an orchestrator can seal and audit verdicts
  inside the loop.
- Fixed the package's Homepage/Issues URLs, which pointed at a placeholder
  org instead of this repository.
- 90 tests (22 new), including receipt tamper/chain cases and MCP
  end-to-end coverage of the new tools.

## 0.1.0 — 2026-11-11

First release.

- Five checks for the silent failures agents ship as "done":
  FL001 `placeholder_shipped`, FL002 `unbacked_claim`, FL003 `stale_state`,
  FL004 `count_mismatch`, FL005 `missing_components`.
- CLI (`failloud check`, `failloud checks`) with text / Markdown / JSON
  reports and a CI-friendly exit-code contract (0 pass, 1 fail, 2 tool error).
- Python API: `check_output`, `run_checks`, `run_single`, `CheckConfig`.
- MCP server (`failloud-mcp`) exposing every check as a tool, compatible
  with the 1.x and 2.x Python MCP SDKs.
- Worked examples: an output that commits all five failures, its corrected
  twin, and a JSON Schema for required-component enforcement.
- 68 tests, including a live MCP stdio end-to-end test.
