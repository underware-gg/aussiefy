# Exploring the dictionary

Explicit discovery explains vocabulary; a discovered word is not automatically a suitable replacement in
an arbitrary sentence. These operations share translation's level, vulgarity and theme policy. They do not
perform a translation or change the caller's text.

| Python | CLI | MCP |
|---|---|---|
| `list_entries(...)` | `aussiefy entries` | `aussie_entries` |
| `get_entry(entry_id, ...)` | `aussiefy entry stoked` | `aussie_entry` |
| `meaning_quiz(seed=0, ...)` | `aussiefy meaning-quiz --seed 0` | `aussie_meaning_quiz` |
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

## Entry IDs and URLs

Entry IDs are permanent public keys from this checkpoint. A released or already published core ID is
never reused for a different entry. Editing a headword normally keeps its ID. A rename or merge retains
old IDs as aliases to the current entry; chains resolve directly to the final card. `get_entry(old_id)`
returns the requested key in `entry_id` and the current key in `entry.id`, so a host can redirect when
those differ. CLI `entry` and MCP `aussie_entry` use exactly this resolution and the current entry's dials,
permissions and held-back policy. Aliases are not duplicate entries in lists, counts, random picks or quizzes.

A deliberately removed ID is reserved permanently and returns `outcome: "removed"`, the requested
`entry_id` and `entry: null`. An alias of a removed entry also reports `removed`. An unknown ID still
returns `not_in_dictionary`; an existing entry blocked by dials returns `nothing_fits`. Omitted entries
remain undiscoverable under the existing policy.

The bundled `entry_ids.yaml` register includes the last release and the already published dev pin.
Keep its keys forever: an ID maps to itself while current, to another ID after a rename/merge, or to null
after removal. Validation rejects cycles, missing targets and reuse of an alias or tombstone as an entry.
Release checks compare the candidate with the exact previous release; a checked-in baseline also protects
the currently published development inventory. This reserves identity, not exact wording: curators must
never repurpose an existing key for an unrelated term. Community/other extension publishers own their
ID histories; a core alias or tombstone cannot be taken by an extension. Custom data directories may
supply their own register; `include_builtin=False` excludes the core register.

## Pages, cards and random entries

`list_entries` takes optional `concept`, `theme` and `initial` filters, which intersect. `initial` is
a lowercase `a`–`z`, or `#` for other characters. The key is the headword (`form`), lowercased with
whitespace normalised and one leading whole-word “a”, “an” or “the” removed. Both the letter and order
within a letter use that key: “a counter meal” is under C, “a Hanrahan” under H, and “the bush” under B.
Equal keys use the entry ID as a stable tie-break. IDs and displayed forms are unchanged. CLI uses `entries --initial k` (quote
`'#'` in a shell); MCP uses `aussie_entries(initial="k")`.

`total` counts entries after the initial filter. `initial_counts` always includes all 27 keys with zero
counts where needed, under the other filters and permissions, before initial filtering or pagination.
It stays the same across pages and selected initials so callers can grey out empty letters. Concept
IDs ignore case; themes use their registered names. Unknown filters raise `UserError`. Entries are ordered
by that article-free headword key, independently of YAML file order. `offset` defaults to 0 and must be a non-negative integer; `limit`
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
| `removed` | A previously published entry ID was deliberately retired (entry detail only) |
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
Where the approved copy calls for the derived line alone, `reason` is `""`; `note` is empty when none
of the query's protections needs a sentence. A missing reading requires a sentence instead. Curators
check this for every real phrase form, rather than borrowing another alternative's evidence.

The dictionary builds evidence lazily for each requested protection and reuses it within that dictionary.
Evidence is retained per matched phrase within a grouped pattern: “gift shop” cannot inherit the HORSE
reading established for “gift horse”. Captured grammar slots are normalised while literal words and
context assertions remain part of that phrase's signature. Dialect citations also respect the request's
document domains and the source's actual singular/plural form.

Authored protections also apply when a query uses capitals, as in `Native Americans`, `US Congress`
or `National Forest`. The shared reader retains the protection while keeping ordinary replacement
readings out of names. Lookup preserves the query's original spelling and character offsets; whole
dictionary expressions can still own their complete phrase.
That exception requires a whole dictionary form or its inflection. A component word from a longer
idiom cannot override the phrase protection: `the toss` stays as written, while the complete idiom
can still be looked up directly. Singular/plural identity forms are explicitly authored together,
as in `Native American|Americans`; neither form borrows the other's explanation evidence.

