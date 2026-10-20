# DD-031: Configure reviewed added narrator opinion

Status: Accepted

Date: 2026-10-19

Extends: [DD-019](dd-019-explicit-composable-document-policy.md),
[DD-025](dd-025-contextual-imagery.md), [DD-030](dd-030-shared-semantic-context.md)

## Context

Some expressions retain an input reference but add editorial judgment: calling the living lucky expresses
an opinion that ALIVE alone does not establish. Other mappings drop real information: courageous people
are not necessarily soldiers, and sympathy does not mean someone died. Tone cannot express this distinction.

## Decision

- Annotate reviewed Entry mappings with `semantic_effects`, initially allowing only `opinion`. All forms
  and mapped concepts must share that addition. Unannotated mappings retain their existing behaviour;
  this change does not certify the rest of the dictionary.
- Resolve one `narrator_opinion` boolean through ordinary document settings. Deadset/Dinkum default false,
  Troppo true, and Custom clears it regardless of the dial; explicit overrides apply last.
- Reuse one rejection rule for automatic candidates, meaning suggestions and annotated garnish extensions.
  The canonical engine path also controls plans and cap-raised change alternatives. Exact term discovery
  remains available with an explicit disabled-effect explanation. Cards expose the reviewed annotations.
- Include the permission in yarn's existing effective contract. Lint counts recognised effect-bearing forms
  in input and output, allowing retained input occurrences while rejecting additional disabled effects.
  The existing form index includes annotated garnish extensions so writer checks share their eligibility rule.
  Verify and yarn submission consume that check. This is bounded known-term checking, not general semantic
  inference or proof that an arbitrary opinion has input support.
- Correct role-losing mappings rather than providing a permission to lose roles. Brave bastards maps to
  courageous people; poor buggers maps to unfortunate people described sympathetically.
- Retain existing imagery exaggeration/association controls. Do not introduce duplicate effect permissions,
  a full ontology, another parser or switches that weaken factual/role preservation.

## Consequences

An exact source expression can remain even when opinion additions are disabled. Different wording that
supports the same judgment may remain conservatively unrecognised; no new entailment engine is claimed.
If a later entry needs both exact and opinion-adding meaning mappings, separate the senses or introduce
mapping-specific effects when that concrete requirement exists. General agent-written opinions beyond known
forms remain subject to writer judgment and external assessment rather than a mechanical guarantee.
