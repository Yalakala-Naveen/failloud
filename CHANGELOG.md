# Changelog

## 0.5.1 — 2026-11-15

MCP Registry readiness: the two gaps that would have failed a registry
listing, fixed. No behaviour changes to the checks themselves.

- New `failloud mcp` subcommand: runs the MCP server over stdio,
  launching exactly what the `failloud-mcp` script launches. Registry
  clients start the server with
  `uvx --from failloud[mcp] failloud mcp`; in 0.5.0 that command did
  not exist (the server was only reachable via `failloud-mcp`), so the
  registry's run command would have failed on first launch. Without
  the `mcp` extra installed, the subcommand exits 2 with the install
  hint instead of a traceback.
- The package README — the long description the registry reads from
  PyPI for ownership verification — now carries the registry ownership
  marker (`mcp-name: io.github.Yalakala-Naveen/failloud`). The marker
  was added to the repo README after 0.5.0 shipped, so 0.5.0's
  published README could never have verified.
- `server.json` updated to 0.5.1 (manifest version, package version,
  and the `--from failloud[mcp]==0.5.1` runtime pin) and re-validated
  against the official registry schema.
- 147 tests (3 new), covering the subcommand's registration, that it
  dispatches to the same server entry point as `failloud-mcp`, and a
  live stdio handshake through `failloud mcp`.

## 0.5.0 — 2026-11-15

Second-pass verification: a PASS is provisional until the record confirms it.

- New `recheck` module: `provisional_label` names every first-pass
  verdict honestly (a FAIL is final; a pass is PROVISIONAL), and
  `recheck_output(original, record)` re-judges a completed output
  against a later snapshot from the system of record — a provider
  delivery export, a database extract, the receiving system's log.
- Every claim and every reported count comes back `confirmed`,
  `contradicted`, or `unverifiable`. Evidence found in the record with
  no failure marker confirms; evidence under a bounce/failure key, or
  in an entry whose status says it failed, contradicts; a record that
  never mentions the evidence does not confirm it — silence is never
  upgraded into a pass. Record list lengths override the record's own
  reported numbers (FL004's doctrine: the list is the true part).
- Motivated by the Nov 12 launch-thread critique: output-only checks
  pass a *consistently wrong* output ("9 sent" where one bounces
  later). The shipped example pair (`examples/second_pass_original.json`
  + `second_pass_record.json`) is exactly that case: provisional PASS,
  then CONTRADICTED, pinpointing the bounced message and the count.
- CLI: `failloud recheck OUTPUT RECORD [--format text|json]` — exit 0
  confirmed, 1 contradicted / unverifiable / already failed, 2 tool
  error. MCP server: new `recheck_against_record` tool.
- 144 tests (18 new), covering the bounce case, status-marked failures,
  unverifiable silence, count reconciliation, and the CLI/MCP contracts.

## 0.4.0 — 2026-11-14

Framework adapters, starting with LangChain: verify outputs in the loop.

- New `failloud.adapters.langchain` module: `to_failloud_doc` normalizes
  the shapes LangChain returns — bare strings, messages (dicts or
  objects, including multimodal text blocks), message transcripts,
  `LLMResult` generations, chain result dicts, agent finishes — into the
  FailLoud envelope, and `verify` checks a raw result in one call.
- `FailLoudCallbackHandler` hooks `on_llm_end` / `on_chain_end` /
  `on_agent_finish`, recording a verdict per finished step; with
  `raise_on_fail=True` it raises `FailLoudVerificationError` so a chain
  stops on a silent failure instead of building on it.
- Tool calls are preserved under `tool_calls` for inspection, never
  promoted to claims — a tool call is an intention, not evidence.
- Duck-typed and zero-dependency: the adapter never imports LangChain.
  New optional extra `failloud[langchain]` adds `langchain-core` so the
  handler subclasses the real `BaseCallbackHandler` when present.
- Runnable demo at `examples/langchain_adapter.py`.
- 126 tests (17 new), covering every normalized shape, placeholder and
  empty-output detection through the adapter, and the handler contract.

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
