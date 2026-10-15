# DD-019: Explicit, composable document behaviour

Status: Accepted

Date: 2026-10-15

Extends: [DD-016](dd-016-reconcile-source-capabilities.md), [DD-017](dd-017-authoritative-plain-documentation.md)

## Context

Automatic genre detection affected more than default embellishment: it restricted garnish, quotes, person
swears, technical vocabulary, imperative recognition and datelines. Explicit dial values could not override
all of those decisions. Technical documentation remained restrained even at Swaggie/Dinkum.

## Decision

General is the default document type. Auto explicitly opts into the existing classifier; named types select
presets. Custom starts with optional document behaviours disabled, including optional retelling length checks.
Core vocabulary substitution, seeded choices, vulgarity limits and selected markup protection remain active.

All document operations accept `document_type` and the same strict `document_config` mapping. Resolve the
selected preset, explicit dials and then exact advanced overrides. Lists replace lists; false, zero and empty
lists are meaningful. Unknown settings and invalid values fail at the boundary. Immutable snapshots prevent
caller mutation changing a running session. Effective configuration and selection provenance are reported.

Document behaviours cover garnish/openings, neutral-person swears, quoted wording, terminology domains,
imperatives, datelines, formal-sentence rework, and the yarn draft, retention, length and performance guidance.
Consumers use the resolved controls rather than branching on detected names. Auto reads the complete original
once, including Markdown units and checks of drafts. A source-free guide cannot select Auto.

Public documentation explicitly selects General, Swaggie, Dinkum, Dad and seed 0, protects Technical vocabulary,
and disables formal-sentence rework. Every generated document carries the same settings notice and a link to
its corresponding authoritative plain source. Legal texts and historical records retain their plain form.

## Consequences

Defaults intentionally change. Callers wanting detected behaviour pass Auto; explicit embellishment can retain
an older retelling choice. Advanced overrides apply consistently across Python, CLI, MCP, Markdown and yarn
sessions. Numeric dial labels describe presets; effective override values are also reported.

Model briefs carry the effective behaviour contract. Mechanical checks enforce quoted wording, datelines,
length and existing factual/markup constraints; semantic style quality still requires evaluation.
