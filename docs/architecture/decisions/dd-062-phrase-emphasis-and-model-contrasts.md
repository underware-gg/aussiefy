# DD-062: Phrase emphasis ownership and model-only lexical contrasts

Status: Accepted. Date: 2026-11-19. Extends DD-029 and DD-061.

## Context

Site checks at 579b2c6 found sequential phonetic rules adding both an infix and an emphatic tail to the
same adjective. Aim raised the probability but the missing ownership affected cap too. Bundled lookup
also equated whisper with shouting and silence: its static vectors encode topic, not logical entailment.
The existing contraction-safe negation guard cannot distinguish affirmative antonyms.

## Decision

Allocate generated emphasis to the phrase/head span. Degree-modifier swaps and adjective stacks allocate first;
phonetic infixes/tails claim an unallocated span and carry ownership through all subsequent edits. Reuse
the rule in changes-card rendering, recalculating each alternative's local claims. Independent heads and
ordinary phonetics remain free. Do not fix a sentence by changing its dictionary wording or lowering aim.

Keep the model threshold and direct lexical routes. Load validated, first-party reviewed lexical poles
from dictionary data and veto model-only paths into another pole's concepts when one pole is asserted.
Grammatical negation and mixed/ambiguous poles cannot establish a positive pole. Keep this bounded
knowledge separate from training-only opposites, automatic source triggers and public request/response
schemas. The shared lookup kernel serves scalar lookup and quiz batches.

## Consequences

Affected seeds intentionally change in either mode. V4 schemas, entry IDs, spellings and evidence weights
remain unchanged. Review live/golden diffs and preserve historical evidence. Known speech-volume, size
and price contradictions have regressions; this is not an exhaustive antonym dictionary or semantic proof.
