# Maintenance follow-through, 17 October 2026

Authorised after contextual imagery commit `50a84f0`. Work is on `dev`; each implementation slice receives
an independent software-design review, Ruff and the complete pytest suite before commit. Clear fixes proceed;
material product tradeoffs are flagged for shaping while independent work continues.

| Slice | Scope | Status |
|---|---|---|
| 1 | Grammar and senses: modal clauses/questions, deliberative shall, restless tossing, object-taking quit, evidentiary establish, wholehearted devotion | Complete |
| 2 | Seed-listicle intake: acquire through existing pipeline, verify senses, reconcile coverage and retain decisions | Complete |
| 3 | Curated slang benchmark with independent review, fixed labels and an honest baseline | Complete |
| 4 | Prose refinement: assess technical/instruction/body voice and fix clear defects while preserving configured flavour | Complete |
| 5 | Bundled-model maintenance: inspect training environment, retrain on final data and enforce existing quality gates | Complete: fresh trial rejected at 31/33; shipped 1.2.0 retained |
| 6 | Pre-launch integration: exercise available client/API paths, measure actual routing/latency, document verified limits | Available-interface checks complete; website/live provider checks remain external |

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
in an isolated Python 3.12 environment. No live API key was present in the captured process. The user confirmed
the website had not been built and named its planned repository `underware-gg/aussiefy-web`. They subsequently
provisionally selected `aussiefy.au`; package support is now being handled by the website agent in a separate
worktree. Available engine/toolkit interfaces are verified below; website routing/browser latency needs the
application. Domain research and a provisional choice do not authorise purchase or deployment.

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

Committed and pushed as `2028a88`.

### Slice 4: bounded prose refinement

The opt-in `unless_question` phonetic guard uses canonical sentence spans, including Mr./U.S. abbreviations,
only after rule-policy eligibility. It prevents bloody-well from splitting a negative question's auxiliary
and subject. Standalone non-question statements and imperatives, other grammatical question infixes,
protected spans and later occurrence rolls retain their existing behaviour. A mixed quoted unit containing
statements and questions can conservatively lose this infix throughout. No new product dial is added.

`Dictionary.plain_words` no longer fabricates lower-case evidence from case-folded capital-only patterns.
Raw lower-case spellings and inflections from lower-case source patterns remain available. Existing POS,
name and command guards remain; the prefix policy declines uncertain Australian/English placement without
blocking ordinary Work. The first full run exposed that regression in the original broad guard: **2,111
passed, two skipped, one failed, 718.70 seconds**. The guard was replaced with the owner correction before
the required complete rerun.

The original three-case [probes](prose-probes.json) use the unchanged publication settings and retain both
outputs. Technical code, names, numeric bounds and the instruction's prohibition/condition remain intact;
the technical case fixes the lowered Australian. The instruction remains deliberately restrained, while
the body keeps its tired/delighted slang and conversational garnish. These are bounded manual readbacks,
not an independent quality score or a general claim that every source can be flavoured equally.

Independent review found a continued-dialogue punctuation defect and a measured quadratic question-span
scan. Both are corrected, with curly-closer regressions and binary-search span lookup. The full golden diff
was read, including corrected Emperor questions and continued Bible/Little Red Riding Hood speech. The
reviewer independently passed the initial 96 focused checks; the final owner correction receives additional
inventory, Markdown-composition, lint/contract and harvest coverage: 196 document/composition/POS/contracts
and 102 harness/reliability/harvest checks pass. The 103 document/composition checks also pass on Python 3.10.
Final independent review passed 205 document/composition/harness/reliability/harvest checks with no remaining
findings. Complete rerun: **2,114 passed, two expected local-corpus skips, 581.91 seconds**; Ruff, whitespace
and generated-publication checks passed.

Committed and pushed as `328d8d1`.

### Slice 5: model maintenance and reproducibility prerequisite

The [first current trial](model-maintenance.md) passed 30/33 required checks, failing on a great war,
a top bloke and honest, and was not exported. The shipped 1.2.0 still passes 33/33 against the current dictionary. All
reference requirements, recipe settings and cut-offs remain. Actual lookup diagnostics use the shared
toolkit; the isolated candidate adapter is not presented as package-reader parity.

An offline-cache metadata interruption reused the already saved evaluation fit without changing its ten
artifacts. Further audit reproduced a real WordNet order defect: relation-pointer sets changed positive
pair selection across process hash salts. The first trial retains that limitation, including differing
evaluation/static pair counts. Sorting neighbours before truncation now stabilises every ordered pair
digest at both splits while preserving sense and lemma priority. A fresh evaluation and full fit must follow
the corrected trainer's commit. The 13 trainer tests pass on Python 3.10 and the primary environment.

Historical gap queries now include covered words. Current raw scores are explicitly historical diagnostics,
not current unseen-generalisation/false-fill claims; no invented 90% model-promotion gate is applied. Training
documentation qualifies historical timing and byte-reproduction observations. Meaning-specific training and
a refreshed unknown-word cohort/source-exclusion contract are flagged for shaping.

The independent six-concern review converged with no remaining findings. Final pre-commit verification:
**2,116 passed, two expected local-corpus skips, 516.67 seconds**; Ruff, whitespace and generated-publication
checks passed. The 13 trainer regressions also pass on Python 3.10. Only the neighbour-order correction and
its evidence are accepted here; a fresh evaluation and full-data trial follow this prerequisite commit.

The prerequisite was committed and pushed as `72015dc`. Both fresh fits then ran from clean inputs, with
all six pair streams independently matched to the ordering evidence. The evaluation candidate passes
28/33 references; the full candidate passes 31/33 and fails girl and a good mate of mine. The canonical
release gate rejects it before export. Shipped 1.2.0 is independently rechecked at 33/33 and remains intact.
[Fresh trial evidence](model-trial-deterministic.json) retains both fits, calibration, complete reference
decisions and eighteen actual lookup comparisons per model. Gains on some queries coexist with misleading
alternatives; model-level reference fixes are not substituted for actual toolkit observations.

Slice 5 is complete as a measured maintenance decision, with the current model retained. Meaning-specific
training and a refreshed unknown-word cohort need shaping before another recipe experiment. Slice 6's
available interfaces are verified; website routing, deployed/browser latency, live-provider execution and
actual external-client MCP registration remain follow-ups for those integrations.

Final independent review reproduces candidate 31/33 and shipped 33/33, both fit hashes and all 36 lookup
projections, with no remaining findings across the six concerns. Closing pre-commit verification:
**2,116 passed, two expected local-corpus skips, 627.03 seconds**; Ruff, whitespace and generated-publication
checks passed. The final change records evidence and the decision to retain 1.2.0; no package model or gate changes.

### Slice 6: available interfaces

The [18 October continuation](../maintenance-2026-10-18/README.md) verifies the newly integrated W10/W3
package as a built wheel through stdio, restricted HTTP/ASGI and the changes Python API, including browser
Unicode offsets and measured changes overhead. Website service/browser work and live external clients remain.

[Integration evidence](integration-checks.md) retains the original capture plus a final recheck against
committed runtime `328d8d1`: all six real stdio tools, matching resolved profiles, exact code/name/number
preservation, CLI lint/verification/checked submission and an explicit missing-key deterministic fallback.
The actual Codex drafting workflow kept the source's facts and all three fitting planned phrases. All
eight runtime-input digests match the committed implementation.

This verifies an editable installed checkout from outside the repo. Live provider execution, separate
agent-client MCP registration and the planned website's routes, Smart/Basic mapping and browser/deployed API
latency remain unverified. Prior core timings are linked, without substituting them for future web timing.
