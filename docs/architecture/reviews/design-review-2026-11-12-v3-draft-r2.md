# Changes and cards v3 r2 — local design review

Date: 12 November 2026
Surface: the diff from engine dev `89502ed`, including review schemas/examples, shared v3 projections,
the extracted construction identity owner and string-compatible preference diagnostic codes.

This is a local review using the software design review concerns and calibration. No independent reviewer
or other agent was contacted, in accordance with the standing instruction. The review target is r2's
coherence and checks, not completion of the combined slices or activation of the new contract.

## Findings

Resolved before the full gate:

| Priority | Location and concern | Evidence and resolution | Calibration / confidence |
|---|---|---|---|
| Medium | `scripts/publish_docs.py`, draft classification; completion | The first full gate found the new normative draft README outside the publication source/output/plain partition. Register contract drafts as kept plain, rename the prefix registry to describe its actual role, and extend existing classification fixtures. The superseded full run was stopped; the final gate starts from the corrected frozen snapshot. | Completion means observed working. High, reproduced failing classification test. |
| Medium | `aussiefy/v3_contract.py`, construction role checks; verification | A unique `(role, ingredient_id)` pair alone permits two different ingredients for the same role. Require exactly one occurrence of every family role and a compatible ingredient kind; also require occurrence joins to cover the canonical part set. | Validate inputs vs trust callers: enforce load-bearing semantic invariants. High, direct inspection. |
| Low | Package draft documentation; structural boundary | Host-specific staging coordination had been repeated in package documentation. Keep deployment choices in the Brain project plan and leave package docs about the consumer contract. | Depend toward stability. High, direct diff inspection. |
| Low | `tests/functional/test_changes_v3_draft.py`, bulldust coverage; completion | The six r1 examples contain no bulldust entry card, so an evidence-specific walk alone misses the entry schema. The rejection sweep now first makes every lexical metadata location valid bulldust, then removes/nulls its maker. | Test behaviour, observed completion. High, observed failing coverage assertion. |

No unresolved findings for the review-stage hand-off. Activating a public v3 producer without the remaining
integration and replay work would violate the stated scope; the package's active v2 boundary remains tested.

## What's done well

- `construction_identity` reuses the exact pre-existing hash framing and rendering order; composition and
  semantic checks share the rule instead of reimplementing an identity that share links depend on.
- The v3 projection derives presentation attribution without mutating TermMetadata or attestation scores.
  Structural checks require makers and graph checks compare occurrences with their cards.
- Nested spans are validated against their own rendering, with two independent length-changing edits and
  a leading non-BMP character as a consumer scenario. No document-global hypothetical offset survives.
- Preference warnings carry codes at creation while retaining Python string behaviour and unchanged JSON
  messages. Real plain and document results exercise the projection; no prose parsing classifies messages.
- Review assets and shared pure helpers add no framework, I/O, settings policy or account knowledge to the
  core. Active changes and lookup have not acquired a partial contract upgrade.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent of this hand-off |
|---|---|---|
| Wire shared cards/envelopes into real changes and lookup together. | Enforce this draft on emitted results and all document restoration routes. | Explicit remaining 3+6 integration; r2 is the requested pre-freeze review artefact. |
| Define request-side replay/pins with persistent riff selectors. | Resolve stored picks without relying on a tuned candidate pool being reproduced untuned. | Required before tuned sharing ships; response identity alone cannot supply a request input. |

Focused verification: 156 cases passed before the final documentation and full gate. Full-gate evidence is
recorded in the linked Brain checkpoint report and external receipts, rather than edited into frozen source.
