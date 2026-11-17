# DD-060: sentence wording follows actual source scope

Status: implemented on dev, 15 November 2026. Frozen v4 response schemas are unchanged.

Display names cannot establish sentence grammar. A noun reading may consume a finite predicate while
its possessor stays outside the span; authored wording may lose negation or replace could with can.
Checking the pattern's possible words cannot establish which operators the source actually used.

English choices now derive one internal WordingScope from the actual tokens and existing tags. It
tracks consumed finite predicates, grammatical operators, bound arguments and an external owner.
An explicit possessive slot may absorb a clearly identified pronoun or simple named possessor using
the existing per-option widened span. Ambiguous compound ownership declines that widening. If the
owner stays outside, an extra determiner or verbal fragment is rejected.

Existing auxiliary slots retain their captured source surface, including adjacent not/never and
number/tense, only for scoped English candidates. Ordinary dictionary realisation is unchanged.
Actual modal and negative signatures must remain compatible, with argument boundaries and negative
carriers retained. Lexical have/do and nominal being are not automatically grammatical auxiliaries;
lexical negative concepts are not equated with a literal grammatical not. Suspected source predicates
use conservative morphology, while a target needs positive evidence of finiteness. Unsupported
negative inversion or ambiguous scope preserves source rather than inventing a successful rendering.

These are necessary grammatical checks, not proof of semantic equivalence. Curators still author the
wording. At the 15 November checkpoint HEARTBREAK, HEART_EFFORT and DOUBT_IT remained source-preserved;
no phrase-specific wording, dictionary patches, new public fields or share-pin protocol are added.
The source sentence's case and existing literal protections remain in force.

Tests use unrelated nouns and predicates through the actual spot renderer, possessive pronouns and
proper names, compound-owner refusals, contractions, singular/plural agreement, negation addition/loss,
argument-boundary movement, could/can/would contrasts, inversion and participle/finite distinctions.

## Approved completion, 17 November 2026

Rob R79 accepts the three source-preserved examples for Gate 4; R80 approves applying faithful authored
forms without another curation/review round. The shared scope binder now lets an explicitly authored
clause bind a clear external possessor as its subject (her to she, or Rob’s to Rob). A missing/ambiguous
owner is never replaced by a guessed you. The auxiliary re-agrees with that explicitly bound subject
(“Your heart was” to “You were”, “My heart is” to “I am”), retaining tense and negation. Only this
owner-to-subject case compares finite auxiliaries by lemma and tense; actual modals remain exact.
The existing per-option span absorbs that owner. Internal
validation and realisation use the clause frame for these finite noun-reading sentence forms; the frozen
v4 response schema is unchanged. Nominal clauses also retain progressive aspect conservatively.

The data now renders “She was heartbroken”, “She was not engaged in it”, and the source’s actual
could/would clause for DOUBT_IT. These are authored meanings, not phrase-specific engine branches.
All 45 authored examples render in the completion audit. Uncertain contractions, compound owners and
unsupported aspect still keep source. Tests use the real spot renderer and unrelated owner/property
examples, as well as the three requested cases.
