# DD-008: One toolkit, with every surface a thin adapter

- **Status:** Accepted
- **Date:** 2026-10-12, the first design review's consolidation (`docs/architecture/reviews/design-review-2026-10-12.md`,
  "Status after the first pass"); the parity tests were strengthened in the second review the same day.

## Context

aussiefy is used by people at a shell, by Python code, by MCP-capable agents, by a Claude Code skill, and by
its own yarn mode. Before the first review, the operations agents need (look up a term, lint a draft, read the
guide, plan a text, translate) were spread across modules under different names, and the surfaces disagreed:
some CLI commands accepted options they then ignored.

## Decision

Define five operations once, as plain Python functions returning JSON-ready dicts: `lookup`, `lint`, `guide`,
`plan` and `translate`, gathered in `aussiefy/harness.py`. Every surface (the Python API, the CLI, the MCP
server, yarn mode's tools and the skill) is a thin adapter over them, with the same parameters by the same
names and defaults. Parity is held by introspection in `tests/test_interfaces.py` rather than by generating the
adapters.

## Consequences

- An agent's knowledge transfers between surfaces, and yarn mode exercises the same tools an outside agent
  would.
- Adding or renaming a parameter means changing every surface, and the parity test fails until that is done.
- The adapters carry no logic of their own, so behaviour is tested once, at the toolkit.
