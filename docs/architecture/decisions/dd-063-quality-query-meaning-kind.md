# DD-063: Match inferred quality queries to quality-capable meanings

Status: Accepted. Date: 2026-11-19. Extends DD-037, DD-053 and DD-062.

## Context

The site's Ask a local checks at 083b9cf found tiny/small retrieving child nouns by model similarity and
loud retrieving people/driving entries by describing words in glosses. These are not antonyms: they
confuse an attribute with the entity/action it describes. Increasing cosine thresholds does not express
the missing distinction. The bundled tagger also reads isolated loud as a noun.

## Decision

Recognise bare/adverb-qualified quality fragments from existing adjective vocabulary and POS evidence.
Add loud to grammar.yaml's existing adjective roots, which establish class without supplying a meaning
or translation trigger. Do not invent a query denylist or new meanings.

Before weak inference can admit a meaning path, require quality-capable source frames (`adj` or
`predicate_adj`) in the concept's triggers/plain forms. Filter paths before descriptive/gloss/fuzzy and
model scoring; an incompatible path's gloss cannot rescue another sense. Use meaning frames rather than
surface entry frames, so noun/clause-shaped quality idioms remain discoverable. Keep explicit term,
exact alias and authored source evidence ahead of this weak-evidence guard. Keep entity-with-modifier
queries and uncertain word classes in the existing fallback. Scalar and batched lookup share the rule.

## Consequences

Tiny/small abstain; loud may still find the quality word lairy for loud/showy clothing. Huge still finds
whopping. Source sense, antonym, negation and dial checks remain independent. No model threshold/weights,
entry IDs/spellings or public v4 fields change. The grammar root updates dictionary identity; regenerate
live receipts/fixtures while preserving historical evidence. This is bounded grammatical validation,
not a proof that all surviving same-kind model matches are synonyms.
