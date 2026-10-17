# Design review: curated benchmark and trainer preparation, 17 October 2026

Surface: independently curated labels, fixed scorer/baseline, trainer annotation cleanup, provenance,
documentation and regressions. One independent reviewer assessed all six software-design concerns.

## Findings

No remaining findings after correction. Premise review established the full Goldilocks source pairing and
excluded child/adult sheila mappings, loose Gettysburg paraphrases and invented events from positive labels.
The score is unique target-expression reproduction, not semantic or aligned-event fidelity. Raw counts
remain explicitly unaligned, including any matching wording in an invented event.

Draft provenance was tightened to record the actual dictionary/scorer/label digests, Git base and dirty flag;
the base commit does not pretend to contain then-uncommitted scorer/labels. The final reviewer independently
matched all three digests and recomputed every per-document result and output hash: 6/10 Gettysburg and
10/22 Goldilocks-full. No engine/dictionary tuning followed the scores; historical gates are unchanged.

The trainer's separate cleanup leaked grammar directives. Recipe placeholders now bind before shared
`strip_markup`, preserving pronouns while removing annotations. This is the same language-boundary rule
owned by the existing utility, not merely a similar-shaped helper. Lowercasing suits the pinned uncased base.
The recipe, quality gates, historical reports and conditional imagery's separation from synonym pairs remain.

The reviewer independently passed 21 benchmark/trainer tests and whitespace checks. The parent passed 167
benchmark/trainer/current-document checks. Complete pre-commit results are recorded in the maintenance ledger.

## What's done well

- Independent pre-measurement labels and explicit exclusions avoid deriving success from current output.
- Hash-bound inputs and narrow sentence-bounded normalisation make the measurement inspectable and repeatable.
- Unique-expression hits and raw counts are distinct; repetition does not inflate coverage.
- No baseline-derived threshold is presented as an independently justified quality bar.
- The trainer reuses the correct owner after slot binding, without redesigning training architecture.

## Related follow-ups

Proceed with planned prose refinement and model maintenance. No additional follow-up identified.
