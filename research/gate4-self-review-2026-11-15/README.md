# Gate 4 self-review and quiz batching — 15 November 2026

V4 was frozen and pushed at b2466bb596bf0271d4217f52405851d4f8e1c966. This follow-through optimises quiz
discovery, adds acceptance witnesses and records the remaining coordination/curation gaps. **Gate 4 is
not cleared:** Rob owns acceptance, and the acceptance matrix explicitly retains H25, H26 and R64.
No stored spelling, permanent ID, profanity tier, theme, source weight or evidence fact changed.

## Quiz cost and behaviour

One request-local adaptive lookup batch replaces four-to-seven full response/card lookups. It shares
ordinary lookup's scoring, grammar, phrase protections, top-50 limit and permissions, with an ID-only
projection. Adaptive forward/reverse exclusions still score several glosses; “one batch” does not mean
one semantic query. Similarity ranks difficulty, never certifies a wrong answer. The public Python,
CLI and MCP request/response shapes are unchanged.

The fixed trigram index is cached by actual immutable spelling content, with at most four corpora;
query answers stay request-local. Form facts have a separate bounded 4,096-key cache. In-memory derived
dictionaries can retain dictionary_id, so that ID is deliberately not the index cache key.

`quiz-benchmark.json` records 40 warm serial paired questions, ten seeds at each vulgarity, alternating
before/after order on the same current dictionary and bundled model. Every full response is identical.
The baseline is the frozen commit above. The receipt records mean/median/max timings and response
hashes; it excludes dictionary/model/index cold setup and is not a hosted-service charging decision.
Reproduce: `.venv/bin/python research/gate4-self-review-2026-11-15/benchmark_quiz.py --baseline-ref
b2466bb596bf0271d4217f52405851d4f8e1c966 --out /tmp/quiz-benchmark.json` (one shell line).

## Acceptance evidence and calibration

`acceptance-matrix.md` maps all 35 engine acceptance bullets, plus ED15, R64, EW4, EW9 and the quiz,
to real test functions. All named test functions were checked against the source AST. Named arvo/esky,
root/general/omit, unknown-selection and fanciful-held controls now have direct witnesses. The held
observer property compares 36 seeded translation/changes requests; it does not claim arbitrary source
insertions preserve sentence-keyed choices.

`plain-example-audit.json` renders every authored concept example: **42 of 45** render safely. The three
unresolved scopes preserve source; the audit explicitly says all_examples_meet_R64=false. Shared guards
reject unsafe display-noun replacement of a consumed be predicate, and sentence wording that changes
an unambiguous required source modal. RESTLESS_SLEEP gains a provisional clause form using existing
subject/be captures. No fake duplicate plain option or Tradie form closes these gaps.

`level-reconciliation.json` covers all 1,286 status=active entries: 1,264 baseline grades remain identical,
and 22 later entries have individual retention rationales. Three have recorded numeric-grade approval;
nineteen remain provisional retention recommendations. The eight manually gated entries are outside
that active cohort; their gates and current grades are untouched. Testimony for use does not approve
a numeric grade. The historical 1,265-row ledger and hero/golden receipt are unchanged.

`calibration-recheck.json` reproduces all 1,409 stored-term score rows, weights and 333 weight-only label
promotions from the 14 November archive. All 1,409 entries/riffs/images have searched records. Labels
remain 447 attested / 942 unverified / 20 bulldust, versus 114 / 1,275 / 20 under the old weights. This is
source-based curator calibration, not independent labelled accuracy, frequency, origin or first-use proof.
The archive is preserved rather than rewritten to acquire the new dictionary identity.

## Historical review closure

The 21 October slice0–1 and 22 October slice0–2 findings were read alongside the current designs and
recorded corrective reviews. Current witnesses close the executable findings below. This is recorded
resolution plus fresh targeted checks, not a claim that every historical reviewer script was re-run.

| Finding | Current witness / disposition |
|---|---|
| ED7 riff/imagery weights | test_attestation and test_themes weighting witnesses; shared metadata weighting. |
| Individual tags, duck/dingo, style notice | test_dictionary_conformance::test_re_review_records_individual_readings_and_applied_tiers; 145 individual records; contributor/test_publish_docs::test_notice_names_the_publication_settings. Seven separately recorded semantic deferrals remain below. |
| Source subject preservation | test_themes::test_real_source_subjects_survive_restricted_translations across four surfaces. |
| Score/testimony/caught-on/forged-label tests | test_attestation boundary, live-summary, independence and specific derived-field errors. |
| Unknown-reading misuse and unexplained holds | Narrow reads_as schema; properly-adv gate and know-a-bloke/never-have-picked-it reasons remain explicit. |
| Possessive profanity | test_dictionary_conformance::test_possessive_compounds_obey_constructor_and_mask_caps. |
| Spaced apostrophe construction ending | test_dictionary_conformance::test_reviewed_composites_share_lint_and_rewriter_theme_policy. |
| Multiplicative variant weights | test_dictionary_conformance::test_variant_preference_survives_composition_and_garnish_weighting; fresh independent 2×3 part-weight witness gives ×6. |
| Opener invention and labels | test_dictionary_conformance::test_reviewed_constructed_openers_obey_invention plus actual labelled construction emission. |
| Forged riff error and uniform themes | test_attestation::test_stored_evidence_labels_are_rejected_everywhere; test_changes_v3_draft::test_theme_shape_is_uniform_throughout_cards_and_projections. |
| Stem reuse and plan/explain IDs | test_dictionary_conformance::test_stem_reuse_and_construction_identity_survive_translation_and_plans. |
| ELU kind | Current sources checked as crowd_dictionary; test_gate4_acceptance::test_elu_construction_stem_sources_keep_their_crowd_kind adds a direct control. |
| EW4 and calibrated weights | Current calibration recheck above and existing reviewed-anchor score tests. |

Separate semantic deferrals retained by the tag ledger are a-blue, cark-it, carked-it, give-a-hiding,
kick-arse, perv-on and put-the-boot-in. Their conservative mixed-sense treatment is not a completed sense
split. Other independent historic curation opportunities do not silently become completed work.

## What Rob still decides

See acceptance-matrix.md for the exact H25/DD-003 conflict, the three source-preserved R64 scopes and
the three Tradie English omissions. “Rulings for Rob” retains plural cunts, the Tradie forms and the
source-only prize-pig FULL candidate, all unapplied, alongside reversible curation recommendations.
No staging, main, tag, release or deployment is part of this checkpoint.


A final source-replay stress check found one existing connective pin discarded by an automatic casing
heuristic after restoring “Calm down”. The bounded fix exempts explicit eligible pins from that automatic
confidence check, preserving all hard gates, exact source casing and strict unused-pin validation.
`tests/functional/test_plain_source_replay.py` checks all 29 offered substitution source choices across
the real fixtures, exact whole edits and complete recapture. Personal choices remain deliberately unshared.
