# Exploring the dictionary

Explicit discovery explains vocabulary; a discovered word is not automatically a suitable replacement in
an arbitrary sentence. These operations share translation's level, vulgarity and theme policy. They do not
perform a translation or change the caller's text.

| Python | CLI | MCP |
|---|---|---|
| `list_entries(...)` | `aussiefy entries` | `aussie_entries` |
| `get_entry(entry_id, ...)` | `aussiefy entry stoked` | `aussie_entry` |
| `random_entry(seed=0, ...)` | `aussiefy random-entry --seed 0` | `aussie_random_entry` |
| `list_wordless_meanings(...)` | `aussiefy wordless-meanings` | `aussie_wordless_meanings` |
| `suggest_name(seed=0, ...)` | `aussiefy suggest-name --seed 0` | `aussie_suggest_name` |
| `variations(family, parts=..., ...)` | `aussiefy variations FAMILY --parts JSON` | `aussie_variations` |

Pass an optional `translator` to each Python operation to reuse a loaded dictionary. CLI operations accept
`--dict`; MCP uses the translator injected into `build_server`. All results are JSON-ready dictionaries;
CLI commands print their complete response with `--json`. Exit 0 means a result was found, 1 means none,
and 2 means invalid input.
For lookup, the status follows its primary outcome: `left_as_written` exits 1; `no_word_yet` exits 1 even when the response includes
suggestions for independently understood object words. Both text and JSON output retain the missing meaning.
Lookup, entry details, pages, random entries, name suggestions and variations carry `dictionary_id`, the
loaded dictionary's content identity, so callers can associate results with the same data revision.

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
contain `{name, tier}` objects, including resolved default tiers for tags with no explicit override.
`minimum_vulgarity` is the lowest default vulgarity tier that permits both the word and every tag.
It describes default placement, independently of the current request's exact theme overrides.
Full lookup results use this same card builder. Changes-v2 entry cards retain their previous shape until
the coordinated changes-contract bump.

Lookup results add `match_kind`: `term` (including inflection), `phrase`, `meaning` or `model`.
`model` means that only the model cleared the matching threshold; a model boosting an already qualifying
meaning match remains `meaning`. The existing `match` sentence and `score` remain on full results;
compact results retain `match_kind`. Image results use the same applicable codes and retain their
separate `association`. Use codes for branching rather than interpreting display prose.

## Outcomes

| Code | Meaning |
|---|---|
| `matched` | A card, name or variation is available |
| `nothing_fits` | A known term or meaning has no compatible offer under these settings, an explicit filter has no eligible entries, or no meaning is waiting for a word |
| `no_word_yet` | The meaning is recognised, but the dictionary has no Aussie word for it yet (lookup only) |
| `left_as_written` | The query is deliberately protected, or its meaning is unclear; changing the dials does not turn it into a missing-word request |
| `not_in_dictionary` | No term/meaning was recognised; the dictionary may be incomplete |
| `page_exhausted` | Eligible entries exist, but this offset is beyond their final page |

`aussiefy.discovery_outcomes` owns this vocabulary. `lookup` reports these codes in `outcome` (`matched`, `nothing_fits`, `no_word_yet`, `left_as_written`, `not_in_dictionary`)
beside its existing note. `no_word_yet` also returns `meanings`, each with its `concept` and `plain` wording.
It is claimed for a meaning established by the shared contextual readings, or an exact match on its authored
plain wording or name (`ACCEPT_AS_TRUE` or `accept as true`), never from spelling similarity alone. Names
ignore case and accept spaces instead of underscores; plain wording also uses the usual apostrophe and
whitespace folding. These discovery names do not add automatic translation triggers.

A recognised wordless meaning takes precedence over unrelated model guesses and dial rejections. Its
`results` can still explain an independently understood object: “believe a liar” reports the testimony
meaning as wordless while offering “a bullshitter” for the object. Such offers do not supply a word for the
missing verb meaning. The model remains a fallback when meaning is unsettled. A known term whose existing
words are blocked by policy still reports `nothing_fits`; this is distinct from having no word at any setting.
Otherwise, cards and imagery count as a successful lookup. An unknown meaning may still be Australian.

### Phrases deliberately kept as written

`left_as_written` has empty `results`, a `note`, span-scoped `protections` and a merged `ruled_out` list.
Each protection carries its `original` wording, `span` (Unicode character offsets in the original query),
its current `reason` and its own `ruled_out`. Several protections keep their separate reasons; the merged
list combines repeated meanings and words. An incidental protection cannot decide the outcome of a query
with another independently recognised meaning. A directly recognised dictionary expression, such as
“dog's breakfast”, still explains itself through normal discovery.

A ruled-out item has one of these shapes:

- Meaning: `{kind: "meaning", concept: "FOREST", words: [...]}`. `words` contains eligible discovery cards,
  or compact cards under `short=True`, capped at `limit` per meaning. These are cited dictionary headwords,
  not instructions to replace a component of the protected phrase. Meaning IDs remain when no word fits.
  Display names will follow with the separately reviewed meaning-label work.
- Dialect: `{kind: "dialect", english: "uk", original: "estate agent", output: "real estate agent"}`,
  naming the guarded swap rather than inventing a meaning ID.

An intentionally retained protection may have empty `ruled_out`, as “a people” does. Its current sentence
stands alone; no “Not read as” line or invented reading is added. Unclear source wording uses the same
outcome with a reason asking for more context, and is not listed as a meaning waiting for a word.
The CLI prints current reasons and any supported citations. No existing reason text is rewritten by lookup.

The dictionary builds evidence lazily for each requested protection and reuses it within that dictionary.
Evidence is retained per matched phrase within a grouped pattern: “gift shop” cannot inherit the HORSE
reading established for “gift horse”. Captured grammar slots are normalised while literal words and
context assertions remain part of that phrase's signature. Dialect citations also respect the request's
document domains and the source's actual singular/plural form.
It does not run the full audit per lookup, cache request-specific cards, invoke a model for a fully protected
query or share evidence across dictionary instances. Every request reapplies its dial and metadata checks.
The [audit command](dictionary.md#sense-boundaries) reports missing effects for curation without removing
protections automatically.
Its additive `variants` records expose these signatures and their readings, with `needs_audit` on each
variant and a `variants_needing_audit` total. The older per-pattern aggregates and totals remain available;
a grouped pattern having some evidence does not prove every one of its forms.

## Meanings without a word yet

`list_wordless_meanings` pages through the meanings the dictionary recognises but has no Aussie word for:
no entry, image or construction expresses them (omitted entries don't count), and the dialect table doesn't
already swap their words for the Australian one (“trash can” becomes “bin”). It takes `offset` and `limit`,
paged as `list_entries` is, and an optional translator, so extension dictionaries' meanings are included.
No dials apply. Results are ordered by concept ID; each has its `concept`, `plain` wording and `examples`,
sentences in which translation reads that meaning (a test proves each for the bundled dictionary). The
outcome is `nothing_fits` when no meaning is waiting at all.

Only genuine meanings are listed. Phrase fences are separate from concepts. The named abstention
concept `UNRESOLVED_SENSE` never appears. Heartbreak, freedom, remorse, being out of work, getting worked up and having a talent are ordinary
meanings waiting for a word. The gift of the gab is a separate set-phrase fence, not the
general talent meaning. See the [dictionary format](dictionary.md).

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
