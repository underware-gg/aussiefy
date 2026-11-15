# Design review: general sentence wording scope

One independent read-only reviewer checked the implementation against the software-design principles
and all six review concerns. The brief requires a general mechanism with no frozen v4 schema change.

## Findings

No outstanding finding remains. The reviewer reproduced a noun fragment from an irregular source
past and an attributive participle incorrectly accepted as a finite target. Conservative source
morphology and positive target grammatical evidence now have distinct roles; both regressions pass.
Proper-name owners retain surface case, argument case conversion uses source/target values separately,
and auxiliary preservation is limited to scoped plain candidates. No ordinary placement or seeded-key
policy changed. The reviewer independently passed 24 scope checks before the final two inversion cases;
the subsequent scope/acceptance focus passes. Earlier rendering/fixture focus passed 317 checks.
Full-suite and delivery receipts are recorded separately with the checkpoint.

## What's done well

- Actual source tokens replace inference from a union of possible pattern words.
- Existing capture, phrase-token, span and spot-rendering mechanisms carry ownership and agreement.
- Operator and argument boundaries prevent simple polarity movement while uncertain cases abstain.
- Ordinary dictionary realisation, frozen schema bytes and held vocabulary remain unchanged.

## Related follow-ups

Rob still decides the Gate 4 disposition of the three source-preserved cases and H25. Authored English
and personal share links remain outside the site's requirements; no request contract is planned.
