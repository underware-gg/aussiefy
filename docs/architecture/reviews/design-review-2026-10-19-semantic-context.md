# Design review: shared semantic context, 19 October 2026

Surface: meaning constraints, grammatical reading, argument preservation, contextual tone, planner
ordering, Markdown boundaries, YAML loader parity, regressions, goldens and documentation. One independent
reviewer assessed all six design concerns. The two additional source-research batches were reviewed
independently, including a separate reviewer for the 60-entry batch.

## Findings

Review resolved negative indefinite subjects gaining positive imagery; a possessive-object realisation
being incorrectly rejected; trailing adverbs and short degree ambiguities being read as objects; and
incomplete or opaque Markdown context bypassing meaning restrictions. Shared polarity, separate binding
and argument-preservation checks, bounded object shapes and explicit unknown following context address
these cases without another tagger or markup parser.

Golden readback caught unsafe proper-name VP binding and “tried his very best” being mistaken for an
object-taking attempt. Supported pronoun/auxiliary chains remain enabled; those ambiguous cases stay plain.
Reviewed golden changes restore objects or preserve unsupported constructions, with incidental seeded
infix changes. Changes fixtures remain unchanged. The CLI explanation now includes the final tone factor.
An additional integration probe reproduced per-unit mood drift in strict Markdown. Units now share the
document's eligible-prose mood; a regression prevents comic terms entering one paragraph of solemn prose.
The complete suite caught tuple/list conversion missing from concept-fix replay. The existing round
serialisation boundary now converts complement constraints alongside triggers; regressions cover new
concepts, preserved constraints, explicit replacement/removal and idempotent replay.

Research review corrected an overly narrow payment-only interpretation of “for sweet bugger-all”, retaining
attested non-monetary wasted-result use, and corrected both ABC source-date locators to 29 October 2009.
The 90 newly reviewed entries remain evidence and proposals, not applied dictionary changes. Cumulative
coverage is 220 of the original 1,254 entries, with no overlap between the three reviewed batches.

Final independent reviews report no remaining findings. The reviewer independently passed the 53
semantic-context tests and 21 preservation tests; the parent passed all 108 focused semantic, schema and
preservation checks. The complete pre-commit suite passed: **2,403 passed, two expected local-corpus skips
in 793.25 seconds**. Ruff, documentation publication, provenance/licensing and whitespace checks passed.

## What's done well

- Existing POS tags and shared reading support exact, direct-entry and similarity routes consistently.
- Canonical candidate weighting includes tone before variety limits; plans consume those same weights.
- Replacements retain arguments, while additive imagery only requires its own bindings to be established.
- The actual pure-Python loader is tested against the complete bundled dictionary.
- Concept replay converts metadata at its existing raw-schema boundary and preserves explicit overrides.
- Source evidence distinguishes terms, components, meanings and usage; missing references do not imply invention.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Temporal noun phrases such as “try every day” | Better argument-versus-adjunct interpretation | Requires semantic evidence beyond bounded object-shape checks |
| Broader tagger ambiguity analysis | Find further useful grammar signals | Current ambiguous degree phrases are conservatively preserved |
| Integrate source recommendations and continue the remaining 1,034 entries | Better lexical coverage and sense precision | The research separates evidence from runtime changes and product decisions |
