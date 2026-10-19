# Explain mode

`--explain` prints a report of every decision the engine made, on stderr, after the translation on stdout.
The same records are in `result.to_dict()["explain"]` and in `--json` output.

For every detected span it records:

- the span and the concept found
- how it was detected (trigger, entry paraphrase, or similarity score)
- the frame, the intensity and the captured slots
- the roll and the probability
- the chosen entry and its weight breakdown
- the other candidates with their probabilities
- every rejected entry with its reason (`--brief` leaves these out)

Garnish and phonetic edits are logged too. For example:

```
$ aussiefy "Are you crazy?" -l 4 -s 0 --explain
Crikey, do you have a kangaroo loose in your top paddock?

level 4, seed 0, mood light
document type general -> general (); embellishment dinkum: garnish connective, infix, insult, opener, riff, tag, tail
document behaviours: {"check_length": true, "command_context": false, "contextual_riffs": true, "dateline_context": false, "draft": true, "entry_riffs": true, "formal_to_rework": true, "garnish": ["connective", "infix", "insult", "opener", "riff", "tag", "tail"], "keep_quotes": false, "keep_share": 0.6, "max_length": 1.6, "openings": true, "perform": false, "person_swears": true, "riff_association": 0, "riff_exaggeration": 1, "term_domains": []}
profile settings: {"frames": ["np", "adj", "adv", "interjection", "imperative", "predicate_adj", "vp", "clause"], "garnish": {"aside": 0.0, "closer": 0.0, "connective": 0.2, "opener": 0.2, "riff": 0.0, "tag": 0.3, "tail": 0.3}, "garnish_gap": 1, "garnish_per_sentence": 1, "max_garnish": {"aside": 99, "closer": 0, "connective": 99, "opener": 1, "riff": 1, "tag": 2, "tail": 1}, "phonetic": 0.5, "rewrite": {"formal_length": 7, "max_coverage": 0.1, "min_formal_words": 2, "min_level": 3, "min_words": 6}, "stack": 0.0, "stretch": [3, 5], "substitution": {"idiom": 0.9, "lexical": 0.85, "phrase": 0.85}, "swearing": {"closer": 0.12, "exclaim": 0.06, "infix": 0.5, "lean": 1.0}}

substitutions:
  [8:13] "crazy" -> "Do you have a kangaroo loose in your top paddock"
      concept CRAZY, frame predicate_adj, intensity 3, via trigger "crazy"; captures subj=you, be=Are
      substituted: roll 0.585 < p 0.9
      chosen roos-top-paddock (p=0.10): w=0.450 (base 1 x intensity-fit 0.50 [4 vs 3] x direct 1 x sources 1.0 x repeat 1.00 x p(idiom) 0.9 x tone-fit 1 (plain/light))
      other candidates: mad-as-a-cut-snake 0.11, mad-as-a-meat-axe 0.11, off-rocker 0.19, off-tree 0.10, snags-short-of-a-barbie 0.19, troppo 0.20
      rejected:
        - mad-as-a-gumtree: needs level 5

garnish:
  opener sentence 0: "crikey" (g-crikey); roll 0.044 < p 0.2
```

The weight factors are described in [the pipeline](../architecture/pipeline.md), step 3. With `--rewrite`,
explain mode also shows which sentences were rewritten and why.
