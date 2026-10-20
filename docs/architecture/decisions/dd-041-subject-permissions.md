# DD-041: Resolve reviewed subject permissions once

Status: accepted
Date: 2026-10-21
Extends: DD-005, DD-026, DD-040

## Context

Swear strength does not describe subject matter: a drinking-game reference can be clean, while a swear
can function as an intensifier without introducing sex or toilet humour. The approved community dictionary
design specifies nine reviewed themes, four default permission sets and exact caller overrides.

## Decision

Store tier defaults in `themes.yaml`, validating all four tiers and all nine booleans. Resolve a frozen
permitted set with the caller's exact `document_config.themes` overrides in `policy.resolve`. General,
Custom and named types use the same eligibility rule; an empty map inherits rather than disables it.
Every tagged expression requires every tag permitted. Swear-cap probes explicitly retain the original
permissions. Strict Markdown shares the resolved Effective value across its units.

Apply the same predicate to substitutions, garnish, entry riffs and contextual images, including lookup,
plans and change cards. `include_gated`, misreading unlocks and embellishment cannot bypass subject policy.
Report all nine booleans as `theme_permissions`; briefs receive the same values as `THEME_PERMISSIONS`.
Constructor ingredients and composites will use this same policy when their planned slice lands.

Tags describe literal subjects or concrete imagery, not an automatic scan of swear substrings or historical
etymology. For example, alcohol containers and drinking sessions carry drinking, a pub raffle carries gambling,
explicit genital imagery carries sex, and a toilet comparison carries bodily functions. Generic insults and
bleached intensifiers do not acquire a sex tag solely from their origins. Water drinking is not alcohol.
Mixed food/drink, exhaustion/drink and drug/drink records become separate senses. Historical ids retain
alcohol senses; the new ids name the non-alcohol senses, preserving existing explicit references. The ANDC
supports both food and alcohol meanings of full as a goog; the earlier unsupported 1927 claim is removed.

Put the shared known-form acceptance check in the core's pure `semantic_checks` module. Lint, verification,
checked agent submissions, sentence hooks and surface models share it. Source occurrences remain allowed
by folded wording and count; longer known expressions own nested words in both source and output, so
have a crack cannot donate a source allowance for an introduced drug expression. Multiple readings at
one span remain unresolved when any reading is permitted or literal. The check covers compiled entry forms
and fixed colour, and deliberately makes no claim to arbitrary topic recognition or all slotted images.

Model prompts and sentence cache identities include the resolved permissions. Fresh and cached replies
use the same acceptance rule. Existing strict-signature sentence hooks are real consumers, so retain their
minimum protocol; use signature capability inspection to pass the new keyword only to hooks accepting it
or arbitrary keywords. All outputs are checked regardless. No TypeError catch-and-retry is used.

New blind-judge snapshots record the complete resolved theme map separately from document behaviours.
Older protocol-2 snapshots remain readable with no theme map; their unrecorded policy is never reconstructed
from current tier defaults. All nine exact booleans are required when a map is present.

## Consequences

Subject permissions compose with level, swearing, meaning and document settings. They prevent new chosen
expressions without removing topics already present in the source. Known-word checks remain bounded and
conservative around ambiguity. Theme tags need curatorial review as vocabulary grows; future constructors
must carry the permissions into generation rather than relying on the post-check as a substitute.

## Verification

Focused tests isolate defaults, immutable exact overrides, all-tag requirements, malformed data, every
selection surface, higher-cap probes, markup routing, source preservation, overlap ownership, strict hook
compatibility, and fresh/cached model rejection. Full-suite and publication results are recorded in the
slice report after the final checks.
