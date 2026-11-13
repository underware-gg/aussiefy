"""A hosted MCP server narrows the toolkit by capability (DD-028): what it hides is gone from the schemas, the
descriptions and the instructions, what it caps is refused over the cap, and every tool is annotated read-only
on every server."""

import asyncio
import inspect

import pytest

from aussiefy import harness
from aussiefy.engine import Translator, default_translator

pytest.importorskip("mcp")
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

from aussiefy.mcp_server import build_server  # noqa: E402

TOOLS = {"aussie_entries": harness.list_entries, "aussie_wordless_meanings": harness.list_wordless_meanings,
         "aussie_entry": harness.get_entry,
         "aussie_random_entry": harness.random_entry, "aussie_suggest_name": harness.suggest_name,
         "aussie_variations": harness.variations, "aussie_bulldust": harness.bulldust, "aussie_lookup": harness.lookup, "aussie_lint": harness.lint, "aussie_guide": harness.guide,
         "aussie_plan": harness.plan, "aussie_translate": harness.translate, "aussie_verify": harness.verify}
HIDDEN = {"unlock", "include_gated", "document_config"}
HOSTED = {"allow_unlock": False, "allow_include_gated": False, "allow_document_config": False, "max_chars": 40, "max_query_chars": 12,
          "lookup_limit": 5}


@pytest.fixture(scope="module")
def hosted():
    return build_server(**HOSTED)


def _tools(server):
    return {t.name: t for t in asyncio.run(server.list_tools())}


def _params(fn):
    return {n for n in inspect.signature(fn).parameters if n not in {"translator", "preferences"} and not n.startswith("_")}


def test_hosted_schemas_drop_what_the_server_does_not_offer(hosted):
    for name, tool in _tools(hosted).items():
        assert set(tool.input_schema["properties"]) == _params(TOOLS[name]) - HIDDEN, name
        if "document_type" in _params(TOOLS[name]):
            assert "custom" not in tool.input_schema["properties"]["document_type"]["enum"], name


def test_hosted_descriptions_and_instructions_never_mention_what_is_hidden(hosted):
    texts = [t.description for t in _tools(hosted).values()] + [hosted.instructions]
    for text in texts:
        for word in (*HIDDEN, "Custom"):
            assert word not in text, (word, text[:80])


def test_every_tool_is_read_only_on_every_server(hosted):
    for server in (build_server(), hosted):
        for tool in _tools(server).values():
            a = tool.annotations
            assert (a.read_only_hint, a.destructive_hint, a.idempotent_hint, a.open_world_hint) == \
                (True, False, True, False), tool.name


@pytest.mark.parametrize('allow_unlock', [True, False])
@pytest.mark.parametrize('allow_include_gated', [True, False])
def test_discovery_of_held_terms_is_independent_of_translation_unlock(allow_unlock, allow_include_gated):
    tools = _tools(build_server(allow_unlock=allow_unlock, allow_include_gated=allow_include_gated))
    assert ('unlock' in tools['aussie_translate'].input_schema['properties']) == allow_unlock
    for name in ['aussie_lookup', 'aussie_entries', 'aussie_entry', 'aussie_random_entry']:
        assert ('include_gated' in tools[name].input_schema['properties']) == allow_include_gated
        assert ('include_gated' in tools[name].description) == allow_include_gated


def test_hosted_discovery_can_show_held_terms_without_translation_unlock(translator):
    server = build_server(translator=translator, allow_unlock=False)
    plain = asyncio.run(server.call_tool('aussie_lookup', {'query': 'all talk'})).structured_content
    shown = asyncio.run(server.call_tool('aussie_lookup', {'query': 'all talk', 'include_gated': True})).structured_content
    assert len(shown['results']) > len(plain['results'])
    assert any(row['held_back'] for row in shown['results'])
    assert 'unlock' not in _tools(server)['aussie_translate'].input_schema['properties']


def test_hidden_discovery_permission_sent_anyway_uses_its_closed_default(hosted, monkeypatch):
    seen = []
    real = harness.lookup
    monkeypatch.setattr(harness, 'lookup', lambda *a, **k: seen.append(k) or real(*a, **k))
    asyncio.run(hosted.call_tool('aussie_lookup', {'query': 'all talk', 'include_gated': True}))
    assert seen[-1]['include_gated'] is False


@pytest.mark.parametrize('query', ['national forest', 'a people', 'real estate agent'])
def test_mcp_lookup_reports_the_same_protected_contract_as_python(query, translator):
    import json

    server = build_server(translator=translator)
    actual = asyncio.run(server.call_tool('aussie_lookup', {'query': query})).structured_content
    expected = json.loads(json.dumps(harness.lookup(query, translator=translator)))
    assert actual == expected and actual['outcome'] == 'left_as_written'


@pytest.mark.parametrize("tool, field", [("aussie_translate", "text"), ("aussie_plan", "text"),
                                         ("aussie_lint", "text"), ("aussie_lint", "original"),
                                         ("aussie_verify", "text"), ("aussie_verify", "original")])
