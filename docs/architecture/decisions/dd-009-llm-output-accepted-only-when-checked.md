# DD-009: LLM output is accepted only when checked, else the draft stands

- **Status:** Accepted
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). The error contract
  at the Claude boundary was made explicit in the second design review the same day. Recorded retrospectively
  on 2026-10-13.

## Context

A language model writes more natural Australian English than a rule engine, but it can invent slang, drop the
vetted phrases, swear past the cap, change the facts, or be unavailable (no SDK, no key, network failure,
refusal). The rule engine is deterministic and always available, but can read like a word swap.

## Decision

The LLM modes are optional and never the only path. Each one starts from the engine's draft and accepts
Claude's output only when it passes checks: the planned phrases survive (`--surface`, `--rewrite`), the result is
one sentence of sane length (`--rewrite`), or the lint passes, most planned phrases are kept and the length is
sane (yarn mode). On a failed check, or any failure at the Claude boundary, the engine's draft stands, the
reason is reported, and the CLI exits 4. All Claude calls go through one seam, `aussiefy/claude.py`, with the
SDK optional. Accepted sentence rewrites and yarns are cached on disk, keyed by everything that decides the
reply; the fluent-surface pass is not cached.

## Consequences

- A user always gets a translation, and a fallback is visible rather than silent.
- The dictionary and the lint keep LLM output genuine; the model adds flow, not vocabulary.
- Repeated rewrite and yarn runs are reproducible offline from the cache.
- The live API paths are tested only with scripted clients; see [limitations](../../functional/limitations.md).
