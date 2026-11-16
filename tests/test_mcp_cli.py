"""The ``failloud mcp`` subcommand.

MCP Registry clients launch the server through the main CLI —
``uvx --from failloud[mcp] failloud mcp`` — so the subcommand must be
registered and must serve the same server as the ``failloud-mcp``
script. The stdio smoke test follows the pattern of test_mcp.py and is
skipped when the ``mcp`` extra is not installed.
"""

import os
import sys
from pathlib import Path

import pytest

from failloud.cli import build_parser, main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mcp_subcommand_registered():
    args = build_parser().parse_args(["mcp"])
    assert args.command == "mcp"
    assert callable(args.func)


def test_mcp_subcommand_launches_the_mcp_server_main(monkeypatch):
    pytest.importorskip("mcp")
    import failloud.mcp_server as mcp_server

    calls = []
    monkeypatch.setattr(mcp_server, "main", lambda: calls.append("served"))
    assert main(["mcp"]) == 0
    assert calls == ["served"]


def test_mcp_subcommand_serves_over_stdio():
    pytest.importorskip("mcp")
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "failloud.cli", "mcp"],
        env=env,
    )

    async def _run() -> list:
        with anyio.fail_after(60):
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return [t.name for t in tools.tools]

    names = anyio.run(_run)
    for expected in ("check_output", "failure_report", "recheck_against_record"):
        assert expected in names
