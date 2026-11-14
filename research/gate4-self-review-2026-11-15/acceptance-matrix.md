# Gate 4 acceptance evidence — 15 November 2026

This is a self-review against the current Brain engine/community designs and build plan, not Rob's
acceptance. H1–H35 follow the engine design's 35 “How we'll know it works” bullets in order. Test paths
below are under tests/functional unless stated. The checkpoint report in the Brain holds final full-suite
and push receipts. Passing a gap detector does not mean the underlying acceptance gap is closed.

Reviewed design revisions:

- Engine: d58696015186a34332193afc1f0a218cdb287f3ab72ef6ea8ea5b6bed5c25312.
- Community: 06b0b189e5ab3ee873a00c7fa6aa4765807df4e33b9f81f33c83012abe06f394.
- Build: 97fe9702431d5b31b4f144acd8d96c849bcb282e130e67d84a3562d2f2794354.
- Package brief: 0b415af9e3ee2686b0c4a12bfcbeb91bd95d7cdacaf896c5a990366d4e009473.

| Item / slice | Acceptance witness | Status and scope |
|---|---|---|
| H1 / 2+6 | `test_runtime_v3.py::test_real_emitter_graphs_and_exact_replay`; `test_constructions.py::test_seeded_results_keep_part_evidence_and_credit_without_borrowing_whole_sources` | Dictionary words/parts carry provenance. Personal, literal, held and rule changes intentionally have no invented evidence under reviewed v4. |
| H2 / 0 | `test_attestation.py::test_hand_checked_score_goldens`; `test_calibrated_attestation.py::test_reviewed_evidence_anchors_cross_the_existing_four_bar_boundary` | Fixed score/label goldens run against current weights. |
| H3 / 0+5 | `test_attestation.py::test_metadata_boundary_invariants`; `test_attestation.py::test_loader_rejects_forged_derived_label_and_retired_imagery_origin`; `test_dictionary_extensions.py::test_extension_boundaries_fail_with_schema_errors`; `test_dictionary_extensions.py::test_invalid_adjustments_are_refused` | Loader boundaries, constructor/source constraints, credit, testimony, stale IDs and invalid adjustments. |
| H4 / 0 | `test_attestation.py::test_live_summary_replaces_export_and_changes_agent_label` | Live testimony changes score/label without mutating stored summary. |
| H5 / 0 | `test_attestation.py::test_testimony_cap_spoken_use_and_geographic_spread`; `test_calibrated_attestation.py::test_crowd_volume_and_testimony_alone_do_not_become_attested` | Testimony ceiling and spoken-use crossing. |
| H6 / 0+6 | `test_attestation.py::test_general_is_a_weight_not_an_eligibility_gate`; `test_attestation.py::test_general_word_remains_an_editor_alternative`; `test_adjusted_selection.py::test_a_strong_preference_can_outweigh_general_english_penalty` | General words remain eligible, less frequent and overridable. |
| H7 / 4 | `test_exploration.py::test_discovery_marks_holds_and_never_returns_omitted_entries` | Held-back reasons and omissions. |
| H8 / 2+6 | `test_changes_v3_draft.py::test_all_imagery_and_sampled_construction_families_use_the_shared_card_contract`; `test_runtime_v3.py::test_real_emitter_graphs_and_exact_replay` | All-card checks plus actual emitted imagery, not only archived draft examples. |
| H9 / 6 | `test_dictionary_extensions.py::test_adjustments_are_exact_scoped_bounded_and_do_not_change_evidence`; `test_adjusted_selection.py::test_adjustments_change_seeded_picks_without_changing_rolls_or_eligibility` | Contextual bands and preserved evidence/eligibility. |
| H10 / 5 | `test_dictionary_extensions.py::test_namespaced_entries_and_entryless_context_meanings_load`; `test_dictionary_extensions.py::test_extension_boundaries_fail_with_schema_errors` | Qualified IDs cannot collide. |
| H11 / 1 | `test_themes.py::test_overrides_are_independent_of_cap_and_document_type`; `test_themes.py::test_lookup_and_locked_probes_cannot_unlock_forbidden_subjects` | Themes independent of profanity caps. |
| H12 / 1+2+6 | `test_themes.py::test_term_tiers_and_exact_theme_overrides_share_one_policy`; `test_constructions.py::test_part_tiers_survive_weaker_family_and_exact_override`; `test_changes_v3_draft.py::test_theme_shape_is_uniform_throughout_cards_and_projections` | Graded tags, exact overrides, composite maxima and uniform cards. |
| H13 / 5+6 | `test_dictionary_extensions.py::test_identity_follows_content_and_order_not_paths_or_modified_times`; `test_adjusted_selection.py::test_tuning_is_deterministic_and_never_leaks_to_later_calls` | Identity changes with content; repeatable requests and relevant output-change witnesses. Unrelated data edits need not change every output. |
| H14 / 6 | `test_adjusted_selection.py::test_popularity_uses_its_wider_band_without_changing_evidence_or_rolls`; `test_adjusted_selection.py::test_known_but_ineligible_preference_neither_grants_access_nor_falls_back`; `test_adjusted_selection.py::test_markdown_units_share_the_runtime_and_public_tuning_report` | Personal/popularity bands, permissions and tuning envelopes. |
| H15 / 6 | `test_adjusted_selection.py::test_invalid_preference_weights_fail_even_for_unknown_records`; `test_adjusted_selection.py::test_unknown_matches_and_terms_warn_without_hiding_valid_preferences` | Weight validation and warnings. |
| H16 / 6 | `test_match_keys.py::test_emitted_identity_is_a_known_dictionary_match`; `test_match_keys.py::test_qualifier_keeps_the_same_root`; `test_adjusted_selection.py::test_exact_key_beats_a_more_recent_preference_at_another_degree`; `test_adjusted_selection.py::test_a_root_adjustment_does_not_apply_to_a_qualified_key` | Match grammar/root/degree and exact/root precedence. |
| H17 / 4 | `test_exploration.py::test_no_match_codes_preserve_meaning_and_direct_term_recognition`; `test_lookup_contract.py::test_discovery_outcomes_and_dictionary_identity_are_shared` | Coded no-match outcomes. |
| H18 / 2+3 | `test_invention_runtime.py::test_curated_candidates_and_failed_rolls_never_try_construction`; `test_invention_runtime.py::test_constructions_respect_dependent_results_and_frames`; `test_constructions.py::test_sampling_is_bounded_and_collisions_cover_dictionary_forms` | Invention timing, grammar and bounded collisions. |
| H19 / 1+3 | `test_themes.py::test_riffs_cards_and_agent_plan_reuse_the_same_permissions`; `test_themes.py::test_imagery_uses_the_same_permission_for_insertion_lookup_and_plans`; `test_themes.py::test_real_source_subjects_survive_restricted_translations` | Shared permissions and retained source subject matter. |
| H20 / 5 | `test_dictionary_extensions.py::test_promoted_aliases_keep_credit_and_refuse_stale_exports`; `test_dictionary_extensions.py::test_malformed_promotion_is_a_schema_error_not_an_indexing_error` | Promotion and stale-export boundaries. |
| H21 / 5 | `test_source_urls.py::test_invalid_source_shapes_raise_a_user_error`; `test_source_urls.py::test_public_shapes_are_preserved_without_any_io` | Package URL mechanism covered. The site's call to it is site-owned evidence. |
| H22 / 6 | `test_runtime_v3.py::test_host_preferences_hook_uses_resolved_dials_once_and_is_never_a_client_argument`; `test_runtime_v3.py::test_hosted_clients_cannot_supply_preferences_or_hidden_popularity` | Hosted capability and host-only preferences. |
| H23 / 4 | `test_exploration.py::test_names_are_seeded_clean_and_cover_the_three_reviewed_shapes`; `test_exploration.py::test_names_never_use_known_garnish_insults_or_themed_literal_parts` | Seeded clean names. |
| H24 / 7 | `test_gate4_acceptance.py::test_arvo_and_esky_are_kept_at_every_level_without_a_substitution_roll`; `test_gate4_acceptance.py::test_general_omitted_and_literal_root_are_not_source_markers`; `test_v4_runtime.py::test_source_swears_are_kept_exact_and_unmasked_at_nan`; `test_owned_readings.py::test_dial_eligibility_does_not_erase_a_source_owned_term` | Direct all-level and negative controls added; source cap/rate/status behaviour. |
| H25 / 7 | `test_v4_runtime.py::test_source_marking_does_not_spend_usage_or_shift_another_roll` | **OPEN clarification.** Test covers recognition/reporting on identical source; literal insertion invariance conflicts with DD-003. Do not call that narrower witness full satisfaction. |
| H26 / 7 | `test_v4_runtime.py::test_plain_choices_preserve_bound_people_tense_and_degree`; `test_v4_runtime.py::test_ambiguous_australian_forms_keep_all_supported_senses`; `test_v4_freeze.py::test_null_target_replays_and_recaptures_the_exact_plain_source`; `test_plain_source_replay.py::test_all_real_fixture_plain_source_choices_replay_exactly_with_existing_garnish`; `test_gate4_acceptance.py::test_every_concept_example_has_an_explicit_rendering_audit_and_known_gaps_are_not_called_complete` | **OPEN** for three held Tradie English forms and the R64 scopes below. Ordinary safe choices and literal replay covered. |
| H27 / 7 | `test_v4_runtime.py::test_selection_distinguishes_passed_over_kept_and_wordless`; `test_gate4_acceptance.py::test_unknown_unchanged_selection_has_the_no_dictionary_code`; `test_v4_freeze.py::test_mixed_selection_explains_each_group_at_its_own_dials` | Passed-over, unknown, mixed and locked selection states. |
| H28 / 7 | `test_personal_terms.py::test_free_text_rating_and_explicit_tier_are_distinct`; `test_personal_terms.py::test_preparing_personal_terms_cannot_change_dictionary_identity_or_entries`; `test_v4_runtime.py::test_personal_terms_are_literal_request_choices_not_dictionary_entries`; `test_mcp_capabilities.py::test_host_personal_terms_are_hidden_and_resolved_once_per_request`; `test_v4_freeze.py::test_host_can_raise_or_remove_its_own_personal_hook_cap` | Rating, inflection, validation, identity and host controls. |
| H29 / 7 | `test_v4_runtime.py::test_ruled_out_words_are_real_at_spot_options`; `test_gate4_acceptance.py::test_fantastic_dreams_is_held_and_cites_the_excluded_praise_reading`; `test_gate4_acceptance.py::test_observing_held_markers_preserves_unrelated_translation_choices`; `test_exploration.py::test_a_wordless_verb_preserves_its_objects_independent_meaning` | Named fanciful case and 36 seeded observer/non-observer witnesses added; independent object swap retained. |
| H30 / 7 | `test_v4_runtime.py::test_only_wordless_readings_are_held`; `test_v4_runtime.py::test_explicit_ruled_out_pick_preserves_inferred_and_selected_readings`; `test_near_runtime.py::test_exact_word_prevents_near_even_when_the_level_blocks_it` | Inferred/chosen readings and exact-word precedence. Ambiguous kept readings are nullable by reviewed v4. |
| H31 / 4+7 | `test_exploration.py::test_wordless_meanings_page_only_genuine_meanings_with_plain_wording`; `test_ed16_meanings.py::test_approved_meanings_wait_through_their_plain_wording_and_examples` | Current genuine waiting set, including explicitly tested six approved ED16 meanings; do not silently conflate historical cohorts. |
| H32 / 4+7 | `test_exploration.py::test_every_waiting_meaning_round_trips_through_lookup`; `test_exploration.py::test_every_concept_example_reads_as_its_meaning` | Actual waiting names/examples at both dial extremes and two backends. |
| H33 / 7 ED14 | `test_concept_listing.py::test_all_concept_counts_equal_the_public_entry_listing`; `test_concept_listing.py::test_blocked_meanings_stay_at_zero_and_omissions_never_create_rows`; `test_concept_listing.py::test_every_ordinary_meaning_has_a_distinct_reader_name_and_search_words` | Plain names, exclusions and filtered counts. |
| H34 / 6 | `test_lookup_contract.py::test_rich_lookup_cards_match_entry_detail_and_report_default_placement`; `test_lookup_contract.py::test_match_codes_do_not_depend_on_display_text` | Shared rich cards and machine match codes. |
| H35 / 5 | `test_dictionary_extensions.py::test_namespaced_entries_and_entryless_context_meanings_load`; `test_ed16_meanings.py::test_malformed_literal_sequences_are_rejected` | Entryless contextual extension meanings and unknown syntax rejection. |
| R64 / 7 | `test_gate4_acceptance.py::test_every_concept_example_has_an_explicit_rendering_audit_and_known_gaps_are_not_called_complete`; `test_gate4_acceptance.py::test_sentence_wording_preserves_a_required_modal_or_declines` | **OPEN:** 42/45 render safely; three scopes abstain and preserve source. This is exhaustive gap detection, not 45 successful renderings. |
| ED15 / 8 | `test_near_runtime.py`; `test_near_meaning_data.py`; `test_v4_freeze.py::test_near_names_are_authored_on_the_change_and_each_option` | Directed relations, exact-word precedence, genres, graded rolls, Deadset, hard gates, replay and authored near names. |
| EW4/calibration | `test_gate4_acceptance.py::test_current_calibration_and_ew4_records_reproduce_the_source_hunt_receipt`; `test_calibrated_attestation.py` | 1,409 searched terms and exact source-hunt score reproduction; not independently measured accuracy. |
| EW9 | `test_gate4_acceptance.py::test_ew9_current_active_levels_have_individual_review_coverage` | 1,264 active baseline grades unchanged; 22 later grades individually reviewed and retained, 19 provisionally. No grade/theme/tier changed. |
| Quiz | `test_quiz_batch.py`; `test_meaning_quiz.py::test_every_askable_entry_has_safe_distractors_at_each_vulgarity` | One prepared adaptive batch, scalar top-50 equivalence, seeded replies and exhaustive safe distractors. |

