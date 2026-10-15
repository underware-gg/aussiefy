"""Markdown and MDX: only the prose is translated; code, tags, links, front matter and headings come back exactly."""

import re
from pathlib import Path

import pytest

from aussiefy import harness


def document_translate(translator, text, **kwargs):
    markup = kwargs.pop("markup", "text")
    return translator.translate(text, _protected=mask(text, markup), **kwargs)

from aussiefy.markup import MarkupError, detect_markup, markup_changed, mask

CORPUS = Path(__file__).resolve().parents[1] / "corpus"
DOCS = sorted(p for p in (CORPUS / "everyday").rglob("*") if p.suffix in (".md", ".mdx")) + sorted(
    (CORPUS / "local").rglob("*.md*"))

MDX = """---
title: Getting started
description: How to get going quickly.
---
import { Callout } from 'nextra/components'

# Getting started

You are very tired after a long day, but the setup is really easy. Run `cargo build --release` in the
`hello_world` directory, then open [the settings page](/reference/config#very-tired) to change the color.

<Callout type="warning">
  Do not delete `config.yaml`. It is very important and the program will fail without it.
</Callout>

```rust
fn main() {
    println!("Hello, world! I am very tired.");
}
```

| Flag | Meaning |
|------|---------|
| `-v` | Very verbose output for a tired developer |

- Install the program quickly.
- Make sure your friend reads main.rs before Monday.

See https://example.com/very/tired for more, or email help@example.com.
"""
PROTECTED = ["---\ntitle: Getting started\ndescription: How to get going quickly.\n---",
             "import { Callout } from 'nextra/components'", "# Getting started", "`cargo build --release`",
             "`hello_world`", "](/reference/config#very-tired)", '<Callout type="warning">', "`config.yaml`",
             "</Callout>", 'println!("Hello, world! I am very tired.");', "|------|---------|", "main.rs",
             "https://example.com/very/tired", "help@example.com"]


@pytest.mark.parametrize("seed", range(4))
def test_mdx_keeps_everything_but_the_prose(translator, seed):
    out = document_translate(translator, MDX, level=5, seed=seed, vulgarity="tradie", markup="mdx").text
    for piece in PROTECTED:
        assert piece in out, piece
    assert "colour" in out and "You are very tired" not in out          # the prose is still translated


def test_tables_and_list_items_take_swaps_but_no_garnish(translator):
    for seed in range(8):
        out = document_translate(translator, MDX, level=5, seed=seed, markup="mdx").text
        rows = [line for line in out.splitlines() if line.startswith(("| `-v`", "- "))]
        assert all(not re.search(r"\| (?:Struth|Well|Now|So anyway|Anyway|Mate),", r) for r in rows), rows
        assert all(not re.match(r"- (?:Struth|Well|Now|So anyway|Anyway|Mate),", r) for r in rows), rows


def test_the_closer_follows_the_last_sentence_not_a_code_block(translator):
    text = "This is very easy and you will be fine.\n\n```sh\nmake install\n```\n"
    for seed in range(12):
        out = document_translate(translator, text, level=5, seed=seed, markup="markdown").text
        assert out.endswith("```sh\nmake install\n```\n"), out


def test_plain_text_is_untouched_by_the_default(translator):
    text = "Run `cargo build` now. It is very easy."
    assert document_translate(translator, text, level=5, seed=3).text == document_translate(translator, text, level=5, seed=3,
                                                                                    markup="text").text


def test_mask_restores_exactly_and_refuses_a_lost_span():
    m = mask(MDX, "mdx")
    assert len(m.text) == len(MDX) and m.restore(m.text) == MDX
    run = re.search(r"[\U00100000-\U0010FFFD]+", m.text).group()
    with pytest.raises(MarkupError):
        m.restore(m.text.replace(run, "", 1))
    with pytest.raises(MarkupError):
        m.restore(m.text.replace(run, run[:-1], 1))


