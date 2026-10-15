"""Markdown changes prose while keeping source syntax and per-unit explanations honest."""

import asyncio
import copy
from dataclasses import replace
from pathlib import Path

from markdown_it import MarkdownIt
import pytest

import aussiefy
from aussiefy import engine, harness, Translator, UserError
from aussiefy.explain import format_explain
from aussiefy.translation import run

ROOT = Path(__file__).resolve().parents[2]


def block_shape(text):
    return [(t.type, t.tag, t.map, t.attrs, t.markup,
             t.content if t.type in ("fence", "code_block", "html_block") else "")
            for t in MarkdownIt("commonmark").enable("table").parse(text) if t.type != "inline"]


def links(text):
    return [(c.type, c.attrs, c.content if c.type == "image" else "")
            for t in MarkdownIt("commonmark").enable("table").parse(text) for c in (t.children or [])
            if c.type in ("link_open", "image")]


def inline_shape(text):
    return [(c.type, c.tag, c.attrs, c.markup, c.content if c.type in ("code_inline", "html_inline", "image") else "")
            for t in MarkdownIt("commonmark").enable("table").parse(text) for c in (t.children or [])
            if c.type != "text"]


def assert_offsets_and_protected(source, result):
    assert result.source == source
    previous_source = previous_output = 0
    parts = sorted([(*p.source_span, p.output_span) for p in result.protected] +
                   [(*u.source_span, u.output_span) for u in result.units])
    for start, end, (out_start, out_end) in parts:
        assert start == previous_source and out_start == previous_output
        previous_source, previous_output = end, out_end
    assert previous_source == len(source) and previous_output == len(result.text)
    for span in result.protected:
        assert source[slice(*span.source_span)].encode() == result.text[slice(*span.output_span)].encode()
    for unit in result.units:
        assert unit.result.source == source[slice(*unit.source_span)]
        assert unit.text == result.text[slice(*unit.output_span)]
        for record in unit.result.records:
            assert unit.result.source[slice(*record.span)] == record.text


PROTECTED = [
    "# Very busy {#busy}\n", "Very busy\n=========\n", "## [1.0.0] - 2026-10-14\n",
    "```text\nI am very busy.\n```\n", "````py\n``` nested\nI am very busy.\n````\n",
    "~~~text\nI am very busy.\n~~~\n", "    I am very busy.\n    This is code.\n",
    "> -\n>   `````py\n>   I am very busy.\n>   `````\n",
    "| Busy | Tired |\n|:---|---:|\n| very busy | very tired |\n",
    "[very busy](relative.md#busy \"Title\")", "![very tired](picture.png)",
    "[busy\\] label\nand tired](some/path_(one).md)\n", "[very busy][busy]\n\n[busy]: target.md\n    \"title\"\n",
    "``very busy ` very tired``", "`very busy\nvery tired`", "<https://example.com/very-busy>",
    "<div title=\"busy\">\n\nI am very busy.\n\n</div>\n", "<!-- very busy\n very tired -->\n",
    "---\ntitle: Very busy\n---\n", "+++\ntitle = 'Very busy'\n+++\n",
    "<Callout>\n\nI am very busy.\n\n</Callout>\n", "{{site.very_busy}}",
]


@pytest.mark.parametrize("protected", PROTECTED)
def test_protected_constructs_and_surrounding_prose(translator, protected):
    # Frontmatter must lead the source; headings/code/tables need their own blocks.
    source = protected + "\n\nI am extremely busy.\n"
    for level, seed in ((1, 0), (3, 7), (5, 19)):
        result = aussiefy.translate(source, markdown=True, translator=translator, level=level, seed=seed, vulgarity=0)
        assert protected in result.text
        assert block_shape(result.text) == block_shape(source)
        assert links(result.text) == links(source)
        assert inline_shape(result.text) == inline_shape(source)
        assert_offsets_and_protected(source, result)
    assert result.text != source


