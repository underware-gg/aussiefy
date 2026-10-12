# AGENTS.md

Guidance for coding agents working in this repository.

## Project

aussiefy rewrites plain English as Australian slang. The engine is a deterministic, seeded rule pipeline in
`aussiefy/` (parse, detect, select, realise, garnish); the slang itself is data in `aussiefy/data/*.yaml`.
User-facing docs: `README.md` (short) and `docs/usage.md` (full guide).

## Setup and checks

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest -q
```

Both must pass before a commit. If a change intentionally alters translations, regenerate the golden corpus
with `scripts/regen_golden.py` and review the diff rather than accepting it blindly.

## Conventions

- Never hard-code slang in the engine. Every phrase is a dictionary entry and every level is a profile in
  `aussiefy/data/profiles.yaml`.
- Output must stay deterministic: random choices are seeded rolls keyed by context, so the same text, level
  and seed always give the same result.
- Copyrighted reference texts are never committed: they live in `tests/corpus/local/` (ignored) and are
  fetched with `scripts/fetch_reference_texts.py`.
- Record user-visible changes under `[Unreleased]` in `CHANGELOG.md` as they land.

## Branches and releases

Work happens on `dev`. `main` holds releases only: each is one squashed, tagged `vX.Y.Z` commit made by
`scripts/promote.py`, which sets the version, checks the tree, changelog, ruff and tests, then commits and tags.
Don't commit to `main` directly.

## Agent skill

`skills/aussiefy/SKILL.md` is a Claude skill for using the toolkit; `.claude/skills/aussiefy` symlinks to it.
