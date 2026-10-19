# DD-037: Contextual matching and discovery-only meanings

Status: Accepted; integrated verification passed.
Date: 19 October 2026.
Extends: [DD-030](dd-030-shared-semantic-context.md).

## Context

Source corrections expose useful distinctions that whole-phrase replacement can erase: “walk home” must
retain home, and an electronic antenna must retain its car/radio/satellite qualifier. Multiword expressions
can also require a real object rather than accept a temporal or quantity adjunct. Some meanings remain
useful for discovery even when plain wording cannot establish a safe automatic use.

## Decision

Extend the existing matcher with one-token nonconsuming context assertions: `?=home|there` checks following
context; `?<=radio|car` checks preceding context. Both remain enforced during approximate matching. They
are excluded from consuming verb/noun-head selection and canonical translated-content cleanup. Alternate
plural spellings extend the existing morphology boundary without changing the preferred output spelling.

`^object` requires an `{np}` capture and delegates to the shared unanchored-object reader. Temporal and
quantity-only adjuncts do not establish the object; an explicit content noun remains valid. Existing
argument-completion checks continue to decline unsupported coordinated/partial objects.

Concept `lookup_only` is an explicit boolean. Such meanings establish no automatic trigger or direct-entry
replacement, but retain form recognition and writer discovery. Mixed entries retain other eligible meanings.
The loader distinguishes intentional discovery from accidentally unreachable vocabulary. Existing statuses,
flags and registers remain independent.

## Consequences

Dictionary patterns preserve destinations, qualifiers, inflection and object roles through shared seams.
No slang ID enters the grammar. General work/artwork/childbirth ambiguity is conservatively left unchanged;
yakka remains discoverable and available for explicit hard work. Wider noun-sense and coordination coverage
can extend these readers later without requiring an accumulating phrase-specific replacement table.