@pytest.mark.parametrize("source", ["", "# Heading only\n", "```\nvery busy\n", "---\nvery busy\n"])
def test_empty_and_unclosed_protected_documents_are_retained(translator, source):
    result = aussiefy.translate(source, markdown=True, translator=translator)
    assert result.text == source and not result.units
    assert_offsets_and_protected(source, result)


def test_nested_prose_markers_emphasis_hard_wraps_and_unicode_offsets(translator):
    source = "# Résumé\r\n\r\n> - **I am very busy.**  \r\n>   I am very tired.\\\r\n>   It is extremely\r\n>   busy here.\r\n"
    first = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0, seed=9)
    again = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0, seed=9)
    assert first.to_dict() == again.to_dict()
    assert first.text.count("\r\n") == source.count("\r\n")
    assert "**" in first.text and "  \r\n" in first.text and "\\\r\n" in first.text
    assert block_shape(first.text) == block_shape(source)
    assert_offsets_and_protected(source, first)
    assert "Source spans use document character offsets" in format_explain(first)
    assert "relative to each prose unit" in format_explain(first)


DOCUMENTS = ["docs/plain/root/README.md", "docs/plain/root/CONTRIBUTING.md", "docs/plain/root/CHANGELOG.md", "skills/aussiefy/SKILL.md",
             "docs/plain/user/getting-started.md", "docs/plain/functional/dictionary.md", "docs/plain/functional/toolkit.md",
             "docs/plain/architecture/pipeline.md", "docs/plain/contributor/data-acquisition.md",
             *[f"tests/corpus/everyday/workplace/{name}.md" for name in
               ("rust_book_hello_world", "black_readme", "mdn_http_cookies", "github_flow", "kubernetes_overview",
                "cloud_gov_pages_why", "rust_1_98_1_release_notes")]]


@pytest.mark.parametrize("path", DOCUMENTS)
def test_real_documents_keep_block_structure_links_and_source_spans(translator, path):
    source = (ROOT / path).read_text()
    result = aussiefy.translate(source, markdown=True, translator=translator, level=5, seed=7, vulgarity=0)
    assert result.text != source and result.units
    assert block_shape(result.text) == block_shape(source)
    assert links(result.text) == links(source)
    assert inline_shape(result.text) == inline_shape(source)
    assert_offsets_and_protected(source, result)


@pytest.mark.parametrize("fallback", ["ngram", "none", None, ""])
def test_offline_profile_defaults_work(translator, fallback):
    dictionary = copy.copy(translator.dictionary)
    dictionary.policy_defaults = {**dictionary.policy_defaults, "embedder": fallback}
    tr = Translator(dictionary)
    assert aussiefy.translate("I am very busy.", markdown=True, translator=tr).units


@pytest.mark.parametrize("fallback", ["bundled", "local", "configured", "st:some/model"])
def test_model_profiles_fail_before_loading_or_engine_work(translator, monkeypatch, fallback):
    dictionary = copy.copy(translator.dictionary)
    dictionary.policy_defaults = {**dictionary.policy_defaults, "embedder": fallback}
    tr = Translator(dictionary)
    real = tr.translate
    monkeypatch.setattr(tr, "translate", lambda *a, **k: pytest.fail("engine/model work before rejection"))
    with pytest.raises(UserError, match="requires ngram or none fallback"):
        aussiefy.translate("I am very busy.", markdown=True, translator=tr)
    with pytest.raises(UserError, match="requires ngram or none fallback"):
        harness.translate("I am very busy.", markdown=True, translator=tr)
    monkeypatch.setattr(tr, "translate", real)
    assert run("I am very busy.", translator=tr, markdown=True, embedder="none").units


@pytest.mark.parametrize("option", [{"rewrite": "all"}, {"rewrite": "hard"}, {"surface": True}])
def test_llm_options_fail_before_client_or_engine_work(translator, monkeypatch, option):
    monkeypatch.setattr(translator, "translate", lambda *a, **k: pytest.fail("engine/LLM work before rejection"))
    with pytest.raises(UserError, match="cannot use --rewrite or --surface"):
        run("I am very busy.", translator=translator, markdown=True, **option)


