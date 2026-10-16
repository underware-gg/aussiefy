# CLI reference

The `aussiefy` command is a thin shell over the [toolkit](toolkit.md), yarn mode and the maintainer tools.
`aussiefy --help` and `aussiefy <command> --help` print the same options as this page.
A near-miss command in one or two words prints a suggestion on stderr and still translates the text.
With no text arguments on a terminal, a hint explains how to finish stdin. Missing or unreadable
user-named files are exit 2; a single path-like argument (for example `drfat.txt`) is treated as a file,
so a typo cannot silently become a successful translation or lint.

Without a command, arguments go to `translate`: `aussiefy "some text" -l 4` is short for
`aussiefy translate "some text" -l 4`.

## Commands

| Command | What it does |
|---|---|
| `translate` | The rule engine's translation (the default command) |
| `yarn` | The optional API client retells the whole text using the shared harness (needs the `llm` extra) |
| `lookup` | Aussie options for a meaning, or what a term means |
| `lint` | Lint an Aussified draft (exit 1 if there are issues) |
| `guide` | The voice, language limits and craft rules for a level and vulgarity |
| `plan` | The engine's draft, planned phrases and difficult sentences, as JSON |
| `verify` | Deterministic severity-based checks against `--original` ([verification](verification.md)) |
| `judge` | Blind comparison: `brief`, `read`, `tally`, optional paid `run`/`unharnessed` ([judging](../contributor/judging.md)) |
| `yarn-tools` | Hand-run yarn `brief`, `lookup`, `lint`, `submit` |
| `validate` | Validate the dictionary and print stats |
| `show` | Show entries by id, form substring or concept |
| `compare` | How much of a target translation's slang the engine reproduces (a benchmark) |
| `gaps` | Words the engine keeps leaving in plain English, with their nearest concepts |
| `embedder` | The embedding model `lookup` and `gaps` use: see [embedding.md](embedding.md) |
| `dev` | Maintainer tools: `scrape`, `fragments`, `harvest`, `tag`, `review`, `round`, `ingest` |

What `compare`, `gaps` and the `dev` steps do is described in [maintainer-tools.md](maintainer-tools.md).

## Shared options

