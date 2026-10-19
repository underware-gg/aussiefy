# DD-030: Share grammatical reading and meaning constraints before selection

Status: Accepted

Date: 2026-10-19

Extends: [DD-010](dd-010-hand-curated-concept-vocabulary.md), [DD-025](dd-025-contextual-imagery.md),
[DD-029](dd-029-changes-builder.md)

## Context

The existing matcher could read an adverb as an object, and an otherwise valid variant could discard a
captured object. Contextual hunger images excluded figurative complements, while vocabulary substitutions
still turned hunger for success into appetite. VP subject binding saw only an adjacent pronoun, hiding
optional images for progressive constructions. Tone already shaped riffs but did not contribute to term
weights before variety limits.

These are shared interpretation and selection problems. Fixing individual strings or adding another
imagery-only parser would distribute the same grammatical knowledge across consumers.

## Decision

- Keep bounded clause-reading helpers in `context.py`, alongside existing sentence and mood reading.
  Detection supplies the POS tags already computed for the sentence. Subject binding passes through
  recognised auxiliaries and adverbs, stopping at lexical verbs and clause boundaries. Binding an agent
  does not give a VP another finite verb or change its replacement span.
- A concept can declare `unless_after`, lowercase complement words that do not establish that meaning.
  Apply this data to exact, direct-entry and similarity matches before overlap resolution. Contextual
  imagery reads the same complement boundary, across soft punctuation within the clause.
  Incomplete document edges and opaque content mean unknown context, not an absent complement; restricted
  meanings stay plain there without reading protected content as prose.
- A noun capture needs nominal or supported gerund structure. Form eligibility requires captured noun and
  object arguments to remain represented by slots or identical literal wording. Binding validity is a
  separate shared check: optional imagery adds to the source, so it need not repeat every source argument.
- Reuse the existing tone/mood weight for terms before variety limits. Existing hard exclusions remain.
  Strict Markdown units receive one document mood from eligible prose rather than recalculating it per unit.
  Planner suggestions prefer the chosen term, then contextual candidate weights; optional images within
  each group prefer fitting tones. The changes builder continues calling canonical eligibility and rendering.

## Consequences

There is no hunger-specific engine branch, second tagging pass, runtime language model, additional dial
or new public toolkit parameter. The controls remain dictionary data and existing resolved policy.

This is conservative bounded interpretation, not full English parsing. Unsupported complements remain
plain; incomplete subject context remains unbound. Lookup is dictionary retrieval, not proof that each
result can replace a particular sentence span. Writer-only imagery remains a rewrite suggestion, with
its usage conditions; binding possessives does not automatically preserve every tense or modal choice.

Changes to eligibility and weights can change seeded output. Read regenerated goldens and change
fixtures for meaning, while retaining deterministic repeatability and source/protected-span checks.
