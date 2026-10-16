# Judge and research workflows

The judge compares two to eight named translations blind against the rubric in `data/judge.yaml`. Its pure
packet construction shuffles names into labels using a seed. Report reading validates rubric version,
integer scores, textual evidence, exact quotations, problem fields and complete ranked tiers, then unblinds
and tallies verdicts. Ties share first place. Invalid reports raise `BadReport` with actionable findings.

```sh
aussiefy judge brief original.txt --candidate engine=engine.txt --candidate yarn=yarn.txt -o trial.json
aussiefy judge read trial.json report.json --json
aussiefy judge tally verdict-one.json verdict-two.json
```

`judge brief`/`read` let an agent supply the report without a paid API. New packets use evaluation protocol 2:
the same effective document behaviours, full numeric profile, embellishment guidance, resolved markup and
source-English context used for writing. `judge.blind()` and CLI `judge brief`/`run` accept `markup`, `english`,
`embellishment`, `document_type` and `document_config`; the reference `unharnessed` routes accept them too.
For example, add `--document-type custom --document-config '{"keep_quotes":true,"profile":{"phonetic":0}}'`
to choose explicit behaviours while inheriting the selected level's numeric defaults. Saved packets contain
the complete resolved snapshot, so later dictionary changes cannot reinterpret those settings. Completeness
and types are checked; deliberately unconventional combinations remain the caller's responsibility.

`Packet.judging(rubric)` returns the key-free `instructions`, `prompt` and `schema` sent to either an agent
or the API. `Packet.to_dict(rubric)` also includes originals, candidates and the unblinding key: keep that
file away from blind judges. Historical packets/verdicts without protocol metadata remain protocol 1;
settings are not inferred, and tallying protocol 1 with protocol 2 raises an error. The API cache includes
both instructions and the effective contract.

 `judge run` uses the shared Claude
client, validates the response, sends an invalid report back once and caches accepted results. `judge
unharnessed --prompt-only` produces the reference retelling brief; a live call is optional. Deterministic
[verification](../functional/verification.md) and the judge measure different things: structure/fidelity
checks versus rubric-scored tone, flow and essence.

`yarn-tools brief|lookup|lint|submit` exposes yarn's existing loop by hand, with the same policy, markup rules
and checked submission as the API loop. Research drivers and their manifests remain under `research/`, with
historical results from the pinned source snapshot. Their source-bearing originals, retellings, packets and
logs inherit corpus attribution through [PROVENANCE.yaml](../../../research/PROVENANCE.yaml); full local-only
exports stay ignored. Sanitised harvests omit entries that reproduce those works.

Tests: [judge](../../../tests/contributor/test_judge.py), [yarn/toolkit](../../../tests/functional/test_harness.py).

The [maintenance comparison](../../../research/maintenance-check-2026-10-15/README.md) pins the completed
20-text Dinkum remeasurement: original source hashes, dials and named document presets, with Dinkum-3 and
pre-fix yarn as unchanged anchors. The [refinement findings](../../../research/document-refinement-2026-10-15/FINDINGS.md)
retain the weak first result and subsequent writer revision, with independent blind judges. Research
evaluation protocol 2 included the effective contract before the public judge API. Current public packets
now carry that contract through every judge route; historical evidence stays unchanged. Do not compare scores across those packet protocols as a causal engine improvement.
For a new study, use new outputs and independent judges rather than recycling verdicts.


The [held-out comparison](../../../research/heldout-2026-10-16/README.md) uses six new-to-refinement texts and
two fresh independent blind judges over the same frozen outputs. The existing study driver accepts a
`--plan` when preparing a new run, records its path/hash, and reuses the production judge contract. It does
not rewrite historical packets or reports. Each repeat has its own frozen report manifest and summary.