def test_every_text_field_is_refused_over_the_cap(hosted, tool, field):
    base = {"aussie_translate": {"text": "She was tired."}, "aussie_plan": {"text": "She was tired."},
            "aussie_lint": {"text": "She was knackered."},
            "aussie_verify": {"text": "She was knackered.", "original": "She was tired."}}[tool]
    cap = HOSTED["max_chars"]
    asyncio.run(hosted.call_tool(tool, base | {field: "a" * cap}))
    with pytest.raises(ToolError, match="at most 40 characters"):
        asyncio.run(hosted.call_tool(tool, base | {field: "a" * (cap + 1)}))


def test_lookup_query_has_its_own_cap(hosted):
    asyncio.run(hosted.call_tool("aussie_lookup", {"query": "very tired"}))
    with pytest.raises(ToolError, match="at most 12 characters"):
        asyncio.run(hosted.call_tool("aussie_lookup", {"query": "extremely tired"}))


def test_lookup_limit_is_capped_and_its_default_fits(hosted):
    schema = _tools(hosted)["aussie_lookup"].input_schema["properties"]["limit"]
    assert schema["maximum"] == 5 and schema["default"] == 5
    assert len(asyncio.run(hosted.call_tool("aussie_lookup", {"query": "very tired"})).structured_content["results"]) <= 5
    with pytest.raises(ToolError):
        asyncio.run(hosted.call_tool("aussie_lookup", {"query": "very tired", "limit": 6}))


def test_hidden_arguments_sent_anyway_never_reach_the_toolkit(hosted, monkeypatch):
    calls = []
    real = harness.translate
    monkeypatch.setattr(harness, "translate", lambda *a, **k: calls.append(k) or real(*a, **k))
    asyncio.run(hosted.call_tool("aussie_translate", {"text": "She was tired.", "unlock": ["all"],
                                                      "document_config": {"garnish": []}}))
    assert calls[-1]["unlock"] is None and calls[-1]["document_config"] is None


def test_every_tool_uses_the_injected_translator(monkeypatch):
    translator = Translator(default_translator().dictionary, lookup_embedder="bundled")
    server = build_server(translator=translator)
    seen = []
    for name, fn in TOOLS.items():
        monkeypatch.setattr(harness, fn.__name__, lambda *a, _fn=fn, **k: seen.append(k["translator"]) or {})
    args = {"aussie_entries": {}, "aussie_wordless_meanings": {}, "aussie_entry": {"entry_id": "stoked"}, "aussie_random_entry": {},
            "aussie_suggest_name": {}, "aussie_variations": {"family": "sideways-call-title",
            "parts": {"stem": "bugger-sideways", "ending": "call-me-the-pope"}}, "aussie_bulldust": {"concept": "HUNGRY"}, "aussie_lookup": {"query": "very tired"}, "aussie_lint": {"text": "G'day."}, "aussie_guide": {},
            "aussie_plan": {"text": "Hi."}, "aussie_translate": {"text": "Hi."},
            "aussie_verify": {"text": "G'day.", "original": "Hello."}}
    for name in TOOLS:
        asyncio.run(server.call_tool(name, args[name]))
    assert len(seen) == len(TOOLS) and all(t is translator for t in seen)


def test_two_servers_keep_their_own_caps_and_share_one_translator(monkeypatch):
    translator = Translator(default_translator().dictionary, lookup_embedder="bundled")
    narrow, wide = (build_server(translator=translator, max_chars=n) for n in (40, 80))
    seen = []
    real = harness.translate
    monkeypatch.setattr(harness, "translate", lambda *a, **k: seen.append(k["translator"]) or real(*a, **k))
    text = "She was very tired after the long meeting at work today."
    assert 40 < len(text) <= 80
    with pytest.raises(ToolError, match="at most 40 characters"):
        asyncio.run(narrow.call_tool("aussie_translate", {"text": text}))
    asyncio.run(wide.call_tool("aussie_translate", {"text": text}))
    asyncio.run(narrow.call_tool("aussie_translate", {"text": text[:40]}))
    assert seen == [translator, translator]


@pytest.mark.parametrize('lookup_limit', [None, 3, 50])
@pytest.mark.parametrize('max_results', [None, 7])
def test_bulldust_limit_is_advertised_and_rejected_before_toolkit(translator, monkeypatch, lookup_limit, max_results):
    from dataclasses import replace

    catalog = replace(translator.dictionary.construction_catalog, max_results=max_results) if max_results else None
    tr = Translator(replace(translator.dictionary, construction_catalog=catalog), lookup_embedder=None)
    server = build_server(translator=tr, lookup_limit=lookup_limit)
    maximum = min(max_results or 20, lookup_limit or 20)
    schema = _tools(server)['aussie_bulldust'].input_schema['properties']['limit']
    assert schema['minimum'] == 1 and schema['maximum'] == maximum
    assert schema['default'] == min(5, maximum)
    seen = []
    monkeypatch.setattr(harness, 'bulldust', lambda *a, **k: seen.append(k['limit']) or {})
    asyncio.run(server.call_tool('aussie_bulldust', {}))
    asyncio.run(server.call_tool('aussie_bulldust', {'limit': maximum}))
    assert seen == [schema['default'], maximum]
    for invalid in [0, maximum + 1]:
        with pytest.raises(ToolError):
            asyncio.run(server.call_tool('aussie_bulldust', {'limit': invalid}))
    assert seen == [schema['default'], maximum]
