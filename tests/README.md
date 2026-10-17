# Tests

Tests have one primary owner matching the documentation layers. A module can exercise other layers while
remaining with the layer whose contract it principally verifies; this avoids splitting fixtures or cases
just to match implementation modules.

| Layer | Primary responsibility |
|---|---|
| [User](user/README.md) | Command journeys, user file boundaries and installed-model configuration |
| [Functional](functional/README.md) | Domain behaviour, corpora and toolkit/surface contracts |
| [Architecture](architecture/README.md) | Dependency direction, deterministic outputs and model structure |
| [Contributor](contributor/README.md) | Dictionary acquisition/curation, docs, provenance, training and releases |

Run the full suite from the repository root with `python -m pytest -q`, or select a layer using
`python -m pytest -q tests/functional` (and likewise for the other folders). The
[contributor testing guide](../docs/contributor/testing.md) describes dependencies and the corpus checks.

Shared resources stay here:

- `conftest.py`: dictionary/translator fixtures, isolated home state and scripted Claude helpers.
- `_checks.py`: well-formedness checks shared by the public and local reference tests.
- `_pins.py`: the test-only pin hook, an engine observer that forces a pick or leaves out a garnish, for
  whole re-renders the changes builder is checked against.
- `fixtures/`: synthetic acquisition inputs and frozen historical target-wording anchors; the latter
  preserve the Gettysburg benchmark denominator independently of dictionary prose.
- `corpus/`: golden, public/licensed and ignored local reference inputs.

No production behaviour or golden data changes with this layout. Test module basenames are unchanged;
historical decisions/reviews use their original flat paths, whose current locations are in these indexes.
Only the two local-corpus cases in `functional/test_local_reference.py` may skip during promotion; the
release checker uses that exact path rather than a folder or wildcard exception.
