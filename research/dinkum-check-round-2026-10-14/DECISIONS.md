# Dinkum-check round, 2026-10-14: decisions

The input was the dinkum check (`../dinkum-check-2026-10-14/`): the terms the yarn agents reached for, and the
lookups that came back empty or wrong, in `texts/*/yarn-notes.md` (candidates only, unreviewed); the wrong-sense
planned phrases, lint suggestions and lookups the notes list, with the reasons in each text's
`yarn-dinkum-declined.yaml`; and the brief's own candidate list, drawn from the same notes.

As in the earlier rounds, the brief was judgement, not ingestion: add a term only where it is genuinely Australian
and current and a plain-English trigger can be caught reliably in that sense; keep the rest out. General English,
British and American terms are skipped however often Australians say them (gig, chopper, up for grabs, cough up).
Glosses, frames and triggers are our own; `sources` cite Wiktionary (CC BY-SA) where a page for the sense exists
(checked by a HEAD request with the User-Agent `aussiefy-research/0.1`; nothing was taken from the pages; no
definition was copied from fairdinkumslang.au or any other site). Wrong-sense entries cost more than missing ones.

## How it was run

1. Each wrong sense was reproduced first: `aussiefy lint` on the agents' drafts with their originals (the
   suggestions), `aussiefy translate` on the sentences and the whole originals at levels 2-5, seeds 0-3, deadset
   and dinkum, and `aussiefy lookup`. Fixed in data where it could be (exclusions, guard concepts, `not_in`), each
   shown gone while the right sense still swaps; the rest are under "Needs engine changes".
2. Every candidate was checked against the dictionary (forms and variants, concept triggers, the dialect table) and
   judged by hand; the verdicts are in `verify/verdicts-dinkum-check.yaml`.
3. `aussiefy dev round research/dinkum-check-round-2026-10-14 --write` (configured by `round.yaml`) wrote
   `entries/dinkumcheck.yaml`, a section of `concepts.yaml` and one trigger on EVERYWHERE.
4. By hand: stuff {obj} up (see below), RETIRE for pull the pin, BOTCH_IT and three guard concepts, the wrong-sense
   fixes.
5. Testing: sentences for each entry and fix in the right and the wrong senses, in stories and in report and
   policy prose; then every substitution that changed over the test corpora and the dinkum check's and the fourth
   pass's originals (levels 2 and 4, seeds 0-2, each genre's own embellishment) was read, the committed data
   against this branch. `tests/test_dinkum_check.py` pins every entry and fix.

## Counts

| decision | candidates |
|---|---|
| add (dictionary entries, by the round) | 6, as 6 entries in `entries/dinkumcheck.yaml` |
| add (by hand) | 2: stuff {obj} up (in `entries/idioms.yaml`), pull the pin takes RETIRE |
| already covered | 24, one of them (all over the shop) with a trigger added: all over the map on EVERYWHERE |
| skip | 29 |

67 rows in all below: 60 vocabulary candidates (the brief's list and the notes' further terms) and 7 wrong-sense
planned phrases and lint suggestions. 7 new entries, none gated, with 7 new
concepts (6 by the round, BOTCH_IT by hand) and RETIRE by hand; 2 new guard concepts (SCREW_UP_FACE, RETIRED_STATE)
and more phrases for COUNTED_LOTS; `not_in` on EVERYONE, FATHER and CHILD.

## Entries added

| entry | form | concept: triggers | frame | level | vulgarity |
|---|---|---|---|---|---|
| stuff-up | stuff up | BOTCH: screw up, mess up (without an object), botch, bungle, foul up | vp | 2 | 0 |
| stuff-it-up | stuff {obj} up | BOTCH_IT (by hand): screw {obj} up, foul {obj} up, make a mess of {obj} | vp | 2 | 0 |
| a-stuff-up | a stuff-up | BLUNDER: a blunder, a botch-up, a foul-up, a cock-up, a mix-up | np | 2 | 0 |
| under-the-pump | under the pump | UNDER_PRESSURE: under (a lot of / heavy / enormous / intense) pressure, of a person | predicate_adj | 3 | 0 |
| not-know-from-a-bar-of-soap | {subj} wouldn't know {obj} from a bar of soap | NOT_KNOW_AT_ALL: {subj} {do}n't / do not / wouldn't / would not know {obj} from Adam | clause | 4 | 0 |
| spitting-rain | {subj} {be} spitting | LIGHT_RAIN: {subj} {be} drizzling (no object after it), raining lightly, only just raining | clause | 3 | 0 |
| a-swag-of | a swag of (variant a whole swag of) | A_RAFT_OF: a raft of (not logs, pumice, debris...), a slew of, a whole raft/slew/host of | adj | 3 | 0 |

