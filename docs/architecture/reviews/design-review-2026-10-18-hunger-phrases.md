# Design review: hunger phrases, 18 October 2026

Surface: two appetite VPs, one bounded trigger, six rewrite-only images, meaningful-output regressions,
independent candidate records, source checks, contributor documentation and provenance. One reviewer
assesses all six software-design concerns against the [hunger harvest](../../../research/hunger-phrases-2026-10-18/README.md).

## Findings

Preliminary review found an aspect mismatch: mechanically replacing feel/feels/felt with hang/hangs/hung
out changed an appetite state into apparent habitual waiting or lingering. Hanging-out is now a writer-only
suggestion with progressive and tense guidance. The automatic VPs both retain the head verb “feel”, keeping
the source's inflection while changing its complement to an appetite phrase.

Focused tests exercise fragments, progressive/simple present, past, questions and modals, plus complement
exclusions and imagery controls. They explicitly distinguish generated original riffs from familiar/shared
expressions and verify that none of the six new images is automatically inserted. The stomach/throat
template binds actual possessives rather than defaulting to a first-person speaker.

Final independent review reports no remaining findings. The reviewer independently passed all 68 initial
hunger/imagery checks and directly checked simple present, progressive, past, perfect, modal and question
forms. The final writer-lookup regression passes with an explicit result limit; the research command also
specifies the level, embellishment and swear cap. All **69** hunger/imagery checks pass. Complete pre-commit
verification passed **2,346 tests, two expected local-corpus skips, 797.30 seconds**. Ruff, whitespace and
generated-publication checks pass. Canonical regeneration leaves translation goldens and changes fixtures
unchanged.

## What's done well

- Existing HUNGRY ownership, VP inflection, clause-boundary guards and imagery metadata handle the new
  expressions without a special engine path, configuration option or schema extension.
- Ordinary appetite is distinct from optional ravenous exaggeration; original inventions retain honest
  origins and familiar constructions do not acquire unsupported claims of exclusively Australian provenance.
- The raw three-agent candidate record and source decisions retain duplicates, exclusions and evidence
  limits, including composed phrases and indexed references whose full pages were unavailable.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Narrow existing predicate hunger substitutions before metaphorical complements | Preserve ambition in “feels hungry for success” | The new VP declines that complement, but the pre-existing shorter predicate rule can still offer “starvin' for success” |
| Extend person binding through progressive auxiliaries | Offer contextual images for “I am feeling hungry” as well as “She felt hungry” | The exact phrase now converts correctly, all templates are discoverable by lookup, and the pre-existing inference gap is explicitly documented without inventing a speaker |
