# DD-007: Pluggable, local similarity, with a bundled static model

- **Status:** Accepted
- **Date:** the pluggable fallback was in place from the initial build; the bundled model was chosen before
  model version 1.0.0 (`training/research.md`) and ships in v0.1.0 (2026-10-12). Recorded retrospectively on
  2026-10-13.

## Context

Some matching has to be by meaning, not spelling: a lookup for "knackered beyond belief" should find
*buggered*, and gap finding needs the nearest concept to a word. Sentence-transformer models do this, but bring
PyTorch (1.3 GB on CPU, more with CUDA), a download, and outputs that change when the model does. Translations
must stay deterministic ([DD-003](dd-003-deterministic-context-keyed-rolls.md)), and the core must run offline
with PyYAML alone ([DD-001](dd-001-no-nlp-dependency-in-the-core.md)).

## Decision

Make similarity pluggable behind one `Embedder` interface, with local implementations only:

- The engine's detection fallback defaults to character-trigram similarity, which needs no model, and uses a
  meaning model only when asked (`--embedder bundled|local`).
- `lookup` and `gaps` default to a bundled static model: MiniLM fine-tuned on the dictionary's own pairs,
  distilled to static vectors, shipped in `aussiefy/data/model` (about 15 MB) and read with the standard
  library alone.
- A bigger sentence-transformers model can replace it, installed and enabled only by explicit commands.

## Consequences

- Users get meaning-based lookup with no extra install and no network.
- Default translations never change when a model is retrained or installed.
- The bundled model must be retrained and released when the dictionary changes (`status` reports it as
  `stale` until then); the process is in `training/README.md`. Each retrain adds about 14 MB to the git
  history.
- `aussiefy/static.py` must re-implement the tokenizer exactly, which a test checks.
