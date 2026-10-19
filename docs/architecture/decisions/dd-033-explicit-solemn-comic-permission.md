# DD-033: Explicit permission for comic terms in solemn text

Status: Accepted; implementation verification in progress.
Date: 19 October 2026.
Extends: [DD-019](dd-019-explicit-composable-document-policy.md),
[DD-030](dd-030-shared-semantic-context.md).

## Context

The engine reads mood independently of document type. Comic substitutions previously had an unconditional
ban in solemn text, even when all configured behaviours allowed them. This conflicted with the direction
that automatic detection feeds controllable settings. Tone also affects images, garnish and closings;
those mechanisms have their own existing preferences and constraints.

## Decision

Expose `solemn_comic_terms` through the existing advanced document configuration and resolved embellishment
settings. The user approved enabling it at Troppo for deliberate comic performance. Deadset, Dinkum
and Custom keep it off; Custom stays opt-in even with the Troppo embellishment label. An explicit boolean
wins for every document type and embellishment setting.

The permission affects the shared substitution eligibility check, so deterministic output, plans and
change alternatives agree. Enabling it does not change detected mood, permit unsupported meanings or
arguments, enable garnish, or lift vulgarity and other policy restrictions. It does not alter the existing
image weighting and closing rules. Dictionary lookup without a source passage remains discovery.

## Consequences

Callers can deliberately permit a comic death idiom in a solemn passage without enabling unrelated
embellishments. Result envelopes report the effective permission. The historical Gettysburg gate keeps
its frozen inputs and threshold; the approved preset applies consistently to every source passage.

Other tone-driven decisions remain visible follow-ups for advanced configurability. This setting only
names the demonstrated unconditional substitution restriction rather than introducing a broad tone bypass.
