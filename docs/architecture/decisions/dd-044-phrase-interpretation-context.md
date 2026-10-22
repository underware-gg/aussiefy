# DD-044: Phrase interpretation by evidence, separate from replacement span

Date: 2026-10-22

Status: Accepted implementation decision; vocabulary placements are curator proposals pending Rob's review.

Extends: [DD-026](dd-026-finite-clauses-and-sense-boundaries.md), [DD-037](dd-037-contextual-matching-and-discovery.md)

## Context

A high-dial reference audit found component words translated under senses their phrases rule out:
“believe a liar” became “reckon”, “thought so much of new clothes” became “reckoned”, and “fantastic
terrors” became “ripper terrors”. Overlap resolution kept the longest span and merged the concepts of
identical spans. Longest-match exclusion cannot let context establish a meaning without also claiming
the context's words for replacement. A consuming `believe {np}` would erase the independent `a liar` →
`a bullshitter` swap. Merging a contextual sense with a bare one on the same word made the excluded sense
a candidate again.

## Decision

Keep one detection stage and one overlap resolution. Distinguish a reading's span (the words it claims
and may replace) from its evidence (the span plus the context it rests on).

- The matcher records the context its zero-width assertions read. The new `?={np}` ends a pattern and
  reads a following nominal object without consuming or capturing it. The shared clause reader validates it
  with the unanchored-object checks. Trailing adverbs stay outside the object. Clause and non-nominal
  complements are rejected, and so is the subject of an infinitive. The similarity fallback does not use
  such patterns.
- Overlap resolution ranks readings by evidence width, then span length and the existing tie-breaks.
  Spans still decide which words a reading holds, so a reading's context remains available to the
  context's own readings. Identical spans merge only on identical evidence; wider evidence supersedes
  readings of the same words. Each kept reading records the concepts it superseded, which explain mode reports.
- A concept without replacement entries holds its reading. Exclusion happens before selection, so neither
  missing candidates, dials nor substitution rolls can restore an excluded sense.
- A `so`/`too`/`such` inside a claimed span, with its `that`/`to` complement immediately after the reading,
  must appear in any replacement form. Negation, tense and objects outside the span keep the existing controls.
- Linguistic knowledge stays in data. `ACCEPT_AS_TRUE`, `FANCIFUL` and the evaluative “think … of”
  concepts are entryless concepts with context triggers. The evaluative concepts are `REGARD_HIGHLY`,
  `REGARD_POORLY`, `OVERVALUE` and `NO_HARDSHIP`. Each keeps one polarity, so a future entry cannot flip
  or flatten the source's regard. No slang ID, sentence or reference text enters the engine.

## Consequences

Translation, the changes builder, plans, lookup and semantic checks read the same resolved readings. An
existing reading changes only where an assertion widens its evidence over a rival on the same words. Existing
candidates change only where a claimed result degree rejects a form that would drop it. Readings
established this way need reviewed patterns, and mixed evidence prefers preservation over a confident sense.
A whole-phrase entry that captures an `{np}` re-inserts it as written. Composing inner swaps into a
captured argument is not implemented. Dictionaries and overlays that use `?={np}` need an engine
with this decision. The `supersedes` key in explain records is additive. The changes
contract is unchanged. Whether to ship replacement entries for the new senses is a curatorial decision.
