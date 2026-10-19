# Design review: semantic benchmark evidence, 20 October 2026

Status: Focused review converged; integrated checkpoint verification passed.

## Findings

All findings from the independent six-concern focused review are closed. The actual training trial,
rejection decision, complete-input witnesses, diagnostic readers, bounded comparisons, research drivers
and current plain documentation were reviewed together. The full repository run passed 3,256 tests with only the two permitted local-corpus skips; Ruff,
publication and provenance/licence checks also passed.

- The executed driver's external drift guard omitted tokenizer/configuration/module files. The exact
  executed bytes remain archived; supplemental during/after witnesses validate all 12 pinned cache files
  and match. The repaired reproduction driver captures and compares the complete snapshot. Three
  integrity tests exercise metadata/weight tampering and the additional storage symlink.
- Diagnostic metadata initially lacked actual uncommitted model identity. It now records the bundled
  version and all three asset hashes; aggregate comparisons also verify those assets are unchanged.
- Aggregation originally used assertions on external CLI artifacts before writing unchanged flags.
  Explicit exceptions now enforce the contract under optimisation. A real mismatched-label packet was
  rejected with Python `-O`, exit 1 and no output, while the unchanged packet aggregates successfully.
  The output records the repaired driver's actual hash. No fit or timing measurement was repeated for
  this analysis-only correction.

- A public-copy spot check found a benchmark query label being translated as ordinary prose. All three
  failed-query labels are now protected code literals in both affected plain guides and their generated
  copies. Markdown token inspection confirms the exact labels, the focused review is clean, publication
  passes and all 146 documentation tests pass after correction. No Python, dictionary or model input changed.

## What's done well

Strict release rejects the full-data candidate at 30/33, retains the evaluation's separate 29/33 and
adopts no failed weights. The separate diagnostic reader has identical pass/known outcomes and top-concept
lists; differing top forms are disclosed rather than described as full-ranking parity. Its actual-reader
lookup comparison keeps dictionary/runtime constant and exposes the mate/cobber regression.

The three literal reproductions fall 9 to 0, with all affected unique outputs read manually. The report
preserves the remaining relational threshold issue and nine verifier abstentions. It distinguishes known
diagnostics from unseen quality, wording overlap from meaning, and 94 exact scorer comparisons from
reader reference outcome parity. Timings run serially after fitting/testing and make no causal speedup or
website latency claim. Baseline labels, scorer, historical anchors, Smart sources, recipe and gates remain
unchanged. Full reference copies stay in local packets; repository evidence is bounded metadata.

The report and documentation accurately retain fingerprint-stale bundled 1.3.0 at 33/33. No canonical
1.4.0 report or model asset is adopted. Research drivers do not add a runtime abstraction or phrase-specific
engine workaround.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Diagnose failed-model concepts/pair sharing before another fit | Establish a supported training hypothesis | Current 1.3.0 remains available and passes the gate |
| Review composed degree, relational thresholds and qualifier ownership | Improve fluent coverage without unsupported severity shifts | Current preservation and abstention boundaries are explicit |
| Extend reviewed families, pairing and unsupported/figurative senses | Broaden useful precision beyond the measured cases | No universal semantic guarantee is claimed |
