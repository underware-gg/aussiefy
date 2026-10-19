# Contextual lookup, 20 October 2026

The baseline diagnostic found wrong meanings through both lexical and model lookup. The repair is source
meaning evidence followed by candidate paths, not query-specific Python mappings or a claim that a refit
alone fixes semantic inference. No historical ranking labels or thresholds are changed.

## Corpus additions

- PROBABLE establishes likelihood without certainty. It has no certified automatic target.
- WAKE_UP establishes becoming awake, with no certified automatic target. Hurrying is a different meaning.
- POSSIBILITY establishes an option that has not been ruled out, including the internally negative wording
  `not impossible` and `not out of the question`. It does not establish categorical impossibility.
- DIFFICULT establishes that something is difficult or `hard ?=to` do. Ambiguous bare hard, `hard at work`
  and material hardness are not certified as difficulty. It does not establish finishing, eating or working hard.
- WORK_HARD gains `work hard ^end`, including the matcher's ordinary verb inflections. The clause-end
  assertion prevents a new rewrite from stranding dependent `enough`, infinitival and prepositional tails;
  a genuine coordinated clause remains eligible under the existing boundary rule.

These are ordinary source-meaning distinctions. No new slang is invented or asserted as attested. They
supply reusable concept data and allow overlays to add reviewed targets through the normal dictionary path.

## Evidence and scope

`detect(fragment=True)` is an explicit toolkit use of canonical detection. Ordinary automatic detection
keeps `fragment=False`. Query-local predicates may be bare, attributive or coordinated, but never gain a
fabricated subject or linking verb. Degree certificates, source-specific effects and argument restrictions
remain dictionary-owned. Complete/unknown noun usage remains separate from direct term discovery.

Detections are positive local evidence, not an exhaustive parse. Lookup's small scope rule may constrain
an entire query only when a recognised head accounts for its grammatical envelope. It includes owned
degree qualifiers, leading determiners and actual captured subjects/verbs. A bounded infinitival or nominal
prepositional tail can belong to that head; IN tagging alone does not prove a preposition. Additional
recognised predicates, subordinate structures, unknown modifiers and unresolved coordination cause
non-exhaustive fallback instead of a global veto. `a melancholy man` must not let MAN exclude all mood terms.

External polarity reuses `positive_context` before each source phrase. This catches `not a tired man` and
`not excellent`, while retaining the established meanings of `not bad`, `not working` and `not impossible`.
A positive occurrence after a denial provides its own path; a query-wide blacklist would lose it.

Candidate eligibility, lexical concept scores and model texts follow the same permitted concept paths.
An unrelated second label cannot rescue a denied meaning. When only one sense of a multi-sense entry is
permitted, its mixed gloss is not used to smuggle another sense back into ranking. Explicit source degree
needs a matching certified bare target grade for inferred lookup. Direct, inflected and partial slang-form
searches remain broader explanations of vocabulary, rather than certified in-place replacements.

Recognised meanings without a compatible option explain abstention separately from an unknown/unvetted
term. Unknown source wording still has model fallback: these rules are not a universal sense classifier.

## Review evidence and remaining limits

The independent review reproduced and closed partial-reading vetoes, multi-sense denial bypasses,
negation before determiners/other frames, swallowed predicate content and coordinated degree ownership.
Synthetic overlay and controlled-model tests verify that these are general mechanisms, not hard-coded
examples. Root integration and full-suite results are recorded in the accompanying review and plan.

Corpus restrictions for figurative `sick of work` and `tired of life`, and better inference for unsupported
queries, remain separate follow-ups. Existing broad sense ambiguity is not silently certified by this
lookup change. Model refresh and measurements compare the same final runtime with both old and new models,
so policy improvements are not misattributed to weights.
