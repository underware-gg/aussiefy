# DD-023: Agent-neutral retelling

Status: Accepted

Date: 2026-10-16

Extends: [DD-008](dd-008-one-toolkit-thin-surfaces.md)

## Context

Claude and Codex can both use the toolkit through shell or MCP. The portable skill already lives outside
client configuration, but discovery and documentation presented only Claude. Shared retelling sessions
also lived beside the optional API driver, and dispatch derived required arguments from Anthropic-shaped
tool definitions. That put a transport representation in charge of a shared workflow rule.

## Decision

Keep the six-operation toolkit agent-neutral. Put retelling briefs, sessions, validation, dispatch and
plain JSON Schema tool contracts in `retelling.py`, with no API-client dependency. The hand-run CLI and
optional API driver consume that same contract. The driver adapts neutral schemas at its edge; no provider
registry or new model API is needed for an agent to run the shared workflow.

Retain existing imports from `aussiefy.yarn` for Python/research consumers. Keep one editable skill under
`skills/aussiefy`, with discovery symlinks for `.agents/skills` and `.claude/skills`. Document installation
and MCP registration for both Codex and Claude Code, and direct reading for other shell-capable agents.

## Consequences

Shared-tool changes have one schema owner. Existing API callers keep working, while other agents use the
same checked submission without that API client. Layer checks protect dependency direction. Provider-free
session tests and real stdio MCP initialization/discovery/calls verify the common boundary; these checks
do not claim live model execution in either client. Client-specific API credentials and model defaults
remain documented with that optional adapter, rather than defining the harness.
