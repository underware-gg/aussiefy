# Original-inventory source audit: complete coverage

All twelve ledgers together cover exactly **1,254 original entries**, with no missing or duplicated IDs.
The baseline is `5d1fb049cd3d9e68295d637563a0c87ea418764c`. The parent independently rebuilt its entry-ID
set from the committed dictionary files, compared the ledger union, and retained ledger hashes and the
sorted-ID digest in [audit-coverage.json](audit-coverage.json).

| Allocation | Entries | Cumulative original coverage |
|---|---:|---:|
| 18 October | 130 | 130 |
| 19 October initial | 30 | 160 |
| Batch 2 | 60 | 220 |
| Batches 3–10, eight disjoint allocations | 960 | 1,180 |
| Batch 11 | 74 | 1,254 |

Batches 3–11 received independent cross-reviews. Corrections included source misattributions and over-narrow
readings: corrected notes retain broader accepted senses rather than turning one source's example into a
universal restriction. The ledgers distinguish direct edited references, primary contexts, components,
whole constructions, source families and access limitations. Failed searches alone do not establish
fabrication and have not prompted new automatic gates or removals.

This is original-inventory research coverage, not certification of every trigger, inflection, register,
frequency, origin claim or output. Later dictionary additions have their own scoped provenance and are
outside the frozen 1,254-ID denominator. Runtime recommendations and proposed source-sidecar additions
remain separate from research completion; consult the implementation plan and individual integration
records before treating a recommendation as an applied engine change.
