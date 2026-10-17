# Design review: contextual imagery, 17 October 2026

Surface: contextual image schema/data, shared grammar and selection, engine insertion and riff state,
advanced configuration, toolkit/CLI/MCP/session adapters, follow-up curation, documentation and regressions.
One independent reviewer assessed all six software-design concerns using the principles and calibration
references. The review included concrete runtime probes and the golden diff.

## Findings

No remaining findings after correction. The reviewer verified the following resolved medium-priority,
high-confidence issues through live probes:

- Parenthetical commas no longer hide preceding negation from contextual eligibility.
- Explicit complement exclusions reject figurative hungry-for/to meanings, including intervening punctuation.
- Contextual insertion rejects dash, slash and opening-bracket continuations. Legacy punctuation behaviour
  remains unchanged; the stricter check applies at the contextual insertion boundary.
- Bare breathless no longer establishes physical breathlessness. Only precise direct triggers authorize
  breathing comparisons; ordinary tiredness offers conditional writer associations.
- Person eligibility recognises verb-phrase actor captures, so past-tense futile work can take its image.
  The starting-gun imperative is available as a writer suggestion without requiring a captured person.
- Slot regression fixtures now use actual token captures, matching the production detection contract.

Earlier conceptual review constraints were also implemented: free-text usage is not executable proof of
fit; writer-only forms cannot insert automatically; stricter slot checks prevent invented possessives;
contextual images share existing budgets, spacing and document state; and image garnish never fabricates
an entry-backed vocabulary substitution.

A proposed loader-root finding was withdrawn after tracing `_read_optional` to `_read`, which already owns
root-type validation and treats null as empty. Regression probes cover that boundary without duplicate guards.
The full-suite benchmark finding was also resolved after independent review of its premise: adding the
ordinary word “breath” to dictionary prose changed dynamic recall from 15/25 to 14/24 while all ten
Gettysburg outputs remained byte-identical. Freeze the established 25 word-anchor sets as historical
target-wording coverage, retain the same ten seeds, matching and 60% threshold, and validate fixture hashes
and span membership. Do not call these independently curated slang labels or alter the general harvest API. The contributor
testing guide now describes this contract; its public wording was adjusted to preserve the evidence meaning
when the existing establish-to-kick-off rule took the wrong sense.

Final verification passed before committing: **1,981 tests passed with two expected local-corpus skips**
in 476.99 seconds. Ruff, whitespace, generated-publication and wheel/provenance checks passed. The research
follow-up report records these results and the Python 3.10 smoke check.

## What's done well

- A pure core module serves engine, plans and lookup using existing dictionary and grammar machinery, with
  no model/network dependency or speculative indexing layer for a small image library.
- Direct suffixes and conditional writer suggestions have explicit forms and semantic boundaries. Curated
  related associations widen writer choice without asserting missing facts.
- Configurable defaults work through the existing exact override mechanism for every document type.
  Custom remains explicit. Insertion probabilities/counts remain distinct from suggestion eligibility.
- Shared seeded selection and riff state preserve density limits across both image sources and Markdown.
- Garnish records identify images directly; unbound lookup templates disclose their limitations.
- All tool surfaces propagate controls and session lookup inherits the writing contract.
- The follow-up ledger covers all 163 earlier unadded/rejected rows without rewriting frozen evidence.
- Golden changes reflect expanded word pools and consequent seeded choices. They were read as output,
  rather than accepted simply because regeneration passed.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| Existing malformed question realisation, including “can I wouldn't know…” | Improve grammatical fidelity | Present in the baseline reference output; not introduced here |
| Existing “turning and chucking” in Hansel's restless sleep | Correct a wrong-sense turn/toss swap | Present in the baseline and outside the new precise restless-sleep trigger |
| Existing object-taking QUIT substitutions, such as “chuck it in smoking” | Preserve the complement when quitting a habit | A final parent probe confirmed the unchanged legacy QUIT/chuck-it-in path; the new command-only entry is excluded from this case |
| Existing establish-as-proof versus establish-as-found sense | Avoid “kick off semantic fidelity” in generated prose | The source wording is fixed here; general sense disambiguation remains independent vocabulary work |
| Independently curated slang benchmark | Measure genuine slang reproduction rather than historical wording | Requires separate labels and a fresh baseline; the fixed historical gate remains coherent |
