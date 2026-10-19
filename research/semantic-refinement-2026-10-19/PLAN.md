# Semantic engine refinement

User direction: improve the existing engine's shared grammatical and semantic interpretation, including
tone, without coupling this work to the separate community-dictionary design. No communication with the
external agent is authorised. Internal research agents continue the source audit separately.

## Completed foundation

Commit `2687d7f` shares clause reading, polarity, nominal arguments and complement restrictions between
translation and contextual imagery. Tone/mood weighting also reaches planner suggestions, and document
mood survives strict Markdown segmentation. Concept restrictions survive research-round replay. The
pure-Python YAML loader reads the complete bundled dictionary.

That slice passed independent review, Ruff, generated-documentation, provenance and whitespace checks,
and the complete suite: 2,403 passed, two expected local-corpus skips (793.25 seconds).

## Completed lexical and argument slice

The current changes distinguish activity starts, rough assembly, comradeship, political people, driving
roles, sleeping accommodation and other reviewed senses. Source additions from the earlier 30- and
60-entry ledgers cover 85 entry records and 110 new URLs. Requested cultural references and conditional
appetite phrases are implemented, with writer suggestions for constructions needing judgement.

Shared argument reading distinguishes bounded temporal/prepositional adjuncts from unanchored objects.
It retains quantified noun objects, nominal compounds, gerunds, temporal subjects and anchored arguments.
It does not claim a complete parser: location-adverb ambiguity and gerund/preposition boundaries remain
explicit follow-ups.

Independent design review has converged. Focused regressions and generated artefact readback passed.
The complete final run passed 2,522 tests with two expected local-corpus skips (775.08 seconds); Ruff,
generated-document freshness, provenance/licensing and whitespace checks also passed.
See [integration scope](meaning-integration.md) and the
[review](../../docs/architecture/reviews/design-review-2026-10-19-meaning-extensions.md).

## Remaining slices

1. Complete full verification of the integrated narrator-opinion setting and entry annotations. Existing
   embellishment profiles resolve its default, with exact advanced overrides; role/reference preservation
   remains independent of permission to add opinion. Translation, lookup, plans, change alternatives,
   garnish and known-term writer checks share the resolved permission. Full integrated verification remains.
2. Complete full verification of the integrated source-derived corrections from batches 3–6 and explicit
   listener binding. Shared mass/count checks, complete terminal arguments and object possessives retain
   quantity, participants and grammar. Existing Australian verse stays unchanged; scientific tree names
   remain available for precise translation. Independent integrated review converged: 368 scoped tests
   passed. The parent observed 509 runtime tests passing in 40.27 seconds. All 212 pre-integration source
   IDs/URLs survive; the combined sidecar has 688 IDs, with all 530 new entry/URL pairs preserved.
3. Implement the settled explicit-severity rule using reviewed semantic degree alongside the existing
   soft intensity axis. Historical ratings do not certify semantic degree. Preserve existing availability
   when input states no degree; require compatible realised degree for an explicit mild/strong source.
   Cover both understatement and overstatement,
   modifier ownership, negation, result clauses and automatic change alternatives. Resolve the tone rule
   through advanced settings. The user approved `solemn_comic_terms` at Troppo, with other defaults off
   and exact overrides winning. The explicit override passed independent cross-surface checks; the
   approved preset update is awaiting integrated verification.
4. Integrate clear supported corrections from research batches 7–11 separately from provisional
   evidence and intentional stylistic policies. All 1,254 original IDs now have research records; independent
   cross-reviews have converged, and the parent verified the exact baseline-ID union with no omissions
   or overlaps. See [coverage](audit-coverage.md). Source candidates and recommendations are not
   automatically runtime changes.

## Verification and scope

Each implementation slice needs meaningful positive/negative tests, generated corpus and change-fixture
readback where affected, public-document freshness, independent design review with findings resolved,
Ruff, the complete suite and provenance checks before commit and push to `dev`. No release promotion is
part of this task. Research coverage counts original-baseline IDs, not later additions, and does not certify
all triggers, constructions, frequency or origin claims.

The separate constructor, theme and attestation-metadata design remains external to this implementation.
Ordinary source research and clear dictionary fixes do not depend on completing that design. Prefer
existing shared context, form compatibility and dictionary concepts to slang-specific engine branches.

## Settled direction

- Behaviour overrides select engine settings; dictionary overlays correct vocabulary data. The user
  requested a generic engine driven by corpus/tooling, with explicit overlays able to replace a faulty
  mapping. Versioned add/patch composition is implemented without post-processing replacements; independent
  review corrections and independent re-review have converged; full verification remains. General fixes still belong in
  canonical data or shared grammar. See DD-032 and the dictionary-overlay review.
