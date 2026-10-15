# Yarn mode by hand, at two settings: the agent's task

You are the model in aussiefy's yarn mode, driving it by hand with `aussiefy yarn-tools`. For each text you are
given, retell it in Australian English twice, once at each of these embellishment settings:
- **dinkum:** in a genuine Aussie voice (yarn mode's default);
- **troppo:** as a yarn performed at the pub. It may take more liberty than dinkum; that's its point.

Each retelling is at the text's level and vulgarity, using the harness: the brief, lookups, lint, and a submit
that validates. Work from the repository root, `/workspace/aussiefy`, with its venv: `.venv/bin/python -m
aussiefy.cli ...` (written `aussiefy` below).

**Don't edit anything in the repository except the files named below for your texts.** The engine is frozen
while the pass runs.

## For each text, and each setting E in dinkum, troppo

- `ORIG` is the text's original: `research/fourth-pass-2026-10-14/texts/NAME/original.EXT`.
- `D` is its directory: `research/fourth-pass-2026-10-14/texts/NAME`.
- `FLAGS` are its settings: `-l LEVEL --vulgarity VULGARITY -s 1 --markup MARKUP -e E`.

Do the two settings as separate pieces of work. Write each one fresh from the original and its own brief, not
by editing another setting's retelling: the point is how they differ.

1. **Brief:** `aussiefy yarn-tools brief ORIG FLAGS`. Read all of it:
   - the system prompt: the voice, the craft rules, and the settings explained;
   - the payload: the original, the EMBELLISHMENT and its guidance, the GENRE and its guidance, the engine's
     draft (dinkum only), the planned phrases with what each replaces and means, riffs, openings
     if the setting takes them, and the difficult sentences.
2. **Write** your retelling.
   - Follow the brief: the level's weight, the embellishment's liberty, the genre's form, the vulgarity cap.
   - Keep every fact, name and number. In markdown or mdx keep every piece of code and markup exactly.
   - At dinkum: keep a planned phrase where it says what the original says there. Decline one
     that takes the wrong sense, with a reason, and don't work it in elsewhere (submit checks).
   - At troppo: write your own retelling from the original first, then draw on the planned phrases as
     vocabulary.
3. **Check:**
   - Look up anything you're unsure of: `aussiefy yarn-tools lookup ORIG "a meaning or a term" FLAGS --log
     D/yarn-E.log.jsonl`.
   - Lint your draft: `aussiefy yarn-tools lint ORIG D/yarn-E-draft.txt FLAGS --declined
     D/yarn-E-declined.yaml --log D/yarn-E.log.jsonl`.
4. **Submit:** `aussiefy yarn-tools submit ORIG D/yarn-E-draft.txt FLAGS --declined D/yarn-E-declined.yaml -o
   D/yarn-E.txt --log D/yarn-E.log.jsonl`.
   - `yarn-E-declined.yaml` is a YAML list of `{phrase: ..., reason: ...}` (quote a value with a colon in it),
     or `[]`.
   - If the submit is rejected, fix what the problems say and submit again. Accepted, it writes `D/yarn-E.txt`.
5. **Notes:** append to `D/yarn-notes.md`, under a `## E` heading, what the harness got wrong or what helped,
   in a few lines:
   - wrong-sense planned phrases;
   - lint or validation false positives;
   - lookups that came back empty or wrong;
   - anything in the brief that misled you, or that made the setting unclear.

   Be concrete, and quote the phrase.

## When you're done

Reply with a short summary across your texts:
- each text's and setting's outcome (accepted after N submits);
- the harness problems you hit most, with examples;
- how clear the two settings were and how they differed in practice;
- new Australian vocabulary you reached for that lookup didn't have.
