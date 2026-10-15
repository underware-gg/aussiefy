# Determinism and seeding

The same text, level, vulgarity, other settings and seed always give the same output, on any machine. This is
what makes the golden tests possible, and it is why a user can repeat a run they liked (see
[DD-003](../../architecture/decisions/dd-003-deterministic-context-keyed-rolls.md)).

## Context-keyed rolls

There is no random number generator in the engine. Every random decision is a SHA-256 roll
(`policy.roll(seed, *parts)`) keyed by the seed and that decision's own context: the sentence text, the span,
and the purpose of the roll (whether to substitute, which candidate, which garnish). Two properties follow:

- **Substitution rolls stay local.** An unchanged sentence with the same occurrence count keeps its
  substitution and candidate-pick rolls. Its chosen phrase can still change: earlier sentences affect
  repetition weights and repeated multiword names. Riffs also depend on text mood and shared limits.
  Garnish uses text-wide counts, spacing and a closer keyed to the full text, so editing one sentence
  can change garnish elsewhere. This is repeatability, not a guarantee that all other wording stays fixed.
- **Higher levels raise substitution probabilities.** The roll for an unchanged span stays the same as
  the level rises. This usually adds substitutions, but eligibility and repeat limits can change: if a
  higher level uses a multiword name earlier, a later occurrence may stay plain. Level nesting is checked
  on selected engine test inputs, not promised for every possible text.

The seed defaults to 0, so a text comes out the same on every run. How a user varies the output (the seed and
`--variety`) is described in the [user guide](../user/getting-started.md#get-the-same-result-again-or-a-different-one).

## What stays outside the deterministic core

- **Similarity models.** The engine's detection fallback is character trigrams by default, which need no
  model. A meaning model (`--embedder bundled|local`) is used only when asked, so default translations don't
  change when a model is retrained or installed. See [embedding](../functional/embedding.md).
- **LLM modes.** Claude's replies are not deterministic, so `--rewrite` and `yarn` cache accepted results on
  disk, keyed by everything that decides the reply. A repeated run reads the cache and gives the same text
  offline. See [LLM modes](../functional/llm-modes.md).

## How it is checked

- `tests/corpus/golden.yaml` pins the exact output for every input at every level, and `tests/architecture/test_golden.py`
  compares against it. `scripts/regen_golden.py` regenerates it after an intended change.
- `tests/functional/test_engine.py` checks determinism, that the seed changes the output, and that higher levels
  substitute a superset of lower ones on selected test inputs, and the repeated-name exception. It also checks stable substitution rolls after an unrelated
  sentence edit, and shows that repetition weights can change the chosen phrase with the same roll.
