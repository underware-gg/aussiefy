# Design review: semantic degree and plural address, 2026-10-19

Status: Converged; integrated verification passed.

## Findings

Independent degree review found that reviewed source forms must own their qualifiers even when not
replacement triggers, and that invalid source frames must not contaminate valid source certificates.
The implementation separates recognition from certification, validates the source frame before transfer
and preserves modifiers for unknown-degree forms. The missing spaced `half cut` variant was corrected in
the corpus rather than by loosening all matching. Independent final degree recheck passed 55 cases and
12 additional phonetic/render-replay probes.

Independent address review found false command readings in parentheticals, arbitrary-interjection
certification and missed coordinated recipients. Ambiguous balanced/qualified/list readings now abstain;
a declared addressee capability supplies the positive lead signal. The integrated reader requires positive evidence for reference as well as address; an unmatched address
is not automatically referential. This removes the separate coordination scanner. Noun modifiers and
unparsed recipient prefixes retain unknown roles. POS guesses need corroborating finite morphology or
governed-object evidence, so bare commands cannot masquerade as quantified subjects.
Independent prototype recheck passed 81 address/schema tests and targeted probes. Integrated qualification
and morphology re-review passed 150 focused cases, 39 additional role probes and two combined
translation/change parity checks, with no remaining findings.

Fieldwise integration retains the original YAML formatting and unrelated metadata. A scratch integration
error in block-list replacement was diagnosed and corrected before adoption. Combined scratch checks
passed 163 tests. The first complete integrated run passed 2,940 tests with two expected local-corpus skips,
with one repetition assertion failing: separating bare `full` from `a bit full` exposed duplicate nested-term
warnings. Repetition aggregation now assigns an enclosing recognised occurrence once across entries;
separate uses of an inner form still count. Independent follow-on review passed all 57 harness tests and
six nested/shared-form probes, with no findings. Final full-suite verification passed **2,942 tests with two expected local-corpus skips in 848.75 seconds**.
Ruff, generated documentation, provenance and diff checks passed.

## What's done well

The existing detection/applicability/form-eligibility seams own these semantics. Vocabulary supplies
meaning and grammar capabilities; no slang ID or screenshot sentence enters Python conditionals.
Style intensity remains separate from reviewed degree, and explicit source modifiers survive later
phonetic processing. Ordinary unknown-degree vocabulary is retained when no degree is stated.

Address semantics retain the np frame and preserve valid referential alternatives. Conservative ambiguity
handling avoids asserting a new person/number reading without enough grammatical evidence. Exact
paraphrases, plans and automatic alternatives cannot bypass the canonical restrictions.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| More reviewed degree families | Extend explicit-degree preservation beyond DRUNK | Requires source/target calibration, rather than guessing from style numbers |
| Broader reference/address grammar | Recover safe transformations of complex recipient/reference phrases | Current ambiguous cases retain grammatical source wording |
| Semantic checks for arbitrary generated prose | Assess meanings not recoverable from known terms | Automatic candidate eligibility is narrower than open-ended semantic verification |
| Model refresh after remaining dictionary corrections | Restore a current dictionary fingerprint when the audited data settles | The bundled model remains usable and required retrieval gates stay enforced |
