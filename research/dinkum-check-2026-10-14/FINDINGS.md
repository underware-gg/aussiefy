# Dinkum check: voice in strict forms

The fourth pass found the new dinkum as good as the third pass's, but less Aussie (register 4.19 against 4.51),
and most of the loss was in official prose and news. Two fixes followed:
- dinkum's guidance now puts the voice into the connecting prose of a strict form;
- the fourth-pass dictionary round.

This check retold the fourth pass's 20 news and official texts again at dinkum, at the same levels and seed. It
judged three candidates blind in the same packets, under rubric version 3:
- **yarn-dinkum:** yarn mode by hand now (four subagents, `YARN_TASK.md`);
- **dinkum-4:** the fourth pass's dinkum retellings, unchanged;
- **dinkum-3:** the third pass's, unchanged.

All 20 retellings were accepted, 19 on the first submit, and all 20 judge reports validated. The tables come
from `summary.json` and the verdicts. With 20 texts and one judge each, a difference of 0.1 in the mean is
within noise.

## Results

| candidate | mean | first | meaning | sense | authenticity | register | tone | flow | variety | essence | critical / major / minor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| yarn-dinkum | 4.46 | 30% | 4.65 | 4.45 | 4.25 | 4.00 | 4.75 | 4.35 | 4.25 | 5.00 | 0 / 5 / 42 |
| dinkum-4 | 4.45 | 12% | **4.90** | **4.60** | 4.20 | 3.60 | **5.00** | **4.50** | 3.85 | 4.95 | 0 / 5 / 36 |
| dinkum-3 | **4.57** | **57%** | 4.85 | **4.65** | **4.35** | **4.05** | 4.85 | 4.45 | **4.35** | 5.00 | 0 / 5 / 38 |

- **Head to head:**
  - New dinkum against dinkum-4: 7 wins, 7 losses and 6 ties.
  - New dinkum against dinkum-3: 7 wins and 13 losses.
- **By group, the mean (register):**

  | group | texts | yarn-dinkum | dinkum-4 | dinkum-3 |
  |---|---|---|---|---|
  | news | 11 | 4.50 (4.00) | 4.46 (3.55) | 4.56 (4.18) |
  | official | 7 | 4.46 (4.43) | 4.52 (4.00) | 4.62 (4.14) |
  | mdx docs | 2 | 4.25 (2.50) | 4.19 (2.50) | 4.44 (3.00) |

- **Verify:** across the 499 sentences, no critical or major problem for the new dinkum, against 5 majors for
  dinkum-4 and 11 for dinkum-3.

## What it says

**The voice came back, and the mean didn't move.**
- Register rose from 3.60 to 4.00, back level with dinkum-3 (4.05). Variety rose from 3.85 to 4.25, and first
  places from 12% to 30%. So the guidance did what it set out to do.
- Fidelity paid for it. Meaning fell from 4.90 to 4.65, sense from 4.60 to 4.45, and tone from 5.00 to 4.75.
- The judges' majors for the new dinkum show where it went wrong. The voice reached into what the form keeps:
  - "we reckon you're responsible" for "we consider you responsible" makes a legal position a casual opinion;
  - "they doubled down on" for "reaffirmed" escalates a decision;
  - "finding energy, groundwater and natural hazards while they're at it" demotes a stated aim;
  - "the areas that do better for a thinning" is ungrammatical.
- One major, on the Interfold doc, says the opposite: at level 5 too much was left verbatim. Its brief had no
  planned phrases, and the agent kept a table whole.

**Dinkum-3 is still the one to beat in these genres.** Its engine drafts carried more colour, and its
retellings voiced the connecting prose without touching what the documents said.

## Changes from this check

1. **Dinkum's guidance** (`genres.yaml`): what's kept includes the force of what it says. An obligation, a
   decision, a finding or a stated aim keeps its verb's weight. The guidance quotes the three slips above.
2. **No riffs in news, docs or official prose below troppo.** A riff is a picture, and in a text about real
   things it's a claim. The Yellowstone draft read "rivers, creeks, bone dry half the year, and lakes"; Yellowstone's creeks aren't
   dry. The plan offers riffs only where the setting takes them, and instructions keep their tails.
3. **Lint no longer asks for a dialect word to change inside a quote the genre keeps.** The engine holds a quote
   as said in news and official prose, and leaves "5 percent" alone there. Lint and submit, though, kept asking
   for "per cent" inside the FOMC's quoted directive, and the agent had to change the quote to pass. US spelling
   inside a quote is still flagged, as the engine respells it (house style).
4. **The dictionary round** for this check's vocabulary (`research/dinkum-check-round-2026-10-14/`).

## Harness problems the yarn agents hit

From `texts/*/yarn-notes.md`.

- **Thin plans.** Most texts had no planned phrases, or one. At level 2 the engine draft was often the original
  word for word, so all the voice was written by hand.
- **DIFFICULT_SENTENCES** in a forecast discussion listed its terms of art ("boundary", "advection",
  "elevation"). News keeps `formal_to_rework`, so its formal sentences are listed, and in a forecast those are
  terms of art.
- **Lookups in the wrong sense, or the opposite one:**
  - "very cold" → coldie and stubby;
  - "raining heavily" → on the turps;
  - "worked very hard" → drunk words;
  - "not out of the question" → not on your nelly;
  - "officials" → the pollies;
  - "stuff up" → the folding stuff;
  - "retire" came back empty, though the dictionary has pull the pin.
- **Lint suggestions:**
  - "gift" → pressie in a gifts policy;
  - "ok" → righto on the adjective ("it isn't ok");
  - "lots" → heaps on "four lots";
  - "everyone" → every man and his dog in official prose;
  - "dad" → old fella in an obituary.

  `name_dropped` fires when a comma sits between a title and a name ("President, George Washington"), and on
  "Christmas Trees" once it became "Chrissy trees".
- **Lint misses American forms** ("outta", "oughta", "wanna", "folks") and some US spellings inside capitalised
  headings ("Specialized Experience").
- **The brief left a few things unclear:**
  - whether bold list labels and table cells in markdown are markup or prose;
  - whether to give °C for "in the 70s";
  - "footy" for American football (gridiron is the word).
