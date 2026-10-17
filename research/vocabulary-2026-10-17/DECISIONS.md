# Vocabulary decisions, 17 October 2026

## X-post suggestions and extrapolations

These suggestions came from the five unharnessed announcement-writing contexts described in the README.
The phrases are creative candidate material, not newly attested traditional sayings. Clean and stronger
versions share an image, while the existing swear-word ratings filter the stronger wording.

| Image | Decision and attachment |
|---|---|
| Brains of a fence post | Clean and stronger riffs on `drongo` |
| Brains of a fucking wheelie bin | Riff on `drongo`; the existing literal wheelie-bin entry keeps its original meaning |
| Wouldn't trust us to run a fucking chook raffle | Existing `couldnt-organise-a-chook-raffle` already covers incompetence; the stronger image is also a `galah` riff |
| Bloke starting a mower that owes him money | Effort image on `hard-yakka` |
| Chippy finding a good chisel used to stir paint | Anger image on `ropeable` |
| Concreter with a boot full of wet cement | Anger image on `ropeable` |
| Apprentice doing up a sump plug | Excessive effort image on `hard-yakka`; not a general translation of "tight" or mechanical advice |
| Brickie dropping a pie face-down | Anger image on `spitting-chips` |
| Roofer putting a nail through a thong | Anger image on `spitting-chips`; does not establish that a source character was injured |
| Let Rob off the lead; pack of prize fuckwits; silly cunts | Ordinary metaphor/composition of existing vocabulary; no separate dictionary meaning |
| Ratchet-strap click; turning the radio/footy up over a foreman, barney or jackhammer | Context-dependent comparisons; no sufficiently useful new meaning or attachment selected |

Curated extrapolations add concrete images to `a-chippy` (pencils), `a-brickie` (mortar and a pie), `tradie`
(tools in the ute), `esky` (guarded shade at the cricket), `servo` (sausage-roll/coffee temperatures), and
`mozzie` (angle-grinder whine). Existing first riffs retain their ordering; where an entry gains its first
riff, the first eligible one becomes the signature suggestion. Riffs are optional colour rather than claims
that these details occurred in the source.

## Earlier vocabulary work

A read-only replay of all eight configured research rounds found every currently proposed entry ID already
present, with no unparsed verdict files. This checks for unapplied accepted entries, not whether every raw
harvest span deserves acceptance or whether older judgement calls should be overturned.

| Round | Planned entries | IDs absent from current dictionary |
|---|---:|---:|
| classics | 211 | 0 |
| dinkum-check | 5 | 0 |
| everyday | 40 | 0 |
| fairdinkum | 147 | 0 |
| fourth-pass | 23 | 0 |
| gap-fill | 137 | 0 |
| second-pass | 18 | 0 |
| third-pass | 24 | 0 |

The historical `new_phrases*.yaml` exports were candidate lists used by earlier rounds, not pending approved
additions. Exact string misses include inflected forms, dropped-g spellings, complete source-specific clauses
and ordinary English. Spot checks confirm coverage of such items as work back, a shonk, a red-hot go,
sparrow's fart and the pox doctor's clerk comparison; they are not blindly re-imported.

