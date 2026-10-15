# Fourth-pass round, 2026-10-14: decisions

The input was the fourth everyday pass (`../fourth-pass-2026-10-14/`): the "Vocabulary" list in `FINDINGS.md` and
the terms the yarn agents reached for in `texts/*/yarn-notes.md` (candidates only, unreviewed); the wrong-sense
planned phrases, lint suggestions and lookups FINDINGS and the notes list, with the reasons the agents gave in each
text's `yarn-*-declined.yaml`.

As in the earlier rounds, the brief was judgement, not ingestion: add a term only where a plain-English trigger can
be caught reliably in that sense; keep a genuine term with no safe trigger for lookup only; skip the rest. Glosses,
frames and triggers are our own; `sources` cite Wiktionary (CC BY-SA) where a page for the sense exists (checked by
a HEAD request with the User-Agent `aussiefy-research/0.1`; nothing was taken from the pages), and an entry
without one is `evidence: own` in its verdict. The wrong senses came first (planned, then lint, then lookup):
wrong-sense entries cost more than missing ones.

## How it was run

1. Each wrong sense was reproduced first, with `aussiefy translate` at levels 2-5, seeds 0-3, dinkum and deadset
   (the planned phrases), `aussiefy lint` (the suggestions) and `aussiefy lookup` (with the bundled model), then
   fixed in data: tighter triggers, `!x`/`!=x` exclusions, `not_in`, guard concepts, and a few entries moved to a
   concept of their own. Each fix was shown gone while the right sense still swaps.
2. Every vocabulary candidate was checked against the dictionary (forms and variants, slot forms, concept triggers,
   the dialect table) and judged by hand; the round's verdicts are in `verify/verdicts-fourth-pass.yaml`.
3. `aussiefy dev round research/fourth-pass-round-2026-10-14 --write` (configured by `round.yaml`) wrote
   `entries/fourthpass.yaml` and a section of `concepts.yaml`.
4. By hand: the wrong-sense fixes below; four concepts the round can't write (MEDAL_AWARD for its `not_in`, and
   TOLERATE, ELDERLY, FAIR_AMOUNT, which carry existing entries); the senses added to existing entries (cop, the
   oldies, crook, a fair whack); seven dialect-table lines.
5. Testing: sentences for each fix and each entry in the right and the wrong senses; then every substitution that
   changed over the test corpora and the fourth pass's 59 originals (130 texts, levels 2 and 4, seeds 0-2, the
   genre's own embellishment) was read, the committed data against this branch. `tests/test_fourth_pass.py` pins
   every fix (24 of its 25 wrong-sense cases fail on the committed data) and every entry.

## Counts

| decision | candidates |
|---|---|
| add (dictionary entries, by the round) | 19, as 19 entries in `entries/fourthpass.yaml` |
| reference only (lookup) | 4 (lurgy, grunt, sausage sizzle, not have a bar of), as 4 entries under lookup-only concepts |
| add (by hand, to existing entries) | 4: cop (put up with), the oldies (old people), crook (injured: the gloss), a fair whack (activated) |
| add (dialect table) | 3 (per cent, hire a car, roadworks), as 7 lines in `dialect.yaml` |
| already covered | 28 |
| skip | 35 |

93 rows in all (the brief's list, with "in a flap" and "down the track" listed once, and "a do" with "a proper do"). 23 entries in the round (19
active, 4 reference), none gated, with 20 new concepts; by hand 11 concepts with entries (MEDAL_AWARD, TOLERATE,
ELDERLY, FAIR_AMOUNT, FRONT_UP, CHAMPION_PERSON, ONE_CIGARETTE, FELLOW_MAN, EMPHATIC_REFUSAL, DOUBLE_NO,
REPLY_TO_THANKS) and 15 guard concepts (GET_EXCITED, COUNTED_LOTS, FELLOW_BEFORE_NAME, BREAKFAST_IDIOM,
COLLEGE_OTHER_SENSE, OLDER_CHILD, BOLTED_TOO_LATE, MONEY_IDIOM_OTHER_SENSE, TOSS_OTHER_SENSE, GIFT_TALENT,
CONGRESS_ACTING, STREAM_OTHER_SENSE, FOODS_PLURAL, FEEL_SORRY, DINNER_OUT); FOREST_OTHER_SENSE and HANDS_OTHER_SENSE
took more phrases.

## Wrong-sense fixes: planned phrases

Each was reproduced first; "before" is the committed data, "after" this branch.

