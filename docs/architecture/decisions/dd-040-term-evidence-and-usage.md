# DD-040: Store term facts and derive evidence and eligibility

Status: accepted
Date: 2026-10-20
Extends: DD-002, DD-005, DD-032

## Context

The community dictionary design separates what backs a phrase from where it came from, whether it feels
Australian, and whether the proposed meaning is sound. The former flags mixed those questions. URLs from
the earlier sense audits include component evidence and search leads, so their presence alone cannot
certify a whole expression. Entries, riffs and contextual imagery need one evidence model.

## Decision

Store structured sources and testimony, search outcomes, production and coinage, curator records, credit,
origin, Australian use, perceived variety, currency, subject matter and meaning uncertainty. Derive score,
five bars, evidence label and first attestation through the pure `evidence.assess` operation at load time.
A live testimony summary replaces the exported summary. Derived fields cannot be supplied as YAML facts.
Testimony sources require a summary, preventing an uninterpretable citation from silently scoring zero.

Versioned `attestation.yaml` starts with explicitly provisional weights: scholarly dictionaries 6, slang
dictionaries and literature/corpora 4, media 3, crowd dictionaries 2. Each further independent source of one
kind contributes half as much as the previous one. A publisher/work contributes once, with its strongest
supported citation. Empty support lists retain unresolved/component-only citations without scoring them.
Community attribution retains its underlying evidence kind and never changes testimony into documentary
evidence. Source dates only count towards first attestation when date support is declared.

The scale has five two-point bars; attested begins at four bars (8 points). Testimony contributes
`8 * (1 - exp(-people / 12)) + 0.75 * log1p(places)`, stopping at three bars (6 points) without documentary
evidence or a curator's supported spoken-use record. This rewards independent breadth without letting
an arbitrary number of testimonials certify itself. The source hunt will calibrate these numbers after
several hundred expression-level assessments; this commit does not claim that calibration is complete.

Both substitution and garnish selection share `1 + 0.5 * score / maximum_score`. This replaces raw URL
counts for substitutions and retains the former bounded
1–1.5 evidence influence while allowing improvements within a bar to matter. General English multiplies
weight by 0.5: it stays eligible and can still win. This moderate default prefers distinctively Australian
wording without effectively removing common general expressions. Level remains an eligibility gate,
re-graded by how distinctly and colourfully Australian the wording is, independently of swearing,
placement or uncertainty. Reviewed individual grades are retained in the migration ledger.

These preference factors apply to substitution and garnish Entry candidates. Entry riffs and contextual
imagery keep their shared tone-and-signature sampler (the first curated option weighs double), as the
design's unchanged colour-selection behaviour requires. They gain the same usage/meaning gates and
evidence labels; evidence alone does not reorder that editorial signature.

Only manual gates and omission remain in status; `slur` and `untagged` remain flags. Foreign-sounding terms,
uncommon Australian usage and doubtful definitions are held back independently of status, even with all
manual gates unlocked. Real but misreadable entry senses have an explicit `misreadable` unlock. Register
alone controls currency; it is no longer duplicated as an archaic flag. Origin itself never excludes a term.
Rob confirmed on 2026-10-20 that the new usage/meaning gates apply to riffs and imagery too. Their existing
embellishment permissions still allow labelled bulldust; lack of attestation is not an eligibility gate.

The unreleased public changes contract remains version 2 during the internal migration. Entry cards keep
URL strings until package slice 6 introduces all new card and construction fields in one coordinated bump.
Riff and imagery offer objects can already carry evidence without changing the closed entry-card schema.

Urban Dictionary is a reference-only crowd source. Its [terms](https://urbandictionary.help/tos/) were
checked before research: no copied definitions or bulk extraction, and no API use without express
permission. Source notes remain our own observations rather than reproduced definitions.

## Consequences

Unreviewed links are retained honestly, so most terms initially remain unverified until their expression
scope is reviewed. That says what our evidence supports, not whether the slang is real. New sources can
change the derived score and label without migrating stored labels. Constructor output cannot carry sources;
coinage needs supported adoption before it can become attested. Copying a citation cannot inflate a score.

The old unlock names are intentionally removed. Lookups can include held-back entries marked by the field
responsible, while omitted entries remain hidden. Import/tag/review tools and provenance checks consume
the same structured source format. The migration changes seeded wording; goldens and the site's current
hero pairs are compared and reviewed, rather than treating old wording as semantic truth.

Historical research rounds remain replayable through an adapter owned by the round importer, after
explicit entry fixes and before canonical validation. It preserves structured records, retains old URLs as
unreviewed citations and records unresolved annotations in notes. Retired flags convert conservatively to
their separate fields; `fabricated` requires manual review without inferring coinage. Manual gates and
definition doubt remain independent. The archives and canonical parser stay unchanged.
