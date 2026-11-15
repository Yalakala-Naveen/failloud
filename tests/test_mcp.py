"""End-to-end MCP test: launch the real server over stdio and call its
tools the way an MCP client (an agent) would.

Skipped when the ``mcp`` extra is not installed.
"""

import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import anyio  # noqa: E402
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

FAILING = json.dumps({"status": "done", "output": {"body": "Lorem ipsum."}})
PASSING = json.dumps({"status": "done", "output": {"body": "Finished, real work."}})


def _server_params() -> StdioServerParameters:
    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "failloud.mcp_server"],
        env=env,
    )


async def _exercise() -> dict:
    with anyio.fail_after(60):
        return await _exercise_inner()


async def _exercise_inner() -> dict:
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]

            fail_call = await session.call_tool("check_output", {"output_json": FAILING})
            fail_payload = json.loads(fail_call.content[0].text)

            pass_call = await session.call_tool("check_output", {"output_json": PASSING})
            pass_payload = json.loads(pass_call.content[0].text)

            report_call = await session.call_tool(
                "failure_report", {"output_json": FAILING}
            )
            report_text = report_call.content[0].text

            receipt_call = await session.call_tool(
                "create_verification_receipt", {"output_json": PASSING}
            )
            receipt_payload = json.loads(receipt_call.content[0].text)

            chain_call = await session.call_tool(
                "verify_receipt_chain",
                {"receipts_json": json.dumps([receipt_payload])},
            )
            chain_payload = json.loads(chain_call.content[0].text)

            recheck_doc = json.dumps({
                "status": "done",
                "claims": [{"action": "email_sent", "target": "a@x.com",
                            "evidence": {"message_id": "m1"}}],
                "counts": {"delivered": 1},
                "output": {"body": "Real deliverable body."},
            })
            recheck_record = json.dumps({
                "bounced": [{"message_id": "m1", "reason": "mailbox not found"}],
                "counts": {"delivered": 0},
            })
            recheck_call = await session.call_tool(
                "recheck_against_record",
                {"output_json": recheck_doc, "record_json": recheck_record},
            )
            recheck_payload = json.loads(recheck_call.content[0].text)
    return {
        "tools": names,
        "receipt": receipt_payload,
        "chain": chain_payload,
        "fail": fail_payload,
        "pass": pass_payload,
        "report": report_text,
        "recheck": recheck_payload,
    }


def test_mcp_server_end_to_end():
    result = anyio.run(_exercise)
    for expected in (
        "check_output",
        "check_placeholder",
        "check_evidence",
        "check_stale_state",
        "check_counts",
        "check_completeness",
        "failure_report",
        "create_verification_receipt",
        "verify_receipt_chain",
        "recheck_against_record",
    ):
        assert expected in result["tools"]
    assert result["fail"]["verdict"] == "FAIL"
    assert result["pass"]["verdict"] == "PASS"
    assert result["report"].startswith("# FAILURE REPORT")
    assert result["receipt"]["verdict"] == "PASS"
    assert len(result["receipt"]["receipt_hash"]) == 64
    assert result["chain"] == {"valid": True, "count": 1, "problems": []}
    assert result["recheck"]["first_pass_label"] == "PROVISIONAL PASS"
    assert result["recheck"]["verdict"] == "CONTRADICTED"
    assert result["recheck"]["claims"][0]["status"] == "contradicted"