| wrong sense | before | fix | still swaps |
|---|---|---|---|
| bush for a legal "wilderness" and a US forest's "forest health" | "a federally designated bush", "improves bush health", "bush health experts" | FOREST_OTHER_SENSE takes designated / federally designated wilderness, wilderness designation, the Wilderness Act, forest health, forest management, forest plan, forest products, forest supervisor | "deep into the wilderness", "the forest was dark" |
| Parliament House for the real US Congress | "Parliament House hasn't acted on the recommendation", "Members of Parliament House voted" | CONGRESS is `not_in: [news, official, technical, instructions]`; its "Congress" refuses a verb after it (has, passed, acted, voted, will, was...: a guard can't end on a verb, see below); guard CONGRESS_ACTING: U.S./US/United States Congress, of Congress (members, an act, the Library), through/by/in/to Congress, and the verb phrase "pass Congress" | "the Capitol", "the legislature" in a story |
| knock together for any "build" | "builds relationships", "We knock together an auction", "the threat builds", "built on infrastructure", "built many types of sites", Gladden "knocked together" a house | CONSTRUCT loses its bare "build" (the third pass's long exclusion list didn't hold: four texts declined it). It keeps put/throw/cobble together and takes "slap together", "rig up" | "They threw together a shed" -> "knocked together" |
| every bastard for refugees, some bugger for a hoped-for husband | the turkey pardon's list of the vulnerable, the fable's husband | not data-fixable: EVERYONE and SOMEONE are already `neutral_person`, and personal and story texts take person swears. See "Needs engine changes" | |
| beaut for "brilliant" meaning clever | "beaut young coders"; testing found "what beaut colours" (bright) | EXCELLENT's "brilliant" refuses a person or a mind after it (young, coders, scientist, student, man, people...) and a light or a colour (sunshine, white, blue, colours...) | "a brilliant game", "a brilliant idea" |
| rapt for "excited" meaning worked up | the mare that "get rapt and desperate", "coders get rapt by learning" | guard GET_EXCITED: get (all/so/too) excited, get overexcited (any tense) | "She was thrilled", "I'm so excited!" -> rapt, stoked |
| do it tough for a forecast's "struggle to" | "Highs will likely do it tough to get out of the 40s" | STRUGGLE's "struggle" refuses to, with, against, for, over, through, up, on... after it | "Families are struggling" -> "doing it tough" |
| pressie in a gifts policy, and in "gift cards" | "No pressies are acceptable for government officials", "pressie cards" | PRESENT is `not_in: [official, news, technical]`; "gift" refuses card(s), shop, tax, certificate, voucher, of (a donation), policy, rule, exceeding, worth...; guard GIFT_TALENT: {subj} {have} / has / had a gift for, a natural/real/rare gift for, the gift of the gab | "She gave me a gift for my birthday" -> pressie |
| a goer inside quoted statements | the FOMC's quoted statement: "reckoned the following statement was a goer" | GO_ALONG (approve, assent to...) is `not_in: [official, technical, news]`: a board's "approved" is a vote. Quotes in a story are dialogue and are translated; keeping them is genres.yaml's `keep_quotes` (not this round's) | "The plan is feasible" -> a goer; "I approve the plan" in a story |
| tucker for "foods", and in food-safety terms | "When thick tucker are cooked" | guard FOODS_PLURAL: thick/these/some/processed/raw/frozen... foods, of foods, the foods, foods such as/like/that/which/are/were (a trigger can't match a singular only, and tucker is a mass noun); FOOD is `not_in: [technical, official]` and refuses preparation, contact, temperature(s), item(s), product(s), container(s), type(s), borne after it | "We need food for the trip" -> tucker |
| quid for "dollar" in exact sums | "sixty cents on any quid", "a quid is worth one hundred and six cents" | guard MONEY_IDIOM_OTHER_SENSE: cents on/in/to the dollar, cents on any dollar, a/the dollar is worth, dollars are worth, the US/Australian dollar, bang for the buck, and the verb phrases pass the buck, buck the trend. DOLLAR's own "dollar" now carries the exclusions quid's `replaces` had (bill, note, coin, amount...), which the bare trigger had bypassed | "It cost ten dollars", "fifty bucks" -> quid |
| You're all good for "Don't worry" as reassurance | the banana-fire post's "Don't worry, it won't explode" | all good (variants you're all good, all good mate) moves to REPLY_TO_THANKS: you're welcome, no problem, not a problem, no trouble, it's fine, that's okay, all good. NO_PROBLEM keeps no dramas, no worries, she'll be right for "don't worry" | "Thanks! No problem." -> all good, no worries, she'll be right |
| fronted up for families arriving | the picnic's "Families fronted up", the Kurdish families arriving in a new country | front up moves to FRONT_UP, lookup only ("present yourself to face something"); ARRIVE keeps rock up and lob | "They arrived late" -> rocked up, lobbed |
| creek for the "northern stream" (the jet stream) | "a stronger northern creek shortwave trough" | STREAM's "stream" refuses shortwave, trough, flow, energy, pattern; guard STREAM_OTHER_SENSE: (the) jet stream, northern/southern/polar/subtropical stream, Gulf Stream, income/revenue/data/audio/video/event stream, workstream | "We swam in the stream" -> creek |
| give a stuff about for "pay attention to" | "Give a stuff about the width of the flapper" (an instruction) | every CARE_ABOUT entry is negative (didn't give a stuff, two hoots, a rat's arse), so its triggers are now only the negative-polarity "care less about" (couldn't care less about -> couldn't give a stuff about), "give a damn about", "give a hoot about": not "care about" ("we care about your privacy"), "pay attention to", "take notice of" | "I couldn't care less about the score" |
| rocks up for things that "show up" | "The food colouring rocks up", "your changes will lob correctly" | ARRIVE's "turn up" and "show up" refuse what follows a thing turning up (in, on, as, correctly, well, again, everywhere, missing...) and an object (turn up the heat). `^person` can't do it on a verb phrase (below) | "He turned up at the party", "She showed up at noon" |
| heaps for counted loads and lots | "60 heaps of dishes" | guard COUNTED_LOTS: loads of dishes/washing/laundry, parking/car/vacant/empty/building/auction lots. "three lots at the auction" stays: a numeral before a noun isn't a pattern (below) | "loads of fun", "lots to do" -> heaps |
| darts for "cigarettes" in a list of amusements | "Sunday baseball, darts and the theatre" | a dart moves to ONE_CIGARETTE ("a cigarette", "a smoke"): one dart, never the plural, which reads as the pub game. Testing found a durry's variant "have a durry" (a verb phrase on a noun entry: "a cigarette" -> "have a durry"): removed | "He lit a cigarette" -> a dart, a ciggie, a durry |
| Not on your nelly for a plain "No" | the Yellowstone FAQ's "No." | not on your nelly moves to EMPHATIC_REFUSAL (absolutely/certainly not, no way, not a chance, over my dead body); found with it, nah, nah ("a doubled no", also offered for the FAQ's "No.") moves to DOUBLE_NO ("no, no") | "Absolutely not!", "No, no, that's not it" -> "Nah, nah" |
| bugger all for "Not much of a housekeeper" | "Bugger all of a housekeeper" | NOTHING's "not much" refuses "of"; its "nothing" refuses but, else, more, less, like, short ("nothing but the napkin", "nothing more" in The Raven) | "Not much happened", "nothing in the fridge" |
| mitts inside "have their hands full" | "Farmers' wives have their mitts full" | HANDS_OTHER_SENSE takes "{poss} hands full", "hands full" | "Keep your hands warm" -> mitts |
| young fellas for the camp's "the boys" | reported by the frog's agent | already held: BOYS_OTHER_SENSE (third pass) takes "of the boys"; no young fella for it in any seed now | "The boy ran home" |
| dead-set legend for "a good man" (a virtuous parson) | "and a dead-set legend" | a dead-set legend moves to CHAMPION_PERSON (an absolute star/champion/hero, a real/true hero); GOOD_PERSON keeps a top bloke, a legend, a good bastard | "She's an absolute star" -> a dead-set legend |
| flamin' for "very"/"completely" in safety lines | "Keep flamin' still" | not fixed: VERY carries every intensifier (dead, bloody, flamin'); see "Needs engine changes" | |
| a shocker for "felt terrible" (remorse) | "I felt a shocker about accidentally stealing the blanket", "felt crook" | guard FEEL_SORRY: feel terrible/awful/bad/dreadful about, feel terrible/awful for, feel terrible/awful that. An exclusion (`terrible !=about`) didn't hold it: the embedding fallback then matched "terrible about" (below) | "The weather was terrible" -> crook, a shocker |
| bloke for the adjective "fellow" | "with bloke Grateful Dead alumni" | "fellow" moves from MAN to FELLOW_MAN (bloke and cove), `not_in: [news, official, technical]`, where it is nearly always the adjective; it refuses alumni, members, citizens, students, workers, travellers, players, colleagues... after it; guard FELLOW_BEFORE_NAME: "fellow {obj}" (a one-word name: fellow Texans). Before a longer name in a story nothing holds it (below) | "Some of these young fellows" -> blokes, "a fellow" -> a bloke |

