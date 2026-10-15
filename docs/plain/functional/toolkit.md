# The toolkit and its surfaces

Language models are good at Australian English when they have quality source material and clear guidance.
The toolkit gives them both, as six plain functions that return JSON-ready dicts. `aussiefy.harness` gathers
them; `lookup`, `lint` and `guide` each live in their own module (`lookup.py`, `lint.py`, `guide.py`).

| Function | CLI | What it does |
|---|---|---|
| `lookup(query)` | `aussiefy lookup "very busy"` | Genuine Aussie options for a meaning, or what a term means ("goog"), filtered to the level and vulgarity |
| `lint(text)` | `aussiefy lint < draft.txt` | Lints a draft for flagged non-Aussie phrases, swearing over the cap (via `aussiefy/data/swears.yaml`), US spelling and US/UK words (`aussiefy/data/dialect.yaml`), plus optional "could be more Aussie" suggestions. With `original=`, also checks fidelity: length, and names and numbers kept or invented |
| `guide(level)` | `aussiefy guide -l 5` | Voice, language limits and the craft rules learned from good translations (swear inside sentences, tag-ons only in dialogue, connectives in narration, no pile-ups, Australian spelling); craft is filtered to the requested dials; `aussiefy/data/guide.yaml` also owns the workflow, plan note and yarn rules |
| `plan(text)` | `aussiefy plan < in.txt` | The engine's draft, its planned phrases, riffs and suggested openings, and the sentences it found too formal |
| `translate(text)` | `aussiefy "text"` | The deterministic rule-engine output |
| `verify(text, original=...)` | `aussiefy verify draft.txt --original original.txt` | Severity-based fidelity, structure and policy checks; [reference](verification.md) |

How an agent uses them, step by step, is in [skills/aussiefy/SKILL.md](../../../skills/aussiefy/SKILL.md),
which also explains each kind of lint issue (`!`), warning (`?`) and suggestion (`~`).

## The Python API

```python
from aussiefy import Translator, translate, lookup, lint, guide, plan, yarn, load_dictionary

r = translate("I'm extremely busy.", level=4, seed=7)
r.text          # "I'm flat out like a lizard drinking."
r.decisions()   # spans, chosen entries and garnish: what the engine decided
r.to_dict()     # the policy envelope, decisions, explain records and difficult_sentences

tr = Translator()   # reuse for many calls; Translator(load_dictionary(["my-extra.yaml"])) to extend
tr.translate(text, level="swaggie", seed=1, vulgarity="dad", regions=["vic"], unlock=["archaic"])
lookup("very tired", translator=tr)   # the toolkit functions take a translator too; the default is shared
```

Every function takes keyword-only dials, by number or name: `level` (default 5) and `vulgarity` (default: the
level's own). `translate`, `plan` and `yarn` also take `seed` (default 0). `translate` and `plan` also take
`variety`, `registers`, `regions` and `unlock`; only `translate` takes `markdown` (default false).
The engine/Translator and `plan` remain plain-text operations. `lookup` takes `limit` (default 8) and `include_gated`, and
`lint` takes `original`. Every function takes an optional `translator` for a non-default dictionary.

Document operations (`translate`, `plan`, `lint`, `verify`, `guide`, `yarn`) also take `document_type="general"`
and `document_config=None`. General defaults to Dinkum; Auto opts into detection; named types select presets;
Custom enables only configured optional behaviours. The shared override object replaces inherited values after
explicit dials, including false and empty lists. See [translation controls](translation-controls.md).

`translate` returns a `Result`, or `DocumentResult` with explicit `markdown=True`
([Markdown contract](markdown.md)); the other toolkit functions return dicts, and `yarn` returns a result whose
`outcome` is `applied` or `fell_back`. The package also exports `Policy`, `Dictionary`, `Entry`,
`default_translator`, and the two errors it raises on purpose: `SchemaError` (an invalid dictionary) and
`UserError` (a problem the user can fix; the CLI prints it and exits 2).

`Result.to_dict()` is a superset of the toolkit translate dict: `text`, `level`, `level_name`, `vulgarity`,
`vulgarity_name`, `policy_warnings`, `seed`, `variety`, `decisions` and `difficult_sentences`, plus `source`
and `explain`. The old `difficult` and duplicate `warnings` JSON keys are gone. Policy warnings name region
tags or unlock flags unused by the dictionary; invalid register and unlock names raise `UserError`.

MCP tools expose parameter descriptions and dial choices in their schemas, and preserve `UserError`
messages as tool errors. `lookup` requires `limit >= 1` and marks each riff's `best` fit.

## The same toolkit, three more ways

- **MCP server, for any MCP-capable agent.** The `aussiefy-mcp` command (stdio) serves the tools
  `aussie_lookup`, `aussie_lint`, `aussie_guide`, `aussie_plan` and `aussie_translate`. Setup is in the
  [user guide](../user/agents.md).
- **Claude Code skill.** [skills/aussiefy/SKILL.md](../../../skills/aussiefy/SKILL.md) walks an agent through
  brief → guide → plan → write with lookups → lint and fix → deliver, using the CLI.
- **Claude API tools.** `tool_definitions()` in the `aussiefy.yarn` module gives `lookup`, `lint` and `submit`
  for any Messages API agent; `brief()` and `dispatch_tool()` in the same module are the loop's pure parts, for
  driving it yourself. Import them with `from aussiefy.yarn import ...`: on the package, `aussiefy.yarn` is the
  yarn function, not the module. [Yarn mode](llm-modes.md) is the reference loop.

Every surface takes the same parameters by the same names and defaults; `tests/functional/test_interfaces.py` holds them
in step (see [DD-008](../../architecture/decisions/dd-008-one-toolkit-thin-surfaces.md)).

Genre, English, embellishment and extended document controls are described in [translation controls](translation-controls.md). `lookup(short=True)` offers compact cards; `lint(suggest=False)` skips optional engine suggestions.
