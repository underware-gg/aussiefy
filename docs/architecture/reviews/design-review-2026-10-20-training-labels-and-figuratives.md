# Design review: training labels and figurative predicates, 20 October 2026

Status: Applied focused review converged; integrated verification passed.

## Findings

No remaining findings in the applied diff. One draft-review finding is corrected: unsupported nonterminal exclusions were rejected even for concepts
without targets. The parser now skips empty target sets before shape validation. Tests cover both active
generation refusal and guard/held-out abstention. No model, recipe, cutoff or reference label changes.

## What's done well

The canonical matcher owns exclusion operators and tokenisation. Complete trigger ownership corrects the
rain contradiction without globally deleting inconvenient negatives. Audits report exact conflicts and
fail before model construction. Standalone in-batch probes and raw-reader scores distinguish demonstrated
signals from causal hypotheses. Figurative meaning and object preservation reuse existing dictionary
triggers, captures and shared eligibility across discovery and automatic surfaces.

## Related follow-ups

| Opportunity | Benefit | Why independent |
|---|---|---|
| Controlled loss experiment | Test competing in-batch labels against frozen gates | Clean pair generation does not establish model-quality improvement |
| Argument-bearing FED_UP target | Translate more annoyance predicates fluently | Current preservation and discovery are sound without a new term |

Final integrated checkpoint: **3,311 passed, two permitted local-corpus skips**. Ruff, explicit research
Pyflakes, publication, provenance/licences and the supported-settings changes budget all passed.
