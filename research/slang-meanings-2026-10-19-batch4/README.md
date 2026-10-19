# Existing slang: fourth research allocation, 120 entries

Checked on 19 October 2026 with assigned baseline `2687d7f` and the refreshed working-tree
snapshots identified in the ledger. This allocation reviews the **exact 120 IDs** assigned in
`/private/tmp/aussiefy-audit-wave1-2.json`, independently of the parallel
[batch 3 allocation](../slang-meanings-2026-10-19-batch3/README.md). All IDs belong to the original
`5d1fb04` inventory and exclude the preceding 220 reviewed IDs. The entry snapshots, concept triggers,
source locators and file digests are in [audit.yaml](audit.yaml).

This is **research only**. No dictionary, engine, status, flag, theme or metadata edits were made.
[sources-proposed.yaml](sources-proposed.yaml) contains 120 proposed per-entry source records for review,
not applied runtime provenance or instructions to replace existing sources.

| Assessment | Entries |
|---|---:|
| Selected lexical sense supported | 99 |
| Mapping, contextual meaning or compatible-frame recommendation | 10 |
| Supported range, tone or contextual boundary worth retaining | 11 |

These 120 plus the preceding 220 cover **340 of the original 1,254**, leaving **914** before counting
parallel batch 3. Reconcile that batch separately before reporting a combined total. Newer working-tree entries are outside this original-baseline accounting; the ledger records the
working inventory size at its research snapshot.

“Supported” concerns the selected lexical sense. It does not certify every trigger, every grammatical
realisation, contemporary frequency, exclusivity to Australia, or the full wording of every composed
construction. Every expression is preserved; this research proposes no automatic gate or removal.

## Recommendations

Nine recommendations concern active records; one concerns an already gated record.

| Entry | Supported meaning and boundary | Suggested integration |
|---|---|---|
| `slanter` | Historical sham/unfair adjective; cheap poor quality need not be dishonest. | Separate cheap-and-nasty quality from dishonest/fraudulent contexts. This archaic entry requires an explicit register override. |
| `snake-juice` | Strong alcoholic drink; technical alcohol is not necessarily a beverage. | Preserve beverage use and distinguish solvent, disinfectant and fuel contexts. This archaic entry requires an explicit register override. |
| `give-a-stuff-about` | Care/indifference idiom, especially negative; comparative caring-less can still mean some care. | Preserve full polarity and degree rather than equating care-less with unqualified care. |
| `kid-stakes` | Historical bluff, joking and pretence; an easy task is not necessarily pretence. | Separate the task-easiness sense of child's play from non-serious/make-believe senses. |
| `mooch-around` | Aimless sauntering; trudging can be weary but purposeful. | Separate wandering, fatigue and purposeful travel rather than using one broad walking concept. |
| `rouse-on` | Reprimand/upbraid; shouting can instead warn, celebrate or ask for help. | Require the scolding sense rather than treating volume or anger alone as a reprimand. |
| `not-a-sausage` | Emphatic zero; very little can be positive. | Preserve quantity distinctions unless an explicit exaggeration policy authorises the change. |
| `ice-brick` | Rigid cooler block; gel packs also include flexible pouches and medical packs. | Preserve physical form and purpose; distinguish unrelated blue-ice senses. |
| `fruit-and-veg` | Goods rather than the section/aisle/department selling them. | Retain the location noun in location-bearing constructions. |
| `the-joes` — gated | Low-spirits noun; all current SAD triggers are predicate adjectives. | Supply a compatible noun construction if the entry is enabled. This is a dormant frame mismatch, not a claimed current automatic substitution. |

The parent remapped gated `a-peb` from broad HOON to LOUT during this research, resolving the earlier
driving-role concern; the refreshed snapshot records the supported hooligan/lout/yob mapping.

