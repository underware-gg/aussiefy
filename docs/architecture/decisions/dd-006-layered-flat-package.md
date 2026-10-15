# DD-006: A layered, flat package, with the layering enforced by a test

- **Status:** Accepted
- **Date:** 2026-10-12, the second design review (`docs/architecture/reviews/design-review-2-2026-10-12.md`,
  finding L1 and "Not carried forward").

## Context

The first design review found that the core pipeline already pointed inward: the engine stages imported
nothing from the toolkit, LLM modes, scraper or CLI, and so were testable on their own. The second review found
about ten function-level imports that hid that layering, and weighed splitting the package into subpackages
(`engine/`, `toolkit/`) to make it explicit.

## Decision

Keep one flat package, document its layers (public API, surfaces, toolkit, LLM modes, engine, dictionary,
similarity, maintainer tools) in [package-layout.md](../package-layout.md), and enforce the rule that the engine
and the dictionary import nothing from the layers above them with a test, `tests/test_layers.py`. Hoist the
in-package imports, keeping deferred imports only for optional dependencies and the CLI's lazy commands.

## Consequences

- The core stays usable and testable without the toolkit, Claude or the CLI, and a violation fails the suite.
- Import paths stay short and stable (`aussiefy.engine`, `aussiefy.lint`).
- The layer of each module is recorded in a document and a test rather than in the directory structure, so
  both must be updated when a module is added. One exception is allowed and named in the test:
  `embed.make_embedder("local")` reaches `models.py` for the installed model's settings.
