# Third everyday pass: the embellishment dial

The first pass's 59 texts, levels (2-5, round-robin) and seed, after the embellishment dial, the second-pass fixes and
two dictionary rounds. For each text:

- **engine:** `aussiefy translate` at the genre's own setting;
- **yarn-deadset, yarn-dinkum, yarn-troppo:** yarn mode by hand at each setting (twelve subagents, `YARN_TASK.md`; each
  retelling written fresh from its own brief);
- **unharnessed:** the first pass's retellings, unchanged.

Twelve judge subagents scored the five candidates of each text blind, under the same rubric (version 2,
`JUDGE_TASK.md`), so the scores line up with the earlier passes. All 177 yarn retellings were accepted; every report
validated. Tables from `summary.json` and `COMPARE.md`.

## Results

| candidate | pass | mean | first | meaning | sense | authenticity | register | tone | flow | variety | essence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| engine | second | 2.82 | 0% | 4.05 | 2.76 | 1.78 | 1.63 | 3.83 | 2.81 | 1.83 | 3.90 |
| yarn | second | 4.62 | 35% | 4.95 | 4.75 | 4.46 | 4.03 | 4.92 | 4.66 | 4.25 | 4.95 |
| unharnessed | second | 4.66 | 65% | 4.80 | 4.44 | 4.49 | 4.71 | 4.75 | 4.69 | 4.49 | 4.93 |
| engine | third | 3.14 | 0% | 4.41 | 3.46 | 2.12 | 1.37 | 4.24 | 3.25 | 1.93 | 4.34 |
| yarn-deadset | third | 4.42 | 7% | 4.98 | 4.75 | 4.29 | 3.49 | 5.00 | 4.27 | 3.58 | 4.97 |
| **yarn-dinkum** | third | **4.73** | **52%** | 4.92 | 4.81 | **4.71** | **4.37** | 4.97 | **4.83** | 4.29 | 4.97 |
| yarn-troppo | third | 4.08 | 29% | 4.12 | 4.41 | 3.98 | 3.59 | 3.76 | 4.07 | **4.51** | 4.17 |
| unharnessed | third | 4.51 | 13% | 4.83 | 4.42 | 4.19 | 4.15 | 4.78 | 4.61 | 4.17 | 4.90 |

("first": the share of texts a candidate ranked first overall, ties shared.)

By the genre each text reads as, the mean, and which yarn setting scored best:

| genre | texts | its own setting | engine | deadset | dinkum | troppo | unharnessed | best yarn setting |
|---|---|---|---|---|---|---|---|---|
| story | 9 | troppo | 3.10 | 4.51 | **4.72** | 3.94 | 4.54 | dinkum 7, deadset 2 |
| personal | 7 | dinkum | 2.52 | 4.39 | **4.62** | 4.00 | 4.50 | dinkum 4, deadset 3 |
| news | 11 | deadset | 3.18 | 4.38 | **4.74** | 4.11 | 4.36 | dinkum 9, deadset 1, troppo 1 |
| instructions | 15 | deadset | 3.23 | 4.39 | **4.71** | 4.25 | 4.60 | dinkum 10, troppo 3, deadset 2 |
| technical | 8 | deadset | 3.56 | 4.30 | **4.78** | 4.00 | 4.61 | dinkum 8 |
| official | 9 | deadset | 3.10 | 4.53 | **4.82** | 4.00 | 4.40 | dinkum 6, deadset 2, troppo 1 |

By level, the mean:

| level | engine | deadset | dinkum | troppo | unharnessed |
|---|---|---|---|---|---|
| 2 | 3.76 | 4.55 | **4.86** | 3.63 | 4.57 |
| 3 | 2.91 | 4.51 | **4.83** | 3.79 | 4.56 |
| 4 | 3.05 | 4.33 | **4.62** | 4.38 | 4.55 |
| 5 | 2.82 | 4.27 | **4.62** | 4.54 | 4.34 |

Verify, summed over the 59 texts (1,785 sentences): no critical or major problem for any yarn setting; the engine
left 733 sentences untouched, deadset 184, dinkum 86, troppo 75; the unharnessed retellings had 1 critical and 7 major.

## What it says

**Dinkum is the setting.** Yarn mode at dinkum is the best candidate overall (4.73, first on 52% of texts), and the best in
every genre, at every level, and on authenticity, register and flow. It beats the unharnessed agent (4.51) in every
genre, by 0.1 (instructions) to 0.4 (news, official), while keeping deadset's fidelity (meaning 4.92, tone 4.97, essence
4.97). This is the goal the user set for yarn mode: as expressive as the unharnessed agent, and more faithful.

**Deadset is the faithful floor.** The best meaning and tone of any candidate (4.98, 5.00), the fewest problems, but
register 3.49 and variety 3.58: a word swap, sentence for sentence, reads as translated. Judges ranked it first on only 7%
of texts, mostly where the brief was level 2 and the genre strict.

