"""FailLoud as an MCP server.

Exposes the checks as Model Context Protocol tools over stdio, so any
agent or orchestrator that speaks MCP can verify its own output — or a
sub-agent's — before acting on it. This is the point of the tool living in
the agent ecosystem rather than next to it: the verifier sits inside the
loop, one tool call away from the work.

Run it directly::

    failloud-mcp            # after pip install "failloud[mcp]"
    python -m failloud.mcp_server

Or register it with an MCP client::

    {
      "mcpServers": {
        "failloud": { "command": "failloud-mcp" }
      }
    }

Tools return JSON strings (the full machine-readable result), except
``failure_report``, which returns the Markdown report.
"""

from __future__ import annotations

import json
from typing import Any

from .engine import run_checks, run_single
from .models import CheckConfig
from .receipts import create_receipt, verify_chain
from .report import render_markdown

try:
    # mcp 1.x: FastMCP. mcp 2.x: renamed to MCPServer, same decorator API.
    try:
        from mcp.server.fastmcp import FastMCP as _ServerClass
    except ImportError:
        from mcp.server.mcpserver import MCPServer as _ServerClass
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        'The MCP server needs the "mcp" extra: pip install "failloud[mcp]"'
    ) from exc

server = _ServerClass("failloud")


def _parse(output_json: str) -> Any:
    try:
        return json.loads(output_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"output_json is not valid JSON: {exc}") from exc


def _config(
    max_state_age_hours: float = 24.0,
    max_segment_gap_seconds: float = 2.0,
    required_paths: str = "",
) -> CheckConfig:
    required = tuple(p.strip() for p in required_paths.split(",") if p.strip())
    return CheckConfig(
        max_state_age_hours=max_state_age_hours,
        max_segment_gap_seconds=max_segment_gap_seconds,
        required_paths=required,
    )


@server.tool()
def check_output(
    output_json: str,
    max_state_age_hours: float = 24.0,
    max_segment_gap_seconds: float = 2.0,
    required_paths: str = "",
) -> str:
    """Run all FailLoud checks over an agent output JSON document.

    Returns the full result as JSON: verdict (PASS / PASS WITH WARNINGS /
    FAIL), error and warning counts, and every finding with its JSON path.
    Use this before trusting or forwarding another agent's output.
    """
    doc = _parse(output_json)
    result = run_checks(
        doc, _config(max_state_age_hours, max_segment_gap_seconds, required_paths)
    )
    return json.dumps(result.to_dict(), indent=2)


@server.tool()
def check_placeholder(output_json: str) -> str:
    """FL001 only: is the output's payload empty or still placeholder text
    while the run claims completion?"""
    outcome = run_single(_parse(output_json), "FL001")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_evidence(output_json: str) -> str:
    """FL002 only: does every claimed action carry evidence — an id, URL,
    receipt, or artifact — that it actually happened?"""
    outcome = run_single(_parse(output_json), "FL002")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_stale_state(output_json: str, max_state_age_hours: float = 24.0) -> str:
    """FL003 only: was the state/context the run used already older than
    max_state_age_hours, missing a freshness timestamp, or version-skewed?"""
    outcome = run_single(
        _parse(output_json), "FL003", CheckConfig(max_state_age_hours=max_state_age_hours)
    )
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_counts(output_json: str) -> str:
    """FL004 only: do reported counts reconcile with the itemized lists in
    the same document?"""
    outcome = run_single(_parse(output_json), "FL004")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_completeness(
    output_json: str,
    required_paths: str = "",
    max_segment_gap_seconds: float = 2.0,
) -> str:
    """FL005 only: are required components present and non-empty, and are
    there dead stretches inside segmented deliverables? Pass required_paths
    as comma-separated dotted paths, e.g. "output.url,output.body"."""
    outcome = run_single(
        _parse(output_json),
        "FL005",
        _config(required_paths=required_paths, max_segment_gap_seconds=max_segment_gap_seconds),
    )
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def failure_report(output_json: str, required_paths: str = "") -> str:
    """Run all checks and return the Markdown FAILURE REPORT — the
    human-readable artifact to attach to a run, issue, or pull request."""
    doc = _parse(output_json)
    result = run_checks(doc, _config(required_paths=required_paths))
    return render_markdown(result, source="mcp:failure_report")


@server.tool()
def create_verification_receipt(
    output_json: str,
    prev_hash: str = "",
    max_state_age_hours: float = 24.0,
    max_segment_gap_seconds: float = 2.0,
    required_paths: str = "",
) -> str:
    """Run all checks and return a hash-chained verification receipt.

    The receipt embeds the full result plus SHA-256 hashes sealing it: pass
    the previous receipt's receipt_hash as prev_hash to extend a chain, and
    any holder of the chain can later prove no verdict was altered, dropped,
    or reordered. Returns the receipt as JSON."""
    doc = _parse(output_json)
    result = run_checks(
        doc, _config(max_state_age_hours, max_segment_gap_seconds, required_paths)
    )
    receipt = create_receipt(
        result,
        source="mcp:create_verification_receipt",
        prev_hash=prev_hash or None,
    )
    return json.dumps(receipt.to_dict(), indent=2)


@server.tool()
def verify_receipt_chain(receipts_json: str) -> str:
    """Verify a receipt chain: every receipt intact, every link in order.

    Pass a JSON array of receipt objects (as returned by
    create_verification_receipt). Returns JSON with valid (bool), the
    receipt count, and every problem found — an edited verdict, a dropped
    receipt, or a reordering each break the chain here."""
    try:
        payload = json.loads(receipts_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"receipts_json is not valid JSON: {exc}") from exc
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("receipts_json must be a receipt object or an array of them")
    problems = verify_chain(payload)
    return json.dumps(
        {"valid": not problems, "count": len(payload), "problems": problems},
        indent=2,
    )


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