- Preserve explicitly stated semantic severity in automatic translations, in both directions. Comic
  understatement remains a writer suggestion; narrator-opinion permission does not authorise changing
  degree. User confirmed this on 19 October. Research reproduces both legless-to-mild and tipsy-to-extreme
  conversions; implementation and independent verification remain.

## Historical wording gate resolution
- The frozen 25-anchor Gettysburg wording-overlap gate requires 60%; the corrected narrator-opinion
  integration measures 56%. Direct comparison against 11aa20c finds exactly one lost anchor: the old
  BRAVE-to-SOLDIERS mapping supplied “diggers”; the corrected mapping supplies “brave bastards”. The
  earlier explanation attributing the gate drop to poor-buggers was incorrect. The anchors, threshold and
  measurement remain unchanged. The user requested further diagnosis rather than approving a relaxed
  gate; investigate valid reusable coverage improvements and report remaining incompatible targets.
  See the [independently checked diagnosis](gettysburg-gate-diagnosis.md). The user subsequently approved
  comic treatment of solemn text at Troppo, with other defaults off and exact overrides winning. This
  applies consistently to all passages, independently of the benchmark. The pre-preset full snapshot
  passed **2,824 tests with two expected skips**; the frozen historical wording gate was its only failure
  (818.12 seconds). The model retrieval gate now passes with the freshly trained, reviewed 1.3.0 model.
  The approved preset integration passed **2,825 tests, two expected skips, in 840.53 seconds**; the
  frozen wording gate passes. Ruff, publication and provenance checks passed.

## Model verification follow-up

The cold-one reference has both an old target label and a real retrieval miss. Current raw top concepts
are pub meal, pub lunch and pub, rather than beer. Independent review confirms that lexical lookup partly
rescues coldie but still ranks unrelated pub options above it. The reference's exact query, top-three rule,
cutoff and required status remain unchanged; the current label list includes COLD_BEER_SERVING. The known
very-cold negative likewise follows the reviewed cold-serving and container descendants rather than
appearing fixed merely because an entry changed concepts. Historical trial reports remain immutable.

A fresh evaluation/full-fit trial completed against the unchanged pinned deterministic recipe, with
cached-only model resolution, fresh checkpoints, an isolated destination and exact dirty-input hashes.
The full fit and isolated package reader both passed **33/33**; evaluation passed **32/33** with girl failure
retained. Every frozen input stayed unchanged through completion. Independent adoption review verified the
artifacts, common-input lookup comparison, provenance and package reader. Model 1.3.0 is prepared in the
working tree; no package release or main promotion has occurred. The complete integrated suite passed
2,825 tests with two expected skips. See [trial and bounded limitations](../semantic-model-2026-10-19/README.md).

One lexical retrieval error came from mentioning loneliness in a physical-solitude gloss. The positive
meaning now stays in the gloss and the non-equivalence in notes. This existing corpus distinction avoids
a phrase-specific blacklist; it does not claim to solve all model associations or define a new related-result API.

Independent source calibration covers all 18 DRUNK entries and 19 forms. See
[degree calibration](drunk-degree-calibration.md). Implementation remains separate; the evidence does not
certify unknown ratings, erase terms or change availability for input without an explicit degree.

## Isolated degree implementation

The next slice is implemented in `/private/tmp/aussiefy-degree-prototype-20261019`, outside the model/full-suite
inputs, and is not yet integrated into this checkout. Optional concept-scoped entry grades and frame/exact-trigger
certificates separate meaning from soft intensity. Shared qualifier ownership reaches substitution and phonetic
preservation, including negated source text. Unsupported compositions retain their wording; form selection,
stacking and change alternatives use compatible realised degree. Source-form grades are not inherited by
arbitrary `replaces` phrases. Bare full is separated from a-bit-full; unreviewed target degree remains available
when the input states no degree.

Independent design/implementation review converged after correcting two findings: reviewed source forms
also need to own their qualifiers, and invalid source frames must not poison applicable certificates.
The parent observed 106 broader prototype passes before those corrections; final independent recheck passed
55 degree/metadata cases and 12 additional forced-phonetic render/replay probes after covering unknown-degree
source forms and the spaced half-cut variant. Full original-checkout integration,
corpus readback, performance measurement and verification remain. Do not describe this prototype as shipped.

## Plural address refinement

The user identified “Hi everyone” becoming “G'day every bugger” in a website showcase. Independent diagnosis
confirms a missing direct-address versus quantified-reference distinction. Referential “Every bugger came”
remains valid; a greeting needs a plural recipient. A separate scratch prototype keeps the np frame,
adds concept-scoped noun-use restrictions to shared applicability, reuses greeting-recipient grammar and
supplies plural-address meanings/forms. Ambiguous detached phrases stay uncommitted rather than guessing
from a comma alone. Initial address/schema checks passed 55 cases; independent review and integration
remain. No website checkout or external agent was contacted.
