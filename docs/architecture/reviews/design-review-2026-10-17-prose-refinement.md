# Design review: prose refinement, 17 October 2026

Surface: phonetic question metadata/loader/execution, initial-capital evidence, dialogue tag attachment,
regressions, generated prose/goldens and bounded technical/instruction/body readbacks. One independent
reviewer assessed all six software-design concerns.

## Findings

No remaining findings after correction.

- Medium grammar finding: a generated Bible tag landed after `?”`. The existing terminal-punctuation
  matcher omitted curly closing quotes when no opening quote remained in the current sentence. Extend its
  existing closer alphabet; twelve punctuation/closer combinations, a complete continued-dialogue case and
  the existing narration-after-quote check cover the seam. No register or speaker-inference policy changes.
- Low measured efficiency finding: scanning all preceding question spans for each match was quadratic.
  Binary search over canonical sorted spans reduced the reviewer's 500/2,000/5,000-question probe from
  0.014/0.138/0.778 seconds to 0.008/0.035/0.112 seconds on that environment. These are isolated diagnostics,
  not website or general throughput claims.
- Qualify the opt-out: canonical quoted units can contain declarations and questions. Such a unit can
  conservatively lose this infix throughout; standalone non-question units remain eligible. Functional
  docs, DD-027 and the ledger now state that observed limit.
- Refresh the actual garnish-code digest after the review corrections. The reviewer independently matched
  the other four code digests and reproduced all three recorded outputs; the final digest was refreshed.
- Medium regression found by the complete suite: widening the case guard also declined the valid Work
  opener. Correct the dictionary's lower-case inventory instead: preserve raw lower-case spellings and
  inferred forms from lower-case source patterns; exclude case-folded capital-only patterns. This removes
  59 capital-only/derived tokens rather than 1,514 legitimate inflections from a wholesale deletion. The
  original engine guard is retained. Controlled inventory and existing composition/lint/harvest tests
  check the actual owner and its consumers.

The reviewer initially passed 96 focused checks. After the owner correction, the parent passed 196
document/composition/POS/contracts checks and 102 harness/reliability/harvest checks; 103 document/composition
checks also pass on Python 3.10. Complete pre-commit results are recorded in the maintenance ledger.
Final independent review passed 205 focused checks and found no remaining findings.

## What's done well

- Only the unsafe infix opts out of questions; other valid question infixes and policy controls remain.
- The canonical tokenizer handles abbreviations without a parallel sentence parser or nationality list.
- Skipped matches retain ordinals, preserving the later statement's seeded choice.
- Source-case evidence is corrected at its dictionary owner, retaining the existing conservative placement
  rule and ordinary-word/command evidence without a broader POS policy.
- Three small original probes preserve both outputs and explicit settings; bounded readback is not presented
  as a controlled writing-quality result. Generated output and complete golden diffs were read.

## Related follow-ups

Proceed with the planned model maintenance and available interface checks. No additional follow-up identified.
