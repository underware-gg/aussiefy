# Using aussiefy from an agent

Language models write good Australian English when they have genuine source material and a check. aussiefy
gives an agent both, through the same six operations (lookup, lint, guide, plan, translate, verify) on every surface.
The operations themselves are described in the [toolkit reference](../functional/toolkit.md).

The workflow is the same everywhere: establish the **brief** and dials, read the **guide**, get the engine's
**plan**, write the text with **lookups**, **lint** and fix it, **verify** against the original, then
**deliver**. Run `aussiefy guide` for the canonical workflow and craft guidance, filtered to your settings.
Use the same dials, document overrides and markup mode throughout. The plan's `note` explains how to use
its phrases without forcing a wrong sense. Reread for meaning and voice; mechanical checks are not a
writing-quality judgement.

## In a compatible agent: the portable skill

[skills/aussiefy/SKILL.md](../../../skills/aussiefy/SKILL.md) walks an agent through that workflow using the CLI.
Its source is agent-neutral; repository discovery links under `.agents/skills/` and `.claude/skills/` point
to that same folder. Codex supports `.agents/skills/` and follows symlinked skills; see its
[discovery documentation](https://learn.chatgpt.com/docs/build-skills).

Install aussiefy so the agent can run the CLI, then copy `skills/aussiefy/` to a location your agent scans.
For example, Codex uses `~/.agents/skills/aussiefy/`; Claude Code uses `~/.claude/skills/aussiefy/`.
Other clients have their own discovery settings. An agent with shell access can also read the skill
directly. Using these CLI tools requires neither the `llm` extra nor an Anthropic API key.

From a repository checkout, copy the skill for either or both clients:

```sh
# Codex
mkdir -p ~/.agents/skills
cp -R skills/aussiefy ~/.agents/skills/
# Claude Code
mkdir -p ~/.claude/skills
cp -R skills/aussiefy ~/.claude/skills/
```

## In any MCP-capable agent: the MCP server

```sh
pip install "aussiefy[mcp] @ git+https://github.com/underware-gg/aussiefy@v0.1.0"
claude mcp add aussiefy -- aussiefy-mcp     # Claude Code; other clients run `aussiefy-mcp` over stdio
codex mcp add aussiefy -- aussiefy-mcp      # Codex
```

Configure other clients to launch `aussiefy-mcp` as a stdio server, with no command arguments. The tools
are `aussie_lookup`, `aussie_lint`, `aussie_guide`, `aussie_plan`, `aussie_translate` and `aussie_verify`.
The server's instructions supply the same workflow; the server itself needs no model credentials.

## In an agent you build

Use the Python toolkit directly, or run yarn's checked loop with your own model. Import the loop's parts
from the module (`aussiefy.yarn` on the package is the function):

  ```python
  from aussiefy.retelling import brief, dispatch_tool, tool_contracts

  tools = tool_contracts()                # neutral name, description and JSON Schema per tool
  session = brief(text, level=5)           # session.system and session.payload brief your agent
  result, accepted = dispatch_tool(session, name, args)   # answer its lookup, lint or submit call
  ```

These functions make no model call. Adapt the tool schema to your model's protocol; `tool_definitions()`
from `aussiefy.yarn` returns Anthropic Messages API definitions for that client. Only a valid `submit` is
accepted. Existing imports of `brief` and `dispatch_tool` from `aussiefy.yarn` remain supported.

To have aussiefy run the built-in loop for you, call `aussiefy.yarn(text, level=5)` or `aussiefy yarn`.
That optional client currently uses Claude and needs the `llm` extra and Anthropic credentials; see
[model-assisted modes](llm-modes.md).

## From a shell

```sh
aussiefy guide -l 5
aussiefy plan -l 5 < story.txt
aussiefy lookup -l 5 "very busy"
aussiefy lint -l 5 --original story.txt < draft.txt   # exit 1 means there are issues
aussiefy verify -l 5 --original story.txt draft.txt   # exit 1 means critical or major problems
```

For the complete checked submission loop without a built-in model call, use
`aussiefy yarn-tools brief story.txt`, then its `lookup`, `lint` and `submit` steps. See the
[CLI reference](../functional/cli.md#command-options) for retained logs, declines and accepted-output files.