@pytest.mark.parametrize("text, kept", [
    ("Use the `--force` flag with care.", "`--force`"),
    ("Read src/main.rs and the user_id field.", ["src/main.rs", "user_id"]),
    ("Call useEffect() in your component.", "useEffect()"),
    ("Press <kbd>Ctrl</kbd> twice.", "<kbd>Ctrl</kbd>"),
    ("An ![old diagram](img/a.png) is here.", "![old diagram](img/a.png)"),
    ("Escaped \\*stars\\* stay.", ["\\*", "\\*"]),
    ("A note[^1] and &nbsp; an entity.", ["[^1]", "&nbsp;"]),
])
def test_inline_spans_are_protected(text, kept):
    m = mask(text, "markdown")
    spans = [text[a:b] for a, b, _ in m.spans]
    for piece in [kept] if isinstance(kept, str) else kept:
        assert piece in spans, (piece, spans)


def test_prose_stays_translatable():
    m = mask("He said e.g. and/or the U.S. was fine. It costs $5 and $10 today.", "markdown")
    assert not m.spans


def test_indented_code_in_markdown_but_not_inside_mdx_components():
    md = "Some text.\n\n    let x = very_tired;\n\nMore text.\n"
    assert any("let x" in md[a:b] for a, b, _ in mask(md, "markdown").spans)
    mdx = "<Callout>\n\n    It is very important.\n\n</Callout>\n"
    assert not any("important" in mdx[a:b] for a, b, _ in mask(mdx, "mdx").spans)


def test_detect_markup():
    assert detect_markup(MDX) == "mdx"
    assert detect_markup("# Title\n\nSee [docs](https://x.y) and `code`.\n") == "markdown"
    assert detect_markup("Once upon a time, she was tired. # not a heading") == "text"


def test_lint_reads_prose_only_and_checks_the_markup_came_through(translator):
    original = "Set `color: red` in the file. The color is wrong."
    clean = harness.lint("Set `color: red` in the file. The colour's crook.", original=original,
                         markup="markdown", translator=translator)
    assert not any(i["kind"] == "spelling" and "color" in i["phrase"] for i in clean["issues"]), clean["issues"]
    broken = harness.lint("Set `colour: red` in the file. The colour's crook.", original=original,
                          markup="markdown", translator=translator)
    assert any(i["kind"] == "markup_changed" for i in broken["issues"])
    assert markup_changed("x `a`", "y `a`", "markdown") == []


def test_yarn_sends_back_a_submission_that_changed_the_code(translator):
    from aussiefy.yarn import brief, validate

    text = "Run `make build` when you are very tired. Then go to bed."
    s = brief(text, markup="markdown", translator=translator)
    assert "MARKUP" in s.payload
    assert any(p.startswith("markup_changed") for p in validate(s, s.plan["draft"].replace("make build", "make it")))
    assert not [p for p in validate(s, s.plan["draft"]) if p.startswith("markup_changed")]


def test_a_rewrite_that_drops_markup_is_refused(translator):
    class Dropper:
        model = "fake"

        def rewrite(self, original, draft, planned, *, level, vulgarity, seed):
            return re.sub(r"[\U00100000-\U0010FFFD]+", "", draft), "ok"

    text = ("The proposition was conceived with considerable deliberation and dedicated to posterity by `init`.")
    r = document_translate(translator, text, level=5, markup="markdown", rewriter=Dropper(), rewrite_mode="all")
    assert "`init`" in r.text and r.rewrites and r.rewrites[0].outcome == "fell_back"


@pytest.mark.skipif(not DOCS, reason="no markdown documents in the corpus")
@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_corpus_documents_keep_their_markup(translator, path):
    """Every Markdown/MDX document in the corpus (and any local ones), at each level: nothing protected changes."""
    text = path.read_text(encoding="utf-8")
    assert mask(text, "auto").restore(mask(text, "auto").text) == text
    for level, seed in ((2, 1), (5, 2)):
        out = harness.translate(text, level=level, seed=seed, vulgarity="tradie", markup="auto",
                                translator=translator)["text"]
        assert markup_changed(out, text, "auto") == []


@pytest.mark.parametrize("glyph", ["\U000f0000", "\U00100000", "\U00100001"])
def test_source_private_use_glyphs_do_not_collide_with_protection(glyph, translator):
    source = f"`code {glyph}` existing {glyph} glyph. She was tired."
    masked = mask(source, "markdown")
    assert masked.restore(masked.text) == source
    assert all(ch not in source for ch in masked.placeholders)
    restored = harness.translate(source, level=1, markup="markdown", translator=translator)["text"]
    assert restored.count(glyph) == 2 and f"`code {glyph}`" in restored
