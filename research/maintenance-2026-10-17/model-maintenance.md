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

## Questions for shaping

Meaning-specific training remains the substantial design question: multi-concept entries, compositional
negation and figurative associations can pull distinct senses together. The observations do not establish
a single cause or justify silently changing the recipe. A refreshed unknown-word benchmark also needs an
explicit current coverage/source-exclusion contract before making unseen-generalisation claims.
