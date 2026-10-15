"""aussiefy: rewrite plain English as genuine Australian English, at levels 1 (light) to 5 (full pub yarn).

The Python API is the toolkit every other surface (CLI, MCP server, yarn mode, the skill) adapts:

    import aussiefy
    aussiefy.translate("I'm extremely busy", level=4).text   # the rule engine (a Result, with explain records)
    aussiefy.translate(markdown_source, markdown=True)      # DocumentResult: prose units and protected spans
    aussiefy.lookup("very tired")                            # Aussie options for a meaning, or what a term means
    aussiefy.lint(draft, original=text)                      # what's wrong with a draft, and what could be more Aussie
    aussiefy.guide(level=5)                                  # voice, language limits and craft rules
    aussiefy.plan(text)                                      # the engine's draft and planned phrases, for an agent
    aussiefy.verify(translation, original=text)              # problems with severity: facts, policy, markup, drops
    aussiefy.yarn(text)                                      # Claude retells it with the toolkit (needs anthropic)

Each takes the same keyword-only dials, by number or name: level 1-5 (tourist, blow-in, local, larrikin,
swaggie) and vulgarity 0-3 (nan, dad, uncle-bob, tradie; default: the level's own, nan at 1-2, dad at 3-4,
uncle-bob at 5). translate and plan also take variety, registers, regions and unlock, and every function an
optional `translator` for a non-default
dictionary: Translator(load_dictionary(["my_entries.yaml"])). Results report both dials as number and name.
"""

from .engine import Result, Translator, default_translator
from .translation import translate
from .markdown import DocumentResult
from .harness import guide, lint, lookup, plan, verify
from .loader import load_dictionary
from .model import Dictionary
from .policy import Policy
from .errors import UserError
from .schema import Entry, SchemaError
from .yarn import yarn

__all__ = ["translate", "lookup", "lint", "guide", "plan", "verify", "yarn", "Translator", "default_translator", "Result",
           "DocumentResult", "Policy", "Dictionary", "load_dictionary", "Entry", "SchemaError", "UserError"]
__version__ = "0.1.0"
