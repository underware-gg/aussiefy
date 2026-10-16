"""Portable retelling and real stdio MCP work without a built-in model client."""

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import textwrap

from aussiefy.retelling import tool_contracts
from aussiefy.yarn import tool_definitions

ROOT = Path(__file__).resolve().parents[2]


def test_api_tool_shapes_are_adapted_from_neutral_contracts():
    contracts = {t["name"]: t for t in tool_contracts()}
    assert set(contracts) == {"lookup", "lint", "submit"}
    assert all(set(t) == {"name", "description", "schema"} for t in contracts.values())
    for tool in tool_definitions():
        assert tool["input_schema"] == contracts[tool["name"]]["schema"]
        assert tool["description"] == contracts[tool["name"]]["description"]
        assert tool["strict"] is True


def test_agent_driven_session_needs_no_provider_sdk(tmp_path):
    program = textwrap.dedent('''
        import builtins
        original_import = builtins.__import__
        def without_provider(name, *args, **kwargs):
            if name.split('.')[0] in {'anthropic', 'openai'}:
                raise AssertionError('Shared retelling tried to load a provider SDK')
            return original_import(name, *args, **kwargs)
        builtins.__import__ = without_provider
        from aussiefy import Translator
        from aussiefy.retelling import brief, dispatch_tool, tool_contracts
        session = brief('She was tired and very hungry.', vulgarity=0,
                        translator=Translator(lookup_embedder=None))
        choices, accepted = dispatch_tool(session, 'lookup', {'query': 'very tired'})
        assert choices['results'] and not accepted
        invalid = "Y'all changed the color."
        checked, _ = dispatch_tool(session, 'lint', {'text': invalid})
        assert not checked['ok']
        rejected, accepted = dispatch_tool(session, 'submit', {'text': invalid, 'declined': []})
        assert not accepted and rejected['problems']
        submitted, accepted = dispatch_tool(session, 'submit', {'text': session.plan['draft'], 'declined': []})
        assert accepted and submitted['accepted']
        assert all('input_schema' not in t for t in tool_contracts())
    ''')
    subprocess.run([sys.executable, "-c", program], cwd=tmp_path, check=True, capture_output=True,
                   text=True, timeout=30, env={**os.environ, "PYTHONPATH": str(ROOT)})


def test_stdio_entry_point_serves_the_shared_toolkit(tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise():
        server = StdioServerParameters(command=sys.executable, args=["-m", "aussiefy.mcp_server"],
                                       cwd=tmp_path, env={"AUSSIEFY_HOME": str(tmp_path / "home"),
                                                          "PYTHONPATH": str(ROOT)})
        async with stdio_client(server) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                tools = await client.list_tools()
                assert {t.name for t in tools.tools} == {
                    "aussie_guide", "aussie_plan", "aussie_lookup", "aussie_lint", "aussie_translate", "aussie_verify"}
                result = await client.call_tool("aussie_translate", {"text": "I'm extremely busy.", "level": 4, "seed": 7})
                assert not result.is_error
                output = result.structured_content
                assert output["text"] == "I'm flat out like a lizard drinking."
                checked = await client.call_tool("aussie_verify", {
                    "text": output["text"], "original": "I'm extremely busy.", "level": 4})
                assert not checked.is_error and checked.structured_content["ok"]

    asyncio.run(asyncio.wait_for(exercise(), timeout=30))
