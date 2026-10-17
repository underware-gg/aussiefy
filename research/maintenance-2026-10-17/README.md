# Maintenance follow-through, 17 October 2026

Authorised after contextual imagery commit `50a84f0`. Work is on `dev`; each implementation slice receives
an independent software-design review, Ruff and the complete pytest suite before commit. Clear fixes proceed;
material product tradeoffs are flagged for shaping while independent work continues.

| Slice | Scope | Status |
|---|---|---|
| 1 | Grammar and senses: modal clauses/questions, deliberative shall, restless tossing, object-taking quit, evidentiary establish, wholehearted devotion | Complete |
| 2 | Seed-listicle intake: acquire through existing pipeline, verify senses, reconcile coverage and retain decisions | Complete |
| 3 | Curated slang benchmark with independent review, fixed labels and an honest baseline | Complete |
| 4 | Prose refinement: assess technical/instruction/body voice and fix clear defects while preserving configured flavour | Pending |
| 5 | Bundled-model maintenance: inspect training environment, retrain on final data and enforce existing quality gates | Pending |
| 6 | Pre-launch integration: exercise available client/API paths, measure actual routing/latency, document verified limits | Pending; website not built |

## Decisions and verification

No product decision is pending at the outset. Model promotion remains conditional on existing reference and
calibration gates. New benchmark labels must be chosen for meaning, not to produce a desired passing score.
The website and live client are separate integration surfaces; core timing does not establish end-to-end latency.

### Slice 1: grammar and senses

Committed and pushed as `ee6d948`.

The initial probes reproduced six existing failures. The fixes share question-form eligibility with
realisation; distinguish perfect-have and possession; decline an independently finite clause under an outer
auxiliary; retain shall; separate wholehearted devotion and truthful assurance; recognise restless tossing;
preserve bare establish; and apply data-owned complete-verb guards to QUIT. Fixed finite/negative idioms
remain useful in statements. Wholehearted language and ambiguous manner words remain plain rather than
being converted into assertions of honesty.

Pattern directives are validated and stripped consistently before lookup/training text is prepared. An
independent review found the perfect-have distinction, which was then fixed and tested. Golden changes
include corrected modal questions, the Bible's wholehearted devotion, Hansel's restless tossing and retained
modal force; resulting seeded contraction/swear choices also move. No historical research evidence changes.

Independent review converged after correcting perfect-have inversion and guarding literal-object restless
compounds. Final verification: **2,049 passed, two expected local-corpus skips, 484.70 seconds**; Ruff,
whitespace, dictionary validation and generated-publication checks passed. The 68 focused regressions also
pass on Python 3.10. The first full run found one obsolete reference assertion forbidding shall-not; it was
replaced with a positive shall-preservation assertion, retaining the ordinary contraction, semantic-count
and historical 60% coverage gates, before the successful complete rerun.

Independent preparation: the seed page fetched through the existing scraper (227 raw rows), exposing a
declared-UTF-8/implicit-Latin-1 fetch bug. Correct decoding produces 212 candidates; raw HTML and copied
definitions remain temporary. The pinned training toolchain, WordNet 3.0 and pinned base model are validated
in an isolated Python 3.12 environment. No live API key is present in the current process. The user confirmed
the website is not built; it will live in `underware-gg/aussiefy-web`, initially at
`aussiefy.underware.gg`. Available engine/toolkit interfaces can be checked now; website routing/browser
latency needs the future application. Standalone domain options are retained separately for shaping; no
purchase or deployment is authorised by that research request.

### Slice 2: seed intake

Committed and pushed as `4a4e489`.

The correctly decoded scrape yields 212 candidates from 227 raw rows. The complete seed ledger accounts
for ten additions, 88 existing term/variant/component matches, 100 conditional craft/verification notes,
three declined sense mappings, five metadata rows, two retained gates and four retained omissions. Coverage
does not claim that a complete row can be substituted grammatically. Manual proposals use our own glosses
and pass the existing `plan_review`/scratch-validation/apply boundary; no API tagger was called.

Independent curation review corrected two premature classifications: the Malvern Star row actually claims
slim/wiry, and financial two-bob-watch usage has contextual attestation. Both remain conditional craft,
rather than asserted wrong meanings. Galah coverage is explicitly a vocative tag/component. New precise
concepts distinguish brazen effrontery, frantic movement and frugal subsistence from arrogance, busyness
and stinginess. The shark/shout pun uses passive conditional wording to bind any subject without inventing
an object pronoun. No actual shark attack is asserted.

The fetch-boundary fix uses the existing HTML decoder only when HTTP omits a charset. Original response
bytes/hash remain separate from decoded working text; raw source prose is not redistributed. Explicit HTTP
charsets, legacy HTML and non-HTML line endings are covered by regressions. Independent review converged
after the evidence corrections above. Final verification: **2,064 passed, two expected local-corpus skips,
492.36 seconds**; Ruff, whitespace, dictionary validation and generated-publication checks passed.
The parent also ran 179 current-document/intake checks; the reviewer independently passed 26 intake/fetch
checks and read the entire golden diff. The fresh CLI scrape reproduced all reviewed candidate forms.

### Slice 3: fixed-label measurement and training preparation

An independent reviewer curated expressions from source/target texts before inspecting outputs or dictionary
entries. The full Goldilocks source is the correct pairing. Strict adjudication excluded little-sheila for a
child, another-crack for national rebirth and the loose bugger-all contribution paraphrase. The frozen set
has 32 unique expressions and explicit wrong-sense/invented-event exclusions. Its first baseline is 6/10
Gettysburg and 10/22 Goldilocks-full, over ten fixed seeds. This is wording reproduction, not semantic/event
fidelity; raw occurrence counts are unaligned. No arbitrary threshold or output-driven label tuning is added.

Model preflight reproduced a separate legacy trainer leak: `clean('quit !of ^end@4')` returned `quit ^end`.
Binding recipe slots before shared `strip_markup` removes annotations without deleting the recipe's
pronouns. This prerequisite is committed before any training run; the recipe and existing quality gates
remain unchanged. Historical model reports and benchmark evidence are not rewritten.

Independent review found no remaining findings and reproduced all frozen baseline counts and output hashes.
The 21 benchmark/trainer regressions also pass on Python 3.10. Final verification: **2,080 passed, two
expected local-corpus skips, 554.42 seconds**; Ruff, whitespace and generated-publication checks passed.
