# Configuration, files and environment

aussiefy needs no configuration for its core: the dials are passed per call, and the dictionary is built in.
These are the settings, files and caches it does read or write.

## Environment

| Variable | Used by | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | `yarn`, `--surface`, `--rewrite`, `dev tag`, `judge run` / live `unharnessed` | The Claude API key. An `ant auth login` profile works instead |
| `AUSSIEFY_HOME` | model settings and the rewrite, yarn, tag and scrape caches | Where machine state lives (default `~/.aussiefy`) |

## Machine state: `$AUSSIEFY_HOME`

- `config.json` records which local model is installed, whether it is enabled, and whether the bundled model
  is switched off. It is written by `aussiefy embedder`. A corrupt file is an error (exit 2), never read as
  empty.
- `models/<name>/` holds an installed sentence-transformers model.

## Caches (under `$AUSSIEFY_HOME`, default `~/.aussiefy`)

| Directory | Written by | Keyed by |
|---|---|---|
| `cache/rewrite/` | `--rewrite` | The sentence, its draft, the planned phrases, level and vulgarity, seed, model and instructions |
| `cache/yarn/` | `yarn` | Everything that decides the reply: the text, plan, dials, seed, model, system prompt and tools |
| `cache/tag/` | `dev tag` | Model, shared vocabulary/system prompt, schema and staged item context; only accepted proposals are kept |
| `cache/judge/` | `judge run` | Packet, model and judge instructions |
| `cache/scrape/` | `dev scrape`, `dev ingest` | The URL (`--refresh` ignores it) |

The rewrite and yarn caches make those runs repeatable offline (`--surface` is not cached). Delete a directory
to force fresh calls. `yarn --no-cache` bypasses reads and writes; the Python yarn function and
`ClaudeRewriter` accept `cache=False`. Their `cache_dir` arguments override the location. The scraper
also accepts `cache_dir` in Python; the CLI has no cache-directory flag. A corrupt reply-cache JSON file
is an error (exit 2) naming the file to delete.

## Working files

The `dev` steps stage their output under `data/staging/` by default (see the [CLI reference](cli.md)); only
`dev review --apply` and `dev round --write` change the dictionary itself.

## Tunable data

Behaviour that is tuned rather than coded lives in `aussiefy/data/profiles.yaml`: each level's substitution
probabilities, frames, registers, garnish and drawl; the `swearing:` rates per vulgarity; and the `rewrite:`
thresholds for what counts as a difficult sentence. The [dictionary](dictionary.md) page lists the other data
files.