Useful primary or edited checks include [Dennis's author glossary](https://en.wikisource.org/wiki/The_Songs_of_a_Sentimental_Bloke/The_Glossary),
[ANDC's kid-stakes analysis](https://history.cass.anu.edu.au/centres/andc/annotated-glossary/k),
[Oxford's care idiom](https://www.oxfordlearnersdictionaries.com/us/definition/english/stuff_1),
[BBC's zero-quantity explanation](https://downloads.bbc.co.uk/learningenglish/features/tews/170606_tews_not_a_sausage.pdf),
and [Esky's own distinction between bricks and gel packs](https://www.esky.com.au/ice-bricks-ice-packs/).

## Observed examples and existing protections

Read-only engine probes used `Translator(lookup_embedder=None)`, `level=5`, `vulgarity=3`,
`embellishment='deadset'`, `embedder='none'` and the seeds below. `unlock=['all']` was used for the probe
matrix; the first two examples additionally enabled `registers=['current','dated','archaic']`.
These explicit research settings are not proposed defaults.

| Entry | Seed | Source | Observed output |
|---|---:|---|---|
| `slanter` | 1 | The cheap and nasty bag broke. | The slanter bag broke. |
| `snake-juice` | 3 | The alcohol evaporated. | The snake juice evaporated. |
| `an-old-coot` | 2 | We met an elderly man. | We met an old coot. |
| `give-a-stuff-about` | 5 | I care less about money. | I give a stuff about the foldin' stuff. |
| `kid-stakes` | 1 | That task seems like child's play. | That task seems like kidstakes. |
| `mooch-around` | 0 | She trudged home. | She mooched around home. |
| `rouse-on` | 2 | They yelled at him for help. | They roused on him for help. |
| `not-a-sausage` | 1 | There is very little left. | There isn't a sausage left. |
| `ice-brick` | 0 | I bought a gel pack for my knee. | I bought an ice brick for my knee. |
| `fruit-and-veg` | 0 | The produce aisle is closed. | The fruit'n veg is closed. |

These are examples, not an exhaustive regression corpus. “The alcohol evaporated” is itself sense-ambiguous;
it demonstrates eligibility outside an established drinking context, not that evaporation rules out liquor.
The knee example supplies stronger explicit purpose context.

Existing protections matter: default registers reject the two archaic entries; “It is child's play” rejects
`kid-stakes` as apparently plural before a singular agreeing verb, while the example above still selects it.
“The elderly man arrived” can resolve a different overlapping detection, while the object example selects
`an-old-coot`. That older-person substitution is supported by the source’s broader old-man meaning;
it is included to calibrate tone rather than asserted as a semantic defect. Neither a single rejection
nor a single selected example proves universal behaviour.

The generated `kidstakes` spelling also deserves a separate realisation check: this research establishes
the meaning boundary and does not propose accepting its current spacing as correct.

## Preservation and source calibration

- **Broader source-backed meanings stay available.** Chiack covers good-humoured banter and more hostile
  derision; smoodge has romantic and flattering uses; play up covers misbehaving people and troublesome
  machines/body parts; clapped-out also describes tired people.
- **Do not invent stricter definitions.** Cambridge explicitly links verandah/veranda and porch and permits
  differing architectural descriptions. Block-of-chocolate usage does not establish a mandatory retail weight.
  Sozzled is very drunk in Cambridge but broadly intoxicated in the historical Australian glossary; preserve
  the range rather than making one degree universally compulsory.
- **Tone is meaningful without requiring deletion.** Blow-in can be dismissive/unwelcome in an edited
  dictionary, while friendly or humorous extensions need not therefore be false. Old coot covers an old
  man, especially an eccentric/crotchety one; the historical examples do not make foolishness mandatory.
  Preserve the broader sense and contextual tone rather than restricting it to oddball referents.
- **A source for a component is not an exact-phrase certificate.** Get-your-gear-off, stay-out-of-strife,
  some-poor-mug and several give-object constructions use attested vocabulary productively. Their ledger
  scopes distinguish that from a traditional fixed expression. Bare-arsed combines edited meaning evidence
  for the ass spelling with primary Australian evidence for the arse compound; those are complementary.
- **Primary construction checks resolve uncertainty.** Contemporary ABC usage supports transitive
  [spruik products](https://www.abc.net.au/news/2013-11-01/wa-mining-representative-in-china-to-spruik-companies/5063910),
  even though an older dictionary section is intransitive. Theatre notes support snout-on for grudges;
  parliamentary speech supplies nick-over-to; reported Australian speech supplies never-have-picked-it.
- **Historical texts are historical evidence.** Dennis and Gilbert H. Lawson establish genuine dated words;
  they do not settle current frequency or present-day repertoire eligibility. Their overlapping glossaries
  and multiple web mirrors are not counted as independent corroboration.
- **Reproductions retain limitations.** The object-one construction for dot is supported by reproduced Oxford
  text with its edition/licensing history unresolved. The source is not presented as a new independent
  dictionary or an independently inspected printed edition. Strengthening that citation is useful later.

The former departmental ANDC M and S pages were checked and do not contain the tempting mob/stir material.
The proposals use the actual Collins mob entry and Jessica Milner Davis's author-uploaded scholarly analysis
for stirring instead. The Macquarie `?p=10990` link could not be retrieved; it is not treated as inspected
kid-stakes evidence. Failed searches do not establish fabrication, and one dictionary's omitted sense does
not disprove a sense supported elsewhere.

## Verification and integration

Sources were manually consulted through public pages or indexed passages. No source definitions, quotation
collections, entire modern articles or acquired corpora are copied into this folder. Notes and semantic
analysis are original. Full historical books, articles and transcripts were not uniformly read cover to cover;
locators and access limitations record the actual evidence used.

Validation checks exact allocation, original inventory membership, no overlap with previous ledgers or
parallel batch 3, record/source integrity, counts, proposed-sidecar coverage and snapshot digests. Both YAML
safe-loader implementations can read these research files. No runtime full-suite run or commit is claimed.
The parent task owns independent design review, provenance, index updates, integration tests and commits.

Use dictionary data for lexical distinctions and shared semantic context for construction, referent, role,
polarity and tone. Avoid engine branches naming individual slang strings. None of this batch requires
changing the other agent's theme or metadata design before recording evidence or making clear semantic fixes.
