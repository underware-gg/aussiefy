# Semantic engine refinement

User direction: improve the existing engine's shared grammatical and semantic interpretation, including
tone, without coupling this work to the separate community-dictionary design. No communication with the
external agent is authorised. Research agents continue the source audit separately.

## Current slice

- Keep clause reading in the existing context module: bounded auxiliary-chain subjects, object shape,
  polarity and complement boundaries. Detection reuses its existing POS tags.
- Express meaning-specific complement restrictions on concepts in data. Apply them to exact triggers,
  direct entry triggers and similarity fallback before resolving overlaps; imagery uses the same boundary.
- Require each selected form to preserve captured arguments. Optional imagery only needs its placeholders
  bound because a suffix adds colour rather than replacing the original arguments.
- Reuse the existing tone/mood weighting in candidate selection before variety limits, and rank planner
  entry suggestions by the same contextual candidate weights. Preserve existing hard policy exclusions.
- Bind optional imagery through supported auxiliary chains without replacing those auxiliaries or inferring
  a speaker for fragments. Rewrite-only images remain writer-assisted, with explicit usage conditions.

## Verification and completion

Pin positive and negative examples across meanings and constructions, including non-hunger concepts,
gerund and nominal objects, literal argument retention, similarity fallback, punctuation, questions,
negation, competing subjects, tone ranking and protected text. Run the affected suites, regenerate and
read goldens and changes fixtures, regenerate public documentation, obtain an independent design review,
resolve findings, then run Ruff and the complete suite before committing and pushing dev.

The parallel source research remains evidence only until its individual recommendations are reviewed;
it does not migrate metadata, theme policy or attestation scoring.

## Remaining slices

The current semantic/YAML slice passed independent design review and complete pre-commit verification:
2,403 tests passed, with two expected local-corpus skips (793.25 seconds). Ruff, generated-documentation,
provenance/licensing and whitespace checks passed. The two new research batches remain evidence and
unapplied recommendations.

- Integrate the reviewed lexical corrections and source additions in the two new audit batches. Keep
  occupations, references, relationships and stated meanings intact; retain the vocabulary when a broad
  automatic trigger is narrowed. Source additions can affect weights and need fixture readback.
- Refine argument-versus-adjunct interpretation beyond nominal shape, including temporal phrases such
  as "try every day". Use shared semantic signals rather than individual slang exceptions.
- Continue bounded research batches across the remaining 1,034 entries of the original inventory. The
  first three reviewed batches cover 220 distinct baseline entries; later additions are counted separately.
- Finish the requested vocabulary additions: Goon of Fortune, Hills Hoist, "could do with a feed" and
  "wouldn't say no to some tucker". Bulldust itself already exists. The separate constructor/theme design
  does not block independent dictionary improvements.

One product choice remains open for the lexical slice: how much narrator opinion may embellishment add?
"Soldiers" becoming "brave bastards" both adds praise and loses the military role; "the living" becoming
"lucky buggers still breathing" preserves its reference but adds an assessment of fortune. Those effects
should be distinguishable. Evidence metadata establishes attestation; themes permit subject matter;
semantic fit establishes contextual suitability. Input support for courage is distinct from a citation
attesting the phrase. The refined proposal lets existing embellishment settings permit increasing
exaggeration/opinion, with advanced overrides, while separately protecting factual roles and references.
Entries and generated Bulldust would declare meaning requirements and embellishment effects consumed by
shared eligibility. This remains a proposal for discussion; the current slice does not implement it.
