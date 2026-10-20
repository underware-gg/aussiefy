# Design review: community dictionary metadata, 21 October 2026

Surface: package slice 0, from `dddf3cc`: stored term facts, derived evidence, the mixed-flag migration,
structured sources, wording grades, importer/provenance consumers and generated documentation. One
independent reviewer assessed all six software-design concerns and re-reviewed the fixes.

## Findings

No remaining design findings. The final full suite passed 3,391 tests, with only the two expected
local-corpus skips. Ruff, documentation generation/check and tracked provenance checks passed.

The review identified and resolved these concrete gaps:

- Riff currency needed the shared metadata parser rather than accepting unvalidated register values.
- Selection needed the continuous score, rather than its rounded bar count, to reward additional evidence.
- A testimony citation without a testimony summary was uninterpretable; the loader now rejects it.
- Malformed search outcomes needed contextual schema errors, and dates need canonical spelling.
- Scrape review needed structured citation merging; the MCP unlock enum needed the new shared values.
- Lint needed to retain foreign-expression findings while excluding eligible general English.
- Old flag advice and a contradictory omission note needed correction after the migration.
- Garnish needed the same evidence and general-wording factor as substitutions. Both now call
  `Effective.metadata_weight`; placement probabilities and seeded roll keys remain unchanged.
- The golden review exposed quote-dependent agreement detection: curly dialogue quotes allowed
  “Very well” to fall through to an intensifier. The generic clause boundaries now recognise equivalent
  straight/curly dialogue, while an adjacent possessive apostrophe cannot start a new clause.
- The new general-English social-event option exposed ambiguous source triggers: a group of people or
  a mathematical function is not a social event. Both the concept and entry now require explicit event
  wording. The intensifier “properly” remains held for unresolved Australian vernacular evidence, without
  making an unsupported rarity or false-definition claim.
- The full run exposed historical round proposals whose URL strings and retired flags could no longer
  load. A non-mutating adapter at the round import boundary preserves archived inputs while canonical
  validation stays strict. Acquisition tools share the pure unreviewed-citation builder. A generic gate
  no longer claims doubtful definition, and explicit omission survives a gated verdict. Regression
  checks also preserve uppercase URL schemes and null notes, and report malformed URLs and invalid
  note types as contextual schema errors.

Independent checks confirmed that all 1,273 ids and every existing URL survived the migration. The flag
ledger covers all 83 formerly flagged entries; the level ledger covers every initially active entry and
those newly activated after separating usage from manual gates. Focused verification included 255
metadata/consumer checks and a later 110-test import/evidence/scrape/CLI run before the final full suite.

The refreshed golden corpus changes 66 of 375 outputs. These changes follow the reviewed grades, usage
gates and bounded weighting; the retained comparison records every changed input/setting by hash.
Four of the five website hero examples stay unchanged. The rain example changes only its opener, from
“Stone the flamin' crows” to “Strewth”. The website checkout was only read.

## What's done well

- One pure scoring function derives evidence from stored facts and accepts replacement live testimony.
  Copies cannot inflate documentary evidence, and testimony retains its cap and provenance.
- The shared metadata weighting rule serves two actual selection paths; entry-specific fit and garnish
  tier rules remain with their existing owners.
- Riffs and contextual imagery retain their existing shared tone/signature sampler, as the design says;
  metadata gates and evidence labels are shared without silently changing their editorial ordering.
- The migration preserves unresolved citations without pretending that component evidence proves a full
  expression. Real scoring anchors and provisional settings are explicit.
- Usage and meaning gates apply consistently to entries, imagery and riffs, independently of whether
  permitted comic material is invented.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Expression-level source hunt and score calibration | Certify unresolved source scope and tune the provisional weights against real examples | Alongside work explicitly retained by the build plan; this slice supplies its model and preserves the evidence |
| Yarn-specific misreadable allowance | Let the agent scaffold expose deliberately enabled ambiguous senses | Belongs with slice 3's agent scaffold |
| Theme policy and full public cards | Apply the stored subject matter and expose the coordinated new contract | Subsequent package slices; no website contract adoption is claimed here |
