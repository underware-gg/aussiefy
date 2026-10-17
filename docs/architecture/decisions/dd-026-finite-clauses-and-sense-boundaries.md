# DD-026: Preserve finite-clause grammar and ambiguous senses

Status: Accepted

Date: 2026-10-17

Extends: [DD-001](dd-001-no-nlp-dependency-in-the-core.md), [DD-002](dd-002-slang-is-data.md)

## Context

A clause idiom brings its own finite verb. Inserting it after a retained auxiliary produces forms such as
“can I wouldn't know…”. Mechanical inversion also gives fixed negative idioms a different question force.
Other defects confused wholehearted devotion with truthful assurance, restless tossing with throwing,
object-taking quitting with an intransitive expression, and evidentiary establish with founding.

## Decision

Decline independently finite clause replacements under an outer auxiliary, retaining predicate alternatives.
Invert modular be/have/do and existential clauses through a shared grammatical function. Perfect-have
inverts directly; possession uses do-support. Fixed finite/negative forms without a supported question
representation remain available in declarations and are declined in questions.

Keep sense boundaries in data. Split wholehearted devotion from truthful assurance; preserve ambiguous bare
sincerely, solemnly and establish. Recognise restless tossing as a longer meaning instead of disabling throw.
Use a generic verb/clause-pattern `^end` directive for complete intransitive phrases: a complement is not allowed,
while adverbial tails before a clause boundary remain outside the replacement. Validate directives at load
time and remove annotations consistently before language matching or training.

Preserve shall because future, deliberative and obligatory force cannot be safely inferred from punctuation
alone. Ordinary will contractions continue. No document-type branch or new product dial is introduced.

## Consequences

Some ambiguous words remain plain. This preserves meaning while other configured vocabulary and garnish
can carry flavour. More elaborate idiom question mappings or modal rewrites require explicit grammatical
representations and evidence, rather than guessing a literal inversion. The change does not claim complete
syntactic parsing or universal sense disambiguation.