## Wrong-sense fixes: lint suggestions

| suggestion | fix | still suggested |
|---|---|---|
| shoot through, clear out for "getting going", "heads off to", "head off to Avail" (data) | LEAVE's "head off" refuses a destination or an object after it (to, for, into, home, back, out, the, it, trouble...); "get going" refuses on, with, again, at, in, early, soon | "We'd better head off", "Let's get going" |
| shoot through for "the horse has bolted", "bolted the shelf onto" | guard BOLTED_TOO_LATE (the horse has/had (already) bolted); RUN_OFF's "bolt" refuses an object or a particle after it (the, it, onto, on, to, down, together, shut) | "He bolted." |
| lob, rock up, front up for things that "turn up" | as above (ARRIVE) | "He turned up at the party" |
| stick out like a sore thumb for "sticks out" (projects) | CONSPICUOUS's "stick out" refuses of, from, over, through and an object ("stick out your tongue") | "It sticks out like that" |
| go troppo, lose the plot for "don't go mad" (overdo) | GO_MAD's "go mad/crazy/nuts" refuse with, on, for, over | "She'll go mad if she finds out" |
| bugger all in "Nothing in this communication is advice", "nothing else", "nothing's hidden" | NOTHING is `not_in: [official, technical]` (a quantifier, not a quantity) and refuses but/else/more... | "nothing in the fridge" |
| no bugger, no bastard for "nobody" in a letter | judged fine: a personal letter takes person swears, and the agent's reason was the letter's swear count, not the sense | |
| quid for "the buck stops", "pass the buck" | DOLLAR's "buck" (and quid's `replaces`) refuse stops/stopped/stop/up after it; pass the buck, buck the trend are guarded | "fifty bucks" |
| the pollies for "the government" meaning agency staff | POLITICIAN is `not_in: [official, technical, instructions]` | "Ask the government" in a story |
| the joint for a city in news | PLACE is `not_in: [news, official, technical, instructions]` | |
| have a crack at for "have a go at" meaning criticise | TRY_OUT drops "have a go at {np}": it is Australian already and as often criticising as trying. TRY's noun "a go" still offers a crack inside it (Unsure) | "try it", "give it a try" |
| the whole box and dice for "the whole lot of you" | EVERYTHING's "the whole lot" refuses "of" | "They took the whole lot" |
| a lucky bugger for "you'd be lucky if" | LUCKY's "lucky" and "fortunate" refuse if/to | "He's very lucky" |
| brekkie inside "a proper dog's breakfast" | guard BREAKFAST_IDIOM (dog's breakfast) | "I had breakfast" |
| stoush for "war stories", for the verb "battle to" | WAR's "war" refuses the compounds (stories, memorial, veterans, crimes, zone, time, effort, dead...); "battle" refuses to/for/against/of/with; "conflict" refuses of/between/with/resolution | "It was a long war" |
| battle on for rain that keeps going overnight | ENDURE's "keep going" refuses overnight, through, until, into, for, all, on | "Keep going!" |
| dilly for "thick" (thick air, thick with vapour) | STUPID's "thick" refuses with/and and is `^person` (a predicate, where `^person` works) | "He's thick" |
| a caper, a lurk for "a racket" (noise) | caper's `replaces` loses "a racket" (the classics entry already said never to) | "a get-rich-quick scheme" |
| too right, bloody oath for an in-sentence "of course" | not reproduced: "Of course she was faster" takes nothing now | |
| suss ... out for "work it out" (reckon a margin) | suss out's `replaces` loses "work {obj} out" | "check it out", "size him up" |
| the Big Smoke for "the city" in news, "the cities" | CITY is `not_in: [news, official, technical, instructions]`; "the city" refuses council, hall, limits, centre, of, officials... | "Life in the city was hard for a bushie" |
| chuck for "coin toss" | guard TOSS_OTHER_SENSE (coin toss, toss of a coin, toss-up, the toss, win/lose the toss); THROW's "toss" (and chuck's `replaces`) refuse to/with/together/gently/until/salad (a recipe's toss) | "Toss me the keys" |
| rug up for "bundle up" (pack an app) | DRESS_WARMLY's "bundle up" refuses an object | "Bundle up, it's cold" |
| I dunno for "She had no idea", "It's got no idea" | DONT_KNOW loses its bare "no idea" (keeps "I have no idea", "I don't know") | "I have no idea" |
| g'day for a surprised "Hello" | not fixed: a greeting and a surprised "hello" are both interjections at a clause start (Unsure) | |
| uni for a US "college" | judged right (an American college is a uni); guard COLLEGE_OTHER_SENSE for the Electoral College, a community college, a college of surgeons... | "He left college" |
| littlie for older kids, and for the verb "kid" | guard OLDER_CHILD (high school, college, teenage, grown, adult, older kids/children); CHILD's "kid" refuses yourself, around, me, you... | "The kids played" |
| choccy for a box of chocolates as a corporate gift, a cookie's value | CHOCOLATE is `not_in: [official, technical]` | in a story or a recipe |
| tea for a client's dinner, "dinner (supper)" | DINNER is `not_in: [official, technical, news]`, refuses party, jacket, meeting, in, at...; guard DINNER_OUT (out for/to dinner, a dinner, business/client/state/gala/formal dinner, lunch or dinner, Christmas/Sunday dinner...); tea's `replaces` carry the same exclusions (the bare one bypassed them) | "Dinner is ready" -> tea |
| a bad trot for "Not a bad run" | judged fine: "not a bad trot" reads right | |
| come hell or high water for "no matter what you shovel into him" | NO_MATTER_WHAT's "no matter what" refuses a following clause (you, he, it, the, happens, people...) | "We'll be there no matter what" |
| no bloody way for "No ID, no go." | not fixed: "ID" after "No" is read as a name, a vocative ("No, John"), so the interjection passes (below) | |
| the oldies for "the folks" (people) | PARENTS's "the folks" (and the oldies' `replaces`) refuse at, from, who, in, of, here, there, around... | "My folks are visiting" |
| give a stuff about for "care about" (positive) | as above (CARE_ABOUT) | |

