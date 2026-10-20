# Design review: subject permissions, 21 October 2026

Surface: community-dictionary slice 1, from `1482f0f`: data-driven subject defaults and exact overrides,
shared selection and acceptance rules, reviewed tags and split senses, model/agent contracts and docs.
One independent reviewer assessed all six software-design concerns and re-reviewed each correction.

## Findings

No remaining findings. The final full suite passed **3,446 tests**, with the two expected local-corpus
skips. Ruff, generated-documentation and provenance/licence checks passed. Documentation-only recording
and index changes are checked separately after that implementation run.

Resolved findings:

- Lint, checked submissions and model hooks could bypass selection's theme filter. A shared pure known-form
  check now serves those paths, retaining original occurrences and reporting recognised forbidden additions.
- Longer allowed expressions must own nested homonyms in both output and source budgets. The same rule
  prevents have-a-crack from supplying an allowance for introduced drug wording, including fixed colour.
- Existing strict-signature sentence hooks must remain usable. Capability inspection passes the optional
  permissions only to hooks that accept them; every reply is checked without TypeError retry.
- Riff tags belong on the actual child records in `riffs.yaml`, independently of their parent entry. Real
  esky, drongo, raffle and cow-pissing regressions verify their own subject restrictions.
- Mixed food/alcohol, exhaustion/alcohol and drug/alcohol senses need distinct records. Existing IDs and
  complete citation trails are retained; unreviewed sources are not silently promoted into evidence.
- Known literal readings must remain unresolved by the bounded checker. Existing `plain_sense` metadata
  covers ordinary full containers, rotten apples, sloshing water, boat tinnies and the name Chrissie,
  while their curated sense still requires its theme during automatic selection.
- Judge snapshots must record resolved themes separately from document behaviours. Old snapshots retain
  an absent theme map; a supplied map requires all nine exact booleans and is never inferred later.
- Functional inventories, the decision index and model/verification documentation now describe the policy
  and its bounded guarantees.

The first broad run exposed 28 stale test expectations: subject prerequisites in offset/discovery/grammar
fixtures, strict response-field sets and the old combined stonkered ID. Their assertions were preserved or
strengthened with explicit subject permissions and the correct sense ID; the final full run is clean.
Seven of 375 golden outputs changed and were reviewed. Changes fixtures were regenerated without changes.

## What's done well

- One resolved immutable permission set serves entries, images, riffs, garnish and editor cap probes.
  Subject matter remains independent of profanity, optional performance and manual usage unlocks.
- The shared acceptance rule is explicit about known forms and ambiguity rather than claiming arbitrary
  subject classification. Source subject matter is preserved.
- Compatibility follows actual consumers: old strict hooks and historical judge snapshots retain their
  behaviour without weakening current validation.
- Reviewed data owns theme distinctions and ordinary readings; no phrase-specific Python exceptions
  are introduced. The migration preserves every prior entry ID and source trail.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Settle tobacco classification | Apply consistent reviewed tags to cigarette terms | Pending product decision; no classification was guessed |
| Continue expression-level source review | Refine sense-specific support and provisional evidence weights | The source hunt runs alongside the package slices; preserved leads keep this separable |
| Composite provenance and contract sequencing | Represent the planned replacement of the old garnish coherently | A dependency of the next slice, raised with Rob before changing the approved order |
