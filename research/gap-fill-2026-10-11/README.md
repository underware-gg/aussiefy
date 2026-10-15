# Gap-fill round, 2026-10-11

We found words the engine leaves in plain English, had three subagents independently retell texts full of
those words in Australian vernacular, had a fourth search the web for vernacular and fillers, had three
more verify every candidate, and applied what survived to the dictionary. Everything each step produced is
stored here, so the round can be audited, reproduced or repeated.

## Steps and files

| step | who | output |
|---|---|---|
| 1. Gap inventory | `aussiefy gaps` over the public-domain reference texts, plus a sweep for plain words with no trigger | `corpus_gaps.yaml` (47 words with their sentences), `inventory.yaml` (85 targets: states, people, things, actions, known failures, filler categories), `existing_forms.txt` (dictionary snapshot) |
| 2. Synthetic passages | a subagent, plain neutral English, no slang | `passages/synthetic/*.txt` (13 passages, 6 spoken), `manifest.yaml` (targets per passage; coverage check: 85/85) |
| 3. Blind rephrasings | three subagents, forbidden to read the dictionary: **A** everyday (level 3), **B** broad pub yarn (level 5), **C** dialect coach and skeptic (level 4) | `rephrasings/{A,B,C}/*.txt` (16 passages each: the 13 synthetic plus Goldilocks, the Hare and the Tortoise, Gettysburg), `uses.yaml` (217 annotated gap uses each: A filled 166, B 184, C 172; 52 / 39 / 67 fillers) |
| 4. Web research | a subagent with web search | `web/findings.yaml` (124 terms, 32 fillers), `web/NOTES.md` (searches, sources, rejects, gaps with no Aussie word) |
| 5. Merge | `merge.py` | `merged.yaml`: 1,400 distinct terms; candidates are those used by 2+ agents or web-attested (354, in `verify/candidates.yaml`) |
| 6. Verification | three subagents under one brief (`verify/BRIEF.md`): content in two slices, fillers plus an audit of existing entries | `verify/verdicts-*.yaml`, `verify/audit.yaml` |
| 7. Apply | `aussiefy dev round` (then `apply.py`, now retired; configured by `round.yaml`), `apply_audit.py`, plus hand fixes | `aussiefy/data/entries/gapfill.yaml`, `concepts.yaml` (new section and appended triggers), corrected existing entries |

## Verification outcome

Of 354 candidates: 119 accepted, 32 gated, 28 merged into existing forms, 8 became triggers only, 28 became
style-guide guidance, and 147 were rejected. The rejections were 75 not Australian (British or general
English), 58 one-off phrasings rather than reusable expressions, 7 wrong sense, 5 duplicates and 2
unattested.

The wrong-sense calls are the useful ones:
- *sheila* means a woman, not a girl;
- *stickybeak* is a nosy person, not a gossip;
- a *furphy* is a false rumour, not a lie;
- *going troppo* is going mad, not bored;
- *a bit rich* is hypocritical, not expensive;
- *deadly* is praise, not boring;
- *up with the sparrows* is early, not wide awake.

## What was applied

- **138 entries** (37 gated) in `entries/gapfill.yaml`, under **72 new concepts** and existing ones. The
  new concepts cover:
  - people: WIFE, HUSBAND, PARENTS;
  - money: EXPENSIVE, LOT_OF_MONEY, POOR;
  - states: NERVOUS, BORED, UNLUCKY, ARROGANT, SUSPICIOUS, ATTRACTIVE;
  - things: CIGARETTE, DINNER, PARTY;
  - talk: DONT_KNOW, WAIT, WELL_DONE.
- **48 plain-English triggers on 13 existing concepts:** irate and enraged → ANGRY; weary and fatigued →
  TIRED; destitute → BROKE; petrified → SCARED; despondent → SAD; elated → HAPPY; inebriated → DRUNK;
  an argument → FIGHT; and others.
- **New fillers:** openers *look*, *listen*, *far out*; tag *ya know*; connective *mind you*; aside
  *dunno.*; tail *and stuff*; opinion closers *that's my two bob's worth.* and *what d'ya reckon?*. Also
  *I dunno*, *hang on*, *good on ya*, *fair call*, *you're dreamin'*, *how good is that?* and *bugger*
  (for "damn").
- **Australian discourse habits,** in the yarn-mode craft guide (`harness.CRAFT`): understatement with
  "a bit", hedging with "reckon", vague tails, clipped "ADJ as", dropped "to" ("down the beach"), "will
  ya?", quotative "goes", "yeah, nah" and "nah, yeah", and sentence-final "but".
- **Corrections to ten existing entries** from the audit. For example: *pissed* is vulgarity 2 and means
  drunk, never angry; *full as a goog* is dated; *rapt* and *stoked* are predicative only; *sook* is a
  crybaby rather than a complainer.
- **An engine fix the fillers verifier found:** closers ignored their `when` contexts, because the engine
  passed none. A closer now sees the last sentence's context. Existing closers are unaffected, since their
  default is "any".

## Guards and hand review

