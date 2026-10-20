# Design review: degree composition, 20 October 2026

Status: Independent focused review converged; integrated verification passed.

## Findings

No remaining findings in the applied diff. Both findings below were corrected and independently rechecked.

- Medium, high confidence: widening a replacement to its qualifier let an uppercase modifier uppercase
  the whole predicate (`She is VERY drunk` became `She is VERY PISSED`). Retained modifiers are now
  restored after predicate casing. Generic tests assert the exact original prefix and lower-case head.
- Medium, high confidence: absorbing a modifier into a clause expansion could discard uncaptured
  frequency/aspect words (`always`, `still`, `getting`). Absorption is restricted to adjective predicates;
  synthetic clause/editor tests preserve all three source forms. Wider clause ownership is independent work.

## What's done well

One degree plan controls eligibility and qualifier absorption. Replacement spans and editor alternatives
share the same engine rendering; source modifiers are retained or absorbed exactly once. Threshold-bearing
constructions use the same certified grade rule in selection and lookup. Unknown evidence and unsupported
compositions remain conservative, and synthetic overlays exercise the rules without naming hunger in code.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| Whole-clause ownership | Preserve aspect/frequency while allowing richer expansions | Adjective substitutions already have bounded owned spans |
| Further graded families | Broaden fluent coverage | Needs independent source/target calibration |
| Broader source/target pairing | Catch more multi-edit degree errors | Current verifier explicitly requires local unchanged context |

Final integrated checkpoint: **3,311 passed, two permitted local-corpus skips**. Ruff, explicit research
Pyflakes, publication, provenance/licences and the supported-settings changes budget all passed.
