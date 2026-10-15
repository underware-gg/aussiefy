# Markdown translation

Select Markdown explicitly with `aussiefy translate --markdown FILE`, `aussiefy.translate(text,
markdown=True)` or MCP `aussie_translate` with `markdown: true`. The default remains plain text; extensions
do not switch modes. The same level, vulgarity, seed and steering options apply.

```sh
aussiefy translate --markdown README.md -l swaggie --vulgarity nan -s 0
aussiefy translate --markdown README.md --json
aussiefy translate --markdown README.md --explain
```

Paragraph, list and blockquote prose is translated in source order. Each physical line and each gap between
protected inline constructs is an engine unit, so phrases do not cross hard wraps or links. Fragments can
have their own garnish; this mode preserves structure rather than rewriting whole paragraphs.

## Protected content and dialect

Headings and explicit IDs stay exact for stable anchors, including Setext and changelog version/date headings.
Code/output fences (including nested containers and variable-length delimiters), indented/inline code, tables
and YAML/TOML frontmatter stay exact. Whole links/images and reference definitions retain labels and destinations.
Autolinks, source escapes, entities, markers and complete raw HTML regions are retained too.

The dialect is CommonMark with tables and the repository's constructs. Ambiguous unclosed regions and
word-adjacent emphasis are conservatively retained. Template expressions and MDX declarations stay protected;
this is not an MDX/JSX prose extractor. The adapter uses `markdown-it-py` block line maps and raw-source inline
spans, never formatted parser output. The light parser supports Python 3.10 and loads only in Markdown mode.

Indentation, boundary/trailing whitespace, hard wraps and line endings survive. Whitespace inside a
rewritten prose phrase can change. Generated prose characters that could create markup are escaped;
newlines in custom slang are flattened within the unit. Original protected bytes are never escaped or reformatted.

Markdown permits only `ngram` or disabled fallback (`none`, including profiles with no fallback). The CLI's
existing `--embedder ngram`/`--embedder none` can override a profile; API/toolkit/MCP callers use the translator's
profile defaults. No embedding parameter is added to the toolkit. LLM modes (`--rewrite`, `--surface`) and
model fallbacks raise `UserError` (CLI exit 2) before a model loads or Claude is called.

## Results and explanations

Python returns `DocumentResult` for Markdown and the existing `Result` for plain text. Toolkit/MCP dicts and
CLI `--json` include the document structure:

| Field | Meaning |
|---|---|
| `format` | `markdown` |
| `text`, `source` | Rendered output and exact original source |
| Dials, warnings, seed, variety | The policy applied to each unit |
| `units` | Each unit's `source_span`, `output_span`, rendered `text` and original engine `result` |
| `protected` | Corresponding source/output ranges copied exactly |

Ranges are half-open Python string character offsets, not UTF-8 byte positions. Child engine records remain
relative to that child's source. Rendered unit text may differ from raw engine text because of escaping.
`--explain` names document source/output ranges before reporting the local engine decisions; there are no
fake document-wide engine records. Markdown text output adds no terminal newline to the document.

`Translator.translate`, `aussiefy.engine.translate` and `plan` remain plain text. Plan does not describe the
adapter's per-unit output; yarn lookup/lint tools stay unchanged.

The contracts are checked in [test_markdown.py](../../../tests/functional/test_markdown.py) and
[test_interfaces.py](../../../tests/functional/test_interfaces.py). See
[DD-015](../../architecture/decisions/dd-015-source-preserving-markdown.md) for the boundary decision.