`aussiefy dev round` regenerates the whole change from the verdicts. These guards apply to triggers and to entries'
`replaces` lists:
- slang is never a trigger (it would swap slang for slang);
- nothing may copy a `training/reference.yaml` query word for word (that would teach to the test: "a
  heap of money" was proposed three times and dropped each time);
- duplicates are skipped;
- every low-confidence accept ships **gated**, so a guess never fires by default.

The hand review is recorded:
- **`concept_aliases.yaml`:** concepts the verifiers named twice (DAWN → EARLY, GOOD_LOOKER →
  ATTRACTIVE, …).
- **`trigger_fixes.yaml`:** triggers that would fire in the wrong sense (*lie* in "lie down", *hot* for
  ATTRACTIVE, *a second* in "a second chance", *not really*), and intensities for the strong and weak
  words.
- **`entry_fixes.yaml`:** `replaces` lists with the same problem (*spunky* had "hot", which turned "the
  porridge was too hot" into "the porridge was spunky"; *perv on* had "check out"), plus four fillers gated
  because the engine can't check what they need. Sentence-final *but* needs a contrast. *yeah, no* signals
  disagreement. *legend* is praise. *hey* has no Australian-specific source.

The golden outputs were regenerated and every changed line was reviewed (34 lines). The changes are re-rolls
among genuine slang (*stuffed* → *zonked*, *went off like a frog in a sock* → *did his block*, *flat chat*
→ *flat out*) and new openers.

## What we learned about the method

The accept rates below are the verifiers' verdicts. Those are LLM judgements, made against search summaries,
so they are not ground truth, but they are consistent across slices.

| where a candidate came from | verified as useful (accepted, gated, merged or trigger) |
|---|---|
| web research alone | 69/76 (91%) |
| web research + one or more rephrasers | 40/44 (91%) |
| two rephrasers agreeing, no web | 52/170 (31%) |
| all three rephrasers agreeing, no web | 21/64 (33%) |

- **Rephrasers generate; research and verification give precision.** Agreement between blind rephrasers
  is a weak signal on its own: three agreeing did no better than two. They converge on general informal
  English (*knackered*, *chuffed*, *gutted*: British or general, so rejected as not Aussie-specific) and on
  one-off phrasings. 58 rejections were for not being reusable expressions at all.
- **Rephrasers still pay for themselves.** They surfaced the vocabulary in context, so a verifier could judge
  sense as well as existence. They produced most of the filler and discourse material, which web research
  finds hardest. And they showed which "gaps" aren't gaps (chair, bowl, porridge: all three kept them plain).
- **The skeptic persona earned its place.** Agent C was the one asked to flag dated, regional and
  wrong-sense terms. It contributed the most accepted terms (75, against 43 and 45), and its notes drove the
  wrong-sense rejections and the audit of existing entries.
- **Ask for annotations, not just text.** The structured `uses.yaml` (gap, plain words, Aussie form, sense,
  confidence) made the merge mechanical. Free-text rephrasings alone would have needed another extraction
  pass.
- **The verification step found an engine bug** (closers ignored their context) and sense hazards in our own
  data, beyond the candidates themselves.
- **Most of the damage risk sat in the plumbing, not the terms.** Triggers and `replaces` lists that fire in
  the wrong sense ("the porridge was too hot" became "spunky") came from correct terms with over-broad match
  patterns. The golden outputs and a hand review of every pattern caught them; per-term verification did
  not.
- **Next time:**
  - send rephraser-only candidates to verification only when they also have a web hit, or budget for
    the 2:1 reject rate;
  - let the web researcher open pages (the network policy blocked it here);
  - have verifiers propose triggers as narrow phrases, never bare common words.

## Limitations

- **Evidence quality.** The network policy blocked page fetches, so the web researcher and verifiers judged
  sources by the search tool's summaries, and entries say so (`seen_via: search_summary`). Several terms
  rest on agent agreement plus the verifier's judgement (`evidence: agents_only`); those at low
  confidence are gated.
- **Gaps with no Aussie word.** Many story nouns (chair, bowl, door, porridge, bear, house, beach) and
  solemn words (government, proposition, forget) have no genuine vernacular alternative. Australians just
  say them, and the dictionary rightly leaves them plain.
- **A stale model.** The bundled embedding model (1.1.0) was trained on the old dictionary; see
  `training/README.md` for the retrain this round triggered.

## Repeating the round

1. Run `aussiefy gaps` on new texts.
2. Update `inventory.yaml`.
3. Re-run the subagent prompts. They are kept in this README's steps and in `verify/BRIEF.md`; give the
   rephrasers the same blindness rule.
4. Run `python3 merge.py`.
5. Run the verifiers.
6. Run `aussiefy dev round research/gap-fill-2026-10-11`, which is a dry run listing what it would drop
   and why. Review it, add fixes to the YAML files here, then run it with `--write`. (Re-running this
   round now needs the later classics round set aside too, since classics entries use gap-fill concepts.)
7. Regenerate and review the goldens.
8. Release a new model version.
