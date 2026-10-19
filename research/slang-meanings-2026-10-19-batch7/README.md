# Public-source meaning audit, 19 October 2026 — batch 7

Research only: **120 exact original-baseline IDs**, mostly garnish and the next idioms. Snapshot `2687d7f`;
original inventory `5d1fb04` contained **1,254** entries. The manifest digest and four dictionary/concept
file digests are in [audit.yaml](audit.yaml), with the captured full trigger records for each selected ID.
Parent semantic work proceeded concurrently in another worktree; these observations describe this snapshot,
not a guarantee that all findings remain unfixed in the live checkout.

| Decision | Entries |
|---|---:|
| Selected sense supported | 49 |
| Multiple meanings, component construction or contextual scope qualified | 58 |
| Mapping, gloss or note correction recommended | 8 |
| Stronger exact-use evidence needed | 5 |
| **Total** | **120** |

The previous seven ledgers cover **700** original IDs. This batch brings the disjoint total to **820**,
leaving **434**, excluding parallel batch8. Integrating both 120-entry batches brings coverage to **940**
and leaves **314** original entries. This is researched coverage, not a claim that all mappings are correct.
There are **107** source-catalogue records and **115** per-entry proposals in
[sources-proposed.yaml](sources-proposed.yaml). Provisional entries are excluded from those proposals.

## Eight bounded recommendations

1. **`point-percy`: preserve bathroom purpose.** Public evidence is specifically urination with penis imagery.
   Generic visits can instead be to wash hands. Retain the phrase for the supported action; do not infer it
   from a toilet-room destination. The Barry McKenzie connection is discussed in Ozwords, with suspected
   coinage explicitly distinguished from established popularisation.
2. **`go-crook-at`, `give-a-serve`, `tear-strips-off`: preserve rebuke context.** All three concern telling
   somebody off. Shared `SCOLD` triggers also admit shouting for help. This overlaps the parent's existing
   source-backed `SCOLD` refinement. Collins directly illustrates the plural *tore strips off*; there is no
   remaining plural-form evidence gap in this record.
3. **`reckon-had-buckleys`, `reckon-no-bloody-way`: preserve uncertainty.** Tentative doubt can leave an
   outcome possible; these render it effectively hopeless or impossible. Keep the strong idioms for that
   meaning, with any deliberately stronger assertion controlled explicitly.
4. **`g-ya-mad-cunt`: qualify the social-use note.** The Australian-affectionate/American-offensive split is
   too categorical. Research documents contextual solidarity alongside continuing offence in Australia.
   This recommends more honest explanatory wording, not an automatic register, flag or dial change.
5. **`do-your-nana`: qualify the derivation.** Collins directly supports *nana* as head and calls its banana
   derivation probable. Preserve the term; replace the categorical equals-chain with qualified wording or
   leave etymology out of the short gloss.

Six read-only observations establish the automatic context issues. One further consent/goer probe is retained
as contextual exploration rather than a confirmed failure. Common settings:
`Translator(lookup_embedder=None)`, level5, vulgarity3, `embellishment='deadset'`, `embedder='none'`,
`unlock=['all']`. These explicit research settings are not proposed production defaults.

| Entry / seed | Input | Observed output |
|---|---|---|
| point-percy / 0 | She went to the bathroom to wash her hands. | She pointed Percy at the porcelain to wash her mitts. |
| reckon-no-bloody-way / 0 | I doubt the plan would work, but it might. | I reckon there's no bloody way the plan will come off, but it might. |
| reckon-had-buckleys / 2 | I doubt the plan could be done, but it might. | I reckon the plan has Buckley's, but it might. |
| reckon-a-goer / 4 | I go along with the plan, but I know it will fail. | I reckon the plan is a goer, but I know it'll fail. |
| give-a-serve / 5 | She yelled at him for help. | She gave him a serve for help. |
| tear-strips-off / 0 | She shouted at him for help. | She tore strips off him for help. |
| go-crook-at / 1 | She shouted at him for help. | She went crook at him for help. |

## Evidence limits and preserved ranges

The five provisional records are `g-bugger-me-sideways` (the exact pope extension), `g-fark-me`
(exact construction and claimed mildness), `g-too-easy` (stronger cheerful-sign-off evidence),
`pay-out-on` (stronger exact mockery-construction evidence), and `stick-out-like-a-country-dunny`
(exact mixed comparison). Limited positive evidence or attested components remain recorded. The pope
extension already has project-authored/fabricated provenance and a gate; this pass does not alter it.
Missing evidence is not proof that the other expressions were invented or have the wrong meaning.

The country-dunny sources distinguish conspicuous *dunny in a desert* from lonely *country dunny*.
That distinction motivates a precise source gap, not a ban on composing a visible isolated-outhouse image.
The fark source is collaborative and contains accent-dependent analysis: spelling alone does not establish
that a swear is less forceful. No new vulgarity classification is imposed here.

Some useful ranges survived scrutiny: *not worth a cracker* explicitly covers both worthless and useless;
*game* covers bravery as well as willingness; *shoot through* has plain-departure and more rapid/avoidant
uses; *dry as a dead dingo's donger* can describe country as well as thirst. The horse-and-jockey hunger
comparison has a folklorist collection and primary creative attestation; personal rhythm preferences do
not make it fabricated. Rookwood's illness/cemetery comparison is supported. Bondi-tram historical detail
is labelled probable by ANDC; do not turn the qualified explanation into certain route history.

The goer source allows an acceptable OR feasible proposal: consenting to a plan known to fail can still
judge it acceptable for another reason. Accordingly, the seed4 example does not establish a contradiction
on its own and supports no automatic narrowing. This source distinction was corrected during cross-review.

Garnish records separate lexical meaning from writing policy. *True story* and *no word of a lie* assert
truth; fool comparisons judge a person; listener questions request a response. Sources for components do
not certify arbitrary insertion, exact long strings or harmlessness in every relationship. Existing semantic
planning is the appropriate place to preserve those distinctions; this research adds no parallel policy.
The equality sentence is transparent project wording, with male-oriented *bloke*, rather than a separately
attested traditional formula for every sort of equality. This is contextual follow-up, not another reproduced
runtime finding.

Evidence includes edited dictionaries, dictionary publishers, parliamentary/oral-history primary usage,
creative primary passages, folklorist collections, research commentary and clearly labelled collaborative or
independent glossaries. Copies and reproductions are not counted as independent authorship. The cow-on-a-flat-
rock account is American collected folklore: it supports the expression and meaning, not Australian-exclusive
origin. Source prose and reference works are not copied; summaries are original paraphrases with scope limits.

## Verification

The ledger was checked for exact manifest order/hash, 120 unique IDs, membership in the original1254,
no overlap with previous700 or parallel batch8, declared decision counts, source-reference integrity and
per-entry proposed URL agreement. Source notes preserve weaker access and full-expression limitations.
The seven probes were observed at the stated snapshot. No runtime/data/flags/docs/index changes, staging
or commits were made by this researcher. Independent cross-review is required before these notes land.
