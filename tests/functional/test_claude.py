"""The one seam to Claude (aussiefy.claude): the request it sends."""

from conftest import FakeClaude, json_reply

from aussiefy import claude


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
