# Model maintenance, 17 October 2026

The first current-dictionary candidate passed 30/33 required reference checks, failing three, and was not exported.
Shipped 1.2.0 remains in place and passes 33/33 against the same current dictionary. No reference was weakened,
reclassified as known or bypassed. Model version 1.3.0 remains unreleased.

## Retained trial

[The rejected trial](model-trial-before-order-fix.json) records the pinned toolchain, original fit/recovery
provenance, evaluation metrics, complete final reference decisions and 18 fixed-query lookup comparisons.
The trainer cleanup was committed first at `2028a88`. The later prose changes did not alter dictionary
training-text fingerprints. The optional cached-only recovery reused the saved evaluation fit after an
offline repository-tree lookup failed; all ten saved checkpoint artifacts remained byte-identical.

The full-data fit failed on **a great war**, **a top bloke** and **honest**. Actual shared lookup comparisons
use the ordinary Swaggie/Uncle Bob/Dinkum policy. The candidate uses an isolated Model2Vec Embedder adapter,
not a package export: no package-reader parity or shipping claim follows. Some queries improve (worked very
hard); others still give misleading alternatives (very cold includes beer). Existing shipped-model misses
also remain, including wake up and probably. This is a bounded diagnostic, not comprehensive language quality.

The current-entry split is shared with freshly scored 1.2.0, but that production model may already have seen
some entries. Its higher current-corpus recall is not a clean common-unseen comparison. Raw gap scores retain
the historical fixed cohort; sozzled, starved, kitchen and umbrella now have dictionary coverage. They are
not current unseen-generalisation or real current false-fill rates. No 90% blanket promotion gate is added:
that separate precision bar concerns enabling automatic gap filling, which remains off.

## Reproducibility correction

The recovered evaluation/static stages reported 10,476 versus 10,477 positive pairs despite matching declared
inputs. Fresh processes with different Python hash seeds reproduced larger differences: 10,478 versus
10,511 pairs, with 347/380 pairs unique to each set. NLTK stores WordNet relation pointers in sets; their
order changed which adjective neighbours survived the recipe's truncation. The first trial therefore
cannot be presented as an exactly replayable fixed-pair experiment. Dictionary growth and cleaner changes
also prevent causal claims against earlier trials.

Sort only similar-to neighbours by stable synset name before selection. Preserve source sense-frequency
order, first-sense slicing, lemma order, exclusions and recipe limits. [Fresh-process evidence](model-pair-order.json)
now matches the complete ordered positive, wrong-sense and opposite pair digests for both splits: 10,493
evaluation positives and 12,640 full-fit positives. The two mocked neighbour-order regressions also pass
alongside the existing trainer tests on Python 3.10 and the primary environment.

A trial after this correction must start with fresh evaluation and full-data fits after the corrected
trainer is committed. The old checkpoint cannot be reused for changed pair selection. Stable data ordering
does not promise bit-identical weights across hardware/toolchains.

## Fresh deterministic trial

The corrected trainer was committed and pushed as `72015dc` before either new fit. Both began from the
pinned base with clean Git inputs, with no checkpoint reuse, recipe changes or weakened gates. Cached-only
snapshot resolution avoided the earlier offline metadata problem. The run finished normally with release
exit 1 because the candidate failed its reference gate; it did not export any package model.

[The fresh trial](model-trial-deterministic.json) retains execution/input/checkpoint hashes, toolchain,
ordered pair counts/digests, all six evaluation setups, calibration summaries, complete candidate/shipped
reference decisions and the same eighteen shared lookup queries for both models.

| Measurement | Result |
|---|---|
| Evaluation fit | 951 entries; 10,493 positive / 5,954 wrong-sense / 2,978 opposite pairs |
| Full-data fit | 1,189 entries; 12,640 positive / 6,675 wrong-sense / 3,821 opposite pairs |
| Tuned evaluation model | 28/33 required references passed |
| Full-data candidate | 31/33 required references passed |
| Shipped 1.2.0, rechecked | 33/33 required references passed |

The full candidate fails **girl** (retrieving WOMAN/GIRLFRIEND) and **a good mate of mine** (missing FRIEND
among its first three distinct concepts). Four known reference failures pass: wide awake, put up with,
dying and worked very hard. These are model-level retrieval checks, distinct from the actual toolkit's
combined lexical/semantic ranking and policy guards. Both actual lookup runs decline girl under the frozen
policy; that does not waive the model gate. The candidate declines probably rather than suggesting definite
certainty, and offers WORK_HARD for worked very hard. It still offers sleep for wake up and beer among very
cold results. These bounded observations do not establish general superiority.

Pair hashes in this trial use compact UTF-8 JSON. The prerequisite report uses ordinary JSON separators;
an independent rebuild matched all six complete ordered streams under both serializations. The saved
evaluation checkpoint, all reference decisions and full calibration also independently reproduced. Stable
selection is established; a single trial does not establish bit-identical retraining weights.

**Decision:** keep shipped 1.2.0. The corrected fresh trial improves the count over the interrupted historical
trial but still fails the unchanged required gate. Dictionary/cleaner/pair-selection changes and a single
fit do not identify a cause for any quality change. No new version, cut-off or reference exception is added.

## Questions for shaping

Meaning-specific training remains the substantial design question: multi-concept entries, compositional
negation and figurative associations can pull distinct senses together. The observations do not establish
a single cause or justify silently changing the recipe. A refreshed unknown-word benchmark also needs an
explicit current coverage/source-exclusion contract before making unseen-generalisation claims.
