# Status and known limitations

- **The frame checker is heuristic.** Expect occasional misfires on unusual syntax. Every one is visible in
  [explain mode](explain.md), and most are fixed by tightening a trigger pattern in the data rather than the
  code. The hand-written frame checker now uses a small bundled POS model for noun/verb context;
  [DD-016](../../architecture/decisions/dd-016-reconcile-source-capabilities.md) records its offline boundary.
- **The LLM modes have not been run against the live API.** Tagging, `--surface`, `--rewrite` and yarn mode
  are tested with fake clients. The yarn workflow itself has been exercised by agents through its research CLI
  (`research/retellings-2026-10-11/yarn_tools.py`), which shares yarn mode's brief and tools.
- **The seed source has not been scraped.** The original build recorded network restrictions reaching
  learnconversations.com; that historical failure is not a current connectivity assessment. The scraper has
  synthetic fixtures, and the hand-curated dictionary and later research rounds use our own glosses.
  Acquisition remains a separate task: see [data acquisition](../contributor/data-acquisition.md).
- **Waltzing Matilda still needs exact edition verification.** Its lyrics have not been compared with an
  accessible scan of Cowan's 1903 sheet music. The Gettysburg fixture was checked on 2026-10-15 against the
  [Library of Congress's standard Lincoln Memorial transcription](https://www.loc.gov/exhibits/gettysburg-address/ext/trans-nicolay-inscribed.html):
  wording matches after documented punctuation/case and word-joining normalisation. The fixture's existing
  typography is retained; see `tests/corpus/reference/SOURCES.yaml`.
- **Fidelity and lookup remain heuristic.** Explicit name aliases avoid inferring replacements inside proper
  names, but sentence-initial names can still escape extraction. Slot/inflection matching and negation anchors
  fix the reproduced toolkit cases; they do not solve general negation or sense disambiguation. For example,
  `not out of the question` can still offer refusal phrases. Review suggestions in their actual sentence.
- **Mechanical acceptance does not establish retelling quality.** The first fresh 20-text blind comparison
  scored meaning 4.95/5 but register 2.00/5: eligible prose was too restrained. All deterministic checks
  passed. A further writer revision under contract-aware evaluation scored meaning 4.95/5 and register
  4.65/5, with some high-level prose still too light and a minor forecast narrowing. The packet protocol
  and judges changed; those rounds do not establish a causal engine improvement. See
  [the findings](../../../research/document-refinement-2026-10-15/FINDINGS.md) for raw results and limits.
- **The bundled embedding model lags the dictionary.** `aussiefy embedder status` reports the shipped model
  (aussie-static 1.2.0) as `stale` after the later research rounds; the next version is described in
  `training/README.md`. The 2026-10-15 offline check passes 33/33 required references but retains 16 known
  failures. Current gap-fill precision remains below the 90% bar, so default automatic filling stays off.
  Default translations are unaffected, since the engine does not use it unless asked.
