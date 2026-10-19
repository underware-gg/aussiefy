# Architecture documentation

How aussiefy is built, and why. The current design is described in the overviews below; the reasons behind it
are in the decision records, which are kept as history rather than rewritten.

## Overviews

| Document | Summary |
|---|---|
| [pipeline.md](pipeline.md) | The five engine stages (parse, detect, select, realise, garnish), and where the optional LLM passes fit |
| [package-layout.md](package-layout.md) | The package's layers, the module in each, the layering rule and how it is enforced |
| [determinism.md](determinism.md) | Context-keyed seeded rolls, what they guarantee, and what is kept outside the deterministic core |
| [embedding-model.md](embedding-model.md) | How the bundled static embedding model is built, read and versioned |

## Decisions and reviews

- [decisions/README.md](decisions/README.md): the decision router, indexing every decision record (DD-001 onwards).
- [reviews/README.md](reviews/README.md): repository and focused design reviews.

## Co-located design documents

- [training/README.md](../../../training/README.md) and [training/research.md](../../../training/research.md): the
  embedding model's training approach, lessons and version history, and the study that chose it.
