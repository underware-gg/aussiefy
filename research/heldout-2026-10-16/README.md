# Held-out retelling comparison, 2026-10-16

Six source texts absent from the earlier 20-text refinement: five newly written fictional own-work inputs
and a newly acquired public-domain Bible passage. Source hashes are disjoint from that study. This is
held-out evaluation relative to that refinement, not a claim that foundation models have never seen the Bible.

| Case | Contract |
|---|---|
| Missed ferry | Larrikin / Dinkum / Dad, General |
| Community library notice | Swaggie / Dinkum / Dad, News; direct quote stays exact |
| Demonstration-lantern instructions | Larrikin / Dinkum / Nan, Instructions |
| Retry guide | Actual repository publication settings, Markdown protections |
| Refund policy | Local / Deadset / Nan, Official |
| Good Samaritan, Luke 10:25–37 | Swaggie / Dinkum / Dad; no added garnish, openings or person swears; quoted dialogue may be retold |

The five synthetic inputs and their source declarations are in
[tests/corpus/heldout/20261016](../../tests/corpus/heldout/20261016/SOURCES.yaml). The Bible source is
[World English Bible Classic](https://ebible.org/eng-web/LUK10.htm), whose publisher explicitly
[dedicates it to the public domain](https://ebible.org/eng-web/copyright.htm). Its 2020 stable text is
stored in [the reference corpus](../../tests/corpus/reference/bible_good_samaritan.txt), with edition,
retrieval date, extraction details and original/derived SHA256 hashes in
[SOURCES.yaml](../../tests/corpus/reference/SOURCES.yaml). The original wording and US spelling remain.
Verse numbers and footnotes are omitted; all eight selected paragraphs are retained. Derived outputs
are retellings, not editions of the World English Bible.

[plan.yaml](plan.yaml) pins sources, policies and the deterministic current-engine anchors. Two fresh
writer contexts receive only originals and current briefs; each uses real lookup/lint/submit calls and
retains the diagnostics. All six current briefs include `ENGINE_DRAFT`, which is the same text as the
current-engine comparator after stripping outer whitespace. Writers receive that draft as intended toolkit
input; they do not open separately labelled anchor files or see historical candidates. This is a guided
retelling versus supplied-draft comparison, not independent candidate authoring. The origin records
`anchors_read: false` / `prior_outputs_read: false` describe file access and historical-output isolation;
they do not imply the brief hid the engine draft. The same six accepted
outputs go to two fresh independent blind judge contexts, without writer feedback or another judge's
reports. Each judge receives the same key-free packets under rubric 3 / production evaluation protocol 2.

The first run's writer contexts are fresh. The second run deliberately reuses those exact outputs and
briefs, with canonical replay under the same engine and per-case lineage records. It is a judge repeat,
not a second authoring experiment. Candidate labels are shuffled by case and held fixed between judges.

The existing [study driver](../document-refinement-2026-10-15/study.py) is reused. A selected plan's path
and hash are frozen in its manifest; collection does not depend on repeating `--plan`. Its production
judge packets carry the actual effective writing settings, rather than a separate research interpretation.
All source, anchor, writer, tool-log, packet and report hashes are checked. Fifteen real brief-construction
calls were checked against the frozen arguments/results and retained verbatim in the hash-bound writer
origin records. Dispatch logs retain the other 28 actual calls: 16 lookups, six lints and six submissions.
The six anchor captures retain a terminal separator newline alongside the translated source's trailing
newline; issued bytes stay unchanged. Packet prompts strip outer whitespace, so this does not change
the compared wording. Issued evidence is never replaced
with changed content. Historical rounds are unchanged and require their own original snapshot for replay.

The reusable driver's `summary.json.limits` retains the inherited phrase “different current and historical
writer contexts” from the original historical-anchor experiment. That generic phrase does not describe
these runs: their only comparator is the supplied current-engine draft, and no historical writer candidate
participates. This study-specific method and pinned plan describe the actual comparison. Frozen driver
and evidence bytes are retained unchanged.

The manifests' `source_commit` records the starting development commit. This study freezes the uncommitted
judge implementation that subsequently lands with these results: the complete `engine_files` map and
`driver_sha256` identify the actual evaluated bytes. The eventual committed checkout must match those
hashes; the starting commit alone is insufficient for replay.

```sh
python research/document-refinement-2026-10-15/study.py prepare --run study-heldout-judge1 --plan research/heldout-2026-10-16/plan.yaml
python research/document-refinement-2026-10-15/study.py prepare --run study-heldout-judge2 --plan research/heldout-2026-10-16/plan.yaml
# Fresh writing / canonical tool calls, then exact output reuse and replay for the second run.
python research/document-refinement-2026-10-15/study.py packets --run study-heldout-judge1
python research/document-refinement-2026-10-15/study.py packets --run study-heldout-judge2
# Each independent judge writes its own *.report.json files, with the full schema and literal evidence.
python research/document-refinement-2026-10-15/study.py collect --run study-heldout-judge1
python research/document-refinement-2026-10-15/study.py collect --run study-heldout-judge2
aussiefy judge tally research/document-refinement-2026-10-15/study-heldout-judge1/texts/*/verdict.json research/document-refinement-2026-10-15/study-heldout-judge2/texts/*/verdict.json > research/heldout-2026-10-16/repeat-tally.json
```

Do not rerun `prepare` over issued evidence. Select new run names for another experiment. Reproducing the
same `packets` or `collect` against unchanged evidence is allowed. The final tally contains 12 assessments
of six distinct texts per candidate; it does not represent 12 independent source texts. The completed results are below. No causal comparison with the earlier study's changed inputs,
writer contexts and evaluation instructions is justified.


## Completed results

Both independent judges completed all six texts. All 28 dispatch calls replayed and all six distinct
retellings passed deterministic verification with zero critical, major or minor problems. Both repeats
bind the same outputs; their 12 verification records are repeated checks of six translations. All 192
criterion-evidence fields contain literal candidate excerpts, and every quoted excerpt was checked.

| Criterion | Guided retelling | Supplied engine draft |
|---|---:|---:|
| Meaning | 5.00 | 4.83 |
| Sense | 5.00 | 4.58 |
| Authenticity | 4.92 | 4.83 |
| Register | 4.58 | 1.58 |
| Tone | 5.00 | 5.00 |
| Flow | 4.92 | 4.75 |
| Variety | 4.92 | 5.00 |
| Essence | 5.00 | 5.00 |
| Overall mean | 4.92 | 4.45 |

[repeat-tally.json](repeat-tally.json) retains the aggregation: `texts: 12` means twelve assessments of
six sources, not twelve independent texts. Judge 1 means were 4.94 / 4.44; judge 2 means were 4.89 / 4.46.
Both ranked the guided retelling above its engine draft on all six sources: twelve paired rankings, with
no ties or disagreements over the overall winner. Two fresh contexts of the same available agent provide
repeat-judge evidence; they are not independent model-family or human replication.

The guided outputs have no critical problems, one major and five minor problem assessments across both
judges. Both scored the lantern instructions at register 3 for a requested level 4; one called that major,
the other minor. This is the clearest remaining weakness: natural, faithful safety prose still comes out
light on Australian body phrasing. Other minor observations concern repeated give-constructions, a stock
technical opener, light technical connecting prose and a repeated-pronoun join in the Bible retelling.
No output or report was revised after blind assessment to remove those findings.

The engine drafts have no critical, sixteen major and four minor problem assessments. Many concern weak
register. Both judges also identified the Bible draft's `hand on heart` for wholehearted devotion as a
wrong idiom, and `what will I do` for the source's deliberative `what shall I do` as a modal shift (severity
differed). Mechanically attached drawl such as `once'n` drew weaker flow/authenticity assessments. These
are concrete engine/quality follow-ups revealed by the new corpus, rather than defects introduced by the
judge-contract implementation. They are recorded in [OPEN_ISSUES.md](../OPEN_ISSUES.md).

These six inputs are now evaluated material. Treat another future tuning comparison on them as reuse,
and select new sources when claiming a fresh held-out study. This bounded, supplied-draft comparison
supports the observed fidelity/flavour balance; it neither establishes a causal gain over the earlier
refinement nor guarantees performance on other texts or judges.
