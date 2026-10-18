# Design review: sourced slang meanings, 18 October 2026

Surface: dictionary senses, source metadata and policy, the bounded research ledger, meaningful-output
regressions, regenerated translation and changes fixtures, contributor documentation and provenance.
One independent reviewer assesses all six software-design concerns. Evidence and scope are retained in
the [meaning-pass ledger](../../../research/slang-meanings-2026-10-18/README.md).

## Findings

The preliminary review reproduced four meaning errors: joblessness implying benefit receipt, religious
contingency becoming surprise, hardship becoming an earnest attempt, and missing energetic/party senses
of the frog comparison. Each is resolved in dictionary data, preserving existing frame checks. Further
source checking separates generic welfare from unemployment benefits, freedom from fair treatment and
religious oaths/past gratitude from conditional hope.

The user selected `dubious_meaning` gating for three original consecration paraphrases. Component
attestation of genuine/loyal does not establish a sacred sense or attest the complete paraphrase.
Golden readback also exposed slotless “christen” discarding the object in “consecrated it”. Its informal
first-use sense now has its own concept and object slot; generic consecration remains plain by default.

The ledger distinguishes 130 manually selected baseline entries from the 1,254-entry inventory and
does not certify every trigger, register or sense. The unavailable Ozwords PDF remains provisional;
the low-spirits mapping is retained pending stronger evidence. The fox comparison retains its supported
satisfied sense alongside evidence of another interpretation.

Final independent review reports no remaining findings. The reviewer independently passed all 32 sourced-sense
regressions and the four harvest tests, reconciled ledger counts and baseline hashes, and checked current
generated documentation and goldens. The affected documentation/harvest/sense run passed 182 tests; complete
pre-commit verification passed: **2,330 tests, two expected local-corpus skips, 977.18 seconds**.
Ruff, whitespace, dictionary validation and generated-publication checks pass. The acquisition round-trip
test now verifies additive source merging against the existing overlay; independent review and all 26
scrape tests pass, preserving hand-curated entries and idempotence.

Final review found and resolved two narrow-trigger defects: adjective-party patterns now exclude common
political/event compound continuations, and “give it everything” requires a clause boundary so it cannot
leave a relative-clause tail behind. Meaningful-output regressions cover both. Generated-document readback
also caught “attempts from hardship” turning into a malformed attempted-object phrase; the plain source now
says “earnest effort from hardship”.

## What's done well

- Precise concepts and explicit number/slot metadata express the observed meanings without an engine
  classifier, new configuration or weakened frame boundaries.
- Existing source overlays and gates retain provenance and deliberate access without rewriting hand
  curation or presenting original paraphrases as traditional idioms.
- Tests exercise meaningful outputs and negative contexts, retaining tense, number and objects. Source
  counts legitimately affect candidate weights; the incidental STUPID and nonsense-choice golden changes
  remain semantically compatible rather than indicating broader triggers.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Source the remaining 1,124 baseline entries | Broader semantic confidence | The selected audit is explicitly bounded and records its baseline |
| Resolve flat-as-a-tack evidence and variant usages | Distinguish additional senses with stronger evidence | Current mappings remain supported or explicitly provisional; absence is not disproof |
| Narrow pre-existing TRY_OUT object capture | Preserve “try hard to finish it” instead of “give hard a burl to finish it” | The new effort owner correctly avoids this complement; the separate existing try-with-object owner still needs its own object/complement fix |
| Shape model-quality work and refresh training separately | Measure behaviour under a defined quality contract | No runtime algorithm or model is changed; this dictionary update makes its data fingerprint stale |
