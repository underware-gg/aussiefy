# Exploring the dictionary

Explicit discovery explains vocabulary; a discovered word is not automatically a suitable replacement in
an arbitrary sentence. These operations share translation's level, vulgarity and theme policy. They do not
perform a translation or change the caller's text.

| Python | CLI | MCP |
|---|---|---|
| `list_entries(...)` | `aussiefy entries` | `aussie_entries` |
| `get_entry(entry_id, ...)` | `aussiefy entry stoked` | `aussie_entry` |
| `random_entry(seed=0, ...)` | `aussiefy random-entry --seed 0` | `aussie_random_entry` |
| `suggest_name(seed=0, ...)` | `aussiefy suggest-name --seed 0` | `aussie_suggest_name` |
| `variations(family, parts=..., ...)` | `aussiefy variations FAMILY --parts JSON` | `aussie_variations` |

Pass an optional `translator` to each Python operation to reuse a loaded dictionary. CLI operations accept
`--dict`; MCP uses the translator injected into `build_server`. All results are JSON-ready dictionaries;
CLI commands print their complete response with `--json`. Exit 0 means a result was found, 1 means none,
and 2 means invalid input.

## Pages, cards and random entries

`list_entries` takes optional `concept` and `theme` filters. Both together mean their intersection. Concept
IDs ignore case; themes use their registered names. Unknown filters raise `UserError`. Entries are ordered
by ID, independently of YAML file order. `offset` defaults to 0 and must be a non-negative integer; `limit`
defaults to 20 and must be 1–100. Follow `next_offset` until it is null. `total` is the number of eligible
entries, not the number on the current page. Offsets are relative to the same dictionary and settings; they
are not durable cursors across dictionary updates.

`get_entry` returns one full card or null in `entry`. `random_entry` accepts the same concept and theme
filters and picks from the entire eligible set, not just the first page. Its seed defaults to 0. The same
loaded dictionary, settings and seed repeat the same choice; candidate order is stable by ID.

These three operations accept `level=5`, `vulgarity=None`, `embellishment=None`,
`document_type="general"`, `document_config=None` and `include_gated=False`. The vulgarity default is the
level's own. Document presets and exact overrides work as in [translation controls](translation-controls.md).
There is no source text for Auto detection, so `document_type="auto"` raises. No global or account settings
are read. `include_gated=True` permits explicit discovery of held-back terms, marked with `held_back`
reasons; it does not bypass level, vulgarity, register or theme restrictions. Omitted entries never appear.

Full discovery cards include the term's type, status, gloss, concepts, frame, form, permitted riffs,
metadata and structured sources, plus evidence and attestation fields. `held_back` names the fields that
keep an entry out of automatic translations, even when the caller permits discovery. Public `themes`
remain names in this slice; reporting each tag's tier and the lowest default tier belongs to the coordinated
card/changes contract update.

## Outcomes

| Code | Meaning |
|---|---|
| `matched` | A card, name or variation is available |
| `nothing_fits` | A known term or meaning has no compatible offer under these settings, or an explicit filter has no eligible entries |
| `not_in_dictionary` | No term/meaning was recognised; the dictionary may be incomplete |
| `page_exhausted` | Eligible entries exist, but this offset is beyond their final page |

`lookup` now reports these codes in `outcome` (`matched`, `nothing_fits`, `not_in_dictionary`) beside its
existing note. Recognition uses the same bounded meaning readings and direct-form matching as ranking;
this is not a claim that an unknown meaning cannot be Australian. A known term held back by policy is
recognised even when its card cannot be offered. Cards and imagery count as a successful lookup.

## Clean name suggestions

`suggest_name` takes only `seed=0`, `shape=None` and an optional translator. Its fixed policy is vulgarity 0,
no themes and no known insults; a caller cannot raise these settings. `shape` is `descriptive` (such as
`stoked-goanna`), `place` (`shazza-from-wagga`) or `phrase` (`fair-dinkum-legend`). Omit it to select a shape
with the seed. Names contain only lower-case letters, digits and hyphens.

`aussiefy/data/names.yaml` is a reviewed catalogue. Describing words and phrase components reference clean,
active Australian dictionary entries; creatures, things, nicknames and places are reviewed literal name
parts. These assembled handles are name suggestions, not newly attested slang. The loader checks the catalogue shape and entry references. Generation checks known profanity, themed
forms and insults across all entry types, including garnish and omitted vocabulary; curated review remains
necessary for unknown meanings. Ineligible references are skipped at generation, so gating or reclassifying
a name word in a valid translation overlay does not prevent the dictionary from loading.
A missing catalogue yields `nothing_fits`, preserving custom dictionaries that do not supply one.

The catalogue is finite. The host checks availability and requests another seed on a clash; this function
reserves no name and promises no uniqueness. It returns the selected shape, seed, name, fixed policy and
outcome. An unsafe assembly is skipped within a bounded search of at most 32 candidates of that shape.

## Construction variations

Pass a family ID and the complete role-to-ingredient mapping from a `bulldust` result. Each role's options
vary only that role, holding the other ingredients fixed. Every returned option is a complete construction
with its label, part evidence and output spans. This checks the assembled expression's profanity and family
policy, not just the proposed word. Missing slots, unknown IDs and incompatible ingredient kinds raise.
The options respect the constructor's settings, including registers, regions, unlock, embellishment and
exact document overrides; no source sentence is inferred from these IDs.

This is construction-level variation discovery. Rendering into an edited document and the coordinated
changes contract are separate operations. See [Bulldust](bulldust.md) for construction policy and evidence.

Hosted MCP uses `lookup_limit` to cap entry pages as well as lookup results, with each default reduced to
fit its cap. Existing capability controls still apply to these tools. Name suggestions have no document or
unlock options. See [the toolkit](toolkit.md) for server configuration.
