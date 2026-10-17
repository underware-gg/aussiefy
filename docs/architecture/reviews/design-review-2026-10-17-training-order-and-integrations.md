# Design review: training order and available integrations, 17 October 2026

Surface: WordNet training-pair selection, trainer regressions, current-model trial evidence, reproducibility
and benchmark qualifications, and real portable CLI/MCP integration captures. One independent reviewer
assessed all six software-design concerns.

## Findings

No remaining findings after correction.

- Low factual wording: the earlier commit changed trainer cleanup, not the recipe. Correct that attribution.
  State that the rejected candidate passed 30 of 33 required checks and failed three; avoid wording that
  could read as 30 failures. Neither the recipe nor any required quality gate changes.
- Qualify historical training time, weight reproducibility and gap-benchmark intent. Current covered words
  are not unseen probes, and a shipped model's current-entry scores are not a common unseen holdout.
- Distinguish the original integration capture from its recheck against committed runtime `328d8d1`.
  Subsequent website-agent coordination is separate from observed deployment evidence.

The reviewer independently passed 13 trainer tests; matched all eight runtime digests to the capture commit;
checked all ten saved evaluation-checkpoint digests; recomputed reference totals; matched all 36 lookup
projections to raw evidence; and reproduced all six complete MCP responses in a fresh outside-repo session.
Both fresh-process hash seeds yield identical ordered pair digests after the correction. Complete pre-commit
results are recorded in the maintenance ledger.

## What's done well

- Sorting stays at the WordNet neighbour boundary before truncation, preserving sense and lemma priority.
- The failed candidate remains rejected and shipped 1.2.0 remains intact. Fresh fits follow the committed
  corrected trainer, rather than reusing a checkpoint trained with different pair selection.
- Retained evidence includes interruptions and limitations; it does not infer web latency or live-provider
  success from local toolkit checks.

## Related follow-ups

Run the already planned fresh evaluation and full fit. Meaning-specific training and a refreshed unknown-word
cohort need separate shaping; the present diagnostics do not establish one cause or justify a recipe change.
