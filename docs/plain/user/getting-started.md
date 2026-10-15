# Getting started

## Install

aussiefy needs Python 3.10 or later. The core depends on PyYAML and markdown-it-py.
These commands install the `v0.1.0` release. For development, check out `dev` in a clone and install
in editable mode. A full commit SHA can be used in place of the tag.

```sh
pip install "git+https://github.com/underware-gg/aussiefy@v0.1.0"                  # core
pip install "aussiefy[llm] @ git+https://github.com/underware-gg/aussiefy@v0.1.0"   # with an extra
```

| Extra | Adds | Needed for |
|---|---|---|
| `llm` | anthropic | `yarn`, `--surface`, `--rewrite` and `dev tag` |
| `mcp` | mcp | the `aussiefy-mcp` server |
| `embeddings` | sentence-transformers | a bigger local embedding model |
| `scrape` | requests, beautifulsoup4 | `dev scrape`, and fetching the local reference texts |
| `dev` | pytest, ruff, mcp, numpy, requests, beautifulsoup4, tokenizers | working on aussiefy itself: see [CONTRIBUTING.md](../root/CONTRIBUTING.md) |

From a clone, install in editable mode instead: `pip install -e '.[llm]'`.

## Translate a text

Give `aussiefy` the text itself, a file path, or nothing to read stdin:

```sh
aussiefy "I'm extremely busy." -l 4 -s 7          # → I'm flat out like a lizard drinking.
aussiefy story.txt -l 3
echo "I'm exhausted." | aussiefy -l 4
```

At level 5 the engine goes all out:

```
$ aussiefy "Good grief, are you crazy? You're overreacting, you're stupid and all talk, and I'm extremely busy cleaning up after you." -l 5 -s 1
Strewth, do ya 'ave kangaroos loose in yer bloody top paddock? Oi, yer carryin' on like a pork chop, yer thick as two short planks and a big-noter, and I'm flat out cleaning up after you.
```

## Choose how Aussie, how rude, and how much liberty

Three dials control the telling, each by number or name:

- `-l/--level`: how Aussie, from 1 (`tourist`) to 5 (`swaggie`, the default).
- `--vulgarity`: how rude, from 0 (`nan`, no swearing) to 3 (`tradie`, anything goes). By default it follows the
  level: `nan` at levels 1-2, `dad` at 3-4, `uncle-bob` at 5.
- `-e/--embellishment`: liberty in the telling, from 0 (`deadset`, straight) through 1 (`dinkum`, limited
  colour) to 2 (`troppo`, a performance). General defaults to `dinkum` across translation and retelling.
  Auto and named document types use their preset's default; an explicit dial overrides it. See [translation controls](../functional/translation-controls.md).

Level and vulgarity are independent, so you can have either without the other:

```sh
aussiefy "..." -l swaggie --vulgarity nan      # full Aussie, no swearing
aussiefy "..." -l tourist --vulgarity tradie   # plain English from a foul mouth
```

What each setting does is in the [dials reference](../functional/dials.md).

## Get the same result again, or a different one

The rule engine gives the same output for the same text, dials, settings and seed. Two settings control variability:

- **The seed.** It is 0 by default, so a text comes out the same on every run. `--seed 3` gives another
  version, and `--seed random` picks a seed and prints it to stderr, so you can repeat a run you liked.
- **`--variety N`** (`variety=N` in Python) sets how far down the list of fitting terms a choice may go. With 1,
  each slot takes its best-fitting eligible term at that point (on meaning, intensity and register).
  Earlier swaps can change repetition weights, so another seed can still change the chosen term; variants
  and drawl can also vary. With 2 or 3, a choice is weighted among that
  many best fits. With 0, the default, it is weighted over every eligible term, which gives the most
  variety and sometimes a looser fit.

```sh
aussiefy -l 4 --variety 1 "I'm exhausted and starving."   # always the best fit: buggered, starvin'
aussiefy -l 4 --seed random "I'm exhausted and starving."  # zonked, stuffed, knackered...; seed printed
```

## See why it chose what it did

```sh
aussiefy "Are you crazy?" --explain           # every decision, on stderr
aussiefy "Are you crazy?" --explain --brief   # the same, without the rejected candidates
aussiefy "Are you crazy?" --json              # text, plan and explain records as JSON
```

What the explain report contains is described in [explain.md](../functional/explain.md).

## Narrow or widen the slang

```sh
aussiefy "..." --region qld                     # prefer regional words (togs, not cozzie)
aussiefy "..." --registers current,dated        # allow dated slang as well as current
aussiefy "..." --unlock not_aussie,fabricated   # allow entries held back for those flags
```

Gated entries are held back for a reason, such as doubtful attestation; `--unlock all` allows every one.

## Look up a word or check a draft

```sh
aussiefy lookup very tired                        # Aussie options for a meaning
aussiefy lookup goog                              # what a term means
aussiefy lint -l 5 --original story.txt < draft.txt   # check your own Aussified draft
aussiefy show lizard                              # dictionary entries by id, form or concept
```

These are the same tools agents use: see [agents.md](agents.md).

## Add your own entries

1. Write entries in a YAML file, in the [entry format](../functional/dictionary.md#entries).
2. Check them: `aussiefy validate --dict my-entries.yaml`.
3. Use them with any command: `aussiefy "..." --dict my-entries.yaml`. `--dict` takes a file or a directory,
   and can be repeated.

In Python, build a translator over the extended dictionary and pass it to any function:

```python
from aussiefy import Translator, load_dictionary, lookup

tr = Translator(load_dictionary(["my-entries.yaml"]))
tr.translate("I'm extremely busy.", level=4).text
lookup("very tired", translator=tr)
```

## Use it from Python

```python
from aussiefy import translate

translate("I'm extremely busy.", level=4, seed=7).text   # "I'm flat out like a lizard drinking."
```

The full API is in [toolkit.md](../functional/toolkit.md).

## When something goes wrong

Every command exits non-zero with a message on stderr when it can't do what was asked; the
[exit codes](../functional/cli.md#exit-codes) say which kind of problem it was. Known limitations are listed in
[limitations.md](../functional/limitations.md).
