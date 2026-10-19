# Similarity and embedding models

Some features match by meaning rather than spelling, where the dictionary's words share no letters with the
query: "knackered beyond belief" finds *buggered*. This page says which features use a similarity model, and
which one.

## Who uses what

| Feature | Model used | How to choose |
|---|---|---|
| `lookup` (and so the agent toolkit) | The configured one: an installed local model if enabled, else the bundled model | `aussiefy embedder enable` or `disable` |
| `aussiefy gaps` | The configured one, for the nearest-concept guess | `--embedder` `ngram`, `bundled` or `local` |
| The engine's concept-detection fallback | Character trigrams (`ngram`) | `--embedder` `ngram`, `none`, `bundled` or `local` on `translate` |

The engine uses a meaning model only when asked, so default translations stay deterministic and do not change
when the model does (see [determinism](../architecture/determinism.md)).

- **`ngram`:** character-trigram similarity, with no dependencies. It is deterministic and catches misspellings
  and morphological variants.
- **`bundled`:** the static model shipped in `aussiefy/data/model` (about 15 MB), read with the standard
  library alone: no torch, no numpy, no download. How it is built is described in
  [the architecture layer](../architecture/embedding-model.md).
- **`local`:** an installed sentence-transformers model (the `embeddings` extra), installed and enabled only
  explicitly. Selecting `--embedder local` requires an installed usable model; it raises an error rather
  than using the bundled model. Only the configured default cascades between available models.
  Stock all-MiniLM-L6-v2 doesn't know the slang, so it is mostly useful as a base for retraining.
- **`none`:** no similarity fallback.

## The `embedder` command

`aussiefy embedder status` shows which model is in use and the bundled model's version. After dictionary
changes, `status` reports the bundled model as `stale`, until a new version is trained.

| Action | Effect |
|---|---|
| `status` | Show the state as JSON |
| `install` | Pip-install CPU PyTorch and sentence-transformers, and download the model (or copy it with `--from PATH`) |
| `enable [bundled\|local]` | Start using the model (default `local`) |
| `disable [bundled\|local]` | Stop using it; `disable bundled` leaves n-grams only |
| `remove` | Delete the installed local model |

All options are in the [CLI reference](cli.md). State lives in `$AUSSIEFY_HOME` (default `~/.aussiefy`): see
[configuration](configuration.md).

## Current measurement

The [2026-10-19 retrain](../../../research/semantic-model-2026-10-19/README.md) prepares model 1.3.0 against
the reviewed dictionary using the unchanged pinned recipe. The full-data fit and exported package reader
both pass all 33 required raw-model checks. The evaluation fit passes 32/33; its separate girl-query failure
is retained. Existing reports and the earlier
[maintenance check](../../../research/maintenance-check-2026-10-15/README.md) remain historical evidence.

That historical lookup comparison covers 18 fixed historical queries plus eight source-audit queries under
the runtime used on 2026-10-19. It does not establish unseen generalisation or universal superiority: that
run offered defo for probably and hurry terms for wake up, and ranked pub above coldie for the cold-one
query. Current lookup applies bounded source-meaning checks before offering lexical or model suggestions;
see [the toolkit](toolkit.md). Updated beer reference labels follow corrected meanings without
changing queries, ranking rules or required status. Automatic gap filling remains off by default.
