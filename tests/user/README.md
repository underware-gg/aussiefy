# User tests

Installing, configuring and using the commands through their user-facing boundaries.

Run from the repository root:

```sh
python -m pytest -q tests/user
```

| Module | Primary responsibility |
|---|---|
| [test_cli.py](test_cli.py) | Command journeys, output and exit codes |
| [test_cli_boundaries.py](test_cli_boundaries.py) | User-supplied files, settings and invalid arguments |
| [test_models.py](test_models.py) | Installed-model setup, configuration and selection |

Shared fixtures, corpus inputs and helpers live at [tests root](../README.md).
