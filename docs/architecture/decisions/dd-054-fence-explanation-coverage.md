# DD-054: Phrase-level explanation coverage and fixed heads

Status: Accepted implementation of R74 and the W1 per-phrase check
Date: 2026-11-03
Extends: [DD-049](dd-049-phrase-fences.md), [DD-053](dd-053-discovery-reading-contract.md)

## Context

R74 approves 14 short explanations. Most other protections can show only their derived reading, but
a group's evidence does not establish every real phrase form. Some apparent gaps are existing meaning
or grammar checks working correctly. An NP-shaped fence can also protect a fixed clause or adverbial
expression; automatically pluralising its last word generates false witnesses such as “hands downs”.

## Decision

Allow an empty reason after every real form has its own derived reading. Retain sentences for the six
held W1 groups and for other unproven forms pending curation. Audit and regression checks require every
generated matched form to have a sentence or evidence. Missing evidence never deletes a protection or
justifies weakening source checks. Contextual authored examples may demonstrate a genuine effect.

Let fences opt out of head inflection through `inflect_head: false`, using the shared compiler. Their
written alternatives, slots, frames and scopes remain intact. Real noun/verb heads retain the default
inflections. This is curated pattern metadata, not a guessed POS filter or a list of engine exceptions.

Verify accepted whole-expression readings end to end through concept triggers and entry replacements.
The existing independent ownership rule already permits them while blocking partial/crossing readings,
including when dials exclude the whole entry. No new priority exception is needed.

## Consequences

The public lookup contract permits an empty `reason` and `note` when the derived line explains the
phrase. The CLI does not print an empty explanatory sentence. The audit adds `unexplained_variants`;
the bundled dictionary requires zero. Its bounded probes remain diagnostic rather than proof about
every possible sentence. The old audit's counts may change as false witnesses are removed and genuine
contextual ones added; curator follow-ups remain separate from approved copy.
