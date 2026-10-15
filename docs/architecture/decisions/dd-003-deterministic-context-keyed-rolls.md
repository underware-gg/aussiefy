# DD-003: Deterministic, context-keyed rolls

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13. Both design reviews of 2026-10-12 name it as a strength to keep.

## Context

Translation needs randomness: whether to substitute a span, which of several fitting idioms to use, which
garnish to add. But users want to repeat a result they liked, tests need to pin exact outputs, and a change to
one sentence should not consume random draws that reshuffle later sentences. A shared random number generator gives none of these,
because every draw depends on every draw before it.

## Decision

Every random decision is a roll computed from a hash: `policy.roll(seed, *parts)` takes SHA-256 of the seed and
the decision's own context (the sentence, the span, the purpose of the roll) and maps it to a number in [0, 1).
The seed defaults to 0. There is no other source of randomness in the engine.

## Consequences

- The same text, level, settings and seed always give the same output, on any platform, so `golden.yaml` can
  pin outputs exactly.
- An unchanged sentence with the same occurrence count keeps its substitution rolls. Chosen phrases
  can change with earlier entry use, and riff and garnish placement depend on shared state and text mood;
  edits do not guarantee identical wording elsewhere.
- Raising the level raises substitution probabilities with the same rolls. This usually adds swaps, but
  changing eligibility and text-wide repetition limits can leave a later occurrence plain at a higher
  level; nesting is a checked example property rather than a universal guarantee.
- The engine is testable without mocks.
- Anything non-deterministic (similarity models, Claude) has to stay outside the default path or be cached:
  see [DD-007](dd-007-pluggable-local-embeddings.md) and [DD-009](dd-009-llm-output-accepted-only-when-checked.md).