def test_generated_syntax_cannot_inject_markdown_structure(translator, monkeypatch):
    real = translator.translate
    injection = '# New heading\n[link](evil) <div> **bold** | table |\n1. item &copy; `code`'

    def translate(*args, **kwargs):
        return replace(real(*args, **kwargs), text=injection)

    monkeypatch.setattr(translator, "translate", translate)
    source = "I am very busy.\n"
    result = aussiefy.translate(source, markdown=True, translator=translator)
    assert result.units[0].result.text == injection
    assert result.text.count("\n") == 1 and block_shape(result.text) == block_shape(source)
    children = MarkdownIt("commonmark").parse(result.text)[1].children
    assert all(c.type == "text" for c in children)


def test_plain_engine_and_plan_contracts_are_unchanged(translator):
    source = "# I am very busy.\n"
    direct = translator.translate(source, seed=7)
    assert isinstance(aussiefy.translate(source, translator=translator, seed=7), engine.Result)
    assert aussiefy.translate(source, translator=translator, seed=7).to_dict() == direct.to_dict()
    assert engine.translate(source, translator=translator, seed=7).to_dict() == direct.to_dict()
    assert harness.plan(source, translator=translator, seed=7)["draft"] == direct.text


def test_all_surfaces_expose_the_document_result(translator, monkeypatch, capsys):
    from aussiefy.cli import main
    from aussiefy.mcp_server import build_server
    import json

    source = "# I am busy.\n\nI am very tired. `I am very busy.`\n"
    monkeypatch.setattr("aussiefy.cli._translator", lambda args: translator)
    expected = aussiefy.translate(source, translator=translator, markdown=True, seed=11).to_dict()
    assert harness.translate(source, translator=translator, markdown=True, seed=11) == expected
    assert main(["translate", "--markdown", "--json", "-s", "11", source]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    server = build_server()
    monkeypatch.setattr("aussiefy.harness.default_translator", lambda: translator)
    mcp = asyncio.run(server.call_tool("aussie_translate", {"text": source, "markdown": True, "seed": 11}))
    assert (mcp[1] if isinstance(mcp, tuple) else mcp.structured_content) == expected


@pytest.mark.parametrize("link", [
    '[label](path "I am very busy) and very tired")',
    "[label](path 'I am very busy) and very tired')",
    '[label](path (very busy \\) and tired))',
    '[label](<path_(one).md> "very busy (and tired)")',
    '[label](path\n  "very busy) and tired")',
])
def test_link_title_delimiters_and_attributes_are_preserved(translator, link):
    source = link + " I am very tired.\n"
    assert links(source)
    result = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0)
    assert link in result.text and links(source) == links(result.text)
    assert result.text != source


@pytest.mark.parametrize("html", [
    '<div>\n\n<!-- </div> -->\n\nI am very busy.\n\n</div>',
    '<div>\n\n<!-- <div> -->\n\nI am very busy.\n\n</div>',
    '<div>\n\n<span title="</div>"></span>\n\nI am very busy.\n\n</div>',
    '<div>\n\n<script>const x = "</div>";</script>\n\nI am very busy.\n\n</div>',
    '<div>\n\n<![CDATA[</div>]]>\n\nI am very busy.\n\n</div>',
    '<script>const text = "I am very busy.";</script>',
    '<style>.busy { color: red; }</style>',
    '<span>I am very busy.</span >',
    '- <div>\n\n  I am very busy.\n\n  </div>',
])
def test_real_html_boundaries_ignore_comments_attributes_and_raw_text(translator, html):
    source = html + "\n\nI am very tired.\n"
    result = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0)
    assert html in result.text
    assert result.text != source and result.units
    assert_offsets_and_protected(source, result)


def test_inline_script_payload_is_untouched(translator):
    html = '<script>const message = "I am very tired.";</script>'
    source = "I am very busy " + html + " today.\n"
    result = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0)
    assert html in result.text
    assert inline_shape(source) == inline_shape(result.text)
    assert result.text != source