All are `register: current`. By hand, on existing entries:

- **pull the pin** (`idioms.yaml`, QUIT) takes RETIRE: "retire" with nothing after it but a time, a place or an
  adverb ("he retired in 2020" -> "he pulled the pin in 2020", "when I retire" -> "when I pull the pin"). Not
  "retire to bed" or "to the lounge", "retire from" (pull the pin on is calling something off), "retire a jersey",
  "the batsman retired hurt", "retire on a pension". Guard RETIRED_STATE holds being retired and the passive ("she
  is retired now", "the ship was retired in 1990"), which gave "she is pulled the pin". Its gloss names the sense.
  Lookup of "retire" now finds it (it was empty).
- **all over the shop** (`classics.yaml`) gets "all over the map" on EVERYWHERE: the forecaster's "all over the map"
  is the same muddle.

**Why stuff {obj} up is a separate entry, by hand.** One entry with both forms (stuff up, stuff {obj} up) picks
between them at random, and the form without the slot drops a captured object: "She screwed it up again" came out
"She stuffed up again", "Don't make a mess of it" as "Don't stuff up it". So the object triggers have their own
concept (BOTCH_IT) and entry, as make {obj} true blue has beside make true blue. The round's form guard reads
"stuff {obj} up" as the same term as stuff up and drops it, so the entry is written by hand in
`entries/idioms.yaml`, which no round rewrites (moved there in review; a test pins it).

## Wrong-sense fixes

Each was reproduced first; "before" is the committed data, "after" this branch.

| wrong sense | before | fix | still swaps |
|---|---|---|---|
| heaps for "four lots" (groups of questions), lint on the auction FAQ | "split into four heaps" | COUNTED_LOTS takes two ... ten lots, both, several, separate, multiple lots | "loads of fun" -> heaps |
| every man and his dog, every bastard for "one price for everyone" in a doc, "let everyone know" in an obituary | "one price for every bastard" | EVERYONE is `not_in: [official, technical, news, instructions]`: there "everyone" is a quantifier | "Everyone came to the barbie" |
| old fella, old man for an obituary's father (planned and lint) | "his old fella's church" | FATHER is `not_in: [news, official, technical]` | "My father is a farmer" in a story |
| littlie for a policy's "a friend's kid" (planned) | "a friend's littlie into a private school" | CHILD is `not_in: [news, official, technical]`: a kid there is any age, and littlie is too familiar | "The kid ran home" |
| the whole bloody show, box and dice for "everything from country rock to jazz" (lint, the obituary) | "the whole box and dice from country rock to jazz" | EVERYTHING's "everything" refuses "from" (a range) | "They took everything" |
| bucketing down for pouring the tea, and for tears pouring down a face (found in testing) | "She is bucketing down the tea", "Tears was bucketing down down her face" | RAINING_HARD's "pouring" refuses an object or a particle after it (the, a, tea, in, down...); "pouring down" refuses her, his, the... | "It is pouring outside" |

Not data-fixable (see "Needs engine changes"): pressie, choccy, tea, littlie in the gifts policy's lint
suggestions (lint reads the draft's genre, not the original's); flamin' and dead for "completely" in a reassurance;
righto for "(ok, maybe stickers)".

**Not reproduced:** "ok -> righto on the adjectival 'it isn't ok'". Neither translate nor lint touches "it isn't ok"
or "aren't ok"; the only "ok" lint offered righto for was the concessive "(ok, maybe stickers)" in the same draft.
An exclusion (`ok !maybe|perhaps`) can't hold it: a trigger's lookahead stops at the comma.

## Lookup

| query | before | after |
|---|---|---|
| stuff up, a stuff-up | the folding stuff; a fair whack | stuff {obj} up, stuff up; a stuff-up |
| under the pump | crook | under the pump first |
| don't know him from a bar of soap | I dunno | the new entry first |
| a light rain, drizzle; spitting | (empty); spitting chips | {subj} {be} spitting |
| retire | (empty) | pull the pin |
| make a mess of it | | stuff {obj} up, a stuff-up |
| very cold -> coldie, stubby; raining heavily -> on the turps; worked very hard -> stonkered, maggoted; not out of the question -> not on your nelly; up for grabs -> chuck it in; officials -> a happy snap; the big finish -> the big end of town; raise -> a sausage sizzle; high -> high as a kite; hang up -> hang on; make out -> pash; call it a day -> knock off, sickie | | the meaning model (below); no gloss says these |
| weather that's all over the shop | (empty) | still empty: the extra words; "all over the shop" alone finds it |

## Every candidate

"covered" names the entry or rule that already has it.

| candidate | decision | entry or rule | why |
|---|---|---|---|
| stuff up (ruin, botch) | add | stuff-up, stuff-it-up (by hand) | |
| a stuff-up | add | a-stuff-up | not "a mistake" (a misjudgement: "it was a mistake to go") nor "a screw-up" (also a person) |
| cough up | skip | | general English |
| under the pump | add | under-the-pump | of a person: a gas or a pipe under pressure stays; prices "under the pump" is said in Australian finance news |
| up for grabs | skip | | general English |
| sus | covered | suss-suspicious (spelling sus) | the forecaster's "sus, uncertain" isn't its sense |
| all over the shop | covered, trigger added | all-over-the-shop; EVERYWHERE takes "all over the map" | |
| not know someone from a bar of soap | add | not-know-from-a-bar-of-soap | only the "wouldn't" form: "don't know" contracts to "dunno" ("I dunno him from a bar of soap") |
| spitting (light rain) | add | spitting-rain | shared with British English, but the everyday Australian word; drizzling something on food is refused |
| chucking it down | skip | | British; bucketing down is in (bucketing-down) |
| bucketing (down) | covered | bucketing-down | |
| nippy | skip | | British; brass monkeys covers the cold |
| a chopper (helicopter) | skip | | general English (American, from the 1950s) |
| a gig (a job, a performance) | skip | | general English; muso covers the musician |
| the cheap seats | skip | | American |
| a do (an event) | covered | a-do (gated) | its gate stands: "a function" is maths in a doc, "a party" a political party |
| shout (pay for someone) | covered | your-shout (SHOUT: treat {obj} to {np}, pay for {obj}) | "pay for the damage" is left alone |
| cop (cop a fine, cop a shower) | covered | cop {np} (COP_IT: get hit/slapped/stuck with {np}; TOLERATE) | "get a fine" has no {np} the form can carry |
| hang about | skip | | British |
| small potatoes | skip | | American |
| on the sly | skip | | general English |
| whip up | skip | | general English |
| knock up | skip | | the pregnancy sense (American and Australian) |
| get it up (pass a motion) | skip | | the sexual sense, as in the fourth pass |
| headache (a hassle) | skip | | general English; HASSLE is in |
| pull strings | covered | work-the-oracle (PULL_STRINGS) | general English itself |
| CV for résumé | skip | | both are said in Australia (job ads ask for a resume), and "resume" is also the verb |
| retire -> pull the pin | add (by hand) | pull-the-pin takes RETIRE | |
| a whole swag of (a lot of) | add | a-swag-of | Bob Weir's agent; before a plural noun only |
| for yonks | covered | yonks, yonks-ago | |
| had a crack at | covered | have a crack | |
| doing it tough | covered | do-it-tough | |
| called it a day | skip | | general English; pull the pin's gloss |
| a crook shoulder | covered | crook (its gloss, fourth pass) | |
| knock off (beat a team) | skip | | as in the fourth pass |
| hung up the glove (retired) | skip | | general English (hang up the boots) |
| all up | covered | all-up (IN_TOTAL) | |
| give us a bell | covered | give-a-ring's variant give {obj} a bell | lookup misses it (as in the fourth pass) |
| dibs, first dibs | covered | CLAIM (bags) | |
| a fair old mix | skip | | British; the agent dropped it |
| gridiron (the NFL) | covered | gridiron (second pass) | |
| a good day out | skip | | general English |
| swag (merchandise) | skip | | American; a swag is the bedroll |
| a wowser | covered | a-wowser | |
| never minced words, a bit of fun | skip | | general English |
| easy as, have a squiz, suss out, dodgy | covered | easy-as, a-squiz, suss-out, dodgy | |
| quick smart, come good | covered | quick-smart, come-good | |
| gave the nod, give the tick | covered | the tick of approval | |
| done and dusted | skip | | British |
| the mob that runs the estate | covered | that-mob | |
| muso, lobbed, Chrissy | covered | muso, lob, Chrissy | planned phrases, kept |
| till they're stuffed | covered | stuffed | |
| a shonk, slanter, dob in, sting, a swifty, dosh, give a ring | covered | | useful lookups, the agent said |
| a doddle | covered | a-doddle (gated) | British; the gate stands |
| outspoken, pretend, urgent | skip | | no Australian word with a safe trigger |
| no relation | skip | | general English |
| barely budged, chugging along | skip | | general English |
| storm, knocked down | skip | | no Australian word |
| bone dry half the year (riff) | skip | | see "Needs engine changes" (riffs in news) |
| burnin' a hole in their pocket (riff) | skip | | the same |
| littlie (planned, a friend's kid) | fixed | CHILD `not_in` | |
| old man (planned, an obituary) | fixed | FATHER `not_in` | |
| flamin' (planned, "completely passive") | not fixed | | needs engine changes |
| lots -> heaps, everyone -> every man and his dog | fixed | COUNTED_LOTS, EVERYONE `not_in` | |
| gift -> pressie (lint, gifts policy) | not fixed in lint | PRESENT `not_in` holds in translate | needs engine changes |
| dad -> old fella (lint, obituary) | fixed for translate | FATHER `not_in` | lint: needs engine changes |
| ok -> righto | not reproduced | | see above |

## What testing changed

- **stuff up split in two** (see above): with both forms on one entry, "screwed it up" lost its object and "make a
  mess of it" gave "stuff up it".
- **"screw up" crumples a face**: "She screwed up her eyes against the sun" gave "stuffed up her eyes"; guard
  SCREW_UP_FACE (screw up {poss} face/eyes/nose/mouth/courage, screw {poss} face up, screw up the paper/letter).
- **"mess up" untidies**: "He messed up the kitchen" stays; BOTCH's "mess up" takes no object.
- **"pouring" for any pouring**: RAINING_HARD's bare "{subj} {be} pouring" took "She is pouring the tea" and "Tears
  were pouring down her face" (an existing wrong sense, found testing spitting); fixed as in the table.
- **"retire"**: "She is retired now" and "the ship was retired" gave "is pulled the pin" (guard RETIRED_STATE: a
  vp's "be" doesn't inflect to "are" and "were", so those are listed); the Sentimental Bloke glossary's "Retiring;
  reticent" (shy) and "To retire; to withdraw" took pull the pin (a semicolon after "retire" is refused; "shy and
  retiring" and the like are guarded).
- **a raft of** took a raft of logs; floating things after it are refused.
- **not know from a bar of soap**: a "{do}n't know" form came out "I dunno him from a bar of soap"; only the
  "wouldn't" form is kept.
- **"ok, maybe"**: tried `ok !maybe|perhaps` on OK_THEN and righto's `replaces`; it didn't hold (the lookahead stops
  at the comma), so it was taken out again.

## Corpus check

Every substitution that changed over the test corpora and the dinkum check's and the fourth pass's originals
(levels 2 and 4, seeds 0-2, each genre's own embellishment, the committed data against this branch):

| text | change | verdict |
|---|---|---|
| the 1922 obituary (in the corpus, the fourth pass and the dinkum check) | father: old fella, old man -> father | fix |
| the GitHub gifts policy (the same three) | kid: littlie, ankle biter, nipper -> kid | fix |
| NWS lightning safety, GitHub flow, Rust 1.98.1 release notes | everyone: every man and his dog -> everyone | fix (instructions and docs) |
| the Sentimental Bloke glossary | Kid, Children: littlie, nipper... -> kept (the glossary reads as news) | neutral: the glossary's own headwords |
| the Sentimental Bloke glossary | "Guy, to do a.—To retire." -> "To pull the pin." | loss accepted: Dennis's "do a guy" is clearing out; a definition's bare "To retire." can't be told from retiring (Unsure) |
| New England weather, the corpus READMEs, the Interfold constitution, Mulga Bill, the Emperor | everything: box and dice <-> shebang <-> bloody show | neutral: the rolls moved (one more swap, "None -> the whole box and dice") |

## Golden changes (tests/corpus/golden.yaml, regenerated)

One output changed: "It's pouring down, so bring your sweater." at L5s0 and L5s1, where bucketing down, pissing down
and the cow on a flat rock swap places (the rolls moved; RAINING_HARD's "pouring down" now carries its exclusions).
Neutral.

## Needs engine changes (not fixed: engine code is out of scope)

- **Lint's suggestions read the draft's genre, not the original's.** `lint._suggestions` translates the draft on its
  own, and a retelling with a voice reads as a story (the gifts policy draft: story 3.85, official 2.98), so a
  concept's `not_in` doesn't hold there: pressie, choccy, tea and littlie are still suggested in the gifts policy,
  every man and his dog in the auction FAQ and the obituary, old fella in the 1922 obituary. The fourth pass's
  PRESENT `not_in` holds in translate and plan (pinned), not in lint. Passing the original's genre (lint already
  computes `read_as` for the dialect check) would fix all of them.
- **A form that leaves a captured slot unused drops it.** An entry's forms are picked at random among those whose
  slots can be filled, and one without {obj} is "usable" when an object was captured ("screwed it up" -> "stuffed
  up"). Preferring the forms that use every captured slot would let stuff up be one entry.
- **The round tooling** reads a slot variant as the same term ("stuff {obj} up" = stuff up) and drops it, and still
  writes no `not_in`, no guards and no concept that carries an existing entry (RETIRE, BOTCH_IT).
- **A trigger's lookahead stops at punctuation**, so "(ok, maybe stickers)" can't be told from "Ok, let's go": a
  concession takes righto.
- **A vp's "be" inflects to is, was, been, being only** (`morph.verb_forms`), so a vp guard on "be retired" misses
  "are retired" and "were retired", which RETIRED_STATE lists by hand.
- **`^person` lets an unknown noun through** ("prices are under the pump", which is said; "the coach is under
  pressure" isn't swapped, since coach isn't a known person noun).
- **The meaning model** (lookup): "very cold" -> coldie, stubby; "raining heavily" -> on the turps; "worked very
  hard" -> stonkered, maggoted, full as a boot; "not out of the question" -> not on your nelly (a negation read as
  a refusal); up for grabs -> chuck it in; officials -> a happy snap; raise -> a sausage sizzle; high -> high as a
  kite; hang up -> hang on; make out -> pash; call it a day -> knock off, sickie. These need the model's negation
  and sense checks; no gloss says them. A query with extra words ("weather that's all over the shop") finds
  nothing where the phrase alone does.
- **An intensifier in a reassurance**: flamin' and dead for "completely passive with no emissions" (the USGS survey,
  planned and lint), as in the fourth pass's "Keep flamin' still".
- **Riffs that claim a fact**, offered in news: "bone dry half the year" for Yellowstone's creeks, spliced into a
  list by the draft ("rivers, creeks, bone dry half the year, and lakes"); "burnin' a hole in their pocket" for an
  official's suitcase of cash. A riff in news or official prose adds a claim or a joke the genre rules out.
- **Lint and submit**: US spelling flagged inside a quoted directive the official genre keeps verbatim (the FOMC's
  "percent"), and inside a quote in news (Ford's "standardize"); `name_dropped` for "the 42nd President, Bill
  Clinton" (an appositive comma) and "pre-cut Chrissy trees" (a capitalised common noun); "repeated: cut" for the
  original's own plain word. Not this round's (lint.py is being changed elsewhere).

## Unsure

- **a cock-up** is a BLUNDER trigger: British input only, and "a stuff-up" is the Australian for it.
- **a mix-up** is gentler than a stuff-up (a confusion, not a bungle); "there was a stuff-up with the tickets" reads
  right, so it stays.
- **pull the pin for "retire"** in news at level 4 ("Teheran pulled the pin"): Australian sports writing says it;
  news is deadset, but the swap is the level's.
- **spitting** and **a swag of** are shared with British (spitting) or informal news English (a swag of); kept as
  everyday Australian, as sure as eggs and go halves were.
- **"To retire."** in a glossary definition (Dennis's "do a guy", to clear out) takes pull the pin; nothing in a
  bare "To retire." says which sense.
- **EVERYONE out of news**: "Everyone in town turned out" in a casual news story loses every man and his dog; news
  "everyone" is mostly the plain quantifier.

## Review

Reviewed before the merge (spot checks in context, and a design review):

- **RAINING_HARD and LIGHT_RAIN** took any subject: "Fans were pouring onto the street" became "Fans was bucketing
  down", "Tears were pouring down" rain, and "she was drizzling" spitting. Their triggers now name the weather's
  "it" ("it {be} pouring"), and most of the exclusion list goes. The matcher now gives a clause trigger's own
  opening pronoun to the form's {subj}, as a {subj} slot would: before, "it {be} freezing" realised as "Yer brass
  monkeys" (COLD_WEATHER had the bug already).
- **stuff {obj} up** moved to `entries/idioms.yaml`, so re-applying the round can't delete it.
- **UNDER_PRESSURE** says what `^person` takes (a pronoun or a name): "the coach" doesn't swap.


## Underware integration status, 14 October 2026

The decisions above record the round's intermediate state. The final source commits and this integration
resolve original-genre lint suggestions through the existing context seam, keep held dialect wording/counts,
move the shared held-span rule to `text.py`, and filter riff offers by the resolved embellishment. LIGHT_RAIN
and RAINING_HARD use the weather's literal `it`; immediate non-weather pouring complements are excluded.
The retained engine limitations above remain research follow-ups unless marked resolved here. The current
implementation and regressions are under the layered test paths `tests/functional/test_dinkum_check.py`,
`tests/functional/test_fourth_pass.py` and `tests/contributor/test_fourth_pass_harness.py`.
