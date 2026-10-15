# DD-013: One squashed, tagged release per version, made by scripts/promote.py

- **Status:** Accepted
- **Date:** in place for the first release, v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded retrospectively
  on 2026-10-13.

## Context

Development produces many small commits on a working branch. Users of `main` want to see releases, each one
the whole change since the last, and a release must not go out with a stale changelog, invalid version or
failing checks.

## Decision

Work happens on `dev`; `main` holds releases only. Each release is one squashed commit on `main`, tagged
`vX.Y.Z` (semver), made by `scripts/promote.py`. The release commit's tree is exactly the branch's tree at the
promoted commit, its message is the version's `CHANGELOG.md` section, and a `Promoted-From:` trailer names the
source commit. The version is defined once in `aussiefy/__init__.py` and read dynamically by pyproject.
The script refuses unless every check passes: a clean working tree, a valid version exactly one semver
step past `main`'s version, no existing tag, a
dated changelog section, `main` holding nothing the branch lacks, and ruff and the full test suite passing on
a clean checkout of the commit being released. Skips are allowed only for the local copyrighted corpus.

## Consequences

- `main` reads as a list of releases, and each release is reproducible from its source commit.
- Nobody commits to `main` directly; the per-commit history lives on the working branch.
- Changes must be recorded under `[Unreleased]` in `CHANGELOG.md` as they land, since the release message is
  built from it.

The working procedure is in [releasing.md](../../contributor/releasing.md).
