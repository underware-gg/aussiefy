# Ingest corpus sources

The common ingestion command replaces the old one-off reference and Interfold fetch scripts:

```sh
aussiefy dev ingest tests/corpus/remote.yaml
aussiefy dev ingest tests/corpus/everyday/interfold.yaml --force
```

A YAML manifest has `out` (relative to its directory), optional `defaults` and an `items` list. Each item has a
filename stem `name` and either a URL or a repository `path` with `repo` / `ref`. HTML becomes readable
paragraphs; optional paired `start` / `end` markers select an excerpt. Raw Markdown/MDX/text files retain
their source bytes, including line endings. Metadata such as title, licence and excerpt declarations stays
in the manifest. Existing files are kept unless `--force`; `--ref` overrides both default and item pins.

Names and repository paths cannot traverse directories; output filenames must be unique. Each fetched page
uses the shared home cache and atomic persistence. Failed pages are reported individually, complete previous
files survive interrupted writes, and a repeated run can recover. Symlinks/directories are rejected as page
outputs. The dictionary acquisition command `dev scrape` separately enforces the reference-only source
policy; generic corpus ingestion does not establish permission to extract or redistribute a source.

Ingesting a source does not establish redistribution rights. Remote-only manifests write into ignored local
storage; committed corpus needs the [provenance gate](licensing.md). The 15 pinned Interfold MDX pages retain
LGPL attribution, while Rockwell/Kieran sources and full research exports remain local.

Tests: [conversion and manifest rules](../../../tests/contributor/test_ingest.py),
[shared fetch/cache recovery](../../../tests/contributor/test_fetch_interfold.py).
