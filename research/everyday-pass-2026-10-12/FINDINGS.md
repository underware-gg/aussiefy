# Everyday pass: results and findings

59 texts from the everyday corpus, each at one level (2-5, round-robin). Each had three candidates:
- **engine:** `aussiefy translate`, seed 1, from the commit the pass was prepared at, before the fixes below;
- **yarn:** a subagent running yarn mode by hand with `aussiefy yarn-tools`;
- **unharnessed:** a subagent with only the brief.

Six judge subagents scored each set blind under rubric version 2 (`texts/*/card.txt`, `summary.json`).

## Results

| candidate | mean | first | meaning | sense | authenticity | register | tone | flow | variety | essence |
|---|---|---|---|---|---|---|---|---|---|---|
| yarn | 4.68 | 63% | 4.68 | 4.51 | 4.54 | 4.81 | 4.58 | 4.63 | 4.81 | 4.85 |
| unharnessed | 4.67 | 37% | 4.97 | 4.66 | 4.66 | 4.29 | 4.97 | 4.73 | 4.10 | 4.95 |
| engine | 2.35 | 0% | 3.32 | 2.20 | 1.34 | 1.66 | 3.02 | 2.25 | 1.56 | 3.41 |

By level, mean (share ranked first):

| level | engine | yarn | unharnessed |
|---|---|---|---|
| 2 | 3.27 (0%) | 4.67 (50%) | 4.69 (50%) |
| 3 | 2.26 (0%) | 4.67 (57%) | 4.63 (43%) |
| 4 | 1.93 (0%) | 4.63 (53%) | 4.70 (47%) |
| 5 | 1.89 (0%) | 4.75 (93%) | 4.63 (7%) |

By group:

| group | engine | yarn | unharnessed |
|---|---|---|---|
| conversational | 2.42 (0%) | 4.57 (43%) | 4.65 (57%) |
| instructions | 2.14 (0%) | 4.72 (75%) | 4.68 (25%) |
| interfold | 2.31 (0%) | 4.69 (50%) | 4.78 (50%) |
| news | 2.49 (0%) | 4.74 (75%) | 4.63 (25%) |
| workplace | 2.36 (0%) | 4.67 (63%) | 4.67 (37%) |

Verify, the deterministic check, summed over the 59 texts. The last column is the share of sentences of five
or more words left as they were:

| candidate | critical | major | minor | untouched |
|---|---|---|---|---|
| engine | 0 | 13 | 30 | 34% |
| yarn | 0 | 0 | 72 | 3% |
| unharnessed | 1 | 12 | 49 | 6% |

**What it says:**
- **Yarn mode already matches or beats the unharnessed agent.** Their means are about equal, but yarn is
  ranked first on 63% of texts against 37%, and on 93% at level 5. It wins on register and variety (the
  brief's weight, and a range of genuine slang). The unharnessed agent wins on meaning, tone and sense: it
  keeps the original's tone and facts more faithfully, because the harness's wrong-sense plan pulls yarn
  writers off course. That is consistent with the yarn agents' reports below.
- **The engine is far behind and gets worse as the level rises:** 3.27 at level 2, 1.89 at level 5. It
  was never ranked first. Its weak criteria are authenticity (1.34), variety (1.56), register (1.66) and
  sense (2.20). On everyday text it leaves 34% of longer sentences untouched, and what it does swap often
  takes the wrong sense. The fixes below target sense; coverage needs the vocabulary round.
- **Harvest:** 2,125 candidate phrasings staged from the yarn and unharnessed retellings (`harvest.yaml`),
  for a dictionary round.

## Findings

What the first manual pass over the everyday corpus turned up, before the fixes. The sources:
- the engine's swaps across all 59 texts (`pass.py prepare`), which I read through;
- the yarn agents' reports;
- the judges' verdicts (`texts/*/card.txt`, once collected).

Note: some engine fixes landed in the working tree while yarn agents were running (and one broke it
briefly with a syntax error). So a few later yarn briefs were planned by a slightly newer engine than
`engine.txt`. The engine outputs in `texts/*/engine.txt` are all from the commit the pass was prepared at.

## Wrong senses and broken grammar in the engine's swaps

**Systematic causes, fixed in the engine:**
- **Similarity fallback accepting fragments of a trigger.** "working" was taken as *not working* (and
  became "stuffed"), "losing" as *losing it* ("a few snags short of a barbie"), "under the" as *under the
  weather* ("crook"). The fallback now needs a span with as many words as the trigger: a misspelling has
  its trigger's shape.
- **Words inside multi-word names.** "United Nations" became "United mobs", "Boston University" became
  "Boston uni", and the "U.S. Food and Drug Administration" lost "Food" to "Tucker". A capitalised word
  next to another capital is now left alone. A lone name like Christmas can still be swapped.
- **Possessive plurals.** "a children's game" became "a littlies's game". These are no longer swapped.
- **Predicates about people on things.** "the water jackets are full" became "stuffed", and "the tank may
  be drained" became "rooted, knackered". Concepts marked `person` now refuse a plain-noun subject that
  isn't a person (the dictionary's person nouns, common roles, and plural agent nouns like "hikers").
