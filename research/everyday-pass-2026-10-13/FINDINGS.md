# Second everyday pass: results and findings

The first pass's 59 texts, at the same levels (2-5, round-robin) and seed, after this round of work: genre gating,
the dictionary round, US/UK dialect swaps, the rails audit, the POS tagger, a/an, and the yarn and lint fixes.
- **engine:** `aussiefy translate` at commit 891f6e1.
- **yarn:** ten subagents running yarn mode by hand (`YARN_TASK.md`).
- **unharnessed:** the first pass's retellings, unchanged. They don't depend on the harness, so the comparison
  isolates it, and re-judging them checks the judges.

Six judge subagents scored each set blind under the same rubric (version 2, `JUDGE_TASK.md`). Every report
validated. The tables come from `COMPARE.md` and `summary.json`.

## Results

| candidate | pass | mean | first | meaning | sense | authenticity | register | tone | flow | variety | essence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| engine | first | 2.35 | 0% | 3.32 | 2.20 | 1.34 | 1.66 | 3.02 | 2.25 | 1.56 | 3.41 |
| engine | second | **2.82** | 0% | 4.05 | 2.76 | 1.78 | 1.63 | 3.83 | 2.81 | 1.83 | 3.90 |
| yarn | first | 4.68 | 63% | 4.68 | 4.51 | 4.54 | 4.81 | 4.58 | 4.63 | 4.81 | 4.85 |
| yarn | second | 4.62 | 35% | 4.95 | 4.75 | 4.46 | 4.03 | 4.92 | 4.66 | 4.25 | 4.95 |
| unharnessed | first | 4.67 | 37% | 4.97 | 4.66 | 4.66 | 4.29 | 4.97 | 4.73 | 4.10 | 4.95 |
| unharnessed | second | 4.66 | 65% | 4.80 | 4.44 | 4.49 | 4.71 | 4.75 | 4.69 | 4.49 | 4.93 |

By level, mean, first pass / second:

| level | engine | yarn | unharnessed |
|---|---|---|---|
| 2 | 3.27 / 3.41 | 4.67 / 4.70 | 4.69 / 4.66 |
| 3 | 2.26 / 2.70 | 4.67 / 4.67 | 4.63 / 4.72 |
| 4 | 1.93 / 2.69 | 4.63 / 4.53 | 4.70 / 4.60 |
| 5 | 1.89 / 2.48 | 4.75 / 4.57 | 4.63 / 4.68 |

Verify, summed over the 59 texts (1,618 sentences):

| candidate | critical | major | minor | untouched |
|---|---|---|---|---|
| engine | 0 → 0 | 13 → 1 | 30 → 14 | 553 → 640 |
| yarn | 0 → 0 | 0 → 0 | 72 → 28 | 54 → 162 |

### What it says

**The judges are consistent.** The unharnessed retellings are word for word the first pass's, and they scored
4.67, then 4.66. Their criteria moved by up to 0.4 in either direction, because each is scored against
different neighbours. A difference much under 0.1 in a mean, or a few points of "first", is noise.

**The engine improved most, and where it was worst.**
- Mean 2.35 → 2.82; levels 4-5 up 0.6-0.8, level 2 up 0.1.
- The gains are fidelity: meaning +0.73, tone +0.81, sense +0.56, essence +0.49, flow +0.56. Verify's major
  problems fell from 13 to 1.
- This is the genre gating (no pub garnish on notices and docs), the rails and the POS guards (fewer
  wrong-sense swaps), and the dialect pass.
- What didn't move:
  - register (1.66 → 1.63) and variety;
  - coverage, which went down: 640 untouched sentences, from 553, because the new guards refuse more than
    the dictionary round added.
- The engine is now a faithful, light translator. It isn't yet an Aussie one at levels 4-5.

**Yarn mode traded register for fidelity.**
- Meaning (4.95), sense (4.75), tone (4.92) and essence (4.95) now match or beat the unharnessed agent's
  first-pass scores: the gap the first pass found is closed.
- But register fell from 4.81 to 4.03 and variety from 4.81 to 4.25, so the unharnessed agent now ranks first
  more often (65% against 35%). Yarn mode lost most in instructions (18% first) and conversational texts (32%).
- The cause is in the agents' notes, over and over. The genre guidance ("plain Aussie", "lightly", "safety
  before colour") and the level ("a full pub yarn") pull against each other at levels 4-5. The agents followed
  the genre, and the judges score register against the level.
- Coverage fell the same way: 162 untouched sentences, from 54.

**What to change:** make the genre decide the *form* of the Aussie, not how much of it there is.
- A level-4 safety notice should still be broad Aussie in its words: plain sentences, no pub openers or tags,
  no flippancy on safety, but every noun and verb that has an everyday Australian word taking it.
- The guidance in `data/genres.yaml` and the brief's "perform" block should say so. The engine's genre policy
  already works this way: it gates garnish, not swaps.
- This is the change to test first in the hill climb: `genres.yaml` guidance and `guide.yaml` perform, with
  register and variety watched against meaning and tone.

