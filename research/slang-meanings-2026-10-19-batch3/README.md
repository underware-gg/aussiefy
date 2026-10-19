# Existing slang: exact 120-entry batch, 19 October 2026

This research covers **every ID in the assigned 120-entry manifest**, excluding the preceding 220 reviewed
original-baseline IDs. Most are historical bush vocabulary and period slang. The assigned Git baseline was
`2687d7ff96d8019522eba9414498ae9c51927353`; original-inventory membership was checked against `5d1fb04`.
The [ledger](audit.yaml) records exact IDs, actual forms and shared triggers, source URLs and limitations,
manifest SHA-256, working-file digests and assessment reasons. No runtime or dictionary changes were made
by this batch.

| Assessment | Entries |
|---|---:|
| Selected sense supported, with stated evidence limits | 90 |
| Qualified mapping, gloss or provenance recommendation | 14 |
| Multiple readings, contextual boundaries or partial evidence | 15 |
| Selected reading still provisional | 1 |

The previous 220 plus this batch make **340 distinct reviewed entries of the original 1,254**, leaving
**914 outside this particular review chain**. A sibling researcher has a separate manifest; their work is
not included in these totals. The parent task should aggregate that disjoint union. These are coverage
figures, not claims of independent professional certification for every sense, trigger, inflection,
register or historical-origin claim.

## Recommendations to review

All vocabulary should be preserved. These are source and static-mapping recommendations, not a list of
14 reproduced runtime failures. Check the current detector, candidate eligibility and realised output before
changing data: shared concepts are being refined concurrently by the parent task.

| Entry | Distinction to preserve | Recommendation |
|---|---|---|
| `coolibah-tree` | Waterside eucalypt versus a named coolibah group. | Avoid inferring the named tree from location alone; retain deliberate scene imagery when authorised by embellishment. |
| `troopers` | Mounted police versus colonial police generally. | Require mounted context for the latter trigger; retain the existing singular variant. |
| `hump-the-swag` | Walking the roads versus travelling with a swag. | Preserve explicitly stated baggage/motive; distinguish historical imagery from literal identification. |
| `native-dog`, `dingo` | Generic wild/feral dog versus a dingo. | Require the intended animal/context for literal identification; do not decide contested taxonomy through a slang mapping. |
| `run-a-banker` | Bank-full level versus an asserted overflow/breach event. | Preserve the explicit event in `burst/overflow its banks`; keep appropriate bank-full usage. |
| `sandy-blight` | Historical eye-condition terminology versus unrestricted modern condition names. | Preserve historical vocabulary while protecting precise clinical wording; do not assume every modern pink-eye reference carries the same historical description. |
| `a-shonk` | Current dishonest-operator sense, historical alternate sense and uncertain derivation. | Qualify the unproved `from shonky` claim; record sense history separately. Current neutral triggers do not require a whole-word gate. |
| `slab` | Named beer package versus any case or bare 24-pack. | Require beer content for bare pack triggers and preserve explicitly different quantities. |
| `slab-hut` | Slab construction versus any rough wooden/log cabin. | Avoid asserting construction details absent from the source. |
| `pox-doctors-clerk` | Showily dressed person versus any showy object or setting. | Use clothing/person context; ordinary object showiness still has other vocabulary. |
| `know-a-bloke` | Direct contact versus a contact with another intermediary. | Preserve relationship structure for the short trigger; retain the attested full chain for chain contexts. |
| `on-your-pat` | Physical solitude/single-handed action versus emotional loneliness. | Separate these readings instead of assuming a lonely person has no company. |
| `ringbark` | Tree-bark operation versus other encircling/girdling senses. | Require the relevant tree operation for factual substitution. |

