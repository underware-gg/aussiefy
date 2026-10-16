# Verification maintenance review, 2026-10-16

Scope: the real optional API SDK boundary, minimum-Python release smoke checks, and consolidation of
`test_repository_contracts.py` into `test_contracts.py`. A single independent reviewer examined the full
diff against `585dc7a` across all six software-design concern areas, with a second pass over the fix.

## Findings

- **High, high confidence — verification/completion, defensive:** the initial `release-head` dependency
  could skip the required check after compatibility failed. GitHub can accept a skipped required check.
  Fixed in `.github/workflows/release.yml` with `always()` and a first-step explicit success guard; the
  exact-head/squash-tree checks still follow. Its workflow contract test pins the guard. This follows
  the Foundation and P18: verify the actual boundary semantics. See
  [GitHub's required-check guidance](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).
- A trailing blank line identified by the whitespace check was removed.

The correction review has no outstanding findings. Local verification covers both SDK generations and
Python 3.10; hosted Actions results will be obtained when an authorised release branch is pushed.

Validation: 1,855 passed / two expected local-corpus skips in 460.83s, actual exit 0; 220 compatibility
checks passed on each local Python/SDK combination. The final documentation/CI-focused run passed 171
cases; Ruff, publication freshness/links, whitespace and provenance with built-wheel inspection passed.
The interrupted earlier full run is excluded from passing evidence.

## What's done well

- Real SDK calls reach a mocked HTTP transport, so request serialization and response parsing are observed.
  Scripted clients remain appropriate for acceptance/fallback scenarios. The SDK's 0.x/1.x transport
  distinction stays in the test fixture; production needs no new abstraction.
- The compatibility matrix covers Python 3.10/minimum SDK and Python 3.12/current SDK. The required
  release check depends on both and fails explicitly when either is unsuccessful.
- One owner now holds toolkit result shapes and the older suite's distinct policy, phrase-normalisation,
  phrase-retention and lookup assertions. Real riff and suggestion examples prevent vacuous checks.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Full judge settings and held-out repeat-judge study | Broader quality evidence under the actual writing contract | The next requested slice changes judging and research, rather than this transport/CI/test ownership boundary |
| Live configured client/API and website latency smoke | Establish service and browser integration evidence | Offline serialization/stdio tests do not require credentials or a deployed website |
