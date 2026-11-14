# Gate 4 foundations and evidence review, 14 November 2026

Review surface: the uncommitted foundation/EW4 diff over `0bd24a146e9f4dc68125ec541afa20d150991a21`, including new files. The software-design-review skill used one independent, read-only reviewer across all six concerns. The parent traced and resolved its findings. Production v3 remains active; this is not a review declaring the remaining v4 runtime complete.

## Findings

| Priority / confidence | Location | Concern and finding | Calibration anchor and resolution |
|---|---|---|---|
| High / high | `aussiefy/rounds.py` concept reconstruction | The typed near tuple was passed back to a list-only parser, breaking unrelated concept fixes. | Preserve real consumers: serialise each relation through asdict. Real round write/reapplication/explicit-clear regressions pass. |
| Medium / high | `aussiefy/recognition.py` supported forms | Unresolved source context could return an owned term with no supported concept. | Enforce domain invariants: filter the entry/concept intersection before overlap resolution; GIFT_TALENT positive and unresolved/nonmatching controls pass. |
| Medium / high | `aussiefy/recognition.py` source grammar | Frame detection did not apply authored entry grammar, confusing social/washing hanging out with eagerness and choosing the wrong for/to record. | Reuse the same rule: grammar_problem and ordinary number fit run before resolution with a shared POS pass. The five for/to/social/washing controls pass. |
| Low / high | `aussiefy/personal_terms.py` phrase characters | Ordinary dropped-g and plural-possessive terminal apostrophes were rejected. | Validate without extra restrictions: permit a terminal straight/curly apostrophe, retaining malformed quote/markup controls. Both orthographies pass. |
| Low / high | `tests/functional/test_literal_phonetics.py` counter assertion | Probability1 could not expose an incorrectly shifted seeded counter. | Test observable behaviour: probability0.5/seed0 makes occurrence2 fail and3 fire. The protected middle match still counts; the last word changes. |

All five findings are resolved in the current source. Focused final helper tests pass49 cases and the real round-preservation module passes24. Overlapping focused evidence runs are not summed into a full-suite total; the full checkpoint gate is recorded separately once complete.

The parent also checked known source-publisher spelling aliases. There was no current same-entry double count among the inspected Oxford/Collins/ABC hosts; new Oxford/Collins labels were normalised to the existing canonical family names without changing the source counts. A provisional other-sense note now keeps physical stiff from the unlucky reading. The displayed explain example is regenerated because intentional evidence weights change candidate probabilities.

## What's done well

- The independent reviewer reproduced the calibration exactly in memory. All300 sample identities are unique and agree with the score rows; every applied follow-through source matches its ledger.
- Blocked pages and wrong senses add no support. Partial forms/meaning limits, historical inspection dates, community authorship and Rob's testimony remain explicit.
- Personal terms are deterministic, request-local objects; preparation does not mutate dictionary entries or identity and supplies no documentary evidence.
- Literal-span tests cover earlier length changes, intersecting multiword matches, and identical unprotected wording elsewhere.
- Active v3 producers and illustrative, non-active v4 proposals remain distinct.

## Related follow-ups

| Opportunity | Concrete benefit | Why separate from this checkpoint |
|---|---|---|
| Broader ambiguity curation before ED10 activation | Recognises supported Australian senses without marking ordinary polysemy as slang. | The source reader is an internal foundation, not yet called by production translation; this work remains required for v4 activation. |
| Concept-free garnish in kept spots | Gives attention markers and similar words a coherent reading/plain-option path. | Belongs to the remaining kept-spot design/integration rather than the evidence calibration. |
| Real ED10–13/ED15 producers and fixtures | Verifies actual kept/personal/held/near emission, selection and surface forwarding. | Schema proposals are not emitter proof; these features are explicitly unfinished and must be completed before freeze. |
| R1 schema errata | Removes the inherited v3 key description and makes each near alternative's citation explicit. | Known proposal corrections are recorded in the Brain draft and must be resolved before freeze. |
