# DD-024: Judge against the effective writing contract

Status: Accepted

Date: 2026-10-16

Extends: [DD-019](dd-019-explicit-composable-document-policy.md),
[DD-021](dd-021-request-local-profile-overrides.md)

## Context

Level and vulgarity alone do not describe an advanced document configuration. A judge that sees only
those dials can demand disabled performance, penalise preserved quotations, or excuse neutral connecting
prose unnecessarily. Research added effective settings to its blind packets, but production judging did not.

## Decision

New blind packets use evaluation protocol 2 and retain a complete snapshot of effective document/profile,
embellishment, markup and source-English settings. Resolve that snapshot through the canonical translation
route instead of reimplementing presets. Both agent and API judging use `Packet.judging()`; reference
retellings receive the same writing semantics, without judge-only scoring directions or toolkit vocabulary.
CLI and Python routes accept the same document overrides. Valid advanced combinations remain the caller's
responsibility; packet reading validates structural completeness and types rather than imposing coherence.

Keep historical packets without metadata as protocol 1. Do not infer missing historical settings from
current dictionary defaults. Record the protocol in new verdicts and reject tallies mixing protocols.
Include instructions and the effective contract in API cache identity. Preserve frozen research evidence;
new runs reuse production packets and record a selected plan's path/hash.

## Consequences

A saved packet carries its actual interpretation across later dictionary edits. Regenerating instructions
still uses the loaded rubric/guidance, so frozen experiments bind complete engine/driver hashes as well.
Protocol 1 consumers remain readable; protocol 2 JSON has additional metadata. Qualitative scores across
changed contracts, inputs or judge contexts are not an isolated causal engine comparison. Repeat judges
assess the same frozen outputs independently; their reports are additional assessments, not new source texts.
