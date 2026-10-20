# Design review: reviewed semantic effects, 2026-10-19

Status: Draft; independent integration review and complete verification pending.

## Findings

Pre-implementation review identified role-losing brave/poor mappings, no permission for added narrator
opinion, and inconsistency between automatic candidates, lookup discovery and writer validation.
The implementation narrows the mappings, resolves one explicit permission and reuses its rejection rule.
The pending independent review must inspect the integrated actual diff before commit.

A focused worktree check also exposed a maintainer script importing another editable checkout.
`regen_changes_fixtures.py` now bootstraps its own ROOT, matching the sibling generators; a real run without
PYTHONPATH confirmed that it reads this branch's data. Annotated garnish extensions enter the existing form
index so the known-term writer check agrees with garnish eligibility, without adding another matcher.

## What's done well

The change uses the existing document policy resolver and canonical candidate seam. It keeps role
preservation distinct from editorial permission and retains existing imagery controls. Bounded known-term
checks make their limits explicit rather than claiming general natural-language understanding.

## Related follow-ups

Continue the source audit and review more mappings for undeclared additions. Mapping-specific effect
metadata is deferred until a concrete entry needs both exact and editorial senses. General semantic
verification of arbitrary generated prose is separate work.

## Verification

The focused semantic/schema/genre/retelling/changes/interface/documentation run passed **373 tests in
38.29 seconds**. After adding schema validation to the metadata case, all **32 semantic-effect tests passed
in 1.93 seconds**. Ruff and publication generation/check passed. Canonical golden regeneration changes
Gettysburg only: preserve death references, use a courage term for brave men, and omit added luck at Dinkum.
Change fixtures regenerate unchanged when the script reads this checkout. A built wheel installed to an
isolated target passed the permission matrix, plan, verify, yarn-submit and changes-schema smoke checks.
Final publication generation/check and Ruff passed. Full-suite verification belongs to parent integration.
