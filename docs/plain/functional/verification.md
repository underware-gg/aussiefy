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