Recognised noun phrases include their determiners and counts. Queries such as `five dollars` and
`two biscuits` use the known noun meaning; a count does not claim unknown words or another clause.
Evidence building does not run the full audit per lookup, cache request-specific cards, invoke a model
for a fully protected query or share evidence across dictionary instances. Every request reapplies its dial and metadata checks.
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

A meaning with only optional imagery is still waiting for a word. An eligible image may accompany
`no_word_yet`; its presence never turns invented comparison wording into a dictionary word. Exact
authored meaning names also select their own eligible images, with the same permissions.


## Guess the meaning

`meaning_quiz(seed=0, ...)` takes random_entry's dials and discovery permissions, without concept/theme
filters. It returns the common envelope and seed, the full `entry` card, four `options` shaped as
`{text, entry_id}` in seeded order, and zero-based `answer`. The correct option's ID equals the card's ID.
The caller can hold the answer/card until the guess; this is one response with no scoring or server session.
When no four-option question can be made, outcome is `nothing_fits`, entry/answer are null and options is [].

Every option is the first clause of an entry's gloss, with parenthetical asides and quoted examples
removed. Question and distractors respect the same level, vulgarity, registers, theme permissions and
include_gated setting. Garnish and self-naming glosses are excluded. Candidate distractors share the frame,
or its word class when fewer than twelve survive; they share no concept, meaningful form word or option
word with the question. Shared lookup at limit 50 excludes known true answers in both directions.
Close, middling and far bands rank enriched meaning text through the caller's lookup embedder. Bands are
best effort, not a taxonomy or a guarantee of distance, and unrecorded polysemy remains a curation issue.
The `ranking` envelope is `{model: <backend name>, fallback: <boolean>}`. With no lookup model it explicitly
reports the char-trigram fallback. Oracle results are reused within the call, without a cross-request cache.

CLI JSON matches Python. Plain CLI output prints the four choices followed by the answer; an interactive
host uses the JSON response to control its reveal. MCP is read-only and honours the host's hidden dials
and injected translator. The same dictionary, settings, model and seed repeat the same quiz.

The current bundled-model response fixture is `tests/fixtures/meaning-quiz.json`. Regenerate intentional
changes with `python scripts/regen_meaning_quiz_fixture.py` and review its diff.


## Browse by meaning

`list_concepts` (CLI `aussiefy concepts`, MCP `aussie_concepts`) lists stored meanings by stable
concept ID. Each row contains `concept`, `plain` and `entry_count`. The count is the total returned by
`list_entries(concept=...)` with the same dials, themes, registers and held-entry policy. Counts are
computed before pagination; meanings blocked by the dials remain with zero. Meanings without a stored
entry are excluded and retain their separate `list_wordless_meanings` listing. Omitted entries never
create browse rows. The standard envelope includes dictionary identity, dials, warnings and pagination.

The Gate 4 wording pass supplies plain names and exact search words for every ordinary concept.
Rob's approved sample wording/search lists are retained. Additional wording is marked provisional in
the dictionary and recorded in the Brain's Rulings for Rob. Search words are discovery terms, not
translation triggers, and this pass changes no source patterns or existing headword spellings.

`plain` is complete reader-facing en-AU wording for the meaning's name; it is not an ID, a template
or a text fragment the caller must complete. `list_entries(concept=...)` filters to entries belonging
to that concept, intersected with the other entry filters and dials. The wording pass retains the
existing protected-query priority behaviour: a new search alias must not overturn a fence as a side
effect. The agreed aliases retain “American football” as a match while “American football game”,
“a people”, “British pounds” and “hiking trail” stay left as written.


Quiz exclusions use one request-local prepared lookup batch. Several adaptive gloss queries still run,
with ordinary lookup's ranking, top-50 limit and permissions; ID-only projection avoids building full
cards for exclusions. Fixed spelling data is bounded and reused by actual content, while query results
stay local to the call. This changes no quiz input, seeded option order or answer contract. See the
[paired measurement and acceptance evidence](../../../research/gate4-self-review-2026-11-15/README.md).
