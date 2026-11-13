# Local design review: slices 3+6 v3 freeze

Date: 13 November 2026. Scope: the diff from `4e86135`, including real producers, request controls,
host boundaries, replay, document offsets, schemas, fixtures and conformance tests.

This is a local six-concern review using software-design-principles and software-design-review.
No independent subagent review or other-agent contact is claimed; the standing no-contact instruction
takes precedence over the review skill's dispatch workflow. Full-suite, publication, provenance/wheel
and performance completion gates are recorded with the final checkpoint in the Brain hand-off.

## Findings

No outstanding design findings after local triage. Resolved findings were:

| Location | Concern | Resolution and evidence |
|---|---|---|
| `aussiefy/changes.py:678`, `aussiefy/markdown.py:439` | Correctness, verification | Track exact article/case/phonetic/escaping edits for local occurrences. Include imagery inside an owner only when actually contained; a separate image splice keeps its own change. Test multiple edits, units and Unicode. A strengthened trailing-part control detects a missing phonetic map rather than passing by edge clamping. |
| `aussiefy/cards.py:68`, `aussiefy/v3_contract.py:64` | Domain, invariants | Share maker projection and rich metadata; preserve explicit coiners and derive agent coinage only for already-assessed bulldust. Keep a pinned garnish target as the canonical object in its offered pool, including withheld responses. Check unique option keys, selected membership, complete part joins, content identity, references and warning parity after structural validation. |
| `aussiefy/engine.py:573`, `aussiefy/pins.py:103` | Trust boundary, completion | Validate exact source/dictionary/seed and immutable target recipes. Replay through real eligibility and realisation; reject unknown, malformed, duplicate, incompatible or unused picks. Complete replay suppresses unlisted automatic choices. Explicit forms cannot inject arbitrary text. |
| `aussiefy/engine.py:443`, `aussiefy/select.py` | Structure, meaning | A transient Entry view reuses source/target fit and literal rendering without adding fabricated dictionary IDs. Fall back only before the roll when curated candidates do not fit; result complements, unsupported frames and opaque spans remain protected. |
| `aussiefy/engine.py`, `aussiefy/changes.py` | Provenance | Do not hide a bulldust entry in an unlabelled secondary stack. It remains eligible as the primary attributed choice. Both automatic and explicit stack paths enforce this. Riffs and imagery retain their own provenance. |
| `aussiefy/mcp_server.py:64`, `aussiefy/tuning.py:38` | Boundaries, state | Clients never supply usable raw preferences; only the host callback does. Resolve its numeric dials once per request/document. Independently expose themes/invention without Custom; validate canonical tool allowlists. Document that the SDK ignores unknown top-level arguments while routed document-config bypasses fail. |
| `aussiefy/engine.py` | Behaviour limits | Explicit replay preserves configured riff counts and spacing; it bypasses the automatic roll, not those limits. A two-image packet replays under its original settings and fails with a lower count or wider gap. |
| `aussiefy/lookup.py` | Completion, contract | Reuse the full resolved neutral header for every lookup outcome, including empty/short paths, while omitting numeric profile detail. Full-gate shape tests exposed the missing tuning/warning header; assertions now check the coordinated v3 fields. |
| `aussiefy/pins.py:176` | Premise, regression | Source-reading probes can have no public match identity. Do not dereference one when no replay is needed, and capture only actual substitution/image choices. Existing protected-query and genre probes exercise this path. |

Calibration: reuse the same domain rule at real second callers; keep explicit values at boundaries;
avoid a persistence/account abstraction; fail on broken supplied choices rather than silently changing
them. Do not weaken reviewed data or add response fields to work around a producer gap.

## What's done well

- Accepted r2 validation fields remain identical; immutable historical assets are retained. Active
  fixtures come from public emitters, including a real constructed opener, imagery, Markdown, warnings,
  lookup and tuned-to-untuned replay. No illustrative projection is presented as emitted output.
- Complete construction recipes resolve one bounded composition. No Cartesian search, fuzzy identity
  recovery, persistent session or server-side preference state is introduced.
- One render path and shared edit maps own coordinates. The optional editor pin sidecar is separate
  from the frozen v3 response and preserves precise source anchors rather than widened change regions.
- Public tuning remains weight-only, before variety, with the existing repeat and failed-roll behaviour.
  The host supplies per-call preferences without teaching the engine whose preferences they are.
- Seven deliberately broken variants exercise fallback, interior phonetic offsets, bulldust maker,
  pinned form validation, per-document callback frequency ambiguous riff wording and replay riff limits; baseline and variant receipts are kept
  with the checkpoint evidence. Existing whole re-render oracles remain part of the full gate.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| Slice 7 names, kept/personal/held spots, selection and plain alternatives | Reader-facing meanings and richer editing | Deliberately the later response contract; the accepted v3 shapes do not include these. |
| Site integration of replay packets and sidecars | Tuned share links can retain forms and riffs | Storage, accounts, request wrappers and deployment belong to the host. No site pin or deployment is changed here. |
| Source hunt and score calibration | Better attestation coverage and calibrated weights | The provisional evidence model and research programme remain separate acceptance work. |
