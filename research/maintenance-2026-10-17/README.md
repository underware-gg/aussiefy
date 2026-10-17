# Maintenance follow-through, 17 October 2026

Authorised after contextual imagery commit `50a84f0`. Work is on `dev`; each implementation slice receives
an independent software-design review, Ruff and the complete pytest suite before commit. Clear fixes proceed;
material product tradeoffs are flagged for shaping while independent work continues.

| Slice | Scope | Status |
|---|---|---|
| 1 | Grammar and senses: modal clauses/questions, deliberative shall, restless tossing, object-taking quit, evidentiary establish, wholehearted devotion | Complete |
| 2 | Seed-listicle intake: acquire through existing pipeline, verify senses, reconcile coverage and retain decisions | Pending |
| 3 | Curated slang benchmark with independent review, fixed labels and an honest baseline | Pending |
| 4 | Prose refinement: assess technical/instruction/body voice and fix clear defects while preserving configured flavour | Pending |
| 5 | Bundled-model maintenance: inspect training environment, retrain on final data and enforce existing quality gates | Pending |
| 6 | Pre-launch integration: exercise available client/API and local website paths, measure actual routing/latency, document verified limits | Pending website source location |

## Decisions and verification

No product decision is pending at the outset. Model promotion remains conditional on existing reference and
calibration gates. New benchmark labels must be chosen for meaning, not to produce a desired passing score.
The website and live client are separate integration surfaces; core timing does not establish end-to-end latency.

### Slice 1: grammar and senses

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
the website is not live; its planned address is `aussiefy.underware.gg`, and its source location is requested
for local integration checks. Standalone domain options are being researched for shaping; no purchase or
deployment is authorised by that research request.