@pytest.mark.parametrize("source", ["a*very busy*b\n", "**very busy**b\n", "a_very busy_b\n"])
def test_word_adjacent_emphasis_is_conservatively_retained(translator, source):
    result = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0)
    assert result.text == source
    assert inline_shape(source) == inline_shape(result.text)


def test_markdown_cli_retains_file_line_endings_and_no_added_terminal_newline(tmp_path, capsys):
    from aussiefy.cli import main

    source = b"# Busy\r\n\r\n```text\r\nI am very busy.\r\n```"
    path = tmp_path / "source.md"
    path.write_bytes(source)
    assert main(["translate", "--markdown", str(path)]) == 0
    assert capsys.readouterr().out.encode() == source


@pytest.mark.parametrize("protected", [
    '<!-- compare 2 > 1: I am very busy. -->',
    '<?compare 2 > 1: I am very busy. ?>',
    '<![CDATA[2 > I am very busy.]]>',
    '<span title="I am very busy > today"/>',
    '<https://example.com/a>',
    '<user@example.com>',
    '[a <!-- ] --> I am very busy.](path)',
    '[<span title="]">I am very busy.</span>](path)',
    '[a `]` b](path)',
    '![a `]` b](path)',
])
def test_inline_boundaries_retain_whole_construct_and_translate_both_sides(translator, protected):
    prefix, suffix = "I am very tired. ", " I am very busy.\n"
    source = prefix + protected + suffix
    result = aussiefy.translate(source, markdown=True, translator=translator, vulgarity=0)
    assert protected in result.text
    assert inline_shape(source) == inline_shape(result.text)
    assert links(source) == links(result.text)
    assert any(unit.source_span[1] <= len(prefix) for unit in result.units)
    assert any(unit.source_span[0] >= len(prefix + protected) for unit in result.units)
    assert result.text[:result.text.index(protected)] != prefix
    assert result.text[result.text.index(protected) + len(protected):] != suffix
    assert_offsets_and_protected(source, result)


@pytest.mark.parametrize("custom_default", [False, True])
def test_strict_document_context_reaches_short_units_and_public_warnings(translator, custom_default, capsys):
    from aussiefy.cli import main
    from aussiefy.genre import text_genre

    source = ("# Guide\n\nWarning: avoid dangerous lightning. Stay inside and keep away from windows. "
              "Check the color and gray labels.\n\nShe wants a cookie.\n")
    config = translator.dictionary.genres
    if custom_default:
        policies = {k: replace(v, default_embellishment=1) for k, v in config.policies.items()}
        translator = Translator(replace(translator.dictionary, genres=replace(config, policies=policies)))
    result = aussiefy.translate(source, markdown=True, translator=translator, level=1, vulgarity=2)
    whole = text_genre("\n".join(source[u.source_span[0]:u.source_span[1]] for u in result.units), source,
                       config=translator.dictionary.genres)
    assert whole.name == "instructions" and len(result.units) >= 2
    assert {u.result.genre.name for u in result.units} == {whole.name}
    assert {u.result.english for u in result.units} == {"us"}
    expected = whole.setting().step
    assert {u.result.embellishment.step for u in result.units} == {expected}
    assert expected == (1 if custom_default else 0)
    assert "biscuit" in result.text
    assert result.warnings == list(dict.fromkeys(w for u in result.units for w in u.result.warnings))
    assert result.warnings and result.to_dict()["genre"] == whole.name
    public = harness.translate(source, markdown=True, level=1, vulgarity=2, translator=translator)
    assert public["policy_warnings"] == result.warnings
    if not custom_default:
        assert main(["translate", source, "--markdown", "-l", "1", "--vulgarity", "2", "--json"]) == 0
        captured = capsys.readouterr()
        assert "policy_warnings" in captured.out and "no swear infixes" in captured.out
        assert main(["translate", source, "--markdown", "-l", "1", "--vulgarity", "2"]) == 0
        assert "no swear infixes" in capsys.readouterr().err
