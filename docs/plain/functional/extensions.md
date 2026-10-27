# Community extension dictionaries

Load a community manifest with the existing `--dict` option or `load_dictionary(extra=…)`. It is an
addition-only format, separate from the privileged [dictionary overlay](dictionary.md#dictionary-overlays)
which can patch core records. The package knows no accounts, site tiers or contributor identities beyond
the plain credit strings supplied in the data.

## Manifest and identifiers

```yaml
format: aussiefy-dictionary-extension/v1
namespace: community
concepts:
  community:EXAMPLE_CLAIM:
    description: An illustrative meaning, awaiting a reviewed word.
    plain: accept a claim
    triggers: {vp: ["trust ?={np}"]}
    examples: ["I trust the story."]
    credit: [{name: example-contributor, scope: definition}]
entries:
  - id: community:demo
    form: zz-demo-form
    concept: [HUNGRY]
    frame: predicate_adj
    credit: [{name: example-contributor, scope: term}]
evidence: []
```

This example is synthetic format documentation, not a proposed slang entry. A namespace starts with a
lower-case letter and otherwise contains lower-case letters, digits or hyphens. New entry ids must use
that namespace followed by a kebab-case id; new concept ids use it followed by an UPPER_SNAKE id.
References may name core ids or another loaded namespace. Unknown concepts and pattern grammar fail
at load, including on concepts without entries. Such concepts participate in contextual interpretation
and the existing wordless-meaning listing.

An entryless extension concept is a meaning waiting for a word, not a guard. `no_entries` is retired
throughout the core and extensions: declaring it, even as false, fails. An extension error names its
filename, concept and the reason. Omit the field and supply the meaning's plain wording and examples.
Phrase fences are core-only and live in a separate file; extensions cannot define them.

Duplicate ids fail. Sharing a namespace across files does not permit overwriting a record. A new entry
with a core form, frame and a shared concept fails with an instruction to use `evidence_for`. A different
meaning has its own concept and qualified id. The engine does not guess that two meanings are equivalent.
Fix a core meaning in the core or through an explicitly supplied maintainer overlay.

## Additive evidence and credit

An `evidence` list record has `evidence_for` and any of `sources`, `testimony`, `spoken_use`, `caught_on`
and `credit`. It cannot change a target's wording, meaning, themes, level or status. Targets must exist;
they may be entries added by another loaded extension, even one later in the file list. All additions
load before evidence is composed, and the combined record passes the usual metadata invariants.

Sources retain their publisher, URL, underlying kind, support and notes. Extension sources are recorded
as `kind: community` with their original kind in `basis`. A community-contributed scholarly citation
therefore still counts as scholarly evidence; attribution is not another vote. The same offline source
URL validator used by core loading applies, with no fetching or DNS lookup.

Credit records are `{name: plain text, scope: term}` or `{name: plain text, scope: definition}`. They are
deduplicated and added to existing credit; their names are carried without account lookup or URL
interpretation. Concepts can carry definition credit too. The existing single-string credit remains
accepted and keeps its current serialised shape; when combined with new records it becomes a term
credit record. The coordinated card contract will normalise its public presentation in slice 6.

## Testimony snapshots

A testimony summary contains `people`, `independent`, `places`, `first_date`, `last_date` and
`summary_date`. Counts are distinct totals, not increments; no names or individual testimony are loaded.
The exporter is responsible for deduplication and independence. Counts and ISO dates use the same
validation as core testimony.

An extension snapshot replaces a target's exported summary, rather than adding anonymous counts which
could overlap. It must be at least as recent as that summary. Multiple evidence records or extensions
must provide the same snapshot for a target; conflicting totals fail and require one consolidated
export. Identical snapshots count once. A newer curator record replaces an older one; contradictory
records on the same date fail. These rules consult no wall clock and infer no identities.

`spoken_use` still needs testimony. `caught_on` still needs documentary support or independent testimony.
Adding evidence never patches those invariants or makes constructor output carry sources.

## Promotion

Copy the accepted entry into core data under a core id, retaining its sources and contributor credit,
and set `promoted_from` to its old qualified id. Credit is a snapshot of the supplied name. Keep
community attribution on contributed citations; the engine never strips it when serialising an entry.

`promoted_from` requires a qualified former id, an unqualified current id and credit for the term's
contributor. It cannot appear on an extension entry, and two core entries cannot claim the same former id.
`dictionary.promoted_entries` maps former ids to core ids. Loading a stale extension entry with a
promoted id fails; evidence must also switch to the new core id. Regenerate the export for its new pin.

## Preference-adjustment data

An optional `adjustments` mapping declares `normal` and `popularity` bands, each two finite positive
bounds containing 1, and a `records` list. The popularity band must contain the normal band. There is
no implicit global tuning table or default band: each export declares its limits.

Each record contains exactly:

| Field | Value |
|---|---|
| `match` | A canonical source-match key supported by the loaded dictionary |
| `term` | An existing core or qualified entry id |
| `level` | Integer 1–5 |
| `vulgarity` | Integer 0–3 |
| `embellishment` | Integer 0–2 |
| `factor` | A finite number within the declared popularity band |

The factor represents full-strength tuning. At normal strength its result is clipped to the normal
band; popularity uses the wider band. Factors from matching extensions multiply, then are clipped to
the intersection of those extensions' bands. Only records for the exact key, term and three dials
participate. Duplicate contexts within one export fail. Community adjustments have no root fallback.

The pure `dictionary.adjustments.factor(…)` query supplies a weight multiplier. Loading it changes no
score, evidence label, eligibility, roll or current translation. Applying it to substitution weights,
the popularity option and personal preferences belong to slice 6, with the coordinated response contract.
It cannot make a term with the wrong meaning eligible.

## Dictionary identity

`dictionary.identity` is a versioned SHA-256 identity over the core data's relative names and bytes,
the built-in-loading mode and each extra file's bytes in load order. It includes adjustment data.
Core model and POS data participate; filesystem paths, modification times and documentation do not.
Relocating identical inputs preserves the identity. Changed bytes or reordered different extras change
it, even if the package version is unchanged. The identity describes a completed file load; subsequent
manual mutation of a dictionary object is outside that snapshot.

Identity computation is loader I/O; the model and adjustment queries read no files. Identity fields on
translate, lookup, plans and changes responses arrive together in slice 6. The current response version
and lookup ranking are unchanged by these loading mechanisms.

See [DD-048](../../architecture/decisions/dd-048-community-extension-composition.md) for composition choices.
