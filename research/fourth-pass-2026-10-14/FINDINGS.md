# Fourth everyday pass: after the dinkum default

The first pass's 59 texts, levels (2-5, round-robin) and seed, after the third pass's changes:
- dinkum as the retelling default;
- the genre-aware garnish;
- troppo's new guidance;
- the craft rules in every setting;
- the harness fixes;
- the third-pass dictionary round;
- the design review's fixes.

The bundled embedder is still 1.2.0, because the 1.3.0 retrain stopped at its gate (`training/README.md`).

For each text, five candidates:
- **engine:** `aussiefy translate` at the genre's own setting;
- **yarn-dinkum, yarn-troppo:** yarn mode by hand now. Twelve subagents, `YARN_TASK.md`, each retelling written fresh from its own brief;
- **dinkum-3:** the third pass's yarn-dinkum retellings, unchanged, so the same judge scores before and after on the same packet;
- **unharnessed:** the first pass's retellings, unchanged.

Twelve judge subagents scored them blind under rubric version 3, whose only change from version 2 is "as rude" → "as vulgar" in register's question, so the scores line up with the third pass. All 118 yarn retellings were accepted, and all 59 reports validated. The tables come from `summary.json`, `COMPARE.md` and the verdicts.

## Results

| candidate | pass | mean | first | meaning | sense | authenticity | register | tone | flow | variety | essence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| engine | third | 3.14 | 0% | 4.41 | 3.46 | 2.12 | 1.37 | 4.24 | 3.25 | 1.93 | 4.34 |
| yarn-dinkum | third | 4.73 | 52% | 4.92 | 4.81 | 4.71 | 4.37 | 4.97 | 4.83 | 4.29 | 4.97 |
| yarn-troppo | third | 4.08 | 29% | 4.12 | 4.41 | 3.98 | 3.59 | 3.76 | 4.07 | 4.51 | 4.17 |
| unharnessed | third | 4.51 | 13% | 4.83 | 4.42 | 4.19 | 4.15 | 4.78 | 4.61 | 4.17 | 4.90 |
| engine | fourth | 3.18 | 0% | 4.47 | 3.73 | 2.12 | 1.41 | 4.41 | 3.27 | 1.63 | 4.41 |
| **yarn-dinkum** | fourth | **4.64** | 23% | **4.93** | **4.81** | 4.59 | 4.19 | **4.98** | **4.68** | 3.98 | **4.98** |
| yarn-troppo | fourth | 4.23 | 24% | 4.32 | 4.36 | 3.93 | 3.92 | 3.98 | 4.07 | **4.85** | 4.44 |
| dinkum-3 | fourth | 4.63 | **39%** | 4.86 | 4.54 | **4.61** | **4.51** | 4.85 | 4.66 | 4.12 | 4.86 |
| unharnessed | fourth | 4.48 | 14% | 4.75 | 4.36 | 4.29 | 4.34 | 4.68 | 4.54 | 4.03 | 4.83 |

("first": the share of texts a candidate ranked first overall, ties shared.)

By genre, the mean:

| genre | texts | engine | yarn-dinkum | yarn-troppo | dinkum-3 | unharnessed |
|---|---|---|---|---|---|---|
| story | 9 | 3.10 | **4.65** | 4.28 | 4.40 | 4.51 |
| personal | 7 | 2.52 | **4.62** | 4.05 | 4.54 | 4.48 |
| news | 11 | 3.19 | **4.68** | 4.23 | 4.67 | 4.26 |
| instructions | 15 | 3.36 | 4.61 | 4.42 | **4.65** | 4.56 |
| technical | 8 | 3.47 | 4.62 | 4.23 | 4.66 | **4.69** |
| official | 9 | 3.21 | 4.68 | 4.03 | **4.81** | 4.38 |

By level, the mean:

