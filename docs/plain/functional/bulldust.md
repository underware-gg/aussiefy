# Bulldust constructor

`bulldust` makes original Australian-sounding expressions from reviewed construction families and typed
ingredients. Results are labelled `bulldust`; a familiar stem does not make a new whole expression attested.
There are no network or model calls. Repeating the same dictionary, settings and seed repeats the results.

```sh
aussiefy bulldust HUNGRY --vulgarity nan --json
aussiefy bulldust --family sideways-with-implement --vulgarity uncle-bob --parts '{"stem":"bugger-sideways"}'
```

```python
from aussiefy import bulldust

result = bulldust("HUNGRY", seed=7, vulgarity="nan")
for candidate in result["results"]:
    print(candidate["text"], candidate["evidence"])
```

Python, the CLI and MCP's `aussie_bulldust` call the same operation. `concept` is an optional dictionary concept
ID, case-insensitive. `family` restricts the pattern. `parts` pins slot names to ingredient IDs returned in a
previous result; compatible unpinned slots vary. A known ingredient of the wrong kind produces no compatible
construction. Unknown IDs or slots are user errors. `limit` defaults to 5 and is bounded by the selected
catalogue (20 in the core).

The other parameters are `level=5`, `seed=0`, `vulgarity=None`, `registers=None`, `regions=None`, `unlock=None`,
`embellishment=None`, `document_type="general"`, `document_config=None`, and Python's `translator=None`.
Vulgarity inherits the level's default; embellishment inherits the selected document preset. Auto detection
requires source text, which this operation does not have: select General or another explicit preset.
The operation reports `constructed` or `no-compatible-construction`, with `results`, attempted combinations,
rejection reasons and the effective policy envelope. CLI exit codes are 0, 1 and 2 respectively for results,
no compatible construction and invalid input.

## Initial families and policy

The small initial catalogue covers surprise-oath stems with implement or title endings, and exaggerated
hunger predicates. For example, “hungry enough to eat the shadow off a sausage” is a reviewed agent coinage.
These are samples of construction, not a claim that every combination is funny or previously unknown.

Families and ingredients must pass the selected level, theme, swear, register and usage/meaning gates.
Entry-backed ingredients retain manual gates, regional rules, wording, weight and evidence from the entry.
A composite takes the highest theme tier among its parts and family; a family can raise a tier but cannot
lower a part's tier. Exact theme overrides remain independent of the swear cap. Lint and model-output
checks recognise reviewed combinations under these same theme tiers, preserving occurrences already in
the source. Ambiguous wording stays unresolved if any complete reviewed reading is allowed.

The constructor rates the actual assembled words, including known profane compounds and words formed
where parts join. Slot names are not spoken text. Reviewed whole-expression ratings still apply; ordinary
words are not swears merely because they contain the same letters.

Bare “bugger me sideways” is Dad's surprise oath. Implement combinations such as “with a rusty spanner”
start at Uncle Bob for sex and innuendo; the title combination starts at Uncle Bob for religion. The
ordinary implement endings do not acquire a sexual tag in isolation. The stronger oath has its own swear
rating and a lower pick weight.

Part weights multiply, so adding neutral ingredients does not dilute a variant's preference. Constructed
openers use that composite weight without a second preference for the stronger swear. Reusing an
entry-backed stem in a different construction does not evade the within-text repeat check. The check
also covers a bare stem used as an ordinary substitution, in either order.

Families declare a maximum exaggeration requirement, compared with `riff_exaggeration`. Comic constructions
in solemn text require `solemn_comic_terms`. Translation uses all reviewed opener families when invention is enabled. Troppo enables it by
default; Dinkum, Deadset and Custom leave it off unless explicitly allowed. Non-garnish constructions
are fallback candidates only where no curated entry fits, through the ordinary render path.
An existing result complement cannot take a second invented result clause. The standalone constructor
is an explicit construction request, independent of automatic translation's fallback switch.

## Evidence, identities and spans

Each result has a distinct `construction/...` ID and `entry_id: null`. Its identity includes the family,
template and ordered ingredient IDs and wording, so changing evidence alone does not change the expression's
ID. Every part records its evidence, origin, credit, ingredient ID and a real entry ID when applicable.
`out_span` is a half-open pair of Unicode code-point offsets into the canonical expression's `text`.
Translation casing and phonetic changes do not alter those canonical spans.

The whole expression has `coined_by: constructor`, a derived `bulldust` label and no borrowed sources.
Evidence for a stem stays on that stem; Rob's ending credit stays on the ending. No persistent dictionary
entry is created. Changes v3 reports construction cards, selected membership and alternatives, plus each rendered
part's local occurrence span. Canonical spans stay in card text; casing, drawl and Markdown escaping
are tracked separately for occurrences. [Contract and replay](changes.md) defines keys and joins.

All rich themes use `{name, tier}` objects with `minimum_vulgarity`. Every assessed bulldust rendering
has an attributable maker, including derived agent coinage where the evidence assessment establishes
it. Plans include canonical construction cards and labelled local parts. The operation also returns
the shared agent-neutral `scaffold`, with eligible meanings/examples, family slots, ingredients and
constraints; Yarn receives the same material without depending on a provider SDK.

## Data and bounds

`aussiefy/data/constructions.yaml` declares `aussiefy-constructions/v1`, `settings`, `ingredients` and `families`.
An ingredient has `id`, `kind` and either `entry_id` or literal `text`. An entry reference inherits all fields;
it cannot override wording or evidence. Literal ingredients accept term metadata, level, vulgarity and weight.
Families declare `id`, `template`, named `slots` mapped to kinds, `concept` and `frame`; optional fields include
term metadata, level, vulgarity, weight, exaggeration, tone, `preferred_words`, `semantic_degree` and opener
`placement`. The loader validates them before generation. Each slot occurs exactly once; format directives,
attribute access and indexing are not accepted. Inserted ingredient text is opaque, even if it contains braces.

An opener family's optional `converted_parts` pins every slot to a compatible ingredient, identifying an
existing opener retained during migration. Translation uses only these pinned recipes until invention is
enabled; standalone generation can still vary their parts. Unknown or incompatible pins fail loading.

The core attempts at most 64 combinations per compatible family, without building the Cartesian product.
Seeded mixed-radix sampling visits distinct combinations. Known full entry forms, riffs and imagery, and
other results in the call, suppress collisions. The dictionary cannot prove novelty beyond that known set.
Candidates closest to the family's preferred word-count band rank first, then seeded weights decide order
within the same cadence score. This is a simple readable-length heuristic, not a fluency or humour model.

The data settings are `search_budget` (1–1024), `max_results` (5–100), and finite non-negative
`cadence_penalty`. Core values are 64, 20 and 0.1. A missing catalogue keeps existing custom data compatible
and returns no constructions. Changing the catalogue or these settings can change seeded results.