## Coordination and acceptance gaps

1. **H25 versus DD-003.** At seed0, level5/Nan/Deadset with no garnish/phonetics/stacking,
   “She is exhausted.” chooses Kerry-Packered (roll0.430288); “She is exhausted, mate.” chooses the oily-rag
   exhaustion form (roll0.063482), with mate kept. Recommendation: retain DD-003 and clarify the same-source
   ownership non-interference requirement. No seeded-key policy change is applied.
2. **H26 Tradie forms.** g-ya-mad-cunt, g-ya-cunt and g-ya-beautiful-cunt still have source-only choices.
   Their three proposed English forms remain held for Rob, as instructed; no fake plain option closes this.
3. **R64 scopes.** HEARTBREAK “Her heart was broken.”, HEART_EFFORT “Her heart wasn't in it.” and DOUBT_IT
   “I doubt it could be done.” need faithful sentence wording with appropriate scope/polarity/modality.
   Frame-only defaults cannot express these safely. Unsafe noun fallbacks and explicit modal changes are
   declined; source is preserved. The missing RESTLESS_SLEEP clause form is repaired provisionally with
   existing subject/be captures. Propose a shared scope-aware sentence-form design, not phrase-specific code.
4. **Separate legacy semantic deferrals.** The tag ledger retains a-blue, cark-it, carked-it, give-a-hiding,
   kick-arse, perv-on and put-the-boot-in for sense separation. Their conservative mixed-sense treatment is
   explicit; do not call those splits completed merely because tags match the ledger.
5. **Rob's curation acceptance.** Existing provisional names/search words, sentence forms and additions,
   plus nineteen later grade retentions, remain recommendations. Plural cunts, the three Tradie forms and
   the source-only prize-pig FULL candidate are unapplied. No spelling or permanent ID changed.

H13 is tested for repeatability, changed identity and relevant-change witnesses; the wording does not
mean an unrelated data edit must alter every output. H21's package validator is verified here; site wiring
needs the site's own checks. Neither qualification changes the engine design silently.