| level | engine | yarn-dinkum | yarn-troppo | dinkum-3 | unharnessed |
|---|---|---|---|---|---|
| 2 | 3.71 | **4.80** | 3.87 | 4.72 | 4.58 |
| 3 | 2.94 | 4.69 | 3.92 | **4.71** | 4.48 |
| 4 | 3.17 | 4.51 | **4.56** | 4.53 | 4.49 |
| 5 | 2.88 | 4.57 | **4.62** | 4.54 | 4.34 |

Problems the judges logged (critical / major / minor):

| candidate | critical / major / minor |
|---|---|
| yarn-dinkum | 0 / 0 / 86 |
| dinkum-3 | 1 / 5 / 105 |
| yarn-troppo | 0 / 21 / 182 (39 majors in the third pass) |
| unharnessed | 0 / 13 / 111 |
| engine | 23 / 102 / 53 |

Verify, over the 1,785 sentences:
- no critical or major problem for any yarn retelling;
- untouched sentences: the engine left 752, yarn-dinkum 122, yarn-troppo 87, dinkum-3 86;
- the unharnessed retellings had 1 critical and 7 major.

## What it says

**New dinkum is as good as the old, and safer, but less Aussie.**
- On the same packets, from the same judges, new dinkum scored 4.64 against the third pass's 4.63. Each won 26 texts head to head, with 7 ties.
- New dinkum drew no critical or major problem, against the old one's 1 critical and 5 major. It has the best meaning, sense and tone of any candidate.
- It lost register (4.19 against 4.51), variety (3.98 against 4.12) and first places (23% against 39%), and it left more sentences untouched (122 against 86).
- The likely cause is the changes meant to make it safe. The engine's draft now has almost no garnish outside stories, and the craft rules that came into every setting ask for restraint (tag-ons only where someone is addressed, no pile-ups).
- It gained most where a voice was always wanted: stories (4.65 against 4.40) and personal writing (4.62 against 4.54). It lost most in official prose (4.68 against 4.81), where the old drafts' colour had been welcome.

**Troppo is better, and now edges dinkum at broad levels.**
- Mean 4.08 → 4.23, meaning 4.12 → 4.32, tone 3.76 → 3.98, register 3.59 → 3.92. Its majors fell from 39 to 21, and its variety is the highest of any candidate (4.85).
- At levels 4 and 5 it scored 4.56 and 4.62, just ahead of dinkum (4.51, 4.57). At levels 2-3 it is well behind (3.87, 3.92).
- So the guidance change ("its claims as it makes them", "a letter stays a letter", "a hazard is never the joke") did what it set out to do.
- What its majors still are:
  - five are story openers on a notice, an obituary, a policy or a doc;
  - three are added claims or examples;
  - three are tone slips on a hazard or a death;
  - the rest are wrong senses.

**The engine moved a little.** Mean 3.14 → 3.18: sense 3.46 → 3.73 and tone 4.24 → 4.41 rose (the wrong-sense guards, the form-aware garnish), while variety fell 1.93 → 1.63 (less garnish outside stories). Its register stays near the floor (1.41) at the deadset most genres default to.

**The judges stayed consistent.** The unharnessed retellings, the same text in every pass, scored 4.67, 4.66, 4.51 and now 4.48.

## Recommendations

1. **Keep dinkum as the default.** Then win back register without giving up its fidelity. Two ways to do that:
   - put more voice into the dinkum brief for non-story genres (the connecting prose can be broad even where the form is strict);
   - or let the engine's draft take connectives in news and official prose, where the old drafts' colour scored well.
   Measure it on this pass's packets, with dinkum-3 as the anchor.
2. **Offer troppo for levels 4-5.** It now matches dinkum there. Keep dinkum the default.
3. **Make openings follow the form at every setting,** troppo included, or give each genre its own openings. Story openers on notices and obituaries were troppo's most common major problem, and every batch reported them.
4. **Keep swear infixes out of instructions, technical docs and news.** Each genre's garnish list in genres.yaml still includes `infix`. They're the engine draft's worst slips, and the plan can't decline them because they aren't planned phrases. Examples: "a bloody good seal" in an EPA guide, "yer bloody code", and "far too fuckin' long" in a lightning notice.

