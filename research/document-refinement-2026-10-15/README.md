# Documentation and retelling refinement, 2026-10-15

## Documentation review and controlled refinements

The numeric/profile override contract is retained: General inherits ordinary document behaviours, Custom
keeps optional behaviours off, and both inherit selected level/vulgarity numeric defaults. No complete
configuration is required. Valid combinations remain the caller's responsibility; types/ranges are checked.

The documentation review found actual fidelity failures alongside dry prose. Technical examples were being
translated, neutral people became insults, relative links became family vocabulary, a fronted predicate
contracted incorrectly, and injected prefixes sometimes left ordinary words capitalised.

The resulting publication configuration remains **Swaggie / Dinkum / Dad**, with the uniform notice and own
plain-source links. It now explicitly keeps quotes and Technical terminology, disables person swears and
stacking, and permits only connective/opener/tag garnish. Probabilities are 0.35/0.35/0.25, per-document caps
10/6/4, and the same placement waits two intervening source sentences. No factual riffs, insults or infixes.
These are publication settings, not changes to the public General or Dinkum presets.

Strict Markdown now separates structural quiet from placement eligibility. A known sentence start may take
a leading opener/connective before inline markup, using whole-source sentence context. Continuation units
cannot; tags, tails and riffs cannot attach to incomplete units. Casing evidence is shared across the
document, and uncertain first-word case can prevent insertion. Exact protected source bytes and local record
offsets remain intact.

The contraction exception is a data-driven `unless_before` regex on the relevant phonetic rule. It preserves
stressed be-verbs in fronted predicates and comparisons while ordinary contractions remain available.
Narrow data guards protect relative links, technical liberty and everything-relative clauses. When existing
finite-word hints do not apply, the new POS-based inference requires an explicit subject and a finite verb,
including the present tense. Its negative cases cover noun/gerund, relative and subordinate fragments;
main clauses after subordinate clauses are covered separately. Existing hint-based inference remains.
Both refinements remain conservative; this is not a complete English parser.

## Same-source publication measurement

[docs-measurement.json](docs-measurement.json) compares the 40 authoritative sources frozen in `245ae75` under the engine
and publication configuration at `912dead`, then under the refined engine/configuration. Both runs read the
same source bytes; no model or remote service was involved.

| Activity | Previous | Refined |
|---|---:|---:|
| Selected garnish placements | 92 | 208 |
| Vocabulary substitutions | 62 | 30 |

The lower vocabulary count reflects exact preservation of quoted examples; those examples must not count
as successful flavour. Activity counts are not quality scores. The observed defects are pinned by isolated
positive/negative grammar, boundary, casing, terminology and publication-example tests. Fourteen of 370
golden outputs intentionally change: finite-clause eligibility, declining unresolved-case prefixes,
conservative fronted contractions and subsequent garnish selection. Updating a trigger also changes its
context-keyed substitution roll, including otherwise valid everything swaps.

Independent design review covered all six concerns. Required findings were reproduced and fixed, rather
than weakening technical protections or disabling all drawl. See
[DD-022](../../docs/architecture/decisions/dd-022-sentence-safe-document-flavour.md) and the repository review.

## Semantic fallback performance

The user reported the website's Smart mode as much slower than Basic and requested optimisation of the
core engine. Astra profiled explicit bundled semantic versus n-gram fallback. Dense vector comparisons
dominated the semantic path; most candidates were subsequently rejected by existing shape checks.

The integrated change indexes mandatory-literal token count and canonical text length before scoring.
It preserves original pattern indices, tie order, exact float scores, final matching and thresholds.
N-gram indexing is unchanged. The bundled dot product preserves arithmetic order using standard-library
`map`/`operator.mul`. No model weights, cache, dependencies or precision settings changed. Measurements
cover core translation, not website routing or end-to-end latency.

Five warmed repetitions on the final integrated engine compare exhaustive scoring with the original dot
product against the optimised path, holding current grammar, dictionary and model weights constant:

