# Package layout

`aussiefy/` is one flat package whose modules fall into layers. Each layer may use the layers below it, never
the ones above. The layering is documented here and enforced by `tests/architecture/test_layers.py`, rather than by
subpackages (see [DD-006](../../architecture/decisions/dd-006-layered-flat-package.md)).

| Layer | Modules |
|---|---|
| Public API | `__init__.py` (translate, translate_changes, lookup, lint, guide, plan, yarn, Translator, load_dictionary, verify, and the result and error types) |
| Surfaces (thin adapters) | `cli.py`, `mcp_server.py`, `skills/aussiefy/SKILL.md` |
| Toolkit | `harness.py` (six agent operations), `lookup.py`, `lint.py`, `guide.py`, `verify.py` (fidelity and policy checks), `align.py` (shared sentence counterparts), `retelling.py` (agent-neutral briefs, JSON Schema tool contracts, sessions, dispatch and checked submission) |
| Document translation | `translation.py` (shared surface routing), `markdown.py` (strict source spans and document results), `markup.py` (extended Markdown/MDX scanning) |
| Optional API clients | `yarn.py` (built-in retelling loop and Anthropic tool adapter), `llm.py` (surface and sentence rewrites), `claude.py` (Anthropic SDK boundary) |
| Engine | `engine.py` (the pipeline), `text.py`, `matcher.py`, `detect.py`, `select.py`, `realise.py`, `morph.py`, `garnish.py`, `context.py`, `policy.py`, `genre.py` (pure form policy and classification), `dialect.py` (source-English swaps), `pos.py` (bundled tagger), `protected.py` (opaque source spans and restoration), `changes.py` (every change, its alternatives rendered in place, in the same pass) |
| Dictionary | `schema.py` (entries, concepts), `cards.py` (the entry cards lookup and the changes builder both show), `masks.py` (the maskable words in a rendering), `model.py` (the dictionary as data, and what derives from it), `loader.py` (reading and validating the YAML), `terms.py` (when two spellings are one term), `dump.py` |
| Similarity | `embed.py`, `static.py` (the bundled model), `models.py` (installed ones) |
| Maintainers | `gaps.py`, `explain.py`, `rounds.py` (research rounds), `judge.py` (blind packets, report validation and optional Claude boundary), `scrape/` (scrape, fragments, harvest, tag, review) |
| Shared | `errors.py` (`UserError`, the error a user can fix) |

`profile.py` belongs to the Engine layer: it validates immutable request-local tuning and applies it to the
selected level and swearing profiles without changing dictionary data. The data the engine reads is in
`aussiefy/data/` (see [the dictionary](../functional/dictionary.md)).

`vocabulary.py` belongs to the Dictionary layer. It composes raw entry/concept additions and explicit
versioned patches before the loader builds one validated dictionary and its indexes. It performs no I/O;
the loader owns files, source sidecars and diagnostics. No overlay matching occurs during translation.

## The layering rule

The core (the engine, the dictionary and the similarity modules other than `models.py`) imports nothing from
the toolkit, the LLM modes, the surfaces or the maintainer tools, so it stays usable and testable on its own.
`tests/architecture/test_layers.py` checks this with an import scan, and allows one exception: `embed.make_embedder("local")`
resolves the installed model's settings through `models.py`, the one place the core reaches out. A second test
keeps the dictionary model (`model.py`, `schema.py`, `cards.py`, `policy.py`, `matcher.py`, `text.py`, `genre.py`) free of the loader's
file I/O.

Optional heavy dependencies (anthropic, mcp, sentence-transformers, torch) are imported lazily, inside the
functions that need them, so the core imports and runs with its core dependencies, offline. Markdown's light parser
loads only in that mode; the plain engine never imports its adapter ([DD-015](../../architecture/decisions/dd-015-source-preserving-markdown.md)).

## Where to change things

- New slang, a new concept or a different level behaviour: the data in `aussiefy/data/`, not the code.
- A new way of detecting or realising a meaning: the engine stage that owns it ([pipeline](pipeline.md)).
- A new agent-facing operation or parameter: the toolkit function first, then each surface, which
  `tests/functional/test_interfaces.py` holds in step.
- Anything that talks to Claude: through `claude.py`, the single seam for the SDK.
- Shared agent workflow or submission rules: `retelling.py`; client-specific tool shapes and model calls
  belong at the edge. See [DD-023](../../architecture/decisions/dd-023-agent-neutral-retelling.md).

Genre configuration and the POS vocabulary are loaded once into the selected dictionary. The classifier and
model derive values without opening files. Syntax scanners supply opaque source spans to the engine; no
Markdown/JSX rules enter its core. See [DD-016](../../architecture/decisions/dd-016-reconcile-source-capabilities.md).

`imagery.py` belongs to the core: it selects reviewed contextual images using dictionary data and existing
subject/slot grammar. Engine insertion and toolkit suggestions share eligibility; bare lookup exposes
unbound templates. See [DD-025](../../architecture/decisions/dd-025-contextual-imagery.md).
