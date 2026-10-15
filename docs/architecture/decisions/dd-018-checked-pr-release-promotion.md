# DD-018: Checked GitHub PR release promotion

- **Status:** accepted
- **Date:** 2026-10-15
- **Extends:** [DD-013](dd-013-one-squashed-release-per-version.md), [DD-017](dd-017-authoritative-plain-documentation.md)

## Context

Direct writes to main cannot express a required GitHub check or atomically enforce the tested base.
Release interruption also needs a safe continuation that preserves published identities and later dev work.

## Decision

Prepare/check/finish use rooted Git and thin GitHub adapters over shared semver, changelog and provenance
rules. A release branch is checked before its preparation commit and again in isolation afterwards. CI
checks the actual pushed release head; no synthetic merge identity substitutes for it. Main requires that
Actions check, strict current-base enforcement and administrator enforcement with no bypass actors.
Finish sends the expected head to GitHub squash merging and verifies the returned commit's parent, tree,
changelog and `Promoted-From:` trailer before immutable tagging/publication.

The published changelog section supplies release prose; the plain source remains editable authority.
Dev fast-forwards to the release source and reconciles main through an ours merge. Later work is retained;
a completed manual reconciliation containing both release identities can resume cleanup. Existing Git/PR/
tag/release state supplies recovery; no extra release-state database or direct-main compatibility path exists.

## Consequences

A provider plan without enforceable private-repository protection prevents automated finish. That is
reported as a platform limitation; neither bypass nor a visibility/paid-plan change is implied. GitHub
calls are substituted only at the network boundary in tests; real Git, isolation, race/refusal and two local
release cycles are exercised. Live publication remains a separate authorisation.