## Harness problems the yarn agents hit

From `texts/*/yarn-notes.md` (595 lines) and the agents' reports. All 59 retellings were accepted, nearly all on
the first submit.

**Wrong-sense planned phrases, by how often they came up:**
- **"punters" for any "people"** (in 20 notes): contributors, park staff, colleagues, a nation, the public
  sector. PEOPLE → punters needs tightening to the sense "customers, punters at the races, ordinary folk as
  an audience".
- **Terms of art in technical text:** HTTP cookie → "bickie"/"bikkie" (20 times in one doc), a build →
  "knock together", struct and humidity fields → "paddock", "new ciphertext" → "brand-spankin'-new". The
  dialect table already skips cookies in technical text, but the dictionary's swaps don't know the genre.
  The fix: a `not_in: [technical]` on entries, as the dialect table has, or a genre veto on concepts.
- "esky" for the adjective "cooler" ("your body stays esky"), the POS guards' next case: an adjective, not a
  noun.
- "bush" for "forest" in compounds ("national bush", "bush health experts"), and "Parliament House" for an
  American "Congress".
- "of course" (a sentence adverb) → "too right" / "bloody oath"; "afraid" (I suspect) → "scared stiff";
  "supposed to" → "reckoned"; "dead" for "really"; "properly" for "very".
- Mild over-colour for the register: "Nah, nah" / "Righto" for a plain FAQ "No." / "Yes."; "carked it" in an
  obituary; "mitts" in a burns notice; "a pressie" in news.
- **Words under discussion and quotations:** "guys" swapped in a post about the word "guys", "quid" inside a
  quoted American's line, "Yes, We Cran" and "weren't chicken" (puns), the verbatim FOMC statement. The engine
  should leave quoted text, and words used as words, alone.

**Engine bugs:**
- "war" matched inside the dialect "warn't" ("stoushn't");
- "1/4" broken into "give a 1 the nod/4";
- drawl inside markdown link text and headings ("[Findin' ways …]", "Minimizin' the Risk");
- fillers before a play's speaker labels ("Anyway, HALE:");
- "Well," / "Now," connectives in news, which genres.yaml allows but the agents and judges read as yarn
  colour;
- "family of American a muso" (an article kept after an adjective);
- "lunch or tea (tea)" (a gloss in brackets swapped too).

**Lint and validation:**
- **Real bugs:**
  - `repeated: a bit full` whenever plain "full" appears three times, because an entry's variant is just
    "full": count a use only on the entry's own form.
  - `dialect: y'all` blocks a submit when the original itself has it, because lint_only ignores the original.
  - "meter" still flagged in one water-meter sentence, after a word the device list lacks.
  - "a bit rough" and "shame" flagged `dubious_meaning`.
  - name checks: "Mr Gladden" for "Mr. Gladden", "Thanksgivin'", a capital after a bold label, "Effective
    Friday".
  - `repeated_phrase` on a recipe's or notice's own terms ("cut", "frying pan or", "to per cent").
- **Lint re-suggests declined phrases:** the agents decline "punters", "esky", "paddock", then lint offers them
  again. Suggestions could skip the plan's declined phrases, and should carry the same sense guards as the
  plan.
- **Submit doesn't notice a planned phrase moved to another spot** ("lobbed").

**Genre misreads:** a 1922 obituary with a dateline, a 1927 sports column, a StackExchange Q&A, the TTS welcome
letter, an encyclopedia entry and the Wikivoyage petrol guide all came through as "story", with yarn openings.
A dateline, and words like "died" and "funeral", should be enough for news. George Ade's fable came through as
news.

**The brief:**
- DIFFICULT_SENTENCES lists the terms a technical or news genre says to keep ("advection", "jurisdiction").
- At vulgarity 0 the brief still carries the swearing craft rules.
- Nothing says whether a heading's text may be retold, or whether °F may carry a bracketed °C.

## Vocabulary for a dictionary round

Reached for by the agents and missing from lookup. These are candidates only, unreviewed (CLAUDE.md: each needs
its sense, trigger, level and vulgarity checked):
- **wowser**, **lair**, **lurk**, **sheila**, **truckie**, **cocky** (farmer), **tradie**, **youse**, **hooroo**,
  **chockers**, **within cooee**, **flash** (fancy), **sprung**, **het up**, **keen as mustard**, **knocked for
  six**, **pull the pin**, **done and dusted**, **a do** / **shindig**, **blow-in**, **send-off**, **time in lieu**,
  **roster**, **hang up the boots**, **call time on**, **go off** (food), **in cahoots**, **on the sly**, **pinch**
  (steal), **the once-over**, **easy as**, **a feed**, **brekkie**, **fridge**, **tea towel**, **freezer bags**,
  **baking tin**, **bathroom cabinet**, **punnet**, **cistern**, **tap washer**, **power point**, **choppers**,
  **gridiron**, **rolled oats**, **white sugar**, **Method** (a recipe heading).

The pass also staged 1,746 phrasings from the retellings (`harvest.yaml`) for that round.
