# The bundled embedder: training, versions, lessons

`aussiefy/data/model` holds a small static embedding model. `lookup` and `gaps` use it to match by meaning
where the dictionary shares no spelling with the query: "knackered beyond belief" finds *buggered*. This
folder records the inputs and process for rebuilding it, releasing a new version, and what we learned building
the first one.

**Who needs torch?** Only whoever retrains the model. The package reads the model with the standard library
(`aussiefy/static.py`), so users never install torch, numpy or anything else, and nothing is downloaded.
Retraining needs the pinned CPU toolchain below. The initial small-dictionary release took about four minutes
on four CPUs; installation size and runtime depend on the dictionary, toolchain and machine. That historical
timing is not an estimate for the current larger dictionary.

| file | what it is |
|---|---|
| `recipe.yaml` | every setting: base model (pinned revision), seed, hold-out, losses, distillation, cut-offs, sources |
| `requirements.txt` | the training toolchain, pinned |
| `reference.yaml` | the checks each version is held to: wrong senses it must avoid, queries it must answer, known failures |
| `opposites.yaml` | concept pairs with opposite meanings (RICH / BROKE, HUNGRY / FULL), trained apart |
| `reports/X.Y.Z.json` | each version's evaluation, reference results, calibration and full provenance (never edited) |
| `research.md` | the study that chose the approach, with the comparison of setups |

## The approach

1. **Pairs from the dictionary.** Each concept trigger and each `replaces` is paired with the entry's form;
   the gloss with the form and its variants; the form with each riff. Wrong-sense pairs come from the
   triggers' `!exclusions`: `great !war|deal|…` gives "great war" paired against EXCELLENT forms. Opposites
   come from `opposites.yaml` (since 1.1.0): A's triggers and glosses are paired against B's forms, glosses
   and description, both ways. Extra sources can add more (see below).
   Recipe placeholders are bound before shared dictionary-language cleanup removes intensity, exclusions
   and grammar directives (`^person`, `^adj`, `^end`): constraints are not training words. Contextual imagery's
   conditional/related writer suggestions are not positive synonym pairs.
