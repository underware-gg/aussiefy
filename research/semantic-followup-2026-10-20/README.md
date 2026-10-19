# Semantic benchmark follow-up, 20 October 2026

This work follows the [read-only baseline](PLAN.md#baseline-evidence). It corrects predicate composition,
calibrates appetite degree through dictionary data, and shares source-context restrictions between lexical
and model-assisted lookup. The fourth slice fits a candidate against the settled dictionary and repeats
the fixed measurements. Work is on `dev`; this is not a package release or `main` promotion.

## Changes and boundaries

Predicate targets retain dependent result operators and complements. Each target form must fit that
context; stacks require an established clause boundary. Plans and editor alternatives use the same rules.
Original-aware verification recognises bounded duplicate-complement errors without claiming arbitrary
retelling correctness.

HUNGRY uses the existing degree system, with reviewed source and target certificates independent of style
intensity. Explicit hunger severity is preserved. For example, `very hungry` remains plain when no target
can preserve both its qualifier and grammatical construction. Bare hunger still has a colourful palette.
The [calibration ledger](hunger-degree-calibration.md) records the evidence and limits.

Lookup uses canonical query-fragment readings, external polarity, reviewed degree and a bounded account
of each query's head and arguments. Eligibility, concept ranking and model text use the same permitted
meaning paths. Direct term discovery stays broader. Unsupported wording can still use imperfect model
fallback; the [lookup ledger](lookup-context.md) describes the scope. No phrase-specific Python exception
or override layer is introduced.

## Measurement method

The repeat retains the baseline's 24 diagnostic inputs, three backends, three embellishments and three
seeds (648 rows), plus 90 reference outputs. These are known diagnostic cases, not unseen generalisation
or independent writing-quality judgements. Full source/output copies remain in local benchmark packets.

Curated expression labels and the separate historical Gettysburg anchors remain frozen. Wording overlap
is reported as wording overlap, independently of meaning and grammar checks. Smart timings compare core
backends without website, network or model-assisted retelling overhead. Optimised/exhaustive scorer
comparisons require exact full-result parity. Changes-builder timing retains its 1.5× supported-settings
budget. Timing phases run serially after fitting and other test workloads finish.

The model comparison uses actual standard-library package readers for old and candidate weights under
the same final dictionary and runtime. It retains 18 historical and eight source-audit queries, plus 23
explicit semantic follow-ups. The 49-query diagnostic set is separate from the unchanged frozen release
references, pinned recipe and cutoffs. Rule improvements and weight differences are reported separately.

## Observed results

[The bounded aggregates](benchmark.json) bind baseline `112bf2b` and checkpoint `b9c8b95` to exact
source, driver, dictionary and asset hashes. All three bundled 1.3.0 asset hashes are unchanged. The
curated labels/scorer, historical anchors and Smart timing sources are also unchanged.

| Known diagnostic signature, on its single source across 27 settings | Before | After |
|---|---:|---:|
| Duplicated `enough` complement | 9 | 0 |
| Explicit `very hungry` weakened to `now I'm peckish` | 9 | 0 |
| `knackered, rooted checked` inside a relative clause | 9 | 0 |

Manual reading of every distinct affected output confirmed the removed duplication and unsafe stack.
These are bounded reproductions within 648 rows, not general error rates. Explicit `very hungry` stays
as written. Unmarked relational hunger can still select `peckish enough to eat anything`; relational
threshold calibration is separate unfinished work, not certified by this result.

All 90 reference outputs passed the structural and critical/major verification checks. Minor issue counts
fell from 126 to 99; those checks do not establish writing quality. The separate
[diagnostic verification](challenge-verification.json) passes all 648 current rows and flags nine of 18
retained previous bad outputs: six explicit hunger downgrades and three duplicate complements. Nine
others receive no major issue because extra edits prevent reliable local pairing. Contractions, added
narration and simultaneous edits remain explicit limits of verification.

Lexical and bundled lookup both now abstain for probably, wake up, hard to finish and not out of the
question, rather than offering unsupported meanings. This is a precision gain with a coverage cost.
Worked hard offers hard-work terms; the small-bottle query returns stubby, the can query tinnie, and the
cold-one-at-pub query coldie. Direct vocabulary discovery remains broader than inferred replacement.
Unknown structures and figurative readings such as sick of work/tired of life still need review.

Curated wording coverage remains Gettysburg **5/10** and full Goldilocks **10/22**. Frozen historical
Gettysburg coverage remains Auto/Deadset **8/25**, Auto/Dinkum **12/25**, Auto/Troppo **15/25**, and
Technical/Troppo **9/25**. Quantity permissions are unchanged. Wording overlap is separate from meaning;
no label, threshold or required check is retuned.

## Performance

Five warm repetitions rotate mode order, excluding construction/loading. Technical is raw Markdown
passed to the core, not an end-to-end Markdown/website request. Timings ran serially after fits and the
integration suite ended. Other system load is not controlled; these are workload measurements, not an SLA
or evidence of a causal speedup from an individual change.

| Input | Words | N-gram ms | Bundled ms | Bundled / n-gram |
|---|---:|---:|---:|---:|
| short known | 15 | 3.64 | 3.44 | 0.95× |
| short fallback | 12 | 2.96 | 4.86 | 1.64× |
| story | 3,209 | 379.57 | 494.33 | 1.30× |
| technical | 580 | 70.54 | 92.16 | 1.31× |

The short-known result is approximately parity. All **94 optimised/exhaustive full-Result comparisons**
match against the same current dictionary and weights. That is scorer parity, separate from backend
performance and model-reader reference outcome parity.

Changes passed every supported-setting **1.5×** gate: site-default median **1.12×**, maximum **1.16×**;
maximum over all gated rows **1.342×**. Stress is reported, not gated (maximum 1.48×). Larger-input maxima
are 1.26× at 10,000 characters and 1.13× at 15,000; Markdown maximum is 1.22×. Repeats/settings match the
baseline three-sample run; no extra confirmation was needed at these margins.

Original-aware writer lint on the unchanged 560-word input took **39.24 ms** warm, versus 39.73 ms in
the baseline, with suggestions and English conversion off. Fixed short-sentence process-CPU medians are
1.726/2.670 ms per ordinary Deadset/Troppo item and 1.589/2.621 ms per degree item. Before values were
2.661/3.551 and 1.764/3.467 ms respectively. These bounded sequential measurements are not a causal
speedup claim. Fresh-process startup was not repeated: the baseline's exact startup source/driver was
not retained, so a new cohort would not be an exact comparison. No website or live model-assisted mode
was measured.

## Rejected model trial

Bundled **1.3.0 remains unchanged**, passes **33/33** required references under the current dictionary,
and remains fingerprint-stale. The fresh 1.4.0 trial is **rejected**. The unchanged pinned recipe, base
revision, seed and cutoffs were used in fresh evaluation and full-data fits; `allow_failures` stayed false.
No prior checkpoint was reused, and no required failure was reclassified. Approximate elapsed execution
was 48 minutes under concurrent integration-test load; that is not a training-throughput benchmark.

| Fit | Entries | Positive pairs | Wrong-sense pairs | Opposite pairs | Required references |
|---|---:|---:|---:|---:|---:|
| Evaluation | 966 training / 242 held | 10,355 | 5,998 | 2,678 | 29/33 |
| Full data | 1,208 | 12,532 | 6,860 | 3,654 | 30/33 |

Evaluation misses honest, feeling a bit under the weather, a cold one at the pub and having a chinwag.
Full-data misses girl, feeling really down and a good mate of mine, so strict release exits 1 **before
export**. A separate manual export made an isolated **diagnostic-only rejected reader** outside the repo;
its [check](rejected-reader-check.json) reproduces every pass/known outcome and top-concept list. Eight
checks have different top-form selections: this is outcome parity, not exact full-ranking parity. No
rejected weights, new package model metadata or canonical 1.4.0 release report are adopted.

[The 49-query comparison](comparison.json) uses actual previous/rejected package readers under the same
runtime, dictionary and settings. Thirteen result rows differ, including scores or lower-ranked entries.
The rejected reader loses mate/cobber for a good mate of mine, a practical regression as well as a raw-gate
failure. Both readers retain poor suggestions on unsupported queries such as very large and hard drive.
Passing one negative-category check does not establish that the remaining suggestions are appropriate.
The changed dictionary and holdout also prevent causal comparison of this evaluation run's retrieval
metrics with old fits. Automatic gap filling remains off.

## Provenance and reproduction

[The exact trial](trial.json) retains all six evaluation setups, calibration, pair counts and ordered
SHA-256 digests, reference calls, toolchain and frozen repository input hashes. Every one of its 125
frozen files remained unchanged through fitting and matched `b9c8b95` before subsequent documentation
updates. [The closure](trial-closure.json) binds the stored trial, diagnostic reader, comparison and checks.

The [executed driver](run-model-executed-r2.py) is byte-identical to the actual run. Its initial drift guard
covered base weights and WordNet but omitted tokenizer/configuration/module files. Supplemental
[during-fit](base-integrity-during.json) and [after-fit](base-integrity-after.json) witnesses validate all
12 cached files against their pinned content addresses and match exactly. The
[repaired reproduction driver](run-model.py) now captures and compares the complete snapshot before/after;
its hash differs deliberately. [Integrity tests](../../tests/contributor/test_model_trial_integrity.py)
cover configuration and weight tampering and the cache's additional storage symlink.

To reproduce the isolated trial, select fresh output/cache paths and provide the pinned base and WordNet
3.0, then use `run-model.py --out PATH --cache PATH --nltk-data PATH` with `HF_HUB_OFFLINE=1` and
`HF_HUB_CACHE` pointing to that cache. The direct SentenceTransformer load also relies on those environment
variables. Two preliminary setup failures (incomplete snapshot metadata and missing NLTK path) occurred
before any fit; their local logs are retained and no checkpoint from them was reused.

Local baseline and repeat packets are `/private/tmp/aussiefy-benchmark-20261020/` and
`/private/tmp/aussiefy-benchmark-followup-20261020/`. Full reference outputs stay there. Repeat the existing
slang, quantity, changes, Smart, writer and short-sentence CPU drivers with the recorded settings;
[benchmark_diagnostics.py](benchmark_diagnostics.py) takes `--out` outside the repository. The archived
packet execution manifest records commands and driver hashes. Then use
[aggregate_benchmarks.py](aggregate_benchmarks.py) with `--before`, `--after` and `--out` for bounded
aggregates, and [verify_diagnostics.py](verify_diagnostics.py) with the same flags for source-aware checks.
[compare_models.py](compare_models.py) takes `--candidate`, optional `--old-model` and `--out` for actual
readers; the diagnostic export path and asset hashes distinguish it from shipped 1.3.0.
[The aggregation boundary check](aggregation-check.json) also verifies that a mismatched label packet is
rejected under Python `-O`, with no false unchanged report written. These are explicit exceptions rather
than removable assertions; the final aggregate binds the repaired driver's hash.

## Remaining work

- Investigate the three full-data model failures and concept-sharing training pairs before another fit;
  retain the current gate and avoid repeating the same recipe without a supported hypothesis.
- Review threshold-equivalent forms inside relational predicates, composed degree and qualifier
  consumption into another certified construction. For example, absolutely starving has a strong HUNGRY
  reading, but the current generic rule gives strong plus a non-relational qualifier unknown realised
  degree, so lookup offers no inferred entry cards. This is a conservative policy limit, separate from
  the model. Current preservation does not claim fluent coverage.
- Extend calibration to further graded families based on observed errors, broaden verification pairing,
  and review unsupported/figurative lookup senses. These are independent follow-ups, not hidden guarantees.

The code slices passed focused design reviews and the 3,253-test integration checkpoint. Final
research/documentation review closed every finding. This evidence checkpoint passed **3,256 tests** with
only the two permitted local-corpus skips, plus Ruff, publication and provenance/licence checks. All 146
focused documentation tests also passed after protecting literal query labels in generated guides.