## Lookup

| query | before | fix |
|---|---|---|
| the drum | noggin | new entry the drum (THE_REAL_STORY) |
| won't cop it, tolerate | no worries; crack hardy | cop takes TOLERATE ("put up with {np}") and its gloss the sense; lookup now offers cop first for both |
| give a hoy | sing out, give a burl | new entry give {obj} a hoy (CALL_OUT) |
| injured | sloshed (the trained model) | crook's gloss names "injured or not working right (a crook knee)"; lookup offers crook |
| old people | (parents only) | the oldies takes ELDERLY |
| the boss | noggin | the boss cocky now ranks first (it was in the dictionary) |
| spendthrift -> tight-arsed, for sure -> clear out, dry/bone dry -> a billabong, drink water -> skol, sign up -> rock up/too easy | | the meaning model; no gloss or description says these (see below) |
| give them a bell | give a hiding | not fixed: the form is give {obj} a bell (give a ring's variant); lookup doesn't match a slot to "them" (below) |
| hot -> spunky | | right: "hot" (attractive) is spunky's sense |

## Entries added

| entry | form | concept: triggers | frame | level | vulgarity |
|---|---|---|---|---|---|
| give-a-hoy | give {obj} a hoy | CALL_OUT (existing): give {obj} a shout, give {obj} a holler | vp | 3 | 0 |
| the-drum | the drum | THE_REAL_STORY (existing): the lowdown, the inside story/word | np | 3 | 0 |
| thats-your-lot | that's your lot | THATS_ALL: that's all, that is all, that's all there is (a clause of its own) | interjection | 3 | 0 |
| go-for-your-life | go for your life | GO_AHEAD: go ahead, help yourself, be my guest, feel free (a clause of its own) | interjection | 3 | 0 |
| sure-as-eggs | sure as eggs | SURE_AS_CAN_BE: (as) sure as can be, (as) sure as anything | adv | 3 | 0 |
| the-go | the go | WAY_TO_GO: the way to go (ending its clause: not "the way to go home") | np | 3 | 0 |
| a-curly-one | a curly one (variant a curly question) | TRICKY_QUESTION: a tricky/tough/difficult/hard question, a tricky one | np | 3 | 0 |
| come-good | come good | TURN_OUT_FINE: turn out fine/all right/okay, work out fine/all right/okay | vp | 3 | 0 |
| sting-overcharge | sting {np} | OVERCHARGE: overcharge {np} | vp | 3 | 0 |
| go-halves | go halves | SPLIT_COST: split the bill, split the cost(s) (not "of"), go fifty-fifty, go Dutch | vp | 3 | 0 |
| down-tools | down tools | STOP_WORK: stop work (not on/at/in), walk off the job, go on strike | vp | 3 | 0 |
| get-over-the-line | get {obj} over the line | FINISH_LINE: get {obj} across/over the finish line, across the line | vp | 3 | 0 |
| down-the-track | down the track | LATER_ON: further/somewhere/later down the road or the line, at some point in the future | adv | 2 | 0 |
| take-longer-than-a-wet-week | take longer than a wet week | TAKE_FOREVER: take forever, take ages | vp | 4 | 0 |
| that-mob | that mob | THAT_CROWD: that crowd, this crowd | np | 3 | 0 |
| like-a-kid-on-red-cordial | like a kid on red cordial | HYPER: bouncing off the walls, hyper (of a person) | predicate_adj | 4 | 0 |
| run-the-ruler-over | run the ruler over {np} (variant {obj}) | ONCE_OVER: give {np} the once-over, cast an eye over {np}, look {obj} over | vp | 4 | 0 |
| get-out-of-the-road | get out of the road | GET_OUT_OF_THE_WAY: get out of the way | vp | 3 | 0 |
| a-gong | a gong | MEDAL_AWARD (by hand, `not_in: [official, technical]`): a medal (not of), an award (not of, ceremony, winning, rate, wage) | np | 3 | 0 |
| the-lurgy | the lurgy | MINOR_BUG (lookup only) | np | 3 | 0 |
| grunt-power | grunt | ENGINE_POWER (lookup only) | np | 3 | 0 |
| a-sausage-sizzle | a sausage sizzle | SAUSAGE_SIZZLE (lookup only) | np | 2 | 0 |
| not-have-a-bar-of | not have a bar of {np} | WANT_NO_PART_OF (lookup only) | vp | 4 | 0 |

All are `register: current`. By hand, on existing entries:

- **cop** (`cop {np}`, classics) takes TOLERATE ("put up with {np}": "had to put up with his snoring" -> "had to cop
  his snoring", "won't put up with it" -> "won't cop it"), and its gloss the sense.
- **the oldies** takes ELDERLY (the elderly, elderly/old/older people, the aged but not aged care or the aged
  pension), `not_in: [news, official, technical, instructions]`; its gloss names the general sense.
- **crook**: the gloss names "injured or not working right (a crook knee)". No trigger: "injured" and "bad" go
  before people and things that a crook would misread (an injured player, a bad idea).
- **a fair whack** (gated `dubious_meaning` since the gap-fill round) is reviewed and active: the "sizeable amount"
  sense is current in Australian speech, and the gate came from A_LOT, whose "a lot" and "very much" are adverbs too
  ("I travel quite a lot" isn't a fair whack). It moves to FAIR_AMOUNT (a fair/sizeable amount, a hefty/tidy sum,
  a lot of money) and drops the adverbial "quite a lot" from its `replaces`.

## Dialect table (dialect.yaml, `us:`)

| American | Australian | note |
|---|---|---|
| rental car(s) | hire car(s) | |
| car rental | car hire | |
| rent a car / a van / a truck | hire a car / a van / a truck (`frame: vp`) | a house or a flat is still rented |
| road construction | roadworks | |
| percent | per cent | `not_in: [technical]`: a doc's percent-encoding |

## What testing changed

- **Guards after a pronoun, and guards ending on a verb.** "She has a gift for languages" wasn't held by "has a
  gift for" (a noun-phrase match right after a pronoun is refused as a verb), so GIFT_TALENT also has "{subj}
  {have} a gift for"; "they pass the buck", "it passed Congress" and "we won the toss" became verb-phrase guards.
  "the buck stops", "Congress has" and the like are refused as guards because they end on a finite verb, so those
  senses are exclusions on the trigger instead.
- **Exclusions the `replaces` bypassed.** A bare `replaces` that repeats a trigger matches the same span, so the
  concept's exclusions don't hold: quid's "buck", chuck's "toss", the oldies' "the folks" and tea's "dinner" now
  carry them.
- **"felt terrible about"**: the first fix, `terrible !=about`, sent the span to the embedding fallback, which
  matched "terrible about" to it by shape (below); a guard holds it now.
- **"the fellow"**: restricting "fellow" to "the/this/that fellow" lost "a fellow" (a swap doesn't keep "a") and made
  "fellows" singular ("these young bloke"); the bare trigger came back with its exclusions, and genres.
- **Descriptions and glosses without slang.** The first drafts said "not rapt", "tucker is a mass noun", "none is a
  quid", "aren't a pressie", "not littlies or ankle biters", and glossed with their own forms ("give us a hoy",
  "the oldies at the bowls club", "it cost a fair whack"): every lower-case word there becomes a plain word
  (`Dictionary.plain_words`). All reworded; the new plain words are ordinary English only.
- **Reference set** (`tests/test_static.py`): "a good mate of mine" twice ranked a new description above FRIEND
  (CHAMPION_PERSON's "a good man ... a champion", then FELLOW_MAN's "a man, called a fellow..."); both reworded, and
  all 33 required checks pass without a retrain. `aussiefy embedder status` will report the model stale against
  the bigger dictionary, as after every round.
- **that mob** has no "this mob" variant: a kept "that" went before it ("that this mob").
- **Accepted after a look** (corpus): the merchant's "to look it over" -> "to run the ruler over it" and the
  letter's "looking me over" -> "running the ruler over me"; "50 percent" -> "50 per cent" in the EPA guide and
  the FOMC minutes; the turkey pardon's "the sick and the elderly" -> "the oldies" (a personal speech; casual but
  warm); the cornbread's "lunch or dinner (supper)" -> "lunch or dinner (tea)" (the agent took tea for the evening
  meal there).