The explicitly outstanding dialect candidate `yield sign` now maps to `give way sign`, including plurals.
The Australian wording is independently supported by the [NSW Government sign reference](https://www.nsw.gov.au/driving-boating-and-transport/driving-nsw/roads-safety-and-rules/stopping-giving-way-turning/stop-give-way-signs-lines).
The match requires the whole road-sign phrase; investment and crop-yield senses remain unchanged.

## Reference-persona decisions

All 15 reference texts were retold in each of three fresh persona contexts: 45 outputs and 203 extracted
expressions. Every extracted phrase was checked to occur in its cited retelling, allowing only apostrophe
and whitespace normalisation. The manifest pins the originals and retained outputs. Agent candidate rows
remain alongside each source; [decisions.yaml](decisions.yaml) records a disposition for every row.

Six new entries were selected:

| Entry | Reviewed meaning and boundary |
|---|---|
| `square-person-up` | Financial reimbursement of a pronoun or named person; not fighting, geometric squaring or repaying kindness |
| `just-the-shot` | Just right for the purpose; familiar Australian usage, curated from own knowledge |
| `crook-in-the-guts` | Queasy or sick in the stomach; not illness in general or a nauseating substance |
| `out-on-poss-feet` | Very tired, retaining the subject's possessive; shared English |
| `work-like-billy-o` | Work vigorously; shared British usage, marked dated |
| `get-cracking` | A command to start work; no new automatic swap of machines starting or narrative "begin work" |

The six entries account for ten candidate rows because expressions recur across personas. Glosses and
triggers are independently written. Sources are linked on entries where available; the financial sense of
[square up](https://en.wiktionary.org/wiki/square_up), Australian use of
[get cracking](https://www.abc.net.au/listen/programs/radionational-breakfast/-get-cracking-david-pocock-s-call-to-action-post-election/105256648), and an Australian oral-history use of
[crook in the guts](https://australiansatwarfilmarchive.unsw.edu.au/archive/htmlTranscript/399?asPdf=y)
were checked without copying definitions or source prose. No claim of exclusively Australian origin is made.

Nine new riffs account for eleven further rows: sheet-of-tin and loose-gate comparisons on `whinge`, heavy
eyelids on `knackered`, rabbit/skirting and corrugated-iron images on `ticker`, a cyclone-battered flat-pack
on `cactus`, a rooster/fence comparison on `skite`, dinner-plate eyes on `gobsmacked`, and milk souring in
the sun on `cranky`. Wording is adapted where needed to follow the entry naturally. These include invented
images, not newly attested traditional idioms.

Nineteen rows are exact existing forms/variants. Another 162 were not selected: they include inflections,
ordinary shared phrasing, context-dependent metaphors and uncertain expressions. This is a bounded curated
extension, not a claim that every remaining phrase is absent or unsuitable forever. In particular, a hungry
belly compared to a mixer full of rocks is colourful but has no clean existing single-term attachment here;
it remains in the raw evidence rather than being forced onto a generic food noun.

One row is explicitly rejected for its supplied meaning: the Uncle Bob pig story uses "as crooked as a
dog's hind leg" for anger. That is a dishonesty/crookedness image, so it is not added as an anger synonym.
The duck/crotch variation is not added over the existing hungry/arse idiom, and broad "pack it in"/"get-up-and-go"
phrasings do not acquire unsafe new triggers from their literary context.

## Replay compatibility

Adding riffs to entries from an earlier round exposed a replay defect: the round's scratch base removed the
entry but retained its riff reference. `base_dictionary` now removes riffs for the exact IDs it sets aside,
in scratch only. Real data is preserved, surviving entries retain their riffs, and a genuinely unknown riff
ID still fails validation. A regression covers own-round and later dependent entries, write-back preservation
and strict orphan detection. The eight-round read-only audit above then completes successfully.

## Independent work still open

- The original seed listicle has not been acquired through the scrape/review pipeline. Its known foreign or
  unattested sayings remain omitted or gated; this pass does not approve bulk import.
- The held-out study's wholehearted-devotion versus `hand on heart` sense defect remains a separate targeted
  data correction. Deliberative modals and formal-prose voice also need their own behaviour work.
- The bundled embedding model remains a separate stale-model maintenance item. New dictionary/riff data is
  usable directly without retraining or claiming new model coverage.

## Verification

- Dictionary validation passes: 1,234 entries and 774 concepts, with no new warnings.
- Full `python -m pytest -q`: **1,924 passed, 2 expected local-corpus skips**, 507.85 seconds.
- `ruff check .` and whitespace checks pass.
- Documentation generation/check and licensing/provenance checks, including an actual built wheel, pass.
- All eight configured round replays complete read-only with no missing proposed IDs or unparsed verdicts.
- The 45 output and candidate-file pairs match the manifest hashes; all 203 extracted phrases occur in
  their cited output after apostrophe/whitespace normalisation.
- Regenerated goldens change nine outputs across four inputs. Changes were read: optional whinge/servo and
  broken-chair imagery, appropriate tiredness/just-right alternatives, and resulting seeded choice changes.
- The independent design review's documentation finding is resolved and its final disposition is clean;
  see [the review](../../docs/architecture/reviews/design-review-2026-10-17-vocabulary-harvest.md).
