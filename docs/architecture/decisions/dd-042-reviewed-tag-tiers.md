# DD-042: reviewed tag tiers and shared subject placement

Date: 2026-10-21

Status: accepted implementation decision; product placements remain subject to the recorded curator rulings.

## Context

The slice 0–1 spec review introduced ED9 after Rob clarified that Nan means polite colloquial Australian,
with familiar cultural exceptions. Literal topic words cannot decide placement: dunny is Nan’s everyday
word; the duck’s crotch comparison is the polite alternative beside the arse version. Chunder and spew
are crass enough for Dad. Tobacco is a separate mature theme starting at Dad. The previous binary set
cannot represent a Nan term within a theme which normally starts higher.

## Decision

Store an optional tier inside each canonical theme tag; a bare name inherits its theme’s default start.
Keep names and parsed explicit tiers as internal immutable tuples, with one canonical themes serializer.
Theme names and monotonic starts derive from themes.yaml, rather than a second Python enumeration.
Validate spelling and booleans at caller parsing, then known names against the selected dictionary at resolution.

Resolve one immutable ThemePolicy containing the caller tier, the data’s starts and exact overrides.
A term passes only when every tag’s tier fits. True admits every strength of that subject; false rejects
all strengths. The swear cap remains independent. A higher-cap editor probe keeps the original policy.
The binary permitted_themes compatibility property and theme_permissions response map describe defaults,
not every per-term exception. They are not sufficient to reconstruct the caller’s graded policy.

Every selection and bounded acceptance path receives the same value. Internal agent/model prompts carry
graded rules, and model cache keys include them. Existing strict hooks stay valid; optional hooks can
receive theme_policy as well as the legacy default set. Judge snapshots preserve the registry and rules
they actually recorded; older snapshots acquire no inferred values. Since snapshots do not contain every
expression’s reviewed tag placement, the blind judge is explicitly told not to infer those placements;
deterministic toolkit checks own known-form eligibility.

Historical round imports keep unresolved retired not_aussie annotations behind a documented manual gate,
not an invalid reads_as unknown value or an invented foreign reading. Explicit reviewed fixes and omission
still take precedence; archived files are not rewritten.

Canonical whole-expression profanity ratings also take precedence over a nested word read alone in lint.
This is a bounded dictionary rule for fixed active forms, with source and output occurrence accounting;
it introduces no phrase-specific Python exception.

Cards’ new placement fields and the changes-contract bump stay together in slice 6. Composite tier
combination and construction-family raises land with their actual caller in slice 2, after these foundations.

## Consequences

Curator feedback changes a canonical value instead of introducing a new exception in engine code. Known
literal readings and source content retain the previous conservative acceptance rules. This does not
claim arbitrary topic or politeness classification. Unclear placements remain questions for Rob; the
refinement report and per-record ledger distinguish those from applied rulings. No weight or threshold
is changed here: the existing metadata preference now reaches all four term-selection paths.