- **Losses accepted**: "built a house of straw" -> knocked together (the pigs) is gone with every other "build";
  the brick house in the same story was the wrong sense. The Drover's Wife's "the city" and Gettysburg's "that
  war" take the Big Smoke and stoush in fewer seeds (the rolls moved).

## Golden changes (tests/corpus/golden.yaml, regenerated)

34 outputs changed; each is a fix or neutral, with one loss:

| input | level/seed | change | verdict |
|---|---|---|---|
| Hello everyone! Grab your sunglasses... | L3s0-L5s0 | every bugger <-> every man and his dog; infixes reshuffled | neutral: the rolls moved |
| She is very lucky and extremely happy... | L3s1, L5s0 | very lucky <-> a lucky bugger <-> luckier than a shithouse rat | neutral |
| The kids want candy and chocolate biscuits. | L2s1-L5s1 | littlies -> kids / little tackers | neutral (CHILD's "kid" changed) |
| Honestly, he is a nice guy and a hard worker. | L3s0, L4s0 | a dead-set legend -> a legend | fix: a nice guy isn't an absolute champion |
| Everyone at university is lazy. | L3s0-L5s1 | every bugger / bastard / bloke and sheila / man and his dog reshuffled | neutral |
| The Emperor's New Clothes | L3s0-L5s0 | "what beaut/grouse colours" -> "what brilliant colours" | fix: bright, not excellent |
| | L1s0-L5s0 | nothing <-> bugger all, every bugger, infixes reshuffled; "No, no" at L1 kept rather than "Nah" | neutral |
| Gettysburg | L3s0, L4s0 | "of that stoush" -> "of that war" | neutral loss: the rolls moved (L5 keeps stoush elsewhere) |
| | L3s0-L5s0 | "who did it tough" -> "who had a proper crack" | neutral |
| Hansel and Gretel | L3s0-L5s0 | "Yeah, but nah" -> "Yeah, nah" for "No, wife"; tea -> dinner (L4s0) | neutral (nah, nah left the plain no) |
| The Raven | L3s0-L5s0 | "and nothing more" -> was "and bugger all (more)", "sweet bugger-all", "fuck all"; now stays "nothing" | fix: "nothing more" is "only this" |
| The Story of the Three Little Pigs | L3s0-L5s0 | "knocked together a house of straw/furze/bricks" -> "built" | fix for the brick house, loss for straw (see above) |
| | L2s0, L3s0 | tea <-> dinner | neutral |

## Needs engine changes (not fixed: engine code is out of scope)

- **A person swear with a warm referent.** "every bugger" for "everybody who's trying to get a second chance" (the
  vulnerable, in a speech about compassion) and "some bugger" for a hoped-for husband: EVERYONE and SOMEONE are
  `neutral_person`, but story and personal texts take person swears. The data can't say "not of people the text is
  being kind about"; a check of the clause the person is in (a sympathetic list, a wish) would.
- **`^person` does nothing on a verb phrase.** It is checked only where a predicate's subject is found; a `vp`
  trigger's subject isn't looked for, so "the rain arrives", "the keys turned up", "the rain will keep going" and
  "the project is getting going" pass. ARRIVE, ENDURE and LEAVE carry exclusion lists instead, and a thing turning
  up "at" somewhere still rocks up.
- **A negative-polarity marker** (say `^neg`: a "not", "never" or "n't" before the trigger). Every CARE_ABOUT entry
  is said in the negative, so "care about" was taken off ("we care about your privacy"), losing "she didn't care
  about it" -> "didn't give a stuff about it". With the marker, "care about ^neg" could come back.
- **The embedding fallback counts a trigger's exclusions in its shape check.** "felt terrible about" refused
  `terrible !=about` and was then matched to it by similarity, since "terrible about" has as many tokens as the
  pattern's elements (a literal and an exclusion) and a length within two characters. The check should count only
  the literal words.
- **A guard can't end on a finite verb** ("the buck stops", "Congress has"): the noun-phrase part-of-speech check
  reads its last word as a verb with a subject before it. Guards are meant to claim words, so they could skip it.
- **A span holding part of a multi-word name is refused, guards too**, so "fellow Grateful Dead alumni" can't be
  guarded; FELLOW_MAN is kept out of news, official and technical texts instead, but a story's "fellow New
  Yorkers" would still become "bloke New Yorkers". "fellow" before a capitalised word could be refused as the
  adjective.
- **An `np` trigger can't keep "a".** `KEPT_DETERMINERS` has the, this, that, these, those and possessives, so a
  pattern that includes "a" loses it ("a fellow" -> "bloke").
- **A counted noun**: a numeral before "lots" or "loads" ("three lots", "60 loads of dishes") is a count, not "a
  large amount"; only the listed compounds are guarded.
- **Quotes**: a goer inside the FOMC's quoted statement, quid in a quoted American's "50 bucks" (Wikivoyage): which
  genres keep quotes is `genres.yaml`'s `keep_quotes`, not this round's.
- **An intensifier on a hazard or a product claim**: flamin', dead and bloody all carry VERY, and only a swear
  intensifier is held by the infix rule; "Keep flamin' still" in a safety step and "flamin' easy" in a selling point
  need an entry-level "exasperated" tone the infix rule can read, or a genre rule for intensifiers.
- **A capitalised word after "No" is read as a name** (a vocative, "No, John"), so "No ID, no go." passes as an
  interjection.
- **Lookup**: a slot form isn't matched against a concrete pronoun ("give them a bell" doesn't find give {obj} a
  bell); opposites and single-word matches from the meaning model (spendthrift -> tight-arsed, for sure -> clear
  out, dry -> a billabong, sign up -> rock up) need the model's negation and sense checks, not data.
