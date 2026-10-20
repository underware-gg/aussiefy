# Design review: publication and semantic dev integration, 20 October 2026

Status: Independent combined review converged; full integrated verification passed.

## Findings

No remaining integration findings.

The integration retains publication commit `70cde1f`, the separate two-file spacing correction `728e1a5`
and semantic feature commit `cc8077e`. Runtime code and dictionary changes merge without conflict.
The two decision indexes conflict because the independent branches both allocated DD-038. Publication
already landed on dev; the incoming semantic record is DD-039, with its body preserved and links updated.
Plain indexes remain authoritative and their public copies are regenerated.

No archived prototype is restored. The dirty-worktree assessment found its useful implementation and
all 530 new source-reference pairs already integrated or superseded. Exact historical contents remain
on the separate orphan branch `archive/dirty-worktrees-20261020` at `a2d70b5`; that branch is not a merge
target. The research plan and report distinguish the measured feature checkpoint from this integration.

## What's done well

Publication settings remain in their existing configuration, while modifier composition and candidate
eligibility remain shared engine policy. Neither feature introduces a second copy of the other's rules.
The integration preserves the typo as its own commit and keeps research measurements bound to their
original inputs. Bundled model assets, the training recipe and required references remain unchanged.

## Related follow-ups

The independent training-objective experiment, additional graded-family calibration, argument-bearing
FED_UP targets, broader clause ownership and the existing give-best binding limit are outside this
integration. No release or main promotion is included.

## Verification

The publication-plus-spacing checkpoint passed 3,273 tests with two permitted local-corpus skips;
Ruff, publication and provenance checks passed before the tiny docs commit.

The final combined run passed **3,328 tests with two permitted local-corpus skips in 933.57 seconds**.
Ruff, explicit research Pyflakes, publication freshness, provenance/licence and whitespace checks passed.
A real default CLI export matched all **41 generated repository pages byte-for-byte**; its manifest
includes both decision records and this review as kept-plain documents. All 395 captured runtime, data,
tooling, test and plain-source inputs remained unchanged through the successful full run.

Independent review verified semantic runtime/tool/test changes against `cc8077e`, publication code and
tests against `70cde1f`, and all bundled model assets, recipe, references and the canonical 1.3.0 report
against `a64c0d2`. The semantic ADR body is unchanged by renumbering. Historical feature performance
measurements retain their own checkpoint; this integration does not claim a new timing benchmark.
