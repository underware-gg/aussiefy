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
| [DD-025](../../../architecture/decisions/dd-025-contextual-imagery.md) | Contextual imagery with explicit writer and engine boundaries | Accepted |
| [DD-026](../../../architecture/decisions/dd-026-finite-clauses-and-sense-boundaries.md) | Preserve finite-clause grammar and ambiguous senses | Accepted |
| [DD-027](../../../architecture/decisions/dd-027-question-safe-infixes-and-source-capitals.md) | Use canonical question spans for opt-in infix guards and preserve unresolved source capitals | Accepted |
| [DD-028](../../../architecture/decisions/dd-028-hosted-mcp-capabilities.md) | A hosted MCP server narrows the toolkit by capability, with every tool annotated read-only | Accepted |
| [DD-029](../../../architecture/decisions/dd-029-changes-builder.md) | Render each alternative in place, in the same pass, behind a pass observer; Python API only | Accepted |
| [DD-030](../../../architecture/decisions/dd-030-shared-semantic-context.md) | Shared clause reading, concept restrictions, preserved arguments and contextual tone weights | Accepted |
| [DD-031](../../../architecture/decisions/dd-031-narrator-opinion.md) | Configure reviewed added narrator opinion without weakening meaning or role preservation | Accepted |
| [DD-032](../../../architecture/decisions/dd-032-dictionary-overlays.md) | Explicit ordered vocabulary corrections compiled into one shared dictionary | Accepted |
| [DD-033](../../../architecture/decisions/dd-033-explicit-solemn-comic-permission.md) | Explicit advanced permission for comic substitutions in solemn text, with an approved Troppo default | Accepted |
| [DD-034](../../../architecture/decisions/dd-034-reviewed-semantic-degree.md) | Reviewed degree and retained qualifiers, separate from style intensity | Accepted |
| [DD-035](../../../architecture/decisions/dd-035-noun-reference-and-address.md) | Shared grammatical noun usage distinguishes reference from direct address | Accepted |
| [DD-036](../../../architecture/decisions/dd-036-source-mapping-effects.md) | Source-specific semantic effects, resolved quantity precision and changes v2 | Accepted |
| [DD-037](../../../architecture/decisions/dd-037-contextual-matching-and-discovery.md) | Nonconsuming context assertions, shared object checks and discovery-only meanings | Accepted |
| [DD-038](../../../architecture/decisions/dd-038-publication-settings-and-variants.md) | Publication settings live only in `publication.yaml`; a host can export the docs at its own vulgarity | Accepted |
| [DD-039](../../../architecture/decisions/dd-039-certified-modifier-composition.md) | Certified modifier composition and replacement ownership | Accepted |
| [DD-040](../../../architecture/decisions/dd-040-term-evidence-and-usage.md) | Store term facts; derive attestation and usage eligibility | Accepted |
| [DD-041](../../../architecture/decisions/dd-041-subject-permissions.md) | Resolve reviewed subject permissions once, independently of profanity | Accepted |
| [DD-042](../../../architecture/decisions/dd-042-reviewed-tag-tiers.md) | Reviewed tag tiers, exact overrides and a data-derived subject registry | Accepted |
| [DD-043](../../../architecture/decisions/dd-043-typed-idiom-construction.md) | Bounded typed composition with honest part evidence and distinct construction identities | Accepted |
| [DD-044](../../../architecture/decisions/dd-044-phrase-interpretation-context.md) | Phrase readings compete by evidence; context establishes a sense without joining the replaced span | Accepted |
| [DD-045](../../../architecture/decisions/dd-045-explicit-dictionary-exploration.md) | Stable explicit discovery, clean handles and validated construction variations | Accepted |
| [DD-046](../../../architecture/decisions/dd-046-lookup-meaning-evidence.md) | Shared meaning evidence and exact authored wording take precedence over lookup guesses | Accepted |
| [DD-047](../../../architecture/decisions/dd-047-source-links-and-match-identity.md) | Shared citation-link validation and contextual source-match identity; slice 5 foundations | Accepted |
| [DD-048](../../../architecture/decisions/dd-048-community-extension-composition.md) | Additive community manifests, aggregate testimony, bounded adjustment data and content identity | Accepted |

| [DD-055](../../../architecture/decisions/dd-055-v3-producers-and-replay.md) | Coordinated v3 producers, local provenance and exact-source replay choices | Accepted for slices 3+6 |

| [DD-056](../../../architecture/decisions/dd-056-meaning-wording-and-negative-vps.md) | Separate meaning wording, exact discovery and grammatical negative verb phrases | Accepted for slice 7 foundation |

| [DD-057](../../../architecture/decisions/dd-057-permanent-public-entry-ids.md) | Permanent public entry keys, aliases, tombstones and release continuity | Accepted |

| [DD-058](../../../architecture/decisions/dd-058-owned-wording-and-selection.md) | Shared source ownership, selection mapping and directed near candidates | Implemented; v4 frozen |

| [DD-059](../../../architecture/decisions/dd-059-quiz-discovery-batch.md) | Prepared quiz exclusions share ordinary lookup scoring | Implemented |

| [DD-060](../../../architecture/decisions/dd-060-sentence-wording-scope.md) | English wording preserves actual sentence scope | Implemented |

## By topic

- **Engine:** DD-001, DD-003, DD-007, DD-029, DD-030, DD-034, DD-035, DD-036, DD-037, DD-039, DD-041, DD-044
- **Dictionary and data:** DD-002, DD-010, DD-012, DD-025, DD-032, DD-037, DD-040, DD-041, DD-042, DD-044, DD-045
- **The dials:** DD-004, DD-005, DD-041, DD-042
- **Structure and interfaces:** DD-006, DD-008, DD-009, DD-015, DD-016, DD-019, DD-020, DD-021, DD-022, DD-023, DD-024, DD-028, DD-029, DD-038, DD-045
- **Sources, licensing and releases:** DD-011, DD-012, DD-013, DD-014
| [DD-049](../../../architecture/decisions/dd-049-phrase-fences.md) | One scoped phrase-fence list, separate from meanings and named abstention | Accepted for ED16 phase A |
| [DD-050](../../../architecture/decisions/dd-050-wordless-meaning-migration.md) | Approved ordinary waiting meanings, contextual eager readings and complete marker retirement | Accepted for ED16 phase A2 |
| [DD-051](../../../architecture/decisions/dd-051-independent-phrase-ownership.md) | Whole-phrase constraints survive partial overlaps without freezing contextual objects | Accepted for ED16 phase C |
| [DD-052](../../../architecture/decisions/dd-052-source-evidence-and-output-grammar.md) | Shared source-role/context evidence, independent output grammar and measured refinement | Accepted for ED16 phase C |
| [DD-053](../../../architecture/decisions/dd-053-discovery-reading-contract.md) | Protected-query explanations, shared discovery cards, dictionary-local evidence and independent hosted discovery | Accepted for slice 6 |
| [DD-054](../../../architecture/decisions/dd-054-fence-explanation-coverage.md) | Per-phrase explanation coverage, approved W1 copy and exact fixed heads | Accepted |

| [DD-062](../../../architecture/decisions/dd-062-phrase-emphasis-and-model-contrasts.md) | Allocate generated emphasis by phrase; veto model-only inference across reviewed lexical poles | Accepted |
