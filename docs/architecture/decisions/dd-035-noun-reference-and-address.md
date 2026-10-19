# DD-035: Noun reference and direct address

Status: Accepted; integrated verification in progress.
Date: 19 October 2026.
Extends: [DD-030](dd-030-shared-semantic-context.md).

## Context

The showcase converted “Hi everyone” to “G'day every bugger”. EVERYONE was a quantified noun-phrase
meaning, so candidate selection could not distinguish reference from addressing a group. “Every bugger
came” remains a valid use; globally removing those phrases would lose that distinction.

## Decision

Keep the np frame. Concepts declare optional `noun_use` (any, reference or address). Shared applicability
uses the grammatical role for exact and direct-entry detections; arbitrary `replaces` cannot bypass it.
EVERYONE is referential. PLURAL_ADDRESS supplies plural recipients, while existing YOU_PLURAL remains
available outside greetings.

`takes_addressee` marks dictionary expressions that can introduce a recipient. The shared grammar reads
that capability, punctuation, known names/recipient shapes and clear commands. It does not infer address
from any interjection, a comma or a second-person pronoun alone. Ambiguous roles satisfy neither restricted
use. Reference requires positive attached-predicate or governed-object evidence, with visible finite
morphology corroborating POS tags. Partial modifier spans and unresolved recipient prefixes stay unknown;
ordinary unrestricted concepts such as FRIEND keep their existing uses.

## Consequences

Simple group greetings and commands get natural plural forms. Parentheticals, qualified recipients and
unparsed coordination conservatively retain source wording. Positive role evidence separates later commands/questions from directly attached reference predicates. No complete discourse/parser claim
is made, and wider coverage can extend the same reader. The website needs no special replacement table.
