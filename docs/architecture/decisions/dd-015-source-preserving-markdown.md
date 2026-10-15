# DD-015: Preserve Markdown source spans above the plain engine

- **Status:** accepted
- **Date:** 2026-10-14

## Context

The plain engine does not know document syntax and can alter code, destinations, anchors and hard wraps.
Translated documentation needs deterministic offline prose, exact protected content and honest explain offsets.

## Decision

Put shared surface routing in `translation.py`, above the engine, with Markdown adaptation in `markdown.py`.
Public API/toolkit, CLI and MCP use that route. The core engine and `plan` retain plain-text contracts and
never import the adapter.

Use `markdown-it-py` version 4's demonstrated block line maps for nested containers/code and native link
destination/title helpers, plus raw-source span protection. Its Python requirement is >=3.10. Translate prose
gaps on physical lines and copy other spans verbatim; do not render normalised parser content back to source.
Preserve headings, code, links, tables, frontmatter, HTML and markers. Retain ambiguous regions conservatively.

Return a distinct `DocumentResult` with child engine results and source/output character ranges. Escape rendered
prose that could create syntax while keeping raw child results for explanation. Allow only offline/disabled
fallback; reject LLM/model modes before loading or calling. Add no toolkit embedding override.

## Consequences

Plain callers and goldens keep their behaviour. Original headings, executable examples, links and line endings
can be checked directly. Line/fragment boundaries reduce context and may change garnish; labels/table prose
and ambiguous emphasis remain in the original language. General MDX/JSX extraction is outside this dialect.

The parser is one light runtime dependency, imported only in Markdown mode. Real repository and licensed
technical documents test source spans and parsed block/inline structure; public JSON exposes the actual
per-unit evidence rather than claiming core offsets address the whole document.
