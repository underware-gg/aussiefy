# Semantic engine refinement

User direction: improve the existing engine's shared grammatical and semantic interpretation, including
tone, without coupling this work to the separate community-dictionary design. No communication with the
external agent is authorised. Internal research agents continue the source audit separately.

## Completed foundation

Commit `2687d7f` shares clause reading, polarity, nominal arguments and complement restrictions between
translation and contextual imagery. Tone/mood weighting also reaches planner suggestions, and document
mood survives strict Markdown segmentation. Concept restrictions survive research-round replay. The
pure-Python YAML loader reads the complete bundled dictionary.

That slice passed independent review, Ruff, generated-documentation, provenance and whitespace checks,
and the complete suite: 2,403 passed, two expected local-corpus skips (793.25 seconds).

## Completed lexical and argument slice

The current changes distinguish activity starts, rough assembly, comradeship, political people, driving
roles, sleeping accommodation and other reviewed senses. Source additions from the earlier 30- and
60-entry ledgers cover 85 entry records and 110 new URLs. Requested cultural references and conditional
appetite phrases are implemented, with writer suggestions for constructions needing judgement.

Shared argument reading distinguishes bounded temporal/prepositional adjuncts from unanchored objects.
It retains quantified noun objects, nominal compounds, gerunds, temporal subjects and anchored arguments.
It does not claim a complete parser: location-adverb ambiguity and gerund/preposition boundaries remain
explicit follow-ups.

Independent design review has converged. Focused regressions and generated artefact readback passed.
The complete final run passed 2,522 tests with two expected local-corpus skips (775.08 seconds); Ruff,
generated-document freshness, provenance/licensing and whitespace checks also passed.
See [integration scope](meaning-integration.md) and the
[review](../../docs/architecture/reviews/design-review-2026-10-19-meaning-extensions.md).

## Remaining slices

1. Integrate the independently reviewed narrator-opinion setting and entry annotations. Existing
   embellishment profiles resolve its default, with exact advanced overrides; role/reference preservation
   remains independent of permission to add opinion. Translation, lookup, plans, change alternatives,
   garnish and known-term writer checks share the resolved permission. Full integrated verification remains.
2. Apply clear source-derived meaning corrections from batches 3 and 4, with source additions and regression
   tests. The isolated implementation preserves species, construction, quantity, contact chains, location
   nouns, solitude versus loneliness, scolding versus shouting, and comparative versus absolute indifference.
   Reconcile later batch 5/6 recommendations against those changes rather than applying duplicate fixes.
3. Finish explicit listener-role binding. Use the existing object-possessive slot and shared argument
   retention to prevent a missing listener becoming the speaker; add standard bend/bent morphology.
   Independent review and full integrated verification remain.
4. Continue the source audit across the original inventory, cross-review each allocation, then integrate
   clear supported corrections separately from provisional evidence and intentional stylistic policies.
   The completed, cross-reviewed batches through 6 cover 700 of 1,254 original entries, leaving 554.
   Batches 7 and 8 are in progress. The later source candidates and recommendations are not yet
   runtime changes.

## Verification and scope

Each implementation slice needs meaningful positive/negative tests, generated corpus and change-fixture
readback where affected, public-document freshness, independent design review with findings resolved,
Ruff, the complete suite and provenance checks before commit and push to `dev`. No release promotion is
part of this task. Research coverage counts original-baseline IDs, not later additions, and does not certify
all triggers, constructions, frequency or origin claims.

The separate constructor, theme and attestation-metadata design remains external to this implementation.
Ordinary source research and clear dictionary fixes do not depend on completing that design. Prefer
existing shared context, form compatibility and dictionary concepts to slang-specific engine branches.
