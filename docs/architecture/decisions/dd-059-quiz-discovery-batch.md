# DD-059: batch quiz exclusion discovery through the ordinary lookup kernel

Status: implemented on dev, 15 November 2026. No public contract change.

The site's measured quiz cost was roughly four lookups. Quiz safety needs forward and reverse
lookup exclusions, with adaptive retries when a distractor is another supported reading. Replacing
those checks with similarity would change correctness; prefetching the whole pool would waste work.

Keep one request-local lazy batch and the existing adaptive algorithm. Scalar and batch paths share
one scoring/permissions kernel and top-50 ordering; the batch projects IDs before response cards and
imagery are built. Query results do not survive the call. No hosted charging rule enters the package.

Trigram index dot products use integer counts and equal scalar cosine scores. Cache fixed spelling
content by actual immutable pattern/gloss tuples, since in-memory derived dictionaries can retain an
identity. `_SPELLING_CORPORA=4` bounds retained fixed indexes across base/extension reloads; the separate
`_TERM_FORM_SETS=4096` cache covers query-independent form facts with headroom above the current corpus.
These are internal resource bounds, not client options or linguistic policy. The pre-existing unbounded
inflection cache is unchanged and is not covered by this new bound.

A 40-question warm, serial paired benchmark uses the same current dictionary/model and alternates
execution order against the frozen v4 commit. Full replies remain identical; the receipt records
roughly half the mean time. This is not a cold-start or hosted-service measurement. Tests verify exact
scalar ID equivalence across models/dials/protections, content-sensitive cache reuse, request-local
answers and absence of full-response lookups/near-card construction in the quiz batch.
