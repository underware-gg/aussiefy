# Status and known limitations

- **The frame checker is heuristic.** Expect occasional misfires on unusual syntax. Every one is visible in
  [explain mode](explain.md), and most are fixed by tightening a trigger pattern in the data rather than the
  code. The hand-written frame checker now uses a small bundled POS model for noun/verb context;
  [DD-016](../../architecture/decisions/dd-016-reconcile-source-capabilities.md) records its offline boundary.
  Dependent result constructions (`so … that`, `too … to`, `… enough to`) retain their operators and
  conservatively admit single-word predicate forms. Recognised coordinated predicates share that
  restriction. Comma-stacked synonyms require established following context; a relative-clause
  continuation, punctuation alone or hidden markup does not establish room for a stack.
  With an original, lint/verify flag a recognised predicate expansion before the source's unchanged
  `enough` tail when the surrounding sentence provides one unambiguous local pairing. They abstain
  without that evidence; this check does not establish grammatical correctness for arbitrary retellings.
- **The built-in API client has not been run against the live API.** Tagging, `--surface`, `--rewrite` and yarn mode
  are tested with fake clients. The yarn workflow itself has been exercised by agents through its research CLI
  (`research/retellings-2026-10-11/yarn_tools.py`), which shares yarn mode's brief and tools.
- **The seed listicle is discovery evidence, not dictionary authority.** It was acquired and reviewed on
  2026-10-17: 212 normalised candidates yielded ten additions, existing component coverage and explicit
  non-promotion decisions. Some creative comparisons remain conditional craft rather than executable
  meanings. See [the decisions](../../../research/maintenance-2026-10-17/seed-decisions.yaml) and
  [data acquisition](../contributor/data-acquisition.md).
- **Waltzing Matilda still needs exact edition verification.** Its lyrics have not been compared with an
  accessible scan of Cowan's 1903 sheet music. The Gettysburg fixture was checked on 2026-10-15 against the
  [Library of Congress's standard Lincoln Memorial transcription](https://www.loc.gov/exhibits/gettysburg-address/ext/trans-nicolay-inscribed.html):
  wording matches after documented punctuation/case and word-joining normalisation. The fixture's existing
  typography is retained; see `tests/corpus/reference/SOURCES.yaml`.
- **Fidelity and lookup remain heuristic.** Explicit name aliases avoid inferring replacements inside proper
  names, but sentence-initial names can still escape extraction. Slot/inflection matching and negation anchors
  fix the reproduced toolkit cases; they do not solve general negation or sense disambiguation. Review
  suggestions in their actual sentence; recognised source guards cover reviewed meanings, not all wording.
- **Mechanical acceptance does not establish retelling quality.** The first fresh 20-text blind comparison
  scored meaning 4.95/5 but register 2.00/5: eligible prose was too restrained. All deterministic checks
  passed. A further writer revision under contract-aware evaluation scored meaning 4.95/5 and register
  4.65/5, with some high-level prose still too light and a minor forecast narrowing. The packet protocol
  and judges changed; those rounds do not establish a causal engine improvement. See
  [the findings](../../../research/document-refinement-2026-10-15/FINDINGS.md) for raw results and limits.
- **The bundled embedding model can lag later dictionary corrections.** Shipped aussie-static 1.3.0 was
  freshly fitted against the reviewed c891945-era inputs; subsequent degree and source-audit changes make
  its exact dictionary fingerprint stale. The 33 required reference checks remain enforced. Fresh full-fit
  and export checks passed 33/33; evaluation retained the girl failure at 32/33. Known relevance/certainty
  problems remain; see [the bounded report](../../../research/semantic-model-2026-10-19/README.md).
  Default automatic gap filling stays off. This is separate from deterministic dictionary matching.
- **Conservative source corrections trade coverage for supported meaning.** General work/activity versus
  artwork or childbirth is not resolved automatically; yakka remains discoverable and available for
  explicit hard work. Unqualified asylum, den and ice box do not establish psychiatric/domestic/portable
  senses. Percy supports intransitive clause endings and supported adverbial tails, retaining other
  complements as written. Coordinated or ambiguous progressive objects can remain plain.
- **Degree and quantity checking cover reviewed families and mappings.** DRUNK and HUNGRY have reviewed
  source/target degree calibration; unknown ratings are not inferred from style intensity. Quantity approximation is explicit
  and preset-controlled, with bounded source/output checks. Local original-aware checks catch known
  incompatible grades, with ambiguity and simultaneous edits limiting coverage. It is not general fact checking.

- **Lookup is bounded meaning discovery.** Recognised heads, external polarity and reviewed degree can
  constrain lexical and model suggestions together. Unknown modifiers, subordinators and unsupported
  structure retain broader fallback; direct term discovery does not certify an in-place replacement.
  Figurative senses without corpus restrictions and unsupported-query model errors remain possible.
