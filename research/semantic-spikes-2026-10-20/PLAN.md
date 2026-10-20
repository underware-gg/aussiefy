# Semantic research and implementation, 20 October 2026

Integration update: the user subsequently authorised integration into `dev`. The original isolation
constraints and feature-checkpoint evidence below describe the completed research phase. Publication
commit `70cde1f` and spacing fix `728e1a5` are retained; the semantic decision is DD-039 because DD-038
landed with publication. Combined review and verification are recorded in the
[dev integration review](../../docs/architecture/reviews/design-review-2026-10-20-dev-integration.md).

Baseline: a64c0d2. Work is isolated on semantic-refinement-20261020 in
`.worktrees/semantic-refinement`; do not change or merge into the shared dev checkout.

## Slices

1. **Research complete.** Research training-pair contradictions, concept sharing, and degree/complement ownership.
   Record reproducible evidence before selecting corrections. Keep model 1.3.0 and all frozen gates.
2. **Implemented, reviewed and verified.** Implement supported degree/complement corrections through shared semantic policy, dictionary
   certificates and behaviour tests. Preserve uncertain readings; no phrase-specific engine exceptions.
3. **Implemented, reviewed and verified.** Implement evidence-supported training/tooling corrections and broader contextual/verification
   coverage. A new fit requires a supported hypothesis and fresh isolated outputs; failed weights stay local.

Review each commit using software-design-review, fix findings, then pass Ruff and the full pytest suite.
Update remaining work after each slice. No release promotion, dev merge, or communication with the
separately managed website/design agent is authorised by this work.

## Verified checkpoint and remaining work

All three slices are implemented and reviewed. The final full run passed 3,311 tests with only the two
permitted local-corpus skips. Ruff, publication, provenance and the supported-settings changes budget pass.
This integrated feature-branch checkpoint includes both dependent reviews; dev and main are untouched.

- A controlled loss-objective experiment is separate next model research. Neither the rain-label fix nor
  a clean preflight establishes a cause for the three required failures. Retain bundled 1.3.0 and all gates.
- Further graded families, argument-bearing FED_UP targets, wider clause ownership, unsupported relations
  and arbitrary multi-edit verification need independent calibration/design. Current work does not claim
  those guarantees.
