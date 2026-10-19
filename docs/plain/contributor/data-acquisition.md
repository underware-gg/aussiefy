# Growing the dictionary

New slang reaches the dictionary three ways: hand curation, the scrape → tag → review pipeline, and research
rounds. Whatever the route, it lands as data ([DD-002](../../architecture/decisions/dd-002-slang-is-data.md)),
passes the loader's validation, and is reviewed as a diff. What each tool does is described in
[maintainer tools](../functional/maintainer-tools.md); this page is the workflow.

## What counts as Aussie

An entry needs to be slang Australians actually use, not slang only Australians use. "Christen", "this neck of
the woods" and "put a sock in it" are shared with other Englishes but are everyday here, so they're in, with a
`notes` line saying so. Phrases that are foreign to Australian speech ("that dog won't hunt") or unattested are
flagged instead, and kept in `aussiefy/data/entries/flagged.yaml` so re-scrapes don't reintroduce them.

Every gloss is written in our own words, never a source's
([DD-012](../../architecture/decisions/dd-012-reference-dictionaries-are-reference-only.md)).

## Reference dictionaries

The Macquarie Dictionary, including its Australian Word Map of regional words, and the Australian National
Dictionary are the best checks on whether a word is genuinely Australian, which region it belongs to and what
it means. They're copyrighted and the Word Map sits behind a subscription, so
`aussiefy/data/source_policy.yaml` marks them reference-only and `aussiefy dev scrape` refuses them unless you
pass `--permitted`. Use them by hand: look a word up, set its `region` and `register`, and cite the page in
`sources`.

The [18 October meaning pass](../../../research/slang-meanings-2026-10-18/README.md) cross-references 130
selected existing entries against named sources, with a ledger of supported meanings, corrections and
unresolved evidence. It distinguishes party/reaction uses of “frog in a sock”, work avoidance from benefit
receipt and joblessness, earnest effort from hardship, fair treatment from liberty, and exclamations from religious
contingency. This is a bounded review, not certification of the entire dictionary. Checked extra URLs live in
`sources.yaml`; component attestation does not establish a whole invented construction as a traditional idiom.

The original “make [it] true blue” and “make fair dinkum” consecration paraphrases require the existing
`dubious_meaning` unlock: genuine/loyal is not the same meaning as sacred. Evidence for a further sense should
produce a precise concept/frame or a review note, rather than a broad trigger that silently changes facts.

The [focused hunger harvest](../../../research/hunger-phrases-2026-10-18/README.md) retains three independent
generations for `feeling pretty hungry`, source checks and decisions. Moderate appetite gets grammatical
verb phrases; colourful clause rewrites and original exaggerations use the existing imagery controls.

## Finding what's missing

`aussiefy gaps FILE...` runs the engine over a corpus and lists the content words it keeps leaving in plain
English, each with a verdict on what to do (add a trigger to the nearest concept, add a concept, or leave it).
`aussiefy compare` against a target translation shows which of its slang the engine misses. Both point at
where to curate next.

## The scrape → tag → review pipeline

```sh
aussiefy dev scrape URL [URL ...] -o data/staging/scraped.yaml   # or saved .html files (+ --source-url)
aussiefy dev tag data/staging/scraped.yaml -o data/staging/tagged.yaml
aussiefy dev review data/staging/tagged.yaml                     # dry run: summary + unified diff
aussiefy dev review data/staging/tagged.yaml --apply
```

`tag` needs the `llm` extra and an API key; `scrape` needs the `scrape` extra. The staging files under
`data/staging/` are working files, not part of the dictionary.

Two more sources feed the same `tag` and `review` steps:

- **Fragments.** `aussiefy dev fragments -o data/staging/fragments.yaml` stages slang buried inside our own
  idioms ("dunny" in "stick out like a country dunny").
- **Harvests.** `aussiefy dev harvest plain.txt aussie.txt` mines an Aussified rewrite (from an agent, the
  `--rewrite` cache or a person) for the spans it changed. Running it on a target translation's misses is how
  they become candidate entries.

`aussiefy/data/entries/fragments.yaml` and the "harvested" sections of the other entry files came from running
both over our own idioms and over an agent's Aussie Gettysburg, then curating by hand.

