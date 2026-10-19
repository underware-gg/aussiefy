# DD-036: Source-specific semantic effects and quantity precision

Status: Accepted; integrated verification passed.
Date: 19 October 2026.
Extends: [DD-031](dd-031-narrator-opinion.md), [DD-034](dd-034-reviewed-semantic-degree.md).

## Context

“Donkey's years ago” is an appropriate indefinite duration for “ages ago”, but using it for “four score and
seven years ago” loses an exact quantity. The user permits that trade in narrative Dinkum/Troppo while
requiring precision at Deadset and for factual documents. Globally labelling an entry as lossy would also
block exact indefinite-to-indefinite mappings. Document-type detection must feed settings, not hidden rules.

## Decision

Concepts declare `trigger_effects` by exact frame and raw trigger, including its intensity suffix. Entries
retain inherent `semantic_effects`. Source effects are concept-scoped and transfer to exact direct matches
of the same span. Alternative precise readings do not inherit another concept's precision loss. Similarity
cannot establish permission-free provenance for a reviewed effect family.

`quantity_approximation` is an exact boolean advanced override. Data-backed General/Story/Personal defaults
permit it at Dinkum/Troppo; Deadset, factual presets and Custom keep it false. The resolver combines dial
and preset defaults before applying explicit overrides. Selection consumes only resolved permissions.

The shared candidate path applies effects to translation, plans, contextual meaning lookup and alternatives.
Explicit term discovery remains available. Research tools retain source annotations through unrelated fixes,
merges and intentional style rewrites, using canonical effect parsing.

Lint/verify check a reviewed source occurrence paired with a compatible recognised target inside an
unambiguous local edit. Permission exempts numbers only within that source occurrence. Other quantities
retain fidelity checks. No-original or ambiguous edits cannot establish a source-specific approximation.

Applied effects belong to a rendering at a source spot. The strict changes payload advances to v2 for
optional `semantic_effects` on alternatives and locked options; entry-card metadata remains inherent.
ID, span and rendering semantics remain unchanged. Strict v1 consumers must adopt the v2 schema.

## Consequences

Precision is configurable without weakening explicit severity or factual identity. Ordinary indefinite
slang remains usable at Deadset. New numeric mappings require reviewed source evidence; a permission does
not create replacements for arbitrary quantities. The bounded checker does not claim semantic alignment
of arbitrary retellings. Historical wording anchors remain frozen and separate from precision checks.
