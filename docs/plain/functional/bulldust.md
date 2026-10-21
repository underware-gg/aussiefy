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
lower a part's tier. Exact theme overrides remain independent of the swear cap.

Bare “bugger me sideways” is Dad's surprise oath. Implement combinations such as “with a rusty spanner”
start at Uncle Bob for sex and innuendo; the title combination starts at Uncle Bob for religion. The
ordinary implement endings do not acquire a sexual tag in isolation. The stronger oath has its own swear
rating and a lower pick weight.

Families declare a maximum exaggeration requirement, compared with `riff_exaggeration`. Comic constructions
in solemn text require `solemn_comic_terms`. In translation, the two surprise families may enter the opener
pool under the existing garnish permissions and rates. This slice does not enable constructed substitutions
as a fallback; that is a separate integration step.

## Evidence, identities and spans

Each result has a distinct `construction/...` ID and `entry_id: null`. Its identity includes the family,
template and ordered ingredient IDs and wording, so changing evidence alone does not change the expression's
ID. Every part records its evidence, origin, credit, ingredient ID and a real entry ID when applicable.
`out_span` is a half-open pair of Unicode code-point offsets into the canonical expression's `text`.
Translation casing and phonetic changes do not alter those canonical spans.

The whole expression has `coined_by: constructor`, a derived `bulldust` label and no borrowed sources.
Evidence for a stem stays on that stem; Rob's ending credit stays on the ending. No persistent dictionary
entry is created. Existing changes version 2 reports constructed garnish with a null entry ID, no constructed
alternatives and a removal when locally renderable. Full public construction cards and in-translation part
spans are reserved for the coordinated contract update.

## Data and bounds

`aussiefy/data/constructions.yaml` declares `aussiefy-constructions/v1`, `settings`, `ingredients` and `families`.
An ingredient has `id`, `kind` and either `entry_id` or literal `text`. An entry reference inherits all fields;
it cannot override wording or evidence. Literal ingredients accept term metadata, level, vulgarity and weight.
Families declare `id`, `template`, named `slots` mapped to kinds, `concept` and `frame`; optional fields include
term metadata, level, vulgarity, weight, exaggeration, tone, `preferred_words`, `semantic_degree` and opener
`placement`. The loader validates them before generation. Each slot occurs exactly once; format directives,
attribute access and indexing are not accepted. Inserted ingredient text is opaque, even if it contains braces.

The core attempts at most 64 combinations per compatible family, without building the Cartesian product.
Seeded mixed-radix sampling visits distinct combinations. Known full entry forms, riffs and imagery, and
other results in the call, suppress collisions. The dictionary cannot prove novelty beyond that known set.
Candidates closest to the family's preferred word-count band rank first, then seeded weights decide order
within the same cadence score. This is a simple readable-length heuristic, not a fluency or humour model.

The data settings are `search_budget` (1–1024), `max_results` (5–100), and finite non-negative
`cadence_penalty`. Core values are 64, 20 and 0.1. A missing catalogue keeps existing custom data compatible
and returns no constructions. Changing the catalogue or these settings can change seeded results.
