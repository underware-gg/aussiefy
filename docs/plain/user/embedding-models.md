# Managing the embedding model

`lookup` and `gaps` use a small embedding model to match by meaning, so "knackered beyond belief" finds
*buggered*. aussiefy ships one, and it works out of the box: you only need this page to check it, switch it
off, or try a bigger one. Default translations never use it. What uses which model is in the
[embedding reference](../functional/embedding.md).

## Check which model is in use

```sh
aussiefy embedder status
```

`active` names the model in use. `stale: true` means the dictionary has changed since the bundled model was
trained; it still works, but may miss the newest entries.

## Switch the bundled model off, or back on

```sh
aussiefy embedder disable bundled   # n-grams only
aussiefy embedder enable bundled
```

## Try a bigger model

A sentence-transformers model can replace the bundled one. It is installed and enabled only when you ask:

```sh
aussiefy embedder install --dry-run   # print the steps first
aussiefy embedder install             # pip-installs CPU PyTorch and sentence-transformers, downloads all-MiniLM-L6-v2
aussiefy embedder enable              # start using it
aussiefy embedder disable             # stop using it
aussiefy embedder remove              # delete the model
```

Install options:

- `--torch pypi` uses PyPI's default PyTorch build instead of the CPU-only index.
- `--torch skip` if PyTorch is already installed.
- `--from PATH` copies a saved sentence-transformers model folder instead of downloading (for offline
  machines).
- `--enable` enables the model straight after installing.

If a download is blocked, the error says which option to try. State lives in `$AUSSIEFY_HOME` (default
`~/.aussiefy`).

Stock MiniLM doesn't know the slang, so it is mostly useful as a base for retraining; the bundled model, which
is tuned on the dictionary, beats it on held-back entries. Retraining is covered in `training/README.md`.
