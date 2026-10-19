# Slang meaning audit: batch 8

Research-only review of the exact 120 original-baseline entry IDs assigned in `/private/tmp/aussiefy-audit-batch8.json`. No runtime vocabulary, mapping, provenance, gate or policy has been changed by these files.

The ledger records **80 selected meanings supported, 13 mapping/wording recommendations, 21 contextual or multiple-usage observations, and 6 provisional evidence gaps**. All 13 recommendation records were active in the snapshot. There are **114 unapplied source-candidate records** and 123 source-catalog records, including complementary and component-only sources. These counts describe different things; a source candidate is not an attestation score or a proposed automatic activation.

Earlier disjoint ledgers cover 700 of the original 1,254 IDs. This batch brings its own verified chain to **820/1,254**, with **434 original IDs outside that chain**. Parallel batch 7 has a separate disjoint manifest and is excluded until its ledger and this one have both been independently reconciled. New vocabulary added after original baseline `5d1fb04` is outside these coverage figures.

## Main recommendations

| Entries | Meaning or construction boundary | Current observation / next action |
|---|---|---|
| `give-two-hoots-about`, `give-a-rats-arse-about` | Caring idioms need the source’s polarity and comparative degree. “Always negated” is too absolute. | Seed 7 changes “I could care less about the prize.” to “I could give two hoots about the prize.” Review the shared care-less trigger; preserve interrogative/conditional and other legitimate positive-polarity uses. |
| `see-the-job-through` | Continuing work does not entail completing it. | Seed 0 yields “They saw the job through but didn't finish it.” from “They carried on the work but did not finish it.” Keep the completion idiom and correct the shared trigger boundary. |
| `have-a-crack-at` | Attempting something does not always preserve the specific action of tasting food. | Seed 1 yields “I had a crack at the soup.” from tasting it. The output is plausible colloquial speech, but less specific; retain the sensory action when that distinction matters. |
| `bawl`, `have-a-sook`, `bawl-eyes-out`, `blubber` | Crying alternatives carry manner and judgement: loud sobbing, intense crying, or sulking/peevishness. | Seed 6 yields “He bawled silently.”; seed 0 turns quiet funeral tears into “had a sook”. Use shared manner/tone context, and keep the vocabulary for appropriate uses. Only bawl and have-a-sook have individual probes; the other two share the same generic CRY triggers. |
| `hoof-it` | The idiom preserves walking but the current match consumes a destination. | Seed 0 changes “We walked home.” to “We hoofed it.” Preserve home/there through detection and realisation. |
| `on-pat-malone` | Physical solitude and emotional loneliness differ. | Seed 0 yields “He was on his Pat Malone in a crowded room.” This predicate-adjective record is eligible, unlike the earlier NP on-your-pat record. |
| `tinnie` | A can of beer is not a bottle of beer. | Seed 1 changes an explicitly opened bottle to a tinnie. Retain can/unspecified-beer uses; preserve explicit packaging. `coldie` independently permits cans or bottles. |
| `uni` | College can denote university, vocational training, secondary education or a named school. | Seed 0 changes vocational college to vocational uni. Preserve the university sense without treating every college as one. |
| `esky` | Portable cooler and kitchen refrigerator/ice compartment are distinct ice-box senses. | Seed 0 changes an explicitly kitchen-refrigerator ice box to an esky. Existing cooler/weather exclusions already protect a different ambiguity. |

The 21 contextual records include normal idiomatic exaggeration and legitimate broader senses; they are **not 21 additional confirmed bugs**. In particular, physical and emotional cold in the mother-in-law’s-kiss comparison coexist; go-out-like-a-light has both sleep and unconsciousness readings; deaf-as-a-post is conventional hyperbole; and a patchwork-doona phrase is not intrinsically impossible, even though patchwork-quilt context may need more precise preservation. Shared words or UK labels do not make an expression non-Australian.

Cross-review preserved three additional broader ranges: a solo walk can itself be the plan sustained by keeping the show going; Collins permits blue-murder to mean a great deal of noise OR fuss, so the joyful-scream probe does not alone establish added complaint/terror; and an edited Canadian historical dictionary explicitly permits postie for other postal workers as well as letter carriers. Its broader Canadian range is not a claim about Australian prevalence, but it prevents a global delivery-only exclusion. All three observations remain contextual, with no hard runtime restriction proposed from their probes.

## Provisional evidence gaps

