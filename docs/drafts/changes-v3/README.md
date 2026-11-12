# Changes and cards v3 — review draft 20261112-r2

This replaces r1 for review. It is not a freeze or an active response contract. The packaged
`aussiefy.changes.VERSION` and changes schema remain v2. Consuming clients review this draft before a coordinated
contract upgrade. Host deployment choices belong in the project plan. This bundle contains three
self-contained JSON Schemas, six changes examples and two full-card lookup projections. Illustrative projections do not claim
that the engine already emits v3 or that a constructor passes the fallback rule in the illustrated source.

## Option identity and replay (B1)

The option key is `entry_id ?? construction_id`. Within one change it appears **at most once across the
combined alternatives and locked arrays**. Multiple riffs of the same entry are not separate options:
choose one rendering for that entry in the response. The selected construction's own `construction_id`
must appear in its alternatives. Keys may recur at different changes.

For a fixed `dictionary_id`, a construction's ID persists across requests, seeds, candidate ordering,
tuning and policy. Its existing algorithm is unchanged: compact UTF-8 JSON of
`["construction-expression/v1", family.id, family.template, [[role, ingredient.id, ingredient.text], ...]]`,
with parts in **template rendering order**, SHA-256, first 24 lower-case hex characters; prefix
`construction/<family.id>/`. The dictionary identity qualifies the catalogue and ingredient resolutions.
Changes to wording or template produce a different expression identity. Different dictionary identities
do not promise an expression will still resolve. The shared `construction_identity` function owns this
algorithm; semantic checks reconstruct and verify it rather than trusting an arbitrary well-shaped ID.

**Construction and riff picks do not have a guaranteed untuned replay.** An identical complete request and
dictionary remains deterministic, but removing personal/community tuning is a different request.
Eligibility, variety, prior usage and bounded construction/riff sampling can change the returned pool.
Persistent identity does not guarantee presence in that pool. `riff_index` is response-local, not a share
identifier. A request-side pin/replay input (including a persistent riff selector) is required before
tuned construction/riff share links ship. It remains part of the 3+6 follow-through; this response draft
does not silently introduce that input or promise replay closure.

## Provenance (B2)

`coined_by` names who invented the wording: `person`, `agent` or `constructor`. `produced_by: agent`
records agent production of the stored record; it is not generally a claim that the agent invented the
wording. An explicit `coined_by` always wins. When the evidence assessment is `bulldust`, there is no
explicit coiner, and `produced_by` is `agent`, the v3 projection derives `coined_by: agent`. That assessment
already requires the unsuccessful search and absence of independent attestation; the projection changes
no stored facts, attestation score or evidence label. Attested agent-produced records acquire no invented
coiner. Constructors remain `coined_by: constructor`, with no sources for the assembled expression; their
parts retain their own provenance.

Every card, rendered change, alternative, locked option, part occurrence and riff occurrence whose
`evidence` is `bulldust` must have a **non-null** `coined_by`. The schemas enforce this condition, and shared
projections fail if there is no attributable maker. Occurrences must agree with their referenced card's
evidence and coiner. The imagery example now identifies its maker as `agent`. Non-lexical changes retain
null evidence and null coiner.

## Coordinates and joins (P1, P3)

All offsets are half-open Unicode **code-point** spans, not JavaScript UTF-16 indices.

- A change's `src_span` addresses the source and its `out_span` addresses the current document output.
- An alternative or locked option's `out_span` identifies the document region it replaces, even when the
  rendering has a different length.
- A part/riff occurrence's `out_span` is **local to its owner's `rendered` (option) or `output` (change)**,
  like masks. Read `ownerText.slice(a, b)` in code-point space. It never assumes a single hypothetical
  document swap. Clients can apply several swaps and re-offset document regions themselves.
- A canonical construction-card part's `out_span` remains local to `construction_card.text`.

Join an occurrence to `constructions[owner.construction_id].parts` using the unique pair
**`(role, ingredient_id)`** within that card. It resolves exactly once; `entry_id` may be null and is not
the join key. Canonical and occurrence joins are unique; each occurrence includes exactly the construction's
parts. A riff joins `entries[entry_id].riffs[riff_index]` or `imagery[image_id]` as its `kind` declares.

## Warnings (P2)

Root `warnings` is exactly `list(Result.warnings)` or `list(DocumentResult.warnings)`, preserving strings,
order and duplicates. Clients and services do not append their own diagnostics here. `warning_details`
has the same length and order; `warning_details[i].message == warnings[i]`.

| Code | Meaning |
|---|---|
| `unknown_preference_match` | A preference's source match is unknown; that preference was ignored. |
| `unknown_preference_term` | A preference's target term is unknown; that preference was ignored. |
| `engine_warning` | An existing engine/policy warning without a more specific code. |

Known preference diagnostics carry codes at their origin; codes are not inferred by parsing prose. The
two preference codes let a host keep tuning diagnostics away from readers. Existing Python warning
callers still receive strings. v3's additional details are introduced at the coordinated envelope upgrade.

## Cards and lookup (P4–P6)

Constructions have a required `gloss`: the family concept's plain-English description. Show it as the card
explanation; it does not pre-empt the slice 7 naming work. All rich metadata, including riffs and canonical
parts, uses `themes: [{name, tier}]` and a resolved `minimum_vulgarity`. Theme names are unique within one
metadata object; tiers use the request's resolved theme policy. There is no string-array alternative.

The changes envelope and **every lookup outcome, including short mode and empty results**, carry
`card_version: 3` and `dictionary_id` at activation. Lookup ranking and outcome fields retain their
existing meanings. `lookup-cards.schema.json` is explicitly a **full-card projection** schema: it checks
the header and rich cards in results, ruled-out readings, protections and imagery. It is not a replacement
for the complete lookup outcome contract or a schema for short-card mode. The two lookup examples include
a populated result and an empty result so Ask a local can discriminate versions before reading cards.

## Validation and remaining work

JSON Schema checks shape. The shared `aussiefy.v3_contract` projections and `validate_response` semantic
checks cover dictionary identity, persistent construction IDs, option uniqueness, selected membership,
map references, source-match round trips, local spans/text, card joins/provenance and warning parity.
The caller structurally validates before invoking semantic checks. Tests include structurally valid
counterexamples and two simultaneous length-changing edits with a leading emoji.

Before freeze: connect these projections to the real changes and lookup producers together, verify
whole-document offset restoration, and complete the request-side replay/pinning contract. Public tuning
inputs and remaining combined 3+6 integration are still pending. No response fields were added for B1 or
B2; `warning_details`, construction `gloss` and envelope `card_version` address the preferences explicitly.
The vocabulary data pass and subsequent meaning-name work retain their planned order.
