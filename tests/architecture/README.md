# Architecture tests

Dependency direction, deterministic golden outputs and bundled-model structure.

Run from the repository root:

```sh
python -m pytest -q tests/architecture
```

| Module | Primary responsibility |
|---|---|
| [test_engine_hooks.py](test_engine_hooks.py) | Pass observer, render-at-spot, phonetic trace and garnish replay leave output unchanged |
| [test_golden.py](test_golden.py) | Exact seeded translation outputs |
| [test_layers.py](test_layers.py) | Package dependency direction and I/O boundaries |
| [test_static.py](test_static.py) | Bundled tokeniser, vectors, metadata and required senses |

Shared fixtures, corpus inputs and helpers live at [tests root](../README.md).
