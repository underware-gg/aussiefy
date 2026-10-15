# Third-pass round, 2026-10-13: decisions

The input was the third everyday pass, the embellishment pass (`../embellishment-pass-2026-10-13/`): the
"Vocabulary" list in `FINDINGS.md` (terms the yarn agents reached for that lookup didn't have; candidates only),
the 3,101 phrasings staged in `harvest.yaml`, and the list of wrong-sense planned phrases and lint suggestions the
engine still produced (FINDINGS' "Wrong-sense planned phrases" and "Lint suggestions miss idioms", with the reasons
the agents gave in each text's `yarn-*-declined.yaml`). The harvest is mostly noise (contractions, drawl, numbers,
merged diff spans); it was mined for recurring Australian vernacular the dictionary lacks.

As in the earlier rounds, the brief was judgement, not ingestion: add a term only where a plain-English trigger can
be caught reliably in that sense; keep a genuine term with no safe trigger for lookup only; skip the rest. Glosses,
frames and triggers are our own; `sources` cite Wiktionary (CC BY-SA) where a page for the sense exists (checked by
a HEAD request with the User-Agent `aussiefy-research/0.1`; nothing was taken from the pages), and an entry
without one is `evidence: own` in its verdict.

## How it was run

1. Every FINDINGS term and every harvest phrasing that looked Australian was checked against the dictionary
   (forms and variants, slot forms such as `do {objposs} head in`, concept triggers and the dialect table), then
   `lookup`/`show`.
2. Each wrong sense was reproduced first, with `aussiefy translate -l 4|5 -e dinkum|deadset` over seeds 0-3 and with
   `aussiefy lint`, and then fixed in data (tighter triggers, `!x`/`!=x` exclusions, `not_in`, new concepts and
   guard concepts), and shown gone while the right sense still swaps.
3. Each vocabulary candidate was judged by hand; the verdicts are in `verify/verdicts-third-pass.yaml`.
4. `aussiefy dev round research/third-pass-round-2026-10-13 --write` (configured by `round.yaml`) wrote
   `entries/thirdpass.yaml`, a section of `concepts.yaml` and two triggers on COMPLAINER.
5. By hand: the wrong-sense fixes (below), two concepts the round can't write because they need `not_in`
   (FISHERMAN, AMERICANS), eight guard concepts, LITTLE_BOY, and seven dialect-table lines.
6. Testing: sentences for each fix and each entry in the right and the wrong senses, over seeds 0-3 at levels 2-5,
   dinkum and deadset; then every substitution that changed over the everyday, reference and classics corpora (106
   texts, levels 2 and 4, seeds 0-2, the genre's own embellishment, deadset and troppo) was read, before (the
   committed data) against after. `tests/test_third_pass.py` pins every fix and entry.

## Counts

| decision | candidates |
|---|---|
| add (dictionary entries) | 21 (20 from FINDINGS, 1 from the harvest), as 23 entries in `entries/thirdpass.yaml` |
| add (dialect table) | 1 (punnet), as 7 lines in `dialect.yaml` |
| reference only | 1 (is she buggery: an entry under a lookup-only concept) |
| already covered | 27 (21 from FINDINGS, 6 rows from the harvest); sook's concept also took "crybaby" |
| skip | 14 (8 from FINDINGS, 6 rows from the harvest) |

64 rows in all (a row may group a few phrasings). 24 entries (23 active, 1 reference), none gated; 21 new concepts
from the round, and by hand FISHERMAN, AMERICANS and LITTLE_BOY plus eight guard concepts (no entries):
BOYS_OTHER_SENSE, FOREST_OTHER_SENSE, DEDICATED_TO, VIABLE_OF_LOOKS, FIELD_OTHER_SENSE, HANDS_OTHER_SENSE,
MONEY_COMPOUND, AMERICANS_GROUP.

## Wrong-sense fixes (by hand)

Each was reproduced first; the "before" outputs are the committed data, the "after" this branch.

| wrong sense | before | fix | still swaps |
|---|---|---|---|
| beaut for any "good" | "beaut mates", "Beaut riddance", "a beaut imitation", "Beaut work", "a beaut sport", "a beaut seal", "my beaut appointment", "a beaut fortune" | GOOD loses its bare "good" trigger (beaut was the only entry on it, and "good" is mostly other senses: close friends, passable, well done, tight). "nice" and "lovely" keep it, but not before a person noun, "work", "try", "of" or "to" ("nice of you", "nice to meet you") | "a lovely day", "a lovely voice", "a nice field of turnips", and every EXCELLENT trigger |
| young fellas for any "boys" | "one of the boys" (a teammate), "the boys here" (the men of a mining camp), "Regards to all the boys" | guard BOYS_OTHER_SENSE: the boys, one/all/of the boys, boys and girls, old boy(s), baby boy(s), oh boy, boys will be boys | "The boy ran home", "a young man" |
| little fella for any child | "your kid", "small children" in a bear-safety step, "our children", "a toddler", "my child" | little fella moves from CHILD to a new concept LITTLE_BOY (little boy, small boy, little lad); CHILD keeps littlie, little tacker, nipper and the rest | "The little boy cried" -> "little fella"; "a small boy" (the Sentimental Bloke glossary) |
| bush for US land terms and idioms | "a national bush" (Yellowstone FAQ), "national bush by the Department of Agriculture", "neck of the bush" | guard FOREST_OTHER_SENSE: national/state forest(s), the Forest Service, forest ranger/district/land/road, wilderness area, neck of the woods, out of the woods, rain forest, forest floor/canopy | "We walked in the woods", "the forest was dark" |
| dead set on for "dedicated to" | "50% of proceeds dead set on liquidity", "dead set on the proposition that all men are created equal", "dead set on his wife" (devoted to), "dead set on win" (determined to) | COMMITTED's triggers are now only phrasings "dead set on" replaces word for word: intent on, (hell-)bent on (not "bent on one knee"), determined on. Taking "dedicated to" off exposed SANCTIFY's "dedicate" ("christened to her work"), so the guard DEDICATED_TO holds "dedicated (here/there) to" | "He was bent on revenge", "intent on winning" |
| swear blind for "resolve" | "its continuing swear blind to achieve" (a noun), "efforts to swear blind difficult issues" (sort out), "highly swear blind that these dead...", "told him not to swear blind" (curse) | RESOLVE (swear blind's concept) is now "insist that something is true": swear up and down, swear that, solemnly swear that, swear on {poss} life that. Not resolve, vow (swear blind takes no "to") or a bare swear | "I swear that it was him" -> "I swear blind it was him"; "swore up and down" |
| a goer for "feasible", said of a woman | "she looked a goer and praiseworthy" | guard VIABLE_OF_LOOKS: feasible/viable after a verb of appearance (looked, seems, appeared), with a pronoun before it, and "she was/is feasible" | "The plan is feasible" -> "a goer" |
| esky for the comparative "cooler" | "An esky airmass will also have moved in" | COOLER's "cooler" no longer swaps before a weather or comparison noun (air, airmass, temperatures, day, night, months, water, front...) or "and"/"or"; the guard COOLER_COMPARATIVE takes "cooler, drier/wetter/cloudier/windier/calmer". Why the guard didn't hold it: it lists the phrases a predicate comparative comes in (stays cooler, a bit cooler) and a few nouns ("cooler air"), and "airmass" wasn't one; the tagger reads "cooler" as a noun before a noun, so nothing else stops it | "Put the drinks in the cooler" -> "esky" |
| the punters in "public, private sector" | "either the punters, private sector or volunteer service" | PEOPLE's "the public" exclusion names the comma and "/" (a mark ends the look-ahead, so it must be named) and adds "private" and "sectors" | "Members of the public" -> "punters" |
| paddock for a field of study or data | "social science paddock(s)", "RH paddocks show residual moisture" | FIELD's exclusion adds "(", show(s/ed), indicate(s), suggest(s); guard FIELD_OTHER_SENSE: {poss} field, science/scientific/technical/related/relevant/appropriate/chosen/medical/legal/academic field, data/RH/wind/temperature/pressure/moisture/text/input/form/search field(s), magnetic/electric/gravitational/force field, playing field, oil/gas field(s), experts/leaders/professionals/researchers/others/work/years/experience/career in the field | "The cows were in the field" -> "paddock" |
| scared stiff for "I am afraid your..." | "I am scared stiff your ideas as to the basis..." | SCARED's "afraid" exclusion adds the determiners and possessives (your, my, the, a, some, no, all...) and someone/something/people: after them "afraid" is "sorry to say" | "She was afraid of the dark" |
| lint: dosh in "pocket money" | "'money' could be: dosh" | guard MONEY_COMPOUND: pocket/prize/seed/hush/protection/danger/spending/lunch/pin/blood/smart money, money order/market/laundering, petty cash, cash flow/register/cow/crop/machine/advance/prize | "I need some money" still suggests dosh |
| lint: mitts for the verb "hands" | "The CCA hands tokens out", "hands you back a ciphertext", "beats hard water hands down", and the scalding report | HANDS's "hands" no longer before its object (me, you, the, a, his, over, out, back, down...); HANDS is `not_in: [technical, instructions, official]` (jokey slang on a burn or a safety step); guard HANDS_OTHER_SENSE: farm/deck/hired/ranch/factory/stage hands, all/old hands, in good/safe/capable hands, change(d) hands, time/blood on {poss} hands, {poss} hands are tied, hands down, with {poss} bare hands, on {poss} hands and knees | "Hands off my car" (the agent took it), "Keep your hands warm" |
| lint: come a cropper for a crashing system | "falls over" (a node crashing) and "trip over bugs" in Kubernetes and Rust docs | FALL_OVER is `not_in: [technical]`; and testing found "I came a cropper the cable", so "fall over", "fall down" and "trip over" now refuse an object after them | "She fell over in the street" |
| lint: beaut in "good sport", bush in "neck of the woods" | as above | the GOOD and FOREST fixes | |

Found while testing, fixed the same way:

- **ENDURE's "hold out"** took "Hold out your hands, boys" -> "Battle on yer mitts": it now refuses an object
  (your, the, a, it, hope, little, much, hands...).
- **FALL_OVER's transitive uses** (above): "tripped over the cable" lost its object.
- **SANCTIFY's "dedicate"** (above): held by DEDICATED_TO for the participle; "dedicate this book to my mother"
  is still "christen this book", left alone because Gettysburg's "dedicate a portion of that field" is the sense
  the entry is for (Unsure).

## Entries added

| entry | form | concept: triggers | frame | level | vulgarity |
|---|---|---|---|---|---|
| pull-the-pin-on | pull the pin on {np} (variant {obj}) | CALL_OFF: call off {np}, call {obj} off | vp | 3 | 0 |
| drag-the-chain | drag the chain | DRAG_FEET: drag {poss} feet, lag behind | vp | 3 | 0 |
| nut-out | nut out | NUT_OUT: figure out, hammer out, thrash out, puzzle out | vp | 3 | 0 |
| give-a-ring | give {obj} a ring (variant a bell) | RING_UP: give {obj} a call, give {obj} a phone call | vp | 2 | 0 |
| heres-the-go | here's the go | HERES_THE_DEAL: here's/here is the deal, here's/here is the plan | np | 3 | 0 |
| whats-the-go | what's the go | WHATS_THE_DEAL: what's/what is the deal (not worth, for, between, on, size), what's/what is the plan (not for) | np | 3 | 0 |
| first-in-best-dressed | first in, best dressed | FIRST_COME: first come, first served (and hyphenated) | np | 2 | 0 |
| workmate | workmate | COWORKER: coworker, co-worker | np | 1 | 0 |
| fisho | fisho | FISHERMAN (by hand, `not_in: [news, official, technical, instructions]`): fisherman, fishermen, angler | np | 3 | 0 |
| yank | Yank (plural Yanks) | AMERICANS (by hand, the same `not_in`): Americans; guard AMERICANS_GROUP holds African/Native/Asian/black/white/South... Americans | np | 4 | 0 |
| a-tragic | tragic | DIEHARD_FAN: die-hard/diehard fan, die-hard/diehard supporter | np | 3 | 0 |
| cheap-as-chips | cheap as chips | DIRT_CHEAP: dirt cheap, dirt-cheap, very/really inexpensive | predicate_adj | 2 | 0 |
| on-song | on song | IN_TOP_FORM: in top/fine/great/peak form, on top form | predicate_adj | 3 | 0 |
| streets-ahead | streets ahead of | FAR_BETTER: far superior to, vastly superior to, miles ahead of | predicate_adj | 3 | 0 |
| go-pear-shaped | go pear-shaped | GO_WRONG_BADLY: go awry, go haywire, go badly/horribly/terribly wrong | vp | 3 | 0 |
| a-good-innings | have a good innings | GOOD_INNINGS: live a long and full life, a long and happy life, a long life, a full and long life | vp | 3 | 0 |
| all-up | all up | IN_TOTAL: in total (not before darkness, silence, control, contrast...) | adv | 2 | 0 |
| a-fair-few | a fair few | QUITE_A_FEW: quite a few | adj | 2 | 0 |
| brolly | brolly | UMBRELLA: umbrella (not term, organisation, group, body, policy, insurance, fund, of, for...) | np | 2 | 0 |
| out-bush | out bush | OUT_BUSH: out in the countryside/sticks/boondocks/backwoods, in the boondocks | adv | 2 | 0 |
| chuck-a-tanty | chuck a tanty | THROW_TANTRUM: throw/have a tantrum, throw/have a hissy fit, pitch a fit | vp | 3 | 0 |
| a-tanty | a tanty | TANTRUM (existing: a tantrum, a hissy fit, a fit of temper) | np | 3 | 0 |
| muck-up | muck up | MISBEHAVE: misbehave (shared with PLAY_UP's play up) | vp | 2 | 0 |
| is-it-buggery | is it buggery (variants is she/he buggery) | EMPHATIC_NO (lookup only): a periphrasis that never occurs | interjection | 4 | 1 |

All are `register: current`. Triggers appended to an existing concept: COMPLAINER takes "crybaby", "cry-baby"
(whinger, sook). THROW_TANTRUM shares "throw a tantrum" and "have a tantrum" with LOSE_TEMPER, which merges the two
readings on that span, so chuck a tanty never lands on "lost his temper".

## Dialect table (dialect.yaml, `us:`)

| American | Australian | note |
|---|---|---|
| pint(s) of strawberries, pint(s) of blueberries, pint of raspberries | punnet(s) of ... | a pint of milk or beer is left alone |
| pint of cherry tomatoes, pint of grape tomatoes | punnet of cherry tomatoes | |

## What testing changed

- **Yanks** went to level 4 and out of news, docs, instructions and official prose: in Obama's turkey-pardon
  speech "20 million more Americans ... who finally have health insurance" became "20 million more Yanks", flippant
  for a sober statistic. The hyphenated groups are held by a guard.
- **fisho** keeps out of news (a park notice's "Anglers will be able to fish these rivers" took it) and the rest.
- **FISHERMAN and AMERICANS are written by hand** outside the round's section, for their `not_in` (a round rewrites
  its section when re-applied, and writes no `not_in`).
- **Guards after a pronoun.** VIABLE_OF_LOOKS's "looked feasible" never held "She looked feasible": a noun-phrase
  match right after "she" (or i, we, they, he, to) is refused as a verb, so the guard also has "{subj} looked
  feasible" (and FIELD_OTHER_SENSE "to {poss} field").
- **Descriptions without slang.** The first descriptions said "not young fellas", "pocket dosh", "aren't mitts",
  "a goer", "christened": every lower-case word in a description is a "plain word" (lint, garnish and the target
  benchmark read them), so "fellas" became plain and the Gettysburg benchmark lost its "old fellas" row (recall
  58%). They were reworded; recall is back at 15/25.
- **Reference set** (`tests/test_static.py`): "a good mate of mine" ranked a fair few's gloss ("a good number")
  and then IN_TOP_FORM's description ("the top of one's game") above FRIEND; both reworded. All required checks
  pass without a retrain; `aussiefy embedder status` will report the model stale against the bigger dictionary,
  as after every round.
- **Accepted after a look** (corpus): Twain's "you leave your umbrella in the house" -> "brolly"; "a nice field of
  turnips", "a nice potful", "nice apples" -> beaut (gained: beaut now repeats less); "a small boy" (Sentimental
  Bloke glossary) -> "a little fella"; "Thursday will likely be dry, although cooler than Wednesday" stays.
- Wrong-sense sentences that stay plain: "the match was called off" (no object, so no pull the pin), "a tough
  call", "give your mum a call" (not a pronoun), "what is the deal worth?", "the plan for the site", "I worked out
  at the gym", "he is very cheap" (stingy), "in good form" (manners), "far ahead of us", "you can't go wrong",
  "in total darkness", "quite a few of them", an umbrella term/organisation, "under the umbrella of the UN", "he
  lost his temper" (no tanty), "the car acted up" (play up only).

## Golden changes (tests/corpus/golden.yaml, regenerated)

30 outputs changed; every one is a fix or neutral:

| input | level/seed | change | verdict |
|---|---|---|---|
| The kids want candy and chocolate biscuits. | L2s0 | little fellas -> littlies | fix: kids aren't all boys |
| I'm thirsty, grab me a cold beer from the cooler. | L2-L4, s0/s1 | esky <-> cooler, by seed | neutral: the rolls moved; half the seeds still say esky |
| The Emperor's New Clothes | L2s0-L5s0 | "my beaut appointment" -> "my good appointment"; "The beaut [old minister]" -> "good" | fix |
| | L3s0-L5s0 | ripper -> beaut ("magnificent, beautiful, excellent"); hands <-> mitts; infix reshuffles; little tacker -> littlie | neutral |
| Gettysburg | L3s0-L5s0 | "dead set on the proposition" -> "dedicated to the proposition"; "to be dead set on the unfinished work" -> "dedicated here to"; "to be here dead set on" -> "dedicated to" | fix: devoted/allocated to, not determined on |
| | L4s0, L5s0 | "we here highly swear blind that" -> "resolve that" | fix: a vow, not an insistence |
| | L2s0, L3s0 | "a portion of that paddock" -> "field" | neutral loss: the rolls moved (L4 and L5 keep paddock) |
| Hansel and Gretel | L2s0-L5s0 | "feed our little fellas" -> "littlies"; little buggers/tackers/ankle biters/nippers reshuffled | fix, then neutral |
| Little Red Riding Hood | L2s0-L5s0 | "This beaut woman" -> "This (bloody) good woman"; "fell upon the beaut woman" -> "good"; "my little fella" (the wolf to Red) -> littlie / little tacker; infixes reshuffled | fix, then neutral |
| Pride and Prejudice ch. 1 | L2s0-L5s0 | "in possession of a beaut fortune" -> "a (bloody) good fortune"; "are dead set on go" -> "are determined to go"; "chuck in a beaut word" -> "good" | fix (the second also grammar) |
| The Story of the Three Little Pigs | L2s0-L4s0 | "a nice field of turnips", "a nice potful", "Are they nice apples?" -> beaut | gain |

## Needs engine changes (not fixed: engine code is out of scope)

- **"good" needs a positive noun list, as "great" has.** `detect.py`'s GREAT_GOOD_NOUNS lets "great" swap only
  before the nouns where it means excellent; "good" has nothing like it, so the only data fix was to take "good"
  off GOOD, losing "a good day", "good weather", "a good feed" -> beaut. A noun list for "good" and "nice" (better
  in data: a concept-level `only_before:` list) would bring those back safely.
- **No "not a person" constraint.** `^person` asks for a person subject; nothing asks for a thing. "feasible" ->
  "a goer" said of a woman is held only by verbs of appearance (VIABLE_OF_LOOKS); "she is feasible" would still
  pass. A `^thing` marker (refuse a person subject) would be the real fix, and would suit Yanks and the punters too.
- **`^person` does nothing on an `adv` trigger** (no subject is found), so COMMITTED couldn't keep "dedicated to"
  for people ("she is dedicated to her work") and drop it for things ("proceeds dedicated to liquidity").
- **A noun-phrase match right after a pronoun or "to" is refused as a verb** (`check_frame`), guards included, so a
  guard must carry the pronoun ("{subj} looked feasible", "to {poss} field").
- **The tagger reads a comparative before a noun as a noun** ("a cooler airmass": cooler/NN), so COOLER needs a list
  of the nouns that follow a comparative; a JJR-before-noun check would do it generally.
- **An exclusion stops at a mark unless it names it**, so "the public, private sector" needed the comma named
  (which also blocks "The public, it seems, ..."). An exclusion that could look past a comma to the next word would
  be finer.
- **The participle-adjective rule misreads a verb before "all"**: "The kids misbehaved all day" isn't swapped
  ("misbehaved all" is read as an adjective before a noun).
- **The mention check needs a cue word** (from FINDINGS): a forum post listing 'boys' and 'guys' as words wasn't
  held. The BOYS guard doesn't cover a bare listed word.
- **A predicate read before a noun** (known from the fairdinkum round): "These are great disappointments" ->
  "beaut disappointments".
- **"The public loved it" is never swapped** (the keep-its-verb rule refuses a singular verb after "the public");
  only "members of the public" reaches the punters.
- **The round tooling** writes no `not_in` and no guard concepts (FISHERMAN, AMERICANS and the guards are by hand),
  and a re-applied round rewrites its section in `concepts.yaml`, so hand edits there would be lost.

## Unsure

- **Yanks** is affectionate in Australian talk but can read as dismissive; level 4 and out of news, docs and
  official prose. "We Americans" in an American's own voice becomes "we Yanks", which Americans also say.
- **young fellas**: the guard takes every "the boys", so "The boys went to the park" (children) stays plain too.
- **SANCTIFY's "dedicate"** still takes "dedicate this book to my mother" -> "christen this book"; not reported, and
  an exclusion after "dedicate" would risk the Gettysburg sense.
- **cheap as chips, on song, streets ahead, a good innings, a fair few, give someone a ring, pear-shaped** are shared
  with British English; kept as the everyday Australian choice, as keen as mustard and knocked for six were.
- **all up** has a long exclusion list after "in total"; a noun not on it ("in total ruin") would still swap.
- **here's the go / what's the go** are written as noun phrases so their whole lead-in is replaced; "what's the
  plan" covers the plan-ahead sense, "what's the deal" the what's-going-on sense.
- **a tanty, chuck a tanty** are childish by design; THROW_TANTRUM keeps them off "lost his temper".
- **muck up** is the kids' sense (muck-up day); "mess up" (a mistake) isn't a trigger.

## Every candidate

From `FINDINGS.md` (F) and `harvest.yaml` (H). "covered" names the entry or rule that already has it.

| candidate | from | decision | entry or rule | why |
|---|---|---|---|---|
| sunnies | F | covered | sunnies | sunglasses, shades |
| pull the pin on (cancel) | F | add | pull-the-pin-on | with its object: "call off {np}", "call {obj} off" |
| the crook (sick) | F | covered | crook, crook-as-a-dog | |
| oldies | F | covered | the-oldies | |
| a good innings | F | add | a-good-innings | "live a long (and full) life" |
| furphy | F | covered | a-furphy | |
| twig | F | covered | twig (gated not_aussie) | British more than Aussie |
| cheap as chips | F | add | cheap-as-chips | prices only; "very cheap" can be stingy |
| pinch | F | covered | STEAL's "pinch {obj}" (nick) | |
| workmate | F | add | workmate | coworker; not "colleague" (official prose) |
| drag the chain | F | add | drag-the-chain | drag one's feet, lag behind |
| bang on about | F | covered | bang-on (TALK_ON) | |
| give someone a ring / bell | F | add | give-a-ring | "give {obj} a call"; not "a tough call" |
| sing out | F | covered | sing-out | |
| here's the go / what's the go | F | add | heres-the-go, whats-the-go | the lead-ins "here's the deal/plan", "what's the deal/plan" |
| brolly | F | add | brolly | not the figurative umbrella |
| nippy | F | skip | | general British; "chilly" has other senses (a chilly reception) |
| Yanks | F | add | yank | the plural noun; level 4; a guard for the groups |
| bench (kitchen counter) | F | covered (dialect) | kitchen counter, countertop | |
| first dibs | F | covered | bags-claim (CLAIM) | |
| pocket money | F | skip | | general English; "allowance" (travel, baggage, make allowance) has no safe trigger |
| dressing gown | F | skip | | the second-pass review dropped bathrobe -> dressing gown: Australians say both |
| punnet | F | add (dialect) | pint(s) of strawberries/blueberries/raspberries/cherry tomatoes | the fruit named, so a pint of milk stays |
| the damage (the bill) | F | skip | | general English; "how much do I owe you" isn't a safe interjection |
| pear-shaped | F | add | go-pear-shaped | go awry/haywire/badly wrong; not "go wrong" |
| have a gander | F | skip | | general British (as in the second-pass round) |
| lurk | F | covered | a-lurk | |
| offsider | F | covered | offsider | |
| nut out | F | add | nut-out | figure/hammer/thrash/puzzle out; not "work out" |
| on song | F | add | on-song | in top/fine/great form; not "in good form" |
| a wrap (praise) | F | covered | give-a-big-wrap | |
| all up | F | add | all-up | "in total", not before a noun ("in total darkness") |
| tragic (a fan) | F | add | a-tragic | die-hard fan/supporter only |
| hang up the boots | F | skip | | general sporting idiom (as in the second-pass round) |
| chuck a tanty | F | add | chuck-a-tanty, a-tanty | own concept, not "lose his temper" |
| sook | F | covered | sook, have-a-sook | COMPLAINER took "crybaby" |
| off with the fairies | F | covered | off-with-the-fairies | |
| a red-hot go | F | covered | a-red-hot-go | |
| doing my head in | F | covered | do-your-head-in (do {objposs} head in) | |
| fair and square | F | skip | | general English |
| stickybeak (noun) | F | covered | stickybeak (NOSY_PERSON) | |
| first in best dressed | F | add | first-in-best-dressed | "first come, first served" |
| muck up | F | add | muck-up | misbehave; not "mess up" or "act up" |
| fisho | F | add | fisho | fisherman, angler; out of news and official prose |
| truckies | F | covered | a-truckie | |
| out bush | F | add | out-bush | out in the countryside/sticks/boondocks |
| cashed up | F | covered | cashed-up | |
| stony broke | F | covered | stony-broke | |
| is she buggery | F | reference | is-it-buggery | echoes the question's subject; no plain "no" can take it |
| streets ahead | F | add | streets-ahead | "far superior to", "miles ahead of"; not "far ahead of" (a distance) |
| a breather | F | skip | | general English (TAKE_A_REST already triggers on it; take a spell is its dated entry) |
| a fair few | H | add | a-fair-few | "quite a few" before a noun |
| rug up, dig the jumper out | H | covered | rug-up, jumper | |
| a bit of ticker, a no-hoper | H | covered | ticker, no-hoper | |
| smoko, bushwalk(ers) | H | covered | smoko, bushwalking, a-bushwalker | |
| squiz, suss out, servo, tucker, dunny, missus, chuck, bung, reckon, heaps, hard yakka, chockers, chinwag, whinge, musos, coppers, ciggies, uni, pollie | H | covered | their entries | |
| blokes n sheilas, crook, a ripper | H | covered | bloke, sheila, crook, ripper | |
| a heads-up, spot on, pipes up, hand on heart | H | skip | | general English |
| watch yourself, if I say so meself | H | skip | | general English (the second is drawl) |
| now this one's a ripper, then there's | H | skip | | stock openers and a grammar habit, not swaps (the troppo pass's judges marked the opener) |
| temps, mix, spots, plus, swap, handy | H | skip | | general English |
| there's, they're, you'll, till, ya, gonna, 'em, -in' | H | skip | | contractions and drawl (phonetic.yaml) |
| colour, honour, organisations, towards, metres | H | covered | spelling rules | |
| 4 C, 30-50 km/h, hectares, litres | H | skip | | units (the metre rule converts) |

## Review (2026-10-13, after the merge)

Every entry checked as genuinely Australian and current, with its gloss, frame, level and vulgarity. The
triggers were then run in their other senses at levels 2 and 4, seeds 0-3, deadset. Two fixes:

- DRAG_FEET's "lag behind" took an object ("began to lag behind the pack" became "began to drag the chain the
  pack"). It is now intransitive only: it skips a following determiner, possessive, pronoun or "schedule".
- DIEHARD_FAN gave "a tragic of the Bulldogs". "Tragic" takes its team before it ("a Bulldogs tragic"), so the
  triggers now skip a following "of".

Accepted as is: "call off the dogs" becomes "pull the pin on the dogs". It's rare, and every other "call off"
(a search, a wedding, a strike) is the right sense. The integration also showed that the engine work merged
alongside this round covers needs-engine-changes item 8: a text about words now holds its quoted and listed
candidates without a cue word.