**Troppo trades fidelity for colour, and loses.** The most variety (4.51), but meaning falls to 4.12 and tone to 3.76,
and it drew 39 of the 50 major problems the judges logged for yarn mode. They name the same faults again and again:
- a pub frame or stock opener the original lacks ("Now, this one's a ripper. Jeff Peters leans on the bar", "Pull up
  a stool." on an anxious forum post);
- the narrator commenting on a deadpan joke ("Talk about not knowin' when to shut his trap");
- added judgements that change a claim ("He can't" for "he won't"; a wife made a cheat "for laughs");
- flippant tags on a safety step;
- similes that don't hold up.

Troppo improves with the level (3.63 at level 2, 4.54 at level 5): at broad levels it's nearly dinkum's equal; at
light ones its colour is out of register. Even on stories, its own genre, troppo (3.94) is well behind dinkum (4.72).

**The genre defaults are wrong for yarn mode.** Four of the six genres default to deadset, and stories to troppo. The
pass says dinkum is better in all six. The genre still decides the *form* (what stays exact, the shape kept), and the
agents report it did that well: the steps, quantities, quotes, code and markup stayed exact at dinkum.

**The engine improved again** (2.82 → 3.14 mean; meaning 4.05 → 4.41, sense 2.76 → 3.46, tone 3.83 → 4.24), from the
wrong-sense fixes and the dictionary rounds. Its register (1.37) stays where it was: at deadset, the default for most of
these texts, it adds nothing beyond the word swaps.

**The judges stayed consistent.** The unharnessed retellings, word for word the same in all three passes, scored 4.67,
4.66 and now 4.51. The drop is the field: they're now judged beside a better candidate, dinkum, which takes the "first"
places (65% → 13%).

## Recommendations

1. **Make dinkum yarn mode's default for every genre**, keeping the genre's form guidance and `person_swears`. Keep
   troppo as an opt-in, and say in its guidance that it suits levels 4-5 and stories told to an audience.
2. **Keep the engine's own defaults conservative.** The engine's garnish at dinkum is what the yarn agents called
   unusable outside stories (below). The engine and yarn mode may want different defaults: the engine deadset outside
   stories, yarn mode dinkum everywhere.
3. **Tighten troppo's guidance** with what the judges marked: no frame or opener the original lacks, no comment on a
   deadpan joke, no added judgement, no tag on a hazard, keep a letter a letter and a speaker in the first person.

## Harness problems the yarn agents hit

From the twelve batches' notes (`texts/*/yarn-notes.md`) and reports.

**The engine's dinkum drafts.** Every batch said the same: an opener on nearly every paragraph; swears and insults
aimed at the reader in safety notices, recipes and docs ("protect yerself, ya galah", "store yer Rust code, ya
galah", "ya flamin' mongrel"); openers on datelines and headings ("Crikey, WASHINGTON, Dec. 27.—", "MAMMOTH HOT
SPRINGS, Wyo. Fuckin' hell, –"); garnish inside quoted documents and stage directions ("Crikey, Productivity growth is
strong", Henry Ford's quote); a capital left after an opener ("Well, Pour the batter"); one fact flipped ("weren't so
lucky" → "weren't lucky as fuck"). Garnish needs the genre's form (no reader insults in instructions, no garnish on a
dateline, a heading, or inside held quotes), not only the setting's placements.

**OPENINGS are story openers in every genre** ("Ever hear the one about…?", "Back in the day," for current news,
"Pull up a stool." for a safety guide). They should come from the genre, or be offered only to stories and letters.

**The brief contradicts itself on headings:** the system prompt says a heading's words may be Aussified, the markdown
MARKUP rule says keep headings character for character. Every agent followed MARKUP. Troppo's "perform" examples
swear ("bastards", "prick") even at vulgarity 0.

**The moved-phrase check counts words anywhere, not the planned spot.** It sent back retellings that used the
original's word again in the agent's own wording ("a look" for "Examine", "really", "lucky", "no", "good"), and
pushed a planned "dosh" into a quoted ad. It should check the planned span (the plan knows each phrase's position),
not the whole text.

**Wrong-sense planned phrases** still come up in every text. Recurring:
- "a beaut" or "beaut" for any "good" (good friends, good riddance, a good imitation, good work);
- "young fellas" for any "boys", "little fella" for any child;
- "bush" in US land terms;
- "dead set on" for "dedicated to";
- "swear blind" for "resolve";
- "a goer" for "feasible", said of a woman;
- "esky" for the adjective "cooler" ("A cooler airmass");
- "the punters" in "public, private sector";
- "paddock" for a field of study or data fields in news;
- "scared stiff" for "I am afraid your…".

The pass also found two gaps in features added last round:
- the mention check needs a cue word, so a forum post listing words in quotes ('guys', 'boys') wasn't held;
- garnish ignores held quotes.

**Lint suggestions miss idioms and parts of speech:** "beaut" inside "good sport", "dosh" in "pocket money", "mitts" for
the verb "hands", "bush" in "neck of the woods", "come a cropper" for a crashing system. **Lookup** matches words inside
glosses ("harmless" → "a mean bastard", "probably" → "no bloody way") and misses inflections ("coves", "playing up").

**Spelling consistency:** the plan offers several spellings of one word in one text (bickie, bickies, bikkie, bikkies;
pressie, prezzies; Chrissy, Chrissie). A text should keep the first spelling it uses.

**Vocabulary** the agents reached for that lookup didn't have (candidates only, unreviewed): sunnies, pull the pin on
(cancel), the crook, oldies, a good innings, furphy, twig, cheap as chips, pinch, workmate, drag the chain, bang on
about, give someone a ring/bell, sing out, here's the go / what's the go, brolly, nippy, Yanks, bench (kitchen
counter), first dibs, pocket money, dressing gown, punnet, the damage, pear-shaped, have a gander, lurk, offsider, nut
out, on song, a wrap (praise), all up, tragic (a fan), hang up the boots, chuck a tanty, sook, off with the fairies, a
red-hot go, doing my head in, fair and square, stickybeak (noun), first in best dressed, muck up, fisho, truckies, out
bush, cashed up, stony broke, is she buggery, streets ahead, a breather.
