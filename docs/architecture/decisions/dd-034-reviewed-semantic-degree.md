# DD-034: Reviewed semantic degree, separate from style intensity

Status: Accepted; integrated verification passed.
Date: 19 October 2026.
Extends: [DD-030](dd-030-shared-semantic-context.md), [DD-031](dd-031-narrator-opinion.md).

## Context

Historical intensity numbers mix style and force. They are not independent evidence that a term means
slightly or extremely drunk. The user chose to preserve explicitly stated degree in both directions,
while keeping vivid vocabulary available when the source states no degree.

## Decision

Use optional concept-scoped entry `semantic_degree` and exact frame/trigger `trigger_degrees` maps with
mild, unmarked and strong bands. Omission stays unknown. Source forms can certify/recognise degree without
becoming replacement triggers. Target certificates never migrate onto arbitrary source paraphrases.

The shared form-eligibility seam compares realised degree, including retained source modifiers. Unsupported
compositions, unknown qualified degree and conflicting source evidence abstain. Modifier ownership is
separate from certification and reaches the existing phonetic pass using current rendered offsets.
The resolver preserves negation, relations and form requirements; stacking cannot discard a modifier.

The dictionary caches a small graded-family index. Similarity fallback cannot invent a certificate for
those families. Loaders, overlays and research-round rewrites validate/preserve annotations; no slang IDs
or specific source sentences enter engine rules.

## Consequences

Initial evidence calibrates DRUNK only. Unknown entries retain availability for unspecified input; no
status/flag or vulgarity policy is inferred from absent evidence. New families need reviewed annotations.
Plans and automatic alternatives share deterministic eligibility. Broad writer discovery remains separate;
this is not a semantic verifier for all generated prose. Existing frozen benchmark inputs remain unchanged.
