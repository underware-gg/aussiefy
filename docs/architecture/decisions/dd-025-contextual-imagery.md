# DD-025: Contextual imagery with explicit writer and engine boundaries

Status: Accepted

Date: 2026-10-17

Extends: [DD-019](dd-019-explicit-composable-document-policy.md), [DD-021](dd-021-request-local-profile-overrides.md)

## Context

Entry riffs require a particular vocabulary choice. Harvests contain useful comparisons with narrower
conditions than existing concepts, and suggestions that need sentence restructuring. Treating all these
as synonyms loses meaning; appending every image breaks grammar or adds unsupported events.

## Decision

Keep reusable idioms in entries and context-attached images in optional `imagery.yaml`. Validate concept,
frame, person, slot, level, vulgarity and exaggeration requirements. A pure core module serves planning,
translation and lookup. Reuse subject/slot grammar and seeded riff selection, rather than inventing entries
for images. Precise new concepts express futile work and physical breathlessness where broader ones fail.

Only direct suffixes may insert automatically. Rewrite and explicitly related associations remain writer
suggestions with required usage conditions. Free-text conditions never authorize automatic eligibility.
Negation suppresses contextual meaning matches conservatively. Bare lookup offers unbound templates.
Insertion consumes the same riff budget, sentence/spacing rules and document state as entry riffs; record
it as garnish with an image ID, without fabricating a substitution. Keep existing entry riffs compatible.

Embellishment supplies configurable defaults for imagery enablement, exaggeration and related association.
All document types accept exact overrides; Custom requires explicit optional behaviours. Troppo expands
reviewed options while preserving grammar and facts. Existing profile probabilities/counts still control
insertion independently of offered suggestions. Writer guidance and all tool surfaces share the contract.

## Consequences

Some vivid candidates remain free-writing craft, not automatic transformations. Writers must establish
conditions on rewrite/related cards; the engine cannot infer arbitrary scenes from a broad adjective.
No model or remote request is required. The library is small enough for a simple scan. Historical round
replay filters only deliberately set-aside references in scratch; real data and original harvest evidence
remain unchanged. New curation decisions supplement the frozen earlier decisions rather than rewriting them.
