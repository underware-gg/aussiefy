# Translation context and embellishment

Level controls the weight of Australian words (1–5); vulgarity controls language (0–3). Embellishment is an
independent third dial: `deadset` (0) changes the words, `dinkum` (1) gives them a conversational voice, and
`troppo` (2) permits a performed yarn. Set it with `--embellishment` / `-e`, or `embellishment=` in Python/MCP.

```sh
aussiefy translate "I am very tired." -l 5 --vulgarity nan --embellishment deadset
aussiefy translate "I am very tired." --english uk --embellishment troppo --explain
```

## Document types and exact behaviour overrides

Document behaviour is explicit. `document_type="general"` / `--document-type general` is the default, with
Dinkum embellishment. It applies no genre-specific restrictions. `auto` opts into deterministic detection of
story, personal, news, instructions, technical or official prose. A named type selects that preset directly.
Named types retain their own default embellishment (story Troppo, personal Dinkum, the others Deadset).
Explicit embellishment always overrides that default.

`custom` starts with optional document behaviours disabled. Choosing an embellishment alone does not enable
its garnish, openings or performance for Custom; specify exactly what you want in `document_config`.
Core vocabulary substitution, level, vulgarity limits and selected markup protection still apply.
Neither General nor Custom requires a complete configuration. Omitted document settings inherit the selected
type's values: General keeps normal optional behaviours, Custom keeps them off. Numeric engine settings in
both cases start from the selected level and vulgarity profiles. Setting an opener probability alone does not
enable the opener in Custom; also include `opener` in its `garnish` list.

Every type accepts the same `document_config` object (`--document-config` takes JSON). Precedence is the
selected preset, then explicit dials, then exact behaviour overrides. Lists replace inherited lists; `false`,
`[]` and `0` are explicit values. Omit a field to inherit; unknown fields and invalid values are errors.

```sh
aussiefy translate "You are very tired." --document-type general -e dinkum --document-config '{"garnish":["tag"],"keep_quotes":true}'
aussiefy translate "Read the API documentation." --document-type custom --document-config '{"term_domains":["technical"],"garnish":[]}'
```

| Setting | Values and effect |
|---|---|
| `garnish` | Exact list from `connective`, `opener`, `tag`, `aside`, `tail`, `closer`, `riff`, `infix`, `insult`; probabilities default to level/vulgarity profiles, with advanced tuning below |
| `openings` | Boolean: offer talker's openings in a plan |
| `person_swears` | Boolean: allow swear words to replace neutral descriptions of people, within the vulgarity limit |
| `keep_quotes` | Boolean: preserve quoted wording; straight/curly double-quoted documents may span paragraphs |
| `term_domains` | List of named detected types whose concept/dialect `not_in` vocabulary is protected; `[]` disables this protection |
| `command_context` | Boolean: recognise sentence-initial imperative verbs as commands |
| `dateline_context` | Boolean: preserve news-style datelines |
| `formal_to_rework` | Boolean: offer difficult formal sentences to a retelling writer |
| `guidance` | Text: replace document-type guidance in the brief |
| `draft` | Boolean: include the engine's draft in a yarn brief |
| `keep_share` | Number 0–1: required share of planned phrases retained or declined by a yarn |
| `check_length` | Boolean: enforce the length limit; Custom defaults to false, and an explicit `max_length` enables it unless explicitly disabled |
| `max_length` | Finite number at least 1: retelling length multiplier, plus the existing 20-word allowance |
| `perform` | Boolean: include performance craft guidance |
| `embellishment_guidance` | Text: replace embellishment guidance in the brief |
| `profile` | Object: override engine probabilities, limits, spacing and thresholds; omitted keys inherit dial defaults |

## Advanced profile tuning

Every document type accepts the same `document_config.profile`. Map keys merge with the selected profile;
lists replace it. `{}` inherits all numeric settings; `frames: []` disables vocabulary substitutions. JSON
`null`, unknown keys, wrong types and out-of-range values are errors. The caller owns the coherence of valid
combinations: a permitted garnish placement with probability zero remains off. Overrides do not change the
shared dictionary or future calls. The ordinary level, vulgarity, seed, registers, regions, unlock, English,
variety and embedder arguments keep their existing roles; these are not duplicated inside `profile`.

