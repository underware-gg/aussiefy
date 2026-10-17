"""MCP server: the toolkit (aussiefy.harness) for any MCP-capable agent.

    pip install -e '.[mcp]'
    aussiefy-mcp                      # stdio transport

Configure your agent to launch aussiefy-mcp over stdio; see docs/user/agents.md.

Each tool is a thin adapter over the harness function of the same name, with the same parameters (less the
in-process translator); tests/test_interfaces.py holds the two in step.
"""

import functools
from typing import Any

from .errors import UserError
from .policy import LEVELS, VULGARITIES
from .schema import REGISTERS, FLAGS

from . import harness
from .guide import style_guide_data

INSTRUCTIONS = """Tools for rewriting English as genuine Australian English (levels 1-5).
Use the shared workflow below for the guide, plan, writing, lint and verification steps.
aussie_translate gives the plain deterministic output if that's all you need; aussie_verify checks a finished
translation against its original. Two independent dials, by number
or name: level 1-5 (tourist, blow-in, local, larrikin, swaggie) and vulgarity 0-3 (nan, dad, uncle-bob, tradie);
vulgarity defaults to the level's own (nan at 1-2, dad at 3-4, uncle-bob at 5), and tradie is never a default.
A third, embellishment 0-2 (deadset, dinkum, troppo), controls liberty in the telling. General is the default
explicit document type, with Dinkum embellishment. Auto opts into detection; named types supply presets;
Custom enables only explicitly configured optional behaviours. document_config applies exact overrides after
the preset and explicit dials. False and empty lists override inherited settings. Its nested profile object
tunes substitution, frames, garnish rates/limits/spacing, stack, phonetic, stretch, swearing and rewrite
thresholds; partial objects inherit missing keys from level/vulgarity defaults. profile_config reports the
complete resolved numeric settings. Custom still requires optional behaviours enabled explicitly."""


INSTRUCTIONS += "\n" + style_guide_data().workflow_for("mcp")


