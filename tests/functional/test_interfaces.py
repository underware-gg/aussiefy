"""One toolkit, one vocabulary: every surface (the Python API, the MCP tools, the CLI and yarn mode's tools)
exposes the harness functions' parameters by the same names and defaults, and forwards what it is given.
These tests are what keep the adapters thin and in step."""

import asyncio
import inspect

import pytest

import aussiefy
from aussiefy import harness

TOOLS = {"aussie_lookup": harness.lookup, "aussie_lint": harness.lint, "aussie_guide": harness.guide,
         "aussie_plan": harness.plan, "aussie_translate": harness.translate, "aussie_verify": harness.verify}

# a non-default value for every toolkit parameter, so a surface that drops or renames one is caught
VALUES = {"level": 4, "seed": 7, "vulgarity": 1, "variety": 2,
          "registers": ["current", "dated"], "regions": ["qld"], "unlock": ["archaic"], "limit": 3,
          "include_gated": True, "original": "She was tired.", "markup": "markdown", "english": "uk", "short": True,
          "document_type": "custom", "document_config": {"garnish": [], "keep_quotes": True,
              "profile": {"garnish": {"opener": 1}, "max_garnish": {"opener": 1}}},
          "embellishment": 2, "suggest": False, "markdown": False}
SUBJECT = {"lookup": ("query", "very tired"), "lint": ("text", "G'day mate."), "plan": ("text", "She was tired."),
           "translate": ("text", "She was tired."), "guide": (None, None),
           "verify": ("text", "She was knackered.")}
# CLI flags for each parameter (the CLI says --region for one region list, as people type it)
FLAGS = {"level": ["-l", "4"], "seed": ["-s", "7"], "vulgarity": ["--vulgarity", "1"],
         "variety": ["--variety", "2"], "registers": ["--registers", "current,dated"],
         "regions": ["--region", "qld"], "unlock": ["--unlock", "archaic"], "limit": ["--limit", "3"],
         "include_gated": ["--include-gated"], "markup": ["--markup", "markdown"],
         "english": ["--english", "uk"], "document_type": ["--document-type", "custom"],
         "document_config": ["--document-config", '{"garnish": [], "keep_quotes": true, "profile": {"garnish": {"opener": 1}, "max_garnish": {"opener": 1}}}'], "short": ["--short"], "embellishment": ["--embellishment", "2"], "suggest": ["--no-suggestions"]}


def _params(fn):
    return {n: p.default for n, p in inspect.signature(fn).parameters.items() if n != "translator"}


def _spy(monkeypatch, name):
    """Wrap harness.<name> (and the module it lives in) so calls still run and their kwargs are recorded."""
    import importlib

    real = getattr(harness, name)
    calls = []

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(harness, name, spy)
    for module in ("aussiefy.lookup", "aussiefy.lint", "aussiefy.guide", "aussiefy.verify"):
        if hasattr(importlib.import_module(module), name):
            monkeypatch.setattr(importlib.import_module(module), name, spy)
    return calls


@pytest.fixture(scope="module")
def server():
    pytest.importorskip("mcp")
    from aussiefy.mcp_server import build_server

    return build_server()


def test_mcp_tools_mirror_the_harness(server):
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    assert set(tools) == set(TOOLS)
    for name, fn in TOOLS.items():
        schema = tools[name].input_schema["properties"]
        assert set(schema) == set(_params(fn)), name
        for param, default in _params(fn).items():
            if default is not inspect.Parameter.empty:
                assert schema[param].get("default") == default, (name, param)


def test_mcp_tools_forward_every_argument(server, monkeypatch):
    for tool, fn in TOOLS.items():
        name = fn.__name__
        calls = _spy(monkeypatch, name)
        subject, value = SUBJECT[name]
        args = {p: VALUES[p] for p in _params(fn) if p in VALUES} | ({subject: value} if subject else {})
        asyncio.run(server.call_tool(tool, args))
        assert calls, tool
        got = {k: v for k, v in calls[-1].items() if k in VALUES}
        assert got == {k: v for k, v in args.items() if k in VALUES}, tool


def test_mcp_tools_return_the_harness_result(server):
    calls = {"aussie_lookup": {"query": "very tired"}, "aussie_guide": {"level": 3},
             "aussie_translate": {"text": "She was very tired.", "seed": 2}}
    for name, args in calls.items():
        result = asyncio.run(server.call_tool(name, args))
        structured = result[1] if isinstance(result, tuple) else result.structured_content
        assert structured == TOOLS[name](**args), name