2. **Fine-tune** `all-MiniLM-L6-v2` on CPU. MultipleNegativesRankingLoss runs over the pairs, with no
   duplicate texts in a batch. ContrastiveLoss pushes the wrong senses apart (margin 0.5), and the
   opposites further (margin 0.75, so to cosine ≤ 0.25, well under lookup's 0.50 cut-off).
3. **Distil** with Model2Vec into static vectors at 256 dimensions. The dictionary's whole words are added
   as tokens, so *arvo* gets its own vector rather than the mean of its word pieces.
4. **Tune the static vectors** on the same pairs and losses. This step matters: distilling alone throws
   away most of what fine-tuning taught.
5. **Export** to the package's own format: float16 rows, the vocabulary, and `meta.json` with the version,
   cut-offs and provenance. `aussiefy/static.py` re-implements the BERT tokenizer exactly; this is checked
   in `tests/architecture/test_static.py` whenever `tokenizers` is installed.

A release runs this twice. The **evaluation run** holds back 20% of entries by id, so nothing from a
held-back entry is trained on, not even its words in the vocabulary. It scores every setup on those entries
(Recall@3 three ways, plus **opposites offered**: how often lookup would offer an opposite concept, over
held-back glosses and unused triggers, with the count recorded per run) and on the reference set, then calibrates.
The **release run** trains on everything, and is what ships.

## Releasing a version

```sh
python3 -m venv .venv
.venv/bin/pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r training/requirements.txt -e .
# change the recipe, the sources, the dictionary or the reference set; commit those changes first
.venv/bin/python scripts/train_embedder.py release --version X.Y.Z   # the next unused version
.venv/bin/python scripts/train_embedder.py check     # the shipped model against the reference set (no torch)
.venv/bin/python -m pytest -q
```

`release` refuses to export if a required reference check fails, and refuses to reuse a version number.
`--dest DIR` makes it a dry run that exports somewhere else. After it succeeds:

- **Read the report.** Compare models on the same current queries and dictionary as well as retaining their
  historical reports. Entry holdout protects the candidate's evaluation fit; a shipped model may already
  have seen some of those entries, so this is not necessarily a common unseen holdout. The roughly ±0.05
  Recall@3 variation observed on 1.0.0's 99 held entries is historical, not a current error bar.
- **Check the calibration.** If the cut-offs in `recipe.yaml` no longer sit where `calibration` says
  related and unrelated pairs separate, change them and release again under a new version.
- **Record it.** Add a row to the version history below.
- **Commit together:** `aussiefy/data/model`, `training/reports/X.Y.Z.json` and the README.

The work folder (`$AUSSIEFY_HOME/train/X.Y.Z`) holds the intermediate models and is never committed.

### Versioning

`MAJOR.MINOR.PATCH`, shown by `aussiefy embedder status` and in the embedder's name
(`bundled:aussie-static-1.2.0`).

- **MAJOR**: a change the reading code or the cut-offs' meaning depends on: the export format, the
  tokenizer, the base model, or the dimensions. It needs a matching change to `aussiefy/static.py`.
- **MINOR**: a retrain that changes the model's behaviour: changed sources (dictionary, extra pairs), a
  broader or refined reference set, or recipe settings.
- **PATCH**: a rebuild with the same recipe and sources, for example a toolchain bump, whose report shows
  no meaningful change.

Reports are immutable. A version's `meta.json` records the sha256 of the recipe, the reference set, the
script and the dictionary, plus the git commit and the toolchain. Anyone can tell exactly what built it.

### Extra sources

`recipe.yaml`'s `sources.extra_pairs` lists YAML files of pairs that aren't in the dictionary:

```yaml
- {anchor: rolling in money, positive: rich as Croesus}   # trained together
- {anchor: a heap of money, negative: stony broke}       # pushed apart (a wrong sense)
```

Prefer adding entries or triggers to the dictionary itself. Extra pairs are for what doesn't belong
there, such as antonym negatives.

### Replicability

- **What's pinned:** the base model's Hugging Face revision, the seed (split, data order, initialisation),
  every hyperparameter, and the toolchain.
- **Pair order:** WordNet neighbour relations are sorted by stable synset name before truncation. Source
  sense-frequency order, primary lemma order and recipe limits are preserved. Fresh-process checks on the
  current dictionary match all ordered positive, wrong-sense and opposite pair digests at both splits.
- **Weight reproducibility is observed, not guaranteed by provenance alone.** sklearn's PCA uses the full
  SVD. The 1.0.0 release reproduced, byte for byte on its original environment, the prototype's model.
  That historical result is not a guarantee for every later toolchain or machine.
- **Across machines or torch builds,** floating-point results can differ in the last bits. Compare the
  reports, not the hashes.

The frozen gap benchmark describes its original unknown-word intent. Later dictionary growth has covered
`sozzled`, `starved`, `kitchen` and `umbrella`; the fixture's comment about a release collision check does not
describe an implemented guard. Preserve its historical reports and treat current raw scores as fixed-query
diagnostics, not unseen generalisation or actual current false-fill rates. A refreshed coverage/source-exclusion
contract needs its own fixed cohort. The 90% precision bar governs enabling automatic gap filling; it is not
an additional blanket gate for every bundled-model replacement.

## Lessons from 1.0.0

- **Stock MiniLM doesn't know Australian slang.** It scores "knackered beyond belief" against "Exhausted,
  worn out." at 0.16, so lookup finds nothing. Fine-tuning on the dictionary is what teaches it.
- **Distilling a fine-tuned model to static vectors loses most of the gain.** Tuning the static vectors
  afterwards recovers it (Recall@3 0.18 → 0.36 on held-back glosses). The result matches the full
  fine-tuned transformer at a sixth of the size.
- **Distilled vectors are float16, and training them at a static model's learning rate (0.05) overflows to
  NaN.** Cast them to float32 for training, and back to float16 for shipping; float16 gave the same
  Recall@3.
- **Watch wrong senses, not just recall.** The full fine-tuned transformer learned girl ≈ woman ≈ *sheila*;
  the tuned static model didn't. The dictionary's `!exclusions` make good negatives.
- **Same topic, opposite meaning is the weak spot.** Static vectors average words, so opposites that share
  a topic sit close together: "a heap of money" brings up *stony broke*. Version 1.1.0 trains them apart
  (see the lessons from 1.1.0).
- **Calibrate against what a query really meets.** Random unrelated pairs never pass 0.33, so they make
  any cut-off look safe. The best wrong match across the whole dictionary has a median around 0.47, and
  many of those "wrong" matches are sibling senses that are fine. Read them by hand before choosing.
- **Hold out by entry, and build the vocabulary from training entries only.** Otherwise the held-back
  forms leak in.
- **128 dimensions cost 4 to 7 points of Recall@3, so 256 stays.** The size is 15.5 MB in the repo and
  14.5 MB in the wheel. Each version adds about 14 MB to git history; if releases become frequent, move
  `vectors.f16` to Git LFS or to a release asset.
- **Reference-set discipline: queries are written before measuring, and a query that fails goes to
  `known` with a reason, never out of the file.** For 1.0.0, the `must_not` rule was refined once after
  measuring. It had counted a wrong sense ranked third at 0.40, which lookup never shows; the rule now
  matches lookup (never reaches the cut-off, never the best match).
- **Network:** CPU torch wheels come from `download-r2.pytorch.org`, not only `download.pytorch.org`, and
  Hugging Face files come from `*.cdn.hf.co`. A proxy has to allow those.

## Lessons from 1.1.0 (opposites)

- **Measure what lookup does, not a proxy.** "An opposite's form in the top 3" moved by one query in 73 and
  hid the effect. "Would lookup offer an opposite" (an opposite entry reaching the cut-off) showed it:
  12% → 3% for the static model, and 22% → 4% for the full MiniLM.
- **Push away from what lookup compares with.** The first attempt paired queries only against the opposite
  concept's forms, and made things worse (reference 30 → 28). Lookup scores glosses, so the negatives
  now include the opposite's glosses and description.
- **The margin has to clear the cut-off.** ContrastiveLoss with margin 0.5 stops pushing at cosine 0.5,
  exactly lookup's cut-off, so a pair at 0.51 barely moved. Margin 0.75 gave the drop.
- **Opposite pairs don't teach meaning a phrase lacks.** "a heap of money" still lands on BROKE: it scores
  against RICH at only 0.29–0.34, in every build and in the full MiniLM too. Fixing it takes positive data,
  meaning RICH triggers for money phrases in the dictionary.
- **They don't generalise past the listed pairs either.** The control check "wide awake" (no AWAKE concept)
  is unchanged.
- **The cost was within noise:** Recall@3 0.36 / 0.72 / 0.42 → 0.35 / 0.71 / 0.40 in the evaluation run.
  "run off my feet" slipped from rank 3 to rank 4 (BUSY 0.36 → 0.34). It was already borderline and failed
  in 1.0.0's evaluation run, so it moved to `known` with that reason. It's still a regression, recorded as
  one.

## Lessons from the blocked 1.2.0 attempt (after the 2026-10-11 gap-fill round)

The gap-fill round grew the dictionary from 543 entries and 281 concepts to 681 and 353. A release
retrained on it was **blocked by the reference gate, and not shipped**. 1.1.0 stays bundled; it is stale,
but the round's new triggers and entries already work through the engine and lookup without a retrain.

- **The held-out numbers aren't comparable across dictionaries.** Every setup fell, n-grams included
  (0.21 → 0.15), because there are more forms to choose from (624) and more near-neighbour concepts (WIFE,
  SPOUSE, HUSBAND). The tuned model's lead over stock MiniLM held (0.30 vs 0.20; 0.66 vs 0.31).
- **Real lookups regressed on some queries.** "rolling in cash" → *stony broke* (1.1.0: *loaded*),
  "a good mate of mine" → *all good* and *nutter*, and "knackered beyond belief" also offered *carked it*.
  A mean-of-words model is pulled by single shared words ("good", "cash"), and a bigger dictionary has
  more glosses to be pulled towards.
- **More epochs didn't help.** 6 instead of 4, for the fine-tune and the static tune, stayed within ±0.02.
- **New concepts need their opposites.** Adding pairs for the new concepts (RICH / POOR, LOT_OF_MONEY /
  BROKE, LUCKY / UNLUCKY, …) brought opposites offered from 0.08 to 0.06, but didn't clear the gate. Keep
  `opposites.yaml` in step with `concepts.yaml`.
- **Next:** try WordNet synonyms as training pairs (plain-English coverage), and check glosses for words
  that over-attract (a gloss like "No problem, it's fine" pulls every query containing "good" or "fine").
  Then compare real lookups side by side with 1.1.0 before releasing, as done here.

## Lessons from 1.2.0 (WordNet, and getting past the gate)

- **Build a gap benchmark before measuring, and check it measures what the tool does.** The first version's
  everyday words (home, time, place) sit inside trigger labels ("go home"), which `aussiefy gaps` never
  scores, so they made every model look like it filled 85% of everyday words. Replaced after the first run.
- **WordNet helps gap words, most of all in the full transformer.** Right top-1 went 0.44 → 0.60 for the
  fine-tuned MiniLM and 0.30 → 0.37 for the shipped static model. Use the first sense only (*tired*'s second
  sense is "banal") and the "similar to" cluster, where WordNet keeps adjective synonyms.
- **Tuning static vectors costs plain-English generalisation.** The distilled-only model beat the tuned one
  on gap words (0.42 vs 0.33). Tuning moves word pieces that plain words share, for the sake of slang.
  Mapping the unseen tokens onto the tuning didn't help, because gap words aren't unseen, only their
  combinations are. Blending 0.7 tuned with 0.3 distilled kept recall and raised right fills from 0.16 to 0.26.
  Blend with one scale per matrix: normalising each row erases Model2Vec's frequency weighting and wrecks
  the model.
- **Push wrong senses away from glosses, as with opposites.** Lookup compares queries with glosses, so
  "great war" had to be trained away from EXCELLENT's glosses, not just its forms.
- **Gloss hygiene matters.** Glosses used "great" for excellent, and "great" also means big, so a big-sense
  query was pulled to *beaut*. Write glosses in words whose other senses aren't common wrong senses.
- **Judge a release by real lookups against the shipped version, not only the gate.** It's in the process
  now. 1.2.0 is better on most of a 16-query side-by-side: *a shady deal* → *dodgy*, *sleepy* → *stonkered*,
  and no *unit* for "under the weather". It is mixed on "a good mate of mine" (*mate*, *cobber*, but also
  *all good*), and lost *fraudulent* → *dodgy*.
- **Precision of automatic gap-filling.** On the benchmark, filled right / (right + wrong) is 72% for the
  static model and 94% for the full fine-tuned MiniLM. The engine's gap-filler therefore stays off by
  default with the bundled model (the bar was 90%); a torch install could clear it.

## The 1.3.0 trial (after the classics round; not released)

The classics round grew the dictionary to 893 entries and 493 concepts: 835 training entries and 10,140 pairs.
We ran two dry-run releases (`release --version 1.3.0 --dest ...`). One used the shipped recipe. The other set
`pairs.trigger_concepts: first`, which pairs each trigger only with forms whose first concept is the trigger's
own. Both reports are in `reports/trials/`.

- **Both stopped at the gate, 29/30, on the same new failure.** "girl" now ranks WOMAN (*sheila*) first,
  the wrong sense the check exists for. The shipped 1.2.0 still passes 30/30 against the new dictionary, so it
  stays.
- **`first` half-works on the chains.** "very tired" now ranks TIRED first (DRUNK first before), but DRUNK
  is still in the top 3, so the known failure stands. It raised gloss→form (0.27 against 0.25) and
  form→concept (0.36 against 0.35), and lowered gap right@1 (0.37 against 0.42).
- **Before the next attempt:**
  - find what pulls "girl" to WOMAN (likely the new GIRLFRIEND concept, or classics glosses using "girl");
  - add the misses the yarn agents hit in real lookups to `reference.yaml`, written before measuring:
    "honest" returns *dodgy*, "put up with" returns *chuck it in*, "sleep" returns *have a root*, "dying"
    returns *toey*, "very cold" returns beer (`../research/retellings-2026-10-11/COMPARISON-2.md`);
  - then decide `first` against `all` on the larger set.

## The second 1.3.0 trial (after the third everyday pass; not released)

After the fairdinkum, second-pass and third-pass rounds the dictionary had 1,198 entries (1,133 training
entries, 12,151 pairs). A release run with the shipped recipe (`reports/trials/1.3.0-trial-2026-10-14.json`):

- **It stopped at the gate, 32/33.** "a top bloke" now reaches *a mongrel bastard* (0.52 against the 0.50
  cut-off), though GOOD_PERSON and SCOUNDREL are already trained apart in `opposites.yaml`; its top three are
  right (MAN, GOOD_PERSON, WILD_ONE). The girl/WOMAN failure of the first trial is gone, and two known failures
  now pass ("run off my feet", "wake up").
- **It isn't clearly better anyway.** Against 1.2.0's report, the tuned static model moves gloss→form 0.264 →
  0.286 (noise), form→concept 0.336 → 0.304, and gap-fills wrong 0.093 → 0.163; opposites offered 0.088 → 0.102.
- **1.2.0 stays.** It still passes 33/33 against the grown dictionary, and the new rounds' entries work through
  the engine's triggers and lookup's word matches without it.
- **Before the next attempt:** find what pulls "a top bloke" to the rotten-person glosses (the "bloke"/person
  words shared by MAN, GOOD_PERSON and SCOUNDREL glosses), and why form→concept fell with more entries (the
  multi-concept chains below are the likely cause).

## The maintenance trial and ordering correction, 17 October 2026

The 1,254-entry dictionary supplies 1,189 training entries. The first current trial passed 30/33 required
references, failing on a great war, a top bloke and honest, so 1.2.0 stays and 1.3.0 is not released. Its interrupted
evaluation fit was reused only for an offline-cache metadata repair. A subsequent audit found hash-dependent
WordNet neighbour selection; the historical trial is retained with that limitation, not treated as an
exactly replayable experiment. Neighbour sorting now stabilises every ordered pair digest across fresh
processes while preserving sense/lemma priority and recipe limits. The correction was committed as `72015dc`
before fresh evaluation and full-data fits. Those pass 28/33 and 31/33 required references respectively;
the full candidate fails girl and a good mate of mine and is rejected before export. Shipped 1.2.0 still
passes 33/33. The recipe, cut-offs and required checks remain unchanged. See the
[maintenance evidence](../research/maintenance-2026-10-17/model-maintenance.md) for both trials, fixed-query
lookup comparisons and the separate meaning-specific training questions.

## Ideas for the next version

- Break the chains between concepts that multi-concept entries create. *stuffed* (TIRED, BROKEN, FULL) and *full
  as a goog* (FULL, DRUNK) pair TIRED triggers with forms that FULL and DRUNK triggers also pair with, so the
  model learns tired ≈ full ≈ drunk; "very tired" ranks DRUNK first (a known failure). One option: pair each
  trigger only with forms whose *first* concept is the trigger's, or add TIRED / DRUNK and FULL / TIRED as
  wrong-sense pairs.

- Give RICH phrase-level triggers ("rolling in money", "made of money") so "a heap of money" has somewhere
  to go. That's a dictionary call, not a training one.
- Expand trigger alternations (`it|that|this {be} impossible`) into separate phrases before pairing. Today
  they're paired as written, and the opposite pairs skip them.
- In lookup, "absolutely starving" is caught by the intensifier n-grams (*bloody*, *too right*) before the
  model's HUNGRY match. That's lookup ranking, not the model.
- Broaden `reference.yaml`, especially with plain queries agents actually send to `lookup`.
- Repeat the evaluation run over a few seeds, to put error bars on Recall@3.

## Version history

| version | date | change | evaluation run: Recall@3 (gloss→form / concept's forms / form→concept) | reference |
|---|---|---|---|---|
| 1.0.0 | 2026-10-11 | first release: recipe, reference set, bundled by default. 497 entries, 3,538 pairs, 307 wrong-sense pairs | 0.36 / 0.72 / 0.42 (stock MiniLM 0.32 / 0.42 / 0.28; n-gram 0.21 / 0.27 / 0.23); opposites offered 0.12, measured afterwards with the 1.1.0 metric | 17/17; evaluation-run model 16/17 |
| 1.1.0 | 2026-10-11 | opposites trained apart: 29 concept pairs, 2,246 opposite pairs, margin 0.75. Reference gains 14 opposite checks; 3 that no build passes are `known` (one, "run off my feet", a borderline regression) | 0.35 / 0.71 / 0.40; opposites offered **0.03** | 29/29; evaluation-run model 28/29 |
| (1.2.0-rc1) | 2026-10-11 | **not released**: retrained on the gap-fill dictionary; blocked by the reference gate (rolling in cash, under the weather, a good mate of mine) and real-lookup regressions | 0.30 / 0.66 / 0.28; opposites offered 0.06 (larger dictionary: not comparable with the rows above) | 27/29 |
| 1.2.0 | 2026-10-11 | the gap-fill dictionary (681 entries, 353 concepts), WordNet synonyms (first sense, 6 per trigger), a 0.7 / 0.3 blend of tuned and distilled vectors, wrong senses pushed from glosses too, and five glosses no longer using "great" for excellent. Gap benchmark: right top-1 **0.37**, filled right 0.23, filled wrong 0.09, everyday filled 0.04 (rc1: 0.30 / 0.09 / 0.16) | 0.26 / 0.62 / 0.34; opposites offered 0.09 | 29/29 (and "having a chinwag" fixed); evaluation-run model 27/29 |
| (1.3.0-trial) | 2026-10-11 | **not released**: retrained on the classics dictionary (893 entries, 493 concepts), with and without `trigger_concepts: first`; blocked by "girl" ranking WOMAN first | 0.25 / 0.57 / 0.35 (first: 0.27 / 0.56 / 0.36); gap right@1 0.42 (first: 0.37) | 29/30 (both) |

## Maintenance measurement, 2026-10-15

The [maintenance check](../research/maintenance-check-2026-10-15/README.md) reruns 1.2.0 against the current
dictionary: 33/33 required references pass and all 16 tracked failures remain. It records raw semantic checks and
current toolkit queries separately, with model/reference/dictionary hashes. No weights were trained or
exported. Default automatic gap filling remains off; its current benchmark precision is below the 90% bar.
A fresh writer/independent-judge Dinkum comparison is pinned but unrun. Existing version reports remain immutable.