def build_server():
    # pydantic and the SDK come with the mcp extra, so they are imported here, not with the package
    from typing import Annotated, Literal

    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from pydantic import Field

    def _names(names: dict[str, int]) -> str:
        return ", ".join(f"{n} {name}" for name, n in names.items())

    # every tool's parameters, typed and described once, so the schema an agent sees says what's valid
    Level = Annotated[Annotated[int, Field(ge=1, le=5)] | Literal[tuple(LEVELS)],
                      Field(description=f"How Aussie, by number or name: {_names(LEVELS)}.")]
    Vulgarity = Annotated[Annotated[int, Field(ge=0, le=3)] | Literal[tuple(VULGARITIES)] | None,
                          Field(description=f"How rude, by number or name: {_names(VULGARITIES)}. Omit for the "
                                            "level's own (nan at 1-2, dad at 3-4, uncle-bob at 5).")]
    Text = Annotated[str, Field(description="The text: plain English to Aussify, or an Aussified draft to lint.")]
    Seed = Annotated[int, Field(description="Seed for the weighted choices: the same text, settings and seed give "
                                            "the same output; change it for a different version.")]
    Variety = Annotated[int, Field(ge=0, description="Choose among the N best-fitting slang terms only (1 = always "
                                                     "the best fit); 0 weighs every eligible term.")]
    Registers = Annotated[list[Literal[REGISTERS]] | None,
                          Field(description="Registers allowed; omit for the level's own (current, plus dated at 5).")]
    Regions = Annotated[list[str] | None, Field(description="Region tags to prefer, e.g. ['qld']; entries tagged "
                                                            "with other regions are left out.")]
    Unlock = Annotated[list[Literal[(*FLAGS, "all")]] | None,
                       Field(description="Flags whose gated (doubtful) entries become eligible, or ['all'].")]

    server = MCPServer("aussiefy", instructions=INSTRUCTIONS)

    def tool(fn):
        """Register a tool whose UserErrors reach the agent as their own message (the SDK hides other errors)."""
        @functools.wraps(fn)
        def run(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except UserError as exc:
                raise ToolError(str(exc)) from exc
        return server.tool()(run)

    @tool
    def aussie_lookup(query: str, level: Level = 5, vulgarity: Vulgarity = None,
                      limit: int = 8, include_gated: bool = False, short: bool = False,
                      embellishment: int | str | None = None, document_type: str = "general",
                      document_config: dict | None = None) -> dict[str, Any]:
        """Genuine Australian slang for a plain-English meaning ('very busy', 'someone'), or what an Aussie term
        means ('goog'). Filtered to the level and vulgarity, so it never offers what lint would reject.
        include_gated also returns entries held back as doubtful (marked as such). short: each result as its form,
        gloss, frame, level and vulgarity only."""
        return harness.lookup(query, level=level, vulgarity=vulgarity, limit=limit,
                              include_gated=include_gated, short=short, embellishment=embellishment,
                              document_type=document_type, document_config=document_config)

    @tool
    def aussie_lint(text: Text, level: Level = 5, vulgarity: Vulgarity = None,
                    original: str | None = None, markup: str = "text", english: str | None = None,
                    embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
                    suggest: bool = True) -> dict[str, Any]:
        """Lint an Aussified draft: flagged or non-Australian phrases, swearing over the cap or overused, US
        spelling, and US and British words (english: us, uk, auto, none, as for aussie_translate). Pass the original text to also check length and that names and numbers survive.
        Also suggests spots that could be more Aussie. markup (markdown, mdx, auto) lints the prose only and,
        with the original, checks its code and markup came through unchanged. embellishment (deadset, dinkum,
        troppo; default Dinkum for General): how much longer than the original it may run. suggest=False
        skips the optional suggestions (a whole engine translation), for a faster check."""
        return harness.lint(text, level=level, vulgarity=vulgarity, original=original, markup=markup,
                            english=english, embellishment=embellishment, document_type=document_type, document_config=document_config, suggest=suggest)

    @tool
    def aussie_guide(level: Level = 5, vulgarity: Vulgarity = None,
                     embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None) -> dict[str, Any]:
        """Voice, language limits and craft rules for Aussifying at a level (1-5), and how much liberty to take
        at an embellishment (deadset, dinkum, troppo; default Dinkum for General)."""
        return harness.guide(level=level, vulgarity=vulgarity, embellishment=embellishment, document_type=document_type, document_config=document_config)

    @tool
    def aussie_plan(text: Text, level: Level = 5, seed: Seed = 0, vulgarity: Vulgarity = None,
                    variety: Variety = 0, registers: Registers = None,
                    regions: Regions = None, unlock: Unlock = None,
                    markup: str = "text", english: str | None = None,
                    embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None) -> dict[str, Any]:
        """The rule engine's draft, the slang it planned (with riffs and suggested openings), and the sentences
        it found too formal to handle, and guidance for the text's genre and embellishment. Takes
        aussie_translate's options. embellishment defaults to dinkum, a retelling's (the plan is for writing
        your own version); pass the genre's own setting for a plan that matches aussie_translate's output."""
        return harness.plan(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                            registers=registers, regions=regions, unlock=unlock, markup=markup, english=english,
                            embellishment=embellishment, document_type=document_type, document_config=document_config)

    @tool
    def aussie_translate(text: Text, level: Level = 5, seed: Seed = 0, vulgarity: Vulgarity = None,
                         variety: Variety = 0, registers: Registers = None,
                         regions: Regions = None, unlock: Unlock = None,
                         markdown: bool = False, markup: str = "text", english: str | None = None,
                         embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None) -> dict[str, Any]:
        """Deterministic rule-engine translation (same text, level and seed give the same output). Change the
        seed for a different version. variety N picks among the N best-fitting terms only (1 = always the best
        fit); 0, the default, weighs every eligible term. registers (current, dated, archaic), regions (e.g. qld)
        and unlock (flags whose gated entries become eligible) narrow or widen what the level allows. markup
        (markdown, mdx, auto) translates only the prose of a document, keeping code, tags, links, front matter
        and headings exactly as they were. english (us, uk, auto, none): the English the text is in, for US and
        UK words Australians say differently (faucet -> tap; British pants -> undies only for uk). embellishment
        (0-2 or deadset, dinkum, troppo): how much liberty the telling takes, from none (the words swap, nothing
        added) to a performed yarn; default Dinkum for General; named types supply presets."""
        return harness.translate(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                                 registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english,
                                 embellishment=embellishment, document_type=document_type, document_config=document_config)

    @tool
    def aussie_verify(text: Text, original: str, level: Level = 5, vulgarity: Vulgarity = None,
                      markup: str = "text", english: str | None = None,
                      embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None) -> dict[str, Any]:
        """Check a finished translation (anyone's: the engine's, yours, a person's) against its original: a log of
        problems, worst first, each with a severity (critical: a lost number, a piece of markup changed, or an
        empty translation; major: breaks the brief; minor: craft, a sentence nothing in the translation says
        again, or a hint worth a look; info: coverage), and metrics. Deterministic; it
        doesn't judge tone or flow. english as for aussie_translate; embellishment sets the length limit (default
        Dinkum for General)."""
        return harness.verify(text, original=original, level=level, vulgarity=vulgarity, markup=markup,
                              english=english, embellishment=embellishment, document_type=document_type, document_config=document_config)

    return server


def main() -> None:
    build_server().run("stdio")


if __name__ == "__main__":
    main()