def test_cli_exposes_every_toolkit_parameter():
    from aussiefy.cli import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction").choices
    for command, fn in {"lookup": harness.lookup, "lint": harness.lint, "guide": harness.guide,
                        "plan": harness.plan, "translate": harness.translate, "verify": harness.verify}.items():
        dests = {a.dest: a.default for a in sub[command]._actions}
        for param, default in _params(fn).items():
            if param in (SUBJECT[command][0], "original", "query", "text"):
                continue          # the subject is positional; lint's original is a file path
            assert param in dests, (command, param)
            assert dests[param] == default, (command, param)


@pytest.mark.parametrize("command", ["lookup", "lint", "guide", "plan", "verify"])
def test_cli_forwards_every_argument(command, monkeypatch, tmp_path, capsys):
    from aussiefy.cli import main

    fn = getattr(harness, command)
    calls = _spy(monkeypatch, command)
    argv = [command, "--json"] if command != "plan" else [command]
    for param in _params(fn):
        argv += FLAGS.get(param, [])
    if "original" in _params(fn):
        (tmp_path / "o.txt").write_text(VALUES["original"])
        argv += ["--original", str(tmp_path / "o.txt")]
    subject = SUBJECT[command][1]
    main(argv + ([*subject.split()] if subject else []))
    got = {k: v for k, v in calls[-1].items() if k in VALUES}
    assert got == {p: VALUES[p] for p in _params(fn) if p in VALUES}, command


def test_cli_translate_forwards_every_argument(monkeypatch):
    from aussiefy.cli import main
    calls = []
    from aussiefy.translation import run
    real = run

    def spy(text, **kwargs):
        calls.append(kwargs)
        return real(text, **kwargs)

    monkeypatch.setattr("aussiefy.translation.run", spy)
    argv = ["translate"] + [f for p in _params(harness.translate) for f in FLAGS.get(p, [])] + ["She was tired."]
    main(argv)
    got = {k: v for k, v in calls[-1].items() if k in VALUES}
    assert got == {p: VALUES[p] for p in _params(harness.translate) if p in VALUES}


def test_the_python_api_translate_is_the_toolkits():
    """aussiefy.translate returns the Result; harness.translate shapes it for agents. Same parameters, same text."""
    assert _params(aussiefy.translate) == _params(harness.translate)
    args = {k: VALUES[k] for k in _params(harness.translate) if k in VALUES}
    assert aussiefy.translate("She was very tired.", **args).text == harness.translate("She was very tired.",
                                                                                       **args)["text"]


def test_yarn_tools_mirror_the_harness():
    from aussiefy.yarn import TOOL_ARGS, tool_definitions

    tools = {t["name"]: t for t in tool_definitions()}
    assert set(tools) == {"lookup", "lint", "submit"}
    assert TOOL_ARGS == {n: tuple(t["input_schema"]["required"]) for n, t in tools.items()}
    # the model supplies the subject; the session supplies the policy
    assert set(tools["lookup"]["input_schema"]["properties"]) == {"query"}
    assert set(tools["lint"]["input_schema"]["properties"]) == {"text"}


def test_every_surface_defaults_to_level_5():
    from aussiefy.engine import Translator

    for fn in (*TOOLS.values(), aussiefy.translate, aussiefy.yarn):
        assert inspect.signature(fn).parameters["level"].default == 5, fn.__name__
    assert inspect.signature(Translator.translate).parameters["level"].default == 5


def test_toolkit_options_are_keyword_only():
    """Only the subject (query or text) is positional, so parameter order can't drift between modules."""
    from aussiefy.engine import Translator
    from aussiefy.yarn import brief

    for fn in (*TOOLS.values(), aussiefy.translate, aussiefy.yarn, brief, Translator.translate):
        params = [p for n, p in inspect.signature(fn).parameters.items() if n not in ("self", "text", "query")]
        assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params), fn.__qualname__


def test_python_api_exports_the_toolkit():
    for name in ("translate", "lookup", "lint", "guide", "plan", "verify", "yarn", "default_translator"):
        assert callable(getattr(aussiefy, name)), name
