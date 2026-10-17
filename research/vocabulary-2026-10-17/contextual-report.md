# Contextual imagery follow-up, 17 October 2026

This follow-up revisits every one of the earlier harvest's 162 `not_added` rows and its one rejected row.
It does not replace or edit the original decisions, manifest, candidate files or 45 creative retellings.
[contextual-decisions.yaml](contextual-decisions.yaml) identifies each original row and gives a revised,
meaning-specific disposition. The output of an unharnessed writer is creative evidence, not attestation.

## Results

| Disposition | Candidate rows | Result |
|---|---:|---|
| Entry | 15 | 10 distinct entries with narrow concepts and grammatical frames |
| Image | 22 | 22 contextual images with usage conditions and explicit writer/engine forms |
| Covered | 41 | Existing dictionary expressions; keep inflection and composition in writing |
| Craft | 85 | Retained creative evidence with specific sense, grammar or fidelity boundaries |
| Total | 163 | Every earlier unadded/rejected row reconsidered |

“As crooked as a dog's hind leg” now has its dishonesty/untrustworthiness meaning. It does not mean
angry, physically bent, or merely poorly made. Other additions include shirty, like the clappers, like a
scalded cat, get-up-and-go, a command-only pack it in, not a sausage, a strong flustered clause, bare-arsed,
and park one's bum. Shared English origins are noted rather than claiming uniquely Australian invention.
The [Oxford entry](https://www.oxfordlearnersdictionaries.com/definition/english/get-up-and-go) supports the
energy/readiness sense of get-up-and-go; definitions here are independently written. Existing Arthur/Martha
coverage was checked against the [Australian National Dictionary Centre](https://history.cass.anu.edu.au/centres/andc/meanings-origins/all).
Other familiar additions are editorial curation from usage knowledge, not newly established attestations.

The imagery library retains belly/mixer and dog/fence hunger comparisons; physical puffing like a broken
compressor or bellows; futile sandstorm sweeping; a snag-on-a-hotplate sleeper; a country-racetrack mind;
selfishness as avoiding decency on one's shoes; and stronger writer-only exaggerations. It also keeps the
low-flying-duck hunger image as a rewrite instead of rejecting it merely because another hunger idiom exists.

The 85 craft rows are not a second blanket rejection. For example, a physical church-pew comparison has no
precise hard-surface anchor; a Tuesday deadline would invent a date; a wedding-suit fitting would invent a
scene; the whole drum need not correctly describe a public story; ordinary knots, backbone or boots must
not acquire the figurative sense merely from their appearance. Each reason remains beside the original ID.
A writer can draw on the retained evidence where the source genuinely supports it.

## Behaviour and design

Contextual images attach to meanings independently of vocabulary substitution. New precise concepts
separate futile effort from busyness and physical breathlessness from ordinary tiredness. Plain breathless
also has an emotional sense, so it is not a direct automatic trigger. Explicit complement guards exclude
figurative hungry-for/to constructions, including punctuation between the adjective and complement.

Only direct suffixes can insert automatically. Rewrite forms and curated related associations are
conditional writer suggestions, with their usage conditions visible. They cannot establish missing facts.
Troppo defaults to exaggeration 2 and related suggestions; Dinkum defaults to exaggeration 1 and direct
meanings; all named types accept the same exact overrides. Custom needs explicit optional behaviours.
Legacy entry riffs remain compatible and independently switchable. Automatic imagery shares their seeded
probability, document count, sentence allowance, spacing and Markdown composition state.

See [the controls](../../docs/plain/functional/translation-controls.md#contextual-imagery) and
[DD-025](../../docs/architecture/decisions/dd-025-contextual-imagery.md). The new ledger is a follow-up only;
the original manifest continues to identify the earlier study accurately.

## Stable historical benchmark

The first full run found one moving-measurement failure: dynamic target recall changed from 15/25 to
14/24 when the new concept descriptions taught `plain_words` that “breath” is ordinary English. All ten
Gettysburg output strings were byte-identical to a scratch baseline restored from commit `7eae354`.
The disappearing hit was “for right down to their final breath”; this is ordinary wording, not slang.

The existing 25 target spans and matching word sets are now frozen with source/target hashes as historical
target-wording coverage. The same ten seeds, normalisation and 60% gate remain; no translation rule or
threshold was changed to make it pass. Fixture integrity checks bind every word to its target span and every
span to the original diff. The general dynamic harvest API remains unchanged. A genuinely curated slang
benchmark would need a separate baseline; this historical proxy is not presented as one.

## Verification

- Full `python -m pytest -q`: **1,981 passed, 2 expected local-corpus skips**, 476.99 seconds.
- Ruff and staged/worktree whitespace checks pass.
- Generated documentation freshness and link checks pass; new public wording was read for meaning.
- Provenance/licence checks pass, including an actual isolated wheel build and inspection.
- Python 3.10 core translation and imagery lookup smoke checks pass.
- All eight historical research rounds replay read-only, with no missing planned IDs or unparsed verdicts.
- Independent design review is clean after resolving context, grammar, measurement and documentation findings;
  see [the review](../../docs/architecture/reviews/design-review-2026-10-17-contextual-imagery.md).
- Original study evidence remains unchanged. Only this follow-up report and its 163-row ledger are added
  beside the frozen earlier study files.

## Remaining work

The independent seed-listicle acquisition, wholehearted-devotion/hand-on-heart correction, deliberative
modals, formal prose voice, bundled-model maintenance and live model/website verification remain separate.
The review also confirmed baseline malformed modal questions and the Hansel “turning and chucking” sense
error, plus a final probe of the existing object-taking QUIT substitution (“chuck it in smoking”); these are tracked in the [review](../../docs/architecture/reviews/design-review-2026-10-17-contextual-imagery.md).
This work does not claim that every craft expression has become an automatic rule, or that arbitrary
cross-sentence context is understood by a deterministic matcher.
