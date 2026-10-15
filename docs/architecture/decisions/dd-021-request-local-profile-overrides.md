# DD-021: Request-local advanced profile overrides

Status: Accepted

Date: 2026-10-15

Extends: [DD-019](dd-019-explicit-composable-document-policy.md), [DD-020](dd-020-document-composition-state.md)

## Context

Exact document behaviours were configurable, but their engine probabilities, limits, spacing, drawl,
swearing weights and rewrite thresholds still required dictionary edits. Callers need to compose flavour
and technical fidelity independently, and inspect the defaults rather than supply every setting.

## Decision

Add `document_config.profile` to the existing shared configuration object. It overrides the selected level
and vulgarity profiles for one request. General keeps ordinary document defaults; Custom keeps optional
document behaviours off. Both inherit the same numeric dial defaults. Supplying a probability does not
activate a placement excluded by the document allow-list. Existing direct policy arguments keep their roles.

Partial maps inherit missing keys; lists replace. Validate names, types, numeric ranges and stretch bounds
at the request boundary. Snapshot nested values immutably and resolve through `policy.resolve`; never mutate
the dictionary. Valid but ineffective combinations remain the caller's responsibility, rather than triggering
implicit adjustments. Grammar, source markup, entry eligibility and vulgarity limits remain independent.

`profile.py` owns advanced tuning and complete JSON-ready inspection snapshots. Document operations and
explain expose `profile_config`, reusable as the nested profile mapping. Yarn briefs carry `PROFILE_CONFIG`
and session tools retain the same request configuration. Lint suggestions also forward these overrides.

Placement limits combine clean and sweary garnish. The sentence budget combines connective/opener/aside/tag
channels; tails, riffs and the one document closer keep their own placement limits. Spacing follows source
sentence ordinals across Markdown units. Zero swear weighting excludes candidates, including when every
alternative is vulgar. These changes intentionally correct existing consumers of the now-public controls.

## Consequences

Default seeded outputs can change where the old channels exceeded shared limits or budgets. Golden diffs
are reviewed alongside isolated zero/one-probability, limit, gap, frame, drawl, swear and rewrite tests.
Dial names still describe baselines; effective overrides describe the actual request. Quality/refinement
studies follow once the controls are settled; mechanical tests do not substitute for a style assessment.
