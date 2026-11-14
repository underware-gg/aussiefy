# Design review: site-reviewed v4 freeze

The amendments after 67aeb737 were reviewed by one independent read-only reviewer against the six
software-design concern areas. Scope: selection group outcomes/locks, near names, source duplicates,
headword keys, null-target replay and the host-set personal-list cap.

## Findings

No unresolved finding remains in this freeze diff. Two confirmed boundary cases were fixed:

| Priority / confidence | Location / concern | Evidence and resolution |
|---|---|---|
| Medium / high | changes.py; verification | Withholding could remove plain:source from alternatives while its replay sidecar still exposed it. Only register a pin for an actually offered plain option. A forced supported withholding branch now rejects the hidden choice. |
| Low / high | changes.py; outcome semantics | An unsettled render region could be called outside_dials although candidates already fit the current settings. Preserve the rendering failure as nothing_fits. A forced supported unsettled-region branch pins this distinction. |

Both reproductions exercised existing failure branches in memory, rather than claiming a natural-corpus
failure. The independent review passed 117 focused checks plus four replay/withholding checks. Subsequent
verification passed 199 focused checks and the 12 freeze-specific checks (overlapping counts). Full gate
receipts are recorded in the Brain checkpoint report. Tests cover each fix and frozen bundle integrity.
An unknown near target now fails the semantic checker cleanly rather than escaping as a dictionary lookup.

## What's done well

- Selection locks reuse ordinary eligibility, rendering and local coordinate handling.
- Near names come from authored concept data and are checked against it.
- Null-target replay protects exact source wording from phonetics and preserves it on recapture.
- Host limits affect host data; direct client lists retain their existing bounded validation.
- Kept duplicate suppression compares complete edited output, including differing option regions.
- Six package schemas match the frozen snapshot, whose manifest pins actual emitted fixtures.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| Authored English choices at kept spots need a later pin protocol | Share those edits | Source replay is complete; personal choices deliberately remain unshared. |
| Meaning-quiz batching and Gate 4 acceptance audit | Reduce question cost and consolidate acceptance evidence | Both are separately authorised next steps after this freeze checkpoint. |
