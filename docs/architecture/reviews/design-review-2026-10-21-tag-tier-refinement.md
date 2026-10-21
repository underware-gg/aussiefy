# Design review: tag-tier foundations and acceptance fixes, 21 October 2026

Surface: local changes from `f175e77` implementing ED9, approved placement rulings and spec-review items
1–7. Rob approved the remaining placement table, now applied in the canonical tags and recorded in the
per-record ledger. This record does not claim the designer's acceptance; that requires their re-check.
The inherited-support pass is separate package work.
One independent reviewer assessed all six software-design concerns and re-reviewed corrections.

## Findings

No remaining findings in the reviewed refinement. The final full suite passed **3,499 tests**, with the
two expected local-corpus skips (985.75 seconds). Ruff, publisher generation/check, tracked provenance
and whitespace checks passed. The independent reviewer cross-checked all 144 ledger records against
canonical tags, found no omitted themed records and passed the 18 placement regressions independently.
A stale ledger reason was corrected. Goldens changed in 41 of 375 outputs: approved opener/weight
choices and toilet→dunny; every pair and the changes fixture were reviewed. Contract version stays 2.

Resolved findings:

- Agent/model and judge instructions initially flattened graded permissions into a binary map. Retelling,
  model payloads/cache identity and judge snapshots now carry graded rules. The blind judge is told not
  to infer unrecorded expression placements; deterministic reviewed-form checks own that judgement.
- The built-in sentence prompt retained the old Dad stoush example after the data guide changed. Both use
  neutral effort, with real acceptance regressions.
- Whole-expression rating ownership initially covered bare words too, masking a changed swear strength.
  Only fixed multiword expressions qualify; existing current-dictionary cache acceptance catches this.
- Archived proposals still used reads_as unknown as a hold. The adapter now preserves unresolved old
  annotations behind a documented manual gate, without changing reviewed fixes, omission or input bytes.
- The integration fixtures now name THEME_RULES, the Dad stomach/throat placement, and canonical polite
  whole-expression ratings. Nan coverage checks chosen entry/garnish ratings and independently lints the
  actual result, instead of treating every nested word as its own complete expression.

## What's done well

- One immutable graded policy serves entries, riffs, images, bounded acceptance and editor cap probes.
  Exact overrides admit or forbid all strengths independently of profanity and performance settings.
- The theme registry and starts derive from validated data. Canonical name syntax has one definition.
  Explicit tag tiers round-trip inside themes; a second writable tier field is rejected.
- The shared evidence/general-English factor reaches both colour pick paths without replacing tone or
  editorial position. General wording remains available, including editor alternatives.
- Strict legacy hooks and historical snapshots preserve their actual inputs; missing historical rules
  are not invented. Current model caches distinguish graded policies and exact overrides.
- Source-retention tests use the real dictionary across four routes and 20 seeds. Evidence tests cover
  replacement scores, independence/support scope, forged labels and documented manual gates.
- Relative Australian politeness informs canonical data review, not Python word tests. Approved Dad sex/violence placements remain independent of their swear ratings; sense-only exceptions stay untagged.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Designer re-check of the reported commits | Confirm slices 0–1 against the amended design | Software review does not replace the requested spec review |
| Continue inherited-citation scoping | Restore informative evidence weighting and labels across the dictionary | Separate source-hunt work for the broader package gate |
| Restore guarded social-party detection | Recover an ordinary social sentence without political/legal ambiguity | An adjacent detection issue, independent of tag-tier foundations |
| Composite family raises and public card placement fields | Carry the same canonical placements into constructions and new cards | Actual callers arrive in slices 2 and 6 respectively |
