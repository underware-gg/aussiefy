# DD-057: permanent public entry IDs

Status: accepted; Rob's site request, 13 November 2026.

Entry IDs are public URL keys. Keep display headwords separate, and never reuse a published ID for an
unrelated term. A bundled append-only register maps each published key to itself, an alias target, or a
null tombstone. The model stores resolved targets; pure validation rejects duplicate/cyclic/dangling
history and any active entry occupying an alias or tombstone. Extensions cannot take reserved core keys.
Custom dictionaries can provide their own register; excluding builtins excludes the core history.

Explicit discovery resolves aliases before applying the current card's existing policy. The response's
entry_id retains the requested key; entry.id is the canonical target, using the existing v3 card shape.
Lists and seeded discovery still enumerate actual entries only. Tombstones return the shared removed
outcome; unknown keys remain not_in_dictionary. There is no invented replacement for a deleted term.

Initial history covers all IDs in the last release and the site's published dev checkpoint. A permanent
baseline regression plus exact-base promotion validation prevents silent loss or retired-key reuse in
future releases. Wording and legitimate sense corrections remain editable; semantic identity is an
editorial obligation rather than a frozen gloss fingerprint. Rename/merge edits must retain aliases,
and removal must retain a tombstone, in the same data change.
