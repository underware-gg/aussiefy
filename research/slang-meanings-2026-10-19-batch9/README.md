# Slang meaning audit — 19 October 2026, batch 9

Research and source proposals only. This folder changes no dictionary records, runtime, flags, rarity, documentation index or release notes.

The exact assigned manifest is `/private/tmp/aussiefy-audit-batch9.json`; its SHA-256 and every source-file snapshot hash are retained in `audit.yaml`. The snapshot was taken at `11aa20c3e6b194bb2de014c314e3f10a8a7783aa` while the parent continued semantic refinements. Current runtime/data may already differ. Per-entry before records and probes explicitly describe their captured state, not the parent's eventual implementation.

## Scope and result

All **120 assigned original-baseline IDs** were examined against their selected concepts, forms, usage notes and trigger snapshots:

| Result | Entries |
| --- | ---: |
| Selected sense supported | 38 |
| Supported range, context or evidence limitations | 73 |
| Precise mapping/note correction recommended | 9 |
| No responsible selected-sense support located | 0 |
| Total | 120 |

There are **126 source records** and **120 proposed source-sidecar associations**. Proposals are candidates, not automatic runtime edits or a claim that each source certifies every gloss/note/trigger. The totals come from the machine-readable ledger, with each of the 120 decisions accounted once.

The original inventory contains **1,254 IDs** at `5d1fb04`. The preceding ledgers cover **940 distinct original IDs**; this batch brings coverage to **1,060**, leaving **194** before the disjoint parallel batch 10 and final batch. This is original-inventory accounting, not the size of the current expanded dictionary.

## Nine recommendations