| Option | Commands | Meaning |
|---|---|---|
| `text` | translate, yarn, lint, plan, verify, judge unharnessed | The text itself, a file path, or nothing to read stdin |
| `--document-type TYPE` | translate, yarn, lint, plan, guide, verify, yarn-tools, judge brief/run/unharnessed | General (default), Custom, Auto detection, or a named type; guide requires a named type |
| `--document-config JSON` | same document operations | Exact behaviour overrides; see [translation controls](translation-controls.md) |
| `-e/--embellishment SETTING` | translate, yarn, lint, plan, guide, verify, yarn-tools, judge brief/run/unharnessed | 0–2 or deadset/dinkum/troppo; default Dinkum for General; named types supply defaults |
| `--english {auto,us,uk,none}` | translate, yarn, lint, plan, verify, yarn-tools, judge brief/run/unharnessed | Source-English dialect context |
| `--markup {text,markdown,mdx,auto}` | translate, yarn, lint, plan, verify, yarn-tools, judge brief/run/unharnessed | Extended document mode; differs from strict `--markdown` ([controls](translation-controls.md)) |
| `--dict PATH` | all leaf commands except embedder, dev ingest, dev round and judge tally | An extra entry file or directory, on top of the built-in dictionary (repeatable); on nested commands, put it after the step |
| `-l/--level LEVEL` | translate, yarn, yarn-tools, lookup, lint, verify, guide, plan, compare, gaps, judge brief/run/unharnessed | 1-5 or `tourist`, `blow-in`, `local`, `larrikin`, `swaggie` (default 5) |
| `--vulgarity VULGARITY` | translate, yarn, yarn-tools, lookup, lint, verify, guide, plan, judge brief/run/unharnessed | 0-3 or `nan`, `dad`, `uncle-bob`, `tradie` (default: the level's own) |
| `-s/--seed SEED` | translate, yarn, yarn-tools, plan, judge brief/run | Seed for the weighted choices (default 0). `random` picks one and prints it to stderr |
| `--json` | translate, yarn, lookup, lint, verify, guide, plan, gaps, judge brief/run/read/unharnessed | Print the full result as JSON (`plan` always prints JSON). yarn-tools tool steps already print JSON; its brief prints the prompt |
| `--variety N` | translate, plan | Choose among the N best-fitting terms only; 0 (the default) weighs every eligible term |
| `--registers LIST` | translate, plan | Comma list from `current`, `dated`, `archaic` (default: per level) |
| `--region LIST` | translate, plan | Comma list of region tags to prefer, such as `qld` |
| `--unlock LIST` | translate, plan | Comma list of flags whose gated entries become eligible, or `all` |

The dials are described in [dials.md](dials.md); the seed and `--variety` in
[getting-started.md](../user/getting-started.md#get-the-same-result-again-or-a-different-one).

## Command options

**`translate`**

| Option | Meaning |
|---|---|
| `--explain` | Report every decision on stderr: see [explain.md](explain.md) |
| `--brief` | With `--explain`, leave out the rejected candidates |
| `--markdown` | Preserve protected source and headings; JSON/explain uses document units: see [markdown.md](markdown.md) |
| `--embedder {ngram,none,bundled,local}` | The concept-detection fallback (default `ngram`): see [embedding.md](embedding.md) |
| `--surface` | Have Claude smooth the joins: see [llm-modes.md](llm-modes.md) |
| `--rewrite {hard,all}` | Hand whole sentences to Claude: the difficult ones, or all |
| `--model MODEL` | Claude model for `--surface` and `--rewrite` (default `claude-opus-5-5`) |

**`yarn`**: `--model MODEL`, the Claude model (default `claude-opus-5-5`); `--no-cache`, bypass the
accepted-result cache for this run.

**`lookup QUERY...`**: `--limit N`, the most results to show (default 8); `--include-gated`, also show
entries held back as doubtful (omitted entries remain excluded). `N` must be at least 1.
With `--json`, `--short` returns compact cards for an agent: form, gloss, frame, level and vulgarity.

**`lint`**: `--no-suggestions` skips engine suggestions.
`--original FILE`, the source text, which adds the fidelity checks (length, names and numbers).
Text markers are `!` issues, `?` warnings and `~` suggestions. With warnings but no issues, it prints
`ok (N warning(s))` and exits 0. Issues exit 1; suggestions are not repeated when already reported.

**`verify`**: requires `--original FILE`; `--all` also lists information such as untouched sentences.
Use `--json` for the full report. Critical or major problems exit 1; minor problems alone exit 0.

**`yarn-tools STEP SOURCE [ARG]`**: `STEP` is `brief`, `lookup`, `lint` or `submit`. `SOURCE` is the original
file. `lookup` needs a query; `lint` and `submit` need a draft file. `--declined FILE` supplies a YAML list
of `{phrase, reason}` records to lint or submit; `--log FILE` appends tool calls and diagnostics as JSONL.
`-o/--output FILE` saves an accepted submission. Each command starts a fresh session, so repeat the same
dials, overrides and markup flags, and carry declines with `--declined`.

```sh
aussiefy lookup --short --json "very busy"
aussiefy verify --original source.txt draft.txt --all
aussiefy yarn-tools brief source.txt -l 3
aussiefy yarn-tools lint source.txt draft.txt -l 3 --log calls.jsonl
aussiefy yarn-tools submit source.txt draft.txt -l 3 -o accepted.txt --log calls.jsonl
```

**`show QUERY`**: matches an entry's id or form by substring, or a concept by name. No match prints a
notice on stderr and exits 1. Entries and staging files use the same YAML field order.

**`compare ORIGINAL TARGET`**: `-l/--level LEVEL` (number or name; default 5); `--seeds N`, how many seeds to
translate with, from 0 (default 10).

**`gaps FILE...`**: `-l/--level LEVEL` (number or name; default 5); `--embedder {ngram,bundled,local}` (default:
the embedder in use, as `aussiefy embedder status` shows); `--draft NAME=PATH`, an Aussified draft of the
text whose file stem is NAME, whose lines still in the original wording are also listed (repeatable);
`--limit N` (default 40).

**`embedder ACTION [WHICH]`**: `ACTION` is `status`, `install`, `enable`, `disable` or `remove`. `WHICH`, with
`enable` and `disable`, is `bundled` or `local` (default `local`). With `install`: `--model NAME` (default
`sentence-transformers/all-MiniLM-L6-v2`), `--torch {cpu,pypi,skip}` (default `cpu`), `--from PATH`,
`--enable`, `--dry-run`. Every action prints its result as JSON.

**`dev`** steps:

| Step | Arguments and options |
|---|---|
| `dev scrape URL...` | `-o FILE` (default `data/staging/scraped.yaml`); `--source-url URL` (required for a saved HTML file; recorded and checked against the policy); `--refresh` (ignore the fetch cache); `--permitted` (override `aussiefy/data/source_policy.yaml` for a source you have permission to extract from) |
| `dev ingest MANIFEST...` | `--force` re-fetches existing files; `--ref REF` overrides pinned defaults and items ([ingestion](../contributor/ingestion.md)) |
| `dev fragments` | `-o FILE` (default `data/staging/fragments.yaml`) |
| `dev harvest ORIGINAL REWRITE` | `-o FILE` (default `data/staging/harvest.yaml`) |
| `dev tag STAGING` | `-o FILE` (default `data/staging/tagged.yaml`); `--model MODEL` (default `claude-opus-5-5`); `--limit N` |
| `dev review TAGGED` | `--apply` (write the changes; without it, a dry run); `--data-dir DIR` (default: the package's data) |
| `dev round DIRECTORY` | `--write` (write the entries and concepts, after validating them); `--data-dir DIR` |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | A negative answer: `lint` found issues, `lookup` found nothing, `show` matched nothing |
| 2 | A bad dictionary, setting or argument: a missing or unreadable file, a corrupt config or reply cache, an unknown dial or policy name, a failed `embedder install`, or no Claude SDK or credentials for `dev tag` |
| 3 | `dev scrape` refused a reference-only source (see `aussiefy/data/source_policy.yaml`) |
| 4 | An LLM mode fell back to the engine's draft: `yarn`, `--surface` or `--rewrite` could not reach Claude, or its result was not accepted. Having nothing to polish is not a fallback |