- **The round tooling** writes no `not_in` and no guard concepts, and a concept carrying an existing entry can't be
  a round's new concept (MEDAL_AWARD, TOLERATE, ELDERLY, FAIR_AMOUNT are by hand, outside the round's section).

## Unsure

- **"have a go at" still offers "a crack" inside it**: TRY's noun "a go" matches "having a go at popular
  amusements" (criticising); "have a go at it" (trying) is the common sense, so it stays.
- **"Yeah, but nah"** can still answer a factual "No." in an FAQ; it is a considered no, milder than nelly.
- **the oldies for "the elderly"** is warm in a personal speech but casual; it is out of news and official prose.
- **knock together** is gone from every "build", including the rough-and-ready ones (a straw house, a cubby), which
  only "throw/cobble/slap together" and "rig up" now reach.
- **a fair whack** has no source for the "sizeable amount" sense (the gap-fill note); activated on judgement.
- **sure as eggs, go halves, down tools, that's your lot, a gong, the lurgy, sting** are shared with British English;
  kept as everyday Australian choices, as keen as mustard and pear-shaped were.
- **do a duck** (an agent doubted it): it is C. J. Dennis's (the Sentimental Bloke glossary) and the entry is
  already `register: archaic`, so it is offered only where archaic terms are; left as is.
