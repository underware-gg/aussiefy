# Changes: every change, with its alternatives

`aussiefy.translate_changes` translates a text exactly as `translate` does, and also reports every change the
translation made, placed in the output. Each word swap comes with its alternatives, and with the options a
vulgarity lock holds back, each rendered where it stands. It's how a page lets a reader edit their own
translation with the engine driving it. The aussiefy website's service passes the result on unchanged.

```python
import aussiefy

cs = aussiefy.translate_changes("I'm exhausted and the toilet is broken.", level=4, vulgarity="dad")
cs.text                  # the translation, as translate gives it
cs.to_dict()["changes"]  # every change, in output order
cs.entries               # the card of every entry the changes name
```

It takes `translate`'s parameters, by the same names and defaults, including `markdown` and `markup`, and also
`embedder`: the similarity fallback (`ngram`, `bundled`, `local` or `none`; the profile's own when omitted), which a
host sets explicitly. It's part of the Python API only: the CLI, the MCP tools and yarn mode don't offer it
([DD-029](../../architecture/decisions/dd-029-changes-builder.md)). `aussiefy.guide.dial_descriptions()` gives every
dial's settings with a one-line description each, for a page that lists them.

## Frozen v3

The active changes and rich-card contracts are v3, using the response fields accepted in review
`20261112-r2`. Packaged schemas are `aussiefy/data/changes.schema.json`, `cards.schema.json` and
`lookup-cards.schema.json`. The last checks the full-card lookup projection, not every lookup outcome
field or short-card mode. The [historical draft](../../drafts/changes-v3/README.md) and its illustrative
examples retain their exact review bytes. Current fixtures in `tests/fixtures/changes/` come directly
from the real emitter, including constructions, imagery, Markdown and coded warnings.

`kept`, `held`, personal terms, plain alternatives and selection results belong to the later contract.

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
tuned construction/riff share links ship. The explicit request-side pins described below retain selected forms, recipes and riffs.
Identity alone, without those pins, still does not promise replay closure.

## Provenance (B2)

`coined_by` names who invented the wording: `person`, `agent` or `constructor`. `produced_by: agent`
records agent production of the stored record; it is not generally a claim that the agent invented the
wording. An explicit `coined_by` always wins. When the evidence assessment is `bulldust`, there is no
explicit coiner, and `produced_by` is `agent`, the shared projection derives `coined_by: agent`. That assessment
already requires the unsuccessful search and absence of independent attestation; the projection changes
no stored facts, attestation score or evidence label. Attested agent-produced records acquire no invented
coiner. Constructors remain `coined_by: constructor`, with no sources for the assembled expression; their
parts retain their own provenance.

Every card, rendered change, alternative, locked option, part occurrence and riff occurrence whose
`evidence` is `bulldust` must have a **non-null** `coined_by`. The schemas enforce this condition, and shared
projections fail if there is no attributable maker. Occurrences must agree with their referenced card's
evidence and coiner. Imagery projections identify the assessed bulldust maker. Non-lexical changes retain
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
callers still receive strings. The v3 producers emit these details together.

## Cards and lookup (P4–P6)

Constructions have a required `gloss`: the family concept's plain-English description. Show it as the card
explanation; it does not pre-empt the slice 7 naming work. All rich metadata, including riffs and canonical
parts, uses `themes: [{name, tier}]` and a resolved `minimum_vulgarity`. Theme names are unique within one
metadata object; tiers use the request's resolved theme policy. There is no string-array alternative.

The changes envelope and **every lookup outcome, including short mode and empty results**, carry
`card_version: 3` and `dictionary_id` in v3. Lookup ranking and outcome fields retain their
existing meanings. `lookup-cards.schema.json` is explicitly a **full-card projection** schema: it checks
the header and rich cards in results, ruled-out readings, protections and imagery. It is not a replacement
for the complete lookup outcome contract or a schema for short-card mode. The two lookup examples include
a populated result and an empty result so Ask a local can discriminate versions before reading cards.

## The contract

`ChangeSet.to_dict()` is version 3 of the `changes` contract. Its root contains `version`, `card_version`,
`text`, `dictionary_id`, `tuning`, `warnings`, `warning_details`, `changes`, `entries`, `constructions`,
`imagery` and `withheld`. Its JSON
Schema ships in the package as `aussiefy/data/changes.schema.json` (`aussiefy.changes.SCHEMA`). Example requests
and responses live in `tests/fixtures/changes/`. Each change has:

- `id`: its kind and source span, as in `substitution:4-13`, with its placement or rule where those alone could
  repeat (`garnish:40-40:connective`). The same text, settings and seed always give the same ids.
- `kind`: `substitution`, `garnish`, `phonetic` (drawl and Australian spelling), `swear_infix` or `dialect` (a
  US or UK word swapped).
- `src_span` and `original`: where it came from in the source. Garnish is put in rather than swapped, so its
  source span is the point where it goes. A drawl inside a swap or a garnish takes that whole span.
- `out_span` and `output`: where it is in the output, as `[start, end)` character offsets.
- `entry_id`, `construction_id` and `vulgarity`: the dictionary entry or constructed expression it came from,
  if either applies, and the vulgarity it needs. A construction has null `entry_id` and a distinct construction ID. A
  rendering's vulgarity is the strongest of everything in it: its entry, a stacked second idiom, a riff and any
  swear infix in the spot. A swear infix's vulgarity is its rule's.
- `masks`: the maskable words in the output (below).
- `alternatives`: for a swap, every option the engine weighed at that spot, the pick among them, in the engine's
  order. Each one has its entry or construction key, its `weight` (they share 1), its `rendered` text, its `out_span`, its
  `vulgarity` and its `masks`. Optional `semantic_effects` records effects of this rendering
  at this source mapping, such as `quantity_approximation`; entry-card effects remain inherent to an entry. For a garnish, it's the other garnish of that placement the engine weighed there.
- `locked`: for a swap, the options the vulgarity cap alone holds back, each tagged with the lowest `vulgarity`
  that lets it in. Selection is run again for the spot with only the cap raised, with every other check
  unchanged: level, registers, gates, grammar, span, document settings (including `narrator_opinion` and `quantity_approximation`), what
  the text has already said, and variety.
  Only an entry rated above the cap in effect is locked (a raised cap also reweighs, so variety's best few can take
  in a clean entry, which isn't). Gated entries appear only where the policy unlocks them. A locked option is
  rendered like the others, at the reader's cap: its riffs and swear infixes are the ones the reader's vulgarity
  allows, as the page shows it before it's unlocked. At Dad, "very cold" as fuckin' reads "fuckin'", though a
  whole re-translation at Uncle Bob would read "cold as fuck".
- `removed` (garnish): `{out_span, rendered}`, how its region reads without it. An opener or connective's region
  takes in the next word, whose capital it lowered. Every garnish has one unless it's named under `withheld`.
- `rule` (phonetic and swear infix): `{id, kind, min_level, before, after}`. `min_level` is the level a drawl or
  spelling rule starts at, from `aussiefy/data/phonetic.yaml`, so a page can say "from level 5, swaggie". A swear
  infix's is `null`: it has no level, since the vulgarity and the embellishment let it in at any level. `pair`
  (dialect): `{english, before, after}`.
- `placement` (garnish): `connective`, `opener`, `tag`, `aside`, `tail`, `closer`, or `riff` for a contextual
  image after a term (which has `image_id` rather than an entry).
- `covers`: the ids, in output order, of the other changes whose output or region overlaps one of this change's
  regions (its alternatives', locked options' or removal's). Swapping or removing this change rewrites text those
  stand on. A drawl or a swear infix inside a swapped term is covered. So is a neighbour whose region overlaps this
  one, and then each covers the other. In "Anyway, he's a few snags short of a barbie", the connective's region is
  "Anyway, he's" and the swap's starts at "he's". Removing the connective rewrites "he's", and swapping in "he
  isn't the full quid" rewrites part of the connective's region, so each covers the other. A garnish region that
  takes in a whole swap is another such pair. A change with no region (a drawl, an infix, a US word swapped) covers
  nothing.

`entries` maps each entry id the changes name to its card, built as `lookup` builds it under the same dials
(`aussiefy/cards.py`): optional `semantic_effects` lists reviewed additions such as `opinion`; riffs appear
under the vulgarity cap where the embellishment takes riffs at all, and a gated
entry's flags where the policy unlocked it.

`withheld` lists, as `{id, reason}`, the swaps and garnish whose renderings are left out, with the pick alone
offered: a swap's other alternatives and locked options, and a garnish's other alternatives and its removal. The
reason is `pick-differs` where the pick, rendered over its region, isn't the output there, and `region-unsettled`
where a drawl or infix match still reads across the region's edge after it has widened as far as it goes. Neither
has happened over the test corpora. They're there so a rendering that might read wrong is never offered, and a
page can tell why a spot has no alternatives.

All offsets count Unicode code points, including source/output spans, alternative regions and mask positions.
For example, `🦘 toilet` becomes `🦘 dunny`: the source span is `[2, 8)` and the output span is `[2, 7)`.
JavaScript clients can slice and splice by code point with `Array.from(text)`:

```javascript
const points = Array.from(text);
const current = points.slice(start, end).join("");
const swapped = [...points.slice(0, start), replacement, ...points.slice(end)].join("");
```

Use the rendering's own text for its mask offsets. Combining marks count separately, so a visible letter or
emoji sequence can occupy several positions.

## How a swap is rendered

Every alternative is rendered as the engine would render it at that spot, with the rest of the output held
fixed. It takes the engine's own path: the form and the spelling the text keeps, the article fitted ("a toddler"
becomes "an ankle biter"), the entry's own replacement span, a stacked second idiom, a riff, and capitals. The
sentence's garnish is put back as it was decided. Then the drawl, spelling and swear infixes run over the spot
alone, with the rolls the engine would give it there: each rule's count starts from the matches in the
unchanged text before it, and reads the whole text's context (quotes, questions, the words either side).

All of a spot's options share one region, so swapping one in replaces the same span. The region widens a word
where a drawl or infix match crosses its edge ("have not" becoming "haven't") or a neighbouring match's
lookaround reads it ("won't bloody well have").

A garnish's region widens the same way. An opener's or connective's region takes in the next word, whose capital
it lowered, and a word more where a match runs on: in "Well, it is easy", a swap or removal of "Well" replaces
"Well, it is", since the drawl's "it is" match crosses "it". A region never cuts the words another swap or
garnish put in: it takes in the whole of one it reaches. Two regions can still share a word they both widened
over for one drawl match, as a connective's and the swap after it share "he's". Then each covers the other.

Each drawl, spelling or infix match in the spot is let in or kept out exactly as the engine's own pass does it
(a question, the words before it, a kept heading or link text, a quoted document), reading those spans where the
match sits.

A swap is local. Swapping one alternative in reads exactly as a whole re-translation with that pick would read
over its region. The rest of the text stays as it was, although a whole re-translation might differ further on:
later picks, garnish and drawl rolls shift. Two swaps in one sentence, or in neighbouring ones, each read as
rendered, unless the first used an entry the second's stacked idiom or riff would have used. Over the everyday
corpus that happens in one pair in about fifty. The engine's
output and its seeds are unchanged by any of this: `translate_changes(...).text` is `translate(...).text`.

## Explicit replay pins

Removing tuning changes a request. Use an explicit request packet to preserve its selected forms,
construction recipes, stacks, entry riffs, imagery and garnish. The response schema stays unchanged:

```python
original = aussiefy.translate_changes("She was exhausted.", level=5, seed=4)
pins = original.replay_pins()
replayed = aussiefy.translate_changes("She was exhausted.", level=5, seed=4, pins=pins)
assert replayed.text == original.text
```

`Result`, `DocumentResult` and `ChangeSet` have `replay_pins()`. A plan also includes `replay_pins`.
`ChangeSet.replay_options()` returns a separate sidecar with `current` (the complete packet) and
`changes` (change ID to `{key, pick}` options). It is absent from `ChangeSet.to_dict()`. A service can
store or deliver it separately. `cs.replay_pins({change_id: option_key})` replaces current picks with
offered alternatives; null selects an offered garnish removal. Unknown changes/options fail. Locked
choices still need the caller to raise the relevant cap. A plain alternative is not added in v3.

The version-1 request schema is `aussiefy/data/pins.schema.json`. A packet contains `dictionary_id`,
`source_id` (SHA-256 of the exact source encoded as UTF-8), original `seed`, `complete` and `picks`.
Substitution and imagery anchors use the precise detected source span and canonical `match`, rather
than a change's widened replacement region. Garnish uses its source sentence span and placement.
All are source Unicode code points; Markdown units are offset into the whole source.

An entry target retains its ID and dictionary form. A construction retains its persistent ID,
family and every typed ingredient slot; replay validates and resolves that one composition without
enumerating the candidate space. An entry riff retains its canonical text, never `riff_index`. The loader requires that text to
identify exactly one riff within the entry; duplicate canonical wording is an error.
Stacked entries retain their own form. A bulldust entry cannot be an unlabelled secondary stack;
it remains available as a primary, attributed choice. A null target retains source wording or removes garnish;
a null image ID removes that image. Duplicate, unknown, malformed, mismatched or unconsumed picks
raise `UserError`; none silently disappear.

A complete packet suppresses unlisted automatic substitutions, imagery and garnish. A partial
packet (`complete: false`) leaves other spots automatic. Dialect, spelling and phonetic rules still
run. Keep the original source, dictionary, seed and behaviour settings for exact output replay.
Removing popularity/preferences preserves the explicit choices; the resulting tuning summary
reports the new call. Offered pools and their weights may differ from the original tuned response.

Explicit picks bypass automatic probability, variety and soft repeat weighting, while every hard
meaning, frame, degree, captured argument, source protection, genre, level, vulgarity, theme and
invention check still applies. Riffs retain configured count/spacing limits, one use per entry/image and their placement and behaviour permissions; garnish
retains source-context, placement and density constraints. A changed request that cannot honour
every pin fails. The package does not store preferences, identities, share links or server sessions.

## Masks

Each rendering lists its maskable words as `{span, ending_start, vulgarity}`: the span in that rendering, where
its ending starts, and the vulgarity it needs. A page can hide what's stronger than its reader allows, keeping
the first letter and the ending (`f$%&ed`). Only actual profanity is masked:

- words on the dictionary's swear list (`aussiefy/data/swears.yaml`), with their plurals and dropped g's;
- compounds built on a listed swear ("fuckwit", "shitfight", "bullshitter"), as the dictionary's own rated
  entries and riffs use them (`Dictionary.swear_compounds`). An ordinary word that happens to hold one
  ("cocktail", "cocky") is never one, and nor is a compound in the reader's own text;
- the profane words an entry authors where they aren't listed (`mask: [wanker]`), in that entry's own renderings
  (a stacked idiom's too), at the entry's vulgarity.

Innuendo, insults and crude words that aren't profanity are never masked: an entry marked `profane: false`
("rooted", "mongrel", "shut your gob") shows in full. An ending is
kept only after a stem that is itself a listed swear or a mask word (`-s`, `-es`, `-ed`, `-er`, `-ers`, `-ing`,
`-in'`, `-in`, `-y`): "fucked" keeps "ed", "fuckin'" keeps "in'", "arseholes" keeps "s". Any other word, a
compound included, is masked whole after its first letter, so `ending_start` is its end ("bullshit"). Where a
word is both listed and authored, it has one mask, at the higher vulgarity.

## Markdown and markup

With `markup`, protected spans (code, links, tags) are masked through the pass and restored after, keeping their
length, so offsets and renderings hold. With `markdown=True`, each prose unit's changes are placed in the
document. Source offsets are document positions. Each rendering is escaped as its unit is, so custom slang can't
make markup. A whole re-render with a swap pinned inside its unit reads the same.

## Cost

`changes` is built in the same pass as the translation. Its budget is 1.5 times a plain translation for each
5,000-character text, for every setting the website's service allows: its default, the strongest dials and each
document type it offers. `python scripts/benchmark_changes.py` gates on that, timing the two in turn in process time.
At the website's default it costs about 1.1 times; garnish alternatives take a share of the headroom alongside the
swaps'. Larger texts, Markdown documents (which the website doesn't take) and a stress setting with every garnish
at full rate are reported, not gated.

Tests: [the contract](../../../tests/functional/test_changes.py),
[renderings against pinned re-renders](../../../tests/functional/test_changes_oracle.py),
[the engine hooks](../../../tests/architecture/test_engine_hooks.py).


Version 2 adds optional applied `semantic_effects` to substitution alternatives and locked options, and
recognises `quantity_approximation` alongside `opinion`. Existing spans, IDs and rendering rules are unchanged.
Consumers validating against the strict v1 schema must use the v2 schema for this package version.
