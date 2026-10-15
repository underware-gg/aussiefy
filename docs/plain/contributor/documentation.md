# Editing and publishing documentation

Edit the linked source under `docs/plain/`, rather than its generated public counterpart. The publication
map in `docs/publication.yaml` pairs each authoritative source with its stable public destination. Root
sources live under `docs/plain/root/`; other guides mirror the public documentation layers.

```sh
python scripts/publish_docs.py generate
python scripts/publish_docs.py check
```

Generation uses the strict Markdown adapter at Swaggie (5), Dinkum (1), Dad (1) and seed 0, with the offline
ngram fallback. It explicitly selects General, protects Technical vocabulary through `term_domains`, and
disables formal-sentence rework. Every published page has the same settings notice and a link to its own plain
counterpart: “Prefer docs that are as dry as a dead dingo's donger?” It preserves headings, tables, links, code and displayed command outputs. The generated notice
links back to the editable source. All outputs are derived from the current dictionary and publication map;
their exact bytes are checked before promotion. Strict Markdown units share document-wide choice and garnish
state; garnish is suppressed on incomplete sentence fragments, keeping flavour out of code/link boundaries.

Relative links in a plain source point to other plain sources where available, or to the actual ungenerated
repository file. Publication remaps those destinations back to their public paths. External destinations and
fragments stay unchanged. Both trees have checked file targets and anchors; no parsed document is rendered
back into Markdown.

During development, a plain-source edit may leave published prose stale. The ordinary command/output tests
read each authoritative current source once, along with ungenerated current docs and skills. Run generation
to preview the published result, and review its readability before committing a publication update.
Promotion requires fresh outputs, valid links and executable examples.

AGENTS/CLAUDE instructions, legal notices and licence texts, the copied standard, ADR records and historical
reviews stay plain. Their current indexes may be published. Training, research and corpus READMEs stay at
their existing paths. Publication does not recursively translate `docs/plain/`.

Add a new current guide to the explicit map. A missing mapped input, an unmapped plain source, a stale or
unexpected generated output, or a broken link fails with its path and a correction. Commands resolve the
repository from the script location, and support `--root PATH` for local fixtures. No LLM call is made.

Tests: [publication](../../../tests/contributor/test_publish_docs.py),
[command examples](../../../tests/contributor/test_docs.py),
[Markdown preservation](../../../tests/functional/test_markdown.py).
