# Historical dirty-worktree archive

This orphan branch preserves only the dirty contents of three obsolete Aussiefy prototype worktrees.
It is an archive, not a runnable package or a merge target. Do not merge or cherry-pick it into `dev`.
There is no missing implementation to recover from these snapshots into the assessed `dev` checkpoint.

## Scope and recovery

Archive branch: `archive/dirty-worktrees-20261020`.
All three source worktrees are based on `2687d7ff96d8019522eba9414498ae9c51927353`.
Assessment target: `a64c0d248cc6d1fd6e870cb5284f1e7005b5d6af`.
The separate semantic-refinement feature branch and documentation-publishing rebase are excluded.
`dev`, `main`, their working files and their refs were not changed by this archive operation.

| Original worktree | Tracked dirty files | Untracked files | Total snapshots |
|---|---:|---:|---:|
| `semantic-effects-20261019` | 42 | 3 | 45 |
| `semantic-listener-20261019` | 35 | 6 | 41 |
| `sourced-senses-20261019` | 28 | 4 | 32 |
| Total | 105 | 13 | 118 |

Each `snapshots/<name>/files/` contains the exact complete dirty version of every modified or untracked
file, namespaced to preserve differences between prototypes. Each `tracked.patch` is the original
`git diff --binary HEAD`, including tracked changes only. Manifests record SHA-256 digests, byte counts,
original paths and file permissions. The base commit remains reachable through normal development history.

To recover a prototype without disturbing another checkout, export the recorded base into an empty
scratch directory, apply that prototype's `tracked.patch` there with `git apply`, then copy only its
manifest-listed `untracked` files from `files/` to their original relative paths. Alternatively, the
complete archived dirty files can be overlaid on that base. Do not overlay these snapshots onto current
`dev`: they predate subsequent corrections. `reconstruction.json` records successful base-plus-patch
reconstruction and SHA-256 comparison of all 118 files before removal.

Ignored files were inventoried but excluded: Python/test/lint caches, generated egg-info and a generated
build/lib tree. No uncommitted model experiment, private reference corpus or independent research file
was present among those ignored files. Unchanged source files, model weights, local virtual environments
and the source repository's Git metadata are not included.

## Assessment

A read-only three-way comparison used each worktree's actual base-to-dirty delta, not just its branch
ancestry. No clean residual patch was found: 39 file versions/changes were identical or already
integrated, and 79 overlapped later integrated work. Source, tests, structured dictionary records and
plain documentation were then checked separately; overlap was not treated as proof of novelty.

- Narrator-opinion policy, candidate/garnish/lookup/writer enforcement and semantic-effect cards are
  integrated in `c891945`. Current development also has source-specific quantity effects and subsequent
  degree work; the prototype's narrower signatures/schema should not replace them.
- Listener/object possessives, mass/count handling, argument completion and source-derived sense splits
  are integrated in `11aa20c`/`c891945`, with additional protective-guard and coordinator fixes.
- All 530 distinct new entry/source-URL pairs across these prototypes are present in the assessment target.
- Every novel regression function is retained. Current listener tests add protective-guard coverage.
- The only omitted dictionary-trigger additions are the two own-form COOLIBAH triggers. They were
  deliberately removed because they rewrote already-Australian verse. Current code retains the precise
  `Eucalyptus coolabah` trigger; the corresponding old positive test was intentionally changed.
- The physical-solitude entry's loneliness contrast survives in notes, keeping its positive gloss clear
  for retrieval. This is a deliberate integration refinement, not missing dictionary work.
- Draft review statuses, old generated goldens and superseded settings descriptions are historical.
  In particular, the prototype's future mass-noun work was completed during integration.

The actual prototype reviews and their unfinished wording are preserved verbatim under `files/`.
They are not assertions about current development readiness. Current integration evidence is in the
assessment target's `docs/architecture/reviews/design-review-2026-10-19-{semantic-effects,sourced-extensions}.md`.
Independent software-design-review found no code, data or documentation intent requiring salvage.

## Verification and independent follow-ups

Four archived regression modules were run against an isolated copy of the assessment target:
230 passed, one old COOLIBAH self-rewrite expectation failed for the intentional reason above.
Replacing only that module with its integrated counterpart yielded 231 passes. No project tests,
cutoffs, fixtures or implementation were edited for this archive, and no new full-suite run is claimed.
The archive has no runtime or test harness; its preservation check is the 118-file reconstruction.

The existing `give best` object-binding availability follow-up remains recorded in the assessment target's
sourced-extensions review. It has no unmerged implementation in these worktrees. Wider semantic/model
research and the two current feature integrations remain independent work, outside this archive.

Project source is MIT-licensed; see LICENSE. Source links in copied dictionary data are references, not
copied external dictionary articles. Archived golden outputs include the existing public-domain reference
inputs and first-party retellings; their attribution and recorded provenance are retained in
[provenance/reference-SOURCES.yaml](provenance/reference-SOURCES.yaml). Generated translations are modified
retellings, not editions of their original source texts. Runtime models and private corpora are excluded.
