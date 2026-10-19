# Existing slang: second source and meaning pass, 19 October 2026

This continues [the first pass](../slang-meanings-2026-10-18/README.md), against
`ee46955aefb1a2181ca80e64f78e7f71d8209e10`. The [ledger](audit.yaml) records **30 previously
unaudited baseline entries**, selected for ambiguous meanings, dropped context and constructional risk.
The current dictionary contains 1,257 entries; the original audit inventory contained 1,254. None of the
three additions after that inventory is counted in this batch.

| Decision | Entries |
|---|---:|
| Selected sense supported | 21 |
| Trigger fit or gloss needs correction | 7 |
| More evidence or a product decision needed | 2 |

Together the two passes cover **160 distinct entries in the original 1,254-entry inventory**, leaving
**1,094 baseline entries outside the reviewed set**. These figures describe review coverage, not the
number of entries independently certified against every sense, trigger, register or inflection.

## Findings to integrate

These are recommendations, not applied changes. All expressions should be preserved; changing an unsafe
automatic mapping is different from declaring the expression inauthentic.

| Entry | Problem in the current mapping | Proposed correction |
|---|---|---|
| `kick-off` | `FOUND` includes assembling objects and bringing things into existence. | Use a specific activity-starting concept. |
| `knock-together` | Broad `FOUND` includes creation without assembly; neutral construction may also acquire haste/roughness. | Remove `FOUND`; retain rough assembly, review neutral assembly separately. |
| `mateship` | `DEVOTION` includes devotion and loyalty with no peer relationship. | Use comradeship or explicitly qualified solidarity between peers. |
| `poor-buggers` | Generic deceased people become a sympathetic reference that no longer states death. | Use pity-bearing contexts or keep it as a writer option. |
| `brave-bastards` | Any soldier gains courage and loses the explicit military role. | Require explicit courage/context or retain as a writer option. |
| `for-sweet-bugger-all` | Bare `for no reason` can mean causeless action rather than an unproductive result. | Preserve the attested non-monetary wasted-result reading; review ambiguous causeless contexts. |
| `a-sleep-out` | An enclosed porch need not be used for sleeping. | Require sleeping use; correct the gloss's enclosure assumption. |

The evidence and precise limits are recorded per entry. Starting and assembling are distinguished in
[Cambridge's kick-off entry](https://dictionary.cambridge.org/dictionary/english/kick-off) and
[Oxford's knock-together entry](https://www.oxfordlearnersdictionaries.com/us/definition/english/knock-together).
The relationship boundary is discussed in [Macquarie's mateship article](https://www.macquariedictionary.com.au/mateship-and-friendship/).
The accommodation boundary is supported by [ANDC's sleepout entry](https://history.cass.anu.edu.au/centres/andc/australian-words-s).

Existing controls should express these distinctions in dictionary data. Avoid scattered engine checks for
individual words. A neutral phrase gaining a little comic intensity can be legitimate embellishment;
losing an occupation, death, object or causal distinction requires a clearer rule. The exact construction
`for sweet bugger all` is used for an unproductive outing in [Peter Temple's *Black Tide*, quoted by Green's](https://greensdictofslang.com/search/quotation?biblid=9250).
That evidence supports non-monetary wasted results: neither a payment-only restriction nor blanket rejection
of `in vain` or `to no avail` is justified. The seven recommendations include this narrower ambiguity
review; they do not declare the demonstrated sense incorrect. Whether loose
paraphrases remain available automatically at strong embellishment is a product decision, not something
source absence alone settles.

## Retained and provisional cases

- `mob`: primary [AIATSIS interview usage](https://aiatsis.gov.au/whats-new/podcasts/understanding-native-title)
  supports group identity in a particular context. It does not establish every bare `tribe` occurrence as
  that context, nor disprove broader Australian uses. Keep the term and shape the automatic trigger rule.
- `snags-short-of-a-barbie`: the exact form has a secondary record, while
  [Macquarie](https://www.macquariedictionary.com.au/are-you-a-couple-of-lamingtons-short-of-a-cwa-meeting/)
  directly documents the related bangers/barbie construction. Preserve `STUPID` use; retrieve the cited
  Green's/Hansard evidence before treating the exact history or every `CRAZY` trigger as verified.
- `stir-the-possum`: current provocative use is supported. A later bounded extension could capture debate
  or enlivening discussion; this is a missing-use opportunity, not an urgent mapping defect.
- `pull-your-head-in`: the non-interference/rebuke use is supported, with a documented quieting sense too.
- `sledge`, `old-mate` and `not-the-full-quid`: small gloss clarifications would communicate their selected
  senses more accurately without removing the entries.
- `swear-blind`: actual assertion triggers fit, despite its misleading `RESOLVE` concept identifier. Inspect
  behaviour before renaming or remapping a concept merely because its name looks wrong.

## Integration and verification

[sources-proposed.yaml](sources-proposed.yaml) contains **28 proposed per-entry source additions**. The
two provisional entries are deliberately excluded. A source may attest a headword or components rather
than a complete expression; the ledger states that distinction. Adding URLs changes candidate source
weights and public cards, so applying this file requires fixture regeneration and review.

Useful regressions when applying the seven corrections:

- Physical chair assembly and literal childbirth must not become an activity kicking off.
- Explicitly cobbled assembly should retain rough-construction options; neutral creation should retain
  its intended operation.
- Religious devotion and brand loyalty must not imply comradeship.
- References to the dead must keep their death meaning; an unspecified soldier must keep their role and
  must not acquire asserted courage.
- Preserve appropriate wasted-result uses of `for sweet bugger all`. Distinguish those from unexplained
  causes in ambiguous `for no reason` contexts, including under negation.
- A porch used for meals must not become sleeping accommodation; a sleeping porch should still match.

The parent task owns implementation, design review, provenance declarations, generated documentation,
fixture review and full checks. This research-only batch does not claim those changes or checks are done.

## Method and limits

Sources were manually inspected through the browser and search index. Some publishers returned HTTP 403
on direct fetch; those access limits are recorded rather than presented as full-page review. No dictionary
was bulk scraped. No source definitions, examples, full texts or historical quotation collections are
redistributed. Notes are original analysis of the repository's mappings. Two pages from one publisher do
not count as independent publishers. A missing sense is not disproved merely because a selected source
omits it. Several expressions are shared English used in Australia; no exclusive Australian origin is
claimed.
