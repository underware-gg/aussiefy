# DD-049: Phrase fences are not meanings

Status: Accepted for ED16 phase A; seven legacy meaning markers remain until phase A2
Date: 2026-10-27
Extends: [DD-044](dd-044-phrase-interpretation-context.md), [DD-048](dd-048-community-extension-composition.md)
Extended by: [DD-050](dd-050-wordless-meaning-migration.md), [DD-051](dd-051-independent-phrase-ownership.md)

## Context

Guard concepts and dialect self-swaps both prevent replacing a component of a larger expression. A guard
is not a meaning waiting for a word. Mixing the two makes discovery and later lookup reasons ambiguous.
The ED16 brief requires reorganising these protections without changing translation or discovery fixtures.

## Decision

Keep fences in `aussiefy/data/fences.yaml`. Each item declares a phrase, frame, kind (`set_phrase`,
`other_sense` or `grammar`), scope and a plain reason. Scope explicitly distinguishes meaning detection
from dialect claims, lists the resolved Englishes (`unknown`, `us`, `uk`) for dialect claims, and carries
any document-domain `not_in` exclusions. Meaning-only fences must not block independent dialect swaps:
“parking lots” still becomes “car parks”. The outer `english=none` dial still disables the dialect pass.

Meaning fences compile into the existing pattern index and compete in the same frame checks and overlap
resolution as readings. They carry no concept IDs. Dialect fences enter the dialect table's existing
longest-match claims, but are never replacements. Both projections read the same canonical fence record.
Identical compiled patterns combine scopes in the data; the loader rejects duplicates and dialect
self-swaps, rejects a dialect fence repeated as a replacement, and warns about matching entry replacements.

Preserve observed scope rather than inferring it from dialect section names. The 43 old self-swaps filed
under `us` did not declare `known_only`; they applied to unknown and British English too. All migrated
dialect fences therefore apply to all three resolved Englishes. This corrects a factual premise of the
classification report, without narrowing the current protection.

`UNRESOLVED_SENSE` is the sole named abstention concept. Its identity prevents entries, imagery and
constructions and excludes it from the waiting list; it needs no generic concept-kind field or
`no_entries` marker. Phase A leaves the seven real meanings' temporary `no_entries` markers intact.
Trigger exclusions and their current matching semantics also remain intact until the measured trials.

## Consequences

Fences have one home and reasons ready for the later lookup contract; no new public lookup outcome is
introduced here. Translation goldens, changes fixtures, lookup snapshots and waiting/listing responses
must remain unchanged. Diagnostic detections no longer present obsolete guard IDs as semantic concepts.
The seven remaining meaning markers and their deliberate listing changes are a separate phase A2 change.
