# Design review: multi-paragraph quotes and frozen refinement rounds

Date: 2026-10-16

Scope: canonical quote recognition, isolated engine/harness/yarn regressions, and the research driver's
local run selection and writer-origin binding. One independent reviewer covers all six concerns.

## Findings

The fresh writer study reproduced a shared defect: straight double quotes containing a blank line were
unrecognised, while curly double quotes already worked. The smallest fix changes the straight-double arm
of `QUOTED_RE`; existing held-span consumers now preserve the same document in translation and checks.
No lint exemption or separate quote parser is added. The digit/inch guard and single-quote/drawl forms remain.

The first round is preserved at commit `245ae75`: 19 submissions were replayed successfully before the fix,
one FOMC case was blocked, and no judge packets or quality scores were produced. The failed draft and actual
diagnostics are retained. A separate writer substring error is corrected in round two, without rewriting
round-one evidence. Independent review found no code/provenance findings; one README sentence was corrected
to say invalid reports can be fixed before their first successful collection. Review converged cleanly.

## What's done well

The correction lives at the shared rule. Positive and negative cases cover plain, strict Markdown and MDX,
lint, verification and actual yarn submission. Unquoted dialect, changed/dropped/duplicated quotes, inches,
adjacent quotes and apostrophised drawl retain their checks. The focused suite passed 238 tests.
The reviewer independently passed all 38 quote/study-integrity cases and verified the old frozen engine,
driver, 20 input sets, 40 anchors and source attribution for all 159 per-case artefacts.

Named local runs retain separate manifests and summaries. Optional writer-origin metadata is frozen with
issued packets. Unchanged briefs permit explicit carry-forward with new canonical tool execution; only the
FOMC brief changes, and its writer deliberately revisited the corrected draft. Historical anchors remain.

## Related follow-ups

The independent 20-case blind comparison follows the committed fix and a fresh round-two freeze. No parser
rewrite or blanket single-quote expansion is required for this reproduced defect.
