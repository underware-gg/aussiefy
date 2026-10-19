"""The package's layering (docs/architecture/package-layout.md), enforced: the engine and the dictionary import nothing
from the toolkit, the LLM modes, the surfaces or the maintainer tools, so they stay usable and testable on their own."""

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "aussiefy"
MODULES = {p.stem for p in PKG.glob("*.py")} | {p.parent.name for p in PKG.glob("*/__init__.py")}
CORE = {"text", "matcher", "detect", "select", "realise", "morph", "garnish", "context", "policy", "schema",
        "imagery", "model", "terms", "embed", "engine", "loader", "vocabulary", "static", "dump", "dialect", "genre", "pos", "protected", "profile", "cards", "masks", "changes"}
UPPER = {"__init__", "harness", "lookup", "lint", "guide", "retelling", "yarn", "llm", "claude", "cli", "mcp_server", "gaps",
         "rounds", "explain", "scrape", "models", "markdown", "translation", "align", "verify", "judge", "markup"}
NEUTRAL = {"errors"}   # shared by every layer, and imports nothing of the package
# embed.make_embedder("local") resolves the installed model's config: the one place the core reaches out
ALLOWED = {("embed", "models")}


def _imported(source: str) -> set[str]:
    """The package modules a module's source imports, relative or absolute (a name that isn't a module, as in
    `from aussiefy import translate`, is the package's own __init__)."""
    out = set()

    def module(dotted: str, names=()) -> None:
        if dotted:
            out.add(dotted.split(".")[0])
        else:
            out.update(n if n in MODULES else "__init__" for n in names)

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.level >= 1:
            module(node.module or "", [a.name for a in node.names])
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "aussiefy":
            module(node.module.partition(".")[2], [a.name for a in node.names])
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == "aussiefy":
                    module(a.name.partition(".")[2] or "__init__")
    return out


def _imports(module: str) -> set[str]:
    return _imported((PKG / f"{module}.py").read_text(encoding="utf-8"))


def test_every_module_has_a_layer():
    assert not CORE & UPPER and not (CORE | UPPER) & NEUTRAL
    assert MODULES == CORE | UPPER | NEUTRAL, "classify each new module, and drop removed ones"


def test_imports_are_found_in_every_form():
    source = ("from . import lint, static\nfrom .scrape.tag import tag_all\nimport aussiefy.yarn\n"
              "from aussiefy import translate\nfrom aussiefy.cli import main\nimport json\n")
    assert _imported(source) == {"lint", "static", "scrape", "yarn", "__init__", "cli"}


def test_the_core_imports_nothing_above_it():
    for module in sorted(CORE):
        upward = {m for m in _imports(module) & UPPER if (module, m) not in ALLOWED}
        assert not upward, (module, upward)


def test_shared_agent_workflow_does_not_depend_on_api_clients():
    for module in ("harness", "retelling"):
        assert not _imports(module) & {"yarn", "llm", "claude"}, module


def test_the_shared_modules_import_nothing_of_the_package():
    for module in sorted(NEUTRAL):
        assert not _imports(module), module


def test_the_dictionary_model_does_no_io():
    for module in ("model", "schema", "policy", "matcher", "text", "genre", "profile", "cards", "masks", "vocabulary"):
        assert "loader" not in _imports(module), module
