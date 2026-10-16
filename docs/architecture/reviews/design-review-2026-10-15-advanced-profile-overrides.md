# Design review: request-local advanced profile overrides

Date: 2026-10-15

Scope: DD-021; advanced profile validation/resolution; engine consumers; translation, plan, guide, lint,
verify, strict/extended Markdown, CLI/MCP and yarn propagation; configuration documentation and isolated tests.
Single independent reviewer assessed all six software-design-review concerns, followed by owner triage.

## Findings

No unresolved findings. Three initial findings were reproduced and corrected:

| Priority / confidence | Location and concern | Finding and resolution | Calibration |
|---|---|---|---|
| High / high | `aussiefy/engine.py`, verification/completion | Clean and sweary channels could separately exceed an advertised placement limit. Count placements together; test combined text limits and a zero closer limit. | Controls must work observably, with one source of truth. |
| High / high | `aussiefy/engine.py`, premise/verification | A hard-coded second-channel budget could emit swears with a zero sentence budget. Apply the remaining shared budget; document separate tail/riff/closer limits and test budgets 0/1/2. | Trace consumers before exposing configuration. |
| High / high | `aussiefy/select.py`, code-level/verification | Zero swear weighting still selected a candidate when every candidate had zero weight. Exclude zero-lean candidates; test both mixed alternatives and an all-vulgar pool. | Fix the cause rather than mask a valid caller configuration. |

The owner also corrected profile propagation into lint suggestions and applied source-sentence spacing to
tails/riffs. Full-suite, golden and publication gates are required before the commit; results are recorded
with the delivered slice rather than inferred from this review.

## What's done well

- Immutable nested snapshots and request-local profile replacement protect shared dictionary state.
- `policy.resolve` remains the canonical resolution path across every document operation.
- Inspection materialises inherited zero rates and fallback limits into reusable `profile_config`.
- The nested profile distinguishes numerical tuning from the document garnish allow-list. General/Custom
  document defaults and their shared numeric inheritance are explicit.
- Tests exercise observable output and boundary failures, including technical wording, grammar, markup,
  swearing caps and actual rewrite dispatch. The reviewer independently observed 67 profile tests pass,
  exit 0, and a nested MCP smoke call succeed.

## Related follow-ups

| Opportunity | Concrete benefit | Why independent |
|---|---|---|
| Planned style/refinement rounds | Assess flavour density and semantic quality with independent writers/judges | The controls can be verified mechanically before that separate quality study. |
