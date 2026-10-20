# Semantic research spikes, 20 October 2026

Baseline: `a64c0d2`. The research and feature checkpoint were isolated in `.worktrees/semantic-refinement`
on `semantic-refinement-20261020`. The user subsequently authorised dev integration; the separate
[integration review](../../docs/architecture/reviews/design-review-2026-10-20-dev-integration.md) records
combined validation. Measurements below retain their original inputs and scope. [Plan and remaining slices](PLAN.md).

## Degree and complement spike

[Before](before.json) and [the degree-only checkpoint](after-degree.json) run the same ten original synthetic sentences,
forced substitution profile, lexical backend and seed. They retain input hashes and exact candidate sets.
These are diagnostic counterexamples, not a generalisation score or independent writing judgement.

- The previous `realised_degree` treated a strong adjective with `absolutely` or `really` as unknown.
  Modifier-compatible strong forms now remain available. A dropped final letter's apostrophe is treated
  consistently as part of a single word by grammatical form checks.
- A modifier can remain on a compatible target or be expressed by a certified target. `very hungry`
  gains strong appetite choices; `slightly hungry` gains mild `peckish`. The target's certificate must
  cover every shared graded reading. Unknown, stacked/contradictory or negated compositions do not gain
  permission. The source modifier's full span belongs to the replacement, including editor alternatives;
  retention restores its exact source spelling and whitespace. Absorption is restricted to adjective
  predicates; it does not newly enable whole-clause expansions that could discard frequency or aspect.
- Previously, `hungry enough to eat anything` offered both mild `peckish` and strong `starvin'`.
  Threshold-bearing constructions now require the same lexical grade; this sentence remains plain
  because no unmarked single-word hunger target is certified. Lookup may explain unmarked VPs, but
  does not certify them as in-place replacements. `too hungry to sleep` has no canonical detection in
  this probe; this work does not claim to expand its detection.
- Original-aware verification extends its existing exact-local pairing to unmarked relational grades.
  It still abstains on ambiguous pairing, changed surrounding clauses and unknown certificates.

