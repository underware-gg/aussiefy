# Package layout

`aussiefy/` is one flat package whose modules fall into layers. Each layer may use the layers below it, never
the ones above. The layering is documented here and enforced by `tests/architecture/test_layers.py`, rather than by
subpackages (see [DD-006](../../architecture/decisions/dd-006-layered-flat-package.md)).

| Layer | Modules |
|---|---|
| Public API | `__init__.py` (translate, translate_changes, lookup, lint, guide, plan, bulldust, yarn, Translator, load_dictionary, verify, and the result and error types) |
| Surfaces (thin adapters) | `cli.py`, `mcp_server.py`, `skills/aussiefy/SKILL.md` |
| Toolkit | `harness.py` (seven agent operations), `bulldust.py` (constructor operation boundary), `lookup.py`, `lint.py`, `guide.py`, `verify.py` (fidelity and policy checks), `align.py` (shared sentence counterparts), `retelling.py` (agent-neutral briefs, JSON Schema tool contracts, sessions, dispatch and checked submission) |
| Document translation | `translation.py` (shared surface routing), `markdown.py` (strict source spans and document results), `markup.py` (extended Markdown/MDX scanning) |
| Optional API clients | `yarn.py` (built-in retelling loop and Anthropic tool adapter), `llm.py` (surface and sentence rewrites), `claude.py` (Anthropic SDK boundary) |
| Engine | `engine.py` (the pipeline), `text.py`, `matcher.py`, `detect.py`, `degree.py` (reviewed degree composition), `semantic_checks.py` (pure bounded source-aware meaning, composition and known-theme checks), `select.py`, `grammar.py` (declared output requirements), `realise.py`, `morph.py`, `garnish.py`, `constructions.py` (pure typed composition), `context.py`, `meaning_context.py` (typed source meaning conditions), `policy.py`, `genre.py` (pure form policy and classification), `dialect.py` (source-English swaps), `pos.py` (bundled tagger), `protected.py` (opaque source spans and restoration), `changes.py` (every change, its alternatives rendered in place, in the same pass) |
| Dictionary | `schema.py` (entries, concepts), `fences.py` (scoped phrase protections and validation), `evidence.py` (stored evidence, pure attestation scoring and shared usage gates), `themes.py` (reviewed tag tiers and immutable subject policy), `cards.py` (the entry cards lookup and the changes builder both show), `masks.py` (the maskable words in a rendering), `model.py` (the dictionary as data, and what derives from it), `loader.py` (reading and validating the YAML), `construction_data.py` (construction catalogue validation), `terms.py` (when two spellings are one term), `dump.py` |
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

`extensions.py` composes additive community evidence and validates same-sense collisions, while
`identifiers.py` owns the shared id grammar. `adjustments.py` validates contextual weight data and performs
pure bounded queries; it imports no selection or evidence-scoring code. `tuning.py` belongs to the Engine
layer: it validates per-call preference inputs, resolves exact keys before latest same-root fallbacks, and
combines personal weights with community factors on already eligible candidates. It performs no I/O and
changes no evidence or eligibility. `dictionary_identity.py` is loader
I/O and fingerprints file inputs. The model stores its result and never imports that I/O module.

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

`fence_readings.py` builds counterfactual explanation evidence in the core, using the shared engine's
source readings and eligible candidates. It performs no I/O and never changes the dictionary or removes
a protection. The maintainer command `scripts/audit_fences.py` serialises its results and missing-effect
diagnostics. Lookup builds and reuses individual protections through a dictionary-local bounded index;
the batch audit uses the same evidence. Ordinary translation does not invoke this build.
`discovery_outcomes.py` owns the shared discovery codes and imports no package modules. Rich discovery
cards are shared by lookup and entry details; changes-v2 retains its existing card until the coordinated bump.

Lookup explicitly requests query-fragment readings from `detect.py`; ordinary replacement detection keeps
its stricter default. Lookup owns the bounded whole-query scope decision and uses local canonical readings
as evidence, rather than treating every matched noun or modifier as a complete parse.

`names.py` owns the reviewed name catalogue and deterministic, clean handle assembly in the core.
`explore.py` is the toolkit boundary for stable pages, full cards, random entries and name suggestions.
Construction variations reuse the constructor boundary in `bulldust.py`, validating each complete expression
with the other parts held fixed. They do not create a second policy or splice implementation.
