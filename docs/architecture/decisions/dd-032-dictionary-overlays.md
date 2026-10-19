# DD-032: Compile explicit dictionary overlays before translation

Status: Accepted

Date: 2026-10-19

Extends: DD-002, DD-010, DD-019

## Context

Document overrides configure behaviour. Existing custom dictionary files only add entries and reject
duplicate IDs. Correcting a bad route could therefore require editing package data or merely adding a
competing candidate. The user requested composable corrections driven by corpus evidence and tooling,
while retaining a generic engine rather than post-processing special cases.

## Decision

The existing dictionary input accepts a versioned `aussiefy-dictionary-overlay/v1` mapping alongside legacy
entry lists. Its operations add concepts, add entries, patch concepts and patch entries. Stable IDs identify
targets; addition never replaces implicitly, patching requires an existing record, and patches cannot rename
IDs. Fields replace whole values, including lists and maps. Later files replace only fields they name.

Compose raw records, preserving explicit defaults. Built-in source references are applied before overlay
files, so explicit replacement can clear them. Validate operations with canonical schemas, resolve final
cross-record references, and compile the normal dictionary indexes once. Behaviour settings and all shared
eligibility checks retain their roles. Translation has no overlay-specific matcher or string-replacement pass.

The loader owns I/O and auxiliary metadata. A pure vocabulary composer owns the versioned record operations.
Record effective entry origin and a bounded per-load operation list for inspection. Existing research-round
file-writing workflows remain distinct; they share concept-field knowledge through the canonical schema.

## Consequences

Corrections affect translation, lookup, plans, lint and alternatives through the same loaded dictionary.
Replacing a faulty concept trigger or entry mapping removes its actual route, rather than hoping a competing
candidate wins. Corpus-based positive and negative regressions remain necessary: a valid overlay is not proof
that its proposed meaning is correct. Generic grammar defects are still fixed in shared engine logic.

V1 covers entry/concept records, not every auxiliary corpus. Sources inherit unless explicitly replaced;
authors review whether they still support changed meanings. A correction file is provenance of the edit,
not attestation of the expression. A failed load returns no dictionary and never edits package files.
