# DD-050: Ordinary waiting meanings and contextual eagerness

Status: Accepted for ED16 phase A2; output-complement grammar remains a phase B trial
Date: 2026-10-27
Extends: [DD-049](dd-049-phrase-fences.md)

## Context

Seven remaining records used `no_entries` for real meanings. Rob approved listing six as waiting for a
word and moving the seventh, EAGER_FOR, into EAGER. A grammatical source reading must not become
abstention merely because the available output has a different frame. “Dying to see it” needs the
adjective “keen” while retaining “to”; blindly replacing the old verb span would drop the preposition.

## Decision

HEARTBREAK, FREEDOM, FEEL_SORRY, UNEMPLOYED, GET_EXCITED and GIFT_TALENT become ordinary meanings with
plain wording and reviewed examples. Keep their existing scope and source restrictions. Freedom is not
merely fair treatment; being unemployed implies neither benefits nor avoidance of work. The gift of
the gab moves to a set-phrase fence. `no_entries` is no longer a core or extension field, even as false.
Only the named abstention concept takes no entries, images or constructions.

EAGER's verb patterns read `die ?=to@4` and `die ?=for+a@4`. Literal context assertions may join words
with `+`, reading them without consuming them. The longest matching assertion alternative supplies the
evidence extent; unknown, missing or interrupted words do not match. Existing single-token assertions
keep their semantics and set-membership path. Multiword alternatives are prepared once per element.
The same literal assertion grammar applies before and after a matched span.

The keen entry supplies predicate-adjective `replaces` patterns for the progressive wording. On equal
evidence and span, the existing entry-before-trigger ordering chooses that fitting direct mapping over
the generic verb reading. No change to overlap ranking or hard-coded slang rule is needed. Other verb
forms still establish EAGER: if no permitted entry fits their frame, translation preserves their words;
lookup still recognises their meaning. A longer thirst reading retains precedence for “dying for a drink”.

Add sourced “hang out for” and “hang out to” as verb-phrase vocabulary on EAGER. Use the existing manual
curation gate pending the output-complement grammar trial, and document the reason in their notes.
`include_gated` makes them available for writer review; they are not automatically enabled or given an
incorrect adjective frame. Evidence remains separate: the current provisional weights label both
unverified, with scores 7 and 3; multiple ABC articles count as one publisher vote.

## Consequences

The waiting list grows from 21 to 27. Lookup returns `no_word_yet` through the six meanings' new plain
wording and examples; heartbreak never becomes ticker. All source and output grammar remains data-driven.
The assertion extension is general pattern grammar, not a per-phrase engine exception. Phase B measures
output grammar and decides what is needed before the new vocabulary's manual gates can be lifted.
No near-meaning ranking change or new lookup outcome is introduced here.
