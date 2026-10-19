# Slang meaning audit: batch 11

Research-only review of the exact **74 original-baseline IDs** in `/private/tmp/aussiefy-audit-batch11.json`, in manifest order: 50 records from `swearing.yaml` and 24 from `thirdpass.yaml`. These files change no runtime vocabulary, concepts, source sidecars, gates, policy, status or documentation.

The ledger records **41 selected meanings supported, 25 contextual or multiple-usage observations, 6 correction recommendations, and 2 provisional evidence gaps**. There are **72 unapplied source-candidate records**, a **70-record source catalogue**, and **20 diagnostic probe cases**. Evidence and candidate counts are different quantities; neither is an attestation score or a request to activate terms automatically.

Earlier disjoint ledgers cover **940/1,254 original IDs**. This batch brings its own chain to **1,014/1,254**, with **240 outside that chain**. Parallel batches 9 and 10 each have 120 disjoint original IDs. The manifests and previous ledgers together partition all 1,254 IDs exactly, but final completion still requires independent reconciliation of the parallel research and later application/review of changes. New entries added after original baseline `5d1fb04` are outside these counts.

## Recommendations to implement

| Entries | Boundary | Observation / next action |
|---|---|---|
| `give-a-shit-about` | Polarity and comparative degree | Seed 0 changes “I could care less about the prize.” to “I could give a shit about the prize.” The negated control works. Refine the shared `CARE_ABOUT` care-less boundary already identified in batch 8; preserve legitimate positive questions and conditionals. |
| `a-funny-cunt`, `a-funny-bugger` | Occupation versus an evaluation of humour | Seed 1 turns “He is a comedian, but not funny.” into “He's a funny cunt, but not funny.” Bare comedian has both an occupation sense and an informal/ironic person sense. Both entries use the same trigger; the second was not separately selected. Preserve occupational information when that is what the source supplies. |
| `no-fuckin-idea` | Personal ignorance versus an information-seeking question | Seed 0 turns “Who knows the answer?” into “I've got no fuckin' idea the answer?” Protect complements and question function in the shared clause matcher; retain the complete rhetorical ignorance reading where appropriate. |
| `first-in-best-dressed` | Malformed provenance | The current `sources` list contains a truncated `https://en.wiktionary.org/wiki/first_in` and a separate `_best_dressed` string. Repair this to the complete comma-bearing [canonical URL](https://en.wiktionary.org/wiki/first_in%2C_best_dressed). The first-come advantage meaning remains valid. |
| `is-it-buggery` | Lookup-only intent versus a real automatic placeholder trigger | `EMPHATIC_NO` says lookup only, yet matches “most certainly not in any way whatsoever”; seed 0 produces “Is it buggery.” without an antecedent question. Represent lookup-only explicitly or bind the question’s actual auxiliary and subject before automatic use. He/she variants already exist; the issue is their context, not their absence. |

These are **six entry recommendations covering five shared or data issues**. They do not imply six separate engine mechanisms. No slang-specific Python checks are proposed.

## Contextual findings, not automatic exclusions

- Friendly vocatives can also offend in Australian contexts. The garnish’s question/second-person signal identifies an addressee, not friendship. Qualify the blanket “fond” and US-only offence wording while preserving affectionate use.
- `a-sick-cunt` is documented high praise; mapping ordinary decency to admiration can add evaluation. `no-fuckin-way` can turn a tentative answer into categorical refusal. These are candidates for the shared configurable semantic-effect/degree policy, not reasons to erase vivid language.
- Most adjective-plus-person-head combinations are productive expressions. The records separate adjective evidence, person/address construction evidence and any whole-expression witness. A generic contempt epithet does not necessarily assert betrayal, a specific fraud or literal parentage. “Little” and “old” can be evaluative rather than literal age/size assertions.
- Funny can mean humorous or peculiar; shonky can refer to dubious integrity or poor reliability; mean can be unkind or stingy. The selected senses remain useful. The `a-mean-bastard` diagnostic did not select that entry, so no output bug is claimed from that case.
- Fisho has both fishing and fish-selling senses. Neither invalidates the other. Yank’s external-US sense is broader than the within-US northern Yankee meaning.
- Good innings can describe a life, a career or a long successful run; death/retirement is a frequent setting, not a mandatory condition. First-in-best-dressed has broader priority uses as well as better-choice uses. Do not narrow either beyond the evidence.
- `drag-the-chain` has edited meaning support, but this pass did not establish the slowest-shearer origin aside as settled history. Shared British labels, or non-Australian origins, do not by themselves make a current expression inauthentic in Australia.
- The coordinated Mary-and-Jane telephone probe remains unchanged; no recipient-loss bug is claimed. Streets-ahead preserves its comparison, and nut-out preserves its answer complement in the positive probes.

## Provisional evidence gaps

| Entry | What this pass establishes and leaves open |
|---|---|
| `luckier-than-a-shithouse-rat` | An exact community witness reports the luck meaning and suggests it may be Canadian. An Australian luck-context witness is still needed. Crazy/cunning rat sayings are different comparisons and cannot certify this one. |
| `a-cooked-cunt` | Community leads cover tired/high and mentally fried readings. Stronger direct contextual evidence is needed for the current unqualified `LUNATIC` association; neither absence nor one competing sense proves the other false. |

Both entries remain in the dictionary unchanged. Their leads remain in `audit.yaml`; they are omitted from `sources-proposed.yaml`. Unsuccessful searches do not establish fabrication or justify a new gate.

## Evidence calibration

Strong primary examples include William Gleeson’s [Kokoda oral history](https://australiansatwarfilmarchive.unsw.edu.au/archive/htmlTranscript/1844?asPdf=y) for crook-as-buggery, [Tasmanian Hansard](https://www.parliament.tas.gov.au/__data/assets/pdf_file/0022/73282/HA-Thursday-17-August-2023.pdf) for chuck-a-tanty, and Australian practical/broadcast usage of here’s-the-go, all-up and out-bush. These are uses in context, not population-frequency measurements or origin certificates.

The scholarly c-word discussion and bastard/bugger corpus chapter provide construction/pragmatic evidence; they are not a certificate that every adjective compound is an independently inherited idiom. Referenced Macquarie entries and older corpora are reported by those authors, not counted as freshly retrieved independent witnesses. A journal article and its repository copy, licensed dictionaries and their reproductions, and AAP republications each belong to their original source family.

Dictionary definitions were paraphrased sparingly into original research notes. No modern definition collection, article body, lyrics or full reference text was copied into package data. Search-index passages are explicitly distinguished from full-page access, and community sources retain their assurance limits. For hungry-duck, the documented low-flying-duck family and explicit arse alternative support the productive stored wording; this does not pretend every dropped-g variant has a separate historical citation.

## Snapshot and validation

The contextual HEAD is `11aa20c`; the working tree contains the parent’s staged semantic-effects integration and concurrent verification. `audit.yaml` records the exact file digests and before fields read during research, not a clean-HEAD claim. Diagnostic translations use level 5, vulgarity 3, Deadset, all registers, explicit unlock and no embedding model; they are observations rather than proposed defaults. Reproduce them against the eventual implementation checkout before fixing anything.

Validated: exact 74 IDs and order; original-baseline membership and uniqueness; no overlap with the prior 940 or either parallel manifest; exact 1,254-ID aggregate partition; manifest hashes; before-field source-file hashes; decision totals; evidence references and candidate URLs; and both Python `SafeLoader` and C `CSafeLoader` on the two new YAML files. Original inventory extraction uses the C loader because that old baseline has the separately reported unquoted-question-mark URL issue. This research task does not run or substitute for the runtime full suite.
