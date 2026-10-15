# Research: choosing the approach (before 1.0.0)

The study that led to the bundled model, kept for the reasoning and the numbers. It was run with the
prototype script before the recipe existed: same data and settings as `recipe.yaml` 1.0.0, except that the
reference set didn't exist yet (the two wrong-sense checks were hard-coded). The current process is in
`README.md`; each version's own numbers are in `reports/`.

## Setup

- **Data**: pairs drawn from the dictionary, 2,825 in total from 398 training entries. Each concept trigger
  and each `replaces` is paired with the entry's form; the gloss is paired with the form and its variants;
  each riff is paired with the form. There are also 192 wrong-sense pairs, taken from the triggers'
  `!exclusions` ("great war", "new york", "heart attack" and so on) and paired with that concept's forms.
- **Hold-out**: 20% of entries by id, seed 13, which is 99 entries. Nothing from a held-back entry is
  trained on: not its form, gloss, `replaces` or riffs. The static model's extra vocabulary also uses
  training entries only.
- **Training**: `all-MiniLM-L6-v2` fine-tuned with MultipleNegativesRankingLoss over the pairs (no duplicate
  texts in a batch), plus ContrastiveLoss (margin 0.5) over the wrong-sense pairs. 4 epochs, lr 5e-5,
  batch 64, CPU.
- **Distil**: Model2Vec `distill` with 256 PCA dimensions, adding the dictionary's whole words to the
  vocabulary so that "arvo" gets its own vector. Distilling alone lost most of what fine-tuning had taught,
  so the final static model ("tuned") takes those distilled vectors and trains them directly on the same
  pairs and losses (sentence-transformers `StaticEmbedding`, lr 0.05, batch 256, 4 epochs). It is then saved
  back in Model2Vec format as float16.

## Recall@3 on the 99 held-back entries

Three tasks:

- **gloss→form**: a held-back gloss must find its own form among all 497 forms.
- **…any form of the concept**: the same query, but any form sharing the concept counts.
- **form→concept**: a held-back slang form must find its concept among the 281 descriptions.

| setup | gloss→form | …any form of the concept | form→concept | size |
|---|---|---|---|---|
| n-gram (character trigram) | 0.21 | 0.27 | 0.23 | 0 |
| stock MiniLM | 0.32 | 0.42 | 0.28 | 91.6 MB, plus torch |
| stock MiniLM, static (distilled) | 0.20 | 0.30 | 0.18 | 15.7 MB |
| Aussie MiniLM (fine-tuned) | 0.38 | 0.66 | 0.42 | 91.6 MB, plus torch |
| Aussie MiniLM, static (distilled only) | 0.18 | 0.36 | 0.29 | 15.7 MB |
| **Aussie static, tuned** | **0.36** | **0.72** | **0.42** | **15.7 MB** |

With n = 99, one standard error is about ±0.05, and this is a single seed. The gaps between n-gram, stock
and Aussie are real. The gap between the two Aussie models is not.

Install footprint: the stock and fine-tuned models need torch. The default `model install` (CPU build)
downloads a 196 MB torch wheel that takes 769 MB once installed; with sentence-transformers and its
dependencies the venv comes to 1.3 GB, and the install takes under a minute. The PyPI build (`--torch pypi`,
CUDA) came to 5.9 GB of venv, including 3.2 GB of NVIDIA libraries. The static model needs only `model2vec`, which pulls in numpy, tokenizers and safetensors (the
`tokenizers` wheel is about 11 MB). It loads without torch or transformers, and 1,000 encodes take 21 ms.

## Wrong senses

Each cell shows the top 3 forms, then the lookup-style score of the wrong entry: the query against its
gloss and description.