| Profile setting | Values and effect |
|---|---|
| `substitution` | Map of `lexical`, `phrase`, `idiom` probabilities, each 0–1 |
| `frames` | List from `predicate_adj`, `np`, `adj`, `adv`, `vp`, `clause`, `interjection`, `imperative`, `tag` |
| `garnish` | Map of placement probabilities 0–1: `connective`, `opener`, `tag`, `aside`, `tail`, `closer`, `riff`; distinct from the outer placement allow-list |
| `max_garnish` | Map of nonnegative integer per-document placement limits, combined across clean and swearing channels; a closer can occur at most once |
| `garnish_gap` | Nonnegative integer source sentences that must pass before the same placement repeats, across channels and Markdown units |
| `garnish_per_sentence` | Nonnegative integer combined budget for connectives, openers, asides and tags; tails, riffs and the document closer have their own placement limits |
| `stack` | Probability 0–1 of stacking a second eligible descriptive idiom |
| `phonetic` | Finite nonnegative multiplier on clean drawl; 0 disables drawl, while Australian spelling remains active |
| `stretch` | Two positive integers `[minimum, maximum]` vowel repeats for stretchable garnish, in ascending order |
| `swearing` | Object: `exclaim` and `closer` probabilities 0–1, plus finite nonnegative `infix` and `lean` multipliers; 0 disables that channel/weight, and vulgarity still caps eligibility |
| `rewrite` | Object: integer `min_level` 1–5; nonnegative integer `min_words`, `min_formal_words`; positive integer `formal_length`; `max_coverage` 0–1; controls difficult-sentence detection and requested sentence rewrites |

For flavour around exact technical wording, enable only suitable garnish, protect terminology and tune the
rates independently. Sentence/markup grammar guards still apply, even at probability 1. In strict Markdown,
leading garnish may precede an inline boundary only at the original sentence start, with whole-sentence
context; suffix garnish and riffs require a complete prose sentence. Ambiguous capitalisation can also
prevent a prefix, rather than change a possible name:

```sh
aussiefy translate 'The browser uses cookies. You are very tired.' --document-type custom --vulgarity nan --document-config '{"term_domains":["technical"],"garnish":["opener"],"profile":{"garnish":{"opener":1},"max_garnish":{"opener":1},"phonetic":0}}'
```

Each document operation reports a complete `profile_config`, including inherited probabilities, fallback
limits, swearing rates and rewrite thresholds. Inspect the defaults with `aussiefy guide --json`, or inspect
a translation/plan/check's JSON for the settings it actually used. Copy `profile_config` into
`document_config.profile` to reuse that numeric configuration, alongside your chosen document behaviours.
Explain reports include these settings too. Yarn briefs include `PROFILE_CONFIG`, and session tools retain
the same immutable snapshot.

Tests isolate [advanced profile behaviours](../../../tests/functional/test_profile_overrides.py), including
zero/one probabilities, shared limits, spacing, drawl, swearing, rewrite dispatch, markup and surface parity.

## Shared document contract

All controls have the same names and meaning in Python, CLI, MCP and yarn sessions. Results and explain mode
report the requested type, resolved type and effective behaviours. Auto resolves against the complete original,
including in Markdown and when checking a draft. `guide` has no source text, so Auto is an error there; select
General or a named type. Markdown syntax protection is independent of document behaviour.

`english=` / `--english` selects `us`, `uk`, `auto` or `none`. The default comes from the profile (`auto` in
the bundled profiles). Auto uses American spellings to infer US English; ambiguous British words such as
“pants” need `uk`. `none` disables dialect swaps. Plain Australian equivalents (faucet → tap) apply at every
level, separately from slang. `dialect.yaml` owns the vocabulary and technical/genre exclusions; source
quotes and mentioned words have their own protections. POS tags help distinguish nouns, verbs and names;
the small bundled tagger runs offline without NLTK.

## Document modes

The explicit [`--markdown` / `markdown=True`](markdown.md) mode preserves whole links, tables and HTML,
returns `DocumentResult`, and permits offline ngram/disabled fallback only. It resolves genre and English
once for the whole document and retains separate source/output ranges for each rewritten unit.

The imported `--markup markdown|mdx|auto` / `markup=` contract is an **extended document mode**. It uses opaque
protected spans while translating sentence context, including eligible link labels, table cells and JSX
children; attributes, code, headings, paths, maths and destination syntax stay protected. Table/list rows
suppress garnish. Auto detects the document dialect from the text. It returns the engine's `Result`, with
source-relative records restored to the original source. This contract also applies to planning, lint,
verification and yarn; a rewrite that drops or duplicates a protected span is refused.

Choose either `markdown=True` or a non-text `markup`, rather than combining them. `--surface` cannot preserve
extended markup; use checked sentence rewrites or yarn. Strict Markdown retains its offline-only contract.
The core `Translator.translate` remains plain text; document selection belongs to the public adapter.

Tests: [genre](../../../tests/functional/test_genre.py), [dialect](../../../tests/functional/test_dialect.py),
[POS](../../../tests/functional/test_pos.py), [extended markup](../../../tests/functional/test_markup.py) and
[strict Markdown](../../../tests/functional/test_markdown.py).

Lint suggestions inherit the original's selected document policy and source-English context, including custom dictionary policies,
even when the draft sounds like a story. Held dialect wording is excused only with the same folded surface
and occurrence count; explicitly kept quotes retain their original spelling too. Planning offers riffs only
where the resolved setting permits them: deadset offers none, and strict news/instructions/docs/official
forms below troppo offer none. The dinkum guidance preserves the force of obligations and findings.