- **"Hello" as surprise** -> g'day stays: no pattern tells a surprised hello from a greeting.
- **knock off (beat a team)**: its form is knock off work's ("knock off" is one form key), and "defeat" would read
  as killing or stealing; not added.

## Every candidate

From `FINDINGS.md` and the agents' notes. "covered" names the entry or rule that already has it.

| candidate | decision | entry or rule | why |
|---|---|---|---|
| a blow-in | covered | a-blow-in (NEWCOMER) | |
| within cooee / not within cooee | covered | within-cooee | the negative is the same form after "not" |
| cop (put up with) | add (by hand) | cop takes TOLERATE | "put up with {np}" |
| give us a hoy | add | give-a-hoy | CALL_OUT's "give {obj} a shout" |
| give someone a bell | covered | give-a-ring's variant give {obj} a bell | lookup misses it (needs engine changes) |
| hooroo | covered | hooroo, say-hooroo (dated) | |
| chockers | covered | chockers | |
| sure as eggs | add | sure-as-eggs | the sentence adverbs only |
| bucketing down | covered | bucketing-down | |
| first dibs | covered | CLAIM's dibs triggers (bags) | |
| sting (overcharge) | add | sting-overcharge | "overcharge {np}" |
| the go ("X is the go") | add | the-go | "the way to go" ending its clause |
| till the cows come home | skip | | general English |
| down tools | add | down-tools | |
| go halves | add | go-halves | |
| par for the course | skip | | general English |
| come good | add | come-good | |
| carry the can | skip | | general British |
| a curly one | add | a-curly-one | questions only |
| the horse has bolted | skip | | general English; now guarded (BOLTED_TOO_LATE) |
| boffins | skip | | general British |
| red cordial | add | like-a-kid-on-red-cordial | |
| lurk | covered | a-lurk | |
| boss cocky | covered | the-boss-cocky (dated) | |
| double-dipping | skip | | general English |
| the drum | add | the-drum | |
| twig | covered | twig (gated not_aussie) | as in the third pass |
| a skerrick | covered | a-skerrick | |
| dab hand | skip | | general British |
| the damage (the cost) | skip | | as in the third pass |
| quick smart | covered | quick-smart | |
| the mob (a group, an outfit) | add | that-mob | mob's own entry is a community |
| a do, a proper do | covered | a-do (gated) | its gate is "a party" (a political party); left |
| a gong | add | a-gong | out of official and technical prose |
| lurgy | reference | the-lurgy | no safe trigger ("a bug" is software) |
| a dud | skip | | general English |
| knock over (finish a task) | skip | | no safe trigger, and it reads as topple or rob |
| down the track | add | down-the-track | the figurative phrases |
| a fair whack | add (by hand) | a-fair-whack activated on FAIR_AMOUNT | reviewed: see above |
| jumper weather | covered | jumper (sweater weather -> jumper weather) | |
| rug up | covered | rug-up | |
| dry as a dead dingo's donger | covered | dry-as-a-dead-dingo (THIRSTY) | |
| lonely as a shag on a rock | covered | lonely-as-a-shag-on-a-rock | |
| strike me pink | covered | g-aside-strike-me-pink (dated) | |
| run the ruler over | add | run-the-ruler-over | |
| toe the line | skip | | general English |
| no dramas | covered | no-dramas | |
| happy as Larry | covered | happy-as-larry | GET_EXCITED keeps it off "get excited" |
| proud as punch | skip | | general British |
| not much chop | covered | not-much-chop | |
| longer than a wet week | add | take-longer-than-a-wet-week | |
| a cracker of a (job) | covered | a-cracker-of-a-day | a general "a cracker of a {np}" has no safe trigger |
| out of the blue | skip | | general English |
| grunt (power) | reference | grunt-power | "power" and "horsepower" have other senses and figures |
| get it up (pass a motion) | skip | | the sexual sense |
| stay out of its road | add | get-out-of-the-road | |
| in a flap | skip | | general British |
| over the line (got it done) | add | get-over-the-line | |
| a good wrap (praise) | covered | give-a-big-wrap | |
| have a squiz | covered | a-squiz | |
| run yer eye over | skip | | general British |
| in cahoots | skip | | general English |
| that's yer lot | add | thats-your-lot | |
| tot up | skip | | general British |
| go for yer life | add | go-for-your-life | |
| safe as houses | skip | | general British |
| I'm blowed if | skip | | dated British |
| clean up (win big) | skip | | general English |
| sausage sizzle | reference | a-sausage-sizzle | no plain name to swap |
| guts (belly) | skip | | general English |
| wet a line | skip | | general English (angling) |
| give us a hand | skip | | general English |
| give a toss | skip | | general British; CARE_ABOUT's negative entries say it |
| roadworks | add (dialect) | road construction -> roadworks | |
| knickers in a twist | skip | | general British |
| pull someone up (on something) | skip | | general British |
| clocked (noticed) | skip | | general British |
| a stickybeak | covered | stickybeak | |
| not want a bar of | reference | not-have-a-bar-of | "have anything to do with" is also a question |
| no relation | skip | | general English |
| someone's patch | skip | | general English |
| per cent | add (dialect) | percent -> per cent | the Australian style |
| tea towel | covered | dialect: dish towel -> tea towel | |
| freezer bags | skip | | not an American/Australian difference (ziploc bag -> snap-lock bag is in the table) |
| full-cream milk | covered | dialect: whole milk -> full-cream milk | |
| had him pegged | skip | | general English |
| on side | skip | | general British |
| pitched in | skip | | general English |
| hire (US rent a car) | add (dialect) | rental car, car rental, rent a car/van/truck | |
| time in lieu | covered | dialect: comp time -> time in lieu | |
| crook (injured) | add (by hand) | crook's gloss | no safe trigger |
| knock off (beat a team) | skip | | see Unsure |
| the oldies (old people in general) | add (by hand) | the-oldies takes ELDERLY | |

