# Changelog

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