## Harness problems the yarn agents hit

From the twelve batches' notes (`texts/*/yarn-notes.md`).

- **Openings and riffs that don't fit the genre.** At troppo, every genre is offered story openers ("Fair dinkum, this happened.", "Back in the day,", "Way back,"), and "Okay, so." is offered though the guide calls it a tic. The riffs carry Australian scenery into American settings: "bone dry half the year" for Yellowstone's cold creeks, and "nothin' but flies and gum trees" for a New Mexico forest.
- **Engine drafts.**
  - Swear infixes appear in instructions, docs and news.
  - "tucker" goes on every "food", with plural agreement broken ("thick tucker are cooked").
  - "quid" goes on "dollar" in money figures.
  - "the old bloke" stands for "the old man" (a father).
- **Wrong-sense planned phrases** still come up in every batch:
  - "bush" for a legal "wilderness" or a US forest's health;
  - "Parliament House" for a real US Congress (the style guide's own example needs a caveat);
  - "knock together" for any "build";
  - "every bastard" for refugees, and "some bugger" for a hoped-for husband;
  - "beaut" for "brilliant" (clever), "rapt" for "excited", and "do it tough" for a forecast's highs;
  - "pressie" for a policy's "gift";
  - "coves" and "sheilas" in the post about the word "guys".
- **Lint suggestions in the wrong sense** were the most common complaint:
  - LEAVE terms ("shoot through", "clear out") for "get going", "bolted" and "heads off";
  - "heaps" for "lots" that are groups;
  - "bugger all" inside negations ("Nothing in this is advice");
  - "quid" for "dollar";
  - "the pollies" for agency staff;
  - "have a crack at" for "have a go at" in the sense of criticising;
  - "brekkie" inside "dog's breakfast".
  Lint also suggests swaps inside kept quotes and for mentioned words.
- **Lint warnings.**
  - `name_added` fires on demonyms of names in the original ("Colombian", "New Englanders", "European") and on the planner's own "Yanks".
  - `name_dropped` fires on capitalised common nouns ("Wife", "Twas"), on sentence starts, and when a comma sits between a title and a name.
  - `repeated_phrase` fires on metric brackets and on the original's own parallel wording.
- **The moved-phrase check** sent back a "Yeah" written for a different "Yes" from the one planned.
- **DIFFICULT_SENTENCES** lists terms of art the genre keeps ("miscompilation", "advection", "position"), up to 58 sentences in one FAQ. At level 2 it lists none, and the plans are thin: several had no planned phrases at all.
- **Lookup.** It offers opposites ("spendthrift" → "tight-arsed") and matches on a single word ("wet a line" → "wet week", "give a toss" → throw). "dry" reaches "billabong", and "drunk" reaches "a mongrel bastard".
- **Nothing checks an added or strengthened claim at troppo.** "Stay out of the water" for "not recommended" got through, and so did invented examples in a policy. The agents caught these themselves.

**Vocabulary** the agents reached for that lookup didn't have. These are candidates only and haven't been reviewed:
- informal speech: a blow-in, within cooee, cop (put up with), give us a hoy, give someone a bell, hooroo, chockers, sure as eggs, bucketing down;
- idioms: first dibs, till the cows come home, down tools, go halves, par for the course, come good, carry the can, a curly one, the horse has bolted;
- slang terms: boffins, red cordial, lurk, boss cocky, double-dipping, the drum, twig, a skerrick, dab hand, the damage, quick smart, the mob, a do, a gong, lurgy, a dud;
- phrases and similes: knock over (finish), down the track, a fair whack, jumper weather, rug up, dry as a dead dingo's donger, lonely as a shag on a rock;
- new senses of existing entries: crook (injured), knock off (beat), the oldies (old people in general).

("tragic", a fan, which one agent listed, is in the dictionary since the third-pass round: `lookup fan` and
`lookup tragic` both find it.)
