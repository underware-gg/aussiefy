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

It takes `translate`'s parameters, by the same names and defaults, including `markdown` and `markup`. It's part
of the Python API only: the CLI, the MCP tools and yarn mode don't offer it
([DD-029](../../architecture/decisions/dd-029-changes-builder.md)).

## The contract

`ChangeSet.to_dict()` is version 1 of the `changes` contract, `{version, text, changes, entries}`. Its JSON
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
  `vulgarity` and its `masks`. For a garnish, it's the other garnish of that placement the engine weighed there.
- `locked`: for a swap, the options that only a higher vulgarity cap lets in, each tagged with the lowest
  `vulgarity` that does and rendered like the others. Selection is run again for the spot with only the cap
  raised, with every other check unchanged: level, registers, gates, grammar, span, document type, what the text
  has already said, and variety. Gated entries appear only where the policy unlocks them.
- `removed` (garnish): `{out_span, rendered}`, how its region reads without it. An opener or connective's region
  takes in the next word, whose capital it lowered.
- `rule` (phonetic and swear infix): `{id, kind, before, after}`. `pair` (dialect): `{english, before, after}`.
- `placement` (garnish): `connective`, `opener`, `tag`, `aside`, `tail`, `closer`, or `riff` for a contextual
  image after a term (which has `image_id` rather than an entry).
- `covers`: the ids of the changes inside the region a swap or removal replaces, which go with it. A drawl or a
  swear infix inside a swapped term is one. So is a neighbouring change that a phonetic match tied to the region.

`entries` maps each entry id the changes name to its card, as `lookup` shows it (`aussiefy/cards.py`), with riffs
under the vulgarity cap.

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

A swap is local. Swapping one alternative in reads exactly as a whole re-translation with that pick would read
over its region. The rest of the text stays as it was, although a whole re-translation might differ further on:
later picks, garnish and drawl rolls shift. Two swaps in one sentence, or in neighbouring ones, each read as
rendered, unless the first used an entry the second's stacked idiom or riff would have used. The engine's
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
make markup.

## Cost

`changes` is built in the same pass as the translation. At 5,000 characters it costs about 1.1 times a plain
translation at the website's default settings. Measure it with `python scripts/benchmark_changes.py`.

Tests: [the contract](../../../tests/functional/test_changes.py),
[renderings against pinned re-renders](../../../tests/functional/test_changes_oracle.py),
[the engine hooks](../../../tests/architecture/test_engine_hooks.py).
