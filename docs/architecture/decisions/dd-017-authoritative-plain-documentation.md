# DD-017: Authoritative plain sources and deterministic published documentation

- **Status:** accepted
- **Date:** 2026-10-15
- **Extends:** [DD-015](dd-015-source-preserving-markdown.md), [DD-016](dd-016-reconcile-source-capabilities.md)

## Context

Published documentation should use the toolkit's Australian voice while editable instructions and examples
remain easy to maintain. Translating an output again loses the original meaning and compounds changes;
checking executable examples in both copies duplicates the same contract.

## Decision

An explicit maintainer-owned map pairs plain Markdown under `docs/plain/` with its existing public paths.
Root documentation uses `docs/plain/root/`. The publisher translates strict source spans at level 5, dad,
seed 0, with an explicit offline fallback; each output links to its source. It remaps local destinations
between the two placements, preserving labels, fragments, external URLs, headings, tables and code.

Executable documentation tests discover authoritative sources and ungenerated current documents once.
Generated freshness and links in both trees are required by promotion. A source edit can precede local
regeneration during development. Legal texts, agent instructions, copied standards, ADRs and historical
reviews remain plain, as do co-located research/training/corpus guides. There is no recursive publication.

## Consequences

Dictionary changes can intentionally change published prose; contributors review regeneration like other
outputs. Release bumping edits the authoritative changelog and regenerates publication while keeping
release headings and code examples intact. No live model or external service controls publication.
