# Licensing and provenance

The project uses MIT for its own material and declares Apache-2.0 and MIT for its bundled model. The
reviewed declarations are in [third_party.yaml](../../../third_party.yaml); generated attribution is in
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md), with canonical texts in [LICENSES/](../../../LICENSES).
Installed pip dependencies are not vendored and are outside this registry.

## Check and regenerate

Install the dev extra, stage new declarations/files, then run:

```sh
python scripts/notices.py check
python scripts/notices.py generate     # after reviewing a declaration change
python scripts/notices.py check --wheel
```

`check` uses `git ls-files` and current file contents; ignored local texts are never read. It also runs in
pytest. `generate` validates the evidence before replacing the notices. Neither command fetches evidence
from the network. An error names the broken declaration or file; stale notices name the generation command.

`check --wheel` additionally builds from an isolated copy of tracked files, using installed build tools
without build isolation or dependency downloads. It compares the wheel's actual package files, licence
bytes, `License-Expression` and `License-File` metadata with the reviewed inputs. Promotion runs this on its
exact committed checkout. Build outputs never enter the working tree. Ordinary pytest tests wheel inspection
with fixture archives and does not build a wheel.

## Bundled components

Each component declares paths, upstream licence/copyright evidence, changes and metadata bindings. Changing
the model name/version or pinned base requires reviewing those declarations. The WordNet entry is a
training-only credit, bound to the existing metadata, with a link to its licence; its database does not ship.
Digests bind both the project licence and canonical third-party texts to their reviewed bytes; changing a
digest requires reviewing its evidence.

Every packaged code/data file needs exactly one component or first-party claim. The registry's package/data
coverage follows the setuptools configuration in `pyproject.toml`; unsupported layouts fail explicitly.
Adding vendored code means replacing its first-party claim with a component declaration, not assuming all
files under the package are automatically the project's own work.

## Corpus and research texts

Tracked `.txt`, `.html` and `.md` files under `tests/corpus/`, `tests/fixtures/` and `research/` need exactly one
provenance claim. Existing reference/classics manifests own their records; rows declare a file, title,
author, licence and notes. A declared file must be tracked and present. Narrow first-party claims describe
synthetic fixtures, project analyses and renderings of public-domain/own texts; a new research directory is
not implicitly first-party.

Copyrighted works without confirmed redistribution permission stay in ignored `tests/corpus/local/`, which
tracks only its README. [remote.yaml](../../../tests/corpus/remote.yaml) explicitly declares an `excerpts` list
for each work: `[]` means no committed excerpt. The previously audited Howl retelling has one exact path,
its required notice header and a 256-word cap **including the header**. The gate enforces that existing
decision; it does not approve new exceptions. Other files named for a remote-only work fail as a backstop.

The everyday groups add manifests requiring title, author, licence, evidence and source URL. Their
[README](../../../tests/corpus/everyday/README.md) records extraction changes and MIT permission notices; CC
licence links are in their rows. `remote_manifests` accepts a list-manifest path, or a mapping with `file`,
`rows` (the top-level collection key) and `name_field` (default `name`). The remote manifests use
`items` and `name`, sharing the ingestion format. Interfold is now declared through the licensed corpus
manifest; the remaining remote-only works retain `excerpts: []` and contribute stems to the copy backstop.
US-only public-domain evidence does not settle Australian redistribution status: the Rockwell and Kieran
passages remain local with remote pointers until that question is resolved.

Coverage and name checks cannot infer authorship or detect every embedded quotation; declarations and licence
evidence still require human review. Historical short quotations recorded in the audit are unchanged.

Every entry in `aussiefy/data/entries/scraped.yaml` names an HTTP(S) source. Its inline and supplemental URLs
must pass the same reference-only policy as the scraper. This does not turn a permitted scraping host into a
redistribution licence: wording and attribution still need review.

The gate's design is recorded in [DD-014](../../architecture/decisions/dd-014-reviewed-provenance-gate.md).

## Source-linked research and POS

The completed source integration pins `Rob-Morris/aussiefy@c0177d7`, extending the initial `95036e1` import. The English POS implementation and
weights retain Matthew Honnibal/NLTK MIT attribution; weight bytes are bound to checked metadata. The 15
Interfold MDX inputs have pinned LGPL-3.0-or-later evidence in
[their manifest](../../../tests/corpus/everyday/interfold-provenance.yaml).

[research/PROVENANCE.yaml](../../../research/PROVENANCE.yaml) links each source-bearing research group to its
redistributable corpus originals. Derived originals, retellings, packets and logs retain source attribution;
short evidence in sanitised candidate exports is declared separately. Four research passes' Rockwell/Kieran
artefacts and unsanitised mixed exports remain ignored locally. The GNU texts in `research/licences/` support
corpus/research attribution and do not alter the package wheel's MIT/Apache licence metadata. The gate rejects
unknown/local sources, empty research patterns, overlapping ownership and changed declared digests.