| Input | Exhaustive semantic | Optimised semantic | N-gram |
|---|---:|---:|---:|
| 3,209-word story | 1,549 ms | 487 ms | 388 ms |
| 580-word technical prose | 276 ms | 93.6 ms | 72.0 ms |
| Short fallback example | 36.0 ms | 4.25 ms | 2.61 ms |

Known-trigger prose is effectively unchanged (~3 ms). Semantic time falls by about 69% on the story and
66% on technical prose; its ratio to n-gram falls to about 1.3 on these long inputs. These are warmed
translation timings, excluding interpreter, dictionary construction and website overhead. No universal
latency guarantee follows from these four samples. All 92 complete-result parity comparisons across
46 inputs/11,267 source words passed. Exact retained float scores and n-gram scoring are also tested.

[smart-performance-current.json](smart-performance-current.json) retains individual timings, options,
platform and source/input hashes. Reproduce with:

```sh
python research/document-refinement-2026-10-15/benchmark_smart.py --repo . --output /tmp/smart-performance.json
```

Validation: **1,814 passed / 2 expected local skips in 455.26s**, with actual full-suite exit 0; Ruff,
40-document publication/link/freshness checks and provenance with isolated wheel inspection passed.
The implementation-focused run passed 347 cases, and the study-integrity run passed 16. Independent
design review converged without outstanding findings. The first full run exposed a release-test fixture
with stale publication settings; the fixture now imports canonical settings. That failing run is excluded
from passing evidence.

## Fresh independent comparison

The comparison uses the unchanged 20-case [pinned study](../maintenance-check-2026-10-15/retelling-study.yaml).
Fresh writers receive original sources and current yarn briefs, not historical candidates. Separate fresh
judge contexts receive key-free blind packets under rubric 3. The two historical anchors remain byte-pinned.
Accepted submissions, diagnostics, reports, source/engine hashes and deterministic verification are retained.
No scores from that fresh comparison are claimed until all outputs and reports are collected and validated.

The local `study.py` driver prepares the frozen brief/source/policy and complete engine-file set, replays
retained tool diagnostics and final acceptance through the canonical yarn session, then issues write-once
blind packets bound to source/output/log hashes. Identical packet regeneration preserves existing reports.
Collection validates all reports before freezing their hashes. Integrity tests reject mutated evidence,
added dictionary files and false acceptance, and permit correction after an invalid first collection. Select a
new local run name for each round; existing manifests/packets are never replaced by changed evidence.

```sh
python research/document-refinement-2026-10-15/study.py prepare --run new-round
python research/document-refinement-2026-10-15/study.py packets --run new-round
python research/document-refinement-2026-10-15/study.py check CASE --run new-round
python research/document-refinement-2026-10-15/study.py collect --run new-round
```

## Controlled second refinement: multi-paragraph quotes

The first frozen round is retained in [study/manifest.json](study/manifest.json), with its outcome in
[study/round-outcome.json](study/round-outcome.json). Nineteen fresh retellings were canonically accepted
and replayed under `245ae75`. FOMC submission was blocked: its straight-double-quoted documents span blank
lines, which the shared quote parser did not recognise. Keeping those documents exact then caused dialect
rejection. No blind packets or quality scores were issued in this aborted round.

The correction permits paragraph breaks in straight double quotes, matching existing curly double quotes.
It applies at shared recognition, with no lint exemption; inches and single/drawl forms retain their
existing guards. Positive/negative regressions cover all translation routes, lint, verify and real submit.
A separately identified writer replacement error in `percentage` is corrected in the new draft; failed
round-one text and diagnostics remain unchanged.

Recomputed briefs change only for FOMC. Its original writer read the new brief and deliberately revised and
submitted the text. The other 19 may carry forward only after exact brief comparison and fresh canonical
tool execution under the newly frozen engine. Per-case writer-origin metadata records that lineage and is
bound to the issued packets. These are reused fresh outputs from this study, not newly authored round-two
texts. The independent blind comparison remains pending until round two is frozen and judged.

The quote-fix full gate exited 0: **1,836 passed / 2 expected local skips in 444.34s**. Ruff, publication
freshness/links and provenance with actual wheel inspection passed. Golden outputs are unchanged.
Independent design review converged cleanly, with 38 quote/study-integrity tests independently passing.
