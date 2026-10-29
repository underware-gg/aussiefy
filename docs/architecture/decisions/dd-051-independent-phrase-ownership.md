# DD-051: Phrase constraints survive partial readings

Status: Accepted implementation of ED16 E6 (Rob, Q56)
Date: 2026-10-29
Extends: [DD-044](dd-044-phrase-interpretation-context.md), [DD-049](dd-049-phrase-fences.md)

## Context

The shared reader selected one non-overlapping set of detections before replacement eligibility.
A partial direct-entry match could defeat an equally wide phrase fence: “the road” displaced
“road pavement”, allowing its remaining “pavement” component to become “footpath”. Output availability
must not decide source meaning, since an ordinary meaning without an Aussie word still owns its words.

## Decision

Before readings compete, every detected meaning fence constrains overlapping consumed spans.
A component or crossing reading that does not cover the complete protected expression is excluded.
A supported whole-expression reading may still compete normally, preserving intentional overlaps
between fences and complete idiom entries. No new priority for all fences or all direct entries is added.

The constraint uses consumed words, not the wider evidence extent. A pattern can read an object as
context without claiming its words, so that object retains its independent meanings and replacements.
When overlapping fences compete, their superseded senses propagate to the surviving reading for
lookup to reject too. Only readings that survive these constraints participate in same-span merging.

The existing `read_meanings` owner supplies both translation and lookup. Fence meaning/dialect and
document-domain scopes are unchanged; this does not merge their distinct projections. No new lookup
outcome, source-match identity, compound permission or public setting is introduced.

## Verification

Paired tests cover the crossing road-pavement defect, a complete expression entry, independent context
objects and rejected senses under overlapping fences. The 704-case ED16 B dataset changes only the
road-pavement output; protected negatives expose no forbidden candidate under its fixed settings.
The golden translation corpus remains unchanged. Later C work adds source roles and typed grammar;
this decision does not claim those are already implemented.
