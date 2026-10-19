# Design review: predicate composition, 20 October 2026

Status: Complete; focused review converged and integrated verification passed.

## Findings

The independent reviewer reproduced two remaining result-construction holes: raw inline formatting hid
`enough`, and coordinated predicates absorbed a shared `so` operator. Detection now reads the existing
visible/unknown following context, retains relational operators even without an immediately visible
result clause, and propagates restrictions through the existing shared-linking-verb grouping. Tests
exercise raw text and the public Markdown route, `so … that` and `too … to`, and multiple backends.

The first verification check treated any recognised long predicate followed by another `enough` as a
major grammatical error. Review reproduced legitimate horse/jockey continuations where the second
`enough` modified `chase`. The final check needs an original, a canonical source predicate with matching
concepts, identical surrounding sentence tokens, and exactly one source pairing. It abstains for
unchanged uses, missing evidence and ambiguous source repetitions. Actual recognised long-idiom nested
continuations are tested, not only unrelated ordinary-English constructions.

## What's done well

Per-form compatibility lives in `usable_forms`/`form_problem`, so a safe short variant remains available
when the primary form is too complex. Entry style class no longer substitutes for grammatical shape.
Plans and automatic alternatives retain the same selection/rendering seam. Stacking reuses
`following_context`: punctuation alone, unfinished relative clauses and hidden context do not establish
room for a comma-stacked synonym. No slang IDs or phrase-specific engine overrides were introduced.

The root's focused composition, degree, context and verification run passed 140 tests. Golden diffs
retain relational operators and remove unsafe stacks; incidental infix placement shifts follow the
existing deterministic match counts. The service fixture removes the stack before `cleaning up` and
updates its alternatives and subsequent offsets without changing the v2 schema or IDs.

The full suite passed **3,132 tests**, with only the two permitted local copyrighted-corpus skips. Ruff,
generated documentation and notices checks passed. Its initial run exposed two obsolete adjacent-swap
exceptions: both state-dependent mismatches disappeared after unsafe stacks were removed. The reviewer
confirmed their removal strengthens the exact pinned-render oracle; the final full run uses no exceptions.

## Related follow-ups

Reviewed multiword complement compatibility could recover safe forms such as `worn out enough`.
Conservative single-word eligibility is sufficient for this slice. Broader attributive parsing and
arbitrary syntactic verification remain independent work. The next authorised slices cover hunger
degree calibration, contextual lookup, then a fresh model and repeat benchmarks.
