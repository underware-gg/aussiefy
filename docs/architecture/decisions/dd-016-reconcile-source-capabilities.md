# DD-016: Reconcile committed source capabilities within the repository layers

- **Status:** accepted
- **Date:** 2026-10-14
- **Extends:** [DD-015](dd-015-source-preserving-markdown.md)

## Context

The source branch advanced 91 commits past the ported corpus, adding genre/embellishment, dialect, POS,
extended Markdown/MDX, ingestion and evaluation. It also embedded document parsing in the engine and read
genre configuration globally. This repo already has an explicit strict Markdown adapter and provenance gate.

## Decision

Import the pinned source snapshot `95036e146da88fb497dae94e8532000913d92bcd`. Keep syntax selection above the
plain engine in the shared translation route. The engine consumes format-independent opaque spans and context;
its tokeniser recognises those runs, and restoration enforces their integrity. Format-specific phonetic
protection arrives as a range provider, using the existing phonetic-stage seam.

Preserve distinct explicit contracts: `markdown=True` retains whole protected constructs and document-unit
evidence; `markup=` retains the source's extended sentence/MDX behaviour. Lint, verification and yarn share
the extended protection inventory. Resolve whole-document genre/English once for strict units. Load genre
configuration and POS vocabulary through the dictionary loader, leaving the model/classifier pure.

Retain existing validation, canonical term/gate/style rules, typed MCP diagnostics and shared atomic fetch
persistence. Move incoming tests to their documentation-layer owners. Attribute POS as bundled MIT-derived
material; source-linked research inherits its corpus licences. Corpus LGPL/GPL texts remain outside the wheel
licence set. Preserve local-only originals/packets/logs and full aggregate exports ignored locally, publishing
sanitised copies with those entries removed.

## Consequences

Both document capabilities survive, with deliberately different contracts instead of an implicit switch.
The selected dictionary governs custom genre policies. Incoming plain-text goldens remain the source baseline;
new data is not retrained. Research can be inspected with explicit attribution while local-only decisions
remain enforced. Further source commits after the pin are a separate reviewed integration.
