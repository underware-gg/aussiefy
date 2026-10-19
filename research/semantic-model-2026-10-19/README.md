# Reviewed dictionary model trial, 19 October 2026

Model 1.3.0 is prepared for `dev`, with no package release or `main` promotion. Its full fit and exported
standard-library package reader both pass **33/33** required reference checks. The evaluation fit passes
32/33, failing girl; this result is retained rather than replaced with the full-fit result.

## Inputs and execution

The recipe, pinned base revision, seed, cutoffs and required ranking rules are unchanged. Beer reference
labels follow the new serving/container concepts, preserving the original queries and their intent. No
failure is reclassified as known, no exact benchmark sentence is added to training, and no
`allow_failures` option is enabled. Prior 1.3.0 trials and version reports remain immutable.

The full fit uses 1,206 entries, 12,577 positive pairs, 6,910 wrong-sense pairs and 3,775 opposite pairs.
The evaluation fit uses 965 training entries and 241 held entries. It has 10,426 positive pairs,
5,790 wrong-sense pairs and 2,900 opposite pairs. Fresh paths prevent checkpoint reuse; cached-only base
resolution verifies the pinned revision. Execution took approximately 22 minutes.

The required model gate prevented committing the corrected dictionary first. [The trial](trial.json)
records the dirty Git state, exact frozen file hashes, dictionary/recipe/trainer/base hashes, ordered pair
counts and digests, toolchain, all evaluation setups, calibration and reference calls. Every frozen input
remained unchanged through completion. The [driver](run.py) and [comparison driver](compare.py) retain
their exact execution paths as audit evidence; choose fresh paths to repeat them. Commit the model and
data together only after the repository's remaining required checks pass.

## Bounded comparison

[The comparison](comparison.json) runs actual shared lookup under fixed Swaggie/Uncle Bob/Dinkum settings
against the same current dictionary. It preserves the earlier 18-query cohort and separately identifies
eight source-audit queries selected before measuring the candidate. The isolated candidate adapter is
distinct from package-reader parity, which the release driver and independent review check separately.

Friend and worked-hard rankings improve in this cohort. The cold-one raw-model check now passes, while
actual lookup ranks pub (0.68), coldie (0.66), then counter lunch (0.62); the old model ranked counter lunch
(0.70), pub (0.69), then coldie (0.66). Probably still offers defo, and wake-up still offers hurry terms.
A negative-category check ceasing to offer one wrong sense does not prove the replacement suggestions
are correct. No blanket quality or unseen-generalisation claim follows.

The gap benchmark retains historical words, some of which now have dictionary coverage. Its figures are
not a fresh unknown-word false-fill measurement. The shipped old model may already have seen entries in
the new holdout cohort. Automatic gap filling remains disabled by default. Meaning-specific and
degree-compatible training remain separate design work; this candidate is not trained on the new degree
prototype, which remains outside the main checkout.
