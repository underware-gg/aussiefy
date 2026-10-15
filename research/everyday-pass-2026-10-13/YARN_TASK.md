# Yarn mode by hand: the agent's task

You are the model in aussiefy's yarn mode, driving it by hand with `aussiefy yarn-tools`. For each text you are
given, retell it in Australian English at its level and vulgarity, using the harness: the brief, lookups,
lint, and a submit that validates. Work from the repository root, `/workspace/aussiefy`, with its venv:
`.venv/bin/python -m aussiefy.cli ...` (written `aussiefy` below).

**Don't edit anything in the repository except the files named below for your texts.** The engine is frozen
while the pass runs.

## For each text

`ORIG` is the text's original (`research/everyday-pass-2026-10-13/texts/NAME/original.EXT`), `D` its
directory (`research/everyday-pass-2026-10-13/texts/NAME`), and `FLAGS` its settings: `-l LEVEL --vulgarity
VULGARITY -s 1 --markup MARKUP`.

1. **Brief:** `aussiefy yarn-tools brief ORIG FLAGS`. Read all of it: the system prompt (the voice, the
   craft rules, the genre's guidance) and the payload (the original, the engine's draft, the planned phrases
   with what each replaces and means, riffs, openings if the genre takes them, difficult sentences).
2. **Write** your retelling. Follow the brief: the level's weight, the genre's guidance, the vulgarity cap.
   Keep every fact, name and number. Keep a planned phrase where it says what the original says there;
   decline one that takes the wrong sense, with a reason, and don't work it in elsewhere. In markdown or mdx
   keep every piece of code and markup exactly.
3. **Check:** look up anything you're unsure of (`aussiefy yarn-tools lookup ORIG "a meaning or a term"
   FLAGS --log D/yarn.log.jsonl`), and lint your draft (`aussiefy yarn-tools lint ORIG DRAFTFILE FLAGS --log
   D/yarn.log.jsonl`). Save drafts as `D/yarn-draft.txt`.
4. **Submit:** `aussiefy yarn-tools submit ORIG D/yarn-draft.txt FLAGS --declined D/yarn-declined.yaml -o
   D/yarn.txt --log D/yarn.log.jsonl`. `yarn-declined.yaml` is a YAML list of `{phrase: ..., reason: ...}`
   (quote a value with a colon in it), or `[]`. If it's rejected, fix what the problems say and submit
   again. Accepted, it writes `D/yarn.txt`.
5. **Notes:** append to `D/yarn-notes.md` what the harness got wrong or what helped, in a few lines:
   - wrong-sense planned phrases;
   - lint or validation false positives;
   - lookups that came back empty or wrong;
   - anything in the brief that misled you.

   Be concrete, and quote the phrase.

## When you're done

Reply with a short summary across your texts:
- each text's outcome (accepted after N submits);
- the harness problems you hit most, with examples;
- new Australian vocabulary you reached for that lookup didn't have.
