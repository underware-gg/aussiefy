# DD-053: Explain deliberately preserved lookup queries

Status: Accepted implementation of the slice-6 lookup contract (R70/R71)
Date: 2026-11-02
Extends: [DD-028](dd-028-hosted-mcp-capabilities.md), [DD-045](dd-045-explicit-dictionary-exploration.md),
[DD-046](dd-046-lookup-meaning-evidence.md), [DD-049](dd-049-phrase-fences.md)

## Context

A deliberately protected expression returned a settings failure rather than explaining why it was
preserved. A fuzzy lookup guess is not evidence of the reading a protection rules out. The evidence
builder now establishes those readings, but a full audit per request is unnecessary work. Some retained
protections have no demonstrable exact alternative reading and must remain honest about that (R71).

Entry-detail discovery already exposes structured evidence that lookup's older cards omit. Hosted
discovery of marked vocabulary is also coupled to permission to unlock automatic translations.

## Decision

- Use one discovery-outcome vocabulary. A query whose established head readings are all protected or
  unresolved returns `left_as_written`, with current reasons, source spans and derived `ruled_out`.
  Direct dictionary expressions remain discoverable. Incidental protections cannot determine the
  outcome of a query with another independent meaning. DD-046 ranking and wordless outcomes stand.
- Represent ruled-out meanings by ID and dial-compatible headword cards, and dialect protections by
  their guarded swaps. Keep an empty list when no exact reading can be established; never promote
  rejected fuzzy suggestions into source evidence. Keep a wordless alternative's real meaning ID.
  Display names belong to the separately reviewed slice-7 model.
- Build evidence lazily per protection, with a bounded cache owned by the loaded dictionary. The
  batch audit uses that same index. Cache immutable evidence, not request-specific cards; each request
  reapplies its dials, metadata checks and per-meaning word limit. Ordinary translation invokes none
  of this work, and dictionaries never share the cache.
- Keep evidence per matched literal phrase, normalising captured grammar slots and retaining literal
  assertions. A grouped fence cannot lend one alternative's reading to another, such as HORSE to
  gift shop. The audit retains its aggregates and adds per-variant evidence and missing-effect flags.
- Share rich discovery cards, including structured sources, evidence, attestation, tag tiers and
  minimum default vulgarity. Resolve explicit/default tag tiers with the same rule policy uses.
  Preserve changes-v2 cards until the coordinated 3+6 contract bump; do not add an intermediate bump.
- Return `match_kind` independently of display wording. A model boosting a qualifying meaning match
  does not make it model-only. Discovery responses identify the loaded dictionary.
- Gate `include_gated` separately through `allow_include_gated`; translation unlocks retain their
  own capability. Hidden arguments and their descriptions stay hidden, with closed defaults.

## Consequences

Callers can distinguish preservation, uncertainty, missing vocabulary and dial rejection without
parsing prose. Several protections keep separate reasons and combine their cited meanings. Empty
evidence is an audit input, never an automatic deletion instruction. Existing reasons remain untouched
until marked replacement copy arrives.

Discovery's richer card is shared by lookup and entry pages. The changes-v2 adapter has a real existing
consumer and is removed or converged when the planned changes-contract bump lands. The source reader,
vocabulary, translation rolls, attestation weights and term placements are unchanged by this contract.
