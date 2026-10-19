# Semantic benchmark follow-up, 20 October 2026

Baseline: `112bf2b`. The read-only benchmarking pass found result-complement duplication,
unsafe stacks within relative clauses, uncalibrated hunger severity, and contextual lookup errors.
429 reference/semantic tests and 33 model reference checks passed despite those counterexamples.
No historical labels, thresholds or anchors are being weakened or retuned.

## Slices

1. **Predicate composition — complete.** Retain relational operators and dependent complements;
   filter each target form rather than its entry's style class. Stack only at established boundaries.
   Keep plans and alternatives on the same selection/rendering path. Add bounded verification for
   recognised duplicate result complements.
2. **Hunger severity.** Review source and target degrees for HUNGRY using the existing generic degree
   system. Preserve explicit severity, including in original-aware verification, without inferring
   unknown certificates from style intensity.
3. **Contextual lookup.** Share supported meaning, polarity, degree and argument restrictions across
   lexical and model routes. Preserve explicit term discovery and abstain where evidence is absent.
4. **Model refresh and repeat measurements.** Fit fresh evaluation/full models after dictionary changes
   settle. Preserve the pinned recipe and historical checks, add distinct relevance checks where needed,
   retain failures and exact provenance, and compare the exported reader's actual lookup behaviour.

Each slice receives a software-design review, fixes for findings, Ruff and the full test suite before
commit. Edit plain documentation and regenerate its public copies. Work stays on `dev`; no release
promotion or communication with the separately managed website/design agent is part of this work.

## Baseline evidence

- Curated target expressions: Gettysburg 5/10 (previously 6/10), full Goldilocks 10/22 (unchanged).
  Removing unsupported sympathy wording loses a hit; wording reproduction is not meaning accuracy.
- Frozen historical Gettysburg anchors: Auto Deadset 8/25, Dinkum 12/25, Troppo 15/25;
  Technical/Troppo 9/25. The historical Auto/Troppo gate remains 60%.
- Warm bundled/ngram runtime ratios on four fixed core inputs: 1.16, 1.62, 1.34, 1.77.
  All 94 optimised/exhaustive full-result comparisons matched.
- `changes` stayed within the 1.5× gate at every supported setting; site-default median 1.10×.
  The two closest rows passed seven-repeat confirmations at 1.126× and 1.299×.
- A diagnostic 24-input, three-backend, three-embellishment, three-seed cohort produced 648 rows.
  The hunger duplication and explicit `very hungry` → `peckish` each appeared in 9/27 policy rows on
  their respective single sources; those are reproductions, not population error rates.
- 90 extra reference outputs passed structural checks and verification's critical/major gate.
  `verify` also accepted the duplicate hunger complement and severity downgrade without an issue.
- Lookup offered `defo` for `probably`, hurry phrases for `wake up`, and `het up` above hard-work terms
  for `worked hard`. Lexical lookup offered impossibility phrases for `not out of the question`.

Existing measurement drivers remain in `scripts/benchmark_{slang,changes}.py`,
`research/document-refinement-2026-10-15/benchmark_smart.py`, and
`research/semantic-refinement-2026-10-19/`. Timings exclude website/network overhead. The local complete
baseline packet is `/private/tmp/aussiefy-benchmark-20261020/`; this summary retains its bounded findings
without committing generated copies of source texts.

## Slice 1 checkpoint

Independent review converged after raw-formatting, coordinated-operator and bounded-verification fixes.
The final full run passed 3,132 tests with two permitted local-corpus skips; Ruff, documentation and notices
checks passed. Two historical adjacent-swap exceptions disappeared and were removed from the exact
pinned-render oracle. Hunger and lookup prototypes remain outside this committed checkpoint.
