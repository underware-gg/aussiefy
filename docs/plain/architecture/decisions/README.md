# Decision records

The architectural history of aussiefy: one record per decision, each preserving the context, the decision and
its consequences as they stood when it was made. Records are numbered in sequence (`dd-NNN-slug.md`, titled
`DD-NNN: Title`) and never renumbered.

## Conventions

- **Format:** Context, Decision and Consequences are required. A short header above them carries the status,
  the date and any pointers.
- **Immutability:** the body of a record is not rewritten once the decision lands. A change of direction is a
  new record that **supersedes** the old one (replaces it) or **extends** it (builds on it); only the header's
  status and pointers are updated.
- **Dates:** the repository was imported as a single commit, so records written for decisions made before the
  import are dated from the documents that evidence them (the changelog, research rounds and design reviews),
  and marked as recorded retrospectively.
- **Placement:** cross-cutting decisions live here. A decision that governs one subsystem may live beside it,
  but is still listed below.

## Index

| Record | Decision | Status |
|---|---|---|
| [DD-001](../../../architecture/decisions/dd-001-no-nlp-dependency-in-the-core.md) | No NLP dependency in the core: a small, deterministic frame checker, not spaCy | Accepted |
| [DD-002](../../../architecture/decisions/dd-002-slang-is-data.md) | Slang is data, never hard-coded: every phrase is a dictionary entry, every level a profile | Accepted |
| [DD-003](../../../architecture/decisions/dd-003-deterministic-context-keyed-rolls.md) | Every random decision is a SHA-256 roll keyed by the seed and its context | Accepted |
| [DD-004](../../../architecture/decisions/dd-004-vulgarity-calibrated-to-australian-ears.md) | Four vulgarity tiers calibrated to Australian ears; no level defaults to the strongest | Accepted; extended by DD-005 |
| [DD-005](../../../architecture/decisions/dd-005-orthogonal-level-and-vulgarity.md) | Level and vulgarity are orthogonal dials; swearing is its own channel | Accepted |
| [DD-006](../../../architecture/decisions/dd-006-layered-flat-package.md) | A layered, flat package, with the layering enforced by a test | Accepted |
| [DD-007](../../../architecture/decisions/dd-007-pluggable-local-embeddings.md) | Pluggable, local similarity, with a bundled static model read by the standard library | Accepted |
| [DD-008](../../../architecture/decisions/dd-008-one-toolkit-thin-surfaces.md) | One toolkit of five operations, with every surface a thin adapter held in step by tests | Accepted |
| [DD-009](../../../architecture/decisions/dd-009-llm-output-accepted-only-when-checked.md) | LLM output is accepted only when checked; otherwise the engine's draft stands | Accepted |
| [DD-010](../../../architecture/decisions/dd-010-hand-curated-concept-vocabulary.md) | The concept vocabulary is hand-curated; tools may only propose | Accepted |
| [DD-011](../../../architecture/decisions/dd-011-copyrighted-texts-stay-local.md) | Copyrighted texts stay local; only pointers and short excerpts are committed | Accepted |
| [DD-012](../../../architecture/decisions/dd-012-reference-dictionaries-are-reference-only.md) | Reference dictionaries are used by hand only, and glosses are our own words | Accepted |
| [DD-013](../../../architecture/decisions/dd-013-one-squashed-release-per-version.md) | One squashed, tagged release per version on `main`, made by `scripts/promote.py` | Accepted |
| [DD-014](../../../architecture/decisions/dd-014-reviewed-provenance-gate.md) | Reviewed provenance held to tracked files, model metadata and actual wheel contents | Accepted |
| [DD-015](../../../architecture/decisions/dd-015-source-preserving-markdown.md) | Preserve Markdown source spans above the plain engine with per-unit evidence | Accepted |
| [DD-016](../../../architecture/decisions/dd-016-reconcile-source-capabilities.md) | Reconcile source document modes, domain configuration and licensed research within the layers | Accepted |
| [DD-017](../../../architecture/decisions/dd-017-authoritative-plain-documentation.md) | Authoritative plain sources and deterministic published prose | Accepted |
| [DD-018](../../../architecture/decisions/dd-018-checked-pr-release-promotion.md) | Checked GitHub PR promotion, exact-head CI and resumable reconciliation | Accepted |
| [DD-019](../../../architecture/decisions/dd-019-explicit-composable-document-policy.md) | General by default, opt-in detection and exact composable document behaviour overrides | Accepted |
| [DD-020](../../../architecture/decisions/dd-020-document-composition-state.md) | Share document choices and garnish limits while preserving Markdown source units | Accepted |
| [DD-021](../../../architecture/decisions/dd-021-request-local-profile-overrides.md) | Inherit and override request-local engine profiles consistently across document operations | Accepted |
| [DD-022](../../../architecture/decisions/dd-022-sentence-safe-document-flavour.md) | Keep technical examples exact while placing conversational flavour at source sentence starts | Accepted |
| [DD-023](../../../architecture/decisions/dd-023-agent-neutral-retelling.md) | Share agent-neutral retelling contracts and keep client integrations at the edge | Accepted |
| [DD-024](../../../architecture/decisions/dd-024-contract-aware-judging.md) | Give agent/API judges the complete effective writing contract while preserving legacy protocols | Accepted |

## By topic

- **Engine:** DD-001, DD-003, DD-007
- **Dictionary and data:** DD-002, DD-010, DD-012
- **The dials:** DD-004, DD-005
- **Structure and interfaces:** DD-006, DD-008, DD-009, DD-015, DD-016, DD-019, DD-020, DD-021, DD-022, DD-023, DD-024
- **Sources, licensing and releases:** DD-011, DD-012, DD-013, DD-014
