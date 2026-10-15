# DD-011: Copyrighted texts stay local; only pointers and excerpts are committed

- **Status:** Accepted
- **Date:** by 2026-10-11, the retellings research (`research/retellings-2026-10-11/`), and in place by v0.1.0
  (2026-10-12). Recorded retrospectively on 2026-10-13.

## Context

Testing against real, well-known texts finds problems synthetic sentences don't, and some of the most useful
texts are still in copyright (for example Ginsberg's "Moloch", or Mackellar's "My Country", in copyright in
Australia until the end of 2038). An Aussified retelling of a copyrighted text is a derivative of it. The
repository is meant to be public.

## Decision

Copyrighted texts are never committed. `tests/corpus/remote.yaml` holds pointers to public copies, and
`scripts/fetch_reference_texts.py` saves the excerpts to `tests/corpus/local/`, which is gitignored apart from
its README. Retellings of those texts stay there too; the repository commits at most a short excerpt, under a
notice header. Committed source texts must be the project's own work or public domain in both Australia (author died
before 1955) and the US.

## Consequences

- Contributors can test against copyrighted texts privately, and `tests/test_local_reference.py` skips when
  the folder is empty, so the suite passes on a fresh clone.
- Results on local texts can't be reproduced from the repository alone; each contributor fetches their own copy.
- The public corpora (`tests/corpus/reference/`, `tests/corpus/classics/`) record each text's provenance.

The working rules are in [tests/corpus/local/README.md](../../../tests/corpus/local/README.md).
