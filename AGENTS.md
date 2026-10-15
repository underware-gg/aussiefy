# AGENTS.md

aussiefy: a deterministic, seeded rule engine (with optional Claude-powered modes) that rewrites plain English
as Australian slang, on three dials: level, vulgarity and embellishment.

Conforms to Agent-Ready Documentation Standard v1.0.0, Level 1.

## Documentation

Start at [docs/README.md](docs/README.md). Each layer has its own index:

- [User](docs/user/README.md): installing and using aussiefy.
- [Functional](docs/functional/README.md): reference for commands, dials, the dictionary format and the APIs.
- [Architecture](docs/architecture/README.md): how it works, with the
  [decision records](docs/architecture/decisions/README.md) and design reviews.
- [Contributor](docs/contributor/README.md): how to work in this repository. Read
  [plain CONTRIBUTING.md](docs/plain/root/CONTRIBUTING.md) before changing anything.

## Other files

- [CHANGELOG.md](CHANGELOG.md): release notes.
- [LICENSE](LICENSE), [LICENSES/](LICENSES/) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md): licensing.
- [docs/standards/](docs/standards/README.md): the documentation standard this project follows.
- [skills/aussiefy/SKILL.md](skills/aussiefy/SKILL.md): the Claude skill for using the toolkit
  (`.claude/skills/aussiefy` links to it).

Editable current guides and root documentation live in `docs/plain/`; public copies are generated.
See [publication instructions](docs/plain/contributor/documentation.md). Agent instructions and legal texts stay plain.
