# Verify a translation

`verify(text, original=...)` checks any translation against its original, using the same level, vulgarity,
English, embellishment and extended-markup controls as lint. It is deterministic and requires no paid API.

```sh
aussiefy verify draft.txt --original original.txt -l 4 --embellishment dinkum
aussiefy verify draft.mdx --original original.mdx --markup mdx --json
```

Python `aussiefy.verify` and MCP `aussie_verify` return `ok`, the policy envelope, `problems` and `metrics`.
Problems are ordered by severity: critical (lost numbers, changed protected markup, empty output), major
(breaking the brief), minor (craft or an unmatched sentence), then info (coverage). `ok` means no critical or
major problem; CLI exit 1 reports failure. `--json` exposes the complete evidence.

Verification reuses lint and fidelity, then aligns original sentences against nearby windows of translated
sentences, allowing a retelling to split or merge them. This is a bounded heuristic, not a proof of meaning
or literary quality. It can miss wrong senses and cannot judge tone/flow; [the judge](../contributor/judging.md)
provides that separate evaluation. Optional suggestions are disabled during verification and yarn submission
to avoid an unnecessary full translation. Lint callers can similarly use `suggest=False` / `--no-suggestions`.

Contract tests: [test_verify.py](../../../tests/functional/test_verify.py).


Source-specific semantic effects are checked only with an original and an unambiguous local edit joining
a reviewed source mapping to a compatible recognised term. `quantity_approximation` permits those paired
losses, and exempts only numbers within that occurrence. It never disables general number checking.
Target-only “yonks ago” is valid indefinite wording. This bounded check cannot establish the numerical
fidelity of arbitrary paraphrases or ambiguous/reordered retellings.

`predicate_composition` is a major issue for a recognised predicate expansion that inserts its own
`enough` complement before the original's retained `enough` tail. The check needs exactly one source
predicate with matching concepts and unchanged surrounding sentence tokens. It abstains without an
original or an unambiguous local pairing; unchanged idioms and legitimate nested constructions are
not automatically errors. It is not a general grammar checker.


`semantic_degree` is a major issue when reviewed source and recognised target grades differ in one
unambiguous local predicate edit. It shares the engine's degree composition and covers the calibrated
DRUNK and HUNGRY families. The source must establish mild or strong degree; surrounding sentence tokens
must match, and every recognised target reading must have a known incompatible grade. Unknown or
ambiguous certificates, negation and additional edits can make the check abstain. This does not rate
unreviewed families or prove the severity of arbitrary paraphrases.
