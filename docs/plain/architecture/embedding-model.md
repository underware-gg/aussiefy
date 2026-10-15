# The bundled embedding model

`aussiefy/data/model` holds a 15 MB static embedding model, aussie-static, which `lookup` and `gaps` use to
match by meaning. What uses it, and how to switch it, is in the
[functional reference](../functional/embedding.md); the decision to make similarity pluggable and local is
[DD-007](../../architecture/decisions/dd-007-pluggable-local-embeddings.md).

## How it is built

All-MiniLM-L6-v2 is fine-tuned on the dictionary's own pairs (triggers, glosses, riffs, and the wrong senses
its `!exclusions` name), distilled into static vectors with Model2Vec, then tuned again. On held-back entries
it matches the full fine-tuned transformer, at a sixth of the size, and beats stock MiniLM.

## How it is read

`aussiefy/static.py` reads the model with the standard library alone: no torch, no numpy, no download. It
re-implements the BERT tokenizer exactly, which `tests/architecture/test_static.py` checks whenever `tokenizers` is
installed. Users therefore never install a machine-learning stack.

## Versions

The model is versioned (`aussiefy embedder status` shows which), and each version is rebuilt reproducibly
from `training/recipe.yaml` with one command. After dictionary changes, `status` reports the model as `stale`.
Licensing of the base models is in [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md).

The full approach, how to retrain and release, the lessons from each version and the version history are in
[training/README.md](../../../training/README.md); the study that chose the approach is
[training/research.md](../../../training/research.md).
