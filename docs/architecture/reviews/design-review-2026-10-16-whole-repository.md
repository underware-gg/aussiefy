# Design review: whole repository and next-release readiness

Date: 2026-10-16

Scope: production code, public surfaces, agent skills/instructions, packaging, release tooling/CI, tests
and current documentation at `66be5ef`, plus the resulting fixes. Six independent reviewers covered
premise, structure, code smells, efficiency, defensive patterns and verification. Concurrency was bounded
to three reviewers at once. Historical corpora/reports were used as evidence rather than rewritten.

## Findings

Initial locations below refer to the audited baseline; resolutions refer to this review's changes.

| Priority / confidence / concern | Location and evidence | Calibration | Resolution |
|---|---|---|---|
| High / high; premise + defensive (2 reviewers) | `aussiefy/yarn.py:318`: cached text bypassed shape/current-rule validation, including a changed dictionary's vulgarity rule | Validate inputs vs trust callers: persisted JSON is a boundary | Check consumed fields and run current-session acceptance before reuse; stale content follows generation/fallback |
| Medium / high; code smells (1 reviewer) | `aussiefy/lookup.py:171`: partial lookup reduced `drinking` to `drinkin`, but dropped-g spelling to `drink` | Simplest design that works | Fix suffix order in the existing branch and retain doubled-consonant support |
| Medium / high; structural (1 reviewer, explicit user requirement) | `aussiefy/yarn.py:256`: shared dispatch derived arguments from Anthropic-shaped definitions | Reduce coupling vs avoid abstraction: two actual consumers | Extract pure sessions, neutral JSON Schemas and dispatch; adapt at the API edge and retain existing imports |
| Medium / high; structural (1 reviewer) | `aussiefy/data/guide.yaml:120` and `aussiefy/guide.py:22`: canonical workflow omitted verify, while the skill required it | DRY applies to knowledge: demonstrated drift | Add verify to shared placeholders and the data-owned sequence; align summaries |
| Medium / high; completion (1 reviewer) | `docs/plain/functional/cli.md:78`: wrong `lint --short` option and incomplete/misstated shared flags | Observed working, not claimed | Reconcile against argparse; add runnable lookup/verify/yarn-tools examples |
| Low / high; premise + code smells + completion (3 reviewers) | `docs/plain/user/agents.md:12`, `docs/plain/contributor/judging.md:25`, `docs/plain/contributor/testing.md:89`: Claude-only setup, incomplete MCP list and stale research/licensing descriptions | Foundation and observed working | Both client setup paths, complete six-tool inventory and corrected current documentation |

Two small same-area cleanups remove unreachable loader type checks after `_read` and reuse the existing
`meaning_texts` rule instead of rebuilding it in runtime lookup. All six concerns converged after the fixes;
the final structural/completion pass also caught and corrected one remaining workflow summary and the
lookup compact-JSON wording. The full suite exited 0: **1,876 passed / two expected local skips in
625.61s**. No required review finding remains open. Ruff, publication freshness/links and actual
wheel/provenance checks passed. The final documentation/boundary/layer run passed **153 tests in 4.42s**
after the documentation-only corrections.

A proposed gaps optimisation was not carried forward: `max(score, 1.0)` cannot be replaced by a constant
under the public unbounded Embedder protocol, and cosine arithmetic can slightly exceed one. The premise
check prevented a measured speedup from changing supported results.

## What's done well

The deterministic core stays below adapters; strict Markdown and extended MDX retain distinct contracts.
Immutable overrides and shared alignment/term rules have concrete owners. Public signatures and installed
MCP schemas have executable parity checks. Expected API failures preserve explicit draft outcomes while
programming errors propagate. Promotion checks isolated exact commits and actual wheel/licence contents.
No unsupported provider registry or new paid model dependency is needed for agent compatibility.

Focused verification includes malformed/stale caches and changed dictionary acceptance, partial term
lookup, shared workflow ordering, provider-free sessions and actual stdio MCP discovery/calls. These
establish shared boundaries, not live model execution in Claude or Codex.

The final boundary/documentation run passed 147 cases independently; an earlier broad focused run passed
228. The parent's subsequent boundary/documentation/layer check passed 153. New provider-free and stdio
tests passed all three cases. Cache/fallback checks independently passed
15 selected cases. Earlier runs with incorrect SDK result-field names or unused test imports are excluded
from passing evidence.

The built wheel was installed into an isolated target and exercised from outside both source checkouts.
Imports resolved inside that target. CLI translation/help, bundled data loading and a shared retelling
submission worked; the installed `aussiefy-mcp` script initialized over stdio, exposed all six tools and
returned the expected translation. This uses installed test dependencies and does not claim a live model
or a clean dependency-resolution installation. The wheel is a development snapshot with the current
0.1.0 metadata; promotion assigns the new release version.

Fetched `origin/main` remains released v0.1.0 at `c147f8b`, and it is an ancestor of this work. The current
changes add public controls and a shared module, so the recommended next bundle is a minor release,
v0.2.0. Preparation, exact release-head CI and explicit publication remain separate from this assessment.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Real declared SDK plus HTTP mock transport | Check external request serialization without paid calls | Existing tests verify adapter behavior; no SDK incompatibility was demonstrated |
| Python 3.10 CI smoke | Exercise the advertised minimum interpreter | Current CI uses 3.12; no compatibility defect was found |
| Consolidate duplicate older contract tests | Give each behavior one test owner | Current runtime fixes and stronger surface checks remain sound |
| Held-out retelling sources, repeat judges and production judge context | Broaden quality evidence and make restrictions explicit in public judging | Separate from agent-neutral workflow and known mechanical defects |