The bounded grammar choice follows the [British Council's intensifier reference](https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/intensifiers):
ordinary versus strong adjectives take different modifiers; enough follows its adjective. The
[BBC strong-adjective lesson](https://downloads.bbc.co.uk/learningenglish/lowerintermediate/unit19/u19_6min_vocab_strong_adjectives.pdf)
also uses the starvation/maximiser construction. These sources support composition, not the stronger
claim that coarse grade certificates establish exact threshold equivalence for every synonym.

## Training spike

The baseline dictionary and unchanged recipe give 12,532 positive, 6,860 wrong-sense and 3,654 opposite pairs over 1,208 entries.
36 entries have multiple concepts (34 with two, two with three). Shared forms such as `stuffed` and
`full as a goog` join genuinely different meanings in a static representation; simply using the first
concept was already tried historically and still failed the girl reference. It is not an adopted fix.

There are three exact unordered positive/negative label conflicts, all for `it pouring down` against
rain forms. The short rain trigger excludes `down` so a longer trigger can own the full phrase, but the
trainer turns that exclusion into a negative even though the longer phrase is a valid rain trigger.
Gloss/description negatives repeat the same mistaken anchor even when not directly positive pairs.
This is a reproducible generation defect, not evidence that it caused any of the three failed references.
The next slice will avoid treating a concept's complete positive trigger as its own wrong sense and
expose contradictions before fitting, rather than globally deleting inconvenient negative labels.

The three rejected-fit misses are different: `girl` is a negative-category check (there is no generic GIRL
concept); SAD has positive `feeling down` triggers but many unrelated down phrases exist; FRIEND has
friend/companion positives but no exact full mate query. We will not add frozen reference queries as
training examples. No causal attribution to a pair subset is established by these observations.

[Sentence Transformers' loss documentation](https://www.sbert.net/docs/package_reference/sentence_transformer/losses.html#multiplenegativesrankingloss)
describes in-batch negatives. The trainer's no-duplicate sampler excludes identical texts, not every
semantically synonymous text. Multiple concepts and same-meaning forms can therefore create competing
training signals; this is a hypothesis requiring a controlled experiment, not permission to relabel
references or change loss/cutoffs. Bundled 1.3.0 stays unchanged. No new fit is claimed here.

## Reproduction

Run `spike.py --out PATH` with the pinned training environment and `NLTK_DATA` pointing to the existing
WordNet 3.0 cache. The script imports this worktree explicitly and writes only the requested JSON file.
No full reference texts or rejected weights are committed. Reports from earlier trials remain immutable.

## Degree slice verification

Focused degree/complement checks pass 132 tests. Golden regeneration changes 13 of 450 settings:
strong appetite wording replaces preserved `very hungry`, strong alcohol predicates can express
`very drunk`, and one long-story setting moves two existing phonetic conjunction choices as the
eligible vocabulary changes. Every changed wording was reviewed; no benchmark label or threshold changes.
Independent design review found and corrected modifier-driven uppercase spill and unsafe clause absorption.
The first full run passed 3,269 tests with two permitted skips and found two stale scripted yarn replies.
Those protocol tests now use the current clean plan as their accepted reply, keeping the 60% phrase-retention
gate unchanged; all 57 harness tests pass. Final integrated verification passed, as recorded below.

## Tooling and figurative-predicate implementation

[The final probe](final.json) binds the final code and dictionary hashes. The degree-only checkpoint above
is deliberately retained as an intermediate snapshot before these data/tooling changes.

The trainer now uses the canonical matcher's exclusion tokens, including immediate `!=` syntax. It no
longer emits `=conference`/`=with` as training words. Sorted parsed alternatives preserve deterministic
order. A complete positive trigger suppresses only its own concept's negative anchor; unrelated negatives
remain. Nonterminal exclusion construction is refused when targets would be generated, with guard-only
and fully held-out concepts left alone. The audit detects reversed/case/whitespace positive-negative
contradictions and negative self-pairs; both fitting stages validate before constructing models.

| Snapshot | Positive | Wrong-sense | Opposite | Exact conflicting pairs |
|---|---:|---:|---:|---:|
| Baseline | 12,532 | 6,860 | 3,654 | 3 |
| Tooling prototype on unchanged baseline data | 12,532 | 6,704 | 3,654 | 0 |
| [Final dictionary audit](training-audit.json) | 12,549 | 6,704 | 3,668 | 0 |

The tooling-only prototype used the baseline dictionary in memory before data edits. Seven rain negatives
were removed by ownership; the remaining reduction follows canonical tokenisation, alternative deduplication
and the existing minimum-length rule applied to actual tokens. New FED_UP triggers also change positive
and opposite generation, including WordNet sources. Those effects are separate from the parser correction;
no model improvement is inferred from these counts. The final audit records exact ordered pair digests,
effective holdout and dictionary/recipe/trainer identity.

The [standalone sampler probe](batch-spike.json), reproduced by [batch_spike.py](batch_spike.py), finds
2,763 off-diagonal logits that are also generated positive pairs across 195 of 198 seed-13 epoch-zero
batches of size 64. At size 256 it finds 10,998 across 53 of 56 batches. This reproduces the configured
no-duplicate sampler independently; it is not a captured historical training schedule. It demonstrates
competing labels under the in-batch-negative objective, not a causal explanation of a particular failed
reference. A controlled alternative-objective experiment is the next model research step; changing the
loss, retraining or adopting weights is not hidden inside this maintenance slice.

[Raw reader scores](failed-queries.json), reproduced by [failed_queries.py](failed_queries.py), distinguish
the three rejected-fit failures. Girl moves WOMAN to first place even below the 0.50 offer cutoff, violating
the existing rank guard. SAD still ranks first for feeling really down, but HAPPY scores 0.501051 and fails
the forbidden-category cutoff. The friend query instead puts a reply-to-thanks meaning first and loses
FRIEND from its leading concepts. These are raw release-reference scores, separate from runtime lookup's
contextual restrictions. Passing one check would not establish overall meaning quality.

For annoyance, existing `{np}` capture, meaning restrictions and form checks now recognise object-bearing
FED_UP sources and prevent literal illness/fatigue mappings. Both lookup backends offer the relevant
standalone idiom. Translation, plans and editor changes retain the original object when no target can
bind it. Literal tired-from and sick-with controls remain available. This precision improvement can leave
source text plain; it does not claim a new argument-preserving FED_UP idiom. Evidence:
[Cambridge, sick (and tired) of](https://dictionary.cambridge.org/dictionary/english/sick-and-tired-of) and
[Cambridge, tired of versus tired from](https://dictionary.cambridge.org/grammar/british-grammar/word-choice-tired-of-or-tired-from).

Focused tooling/parser/figurative checks pass 50 tests; degree/complement/lookup/golden checks pass 192.
Ruff includes an explicit pass over research drivers. Final full-suite, publication and provenance checks
passed, as recorded below. All bundled model assets, recipe cutoffs and frozen required references remain unchanged.

## Final verified checkpoint

[Verification evidence](verification.json) records **3,311 passed and two permitted local-corpus skips**
in 808.01 seconds. Both focused design reviews converged after fixes. Ruff, explicit research Pyflakes,
publication and provenance/licence checks passed. The final added dual-concept regression requires every
shared grade to agree before modifier absorption; the combined focused run passed 114 tests.

[The changes budget](changes-budget.json) passed at every supported setting. The maximum raw supported
ratio was **1.334×**, against **1.5×**; site-default median was **1.10×**, maximum **1.14×**.
Three warm repeats used process CPU time, serially after test/research jobs ended. Larger and Markdown
cases and stress are reported separately, not gated. Background system load was not controlled; these
are budget observations, not a causal speedup or website latency claim. The report binds its executed
driver, raw result and frozen final probe by hash.

The bundled three model assets, recipe, references and canonical 1.3.0 report match baseline byte-for-byte.
No failed weights or new model report were adopted at this feature checkpoint. Its measurements precede
the subsequently authorised dev integration, which has separate verification evidence. No release
promotion is included.

Remaining independent work: a controlled loss-objective experiment against the frozen gates and actual
lookup checks; argument-bearing FED_UP targets; further graded-family calibration and wider clause or
multi-edit ownership. Current missing evidence preserves source text rather than inventing compatibility.
