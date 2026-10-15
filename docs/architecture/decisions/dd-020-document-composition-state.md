# DD-020: Shared document state across source-preserving units

Status: Accepted

Date: 2026-10-15

Extends: [DD-015](dd-015-source-preserving-markdown.md), [DD-019](dd-019-explicit-composable-document-policy.md)

## Context

Strict Markdown translates individual physical-line/inline gaps to retain exact source bytes and local
explanation offsets. Resetting translation state in each gap repeats garnish beyond its document limits and
can insert an opener halfway through a sentence, especially after code or a link.

## Decision

Retain the source units and local evidence. Their internal composition context shares one request-local
TextState and supplies whole-source sentence positions, structural quiet regions and fragment boundaries.
Garnish spacing uses whole-source positions; partial sentences receive no sentence garnish or riff. Later
complete sentences remain eligible. Only the final prose unit can attempt a closer, when its source sentence
ends there. Protected bytes and public surface parameters remain unchanged.

Composition describes source structure; it does not infer or alter document-type controls. Explicit policy
resolution and the advanced overrides remain separate. Plain translation retains its existing pipeline.

## Consequences

Markdown choices and garnish depend on the preceding units in the same document. Repeated calls remain
seeded and reproducible. No state survives a request. Hard wraps and inline constructs can reduce garnish
opportunities; vocabulary and drawl still apply to eligible prose. Public unit records retain local offsets.

Tests: [document composition](../../../tests/functional/test_markdown_composition.py),
[Markdown preservation](../../../tests/functional/test_markdown.py),
[document controls](../../../tests/functional/test_document_policy.py).
