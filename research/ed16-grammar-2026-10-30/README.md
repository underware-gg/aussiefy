# ED16 measured source and grammar refinement

This is original project analysis and synthetic trial data, licensed under the repository's MIT licence.
No external source pages or copied definitions are included. This is not a new source-attestation round.

`selection.json` preserves the fixed 20-entry sample selected before curation: eight noun, six verb,
four predicate-adjective and two clause entries. Half of each stratum was selected for structural
complexity and half seeded-random (20261029). Difficult entries remain in the sample.

`pilot.json` retains each decision, annotation, positive sentence, contrast, settings and observed
rendering/candidate diagnostics. Thirteen entries receive count, state or following-boundary annotations;
seven retain unknown fields rather than invented contracts. All 20 have working positive renderings under their recorded settings.
The pilot discovered the friend-request boundary, now a shared lexical fence, and a possessive-binding
gap for archaic old pot. An explicit archaic-register trial distinguished the binding failure from the default register exclusion;
existing possessive source patterns now supply that binding without changing the register policy. The
reported failure is retained alongside the corrected result. Existing rendering handles the
party expression's explicit plural, internal arguments and self-regard variants.

The first review session records 189.36 seconds of gross agent wall time, including bounded diagnostics
and command overhead. Automated rendering time is recorded separately. Annotation writing, engineering,
test setup, interruption and review overhead are not a metered human-work study. Do not turn this into
a human per-entry estimate. For planning only, allow roughly **6–25 agent-hours** for an initial review
of the remaining 1,187 idioms, plus research, rulings and verification: this is a low-confidence allowance
of about 2–8 times the sample's gross linear review time, not a statistical confidence interval. The
18 straightforward entries and two corrected cases do not establish the cost of the difficult tail.

`exclusion-migration.json` records before/after patterns, every moved alternative, retained semantic or
argument restrictions, scopes, reasons and individually reviewed lexical units. Grouped fence records
share scope and reason. Former two-token exclusions deliberately become actual whole-phrase ownership:
this can release independent words that were incidentally within two tokens. It is not a byte-identical
parser reorganisation. Existing fence wording is preserved; new expressions have new scoped reasons.

The measured 36-entry grammar cohort uses unknown for unestablished adjunct combinations, rather than
adopting the spike's incomplete whitelist. Known incompatible direct objects and of-complements are
explicit. The 110 retired grammar fences are covered by source-role, existing mass-number or declared
active-event requirements. The three reserved-retiring expressions remain as other-sense fences, with
their original reasons, because output-event checks alone do not prevent a wrong meaning in lookup. Breakfast-idiom and down-in-the-dumps protections remain necessary.
`measured-cohort.json` retains that initial field review; the package data is authoritative where the
pilot adds annotations afterwards. `timing.json` retains three alternating baseline/current comparisons
on all 45 pinned inputs (41,721 characters): the median measured process-CPU ratio is 1.0131. This narrow
warm engine check found no material regression; it excludes dictionary loading and model-backed modes.
`golden-deltas.json` binds the 21 changed output/settings pairs without reproducing reference texts.

The retained [phase-B corpus](../../tests/corpus/ed16/README.md) has 704 cases: 661 negative exposure
checks, 42 controls (only 31 originally had an eligible word) and one argument-preservation case.
These are synthetic regression labels, not exhaustive inflections or certified naturalness scores.
