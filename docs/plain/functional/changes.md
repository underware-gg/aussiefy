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

## The contract

`ChangeSet.to_dict()` is version 2 of the `changes` contract, `{version, text, changes, entries, withheld}`. Its JSON
Schema ships in the package as `aussiefy/data/changes.schema.json` (`aussiefy.changes.SCHEMA`). Example requests
and responses live in `tests/fixtures/changes/`. Each change has:

- `id`: its kind and source span, as in `substitution:4-13`, with its placement or rule where those alone could
  repeat (`garnish:40-40:connective`). The same text, settings and seed always give the same ids.
- `kind`: `substitution`, `garnish`, `phonetic` (drawl and Australian spelling), `swear_infix` or `dialect` (a
  US or UK word swapped).
- `src_span` and `original`: where it came from in the source. Garnish is put in rather than swapped, so its
  source span is the point where it goes. A drawl inside a swap or a garnish takes that whole span.
- `out_span` and `output`: where it is in the output, as `[start, end)` character offsets.
- `entry_id` and `vulgarity`: the entry it came from, if it came from one, and the vulgarity it needs. A
  rendering's vulgarity is the strongest of everything in it: its entry, a stacked second idiom, a riff and any
  swear infix in the spot. A swear infix's vulgarity is its rule's.
- `masks`: the maskable words in the output (below).
- `alternatives`: for a swap, every option the engine weighed at that spot, the pick among them, in the engine's
  order. Each one has its `entry_id`, its `weight` (they share 1), its `rendered` text, its `out_span`, its
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
