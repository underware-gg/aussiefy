# aussiefy documentation

aussiefy rewrites plain English as Australian slang, with independent level (1-5), vulgarity (0-3) and
embellishment (0-2) controls. Genre sets the default embellishment and the form the voice follows. This is the front door to its documentation, which is organised in four layers, each with
its own index. It follows the [Agent-Ready Documentation Standard](../standards/agent-ready-documentation.md)
v1.0.0, at Level 1.

## Layers

| Layer | What it covers |
|---|---|
| [User](user/README.md) | Installing aussiefy and getting things done with it: translating, the dials, the Claude modes, using it from an agent |
| [Functional](functional/README.md) | Reference: what every command, option, dial, data file and API does, and the tests that pin that behaviour |
| [Architecture](architecture/README.md) | How it works and why: the pipeline, the package layers, determinism, the decision records and the design reviews |
| [Contributor](contributor/README.md) | How to work on it: setup and checks, testing, growing the dictionary, and releases |

## Other project files

- [README.md](root/README.md): the project's landing page.
- [CONTRIBUTING.md](root/CONTRIBUTING.md): the contributor layer's landing page, with the baseline rules.
- [CHANGELOG.md](root/CHANGELOG.md): what changed in each release.
- [LICENSE](../../LICENSE): the MIT licence for aussiefy. [LICENSES/](../../LICENSES) holds the full Apache-2.0 and
  MIT texts for bundled third-party material.
- [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md): attribution and changes for the bundled embedding model.
- [standards/](standards/README.md): the documentation standard this project follows.

Current guides are edited in this plain tree and published at stable public paths. See
[documentation publication](contributor/documentation.md).
