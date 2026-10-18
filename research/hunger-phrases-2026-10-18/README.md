# Hunger phrases, 18 October 2026

User phrase: **“feeling pretty hungry”**. Baseline: `3b516f3`, after the bounded meaning audit.
Three independent agents generated eight variants each without repository, skills, dictionaries, tools or
other-agent context. [The candidate record](generations.yaml) retains all 24 phrases and their intensity or
origin notes. Generation discovers candidates; it does not attest them.

## Decisions

| Candidate or family | Decision |
|---|---|
| Could go a decent feed; could do with a feed | Keep a familiar clause-rewrite suggestion. Add the composed automatic VP “feel like a decent feed”, which preserves the source verb's tense and aspect. |
| Hanging out for a feed | Keep as a familiar rewrite suggestion. Direct mechanical inflection produced “hangs/hung out”, suggesting waiting or lingering; a writer must use the appropriate progressive construction. |
| Wouldn't say no to some tucker | Add the composed VP “feel like some tucker”. The original modal construction remains a candidate, rather than risking a lost negation or changed tense. |
| Peckish; bloody hungry; absolutely/bloody starving | Already represented by the existing hungry/peckish/starvin' vocabulary and swear controls; no duplicate entries. |
| Eat a horse; eat the arse out of a low-flying duck | Existing horse-and-jockey/duck comparisons already cover the stronger appetite; no duplicate. |
| My guts are growling | Existing hunger imagery already supplies growling-belly comparisons. Do not infer literal stomach noise from ordinary hunger. |
| Stomach thinks throat's been cut | Add a familiar shared-English rewrite template with bound possessives. Preserve tense and avoid claiming literal injury. |
| Guts staging a bloody protest | Add an original rewrite suggestion, requiring permitted exaggeration and the existing swear cap. |
| Butter a beer coaster | Add an original ravenous-hunger rewrite, rather than an attested traditional idiom. |
| Tomato sauce on a thong; call it dinner | Add an original ravenous-hunger rewrite; explicitly identify the Australian footwear sense. |

Two automatic VP entries share the existing `HUNGRY` meaning. Its narrow `feel pretty? hungry ^end`
pattern consumes the complete feeling phrase and declines complements such as “for success”. Existing
predicate hunger substitutions can still misread that metaphor; this pass does not claim to fix them.
The six new images are all rewrite-only suggestions. They cannot be appended automatically, even with
riff probability set to one. Four elaborate images require exaggeration 2; the two understated suggestions
allow exaggeration 0. Existing level, vulgarity, negation, subject and complement controls apply.

Person binding remains bounded: the existing planner does not always bind a subject through progressive
auxiliaries. `I am feeling pretty hungry` converts correctly but currently offers no contextual images;
`She felt pretty hungry` offers the six new rewrites with the correct possessives. Bare fragments also lack
an established person. A writer can discover all six templates with
`aussiefy lookup hungry -l 5 -e troppo --vulgarity dad --limit 20`; the default eight-result limit truncates
the combined existing/new image list, and “bloody” needs vulgarity 1 or higher. Broader subject inference
is separate work; no fallback speaker is invented here.

## Source checks

No source definitions, whole pages or reference texts are copied into the repository. Glosses and decisions
are original wording. Headword evidence supports the composed phrases without attesting each full sentence.

- [Oxford, feed (noun)](https://www.oxfordlearnersdictionaries.com/definition/english/feed_2): informal meal
  sense supports the new composed feed VP; the word is shared English.
- [Collins, tucker](https://www.collinsdictionary.com/us/dictionary/english/tucker): food in Australian usage;
  one dictionary section labels it old-fashioned. That is not evidence of exclusive Australian use or a
  separately attested full “feel like some tucker” idiom.
- [The Murrumbidgee Naturalist, April 2021, p. 8](https://mfn.org.au/files/2021_04%20%23291%20MFN%20newsletter%20v2.pdf):
  primary usage of the hanging-out construction while describing a cockatoo waiting for food. This is
  construction evidence, not a claim about human usage frequency.
- [State Library of South Australia, Oswald letters](https://archival.collections.slsa.sa.gov.au/prg/PRG1626_2_OswaldLetters_Transcript.pdf):
  the indexed 5 November 1915 letter uses the could-go construction with “a good feed”. The selected “decent”
  variant is a composition, rather than a verbatim historical citation.
- [Jonathon Green via ADS-L, 25 August 2003](https://listserv.linguistlist.org/pipermail/ads-l/2003-August/033413.html):
  indexed historical note traces the throat-cut hunger expression to older English sources, contradicting
  an exclusively Australian origin. The browser's direct fetch was unavailable; no full-page retrieval is claimed.
- [Wiktionary, stomach/throat expression](https://en.wiktionary.org/wiki/one%27s_stomach_thinks_one%27s_throat_has_been_cut):
  indexed hunger meaning corroborates the interpretation; direct fetch was unavailable.
- [Nillumbik contemporary-writing anthology, 2022, p. 39](https://www.nillumbik.vic.gov.au/files/assets/public/explore/arts-and-culture/awards-and-prizes/nsc_npcw_catalogue_anthology_2022_digital.pdf):
  indexed primary Australian usage corroborates the existing low-flying-duck comparison. No new duplicate is added.

## Verification

Tests cover the exact fragment, progressive/simple present, past, modal and question forms, complement
exclusions, writer-only imagery, subject/possessive binding, origins, exaggeration, vulgarity and negation.
Final independent design review reports no remaining findings. All **69** hunger/imagery checks pass,
and the broader affected documentation/changes run passed **309** tests before the extra lookup regression.
Complete pre-commit verification passed **2,346 tests with two expected local-corpus skips in 797.30 seconds**.
Ruff, whitespace and generated-publication checks pass. Canonical regeneration leaves translation goldens
and changes fixtures unchanged. See the [review record](../../docs/architecture/reviews/design-review-2026-10-18-hunger-phrases.md).
