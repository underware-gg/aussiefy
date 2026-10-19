# Design review: contextual lookup, 20 October 2026

Status: Focused review converged; integrated verification passed.

## Findings

The independent review reproduced and closed four related source-evidence defects:

- A partial MAN or VERY reading globally excluded other query meanings. Scope now distinguishes local
  evidence from an exhaustive recognised head, and abstains for unaccounted content.
- A multi-concept entry's unrelated second label rescued a denied sense. Candidate eligibility, concept
  scoring and model texts now use the same permitted paths; restricted paths omit the mixed gloss.
- Immediate predicate negation missed determiners and other frames. External polarity shares
  `positive_context` before the source phrase, preserving phrase-internal negative meanings and separately
  supported positive occurrences after a denial.
- A complement branch swallowed recognised predicates or treated every IN tag as a preposition. It now
  reuses nominal prepositions, declines other predicate/subordinate content, and includes degree-owned
  spans when accounting for coordinated heads.

Golden review also narrowed ambiguous `hard` to `hard ?=to`, avoiding an unsupported difficulty reading
in `hard at work`. The source assertion is dictionary data, with regression coverage.

The final focused review has no remaining findings relative to the bounded lookup goal. Root adoption,
documentation and full-suite verification are recorded separately below.

## What's done well

Query fragment mode is explicit and defaults off in ordinary detection. It neither fabricates subjects
nor changes automatic replacement framing. Corpus meaning guards replace query-specific Python fixes.
`work hard ^end` uses the matcher's existing inflection and clause-boundary policy, preserving dependent
tails while allowing genuine coordinated clauses.

Direct, inflected and partial term discovery remains intentionally broader than inferred meaning.
Reviewed source degree constrains bare inferred targets. POS tags are computed once and shared with the
canonical detector. Controlled-model and overlay tests distinguish policy behaviour from the current
model's incidental rankings; historical model thresholds and references remain unchanged.

The adopted root passed the combined 259-check run. After the corpus narrowing, 97 lookup/sense checks
passed and the reviewer confirmed the dictionary assertion and its regressions. Golden review found only
intended appetite preservation plus an incidental deterministic drawl shift.

The first full run passed 3,251 tests with two permitted skips, but exposed one obsolete route assertion:
`knackered beyond belief` now receives canonical TIRED matches rather than requiring model scores. The
reviewed test retains that original positive case and adds `physically exhausted beyond endurance`, which
must still retrieve TIRED vocabulary through the actual local-model route. All 91 static/lookup checks
passed after the change. No frozen reference, threshold or required model gate changes. The final full rerun passed 3,253 tests with two permitted local-corpus skips.
Historical measurement prose and the stale refusal example are also corrected and independently reviewed;
146 documentation tests plus publication and Ruff checks pass.

The final integrated checkpoint passed 3,253 tests with only the two permitted local-corpus skips.
Ruff, publication and provenance checks passed. The review index links all three October 20 reviews;
plain-source relative-link corrections were validated by publication. No runtime or dictionary change
was made after the final full run.

## Related follow-ups

Add reviewed corpus restrictions for figurative `sick of work` and `tired of life`. Improve inference for
unsupported wording independently of the current bounded source rules. Unknown-query model fallback
remains imperfect; no universal word-sense guarantee is claimed.