Harvesting is candidate discovery, not attestation. Review each expression against existing forms, variants,
triggers and dialect swaps before adding it. A newly written comparison can be useful without being a
saying in common use: keep it as optional colour in `riffs.yaml`, attached to a term whose meaning it suits,
rather than inventing a plain-English trigger for it. Riffs must read naturally after their term and respect
the same vulgarity and document controls as existing colour. Retain the source, persona and decision for
each research candidate; a persona is a writing brief, not a new engine setting.

## Research rounds

Research rounds are the bigger route in: subagents extract or propose candidates, verifiers check each one
under a brief, and `aussiefy dev round research/<round>` applies the verdicts. Run it without `--write` first to
see what it would add and drop, and why; `--write` validates the result in a scratch copy before touching the
dictionary. Each round's `README.md` says how it was run and how to repeat it, and, for a round applied this way,
its `round.yaml` configures the apply.

A new concept keeps all supported metadata (`description`, `triggers`, `person`, `neutral_person`, `not_in`).
Optional `concept_fixes.yaml` maps concept IDs to explicitly reviewed field overrides. It can also define an
entryless guard concept; an unused concept inferred from a rejected candidate is still discarded.

```yaml
TIRED:
  not_in: [technical]
ZZ_GUARD:
  description: A reviewed guard with no output entry.
  triggers: {np: [a reviewed guard phrase]}
```

Field overrides replace the named field, so `triggers` replaces the complete trigger mapping. They apply last,
after `trigger_fixes.yaml`'s additions/removals/intensities, and the dry run lists their IDs and fields.

Reapplication preserves previously written concept records and their hand edits. New definitions are appended
to the round's own section. Explicit trigger fixes update triggers while keeping other metadata; explicit
concept fixes rewrite only affected records, whose internal formatting/comments may change. Neighbouring
records and section comments remain intact. Move an intentional change into a fix file rather than relying
on edited verifier verdicts to overwrite a concept already written.

A second reviewed sense may reuse an existing primary form when its verdict declares
`allow_existing_form: true` and supplies at least one concept not already attached to that form. The same
flag may sit on a hand-written `extra_entries.yaml` record. The default duplicate guard remains active;
identical senses cannot bypass it. Existing variant handling is unchanged. Every write still validates the
complete candidate dictionary in scratch before changing the real files.

| Round | Summary |
|---|---|
| [vocabulary-2026-10-17](../../../research/vocabulary-2026-10-17/README.md) | X-post suggestions and 45 unharnessed reference-persona retellings, curated into six entries and 25 optional riffs; no persona preset or scored benchmark |
| [gap-fill-2026-10-11](../../../research/gap-fill-2026-10-11/README.md) | Words the engine left in plain English, retold by subagents and searched on the web, then verified and applied with `dev round` |
| [classics-2026-10-11](../../../research/classics-2026-10-11/README.md) | Australianisms from classic Australian texts (`tests/corpus/classics/`), seed terms and the retellings, verified and applied with `dev round` |
| [swearing-2026-10-12](../../../research/swearing-2026-10-12/README.md) | Making level and vulgarity orthogonal, and adding plain-word swears; applied as engine and data changes rather than with `dev round` ([DD-005](../../architecture/decisions/dd-005-orthogonal-level-and-vulgarity.md)) |

The retellings study compared the engine, yarn mode and an unharnessed agent on the same texts:
[COMPARISON.md](../../../research/retellings-2026-10-11/COMPARISON.md) (five texts) and
[COMPARISON-2.md](../../../research/retellings-2026-10-11/COMPARISON-2.md) (four more, after the classics round).

## Concepts

The concept vocabulary in `aussiefy/data/concepts.yaml` is hand-curated
([DD-010](../../architecture/decisions/dd-010-hand-curated-concept-vocabulary.md)). When `tag` proposes a concept
that doesn't exist, the entry is gated as `untagged` and the proposal goes in its review notes: decide whether
to add the concept, map the entry to an existing one, or drop it.

## The seed listicle

The original brief's [seed listicle](https://learnconversations.com/funny-aussie-old-sayings-and-phrases/)
was acquired on 2026-10-17. The fetcher now honours a declared HTML encoding when the HTTP response omits
its charset; an explicit HTTP charset wins, and non-HTML text retains its existing decoding. Previously
cached corrupted pages need `--refresh`:

```sh
aussiefy dev scrape --refresh https://learnconversations.com/funny-aussie-old-sayings-and-phrases/
```

The review covered 227 raw rows and 212 normalised candidates. Ten entries were promoted through the normal
validated review boundary, using manually authored proposals and original glosses; the API tagger was not
called. Of the remainder, 88 have existing term/variant/component coverage, 100 remain craft or verification
notes, three proposed senses were declined, five rows were metadata, and six retain existing gate/omit
decisions. Component coverage does not promise automatic replacement of a whole sentence. The complete
[decision ledger](../../../research/maintenance-2026-10-17/seed-decisions.yaml) and
[proposals](../../../research/maintenance-2026-10-17/seed-proposals.yaml) retain the review. Raw HTML,
copied meanings and usage examples remain temporary, outside the repository.

The source's known problems remain flagged in `aussiefy/data/entries/flagged.yaml`. "That'll
do, pig", "cruisin' for a bruisin'", "that dog won't hunt" and "throw another shrimp on the barbie" are omitted.
"All hat and no cattle" (Texan) and "bugger me sideways'n call me the pope" (no attestation found) are gated.
Both appear in the brief's sample output, so `--unlock not_aussie,fabricated` brings that flavour back.

## After changing the dictionary

Use corpus examples to identify whether a correction belongs in a shared grammar rule, a concept's meaning
patterns, or an entry's forms and constraints. Fix broadly applicable errors in the canonical data or engine;
an overlay is useful for testing a reviewed correction and for local vocabulary policies, not a replacement
for improving the bundled dictionary. The [runtime overlay format](../functional/dictionary.md#dictionary-overlays)
can add or patch concepts and entries through the existing loader. It is separate from research-round
`concept_fixes.yaml`, whose workflow writes reviewed changes back to the maintained source files.

For each proposed correction, keep a positive example, a close wrong-sense example and a grammar variant
such as tense, plural, negation or a changed participant. Check candidate eligibility as well as selected
outputs, so a faulty route is removed rather than merely losing one seeded roll. Run lookup, plans and change
alternatives over the same loaded dictionary where affected. Do not copy entire reference queries into
special-case mappings to raise a benchmark score; existing research-round checks reject that practice.

1. `aussiefy validate` must pass with no new warnings.
2. Run the test suite, regenerate the golden corpus if translations changed on purpose, and review its diff
   ([testing](testing.md)).
3. The bundled embedding model is now `stale`; retraining it is a separate release, described in
   [training/README.md](../../../training/README.md).
4. Record the change under `[Unreleased]` in `CHANGELOG.md`.

## Integrating a source-meaning audit

Research under `research/slang-meanings-2026-10-19-batch3/` and `batch4/` distinguishes selected meanings,
complete constructions, components, historical contexts, source chains and access limitations. Their 239
proposed source records are merged into `aussiefy/data/sources.yaml` without replacing existing URLs.
A source on a public card supports that reviewed scope; it does not certify every trigger, every form,
current frequency or Australian exclusivity. Multiple editions or mirrors of one work remain one witness.

Apply clear lexical distinctions as dictionary concepts and compatible forms, with positive eligibility and
negative meaning tests. The latest integration preserves quantities, location nouns, physical reference,
polarity and activity purpose without slang-specific engine checks. New fruit-and-veg location phrases cite
the food component and explicitly state that their location wording is compositional, rather than claiming
independent fixed-idiom attestation. Existing gates and flags stay in force.

The `give best` object-binding availability question remains a separate grammatical investigation.
Listener-role handling now binds the listener explicitly and declines partial terminal arguments rather than
borrowing the speaker or dropping another coordinated listener.

The next reviewed mappings also distinguish cans, small bottles and unquantified beer; keep stated
currency, animal species, meal time and event identity. Information nouns and gossip activities have
separate grammatical forms. Uncountable terms use `number: mass`, so spelling alone does not classify
`kid stakes` as plural and a plural subject does not become `the goss were`. Ambiguous source plurals
are withheld rather than repaired by rewriting neighbouring agreement. Count selectors, including numerals
across modifiers, remain countable; mass-compatible quantifiers and container complements remain available.
`Amber fluid` has edited Australian-English mass-noun evidence; container-specific terms remain restricted
to their source shapes. Longer named-beverage concepts preserve compounds such as root beer and ginger beer.
