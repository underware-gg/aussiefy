# Existing slang: source and meaning pass, 18 October 2026

Prompted by the missing lively-party sense of “go off like a frog in a sock”. This pass inventories the
dictionary at `5d1fb04` and manually cross-references a selected set of core terms and risky meanings.

The [ledger](audit.yaml) records **130 selected existing entries out of 1,254 inventoried entries**
(1,173 active, 77 gated, four omitted). It retains baseline file digests, source URLs, publication types,
lookup headings, decisions and original reasoning. The additional party entry is a new representation of
an existing expression, not another independently researched saying.

## Method and limits

Priority goes to the Australian National Dictionary Centre's public, letter-specific references, with
Cambridge and Green's for shared English and grammatical distinctions. Aussie English supplies explicit
party/reaction uses of the frog expression. Australia Day's community glossary corroborates selected uses;
its F and L pages are one publisher, not two independent sources. The fox comparison also has a primary
speaker's different interpretation in a band interview.

Sources were read by hand through the browser. No reference dictionary was bulk scraped, and no source
definitions, usage examples or full texts are redistributed. The runtime's existing `sources.yaml` sidecar
adds the checked URLs without rewriting other hand-curated entry files. Source quotations and etymological
stories are not copied into glosses. Source-selected headwords may support an inflected or composed form;
that does not establish a full construction as a traditional idiom.

This is a bounded pass, not certification of all 1,254 entries, every trigger, every register/region claim or
every possible sense. A selected sense can be supported without being exhaustive. A source's omission of a
sense does not disprove that sense. Multiple websites repeating a definition do not necessarily constitute
independent evidence. Previously committed research and measurements remain historical evidence.

## Decisions

| Decision | Existing entries |
|---|---:|
| Selected sense supported | 114 |
| Mapping, missing-sense or gloss correction | 11 |
| Multiple documented interpretations; current sense retained | 1 |
| Provisional evidence needs further checking | 1 |
| Loose consecration paraphrase gated by user decision | 3 |

The corrections stay in dictionary data and existing configuration controls:

- **Frog in a sock:** retain the anger sense and add explicit excited-reaction verbs plus a lively-party noun
  phrase with its own plural. Generic parties, ordinary excitement and a literal pendulum in full swing do
  not establish those meanings. “The party was really lively” is not newly detected: the current bounded
  patterns cover “a lively party” and “partied wildly”, without introducing an event-subject classifier.
- **Unemployment:** joblessness stays plain. “On the dole” requires unemployment-payment receipt;
  “dole bludger” requires an explicit accusation of work avoidance while claiming those payments. The old
  broad concept affected lookup; its NP frame already prevented it replacing predicate “unemployed” in
  deterministic translation. Generic welfare is also no longer assumed to mean unemployment benefits.
- **Crikey and religious phrases:** “by crikey” is an exclamation. “God willing” remains conditional hope;
  oaths, gratitude for past divine help and “under God” retain their wording rather than becoming surprise
  or future uncertainty. The difference was already noted in the frozen curated wording labels.
- **A proper crack:** map earnest effort separately from suffering hardship. Remove ambiguous “fight hard”
  from hardship detection; it can describe actual combat. Attempt patterns keep their complements intact.
- **A fair go/shake:** map fair treatment and equitable opportunity, preserving generic freedom and liberty.
- **Barrack for:** describe the supportive construction separately from bare “barrack” meaning jeer.
  “Dennis” in the earlier gloss refers to the historical author, not a regional sense.
- **Christen:** use the informal first-use sense with an explicit object slot. Generic consecration remains
  plain; the earlier slotless paraphrase could also discard the object in “consecrated it”.
- **Consecration:** the user chose the existing `dubious_meaning` gate for the original “make [it] true blue”
  and “make fair dinkum” paraphrases. Genuine/loyal differs from sacred. Explicit unlock access is retained;
  component attestation is not passed off as attestation of the complete paraphrase.

The engine, dials and model files are unchanged. The dictionary change makes the bundled model's data
fingerprint stale; no retraining or quality claim is made. New URLs also change the sources on lookup/change
cards, so contract fixtures are regenerated and reviewed alongside translation goldens and public docs.

## Verification

Focused regressions cover meaningful outputs, tense, singular/plural party forms, false-positive contexts,
benefit receipt, lookup, effort versus hardship, religious claims and explicit gate access. Independent
software-design review reports no remaining findings. The affected documentation/harvest/sense run passed
182 tests and the acquisition run passed all 26 tests. Required complete verification passed **2,330 tests
with two expected local-corpus skips in 977.18 seconds**; Ruff, dictionary validation, whitespace and generated
publication checks also pass. See the [review record](../../docs/architecture/reviews/design-review-2026-10-18-sourced-meanings.md).

Review narrowed adjective-party patterns before common political/event compound continuations and added
a clause-end requirement to “give it everything”, retaining relative-clause tails. The engine's pre-existing
`TRY_OUT` object capture can still misread “try hard to finish it” as “give hard a burl to finish it”; this is
recorded separately rather than claiming the new effort owner fixes every attempt construction.

## Remaining work

“Flat as a tack” needs more evidence before changing its current low-spirits mapping. An indexed ANDC
October 2005 FLAT-CHAT passage supports full exertion/speed, but its old PDF URL returns HTTP 404 (confirmed
by a direct request outside the sandbox). That is provisional evidence, not proof that other senses are wrong.
“Grinning like a shot fox” has both satisfied and defeated-smile interpretations in the checked sources;
the current supported happy/satisfied reading is retained without claiming exclusivity. ANDC also records
childish withdrawal for “spit the dummy”; calm quitting is not automatically treated as a tantrum.

The remaining 1,124 baseline entries have not been individually sourced in this pass. Continue from the
ledger rather than treating absence from it as a rejection. Website release-pin/live checks, the controlled
performance follow-up and model-quality shaping remain separate work; this pass does not clear them.
