# Retelling refinement findings, 2026-10-16

## Round two: fidelity recovered, voice too restrained

Twenty texts were judged blindly by two fresh contexts, independently of the writers, using rubric 3.
All source/anchor hashes are pinned. The round is frozen at `f02aab0`; its
[summary](study-round2/summary.json), source-linked per-case verdicts and reports retain the actual results.

| Criterion, mean out of 5 | Current | Dinkum-3 | Earlier yarn |
|---|---:|---:|---:|
| Meaning | 4.95 | 4.60 | 4.70 |
| Sense | 5.00 | 4.85 | 4.70 |
| Authenticity | 4.75 | 4.75 | 4.50 |
| Register | 2.00 | 4.55 | 4.75 |
| Tone | 5.00 | 4.80 | 4.90 |
| Flow | 4.85 | 4.55 | 4.40 |
| Variety | 5.00 | 4.65 | 4.80 |
| Essence | 5.00 | 5.00 | 5.00 |
| Mean of the eight criteria | 4.57 | 4.72 | 4.72 |

Current never ranked first overall. It lost all 20 paired overall comparisons against Dinkum-3, and lost
19/won one against the earlier yarn. Its register means at levels 2–5 were 2.75/2.43/1.25/1.40. The issue
therefore extends beyond any single text. Judges recorded 17 major and 11 minor current problems, mainly
under-retelling; no current critical problem was reported. One meaning weakness concerns seasonal weather
wording. All 20 deterministic verification checks nevertheless passed.

The writers independently confirmed that they overgeneralised fidelity protections and wrote fairly neutral
conversational English. They underused permitted Australian vocabulary and idiomatic phrasing. Empty garnish
does not forbid paraphrasing existing propositions. Sparse plans also leave much of that work to the writer:
some cases offer one phrase, while Interfold use cases offers none. Mechanical acceptance is not a voice test.

The first round, before this comparison, ended with 19 accepted texts and a blocked FOMC submission. Its
[outcome](study/round-outcome.json) and rejected diagnostics remain. The shared multi-paragraph straight-quote
defect was fixed before round two. Nineteen byte-identical briefs/texts carried forward with new canonical
tool execution; the FOMC writer read the changed brief and revised its draft. All 66 round-two tool calls
replayed, and 480 criterion-evidence fields contained verbatim candidate excerpts.

## Interpretation and evaluation limits

These results support the fidelity of this particular writing sample and expose weak register. They do not
show that composable settings prevent flavour. They do not isolate an engine, model or prompt effect:
current and historical writers differ, there is one report per text, and only two fresh judge contexts.

The original packets gave judges level/vulgarity without the full document, embellishment and markup
contract. Their level-5 description also conflated broad Australian wording with a performed pub yarn.
That limits interpretation under restrictive document settings. Most under-retelling findings concern
eligible body prose and remain substantive. The spelling criticism of a bold list label is valid; the
label is eligible prose, not a protected Markdown heading.

Raw round-two packets, reports and scores remain unchanged. Subsequent protocol 2 includes the effective
contract in anonymous packets and clarifies that level controls eligible vocabulary/cadence, while
embellishment/document settings control performance and added garnish. Scores across these protocols are
not directly comparable. The eight criterion definitions and historical text anchors remain unchanged.

## Controlled third refinement

Review found duplicated infix advice: a generic craft section recommended swear infixes even when the
effective garnish list forbade them. The duplicate is removed; the existing gated section remains. Isolated
guide/yarn tests cover General, Custom, News, Official, explicit infix activation and the clean cap.
This fixes a configuration contradiction without claiming it caused the low register scores.

The writers revisited all 20 texts with the same controls and sources, concentrating the selected
Australian voice in eligible prose while preserving facts, qualifications, quotations, technical terms
and markup. New canonical submissions and fresh independent protocol-two judges test the result.

Round three is frozen at `d11446c`. All 20 outputs were deliberately revised by the continuing original
writer contexts, with aggregate weak-register feedback but no historical candidate text or judge reports.
The generic `writer` field retained by `prepare()` in its frozen manifest describes the original creation
of those contexts; it must not be read as a claim that round three used new writer contexts. Per-case
`writer-origin.json` records carry the precise lineage. All 100 retained tool calls replayed under the
frozen engine. Two new independent judge contexts received the contract-aware anonymous packets.

### Results under evaluation protocol 2

The [round-three summary](study-round3/summary.json) and attributed per-case reports retain all results.
This table compares candidates within protocol 2; it is not a before/after score comparison with round two.

| Criterion, mean out of 5 | Current revision | Dinkum-3 | Earlier yarn |
|---|---:|---:|---:|
| Meaning | 4.95 | 4.05 | 4.25 |
| Sense | 5.00 | 4.60 | 4.65 |
| Authenticity | 4.95 | 4.90 | 4.75 |
| Register | 4.65 | 4.05 | 4.65 |
| Tone | 5.00 | 4.90 | 4.90 |
| Flow | 5.00 | 4.75 | 4.60 |
| Variety | 4.95 | 4.70 | 4.75 |
| Essence | 5.00 | 5.00 | 5.00 |
| Mean of the eight criteria | 4.94 | 4.62 | 4.69 |

Current ranks ahead of Dinkum-3 in all 20 paired overall comparisons. Against earlier yarn it wins 16,
ties two and loses two. Its fractional share of first places is 0.85. All 20 deterministic checks pass;
Santa Fe retains one non-blocking repetition warning for the literal tree-cutting action. Every one of
the 480 criterion-evidence fields contains a verbatim excerpt from its own anonymous candidate.

The judges report no current critical problems, one major and eight minor. The major is Yellowstone's
underweight level-5 body voice; its forecast also narrows precipitation to rain, a minor meaning weakness.
Other remaining findings concern some restrained connecting prose, repeated idioms and one stock-sounding
intensifier. Current register means at levels 2–5 are 5.00/5.00/4.25/4.20. Broad high-level voice therefore
still needs editorial judgement; the strong aggregate is not a claim of perfect fidelity or register.

### What this establishes, and what remains

This sample supports coexistence of strong Australian voice and high fidelity under the composable
controls. It does not isolate an engine improvement: continuing writers revised familiar sources after
feedback, judges and packet context changed, and there is one report per case from two judge contexts.
The unchanged historical anchors receive different ratings under the new context too. Neither the
round-two-to-three score difference nor the anchor ratings establish a causal prompt/model/engine effect.
The live Claude API and website latency remain untested by this study.

No frozen text or report is corrected after judgement. The remaining case weaknesses stay visible for a
future writing/refinement round. A general production judge-context API, held-out sources and repeat judges
are independent next steps; current research packets already carry the effective contract. Repository-doc
flavour density remains an editorial review point, not something these news/official/MDX scores measure.

Validation for the results slice: the full suite exited 0 with **1,846 passed / 2 expected local skips in
396.36s**. Final publication/provenance and independent interpretation review are recorded in the linked
[design review](../../docs/architecture/reviews/design-review-2026-10-16-retelling-results.md).
