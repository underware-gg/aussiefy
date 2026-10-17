# X-post and reference-persona vocabulary harvest

This is candidate discovery and editorial curation, not a scored retelling benchmark or evidence of engine
quality. The user requested the X-post agents' colourful language and related expressions, then three
unharnessed versions of every reference text: a tradie, a dockie and an uncouth Uncle Bob.

## Inputs and method

The reference set is all 15 `.txt` files in `tests/corpus/reference/`, whose editions, authors and licences
are recorded in [SOURCES.yaml](../../tests/corpus/reference/SOURCES.yaml). Each of three fresh agent contexts
received one persona brief and the same instruction to read only those originals, write full retellings,
retain meanings and supplied excerpt endings, and list distinctive expressions actually used. They received
no Aussiefy skill, dictionary, engine draft, prior retelling or tools from the writing workflow. Shell access
was allowed only for reading originals and saving scratch outputs. One context handled all 15 texts for its
persona; these are not 45 independent writer contexts.

The raw outputs are under `texts/<reference-stem>/<persona>.txt`, with the agents' candidate lists alongside.
They are retained unchanged. Persona descriptions are creative briefs, not engine presets, occupational
linguistic research or representations of how every worker speaks. The Uncle Bob brief did not impose the
engine's same-named vulgarity cap. No blind judges, fidelity certification or quality scores were requested
or run. The manifest records source/output hashes and the context names.

The earlier X-post exercise used five fresh contexts given the same plain announcement brief. Its selected
suggestions and editorial extrapolations are recorded in [DECISIONS.md](DECISIONS.md), without inventing a
full transcript for that earlier exercise.

## Curation

Agent labels such as `established: true` are proposals, not attestations. Review the expression's actual
sense and grammar, compare current forms/variants/triggers and dialect swaps, and distinguish established
slang from a newly written image. Accepted creative comparisons go into `aussiefy/data/riffs.yaml` under a
semantically appropriate entry. They inherit existing mood, swear-cap and effective document/profile rules.
Nothing in this pass adds persona detection or a persona switch to the engine.

See [DECISIONS.md](DECISIONS.md) for accepted terms, rejected or covered candidates, the earlier-round audit
and remaining independent vocabulary work. Raw retellings may contain awkward phrasing, invented images or
meaning errors: inclusion in the evidence is not dictionary acceptance.
