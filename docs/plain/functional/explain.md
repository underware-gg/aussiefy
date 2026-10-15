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
genre story (story 1, personal 0.08, technical 0, instructions 0, news 0, official 0); embellishment troppo: garnish aside, closer, connective, infix, insult, opener, riff, tag, tail

substitutions:
  [8:13] "crazy" -> "Do you have a kangaroo loose in your top paddock"
      concept CRAZY, frame predicate_adj, intensity 3, via trigger "crazy"; captures subj=you, be=Are
      substituted: roll 0.585 < p 0.9
      chosen roos-top-paddock (p=0.10): w=0.450 (base 1 x intensity-fit 0.50 [4 vs 3] x direct 1 x sources 1.0 x repeat 1.00 x p(idiom) 0.9)
      other candidates: mad-as-a-cut-snake 0.10, mad-as-a-meat-axe 0.10, off-rocker 0.20, off-tree 0.10, snags-short-of-a-barbie 0.20, troppo 0.19
      rejected:
        - mad-as-a-gumtree: needs level 5

garnish:
  opener sentence 0: "crikey" (g-crikey); roll 0.044 < p 0.2
```

The weight factors are described in [the pipeline](../architecture/pipeline.md), step 3. With `--rewrite`,
explain mode also shows which sentences were rewritten and why.