Source anchors include [EUCLID's named coolibah description](https://apps.lucidcentral.org/euclid/text/entities/eucalyptus_coolabah.htm),
[Collins's mounted-police sense](https://www.collinsdictionary.com/us/dictionary/english/trooper),
[ANDC's swagman account](https://history.cass.anu.edu.au/centres/andc/australian-words-s),
the [Australian Museum's dingo page](https://australian.museum/learn/animals/mammals/dingo/),
[Collins's banker entry](https://www.dictionary.com/browse/banker) and
[beer-package sense](https://www.collinsdictionary.com/dictionary/english/slab).
The source for the historical eye-condition description is [Merriam-Webster's blight entry](https://scrabble.m-w.com/dictionary/blight);
this is lexical research, not clinical diagnosis or treatment guidance.

The exact contact-chain idea is genuinely in [Dennis's poem, “The Intro”](https://www.gutenberg.org/cache/epub/4730/pg4730-images.html).
Its existing literary citation should be retained, while avoiding an added intermediary for every simple
contact assertion. [Dennis's glossary](https://en.wikisource.org/wiki/The_Songs_of_a_Sentimental_Bloke/The_Glossary)
also explicitly supplies the solitude reading behind `on-your-pat`.

## Preserve the demonstrated breadth

Several tempting restrictions would go beyond the evidence:

- **Goanna:** the [Australian Museum discusses monitors beyond Australia](https://australian.museum/learn/animals/reptiles/australian-goannas-evolution-and-radiation/)
  and explicitly calls the [Indonesian Komodo dragon a goanna](https://australian.museum/learn/australia-over-time/extinct-animals/megalania-prisca/).
  Clarify the Australian-only gloss; do not impose an Australian-species-only selector rule.
- **Mulga:** [Collins expressly records outback/bush as well as acacia and scrub](https://www.collinsdictionary.com/dictionary/english/mulga).
  A compulsory acacia-habitat restriction would wrongly discard the broader reading.
- **Wrap:** [Collins records the Australian praise noun with both wrap and rap spellings](https://api.collinsdictionary.com/dictionary/english/wrapped).
  Do not “correct” the current spelling merely because rap also exists.
- **Front up:** [actual Australian court-appearance use](https://www.abc.net.au/news/2007-03-05/accused-officers-front-up-to-committal-hearing/2208370)
  supports the selected sense even though a consulted dictionary page emphasises payment and sporting effort.
- **Chew the rag, nark, grafter, flash, cray and cop:** a source or dialect's familiar alternate meaning
  does not erase the selected historical/regional sense. Distinguish the readings instead of treating one
  dictionary as exhaustive.

For `give-best`, [Morris documents the historical surrender/superiority construction](https://www.gutenberg.net.au/ebooks09/0900231h.html).
Its stored object slot and two bare defeat-admission triggers deserve an availability check. The current
`select.binding_problem` rejects an object-dependent form when no object is captured, so this is not a claim
that unresolved placeholders are emitted. The same caution applies when interpreting fixed livestock
triggers and other shared concept frames.

The period meanings of `bosker`, `dilly`, `kipsie`, `gazob`, `sprag`, `bong-tong` and related entries have
primary author-glossary evidence. That establishes historical use, not present-day commonness. No automatic
uncommon flag or status change follows from age alone. Shared British or wider-English attestation also
does not prove an expression is absent from Australian repertoire.

## Provisional and partial evidence

One entry remains explicitly provisional:

- `have-a-mag`: the cited Dennis glossary explains noisy/scolding speech. A weak anonymous reprint records
  the chat construction, but a stronger edited or Australian primary source is still needed before claiming
  that citation verifies neutral chatting. The meaning is not declared false.
`willing` is supported by Dennis’s clipped headword **Willin’**, which records the vigorous/hearty
adjective. Keep its gate and distinguish that directly attested adjective from the compositional full
phrase `a willing affair`; this source alone does not establish the exact whole phrase or modern frequency.

Other limits remain visible without hiding supported uses. `cop` has edited receipt-of-punishment support;
its tolerance reading has a named Cassell's citation through an author glossary, rather than an independent
read of the original entry. `little-fella`, `cheeky-bugger`, `the-poor-bugger` and several other constructions
have component evidence, which is not automatically proof of a conventional full idiom. `a-hanrahan` has
clear character/allusion evidence; that is different from finding an independent common-noun dictionary
entry. `in-all-my-natural` has an [edited full-construction record in the Concise Ulster Dictionary](https://cms.nationalmuseumsni.org/sites/default/files/2022-10/Concise-Ulster-Dictionary-Letters-A-Z.pdf),
while the particular Dennis attribution remains to be located. None of these gaps means fabricated.

The shonk evidence records a [neutral current explanation by an Australian writer](https://billmitchell.org/blog/?p=36591)
and [separate lexical sense history](https://en.wiktionary.org/wiki/shonk). The linked Green's record could
not be read, so the ledger does not claim independent confirmation of it. No ethnic trigger was found in
this entry's current `SWINDLER` mapping. Correcting an uncertain derivation is a clear provenance repair;
an automatic whole-word gate is not inferred.

## Integration and validation

[sources-proposed.yaml](sources-proposed.yaml) contains **119 proposed per-entry source records**, excluding
the provisional entry and omitting weak/indirect source candidates where a stronger selected-sense
source is available. These are review candidates, not applied provenance or runtime changes. Some URLs
support a component, historical meaning or specific primary context; consult the per-entry evidence scope
before using them in public cards or source weighting.

Validation checked the exact manifest/order and SHA-256, all 120 original-inventory memberships, uniqueness,
no overlap with the previous 220, totals, references and source-candidate exclusions. Working-file digests
identify the snapshot. The parent is concurrently splitting/refining shared concepts, so some records already
reflect those working changes; reconcile recommendations against the final parent state before integration.
No generated corpus, full runtime suite, provenance declaration or commit is claimed by this research batch.

Sources were manually inspected using browser pages and public indexed passages. Direct-fetch failures,
source chains, reprints and original works not separately retrieved are stated. Same-work Gutenberg and
Wikisource editions are not independent witnesses. Collins on a licensed mirror is still Collins.
Community dictionaries and anonymous mirrors are not elevated to professional editorial authority.
Notes are original mapping analysis, with no reproduced definition collection or source examples.

Apply the software-design principles by storing lexical/domain distinctions in dictionary data and using
the shared semantic context machinery. Do not add one-off engine checks for individual slang strings.
Keep literal role, reference, quantity, species and construction preservation distinct from an explicitly
chosen degree of comic imagery. Shared semantic-fit checks and resolved embellishment settings govern
that boundary; ordinary lexical fixes can proceed independently of the separate constructor/metadata design.
