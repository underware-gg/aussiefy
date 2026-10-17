# DD-027: Question-safe infixes and source capitals

Status: Accepted

Date: 2026-10-17

Extends: [DD-022](dd-022-sentence-safe-document-flavour.md)

## Context

The bloody-well infix can separate a fronted negative auxiliary from a noun-phrase subject, producing
“Doesn't bloody well my suit fit?”. A punctuation regex cannot reliably delimit questions containing
abbreviations. Separately, the dictionary's ordinary-word inventory contains trigger words such as
Australian and English; their adjective POS tags do not establish that their capitals are positional.

## Decision

Let phonetic data opt a rule out of questions through the boolean `unless_question`. Only the problematic
bloody-well rule opts in. Use canonical tokenisation and sentence spans after policy eligibility, preserving
occurrence ordinals for skipped matches and existing protected-span behaviour. Standalone statements and
imperatives remain eligible, as do other grammatical question infixes. Mixed quoted units containing a
declaration and questions conservatively skip this infix throughout. No document-specific branch is introduced.

Correct lower-case evidence at its owner, `Dictionary.plain_words`. Keep raw lower-case spellings and
compiled inflections from lower-case source patterns. A mixed/capitalised source pattern cannot manufacture
lower-case evidence merely through compilation's case folding. Existing ordinary-word, name and command
guards remain; “Work happens…” can still take an opener. Reuse the existing placement policy, which declines
a prefix when case is unresolved; do not add a nationality list or widen the POS guard.

## Consequences

Some uncertain source starts take less leading garnish, while other configured flavour remains. The
question opt-out is intentionally conservative and does not claim a general parser for negative questions.
Canonical sentence splitting handles the supported abbreviation cases consistently across the engine.
Technical/instruction/body probes and paired positive/negative regressions provide bounded evidence;
they do not establish general writing quality or a controlled judge-study result.
