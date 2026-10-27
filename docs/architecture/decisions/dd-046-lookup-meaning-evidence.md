# DD-046: Lookup respects established meaning evidence

Status: Accepted
Date: 2026-10-25
Extends: [DD-044](dd-044-phrase-interpretation-context.md), [DD-045](dd-045-explicit-dictionary-exploration.md)

## Context

The web review found that lookup offered unrelated model matches for examples which translation correctly
held as meanings without an Aussie word. Exact plain wording was not recognised consistently, and raw
imagery triggers could restore a sense the interpretation stage had ruled out. A no-result policy check
could then report `nothing_fits` even though the recognised meaning had no word at any dial setting.

## Decision

Translation and lookup use `detect.read_meanings` to resolve contextual readings. It retains contradicted
person-only senses for lookup to rule out rather than confusing them with unknown meanings. Translation's
fallback controls and lookup's fragment support remain explicit caller options. Lookup imagery reads the
same resolved detections rather than independently pooling raw triggers.

An exact match on authored `plain` wording or a concept's name is also evidence for explicit meaning
discovery. Names accept the ID or its words (`ACCEPT_AS_TRUE` or `accept as true`). Matching uses the
existing case, apostrophe and whitespace folding, not spelling similarity. These names and plain wording
do not become translation triggers, and no phrase-specific lookup override is introduced.

A recognised wordless meaning returns `no_word_yet` ahead of model guesses and dial-rejected entries.
Its `meanings` identify what was recognised. The engine does not ask the model for unrelated alternatives
to that established meaning. Model discovery remains available for queries whose meaning is unsettled.
This follows the source-evidence boundary rather than adding another ranking preference.

Context objects remain independently discoverable. For example, `believe a liar` has a wordless testimony
reading but still offers the object's `a bullshitter`; already-Aussie object wording such as `my mate`
can be explained too. The object's frame-checked dictionary forms supply discovery evidence within its
own context extent; they do not assert an automatic translation sense or restore candidates for the held
verb. These results retain all dial and metadata checks. A `no_word_yet` response may therefore include
results for an independently understood part, while still naming the missing meaning separately.
CLI text and JSON retain that primary outcome and exit 1 for `no_word_yet`, even with object offers.

Guard outcomes and the later card/match-kind contract are unchanged. Open curatorial rulings are not
settled by this mechanism change.

## Verification and consequences

Every listed wordless meaning's plain wording and reviewed examples must look up as that meaning using
both lookup backends and low/high dial settings. Separate controls preserve independent object offers,
negation and unknown-query model fallback. Translation output and its seeded choices are unchanged.

Exact authored wording and names are cached per dictionary. Wordless queries can return without model
scoring. Adding a corresponding entry removes a meaning from the waiting set through the existing
dictionary-derived coverage rule; policy-blocked existing words still report `nothing_fits`.
