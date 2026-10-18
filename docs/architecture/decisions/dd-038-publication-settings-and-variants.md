# DD-038: Publication settings live in one place, and a host can export the docs at its own vulgarity

Status: Accepted

Date: 2026-10-18

Extends: [DD-017](dd-017-authoritative-plain-documentation.md)

## Context

The publisher read its translation settings from `docs/publication.yaml`, then refused any that didn't equal a
copy written into `scripts/publish_docs.py`. The settings notice on every page was written out by hand too, as
Swaggie, Dinkum and Dad. So the code held the same settings in three places, and the repository could only
publish at Dad.

The aussiefy website hosts the docs in two site voices. Dad must match the repository's own pages. Tradie uses
the same settings with tradie vulgarity, plus a small `document_config` overlay: `infix` added to the garnish
list and `profile.swearing.exclaim` set to 0.4. The docs sources and the publisher aren't in the wheel, so the
website builds from a checkout of the tagged release. Its generator is a separate program that also imports
`aussiefy`.

## Decision

`docs/publication.yaml` is the only copy of the publication settings that the publisher reads. Its translation
block must give every setting publication fixes: level, vulgarity, seed, embellishment, document type and
`document_config`. Everything else follows the package's defaults. The publisher checks that the level and seed
are integers and that the package's own policy accepts the settings, so a bad `document_config` key is refused
with the package's message. Vulgarity and embellishment are held by their stop names.

The notice comes from the settings. Each stop's label is in an explicit table covering all twelve stops
("Blow-in", "Uncle Bob"). A stop with no label is refused, and a test holds the table to the package's stops.

**The host contract is a command, run in its own process from the checkout:**

```sh
python scripts/publish_docs.py export --root CHECKOUT --out DIR [--vulgarity V] [--overlay FILE]
```

- It applies the vulgarity and merges the overlay (YAML or JSON) onto the yaml's `document_config`. Maps merge
  key by key; anything else, a list included, replaces, as `document_config.profile` overrides do (DD-021). The
  merged settings go through the same checks as the yaml.
- It writes every page into `DIR` at its public path. `DIR` must be new or empty, and outside the repository.
- It refuses to run unless the `aussiefy` it imported is the checkout's own package. Run in-process next to
  another copy, the publisher would build with whichever copy was imported first.
- It prints a JSON manifest:

```json
{"settings": {"level": 5, "vulgarity": "tradie", "seed": 0, "embellishment": "dinkum",
              "document_type": "general", "document_config": {"...": "the merged overlay"}},
 "documents": [{"source": "docs/plain/root/README.md", "output": "README.md"}],
 "kept_plain": ["docs/architecture/decisions/dd-001-no-nlp-dependency-in-the-core.md"]}
```

An overlay that adds to a list carries the whole list. The host builds it from the yaml's list, which a plain
export's manifest reports. `export()`, `with_settings()`, `kept_plain()` and `manifest()` implement the command.

**The host rewrites links on its own Markdown tree.** The exported pages keep the repository's relative links,
each relative to its page's output path. The host resolves each destination against that path. The target is
then exactly one of four things:

- a `documents` output: the host's page for it
- a `documents` source: the plain counterpart, linked from each page's notice
- a `kept_plain` document: an ADR, a historical review or the copied standard, served plain
- any other path: a repository file

Fragments, queries and external links carry through unchanged. The host rewrites the links its own Markdown
renderer finds, so the package needs no knowledge of the site's URLs and no second copy of the link grammar. A
test holds every Markdown document under `docs/` to exactly one of the first three.

The repository's own `generate` and `check` are unchanged: they publish at the yaml's settings, Dad today.

## Consequences

- Changing a publication setting needs no code change, and the notice follows it. The contributor guide also
  describes the current choices, so it is updated in step. The repository's published pages came out
  byte-identical when this landed.
- An export at the yaml's own settings equals the repository's pages, so the website's Dad pages match GitHub.
- The host runs the command with an interpreter that has the package's dependencies, such as the pinned wheel's
  environment. The checkout's package, first on the script's path, is the one that runs.
- A new dial stop needs a notice label before publication can name it.

Tests: [publication](../../../tests/contributor/test_publish_docs.py).
