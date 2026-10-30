# DD-052: Separate source evidence from output grammar

Status: Accepted implementation of ED16 E1–E7 (Rob, Q48–Q58)
Date: 2026-10-30
Extends: [DD-044](dd-044-phrase-interpretation-context.md), [DD-049](dd-049-phrase-fences.md),
[DD-051](dd-051-independent-phrase-ownership.md)

## Context

An adjective such as cooler could establish a container meaning, and broad aliases confused sympathy with
remorse or a present with aptitude. Lists of following words mixed lexical expressions, source meanings
and output grammar. The compound trial also rejected natural footy matches, choccy bickies and nan's bed.
Correctly recognising a meaning does not prove that every synonymous phrase fits the sentence.

## Decision

Extend the existing shared reader, preserving separate meaning, ownership and output-fit stages:

- Source role evidence combines tags, determiners, possessives, adjective roots and predicate context.
  It distinguishes noun heads, modifiers, possessors, adjective uses and unknown roles. It is not a
  default compound ban. A concept can declare the nominal roles its meaning supports.
  Selection reuses an established head/possessor role instead of treating a complete noun phrase
  before an ordinary finite verb as an unfinished adjective phrase.
- Typed source-context conditions establish a preposition and argument, with reviewed head, action or
  person evidence where needed. Supported, contradicted and uncertain readings remain distinct.
  Lookup receives rejected senses too. Uncertain contexts retain the single holding meaning, while
  evidence-only arguments keep their independent readings.
- Entries independently declare required or forbidden following shapes, count/mass requirements and
  state/event or voice needs. Evidence is computed once for candidates at the same spot. Missing
  metadata adds no check; uncertain evidence for a declared requirement rejects that candidate.
  Existing alternatives are tried before leaving the wording unchanged.
- Actual lexical units move from trigger exclusions into shared fences with their scopes. Semantic
  and argument exclusions remain when general evidence has not replaced them. Retire a protection
  only after its negative cases and valid neighbouring uses pass together.

Anticipation uses participial `hanging out` with an external for/NP or to/action complement, retaining
the copula and separate evidence for each use. Existing negated-predicate abstention is unchanged.
The three narrowed meanings retain their existing IDs and plain labels. DD-046 ranking, source-match
identity construction and the planned slice-6 lookup outcome are unchanged.

## Consequences

Reviewed corrections can strengthen reusable dictionary conditions with positive/negative examples,
rather than adding sentence replacement code. Feedback remains review material, not an automatic
dictionary mutation. Coverage reports measure annotations, not accuracy. The bounded reader does not
infer arbitrary semantic domains, dependencies or agency; unknown cases remain conservative.

The 704 retained phase-B cases distinguish forbidden candidate exposure from functioning positive
controls. A fixed 20-entry pilot exercises curation and retains its findings and timing limits. Its
selection is disproportionate and cannot establish whole-dictionary accuracy or human curation cost.
The initial annotations are deliberately incomplete; this does not commission the full curation round.

Existing fence reasons and waiting-meaning labels remain under their separate W1/W2 review. Newly
introduced lexical units have their own scoped reasons; they do not apply the pending wording drafts.
