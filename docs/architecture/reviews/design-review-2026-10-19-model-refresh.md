# Design review: reviewed-dictionary model refresh, 2026-10-19

Status: Independent review converged; integrated verification passed.

## Findings

The review found one stale toolchain statement: the requirements header described Python 3.13 as the
current build, while candidate metadata records Python 3.12.13. The comment now points to per-build
metadata and reports; dependency pins are unchanged. No model-adoption blocker remains in the scoped review.

The independent reviewer reproduced **33/33** required checks through the standard-library package
reader, verified finite/nonzero vectors, dimensions and vocabulary count, and matched report/candidate
metadata, frozen-input hashes and driver hashes. Fresh evaluation/full fits use the unchanged pinned
recipe/base without failure overrides. Evaluation remains **32/33**, with its girl failure retained.

The concrete installed artifacts, research records and report match the isolated candidate. Model status
reports 1.3.0 with an exact current-dictionary fingerprint. Independent provenance/licence and generated
documentation checks passed. The complete integrated suite is still running; commit and release gates
are not waived by these focused results.

## What's done well

Dirty-input provenance is explicit because the corrected dictionary could not pass its required model
gate before retraining. Every recorded input stayed unchanged during both fits. The code retains full-fit
and held-out measurements separately, keeps prior reports immutable and separates model versioning from
package release promotion. The pinned upstream and licence declarations are retained with the updated
model binding and generated notices.

Actual shared lookup comparisons use common current inputs and retain the original fixed cohort. The
adoption notes disclose probably-to-defo, wake-up-to-hurry and pub-first ranking limitations. Avoiding a
specific known wrong category is not described as proving the intended alternative correct.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Certainty-aware lookup | Distinguish probable from definite | An existing retrieval defect remains despite its lower score |
| Context-sensitive ranking | Improve pub-first and container alternatives | Passing the cold-beer reference does not establish ideal ordering |
| Meaning-specific training and stronger contrast benchmarks | Separate sense/degree chains and correct meaning from category avoidance | Requires its own reviewed recipe and fixed comparison design |

No `main` promotion, package release or full-suite success is claimed.

## Final integration verification

The complete reviewed integration passed **2,825 tests with two expected local-corpus skips in 840.53 seconds**.
Ruff, generated-document checks and provenance checks passed. The user approved enabling comic dictionary
terms in solemn text at Troppo, retaining other defaults off and exact overrides winning. Independent
review verified that matrix across the public surfaces. The frozen historical wording gate now passes;
its anchors, input texts and threshold are unchanged. Earlier failed/pending results above describe prior
snapshots and are superseded by this verification. No package release or main promotion is included.