| setup | "girl" | must not be sheila | "a great war" | must not be EXCELLENT |
|---|---|---|---|---|
| n-gram | burl, a burl, ginormous | ok (0.00) | a goer, bloody great, a geek | ok (0.26) |
| stock MiniLM | beauty, game, young fella | ok (0.33) | bloody great, a shitfight, battle on | ok (0.32) |
| Aussie MiniLM | littlie, Chrissie, **sheila** | **fails (0.51, which is over lookup's 0.50)** | a shitfight, bloody great, a stoush | ok (0.34) |
| Aussie static, distilled only | littlie, Chrissie, young fella | ok (0.47) | battle on, bloody great, a shitfight | ok (0.58) |
| Aussie static, tuned | littlie, nipper, ankle biter | ok (0.28) | a stoush, a shitfight, a mad cunt | ok (0.37) |

"bloody great" belongs to HUGE, which is the right sense of "great" in "great war". "a mad cunt" would
be filtered by lookup's vulgarity cap.

Caveat: "great war" is itself one of the wrong-sense training pairs, since it comes from the dictionary's
`great !war|…` exclusion, so that check is partly in-sample. "girl" appears nowhere in the dictionary. The
fine-tuned transformer learns girl ≈ woman ≈ sheila, and the tuned static model does not.

A real query: "knackered beyond belief" against TIRED's "Exhausted, worn out." scores 0.16 with stock
MiniLM, so lookup finds nothing. The tuned static model scores it 0.44.

## Calibration: the stock model, as installed

Measured with `calibrate`, the constants were set as follows.

**lookup `MODEL_THRESHOLD`: 0.55 → 0.50.** Thirty trigger→own-entry pairs scored a median of 0.62 (p25
0.43). Thirty random unrelated pairs never passed 0.33. A query, though, meets the whole dictionary, and
its best wrong match there has a median of 0.47. Reading those 30 by hand, 4 are genuinely wrong at 0.50
or above ("very little" → heaps, "out of work" → smoko, "crocodile" → roo, "take a seat" → have a feed),
against 8 at 0.45. At 0.50, two thirds of right matches pass.

**gaps `CONFIDENT`: kept at 0.60, now measured.** The test was 30 trigger words (leave-one-out) against 30
words no concept covers. With MiniLM, no unrelated word reached 0.60 (the highest, "chair" → SIT_DOWN,
scored 0.58), and 53% of right nearest guesses did. With n-grams, 7% of unrelated words and 20% of right
guesses reached it. One cut-off serves both. MiniLM's nearest concept was right for 63% of words, and the
tuned static model's for 80%.

For the tuned static model, the same harness puts the cut-offs in the same band: lookup about 0.50–0.55
and gaps about 0.55. Those numbers are optimistic, because its training saw these triggers.

## Recommendation

Offer the tuned static model in place of MiniLM plus torch.

- It matches the fine-tuned transformer on held-out Recall@3, and it is the only tuned variant to pass
  both wrong-sense checks.
- It is 15.7 MB instead of 92 MB plus 1.3 GB (CPU) to 6 GB (CUDA) of torch and its dependencies.
- It is deterministic, and fast enough to embed the whole dictionary on every call.

## Shipped: the bundled model

The recommendation went further than an optional download: the model now ships in the package and is the
default for `lookup` and `gaps`.

- **Release model**: trained on all 497 entries (3,538 pairs, 307 wrong-sense pairs) with the settings
  above. `export` writes it to `aussiefy/data/model` as 29,817 × 256 float16 rows, a vocabulary and
  `meta.json`: 15.5 MB in the repo, 14.5 MB in the wheel.
- **Runtime**: `aussiefy/static.py` reads it with the standard library alone, re-implementing the BERT
  normaliser, added tokens and WordPiece. Against `tokenizers` and Model2Vec over 2,783 dictionary and
  corpus texts it gives identical token ids, and vectors within 0.0002. Loading takes 13 ms, and encoding
  all 2,783 texts cold takes 0.25 s. `tests/architecture/test_static.py` re-checks the token ids whenever `tokenizers`
  is installed.
- **Cut-offs**: in `meta.json`, so each model carries its own. Lookup is 0.50: on held-back entries the
  80% model's related pairs had a median of 0.53, and about 5 in 30 queries let a genuinely wrong best
  match in, the same rate as stock MiniLM. Gaps is 0.60, as for stock MiniLM; no unrelated word reached it.
- **Precedence**: an installed and enabled sentence-transformers model, else the bundled one, else
  n-grams. `aussiefy model disable --bundled` switches the bundled model off.
- **Staleness**: `meta.json` records the sha256 of the dictionary files, and `aussiefy model status`
  reports `stale: true` once they change. Retraining is now one `release` command (see `README.md`).

Known weakness: like most embedders, it puts a word near its opposite on the same topic. "a heap of money"
brings up *a brass razoo*, *stony broke* and *skint* at about 0.68. The wrong-sense pairs only cover what
the dictionary's `!exclusions` name. Antonym pairs ("rich" vs "broke") would be the next thing to add as
negatives.

Git cost: every retrain adds about 14 MB (compressed) to the history. If retrains become frequent, move
`aussiefy/data/model/vectors.f16` to Git LFS or to a release asset fetched at build time.
