# DD-022: Sentence-safe document flavour

Status: Accepted

Date: 2026-10-15

Extends: [DD-020](dd-020-document-composition-state.md), [DD-021](dd-021-request-local-profile-overrides.md)

## Context

Reviewing the generated docs found translated technical examples, inappropriate person swears, erroneous
contractions and case after prefixes. Blanket suppression of incomplete Markdown units also blocked safe
leading garnish at real sentence starts. More drawl or a higher dial could not fix these separate concerns.

## Decision

Tune publication through its existing advanced configuration, retaining Swaggie/Dinkum/Dad. Preserve quotes,
technical vocabulary and neutral people; permit connective/opener/tag colour with explicit rates, caps and
spacing, without factual riffs, insulting garnish, infixes or idiom stacking. Public preset defaults remain.

Separate structural quiet from placement eligibility. Strict Markdown supplies complete source-sentence
contexts and document-wide written-word evidence. An incomplete unit may receive only leading garnish when
it genuinely starts a source sentence. Continuation units, structural quiet regions and held quotes cannot.
Tails, tags and riffs do not attach to incomplete units. Shared source ordinals, limits and local offsets
remain intact. If first-word casing cannot be resolved safely, decline a prefix rather than force a case.

Phonetic rules may declare an `unless_before` regular expression. The generic engine skips a match whose
preceding grammatical context matches it; the concrete fronted-predicate exception stays in data. Ordinary
contractions remain available. Context guards and malformed regexes are validated by the dictionary loader.
Narrow dictionary guards protect relative links and pronouns that introduce relative clauses; the Technical
terminology domain protects liberty used as a dial concept.

When existing finite-word hints do not apply, fragment inference also accepts finite present-tense clauses
with an explicit noun/pronoun subject and POS evidence for a finite verb. Negative cases for this fallback
cover noun/gerund phrases, relative clauses and subordinate clauses alone. Existing hint-based inference
remains. The POS tagger supplies evidence; uncertain parses stay conservative. Fronted
how/where/who/what predicates, comparisons and ordinary auxiliary uses have paired regression cases.

## Consequences

The docs can gain conversational colour around markup while retaining exact technical examples. These
changes are verified with isolated positive/negative cases and a reviewed generated diff. They do not claim
complete English parsing: POS-based fragment inference and stressed-auxiliary coverage remain conservative.
A separately frozen, blind writer/judge study assesses retelling quality after these fixes.
