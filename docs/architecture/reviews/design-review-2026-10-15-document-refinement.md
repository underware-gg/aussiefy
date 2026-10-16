# Design review: document flavour and technical fidelity

Date: 2026-10-15

Scope: publication configuration, strict Markdown boundary/casing context, phonetic and terminology guards,
finite-clause inference, semantic fallback performance, generated documentation, and isolated behaviour
tests. One independent reviewer covered all six concerns; a separate Astra agent profiled performance.

## Findings

The initial review reproduced translated quoted examples, a stressed-verb contraction, blanket fragment
suppression, inappropriate person swears, relative-link sense corruption and ambiguous first-word casing.
The fixes preserve quoted examples, tune publication through existing overrides, separate structural quiet
from leading placement eligibility, carry source context, add narrow data guards and decline uncertain-case
prefixes. Each defect has focused positive/negative coverage. Requested follow-ups added broader contraction
cases and finite-clause inference; review then reproduced missing whether/until/before/after contexts and
these were fixed. A positive fixture was corrected to use a verb the existing POS tagger recognises,
preserving conservative inference. Performance review consolidated the shared length tolerance.

Final independent review found no outstanding findings. Its focused verification passed 82 tests; the
broader implementation check passed 347 tests. Full-suite and publication evidence is recorded in the
research report after the final gates complete.

The separate research-helper review reproduced packet overwrites, unchecked source/brief/policy changes,
trusted acceptance logs, incomplete file-set freezing and premature report freezing. The driver now binds
immutable packets to validated evidence, replays canonical tool diagnostics/acceptance, snapshots all Python
and data files, checks its own hash/rubric, and validates reports before freezing. Sixteen integrity tests
cover these contracts. Final independent review found no outstanding helper findings.

## What's done well

General/Custom defaults remain explicit. Publication reuses request-local controls without altering dial
semantics. Shared TextState/source ordinals and exact protected bytes remain intact. The phonetic context
guard is data-driven and validated at loading. Tests exercise actual output and legitimate unaffected uses,
including ordinary contractions, family vocabulary, proper names and acronyms.

Semantic fallback eliminates only candidates already rejected by mandatory-literal count and canonical
length. Original indices and tie order remain; exact raw scores and complete results are compared against
exhaustive scoring. N-gram indexing is unchanged. The bundled dot product preserves arithmetic order.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Fresh independent writer/judge comparison | Assess meaning, register and naturalness separately from mechanical correctness | Runs against the frozen refined implementation after this slice. |