| Entry | What is supported and what remains open |
|---|---|
| `blind-as-a-welders-dog` | An Australian brewery founder directly reports the complete phrase in a drunkenness context. Stronger visual-impairment evidence is needed before deciding how to change the current BLIND mapping. Anonymous visual-joke usage is a lead, not grounds to declare the visual reading false. |
| `enough-to-make-a-brown-dog-spew` | The related kill-a-brown-dog family has historical discussion; that is not exact evidence for the stored spew comparison. |
| `gone-for-six` | Community recollection reports the exact death expression and quotes related go-for-six definitions. The original quoted dictionary and the broader exact-form ruin/loss range need verification. Literal six-month absences and knocked-for-six surprise are excluded as substitutes for evidence. |
| `like-a-koala-up-a-gum-tree` | Existing personal Coolangatta testimony is retained. A 1993 linguistic field report has a related awkward comparison; it neither independently confirms nor disproves the contentment reading. |
| `square-person-up` | Debt-settlement meaning is supported, but the retrieved community entry explicitly uses intransitive square-up-with-you. Seek a direct-person repayment witness for square-you-up; do not infer that familiar spoken construction is ungrammatical from this gap. |
| `just-the-shot` | This pass did not establish a sufficiently strong exact-form public source. A meaning-side just-the-thing comparator is labelled as such, not misrepresented as an attestation. |

No provisional entry is proposed for removal or gating merely because stronger sources were not found. No related/component-only source is proposed as exact whole-expression evidence. The six provisional IDs are omitted from `sources-proposed.yaml`; their leads and limits remain in `audit.yaml`.

## Evidence calibration

- Edited lexical entries are preferred where available. Primary sources include recorded Australian off-your-chops speech, a war oral history for crook-in-the-guts, an editorial wouldn’t-be-dead-for-quids use, an Australian brewery interview, historical committee speech, and official McDonald’s breakfast-menu usage of brekkie/Macca’s. Such examples show use; they do not establish population frequency, Australian origin or every sense.
- Oxford’s bawl entry explicitly illustrates **bawling one’s eyes out**, so this is full-construction evidence rather than separate-word evidence. The existing model provenance does not make an otherwise established idiom invented.
- Whole constructions, phonetic variants, inflectional variants and productive adaptations are distinguished per entry. Related show-on-the-road, alive-and-kicking, brown-dog and koala comparisons are not passed off as exact traditional attestations for different stored wording.
- Dictionary.com’s licensed dictionaries and their original publishers are one source family. Third-party Oxford reproductions, community Wiktionary entries, speaker recollections and reader-submission collections are labelled with their actual assurance limits. Referenced books/newsprint not independently retrieved are not counted as fresh witnesses.
- Regional swimwear meanings are verified separately from state-preference claims. The Word Map reports contributors in several regions; no state exclusivity or representative prevalence statistic is inferred. The original Word Map URL is a candidate; the indexed reproduction actually inspected is identified in the ledger.
- Smoko is not forced to involve smoking: Collins explicitly includes tea/refreshment breaks. Lollies are not forced to be wrapped; broader edited sweet/candy senses coexist. Galah does not require noisiness, and drongo’s popular racehorse-origin story is not treated as settled.
- Source definitions were paraphrased into original research notes. No modern dictionary or prose collection was bulk copied into package data. Failed or inaccessible lookups are not evidence of fabrication.

## Read-only probes and validation

`audit.yaml` records diagnostic level 5, vulgarity 3, Deadset embellishment, no embedding model, all registers and explicit unlock. The 17 probe cases record the first selection found in seeds 0–24, or the failure to select a named entry. They are observations, not proposed default settings or promises about later commits. In particular, smash-the-vase and sleep-with-him did not select the targeted records: no active-object or partner-dropping bug is claimed for them.

Validated: exact 120 manifest IDs and order; uniqueness and membership in the original 1,254; no overlap with the previous 700 or parallel batch-7 manifest; decision counts; source-reference and candidate-URL integrity; both YAML loaders on the two YAML research files; current entry frames, status, forms and trigger snapshots. Before fields and file digests deliberately record a concurrent working-tree snapshot, not a pristine HEAD claim. Recheck runtime reproductions when implementing because the parent agent is changing shared semantics independently.

The ledger’s baseline commit is contextual. The original baseline has the already reported unquoted `?` URL flow-list parser bug, so original-ID extraction uses the C loader; the new research files themselves parse equally with Python SafeLoader and CSafeLoader. Runtime/full-suite checks belong to the later implementation slice, not these unapplied notes.
