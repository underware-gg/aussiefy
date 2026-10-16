# Contributing to aussiefy

These are the baseline rules for working on aussiefy, for people and agents alike. The rest of the contributor
documentation (testing, data acquisition, releases) is indexed in
[docs/contributor/README.md](../contributor/README.md).

## Set up

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

The `dev` extra includes the test dependencies and isolated wheel-build tools, plus a TOML reader on Python
3.10, so the interface, scrape and embedding checks run rather than skip. It includes the optional API SDK for
offline HTTP tests. Promotion checks run too. Add `embeddings` when working on that optional backend. Only the two local copyrighted-corpus tests may skip in a release.

## Check

```sh
ruff check .
python -m pytest -q
```

Both must pass before a commit. The suite includes golden outputs and the reference texts, and can take several minutes. If a change intentionally alters translations, regenerate the golden corpus with
`python scripts/regen_golden.py` and review the diff rather than accepting it blindly (see
[testing](../contributor/testing.md)).

The suite also checks tracked provenance and generated third-party notices. Stage new files/declarations
before checking; promotion checks the exact committed checkout and additionally inspects a built wheel.
See [licensing and provenance](../contributor/licensing.md) for the commands and evidence requirements.

## Documentation

Edit the authoritative sources under `docs/plain/`. Public Markdown is generated: run
`python scripts/publish_docs.py generate` to preview, and `check` before promotion. Runnable examples are
checked against plain sources while development outputs may be stale. See
[documentation publication](../contributor/documentation.md).

## Conventions

- **Never hard-code slang in the engine.** Every phrase is a dictionary entry and every level is a profile in
  `aussiefy/data/profiles.yaml` ([DD-002](../../architecture/decisions/dd-002-slang-is-data.md)).
- **Keep output deterministic.** Random choices are seeded rolls keyed by context, so the same text, level and
  seed always give the same result ([DD-003](../../architecture/decisions/dd-003-deterministic-context-keyed-rolls.md)).
- **Respect the layering.** The engine and the dictionary import nothing from the toolkit, the LLM modes, the
  surfaces or the maintainer tools ([package layout](../architecture/package-layout.md)).
- **Change every surface together.** A toolkit parameter has the same name and default in the Python API, the
  CLI, the MCP server and yarn mode's tools; `tests/functional/test_interfaces.py` checks this.
- **Keep remote-only full texts local.** Copyrighted full texts without confirmed redistribution permission
  live in the gitignored `tests/corpus/local/`. Licensed corpus material needs provenance and attribution;
  the previously audited Howl excerpt has an exact declared path, notice header and word cap. New exceptions
  need review (see [licensing](../contributor/licensing.md) and [local texts](../../../tests/corpus/local/README.md)).
- **Keep the docs in step.** Update the documentation with the change that affects it, and record a new
  architectural decision as a decision record in
  [docs/architecture/decisions/](../architecture/decisions/README.md).
- **Record user-visible changes** under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md) as they land.
- **Write Australian spelling** in documentation and user-facing messages (colour, organise, licence as a
  noun). Data is different: trigger patterns and `aussiefy/data/dialect.yaml` must match plain and US
  English as written.

## Branches and releases

Work happens on `dev`. `main` holds releases only: each is one squashed, tagged `vX.Y.Z` commit made by
`scripts/promote.py`. Don't commit to `main` directly. The procedure is in
[docs/contributor/releasing.md](../contributor/releasing.md).
