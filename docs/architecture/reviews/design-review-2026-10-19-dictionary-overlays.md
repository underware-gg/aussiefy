# Design review: explicit dictionary overlays, 2026-10-19

Status: Independent review converged; integrated verification passed.

## Findings

The design review required a clear distinction between behaviour settings and vocabulary corrections,
canonical validation, source-clearing precedence and deterministic add/patch operations. The implementation
adds no translation-specific matching path: raw records compose before the normal dictionary/index build.

The initial independent implementation review reproduced three findings:

| Priority | Finding | Resolution |
|---|---|---|
| High | Exposed plural/map/weight fields could survive validation and fail or silently change meaning later. | Canonical schema validation checks plural text, actual slot/trigger maps, positive finite weights and boolean/text fields; operations are validated before later layers can shadow them. |
| Medium | Duplicate-key checking discarded standard YAML merge-anchor handling in legacy entry lists. | Check duplicate explicit keys, then delegate merge flattening/construction to the established safe parser. Both parser implementations have regressions. |
| Medium | Entries introduced through extra files could lose their source sidecar references. | Bind source inheritance once when each raw record is introduced, before patches. Explicit source replacement remains final; complete custom inventories retain their source parity. |

An unrelated source-integration expectation surfaced in the broader CLI checks: the physical-solitude
predicate already supplies the on-your-pat form, so research-round replanning correctly drops the old
duplicate NP entry. The CLI test now requires the observed 210-entry plan and both explicit duplicate-form
diagnostics. Collision checks and research inputs remain unchanged.

## What's done well

The small raw composer preserves explicit defaults and leaves file access/index construction in the loader.
Add and patch operations cannot accidentally replace or create targets, named fields replace whole values,
and all normal meaning, grammar, dial and policy guards retain their roles. No output string replacement,
slang-specific core branch or persistent correction-history subsystem is introduced. Effective origin and
per-load operations support inspection through the existing validate/show tools.

Legacy entry-list files remain addition-only. The research-round writer remains a distinct workflow and
shares canonical concept-field knowledge rather than being imported into the core loader. Corpus guidance
puts general fixes in canonical data/shared grammar and requires positive, wrong-sense and grammar variants.

## Related follow-ups

Auxiliary riff, imagery, grammar and profile overlays need their own explicit formats if required later.
This version covers entries and concepts. Constructor/community metadata design remains separate.
Semantic severity and tone policy continue in their existing slices; this change alters neither presets nor
the frozen historical wording gate.

## Verification

Initial overlay/schema/research-round checks passed **98 tests in 82.70 seconds**. The first surface run
observed 133 passes and the separate classics-plan expectation failure described above. After the review
fixes and that expectation correction, **143 tests passed in 30.20 seconds**, covering overlays, canonical
schema, both YAML parsers, complete source inheritance, CLI/boundaries and package layering. Tests exercise
translation, lookup, plan, lint, changes and an injected MCP server against the same corrected dictionary;
the old route disappears and the vulgarity cap still applies. Ruff passed.

The independent broader re-review passed **80 tests in 77.41 seconds**. A remaining nested-merge duplicate
case was then corrected through SafeLoader's own merge traversal: each node's explicit keys are checked
before mutation, preserving valid inherited overrides and alias chains. Final independent review found
no remaining findings, with **39 focused tests passing in 18.39 seconds** (ten intentionally deselected
unrelated cases). The parent also observed 49 overlay/layer tests passing after that correction. Generated
documentation was refreshed. These counts are overlapping checks, not an additive test total.

No full-suite success or new commit is claimed here. Earlier semantic work still has an unchanged 60%
historical Gettysburg wording gate measuring 56%; that decision is not overridden by this implementation.

## Final integration verification

The complete reviewed integration passed **2,825 tests with two expected local-corpus skips in 840.53 seconds**.
Ruff, generated-document checks and provenance checks passed. The user approved enabling comic dictionary
terms in solemn text at Troppo, retaining other defaults off and exact overrides winning. Independent
review verified that matrix across the public surfaces. The frozen historical wording gate now passes;
its anchors, input texts and threshold are unchanged. Earlier failed/pending results above describe prior
snapshots and are superseded by this verification. No package release or main promotion is included.