## Review

Reviewed before the merge: the decisions table, the new entries' triggers in context (two seeds at level 5), and the
golden changes listed above. Three slips were fixed:

- **that mob** took "this crowd" too, flipping what was pointed at: THAT_CROWD keeps "that crowd" only.
- **the drum** shared THE_REAL_STORY, so "The real story is that the dam failed" became "the drum is that…". The
  drum is inside word passed on: it moves to its own concept, INSIDE_WORD (the lowdown, the inside word). The good
  oil keeps the real story.
- **sting** was inflected regularly ("stinged"): it joins morph's irregular verbs (stung).

Each is pinned in `tests/test_fourth_pass.py`. The straw house's lost "knocked together" is accepted: the build
trigger it came from was the wrong-sense one.


## Underware integration corrections, 14 October 2026

The historical candidate table describes the source round. SPLIT_COST now requires an explicit fifty-fifty
cost split: a generic bill split or going Dutch may involve unequal or multiple shares and cannot establish
halves. The replay verdict uses the same narrowed triggers; positive halves and rejected multiparty/Dutch
cases are covered in `tests/functional/test_fourth_pass.py`. Weather shorthand keeps literal-subject agreement
while rejecting immediate liquid-pouring complements. These reviewed corrections supplement the round's
original decisions rather than reporting a new paid evaluation.