- **Inflection.** "lob" made "lobed" (now "lobbed": one-syllable verbs ending consonant-vowel-consonant
  double the consonant). "a dart" listed the plural "darts" as a variant, which made "dartses".

**Triggers too loose, tightened in the data:**

| Original | Engine gave | Why it's wrong |
|---|---|---|
| people, citizens | battlers | battlers are the struggling poor, not people in general |
| the nation, community | mob | "across the mob" for *across the nation*, "the Kurdish mob" |
| task(s) | yakka, hard yakkas | yakka is uncountable hard work |
| build, built | knock together | building reliable software or a society isn't knocking it together |
| figure, expect | reckon | "a picturesque reckon", "Reckon a cold night" |
| field(s) | paddock(s) | struct fields, fields of study |
| relative | rello | "elevated relative to the goal" |
| zero | sweet bugger-all | "the sweet bugger-all ciphertext" |
| less | maggoted | maggoted means drunk |
| live | keep on kickin' | "playing live" |
| dedicated to | dead set on | "50% of proceeds dedicated to liquidity" |
| a good many | a beaut many | an idiom of quantity |
| dollar bill | quid bill | quid has no bill |
| food colouring, food safety | tucker colouring | food as a modifier |
| agree to (a verb) | gave raise the target range the nod | the slot took a verb phrase |
| taste than | have a crack at than | "taste" as a noun |
| done in any case | stuffed | "done in" as a phrase |
| packed while frozen | chockers | "packed" as packing |
| pay attention to | give a stuff about | means caring at all, usually negated |
| loads (of dishes) | heaps | a count, not a lot |

**Still open:**
- **Tone.** Contemptuous person swears in neutral or safety text: "If some mongrel is struck by
  lightning", "every bastard", "little buggers" for millions of children.
- **Garnish in the wrong genre.** It goes before script speaker labels and in headings, after FAQ
  questions, and as pub closers on press releases.

## Yarn mode (from the agents at the wheel)

- **The plan was the weakest input.** Most declines were wrong senses (above). The keep-60% rule then
  pushed agents to work wrong-sense phrases in elsewhere to make the count. That measures compliance, not
  quality. A short plan with one or two wrong picks sits right at the line, and duplicates (7 of 15
  planned phrases were "dunny") pit the rule against the no-repeats guide.
- **One frame for every text.** The system prompt is the same at every level and for every genre ("an
  Australian storyteller ... perform it"). Docs, FAQs, policies, scripts and safety notices need a
  different frame and a colour budget. OPENINGS are story openers on every genre ("True story, this." for
  medicine disposal).
- **The engine draft isn't a floor at level 4.** Agents threw it away and used it to see what to avoid.
- **Riffs are often off-tone** (a redback under the dunny seat in medicine-disposal guidance).
- **Lint false positives:**
  - "meter" (a water meter) demanded as "metre";
  - flagged words inside a direct quotation;
  - `name_dropped` and `name_added` on headings, capitalised common nouns, date localisation ("Oct. 11"
    to "11 October") and names broken across lines;
  - declining a phrase needs its dictionary form, not the form the plan printed ("dartses").
- **Lint misses:** "has a go at you" repeated four times; "pissin'" over the cap at vulgarity 1.
- **Lookup:** verbose (wants a brief mode), and empty for figurative meanings and for sports, trades and
  news vocabulary ("wowser", "hang up the boots", "stoush" for a boxing match, "good riddance").
- **What helped:**
  - the style guide's "how Australians talk" notes;
  - lint's US spelling and US word checks and its repetition warning;
  - the decline mechanism;
  - DIFFICULT_SENTENCES;
  - lookup for confirming a choice;
  - the markup rule.
