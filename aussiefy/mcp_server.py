"""MCP server: the toolkit (aussiefy.harness) for any MCP-capable agent.

    pip install -e '.[mcp]'
    aussiefy-mcp                      # stdio transport

Configure your agent to launch aussiefy-mcp over stdio; see docs/user/agents.md.

Each tool is a thin adapter over the harness function of the same name, with the same parameters (less the
in-process translator); tests/test_interfaces.py holds the two in step. A hosted server narrows them by
capability (build_server's options; DD-028).
"""

import functools
import inspect
from typing import Any, Callable, Collection

from .engine import Translator, default_translator
from .errors import UserError
from .policy import DOCUMENT_TYPES, LEVELS, VULGARITIES
from .schema import REGISTERS, UNLOCKS

from . import harness
from .constructions import DEFAULT_LIMIT, ConstructionCatalog
from .explore import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, INITIALS
from .guide import style_guide_data

_CORE = """Tools for rewriting English as genuine Australian English (levels 1-5).
Use the shared workflow below for the guide, plan, writing, lint and verification steps.
aussie_entries lists stable pages; aussie_entry fetches a card and aussie_random_entry samples the dictionary.
aussie_meaning_quiz gives a seeded term, four glosses and the answer/card for a reveal.
aussie_concepts lists meanings with eligible-entry counts under the caller's dials.
aussie_wordless_meanings lists meanings recognised but with no Aussie word yet.
aussie_suggest_name suggests clean handles; aussie_variations offers compatible changes to constructed expressions.
aussie_bulldust constructs labelled sayings from reviewed families with evidence on every part.
aussie_translate gives the plain deterministic output if that's all you need; aussie_verify checks a finished
translation against its original. Two independent dials, by number
or name: level 1-5 (tourist, blow-in, local, larrikin, swaggie) and vulgarity 0-3 (nan, dad, uncle-bob, tradie);
vulgarity defaults to the level's own (nan at 1-2, dad at 3-4, uncle-bob at 5), and tradie is never a default.
A third, embellishment 0-2 (deadset, dinkum, troppo), controls liberty in the telling. General is the default
explicit document type, with Dinkum embellishment. Auto opts into detection; named types supply presets."""

# what only a server with document_config describes (allow_document_config=False drops it with the Custom type)
_DOCUMENT_CONFIG = """
Custom enables only explicitly configured optional behaviours. document_config applies exact overrides after
the preset and explicit dials. False and empty lists override inherited settings. Its nested profile object
tunes substitution, frames, garnish rates/limits/spacing, stack, phonetic, stretch, swearing and rewrite
thresholds; partial objects inherit missing keys from level/vulgarity defaults. profile_config reports the
complete resolved numeric settings. Custom still requires optional behaviours enabled explicitly. themes overrides exact per-theme booleans
independently of profanity; omitted themes inherit term-tier placement, and theme_permissions reports all default permissions.
Every expression needs all its reviewed tag tiers allowed; true admits every strength and false forbids all. Restriction never deletes original subject matter."""



def instructions(*, allow_document_config: bool = True) -> str:
    return _CORE + (_DOCUMENT_CONFIG if allow_document_config else "") + "\n" + style_guide_data().workflow_for("mcp")


INSTRUCTIONS = instructions()

def _describe(doc: str, hidden: set[str]) -> str:
    # Optional parameter descriptions occupy their own lines in the tool docs.
    return '\n'.join(line for line in inspect.cleandoc(doc).splitlines()
                     if not any(line.startswith(name + ' ') for name in hidden)).strip()


