# Existing slang: sixth research allocation, 120 entries

This is **research only**: the exact 120 IDs in `/private/tmp/aussiefy-audit-wave2-2.json`, checked on
19 October 2026. The assigned Git baseline is `2687d7f`; the [ledger](audit.yaml) identifies the actual
working-file snapshot, including concurrent parent semantic changes. All IDs belong to the original
`5d1fb04` inventory and exclude the preceding 460 reviewed IDs and the parallel batch 5 allocation.
No package, runtime provenance, flag, theme or policy changes were made.

| Assessment | Entries |
|---|---:|
| Selected lexical sense supported | 88 |
| Mapping, construction or degree recommendation | 11 |
| Supported range, tone or contextual boundary | 20 |
| Stronger evidence still needed for selected reading | 1 |

[sources-proposed.yaml](sources-proposed.yaml) contains **119 per-entry source candidates**, unapplied.
The provisional `cut-upset` record retains its community evidence and existing gate; no claim of invention
or falsity follows from weaker sources or failed searches.

The preceding 460 plus this batch cover **580 of the original 1,254**, leaving **674** before counting
parallel batch 5. Reconcile both allocations independently before reporting their combined coverage.
Working-tree additions outside the original baseline do not inflate these coverage totals.

## Recommendations

Nine recommendations concern active records; two concern already gated records. These are source and
construction findings, not a claim that every trigger universally fails. The ledger also records successful
protections and actual diagnostic probes.

| Entry | Distinction to preserve | Suggested integration |
|---|---|---|
| `a-bitzer` | A mixed-breed dog versus a crossbred animal of unspecified species. | Resolve the animal referent before choosing the canine sense; preserve other assembled-object uses separately. |
| `a-goss` | Interpersonal gossip versus an unrelated newest item; noun phrase versus verb phrase. | Preserve the existing phrase-tail guard, resolve bare `the latest` context, and keep `have a goss` out of an object noun phrase. |
| `biffo` | Fighting/aggressive behaviour versus a disagreement explicitly lacking aggression. | Preserve physical and figurative aggression uses without requiring all disputes to be fights. |
| `a-counter-lunch` | Pub lunch versus pub dinner. | Choose the existing `counter meal` variant for dinner; the whole record need not be rejected. |
| `a-bush-doof` | An outdoor electronic-dance event versus any dance party. | Respect explicit indoor or incompatible event context; literal wilderness is not compulsory. |
| `a-bit-full` | Mild intoxication versus an explicit severe degree. | Retain the euphemism while preserving source severity where required. |
| `piss-up` | A drinking occasion versus other kinds of binge. | Resolve the binge activity; preserve non-alcohol contexts. |
| `southerly-buster` | A particular abrupt southerly change versus any cold front or cool change. | Preserve direction and event identity without imposing one research study's numerical criteria on all colloquial uses. |
| `bend-ear` | The listener's ear versus the speaking agent's ear. | Bind the actual listener, preserve explicit listener captures, and correct irregular `bend`/`bent` through shared morphology. |
| `pull-the-other-one` — gated | Disbelief versus a sincere request for confirmation. | Retain sceptical use; do not turn every `really`/`is that true` into refusal to believe. |
| `cost-a-bucketload` — gated | A cost verb construction versus an expensive predicate adjective. | Supply compatible grammar and the charged-person role when required. This is already blocked by frame checks. |

