"""The one seam to Claude (aussiefy.claude): the request it sends."""

from conftest import FakeClaude, json_reply

from aussiefy import claude

import importlib
import json
from importlib.metadata import version

import anthropic
import pytest


@pytest.fixture
def sdk_transport():
    # SDK 1.x moved to httpx2; exercise each supported SDK with its own real transport types.
    http = importlib.import_module("httpx" if version("anthropic").startswith("0.") else "httpx2")
    requests = []

    def respond(request):
        requests.append(request)
        return http.Response(200, json={
            "id": "msg_offline", "type": "message", "role": "assistant", "model": "test-model",
            "content": [{"type": "text", "text": '{"ok":true}'}], "stop_reason": "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 5},
        })

    with anthropic.Anthropic(api_key="test-offline", base_url="https://sdk-test.invalid",
                             max_retries=0, http_client=anthropic.DefaultHttpxClient(
                                 transport=http.MockTransport(respond))) as client:
        yield client, requests


def test_real_sdk_serializes_structured_request_and_parses_reply(sdk_transport):
    client, requests = sdk_transport
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}},
              "required": ["ok"], "additionalProperties": False}
    assert claude.call_json(client, model="test-model", system="SYS", prompt="phrase", schema=schema,
                            max_tokens=100, effort="high", cache=True) == {"ok": True}
    [request] = requests
    assert request.method == "POST" and request.url.path == "/v1/messages"
    assert request.headers["x-api-key"] == "test-offline"
    assert all(beta in request.headers["anthropic-beta"] for beta in claude.BETAS)
    body = json.loads(request.content)
    assert body == {
        "model": "test-model", "max_tokens": 100, "fallbacks": "default",
        "system": [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "phrase"}],
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": schema}},
    }


def test_real_sdk_serializes_neutral_tools_and_cached_conversation(sdk_transport):
    from aussiefy.yarn import tool_definitions

    client, requests = sdk_transport
    tools = tool_definitions()
    messages = [{"role": "user", "content": "brief"},
                {"role": "assistant", "content": [{"type": "tool_use", "id": "tool_one", "name": "lookup",
                                                     "input": {"query": "tired"}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tool_one",
                                                "content": "options"}]}]
    response = claude.create(client, model="test-model", system="SYS", messages=messages, max_tokens=100,
                             tools=tools, cache=True)
    assert claude.json_reply(response, ("ok",)) == {"ok": True}
    [request] = requests
    body = json.loads(request.content)
    assert body["tools"] == tools and all(t["strict"] for t in body["tools"])
    assert body["messages"][1:] == messages[1:]
    assert body["messages"][0]["content"] == [
        {"type": "text", "text": "brief", "cache_control": {"type": "ephemeral"}}]
    assert body["cache_control"] == {"type": "ephemeral"}
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert body["output_config"] == {"effort": "low"}
    assert messages[0]["content"] == "brief"


def test_call_json_caches_only_the_system_prompt():
    """Many calls share the system prompt; each prompt is new, so a breakpoint after it would be a write no call
    reads."""
    client = FakeClaude(json_reply({"ok": True}), json_reply({"ok": True}))
    assert claude.call_json(client, model="m", system="SYS", prompt="phrase", schema={}, cache=True) == {"ok": True}
    assert client.kwargs["system"] == [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}]
    assert client.kwargs["messages"] == [{"role": "user", "content": "phrase"}]
    assert "cache_control" not in client.kwargs      # automatic caching would land after the prompt
    claude.call_json(client, model="m", system="SYS", prompt="phrase", schema={})
    assert client.kwargs["system"] == "SYS"
    assert "cache_control" not in client.kwargs


def _breakpoints(request: dict) -> int:
    """The cache_control markers a request carries: on blocks, plus the top-level automatic one."""
    def count(node) -> int:
        if isinstance(node, dict):
            return ("cache_control" in node) + sum(count(v) for k, v in node.items() if k != "cache_control")
        return sum(count(v) for v in node) if isinstance(node, list) else 0
    return count(request)


def test_a_cached_conversation_caches_its_growing_tail():
    """A loop's request (yarn's) marks the system prompt and the brief, and turns on automatic caching, which
    moves its breakpoint to the last block as the conversation grows: within the API's four, all at one TTL."""
    client = FakeClaude(json_reply({}))
    messages = [{"role": "user", "content": "brief"}, {"role": "assistant", "content": "turn"},
                {"role": "user", "content": "result"}]
    tools = [{"name": "t", "description": "d", "input_schema": {"type": "object"}}]
    claude.create(client, model="m", system="SYS", messages=messages, tools=tools, max_tokens=10, cache=True)
    sent = client.kwargs
    assert sent["cache_control"] == {"type": "ephemeral"}
    assert sent["system"] == [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}]
    assert sent["messages"][0]["content"] == [{"type": "text", "text": "brief", "cache_control": {"type": "ephemeral"}}]
    assert sent["messages"][1:] == messages[1:]
    assert _breakpoints(sent) == 3
    assert messages[0]["content"] == "brief"    # the caller's conversation isn't changed


def test_an_uncached_request_carries_no_breakpoints():
    client = FakeClaude(json_reply({}))
    claude.create(client, model="m", system="SYS", messages=[{"role": "user", "content": "p"}], max_tokens=10)
    assert _breakpoints(client.kwargs) == 0