def build_server(*, translator: Translator | None = None, allow_unlock: bool = True, allow_include_gated: bool = True,
                 allow_document_config: bool = True, allow_tuning: bool = True,
                 preferences_hook: Callable[..., list[dict] | None] | None = None,
                 allow_personal_terms: bool = True,
                 personal_terms_hook: Callable[..., list[dict] | None] | None = None,
                 max_personal_terms: int | None = 50,
                 allow_themes: bool = True, allow_invention: bool = True,
                 tools: Collection[str] | None = None, max_chars: int | None = None,
                 max_query_chars: int | None = None, lookup_limit: int | None = None):
    """The MCP server. The defaults serve everything, for a local install; a hosted service passes its
    capabilities. allow_unlock=False hides unlock; allow_include_gated=False hides include_gated independently;
    allow_document_config=False hides
    document_config and the custom document type; max_chars caps every text field (text, original);
    max_query_chars caps aussie_lookup's query; lookup_limit caps its limit. translator is the one every tool uses (default: the toolkit's)."""
    if max_personal_terms is not None and (type(max_personal_terms) is not int or max_personal_terms < 1):
        raise UserError('max_personal_terms must be a positive integer or None')
    if max_personal_terms != 50 and personal_terms_hook is None:
        raise UserError('a custom max_personal_terms requires a host personal_terms_hook')
    def supplied_personal_terms(**dials):
        from .personal_terms import prepare
        dictionary = (translator or default_translator()).dictionary
        return prepare(personal_terms_hook(**dials), dictionary, max_terms=max_personal_terms)
    personal_provider = supplied_personal_terms if personal_terms_hook is not None and allow_personal_terms else None

    # pydantic and the SDK come with the mcp extra, so they are imported here, not with the package
    from typing import Annotated, Literal

    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.server.mcpserver.tools import Tool
    from mcp.types import ToolAnnotations
    from pydantic import Field, StrictBool, create_model, model_validator

    def _names(names: dict[str, int]) -> str:
        return ", ".join(f"{n} {name}" for name, n in names.items())

    # every tool's parameters, typed and described once, so the schema an agent sees says what's valid
    Level = Annotated[Annotated[int, Field(ge=1, le=5)] | Literal[tuple(LEVELS)],
                      Field(description=f"How Aussie, by number or name: {_names(LEVELS)}.")]
    Vulgarity = Annotated[Annotated[int, Field(ge=0, le=3)] | Literal[tuple(VULGARITIES)] | None,
                          Field(description=f"How rude, by number or name: {_names(VULGARITIES)}. Omit for the "
                                            "level's own (nan at 1-2, dad at 3-4, uncle-bob at 5).")]
    Text = Annotated[str, Field(max_length=max_chars,
                                description="The text: plain English to Aussify, or an Aussified draft to lint.")]
    Original = Annotated[str, Field(max_length=max_chars, description="The original text it was translated from.")]
    Query = Annotated[str, Field(max_length=max_query_chars, description="A plain-English meaning or an Aussie term.")]
    Limit = Annotated[int, Field(le=lookup_limit)] if lookup_limit else int
    limit_default = min(8, lookup_limit) if lookup_limit else 8
    DocumentType = str if allow_document_config else Literal[tuple(t for t in DOCUMENT_TYPES if t != "custom")]
    Seed = Annotated[int, Field(description="Seed for the weighted choices: the same text, settings and seed give "
                                            "the same output; change it for a different version.")]
    Variety = Annotated[int, Field(ge=0, description="Choose among the N best-fitting slang terms only (1 = always "
                                                     "the best fit); 0 weighs every eligible term.")]
    Registers = Annotated[list[Literal[REGISTERS]] | None,
                          Field(description="Registers allowed; omit for the level's own (current, plus dated at 5).")]
    Regions = Annotated[list[str] | None, Field(description="Region tags to prefer, e.g. ['qld']; entries tagged "
                                                            "with other regions are left out.")]
    Unlock = Annotated[list[Literal[(*UNLOCKS,)]] | None,
                       Field(description="Flags whose gated (doubtful) entries become eligible, or ['all'].")]

    Themes = Annotated[dict[str, StrictBool] | None, Field(description="Exact per-theme permissions; canonical theme names map to true or false, independently of profanity.")]
    Invention = Annotated[StrictBool | None, Field(description="Allow reviewed construction fallback; omit for the setting's default (Troppo on). Grammar, source protection and all other permissions still apply.")]
    Popularity = Annotated[StrictBool, Field(description="Apply the community adjustments with their wider popularity band; never changes eligibility or evidence.")]
    if tools is not None and (isinstance(tools, str) or not isinstance(tools, Collection)
                              or any(not isinstance(name, str) for name in tools)):
        raise UserError('tools must be a collection of canonical tool names')
    selected_tools = None if tools is None else set(tools)
    known_tools = set()

    hidden = ({"unlock"} if not allow_unlock else set()) | \
        ({"include_gated"} if not allow_include_gated else set()) | \
        ({"document_config"} if not allow_document_config else set()) | \
        ({"popularity"} if not allow_tuning else set()) | \
        ({"personal_terms"} if not allow_personal_terms or personal_terms_hook is not None else set()) | \
        ({"themes"} if not allow_themes else set()) | \
        ({"invention"} if not allow_invention else set())
    # every tool only reads: no side effects, same answer for the same call, nothing outside the package
    read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True,
                                open_world_hint=False)

    registered_tools = []

    def tool(fn):
        """Register a tool whose UserErrors reach the agent as their own message (the SDK hides other errors),
        without the parameters this server doesn't offer (they keep their defaults)."""
        known_tools.add(fn.__name__)
        if selected_tools is not None and fn.__name__ not in selected_tools:
            return fn
        @functools.wraps(fn)
        def run(*args, **kwargs):
            try:
                forbidden = set(kwargs) & (hidden | {'preferences', '_preferences_hook', '_personal_terms_hook'})
                if forbidden:
                    raise UserError('parameters not offered by this server: '+', '.join(sorted(forbidden)))
                config = kwargs.get('document_config')
                if isinstance(config,dict):
                    forbidden = ({'themes'} if not allow_themes else set()) | ({'invention'} if not allow_invention else set())
                    if forbidden & set(config):
                        raise UserError('document_config cannot override disabled host permissions')
                return fn(*args, **kwargs)
            except UserError as exc:
                raise ToolError(str(exc)) from exc
        signature = inspect.signature(fn)
        run.__signature__ = signature.replace(
            parameters=[p for p in signature.parameters.values() if p.name not in hidden])
        registered = Tool.from_function(run, description=_describe(fn.__doc__, hidden & set(signature.parameters)),
                                        annotations=read_only)
        if 'personal_terms' in hidden and 'personal_terms' in signature.parameters:
            # Validate raw arguments before the SDK drops unknown/hidden fields.
            def reject_client_personal_terms(cls, values):
                if 'personal_terms' in values:
                    raise ValueError('personal_terms are not offered by this server')
                return values
            registered.fn_metadata.arg_model = create_model(
                fn.__name__ + 'HostArguments', __base__=registered.fn_metadata.arg_model,
                __validators__={'host_personal_terms': model_validator(mode='before')(reject_client_personal_terms)})
        registered_tools.append(registered)
        return run

    catalog = (translator or default_translator()).dictionary.construction_catalog
    bulldust_max = catalog.max_results if catalog else ConstructionCatalog().max_results
    if lookup_limit:
        bulldust_max = min(bulldust_max, lookup_limit)
    BulldustLimit = Annotated[int, Field(ge=1, le=bulldust_max)]
    bulldust_default = min(DEFAULT_LIMIT, bulldust_max)

    @tool
    def aussie_bulldust(concept: str | None = None, family: str | None = None, parts: dict[str, str] | None = None,
                        level: Level = 5, seed: Seed = 0, vulgarity: Vulgarity = None, limit: BulldustLimit = bulldust_default,
                        registers: Registers = None, regions: Regions = None, unlock: Unlock = None,
                        embellishment: int | str | None = None, document_type: DocumentType = "general",
                        document_config: dict | None = None, themes: Themes = None, invention: Invention = None,
                        include_scaffold: bool = False) -> dict[str, Any]:
        """Construct Australian-sounding idioms from reviewed families, labelled bulldust with part evidence.
        concept is a dictionary ID such as HUNGRY. family restricts the pattern; parts pins named slots to
        ingredient IDs from a result so the remaining parts can vary. No global novelty is promised.
        include_scaffold adds the full agent scaffold; the default returns only construction results."""
        return harness.bulldust(concept, family=family, parts=parts, level=level, seed=seed, vulgarity=vulgarity,
                                limit=limit, include_scaffold=include_scaffold, registers=registers, regions=regions, unlock=unlock,
                                embellishment=embellishment, document_type=document_type,
                                document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_lookup(query: Query, level: Level = 5, vulgarity: Vulgarity = None,
                      limit: Limit = limit_default, include_gated: bool = False, short: bool = False,
                      embellishment: int | str | None = None, document_type: DocumentType = "general",
                      document_config: dict | None = None,
                      themes: Themes = None, invention: Invention = None, unlock: Unlock = None) -> dict[str, Any]:
        """Genuine Australian slang for a plain-English meaning ('very busy', 'someone'), or what an Aussie term
        means ('goog'). Filtered to the level and vulgarity, so it never offers what lint would reject.
        include_gated also returns held-back entries for discovery, marked with their reasons.
        Results name their match kind and dictionary identity; protected phrases return left_as_written
        with their current reasons and derived ruled-out readings, possibly empty.
        short: compact entry cards with match-kind codes."""
        return harness.lookup(query, level=level, vulgarity=vulgarity, limit=limit,
                              include_gated=include_gated, short=short, embellishment=embellishment,
                              document_type=document_type, document_config=document_config, unlock=unlock, translator=translator, themes=themes, invention=invention)

    PageLimit = Annotated[int, Field(ge=1, le=min(MAX_PAGE_SIZE, lookup_limit) if lookup_limit else MAX_PAGE_SIZE)]
    page_default = min(DEFAULT_PAGE_SIZE, lookup_limit) if lookup_limit else DEFAULT_PAGE_SIZE
    Offset = Annotated[int, Field(ge=0)]
    Initial = Literal[tuple(INITIALS)] | None

    @tool
    def aussie_entries(concept: str | None = None, theme: str | None = None, initial: Initial = None, offset: Offset = 0,
                       limit: PageLimit = page_default,
                       level: Level = 5, vulgarity: Vulgarity = None, include_gated: bool = False,
                       embellishment: int | str | None = None, document_type: DocumentType = "general",
                       document_config: dict | None = None, themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """List a stable page of entry cards by concept, theme and headword initial (a-z or #), ignoring leading a/an/the. Filters intersect.
        total counts the filtered set; initial_counts counts all initials under the other filters, before pagination.
        include_gated also returns entries held back as doubtful (marked as such)."""
        return harness.list_entries(concept=concept, theme=theme, initial=initial, offset=offset, limit=limit, level=level,
                                    vulgarity=vulgarity, include_gated=include_gated, embellishment=embellishment,
                                    document_type=document_type, document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_concepts(offset: Offset = 0, limit: PageLimit = page_default,
                       level: Level = 5, vulgarity: Vulgarity = None, include_gated: bool = False,
                       embellishment: int | str | None = None, document_type: DocumentType = "general",
                       document_config: dict | None = None, themes: Themes = None,
                       invention: Invention = None) -> dict[str, Any]:
        """List meanings with dictionary entries, ordered by stable concept ID.
        Each result has concept, plain wording and entry_count under the same dials as aussie_entries.
        Zero counts are retained. Meanings waiting for a word have their own listing.
        include_gated permits held-back entries to contribute to the counts."""
        return harness.list_concepts(offset=offset, limit=limit, level=level, vulgarity=vulgarity,
                                     include_gated=include_gated, embellishment=embellishment,
                                     document_type=document_type, document_config=document_config,
                                     themes=themes, invention=invention, translator=translator)

    @tool
    def aussie_wordless_meanings(offset: Offset = 0,
                                 limit: PageLimit = page_default) -> dict[str, Any]:
        """List a stable page of meanings the dictionary recognises but has no Aussie word for yet, each with its
        plain wording and example sentences."""
        return harness.list_wordless_meanings(offset=offset, limit=limit, translator=translator)

    @tool
    def aussie_entry(entry_id: str, level: Level = 5, vulgarity: Vulgarity = None,
                     include_gated: bool = False, embellishment: int | str | None = None,
                     document_type: DocumentType = "general", document_config: dict | None = None,
                     themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """Resolve a permanent ID to its current card under the requested dials.
        entry_id retains the requested key; entry.id is canonical for redirects. Removed IDs report removed.
        include_gated also returns entries held back as doubtful (marked as such)."""
        return harness.get_entry(entry_id, level=level, vulgarity=vulgarity, include_gated=include_gated,
                                 embellishment=embellishment, document_type=document_type,
                                 document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_random_entry(seed: Seed = 0, concept: str | None = None, theme: str | None = None,
                            level: Level = 5, vulgarity: Vulgarity = None, include_gated: bool = False,
                            embellishment: int | str | None = None, document_type: DocumentType = "general",
                            document_config: dict | None = None, themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """Pick a seeded entry from the whole eligible dictionary, optionally by concept and theme.
        include_gated also returns entries held back as doubtful (marked as such)."""
        return harness.random_entry(seed=seed, concept=concept, theme=theme, level=level, vulgarity=vulgarity,
                                    include_gated=include_gated, embellishment=embellishment,
                                    document_type=document_type, document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_meaning_quiz(seed: Seed = 0, level: Level = 5, vulgarity: Vulgarity = None,
                           include_gated: bool = False, embellishment: int | str | None = None,
                           document_type: DocumentType = "general", document_config: dict | None = None,
                           themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """A seeded term, four gloss options, zero-based answer and full card for a meaning quiz.
        The same dials apply to question and distractors.
        include_gated also returns entries held back as doubtful (marked as such).
        Known true readings are excluded through shared lookup; similarity bands are best effort.
        ranking reports the model and explicit trigram fallback when no meaning model is available."""
        return harness.meaning_quiz(seed=seed, level=level, vulgarity=vulgarity, include_gated=include_gated,
                                   embellishment=embellishment, document_type=document_type,
                                   document_config=document_config, themes=themes, invention=invention,
                                   translator=translator)

    @tool
    def aussie_suggest_name(seed: Seed = 0, shape: str | None = None) -> dict[str, Any]:
        """Suggest a clean Aussie handle: descriptive, place or phrase. No themes or insults.
        The caller checks uniqueness and asks again on a clash."""
        return harness.suggest_name(seed=seed, shape=shape, translator=translator)

    @tool
    def aussie_variations(family: str, parts: dict[str, str], level: Level = 5, seed: Seed = 0,
                          vulgarity: Vulgarity = None, registers: Registers = None, regions: Regions = None,
                          unlock: Unlock = None, embellishment: int | str | None = None,
                          document_type: DocumentType = "general", document_config: dict | None = None,
                          themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """Compatible part changes for a constructed expression, keeping the other parts fixed.
        Pass its family and complete role-to-ingredient mapping. Options include the whole expression and spans."""
        return harness.variations(family, parts=parts, level=level, seed=seed, vulgarity=vulgarity, registers=registers,
                                  regions=regions, unlock=unlock, embellishment=embellishment,
                                  document_type=document_type, document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_lint(text: Text, level: Level = 5, vulgarity: Vulgarity = None,
                    original: Original | None = None, markup: str = "text", english: str | None = None,
                    embellishment: int | str | None = None,
                    document_type: DocumentType = "general", document_config: dict | None = None, themes: Themes = None, invention: Invention = None,
                    suggest: bool = True, unlock: Unlock = None) -> dict[str, Any]:
        """Lint an Aussified draft: flagged or non-Australian phrases, swearing over the cap or overused, US
        spelling, and US and British words (english: us, uk, auto, none, as for aussie_translate). Pass the original text to also check length and that names and numbers survive.
        Also suggests spots that could be more Aussie. markup (markdown, mdx, auto) lints the prose only and,
        with the original, checks its code and markup came through unchanged. embellishment (deadset, dinkum,
        troppo; default Dinkum for General): how much longer than the original it may run. suggest=False
        skips the optional suggestions (a whole engine translation), for a faster check."""
        return harness.lint(text, level=level, vulgarity=vulgarity, original=original, markup=markup,
                            english=english, embellishment=embellishment, document_type=document_type,
                            document_config=document_config, suggest=suggest, unlock=unlock, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_guide(level: Level = 5, vulgarity: Vulgarity = None,
                     embellishment: int | str | None = None,
                     document_type: DocumentType = "general", document_config: dict | None = None,
                     themes: Themes = None, invention: Invention = None) -> dict[str, Any]:
        """Voice, language limits and craft rules for Aussifying at a level (1-5), and how much liberty to take
        at an embellishment (deadset, dinkum, troppo; default Dinkum for General)."""
        return harness.guide(level=level, vulgarity=vulgarity, embellishment=embellishment,
                             document_type=document_type, document_config=document_config, translator=translator, themes=themes, invention=invention)

    @tool
    def aussie_plan(text: Text, level: Level = 5, seed: Seed = 0, vulgarity: Vulgarity = None,
                    variety: Variety = 0, registers: Registers = None,
                    regions: Regions = None, unlock: Unlock = None,
                    markup: str = "text", english: str | None = None,
                    embellishment: int | str | None = None,
                    document_type: DocumentType = "general", document_config: dict | None = None,
                    themes: Themes = None, invention: Invention = None,
                    popularity: Popularity = False, pins: dict | None = None,
                    personal_terms: list[dict] | None = None) -> dict[str, Any]:
        """The rule engine's draft, the slang it planned (with riffs and suggested openings), and the sentences
        it found too formal to handle, and guidance for the text's genre and embellishment. Takes
        aussie_translate's options. embellishment defaults to dinkum, a retelling's (the plan is for writing
        your own version); pass the genre's own setting for a plan that matches aussie_translate's output."""
        return harness.plan(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                            registers=registers, regions=regions, unlock=unlock, markup=markup, english=english,
                            embellishment=embellishment, document_type=document_type, document_config=document_config,
                            translator=translator, themes=themes, invention=invention, popularity=popularity, pins=pins, _preferences_hook=preferences_hook, personal_terms=personal_terms,
                            _personal_terms_hook=personal_provider)

    @tool
    def aussie_translate(text: Text, level: Level = 5, seed: Seed = 0, vulgarity: Vulgarity = None,
                         variety: Variety = 0, registers: Registers = None,
                         regions: Regions = None, unlock: Unlock = None,
                         markdown: bool = False, markup: str = "text", english: str | None = None,
                         embellishment: int | str | None = None,
                         document_type: DocumentType = "general", document_config: dict | None = None,
                         themes: Themes = None, invention: Invention = None,
                         popularity: Popularity = False, pins: dict | None = None,
                    personal_terms: list[dict] | None = None) -> dict[str, Any]:
        """Deterministic rule-engine translation (same text, level and seed give the same output). Change the
        seed for a different version. variety N picks among the N best-fitting terms only (1 = always the best
        fit); 0, the default, weighs every eligible term. registers (current, dated, archaic) and regions (e.g.
        qld) narrow or widen what the level allows.
        unlock (flags whose gated entries become eligible) widens it.
        markup (markdown, mdx, auto) translates only the prose of a document, keeping code, tags, links, front matter
        and headings exactly as they were. english (us, uk, auto, none): the English the text is in, for US and
        UK words Australians say differently (faucet -> tap; British pants -> undies only for uk). embellishment
        (0-2 or deadset, dinkum, troppo): how much liberty the telling takes, from none (the words swap, nothing
        added) to a performed yarn; default Dinkum for General; named types supply presets."""
        return harness.translate(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                                 registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english,
                                 embellishment=embellishment, document_type=document_type,
                                 document_config=document_config, translator=translator, themes=themes, invention=invention, popularity=popularity, pins=pins, _preferences_hook=preferences_hook, personal_terms=personal_terms,
                            _personal_terms_hook=personal_provider)

    @tool
    def aussie_suggest_selection(text: Text, span: list[int], level: Level = 5, seed: Seed = 0,
                         vulgarity: Vulgarity = None, variety: Variety = 0, registers: Registers = None,
                         regions: Regions = None, unlock: Unlock = None,
                         markdown: bool = False, markup: str = "text", english: str | None = None,
                         embellishment: int | str | None = None,
                         document_type: DocumentType = "general", document_config: dict | None = None,
                         themes: Themes = None, invention: Invention = None,
                         popularity: Popularity = False, pins: dict | None = None,
                         personal_terms: list[dict] | None = None) -> dict[str, Any]:
        """Translate once and suggest alternatives at an output span, snapped to words and whole changes."""
        return harness.suggest_selection(text, span=span, translator=translator, level=level, seed=seed,
            vulgarity=vulgarity, variety=variety, registers=registers, regions=regions, unlock=unlock,
            markdown=markdown, markup=markup, english=english, embellishment=embellishment,
            document_type=document_type, document_config=document_config, themes=themes, invention=invention,
            popularity=popularity, pins=pins, personal_terms=personal_terms, _preferences_hook=preferences_hook,
            _personal_terms_hook=personal_provider)

    @tool
    def aussie_verify(text: Text, original: Original, level: Level = 5, vulgarity: Vulgarity = None,
                      markup: str = "text", english: str | None = None,
                      embellishment: int | str | None = None,
                      document_type: DocumentType = "general", document_config: dict | None = None,
                      themes: Themes = None, invention: Invention = None, unlock: Unlock = None) -> dict[str, Any]:
        """Check a finished translation (anyone's: the engine's, yours, a person's) against its original: a log of
        problems, worst first, each with a severity (critical: a lost number, a piece of markup changed, or an
        empty translation; major: breaks the brief; minor: craft, a sentence nothing in the translation says
        again, or a hint worth a look; info: coverage), and metrics. Deterministic; it
        doesn't judge tone or flow. english as for aussie_translate; embellishment sets the length limit (default
        Dinkum for General)."""
        return harness.verify(text, original=original, level=level, vulgarity=vulgarity, markup=markup,
                              english=english, embellishment=embellishment, document_type=document_type,
                              document_config=document_config, unlock=unlock, translator=translator, themes=themes, invention=invention)

    if selected_tools is not None and selected_tools-known_tools:
        raise UserError('unknown tools: '+', '.join(sorted(selected_tools-known_tools)))
    return MCPServer("aussiefy", instructions=instructions(allow_document_config=allow_document_config),
                     tools=registered_tools)


def main() -> None:
    build_server().run("stdio")


if __name__ == "__main__":
    main()