Source anchors include [Oxford's bitzer senses](https://www.oxfordlearnersdictionaries.com/definition/english/bitzer),
[Collins's outdoor doof definition](https://www.collinsdictionary.com/dictionary/english/doof),
[GPSA's counter-lunch guide](https://gpsupervisorsaustralia.org.au/communication-toolbox/assets/docs/t4/R4.17-Australian-Slang-Dictionary.pdf),
[Cambridge's listener-directed idiom](https://dictionary.cambridge.org/dictionary/english/bend-ear),
and [the Bureau's explanation of southerly busters](https://media.bom.gov.au/social/blog/18/the-big-bust-southerly-busters-explained/).

## Observed examples and existing protections

Read-only probes used `Translator(lookup_embedder=None)`, level 5, vulgarity 3, `embellishment='deadset'`,
`embedder='none'`, `unlock=['all']`, and registers `current`, `dated`, `archaic`. These explicit diagnostic
settings are not proposed defaults. Complete settings, sources, seeds and observations are in the ledger.

| Entry | Seed | Source | Observed output |
|---|---:|---|---|
| `a-bitzer` | 0 | We bred a crossbreed of two cattle. | We bred a bitser of two cattle. |
| `a-goss` | 3 | I heard the latest gossip. | I heard the have a goss. |
| `a-goss` | 0 | We are testing the latest. | We're testing a goss. |
| `biffo` | 0 | It was an argument, with no aggression. | It was a bit of biffo, with no aggression. |
| `a-counter-lunch` | 1 | We booked a pub dinner for eight. | We booked a counter lunch for eight. |
| `a-bush-doof` | 0 | We attended a dance party inside a hotel ballroom. | We attended a bush doof inside a hotel ballroom. |
| `a-bit-full` | 5 | He was legless. | He was a bit full. |
| `piss-up` | 0 | It was a binge of science documentaries. | It was a piss-up of science docos. |
| `southerly-buster` | 0 | A cold front crossed the American plains. | A southerly buster crossed the American plains. |
| `bend-ear` | 3 | She rambled about the trip. | She bended her ear about the trip. |

Protections are important to the diagnosis. `The latest software` already rejects the gossip candidate
because the noun phrase continues. The same pub-dinner example correctly chooses `counter meal` at seed 0.
`Talked his ear off` captures the actual listener's possessive, while bare `rambled` supplies only the
speaking agent. `Cost-a-bucketload` and `shame-job` are rejected for incompatible frames, even under explicit
unlock. A calm-argument wording with an intervening modifier did not produce the same detection as the
explicit non-aggression example above. These are bounded observations, not exhaustive guarantees.

The strongest examples identify explicit conflicts in referent, activity, setting, meal time or degree.
They do not establish that every ambiguous use must be rejected, or prohibit intentional imagery under an
authorised embellishment policy. Prefer dictionary sense distinctions plus shared semantic context and
form compatibility over engine branches keyed to individual slang strings.

## Meaning ranges and evidence calibration

- **Keep broader supported senses.** Willy-willy is not restricted by every edited source to one small
  dust-devil subtype. Shout can extend beyond drinks. Stonkered has fatigue and drunkenness uses, supported
  here by an edited fatigue definition and an independent Australian news usage in an alcohol context.
- **Avoid invented time restrictions.** Little Lunch is morning snack time in ACTF material, while
  [Kenthurst Public School's timetable](https://kenthurst-p.schools.nsw.gov.au/school-life/bell-times) uses
  the same name for an afternoon break. Preserve this actual variation rather than insisting on morning.
- **Tone and discourse are contextual.** Look can be forceful; repeated nah need not always be friendly.
  Final but carries contrast and turn-taking functions, rather than being empty decoration. The yeah-no
  literature also records multiple discourse functions. These notes preserve the vocabulary and current
  gates while exposing the contextual signals useful to the semantic engine.
- **A component is not automatically a fixed whole phrase.** Tick plus hang-on, pearler plus of-a-day,
  opinion-valued two-bob's-worth in a closing sentence, and several approval responses have explicit scopes.
  Direct source checks did find complete `tell porkies` and `perv on` examples; they are not left with an
  artificial exact-phrase evidence gap.
- **Historical evidence stays historical.** Downing's molo and the state-school intoxication simile support
  the selected meanings without proving present-day frequency. Original compilations, their reproductions
  and their mirrors are not independent witnesses. The Thorne reproduction's full PDF exceeded the tool's
  size limit; the actual indexed headword and title/author/edition passages were read.
- **Indirect and community sources are labelled.** Shitty's bad-mood sense is recorded through a scholarly
  appendix reproducing dictionary data, not a separately inspected Green/New Partridge edition. Word Map
  and Wiktionary evidence remain distinguishable from edited dictionaries and primary speech. The bare
  emotional `cut` has a dated community contribution, but stronger contextual evidence remains outstanding;
  the different `cut up` expression is not substituted as exact evidence.
- **Australian use and origin are different questions.** Edited references sometimes label shared words
  UK, New Zealand or Canadian. Those labels alone do not disprove Australian use or justify omission.
  Specific Australian sources complement general meaning evidence where available; this is not a uniform
  contemporary-Australian-frequency certification of all 120 records.

## Verification and integration

Validation checks the exact manifest, original membership, disjointness from previous ledgers and batch 5,
assessment counts, source references, proposed-URL integrity and snapshot digests. Both YAML safe loaders
read the research files identically. This pass does not claim a runtime full-suite run or a commit.

Notes and analysis are original. No dictionary definitions, acquired quotation collections or modern
articles are copied into this folder. Public pages and indexed passages were manually consulted; access
limitations and the actual evidence scope are recorded. This review does not claim that every linked book,
research paper or historical volume was read cover to cover.

The parent task owns independent review, integration, runtime provenance, index changes, tests and commits.
The other agent's theme/metadata design is outside this research allocation.
