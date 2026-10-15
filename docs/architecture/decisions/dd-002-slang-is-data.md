# DD-002: Slang is data, never hard-coded

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13 from the old manual and the agent instructions.

## Context

The value of the project is the slang itself: which phrases are genuinely Australian, what each means, how
rude it is, how hard it is to follow, and which level should use it. That knowledge grows by hand curation and
research rounds, and it must be reviewable, validated and attributable. If phrases or level rules lived in the
code, every addition would be a code change, and the engine could not be tested apart from its content.

## Decision

The engine never hard-codes slang. Every phrase is an entry in the YAML dictionary under `aussiefy/data/`, every
level is a profile in `aussiefy/data/profiles.yaml`, and the drawl, spelling, riffs, style guide and swearing
rates are data files too. The engine has no level logic of its own: everything a level does is read from its
profile.

## Consequences

- Research rounds, scraping and hand curation all add data, through a validating loader, without touching the
  engine. Users can extend the dictionary with `--dict` without forking the package.
- Most misfires are fixed in data (a trigger pattern, a frame, an intensity), not code.
- The data needs its own schema, validation and review tooling (`aussiefy/loader.py`, the `dev` steps), and
  the engine's behaviour can only be understood together with the data.
