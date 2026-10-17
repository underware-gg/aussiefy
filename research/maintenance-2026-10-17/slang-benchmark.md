# Curated target-expression benchmark, 17 October 2026

The [fixed labels](../../tests/fixtures/curated-slang-labels.yaml) were chosen before measuring outputs. An
independent reviewer read the paired sources and targets without consulting dictionary entries, engine
output, historical anchors or scores. Parent/reviewer adjudication excluded child/adult sheila mappings
and loose Gettysburg paraphrases. This is separate from the unchanged historical 25-anchor gate.

Goldilocks is paired with `goldilocks_full.txt`, which actually supplies the target's story events. Using
the shorter reference would incorrectly classify inherited details as inventions. Both sources and targets
are hash-bound. Gettysburg has ten unique labels; Goldilocks-full has 22. Shared Australian/British
colloquialisms qualify; Australian exclusivity is not claimed.

## What is measured

Run the whole source at level 5, vulgarity 2, Troppo, General, no embedding fallback and seeds 0–9. A label
is reproduced if any run contains one of its reviewed forms. Normalisation folds case, restores dropped g,
and treats punctuation/hyphens as word separators; phrases cannot cross a sentence boundary. It does not
stem arbitrary words, infer synonyms or use the changing dictionary to decide what counts.

The report retains hit seeds, raw output occurrence counts and per-output hashes. Repetition does not
inflate unique-expression coverage. Counts are unaligned: any matching output occurrence counts, without
proving it represents the labelled source event. In particular, the excluded invented closing spewing
event is not automatically filtered from a raw count. There is no source-event score.

This measures reproduction of a reviewed target palette. Different valid slang does not count; an expression
used incorrectly can count. It does not establish general fidelity, grammar, density, authenticity or writing
quality. Interjections, discourse particles, drawl and inserted swears are outside positive expression labels.
Separate reading, verification and judgement remain necessary.

## First baseline

| Source | Unique target expressions reproduced across ten seeds |
|---|---|
| Gettysburg | 6/10 (60.0%) |
| Goldilocks-full | 10/22 (45.5%) |

The [baseline report](slang-baseline.json) retains the exact results. Its dictionary, label and scorer
digests, Git base and dirty-working-tree flag identify the actual inputs. The scorer/labels were new
uncommitted files when measured; the Git base alone is not claimed as their implementation. The committed
files and recorded digests reproduce counts/output hashes; Git metadata naturally differs on later checkouts.

No passing threshold was inferred from these scores, and no output-driven engine/dictionary tuning followed.
The old 60% historical gate remains unchanged. Its numeric coincidence with the new Gettysburg result does
not make the measurements equivalent. Broader quality bars need separately agreed evidence.

```sh
python scripts/benchmark_slang.py
python scripts/benchmark_slang.py --output /tmp/aussiefy-slang-current.json
```

Keep this baseline as recorded. Material changes to labels/input pairing need a new benchmark version and
baseline, rather than rewritten history. Tests validate paired hashes, transcription and scorer boundaries
without introducing a score-based regression floor.
