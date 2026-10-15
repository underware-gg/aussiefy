# Branches, the changelog and releases

## Branches

Work happens on `dev` (or a branch off it). `main` holds one checked, squashed commit per tagged release.
`scripts/promote.py` prepares a release branch, checks its exact head/base and finishes through a GitHub PR.
Before the first release, `dev` is the GitHub default branch so visitors and clones see the working project;
`main` still contains only repository setup. After the first checked release reaches `main`, change the
GitHub default branch to `main` and update installation examples to a released tag. Development stays on `dev`.
Don't commit to `main` directly. The decisions are [DD-013](../../architecture/decisions/dd-013-one-squashed-release-per-version.md)
and [DD-018](../../architecture/decisions/dd-018-checked-pr-release-promotion.md).

## The changelog

Edit [plain CHANGELOG.md](../root/CHANGELOG.md), under `[Unreleased]`. Preparation increments the single
version in `aussiefy/__init__.py`, dates that section and regenerates published docs and notices. The
published dated section becomes the squash message and GitHub release notes. `Promoted-From:` names the
checked release head, which includes the preparation commit; the squash tree must equal that head's tree.

## Repository enforcement

Install the workflow in `.github/workflows/release.yml`, then apply and read back main protection:

```sh
python scripts/promote.py configure
```

The required check is `aussiefy-release-head`, pinned to the GitHub Actions app. It runs on pushes to
`release/v*`, on the actual pushed SHA, with a read-only token; it does not execute a synthetic PR merge
commit. Main must require PRs and strict/up-to-date checks, enforce them for administrators, and allow no
review bypass actors, force pushes or deletion. Existing incompatible protection is retained for explicit
maintainer review rather than weakened automatically. Additional required checks remain enforced by GitHub.

Automated finish refuses if this enforcement cannot be verified. Private repositories need a GitHub plan
that supports protection; HTTP 403 is a platform limitation, not an unprotected-rule result. Keep the
repository private until a separate visibility decision, or arrange a suitable plan. Do not substitute
administrator bypass or a direct push for this gate.

## Preparing and finishing

Use a clean `dev` identical to `origin/dev`. `prepare` fetches refs, creates `release/vX.Y.Z`, bumps the
plain source, generates publication/notices, checks an isolated exact candidate, commits preparation and
checks the committed tree again before pushing or opening a PR. No force updates occur.

```sh
python scripts/promote.py prepare minor
python scripts/promote.py check --pr 1
python scripts/promote.py finish --pr 1 --head RELEASE_HEAD_SHA --base CHECKED_MAIN_SHA
```

Use the PR number and full head/base SHAs printed by `check`; the placeholders above are not values.
Preparation takes `major`, `minor` or `patch`. Commands resolve the repository from the script location,
independently of cwd; global `--root PATH` selects a fixture/other checkout. `check` without `--pr` is the
local/CI gate, with explicit `--head`, `--base` and `--branch` available for a detached checkout.

Checks require valid semver, a dated published changelog, current main ancestry and previous release
provenance, an equal squash/head tree, fresh publication and links, Ruff, full pytest and the actual
wheel/provenance/licence gate. Only the two local-corpus tests in `tests/functional/test_local_reference.py`
may skip. See [testing](testing.md), [publication](documentation.md) and [licensing](licensing.md).

Finish requires unchanged checked PR head/base, the successful newest Actions check on that exact head,
and observed strict server protection. Expected-head merging protects against a head move; strict server
checks close the base-move race. After squash merge, finish reads back parent, tree, changelog and trailer
before creating the immutable tag and publishing notes. It fast-forwards dev to the release head,
reconciles main with `git merge -s ours`, pushes dev, then removes the release branch. Deletion uses an
expected-head lease; dev and main are never force-updated.

## Interrupted work

A failed preparation stays on its release branch with reviewable changes. Fix the reported issue and
resume the same `prepare` command on that branch. An existing candidate is checked again; it is never
silently rebuilt from another source. Repeated pushes/PR creation reuse matching state and reject conflicts.

Resume finish with the same PR/head/base. It inspects the existing merged PR, immutable tag and GitHub
release before continuing; matching completed actions are reused, mismatched provenance/tags/notes fail.
If later dev work arrives, stop and retain it. After publication, merge the release into dev, resolve any
conflicts, reconcile verified main with `git merge -s ours origin/main`, push dev, then resume cleanup.
The completed reconciliation must contain both the checked release source and verified squash commit.
Do not reset later commits or roll back a published release. A moved main requires explicit inspection.

Two local release cycles and interruption/race tests verify this workflow. A real PR/check/tag/release is a
separately approved operation; implementing the workflow does not publish a release.

## Releasing a new embedding model

The embedding model has separate version numbers and procedures: see [training/README.md](../../../training/README.md).
A new model ships in the next package release with a changelog entry.
