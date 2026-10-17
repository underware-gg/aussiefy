# DD-029: Render each alternative in place, in the same pass, behind a pass observer

Status: Accepted

Date: 2026-10-17

Extends: [DD-003](dd-003-deterministic-context-keyed-rolls.md), [DD-008](dd-008-one-toolkit-thin-surfaces.md)

## Context

The aussiefy website lets a reader edit their own translation. Each change shows its alternatives, already
rendered in context, and swapping one in changes only that spot. A pick is more than `realise(entry, form)`.
The splice path also picks a spelling, fits the article, takes an entry-dependent span, may stack a second idiom
or add a riff, and the drawl and swear-infix pass runs over the whole output afterwards. Its rolls are keyed by
each rule's occurrence count. Re-rendering a spot after the pass loses the state the spot was rendered with. A
whole re-render for each alternative costs 15 to 45 translations for each text. Changing the keying would change
every output.

## Decision

`aussiefy/changes.py`, in the engine layer, builds the changes in the same pass as the translation. The engine
exposes hooks that don't change its output:

- `render_at_spot`: the splice path, shared by translate and the builder.
- An optional `PassObserver`: a snapshot of each spot at its pick, each sentence's splices and garnish (with the
  `GarnishOffer` each garnish was picked from: its pool, weights and key), the closer, and a trace of each
  phonetic rule's pass.
- `replay_garnish`: garnish placement that reports where its words went.
- `phonetic_admits`: the one gate on each phonetic match (a question, the words before it, kept and preserved
  spans), which the engine's pass and the builder's pass both ask.
- `eligible`: selection's checks, which the builder runs again with only the vulgarity cap raised for `locked`.

The builder renders each alternative on a copy of the state at its spot. It puts the sentence's garnish back as
decided, then runs each phonetic rule over the spot's region alone. That pass starts from the rule's count in the
unchanged text before the spot and reads the whole text's context. A region widens a word where a match crosses
its edge or a neighbour's lookaround reads it. A spot's options share one region. Where the pick's own rendering
isn't the output over its region, or a match still crosses its edge once it can widen no further, the swap offers
the pick alone and the response names it under `withheld`, so a swap that may read wrong is never offered.

Garnish is held to the same rule. Each garnish the engine weighed, the pick and the removal included, is told with
the sentence's other garnish and put through its region's phonetic pass; a contextual image and the closer too. A
placed garnish's region widens as a swap's does, by the same rule and cap, a word at a time, and over another
change's words whole rather than cutting them: "Well, it is", where a connective's region would end at "it", the
word it lowers, takes in "is". Where the pick doesn't read as the output there, or a match still reads across the
region's edge, the garnish offers its pick alone, without its removal, and is named under `withheld`. So a
garnish's `removed` is optional in the schema, present unless the garnish is withheld. Without widening, about
one garnish in 27 over the everyday corpus was withheld this way; with it, none is.

A locked option is an entry rated above the cap in effect that selection takes with only the cap raised: raising
the cap reweighs swearing in, so variety's best few can take in a clean entry, which isn't locked. Locked options
render at the reader's cap, with the riffs and infix rates the reader's vulgarity allows, as the page shows them
before they're unlocked. At Dad, "very cold" as fuckin' reads "fuckin'", though a whole re-render at Uncle Bob
would read "cold as fuck".

The output is the `changes` contract, version 1, with a JSON Schema in the package. Version 1 was amended before
release, as this review found: it gained `withheld`, and a withheld garnish has no `removed`. It was amended
again, unreleased, after the website's service found a connective's region overlapping a neighbouring swap's.
`covers` had listed only the changes nested inside a region. It now lists every change whose output or region
overlaps one of the change's regions, so two changes whose regions overlap list each other. A drawl, spelling or
infix change's `rule` also gained `min_level`. Ids are each change's
kind and source span, made by one format (`changes.ID_FORMAT`). Every rendering lists its maskable words, and only profanity is masked: swear-list words, the
compounds the dictionary's rated words build on one, and the profane words an entry authors (`mask`). An entry
whose rudeness is innuendo, an insult or a crude word is marked `profane: false` and shows in full.

It's offered as `aussiefy.translate_changes`, with translate's parameters, and not on the CLI, the MCP tools or
yarn mode. This departs from DD-008's surface parity on purpose: the contract serves a host that edits a
translation in place (the website's service), not an agent writing one.

A test-only pin hook, an observer that forces a pick or garnish, checks every rendering against a whole
re-render with that pick.

## Consequences

- Translation output and seeds are unchanged, with or without the observer. A byte-identity test and the golden
  corpus hold this.
- A swap is local. It reads as a whole re-render would over its region, while later picks and rolls, which a
  re-render would shift, stay as they were. Two swaps can interact only through the state one leaves for the
  other: the entries a later stack or riff may use.
- A change's `covers` lists every other change whose output or region overlaps one of its regions: the changes a
  swap or removal of it rewrites text under. That includes a drawl or infix inside a swap, and a neighbour whose
  region overlaps its own. A garnish region can take in a whole swap, and "Anyway, he's" shares "he's" with the
  swap that starts there. Two changes whose regions overlap cover each other. So, through their regions,
  neighbouring changes are either independent or listed as covering each other. The state one swap leaves for
  another, above, is not covered. A change with no region (a drawl, an infix, a US word) covers nothing.
- A drawl or spelling rule's `min_level` is the level it starts at, as `phonetic.yaml` gives it. A swear infix has
  no level: the vulgarity and the embellishment let it in at any level. The loader refuses a `min_level` on an
  infix rule, and `PhoneticRule.is_infix` decides a rule's change kind, its `rule.kind` and the engine's gate.
- The budget is 1.5 times translate for each 5,000-character text, for every setting the website's service allows
  (its default, the strongest dials, each document type it offers). `scripts/benchmark_changes.py` gates on it,
  timing translate and `changes` in turn in process time. At the website's defaults it costs about 1.1 times.
  Garnish alternatives and removals take a share of the headroom alongside the swaps'. The budget doesn't apply to
  Markdown documents, which the website doesn't take, nor to larger texts or a stress setting with every garnish
  at full rate: those are reported.
- A phonetic rule whose lookaround reaches further than the builder's context window (64 characters), or across
  sentences, would break the region pass. The pinned re-render tests over the everyday corpus catch it.

Tests: [the contract](../../../tests/functional/test_changes.py),
[pinned re-renders](../../../tests/functional/test_changes_oracle.py),
[engine hooks](../../../tests/architecture/test_engine_hooks.py).
