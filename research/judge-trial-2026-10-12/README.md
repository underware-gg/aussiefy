# Judge trial, 2026-10-12

The first live run of `aussiefy judge` in agent mode, to see the whole loop work before the rubric is settled.
It was judged under rubric version 1. The feedback below went into version 2, so `judge read` now refuses
this packet: versions don't mix, and the verdict and card here are the record.

- **Original:** `original.txt`, a NASA press release (public domain, from `tests/corpus/everyday/news/`).
- **Brief:** level 4 (larrikin), vulgarity 1 (dad).
- **Candidates:**
  - `engine`: `aussiefy translate -l 4 -s 1`;
  - `engine_best`: the same with `--variety 1`;
  - `unharnessed`: a subagent's own retelling, written with no tools from `aussiefy judge unharnessed --prompt-only`.
- **Judge:** a second subagent. It saw only what `aussiefy judge brief` prints (instructions, prompt and schema, but not the key) and wrote `report.json`.
- **Unblinding:** `aussiefy judge read packet.json report.json` validated the report and unblinded it into `verdict.json` and `card.txt`.

## Result

The report passed validation on the first try, every quote verbatim. The ranking was unharnessed (mean 4.62),
then engine (2.25), then engine_best (2.12).

The judge found what the deterministic `verify` can't:
- **Two wrong-sense swaps:** "across the mob" for *across the nation*, and "battlers" for *the people*.
- **The engine is far too light for a level-4 brief:** most sentences are left verbatim on an everyday text.
- **The closer is a stock exclamation** bolted onto a press release.

`verify` found no critical or major problem in any of the three. It reported the closer as `stock_closer`,
and 42% of the engine's sentences as untouched (info). It also gave one false positive: `name_added` for
"October" in the unharnessed retelling, where the original wrote "Oct.".

## The judge's feedback on the rubric (applied in version 2)

1. **Additions:** a problem's `original` has nowhere to point for an invented line. Allow an empty
   `original` and say it means "added".
2. **Ties:** near-identical candidates are forced into a strict order. Allow ties in the rankings, or say
   that the order between near-equals is arbitrary.
3. **Overlap and an unclear anchor:** `register` and `authenticity` overlap for an untranslated text, and
   `essence` is unclear when a text is left verbatim ("unmistakably the original" against "not retold").
4. **Tone:** say that a change of register the brief asks for (a press release told as a yarn) is not a
   loss of tone.
5. **Counting:** log a problem that runs through the whole text once, with one representative quote.
6. **Colour:** say how far an added aside may go before it counts as invented content.
