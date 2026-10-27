# DD-047: Citation links and contextual source-match identity

Status: Accepted for slice 5 foundations; the extension/tuning integration is unfinished
Date: 2026-10-25
Extends: [DD-034](dd-034-reviewed-semantic-degree.md), [DD-044](dd-044-phrase-interpretation-context.md)

## Context

The initial slice 5 trial added citation-link validation and source-match keys. Its public-link rules
correctly rejected reserved hostnames used by unrelated scrape/archive fixtures. Phrase interpretation
also exposed two identity gaps: unresolved readings retained the attempted sense's identity, and display
pattern text had lost context directives such as `^start` and `^person` before fingerprinting.

## Decision

`validate_source_url` is one offline shape check for submitted and loaded citation links. It returns the
original URL or raises `UserError`; dictionary parsing wraps that as `SchemaError`. URLs must be HTTP(S),
at most 2048 characters, without credentials, controls, spaces, IP literals or non-default ports, and use
public hostname syntax rather than single-label/reserved internal suffixes. It does not fetch, resolve DNS,
certify source content or guarantee a network destination. Tests needing a valid citation use the reserved
example sites under `.org`/`.com`, rather than `.test` or `.example` suffixes which represent invalid links.

Archived-round adaptation remains immutable. It preserves a valid original URL's bytes and validates the
adapted citation through the current schema, rather than bypassing URL rules because a record is old.

Detection retains its winning compiled `Pattern`, separately from the candidate concepts merged at the
same span. `detection_match` intersects that provenance with the meanings actually retained. A holding
reading (`UNRESOLVED_SENSE`) returns no semantic match key; it cannot claim the attempted belief or regard
reading. Context-filtered and superseded concepts do not enter its root. A known dictionary pattern may
therefore support a nonempty subset of its concepts in a particular context.

Source roots contain sorted concept IDs, frame and a SHA-256 fingerprint of the compiled pattern grammar.
The fingerprint version is `pattern-v1`. It includes token/slot/assertion elements, grammatical roles,
inflection forms and context directives. Equivalent case, whitespace and stylistic intensity do not
change it; different assertions or person/clause-boundary constraints do. Guard status, source captures,
entry IDs and evidence scores are not pattern grammar and do not enter the fingerprint. In particular,
adding an output entry to a formerly wordless meaning does not itself re-key its source pattern.

Key parsing checks canonical syntax. Dictionary validation checks the authored pattern and supported
concept subset. Detection remains the only owner of reviewed degree composition and conflict abstention;
validation does not independently try to prove that every possible qualifier is reachable for every
pattern. An adjustment can apply only to an exact key actually emitted by detection. No stylistic
intensity is promoted into a semantic degree certificate.

Research ledgers and reports retain original scope analysis and bibliographic references. Their own MIT
provenance is recorded in `research/PROVENANCE.yaml` and exact first-party claims in `third_party.yaml`;
external publications are cited, not relicensed. This does not apply source evidence, certify 125 senses
or upgrade an attestation label.

## Consequences

Unresolved readings have no semantic tuning target until their meaning is established. Public change-card
integration remains in slice 6. Namespace extensions, evidence composition, promotion, adjustments and
dictionary identity are still later slice 5 work; these repairs do not claim that slice complete.

Context, filtered-sense, unresolved-reading, canonicalisation and captured-name controls exercise the key
boundary. The scrape/archive fixture tests and source-URL rejection tests exercise the same validator
without DNS or source downloads. Research provenance checks cover the preserved, unapplied inventory.
