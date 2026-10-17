# Design review: fidelity maintenance, 17 October 2026

Surface: matching directives, finite clause selection/realisation, morphology, sense triggers, phonetic rules,
golden outputs, documentation and focused regressions. One independent reviewer assessed all six concerns
against the software-design principles and calibration references, including runtime probes and output readback.

## Findings

No remaining findings after correction. Two medium-priority, high-confidence findings were resolved:

- Perfect-have clauses need auxiliary inversion, while possession needs do-support. The shared question-form
  function now distinguishes them; selection and realisation use the same eligibility rule.
- Bare restless-sleep compounds swallowed literal throwing with an object, including the longer progressive
  clause pattern. Complete-phrase guards now apply to both verb and clause patterns, with explicit in-bed
  forms. Independent probes preserve ball/rubbish/pancake throwing and recognise both in-bed word orders.

Earlier premise review also tightened the scope: fixed finite/negative idioms remain available in statements
but are declined in questions; shall is preserved in all contexts because punctuation does not establish its
modal force; QUIT guards handle general complements; ambiguous establish and wholehearted devotion stay plain.

The reviewer independently ran all 68 focused regressions and whitespace checks. Full-suite results are
recorded in the maintenance ledger before commit.

## What's done well

- Selection and realisation share question eligibility rather than duplicating grammatical assumptions.
- Data-owned directives express the same complete-phrase boundary for two actual callers; unsupported
  frames and unknown directives fail at the dictionary boundary.
- Conservative sense boundaries retain useful, precise slang without guessing missing source meaning.
- Golden and documentation readback demonstrates the fixes in actual text, including the Bible and Hansel.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| “Doesn't bloody well my suit fit…” in the existing Emperor output | Place emphasis after the question subject | Existing garnish behaviour, assigned to prose refinement |
| Independently curated slang labels | Measure actual slang reproduction separately from historical wording coverage | Requires a new fixed-label baseline |
