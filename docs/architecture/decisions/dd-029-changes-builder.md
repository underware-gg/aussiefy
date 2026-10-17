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
- An optional `PassObserver`: the state at each pick, each sentence's splices and garnish, the closer, and a
  trace of each phonetic rule's pass.
- `replay_garnish`: garnish placement that reports where its words went.
- `eligible`: selection's checks, which the builder runs again with only the vulgarity cap raised for `locked`.

The builder renders each alternative on a copy of the state at its spot. It puts the sentence's garnish back as
decided, then runs each phonetic rule over the spot's region alone. That pass starts from the rule's count in the
unchanged text before the spot and reads the whole text's context. A region widens a word where a match crosses
its edge or a neighbour's lookaround reads it. A spot's options share one region.

The output is the `changes` contract, version 1, with a JSON Schema in the package. Ids are each change's kind
and source span. Every rendering lists its maskable words.

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
- Nested changes are listed in `covers`, so a page drops a drawl or infix that a swap replaces.
- At 5,000 characters, `changes` costs about 1.1 times translate at the website's defaults, and about 1.3 times
  with every garnish placement on (`scripts/benchmark_changes.py`).
- A phonetic rule whose lookaround reaches further than the builder's context window (64 characters), or across
  sentences, would break the region pass. The pinned re-render tests over the everyday corpus catch it.

Tests: [the contract](../../../tests/functional/test_changes.py),
[pinned re-renders](../../../tests/functional/test_changes_oracle.py),
[engine hooks](../../../tests/architecture/test_engine_hooks.py).