| Entry | Evidence and precise recommendation |
| --- | --- |
| `cactus` | Preserve ruined/broken meaning. The cited [Macquarie article](https://www.macquariedictionary.com.au/were-totally-cactus/) speculates that **onkus** is dying out, in its own paragraph. Remove the current attribution of that speculation to cactus. The adjacent clapped-out fatigue paragraph is not cactus evidence either. |
| `pissed` | Preserve drunk meaning and the existing exclusion of bare ambiguous input from DRUNK. Replace **never angry in Australia** with qualified wording: the [collaborative range reference](https://en.wiktionary.org/wiki/pissed) explicitly reports spread of the angry sense to Australia. This is evidence against an absolute geographical prohibition, not a representative Australian usage survey. |
| `loony-bin` | Preserve psychiatric-hospital sense; disambiguate bare asylum from refugee protection. Edited [asylum](https://www.collinsdictionary.com/dictionary/english/asylum) has both kinds of meaning. The refugee probe is a sense and noun-grammar defect, not a new offensiveness-policy recommendation. |
| `lounge-room` | Preserve domestic living-room meaning. Edited [den](https://www.collinsdictionary.com/dictionary/english/den) also names an animal lair; the bare trigger converts a fox's den into a lounge room. Distinguish the two senses. |
| `bin-chicken` | The [Australian Museum](https://australian.museum/learn/animals/birds/australian-white-ibis/) names Australian white ibis as bin chicken; [ABSA](https://absa.asn.au/wp-content/uploads/2022/01/Glossy-Ibis-BIH2-NZ.pdf) identifies glossy ibis as a different species. Protect explicitly different species names; do not declare every ambiguous local ibis reference invalid. |
| `wheelie-bin` | Edited [wheelie bin](https://www.collinsdictionary.com/dictionary/english/wheelie-bin) has wheels. Generic rubbish bins need not. Preserve an explicitly unwheeled bin rather than adding a contradicted subtype; retain valid ordinary wheeled-bin use. |
| `footpath` | Preserve sidewalk/pedestrian sense. Edited [pavement](https://www.collinsdictionary.com/dictionary/english/pavement) also means a paved surface/thoroughfare. Preserve explicitly nonpedestrian road/runway contexts. |
| `grog` | Alcoholic drink is supported; not every chemical alcohol is a beverage. Coordinate the parent's ALCOHOL narrowing already in flight, demonstrated here with explicitly isopropyl laboratory alcohol. This is not a proposal to remove grog. |
| `aerial` | Electronics aerial differs from [biological antennae](https://www.collinsdictionary.com/dictionary/english/antenna). The ant probe crosses sense and number. Require the electronics meaning and separately verify plural preservation for genuine radio/TV antenna inputs. |

## Observed examples

Read-only `Translator(lookup_embedder=None)` probes used level 5, vulgarity 3, `embellishment='deadset'`, `embedder='none'`, all three registers and explicit `unlock=['all']`; these are research settings, not production defaults. Exact outputs/seeds are in `audit.yaml`. The run also had the parent's concurrent working-file changes, with HEAD `11aa20c`; source-file hashes describe the inventory snapshot, not a pristine-checkout claim.

| Input | Selected observed output | Seed |
| --- | --- | ---: |
| The ant waved its antennae. | The ant waved its aerial. | 0 |
| The small rubbish bin had no wheels. | The small wheelie bin had no wheels. | 0 |
| We watched a glossy ibis wading in the marsh. | We watched a glossy bin chicken wadin' in the marsh. | 0 |
| The refugee sought asylum from persecution. | The refugee sought loony bin from persecution. | 0 |
| The fox slept in its den. | The fox slept in its lounge room. | 0 |
| The aircraft landed on the runway pavement. | The aircraft landed on the runway footpath. | 0 |
| The laboratory used isopropyl alcohol rather than drinkable alcohol. | The laboratory used isopropyl grog rather than drinkable piss. | 1 |

Two further probes are **context questions**, not categorical contradictions inferred from one narrow source:

- `the-folding-stuff`: “Her money consisted entirely of coins.” becomes “Her folding stuff consisted entirely of coins.” The consulted collaborative headword distinguishes paper money from coins; broader figurative money use needs construction-level assessment before forbidding the general MONEY mapping.
- `battlers`: ordinary working families can become battlers despite an explicit wealthy/comfortable context. The [ANDC account](https://history.cass.anu.edu.au/centres/andc/meanings-origins/all) includes determined livelihood struggle and contemporary mortgage-holder usage. A political/class identity can be broader than literal financial hardship; do not turn this single probe into an automatic income test.

## Context, scope and unresolved product decisions

`parliament-house` intentionally localises an American institution and already excludes news, official, technical and instructions contexts. [Parliament's own account](https://www.aph.gov.au/About_Parliament/Parliamentary_departments/Parliamentary_Library/Research/FlagPost/2023/May/Parliament_House_35th_anniversary) distinguishes building and institution, but metonymy alone does not prove an unintended defect. The parent has been asked to assess whether this explicit entity-localisation policy should remain, gain its own control or be surfaced as added fictional/local context. No policy is silently reversed here.

Other contextual notes preserve supported breadth:

- `paddock` has a wider Australian fenced-land/playing-field range than a British horse enclosure. `punters` can be the public/customers without gambling. `old-codger` can be affectionate or mildly derisive. `joint` need not always be disreputable.
- The primary [SBS transcript](https://www.sbs.com.au/audio/podcast-episode/how-ya-goin/u4apcg1wy) supports how-ya-goin as a greeting, sometimes simply hello. `nah-yeah` and `yeah-nah` have typical yes/no readings, while [linguistic research commentary](https://blog.oup.com/2019/03/where-phrase-yeah-no-come-from/) on related yeah-no cautions against reducing every discourse function to Boolean negation.
- The 1964 Australian surfing quote for `stoked` is actually present in Wiktionary; first in that listed adjective section is not first-ever use. Commonest-thrilled, rapt's claimed usage peak and grouse's seventies-favourite flourish are not established frequency measurements here.
- `dag` and `daggy` support unfashionable/awkward/eccentric meanings, with affection possible. Do not insist every referent be objectively likeable. `nana nap` need not be taken by an actual grandmother or only in an afternoon.
- Sources support different degrees for `starvin` and `peckish`. The parent already owns hunger/dial refinement; these notes do not introduce a competing policy.
- Relative offence ranks (`donger`, `flamin`, `rooted`) and flavour are context/house-policy decisions, not universal facts proved by a dictionary. No flags or rarity metadata change because of an old source, British/New Zealand label, collaborative headword, or incomplete lookup.

## Evidence handling and continuation

All explanations are original paraphrases. No source definitions are copied into runtime. Public edited references, dictionary-publisher commentary and attributable primary guides/transcripts are preferred; collaborative sources and mediated historical quotations are labelled. Dictionary.com's licensed Collins entries are not independent confirmation of Collins. A regional label does not prove a term is absent elsewhere or uniquely originated there.

IDP rooted and StudyAdelaide sweet-as evidence were read as public indexed publisher passages; direct IDP fetch failed. Other unsuccessful guessed URLs/searches are not positive citations. Exact combined forms supported only by components (`young fella`, `little tacker`, phonetic variants, `bloody great`) are identified accordingly. Source association is not certification of every usage note.

Implementation should use the existing concept/sense-selection structure, preserve broad accepted senses, and add focused regression cases only for demonstrated distinctions. Research is kept separate from runtime recommendations and product decisions. After independent cross-review, the parent may integrate precise fixes, recheck concurrent changes and review before committing. Remaining original IDs are delegated in disjoint batches; provisional results elsewhere remain provisional, not fabricated by default.
