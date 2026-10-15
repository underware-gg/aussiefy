# Maintenance check, 2026-10-15

The explicit document-policy implementation and the engine/lookup/harness/round-tool fixes are integrated on
`dev`. This records what was measured and what still needs an independent run. It does not release a new model
or claim a new retelling quality score.

## Offline model measurement

[model-check.json](model-check.json) records the source commit, dictionary/reference fingerprints, model-file
hashes, raw semantic checks, gap benchmark and 15 actual toolkit queries. Lookup explicitly uses the bundled
model at level 5 and vulgarity 3, independent of machine-installed model settings.

```sh
python research/maintenance-check-2026-10-15/check.py --output /tmp/aussiefy-maintenance-model-check.json
```

The evaluator needs NumPy from the maintainer environment; inference in the installed toolkit still needs
only the standard library. It reuses the existing training evaluation functions, performs no training and
calls no remote API.

| Measurement | Current result |
|---|---|
| Bundled model | aussie-static 1.2.0, unchanged weights |
| Required raw-model references | 33/33 pass |
| Tracked raw-model failures | 16 remain; none newly pass |
| Gap benchmark right top-1 | 0.302 |
| Gap benchmark filled right / filled wrong | 0.186 / 0.140 |
| Everyday words automatically filled | 0.154 |

The rounded filled-right/wrong rates imply about 57% precision, below the 90% bar for enabling default
automatic gap filling. The dictionary has grown, so these are current baseline measurements, not evidence
of a gain or regression against a differently sized historical dictionary.

Raw semantic references and toolkit behaviour differ. The toolkit now parses filled slots, respects the
entry frame for inflection and uses conservative negation anchors. `give Bob a bell` (also with terminal
punctuation) selects telephone vocabulary; `shouted` and `harmless` safely return no suggestions in this check.
These fixes do not establish general semantic disambiguation. The captured toolkit queries still show:

- `not out of the question` offering refusal/impossibility;
- `worked very hard` offering unrelated happiness/ease;
- `probably` offering stronger certainty;
- `officials` offering politicians and an unrelated photo phrase;
- `stuff up` including the money sense of “stuff”.

Keep 1.2.0 bundled. Two prior 1.3.0 trials failed required references; this check supplies no evidence to export
new weights or add another binary to history. Before a future export, agree storage while preserving offline
installation, then compare real toolkit queries as well as raw references. Do not turn the measured queries
into training examples or remove failed references to make a gate pass.

## Fresh Dinkum comparison: prepared, not run

[retelling-study.yaml](retelling-study.yaml) pins 20 original sources and their hashes, level/vulgarity/seed,
explicit named document type, markup mode, Dinkum setting and unchanged historical anchor hashes. Named types
hold the prior form choice constant now that General is the default. The anchors are Dinkum-3 and the earlier
pre-fix yarn from the Dinkum check. No new source texts or retellings are copied into this directory.

For each case, obtain a fresh `yarn-tools brief` with its policy, write from that brief, use lookup/lint/submit
and retain accepted output and diagnostics in a local run directory. Compare `current`, `dinkum-3` and
`pre-fix-yarn` with seeded blind `judge brief` packets under rubric 3; have a separate judge supply reports,
then validate/read/tally them through the existing commands. A writer and judge may drive those CLI workflows
as agents without a paid API, or use the live API with configured credentials. There is no Anthropic API key
configured in this environment. Fresh writer output and independent judgement remain outstanding.

The important comparison is whether the stronger verb/quote fidelity rules recover meaning while keeping the
register regained in the earlier study. Tests, old verdicts and replayed submissions cannot answer that.

## Choices to review

- **Custom starts bare.** Optional document behaviours are off; vocabulary, selected markup protection and
  dial limits still apply. Advanced list overrides replace lists exactly, and false/zero/empty values count.
- **The docs use Swaggie / Dinkum / Dad.** General plus explicit Technical term protection gives them flavour
  around preserved terms. Shared document state limits garnish; incomplete Markdown fragments do not acquire
  sentence openers. Review whether the resulting density is right before a release.
- **Name aliases are explicit.** `grammar.yaml` contains the reviewed whole-phrase Christmas Trees aliases.
  Lint never infers those aliases from a word inside a person/place name. Sentence-initial name extraction
  remains an existing limitation.
- **Model work remains evidence-led.** Retain current weights, measure fresh yarns independently, then decide
  whether a further model experiment is justified.

Other independent engine/data opportunities remain listed in [OPEN_ISSUES.md](../OPEN_ISSUES.md), including
negative-person marking, richer trigger guards and semantic negation. They are not silently declared resolved.
