# Community dictionary package: slice 0

## Australian-use re-review, 23 October 2026

`theme-review.json` now records 145 individual readings, including the ruder low-flying duck omitted
from the original 144-record ledger. It preserves the previous review separately and distinguishes Rob's
explicit rulings, preserved rulings and curator decisions under his contextual-reading delegation.
Thirty-one clear tag corrections are applied without changing wording vulgarity. There are no pending
owner tag questions. Seven mixed-sense records retain their existing conservative tags pending shared
sense separation; they are explicitly listed and must not be mistaken for completed semantic fixes.
The governing policy is [Australian interpretation](../../docs/plain/contributor/data-acquisition.md#interpret-terms-as-an-australian-would).

Original implementation analysis, 20 October 2026. Spec: the approved Community Dictionary Package Brief,
Build plan and Engine design in the Brain. Starting commit: `dddf3cc` on local `dev`; no website files edited.

## Starting facts

The earlier `a64c0d2` counts still hold: 1,273 entries, 1,189 active, 80 gated, four omitted; flags on 83
distinct records (34 not_aussie, 43 dubious_meaning, 23 archaic, one fabricated); 30 imagery records and
85 riffs on 54 entries. Eighteen active entries have no source; 2,132 deduplicated loaded source annotations
include nine non-URL producer/testimony/region annotations. The migration retains those as production,
testimony or explicit historical notes rather than pretending they are web citations.

The original reference-persona decision ledgers identify 16 newly added entry targets. These retain
`produced_by: agent` separately from coinage: their discovery through an agent does not make established
language invented. Existing entries merely marked covered by those ledgers keep their original provenance.

## Review records

- `level-review.yaml` records every initially active entry, plus those newly activated by separating metadata
  from manual gates. The review follows ED8 wording distinctiveness; unchanged grades remain explicit.
- `flag-review.yaml` records all 83 formerly flagged entries, with register and usage/meaning decisions.
  Shared general English becomes eligible at a lower weight. Clearly American/British-sounding terms stay
  held back through fields; they are retained for marked discovery. Real senses with competing modern
  readings use misreadable; uncertain definitions use doubtful_definition. Context/grammar-dependent gates
  stay manual. The four former omission decisions were individually reviewed: three foreign/tourist
  expressions stay out through usage fields, and the Babe quotation keeps a manual context gate.
- All 11 archaic-flag/dated-register disagreements were reviewed with the definition and register: dated
  wording retains dated; cheesed off and full bottle on are treated as current. Unambiguous historical
  terms retain archaic register. Neither currency nor swearing alone sets wording level.

## Evidence migration and source hunt

Existing URLs are preserved as structured citations. Empty support lists deliberately mean expression-level
scope is unresolved: previous ledgers expressly disclaim certification of every full construction, origin,
frequency or metadata score. These links are useful evidence to review, not discarded work. Scores and
labels stay provisional until this follow-through source hunt records what each supports. This is not a
claim that every link or every term has received a new source search.

Initial independently checked anchors are g'day, arvo and bulldust: ANDC headwords plus Wiktionary senses,
with supported usage and the earliest periods reported by ANDC. They provide real fixed scoring examples;
the broader hunt still prioritises the previously unsourced entries, riffs and crowd-only terms.

### Inherited-source integration, 21 October 2026

The immutable `inherited-source-audit.json` and companion Markdown supersede earlier partial checkpoints:
all 2,141 inherited entry/URL pairs have dispositions (1,570 inspected, 571 blocked). The extra 41 lead
records are separate. This is coverage of citations, not a finding that every mapping is sound or attested.

`apply_source_audit.py` applies only the frozen audit's complete-sense entry cohort, with the explicit
deferrals and publisher/work identities in `source-integration-policy.json`. Other statuses, including
partial meanings, frames and stored variants, remain reference-only; the six imagery rows are reserved for
the imagery cohort. No source URL, concept, frame, trigger, theme, usage or meaning gate is removed.
The manifest records each included pair. Run without `--apply` to preview from the immutable inventory
commit; repeated applications of the same policy are byte identical. This is a one-off research migration,
not a general update command: `--apply` refuses any other HEAD. The writer validates the resulting complete
dictionary before changing its data files. Trial policy changes also rebuild from the immutable baseline,
so a newly deferred pair cannot retain support from an earlier trial.

Same-work mirrors retain separate URLs but share one scoring identity. Lexicographic articles use media
weight, not a dictionary weight just because of the publisher; the contributor-reported Word Map uses
crowd weight. An exact ANDC lexicon page uses scholarly-dictionary weight. Dates retain their witness/sense
scope; a phrase such as "late 19th century" stays in the note rather than becoming an invented exact year.
No score thresholds are recalibrated. The stored distribution records the resulting scores and labels.
Goldens change because the existing continuous evidence preference now has reviewed inputs; the source
review file records affected outputs. Remaining mapping candidates, partial-support integration and the
191 IDs whose inherited sources were all blocked are deliberate follow-through work, not proof of false
or invented language. The separate `unsourced-ew4-audit.json`/`.md` and URL-only `unsourced-ew4-searches.json` now record the first
hunt for all 23 uncited entries, 25 imagery records and 85 riffs (133 targets). Search coverage does not
mean successful attestation; their scoped proposals and mapping questions still await integration.

Imagery incorporates `20261019-report~Imagery Source Search` from the Brain, preserving its partial-coverage
limits: sampled web/Trove/Books, no keyed Trove full text, ANDC or Macquarie subscription search. Its 20
unfound agent comparisons carry provisional nothing-found records; the three explicitly original hunger
comparisons have agent coinage. The two requested appetite compositions carry Rob's testimony and remain
unverified. The clean low-flying duck form links to the existing ruder entry without copying its wording or
vulgarity. Stomach/throat and horse/jockey remain preserved rather than rejected for taste. The source notes
for Oswald letters, the Murrumbidgee newsletter, Green's/ADS-L and Wiktionary retain variant/access limits;
copies of reported citations are not separately counted as primary witnesses.

Urban Dictionary's reference-only policy was added after checking its terms at
<https://urbandictionary.help/tos/>. No bulk extraction, definitions or API requests were used.

The final wording review changes 113 levels. General wording is explicit on 105 entries. The refreshed
golden corpus changes 66 of 375 outputs; `golden-review.json` identifies each case without duplicating
the long reference texts. Four of five current website hero pairs are unchanged; the rain example's
opener becomes "Strewth" instead of "Stone the flamin' crows". No website files were changed.

Golden review also exposed two latent sense boundaries as the general-English terms became eligible.
Quote-equivalent clause detection now protects dialogue agreement “Very well”; social-event mappings
require explicit event wording rather than a bare party (which can mean a group) or function. The
intensifier properly stays held through `reads_as: unknown` pending Australian vernacular evidence;
its documented meaning is not marked false, and no rarity claim follows from the limited search.

## Scope and direction

DD-040 records provisional numeric choices and the public-contract staging. Rob explicitly settled the
imagery/riff ambiguity during implementation: usage/meaning gates apply to all term types; bulldust still
follows existing embellishment permissions. Theme-policy resolution is slice 1; the constructor and the
manual historical composite replacement are slice 2. New full cards and changes contract fields land
together in slice 6. The three separately briefed website vocabulary fixes are subsequent independent work.

### Mapping-question follow-through

`mapping-followthrough.json` and `.md` add 13 inspected bodies and four blocked attempts, separately from
the frozen audits. These later sources settle several earlier *questions*, not established errors: actual
Australian use supports flat-as-a-tack for low mood and country-dunny for conspicuousness, and admiring
nonsexual perv-on is documented. Keep those mappings/gloss scope. Just-gammon/gammin supplies a better
supported complete joking form; bare gammon is unconfirmed, not disproved. Little-shit warrants the existing
opinion permission when it replaces neutral CHILD. Too-easy as an acceptance response is supported; the
unrestricted closer is still a pragmatic-context question. These findings await a separate scoped data
refinement; this source-support cohort changes no mappings or gates.
