# Contributor tests

Maintainer acquisition, dictionary curation, provenance, documentation, training and promotion tools.

Run from the repository root:

```sh
python -m pytest -q tests/contributor
```

| Module | Primary responsibility |
|---|---|
| [test_docs.py](test_docs.py) | Executable current documentation examples |
| [test_fetch_interfold.py](test_fetch_interfold.py) | Local-only pinned MDX acquisition and save recovery |
| [test_fetch_reference.py](test_fetch_reference.py) | Local-reference HTML extraction and markers |
| [test_harvest.py](test_harvest.py) | Dictionary fragments and candidate harvesting |
| [test_notices.py](test_notices.py) | Tracked provenance, notices and wheel inspection |
| [test_publish_docs.py](test_publish_docs.py) | Source/output placement, link/anchor integrity and deterministic publication |
| [test_refinement_study.py](test_refinement_study.py) | Frozen writer evidence, canonical acceptance replay and immutable blind study packets |
| [test_promotion_github.py](test_promotion_github.py) | gh REST request bodies, pagination and enforcement diagnostics |
| [test_promote.py](test_promote.py) | Pinned release checks, server enforcement, interruption recovery and two local PR release cycles |
| [test_rounds_preservation.py](test_rounds_preservation.py) | Metadata, guards, reviewed second senses and explicit fixes across reapplication |
| [test_rounds.py](test_rounds.py) | Research verdict planning and apply/replay |
| [test_scrape.py](test_scrape.py) | Dictionary acquisition, tagging and review pipeline |
| [test_seed_intake.py](test_seed_intake.py) | Declared encodings, seed curation completeness and precise new senses |
| [test_staging.py](test_staging.py) | Maintainer staging format and source-policy boundaries |
| [test_train_embedder.py](test_train_embedder.py) | Trainer CLI and recipe handling |
| [test_judge.py](test_judge.py) | Blind packets, report shapes, evidence and tally |
| [test_ingest.py](test_ingest.py) | Manifest validation and shared conversion |
| [test_fourth_pass_harness.py](test_fourth_pass_harness.py) | Fourth-pass research workflow contracts |
| [test_third_pass_harness.py](test_third_pass_harness.py) | Third-pass agent payload and workflow contracts |

Shared fixtures, corpus inputs and helpers live at [tests root](../README.md).

- [Contextual curation](test_contextual_curation.py): complete follow-up decisions and valid promotion targets.
