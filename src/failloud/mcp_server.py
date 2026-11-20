"""FailLoud as an MCP server.

Exposes the checks as Model Context Protocol tools over stdio, so any
agent or orchestrator that speaks MCP can verify its own output — or a
sub-agent's — before acting on it. This is the point of the tool living in
the agent ecosystem rather than next to it: the verifier sits inside the
loop, one tool call away from the work.

Run it directly::

    failloud-mcp            # after pip install "failloud[mcp]"
    failloud mcp            # same server, through the main CLI — the
                            # launch command MCP Registry clients use
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
from .recheck import provisional_label, recheck_output
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

_INSTRUCTIONS = (
    "Verify an AI agent's answer, output, or tool call before you act on it. "
    "FailLoud deterministically checks agent output JSON for the silent "
    "failures agents ship as 'done': placeholder content (FL001), claimed "
    "actions with no evidence they happened (FL002), work based on stale "
    "state (FL003), reported counts that contradict the itemized record "
    "(FL004), missing or silently empty components (FL005), and RAG answers "
    "whose citations or numbers the retrieved sources do not support "
    "(FL006). Call check_output before trusting, forwarding, or executing "
    "another agent's output; call check_groundedness to check whether an "
    "LLM answer is supported by its sources."
)

try:
    server = _ServerClass("failloud", instructions=_INSTRUCTIONS)
except TypeError:  # an SDK build without the instructions kwarg
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
    """Verify an AI agent's answer or tool call before you act on it: run
    all six FailLoud checks over an agent output JSON document.

    Catches outputs that claim "done" while the payload is placeholder
    (FL001), claimed actions with no evidence they happened (FL002), work
    based on stale state (FL003), reported counts that contradict the
    itemized record (FL004), missing or silently empty components (FL005),
    and RAG answers whose citations or numbers the retrieved sources do
    not support (FL006). Returns the full result as JSON: verdict (PASS /
    PASS WITH WARNINGS / FAIL), error and warning counts, and every
    finding with its JSON path. Use this before trusting, forwarding, or
    executing another agent's output.
    """
    doc = _parse(output_json)
    result = run_checks(
        doc, _config(max_state_age_hours, max_segment_gap_seconds, required_paths)
    )
    return json.dumps(result.to_dict(), indent=2)


@server.tool()
def check_placeholder(output_json: str) -> str:
    """Check whether an agent output is safe to treat as final: is its
    payload empty or still placeholder text (lorem ipsum, {{template}}
    braces, "coming soon") while the run claims completion? FL001 only."""
    outcome = run_single(_parse(output_json), "FL001")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_evidence(output_json: str) -> str:
    """Check whether an agent actually did what it claims: does every
    claimed action (sent, posted, published, updated…) carry evidence — an
    id, URL, receipt, or artifact — that it actually happened? FL002
    only."""
    outcome = run_single(_parse(output_json), "FL002")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_stale_state(output_json: str, max_state_age_hours: float = 24.0) -> str:
    """Check whether an agent worked from state you can still trust: was
    the state/context it used already older than max_state_age_hours,
    missing a freshness timestamp, or version-skewed? FL003 only."""
    outcome = run_single(
        _parse(output_json), "FL003", CheckConfig(max_state_age_hours=max_state_age_hours)
    )
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_counts(output_json: str) -> str:
    """Check whether the numbers in an agent's report are true: do the
    reported counts reconcile with the itemized lists in the same
    document, and does every total equal the sum of its parts? FL004
    only."""
    outcome = run_single(_parse(output_json), "FL004")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_completeness(
    output_json: str,
    required_paths: str = "",
    max_segment_gap_seconds: float = 2.0,
) -> str:
    """Check whether an agent's deliverable is actually complete: are the
    required components present and non-empty, and are there dead
    stretches inside segmented deliverables? FL005 only. Pass
    required_paths as comma-separated dotted paths, e.g.
    "output.url,output.body"."""
    outcome = run_single(
        _parse(output_json),
        "FL005",
        _config(required_paths=required_paths, max_segment_gap_seconds=max_segment_gap_seconds),
    )
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def check_groundedness(output_json: str) -> str:
    """Check whether a RAG / LLM answer is supported by its sources before
    you present or act on it: do its citations resolve to sources that
    were actually retrieved (no hallucinated citations), are the cited
    sources non-empty, and does every number in the answer appear in the
    sources? FL006 only."""
    outcome = run_single(_parse(output_json), "FL006")
    return json.dumps(outcome.to_dict(), indent=2)


@server.tool()
def failure_report(output_json: str, required_paths: str = "") -> str:
    """Verify an agent output before it is trusted and return the Markdown
    FAILURE REPORT — the human-readable artifact to attach to a run,
    issue, or pull request."""
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
    """Verify an agent output and seal the verdict into a hash-chained
    receipt, so a later step can prove the verdict it acted on was never
    altered. Runs all checks and returns the receipt.

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
    """Check that a chain of FailLoud verification receipts is intact
    before trusting the verdicts recorded in it: every receipt unaltered,
    every link in order.

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


@server.tool()
def recheck_against_record(output_json: str, record_json: str) -> str:
    """Re-judge an agent's claims against the system of record before
    treating its "done" as fact (second pass).

    A first-pass PASS is provisional — the output only had to agree with
    itself. Pass the original output and a later snapshot from the system
    of record (a provider export, a database extract) and every claim and
    reported count comes back confirmed, contradicted, or unverifiable.
    Evidence that now sits in a failure context (bounced, rejected,
    failed) contradicts the claim that carried it. Returns JSON with the
    first verdict, the provisional label, the second-pass verdict
    (CONFIRMED / CONTRADICTED / UNVERIFIABLE / FAIL), and the per-claim
    and per-count detail."""
    doc = _parse(output_json)
    try:
        record = json.loads(record_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"record_json is not valid JSON: {exc}") from exc
    first = run_checks(doc, _config())
    result = recheck_output(doc, record, first_result=first)
    payload = result.to_dict()
    payload["first_pass_label"] = provisional_label(first)
    return json.dumps(payload, indent=2)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
