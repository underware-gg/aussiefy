# DD-043: bounded typed idiom construction

Date: 2026-10-21

Status: accepted implementation decision; family placements follow Rob's recorded curator rulings.

## Context

The community dictionary design treats partial composites and invented idioms as one data mechanism.
A constructed phrase must retain evidence on its parts without certifying the assembled expression or
pretending to be a persistent entry. The same operation serves Python, CLI and MCP. Existing changes v2
cannot represent constructed substitution alternatives; its coordinated update is a later slice.

## Decision

Keep pure domain values and generation in constructions.py, catalogue parsing in construction_data.py,
and the public operation boundary in bulldust.py. The loader owns I/O. Move the existing detection-free
entry dial/policy gates into policy.py so composition can reuse them without a selection/detection/loader
import cycle; select.py preserves its existing imports as re-exports.

Compile strict named templates once. A slot occurs exactly once and accepts only its declared ingredient
kind. Assemble fragments in template order, treating inserted text as opaque and recording Unicode
code-point spans in the canonical expression. Identity hashes version, family, template and ordered part
IDs and wording, independently of mutable evidence. Construction IDs occupy their own namespace.

Entry references inherit canonical metadata and limits; literal parts own theirs. Eligibility precedes
composition. The result combines maximum theme tiers across parts and family, and the family may raise
but not lower them. Profanity is the maximum independent rating. Whole-expression evidence is freshly
assessed as constructor coinage with no sources; citations and contributor credit stay on the parts.

Sample at most the configured budget per family with seeded affine mixed-radix enumeration. Do not
materialise all combinations. Suppress known full-expression and within-call collisions. Rank the word
count's distance from a reviewed band, then apply seeded weights within equal cadence scores. Defaults
live in data: 64 attempts per family, 20 maximum public results, 0.1 distance penalty. Loader bounds
(1024 attempts and 100 results) keep user-supplied catalogues finite at this boundary. This heuristic
cannot certify humour or novelty; small independently reviewed families provide the craft constraint.

Surprise constructions enter the opener pool as Entry | Construction values, preserving the ordinary
placement rates, tone rules and swear channels. The changes builder uses real entry IDs only for real
entries. Under v2 a constructed garnish has null entry_id, no constructed alternatives and a normal local
removal. Internal traces and the standalone operation retain its provenance; full public provenance and
substitution support wait for the single coordinated contract bump. No invented withholding reason or
fake persistent entry is introduced to fit the old schema.

## Consequences

The initial catalogue is deliberately small: surprise stems with implements or a credited title ending,
and reviewed hunger imagery. The stem's British/general citations establish the surprise sense, not
Australian nationwide frequency. The stronger stem receives one lower weight rather than two discounts.
Rob approved implement and title combinations at Uncle Bob under their respective themes, independently
of the bare stem and swear cap. The title ending keeps the existing glued apostrophe-n form for continuity;
its join is data and can be refined without a code exception.

Standalone generation and opener composition are now available. Fallback substitution, the shared agent
scaffold, contextual variations, extension identities and the new changes/card contract remain separate
planned slices. A caller may pin compatible slots now without copying a sentence-specific exception.
