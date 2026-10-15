# Second-pass round, 2026-10-13: decisions

The input was the second everyday pass (`../everyday-pass-2026-10-13/`): the "Vocabulary for a dictionary
round" list in `FINDINGS.md` (terms the yarn agents reached for that lookup didn't have) and the 1,746 phrasings
staged in `harvest.yaml`. The harvest is mostly noise (ordinary English, drawl respellings, merged diff spans,
text-specific retellings); it was mined for Australian vernacular the dictionary lacks, preferring what
recurred across texts or agents, and the Aussie choices the style guide recommends ("meant to", "the odd",
"keen", "reckon").

As in the fairdinkum round, the brief was judgement, not ingestion: add a term only where a plain-English trigger
can be caught reliably in that sense; keep genuine terms with no safe trigger for lookup only; skip the rest.
Glosses, frames and triggers are our own; `sources` cite Wiktionary (CC BY-SA) where a page for the sense exists,
and an entry without one is `evidence: own` in its verdict.

## How it was run

1. Every FINDINGS term and every harvest phrasing that looked Australian was checked against the dictionary
   (forms and variants, concept triggers and the dialect table), then `lookup`/`show`.
2. Each candidate was judged by hand; the verdicts are in `verify/verdicts-second-pass.yaml` (the everyday
   round's verifier format).
3. `aussiefy dev round research/second-pass-round-2026-10-13 --write` (configured by `round.yaml`) wrote
   `entries/secondpass.yaml` and a section of `concepts.yaml`.
4. By hand: one adverb entry (a round can't add a second entry with one form), two concepts the round can't write
   (one needs `not_in`, one is a guard with no entries), and the dialect-table lines.
5. Testing: for each entry, sentences using the trigger in its sense and in other senses, over seeds 0-5 at
   levels 2 and 4, with `-e deadset` and `-e troppo`; then every substitution the new entries and dialect lines
   make over the everyday, reference and classics corpora (levels 2 and 4, seeds 0-2, the genre's own
   embellishment, deadset and troppo) was read. What that changed is under "What testing changed".

## Counts

| decision | candidates (rows below) |
|---|---|
| add (dictionary entries) | 16, as 18 entries: 17 in `entries/secondpass.yaml`, and a fair bit's adverb by hand in `lexical.yaml` |
| add (dialect table) | 8, as 20 lines in `dialect.yaml` (one a guard) |
| reference only | 1 (wouldn't it rot your socks: an entry under a lookup-only concept) |
| already covered | 70 (63 in the dictionary or a trigger of an existing concept, 7 by the dialect table) |
| skip | 37 |

132 rows in all (a row may group a few related phrasings). 19 entries (18 from the round, 1 by hand), none gated;
16 new concepts from the round and 2 by hand (HAPPY_SNAP, which needs `not_in`, and the guard
AMERICAN_FOOTBALL_COMPOUND).

## Entries added

| entry | form | concept: triggers | frame | level | vulgarity |
|---|---|---|---|---|---|
| keen | keen | EAGER: eager ^person | predicate_adj | 1 | 0 |
| keen-as-mustard | keen as mustard | VERY_EAGER: very/really/extremely eager ^person, raring to go ^person | predicate_adj | 3 | 0 |
| keen-on | keen on | KEEN_ON: enthusiastic about | predicate_adj | 1 | 0 |
| meant-to | meant to | SUPPOSED_TO: supposed to | predicate_adj | 1 | 0 |
| the-odd | the odd | OCCASIONAL: the occasional | adj | 1 | 0 |
| a-fair-bit | a fair bit | QUITE_A_LOT (np): quite a lot, quite a bit, a fair amount | np | 1 | 0 |
| a-fair-bit-adv (lexical.yaml) | a fair bit | QUITE_A_LOT (adv): quite a lot, quite a bit, considerably ^adj | adv | 1 | 0 |
| easy-as | easy as | DEAD_EASY: very easy !=to\|for, really easy !=to\|for, easy as pie, a piece of cake | predicate_adj | 2 | 0 |
| done-and-dusted | done and dusted | ALL_DONE: all done !=for\|with\|up, over and done with, all finished !=with, completely finished !=with | predicate_adj | 2 | 0 |
| het-up | het up (variant all het up) | WORKED_UP: worked up ^person, all worked up | predicate_adj | 2 | 0 |
| knocked-for-six | knocked for six | STAGGERED: thrown for a loop, floored ^person, knocked sideways ^person | predicate_adj | 3 | 0 |
| knock-for-six | knock {obj} for six | STAGGER_SOMEONE: throw {obj} for a loop, knock {obj} sideways | vp | 3 | 0 |
| fridge | fridge | FRIDGE: refrigerator !=car\|cars\|truck\|trucks\|van\|vans\|ship\|ships | np | 1 | 0 |
| a-happy-snap | a happy snap | HAPPY_SNAP (`not_in: [technical, news, official]`): snapshot !=of\|in\|shows\|showed\|suggests\|suggested, holiday photo, vacation photo | np | 3 | 0 |
| get-on-the-blower | get on the blower | GET_ON_THE_PHONE: get on the phone | vp | 3 | 0 |
| go-off-food | go off | GO_OFF_FOOD: go rancid, go mouldy, go moldy, spoil quickly, spoil easily | vp | 1 | 0 |
| a-lair | a lair | BOASTER (existing: show-off, braggart, boaster, big talker) | np | 4 | 0 |
| gridiron | gridiron | GRIDIRON: American football | np | 2 | 0 |
| wouldnt-it-rot-your-socks | wouldn't it rot your socks (variant wouldn't it) | EXASPERATION (lookup only): a periphrasis that never occurs | interjection | 5 (dated) | 0 |

All are `register: current` except wouldn't it (dated). Guard concept, by hand: AMERICAN_FOOTBALL_COMPOUND holds
"American football player/team/league/game/coach/fan/field/season/star" (and plurals), so FOOTBALL's footy can't
land inside the American game's name before a noun.

## Dialect table (dialect.yaml, `us:`)

| American | Australian | note |
|---|---|---|
| dishtowel | tea towel | beside the existing "dish towel" |
| granulated sugar | white sugar | "granulated white sugar" isn't caught (no match) |
| cake pan, loaf pan, baking pan | cake tin, loaf tin, baking tin | "baking sheet" was already baking tray |
| old-fashioned oats, old-fashioned rolled oats | rolled oats | "oatmeal" alone stays: it is porridge or rolled oats |
| medicine cabinet | bathroom cabinet | |
| bathrobe, bath robe | dressing gown | |
| electrical outlet, electric outlet, wall outlet, power outlet | power point | a bare "outlet" (a retail or media outlet) isn't touched |
| comp time, compensatory time | time in lieu | |
| travel comp time | (kept) | a guard: the US federal entitlement's name in `tts_travel_comp_time` |
| council member, councilman, councilwoman | councillor | a capitalised title ("Council member Mike Cortese") is left, as the table leaves names |

"American football -> gridiron" was tried in the table first, but the table skips a capitalised word as a name,
so it never fired; it is an entry instead.

## What testing changed

- **keen as mustard got its own concept.** On EAGER beside keen, intensity fit still gave it a plain "eager"
  about a quarter of the time ("he was eager" -> "keen as mustard", overstated). VERY_EAGER takes only the strong
  phrasings.
- **"all done up"** (dressed up) became "done and dusted": "up" joined "for" and "with" in the exclusion.
- **gridiron** moved from the dialect table to an entry (above), and testing found the existing FOOTBALL
  making "an American football player" "an American footy player"; the guard concept holds it.
- **happy snap** keeps out of docs, news and official prose, and "snapshot of/in/shows/suggests" is blocked
  everywhere: "a snapshot of the economy", "take a snapshot of the database" and "the snapshot shows a decline"
  are untouched.
- **easy as** can't take a complement, so "very easy to host static files" (in a docs text in the corpus) and
  "easy for you" are blocked; "dead easy" was dropped as a trigger (it copies a reference query).
- Accepted after a look: "I was supposed to leave the blanket behind" -> "meant to"; Boston baked beans "in which
  they are supposed to be cooked" -> "meant to"; "It takes quite a bit of remembering" (a 1927 news story) -> "a
  fair bit of remembering"; the FDA and recipe texts' refrigerator -> fridge, granulated sugar -> white sugar,
  baking pan(s) -> baking tin(s); the NWS lightning notice's "an electrical outlet" -> "a power point"; the FDA
  "medicine cabinet" -> "bathroom cabinet"; Nashville's "council members" -> "councillors"; Daddy-Long-Legs's
  "bath robe" -> "dressing gown".
- Wrong-sense sentences that stay plain: her eager eyes, an eager student, the market is eager (^person); the
  supposed thief, I supposed he was right; an occasional contributor, occasional showers; prices rose
  considerably; we are all done for, I'm all done with him; worked up a sweat, worked up the courage, the plan
  was worked up; the hall was floored with oak; the refrigerator car, a refrigerator truck; the app on the phone;
  don't spoil the surprise, the deal went bad, things went sour; "Can you beat that?" (both senses).
- **keen on lost "a big fan of" and "a huge fan of"**: they caught "a big fan of the type used in barns", and with
  them (and a concept description mentioning a friend) the bundled embedder ranked keen on first for the reference
  query "a good mate of mine" (`tests/test_static.py`). "passionate about" was tried and dropped too: keen on
  understates it ("passionate about justice"). Its description was reworded; all required reference checks pass
  without a retrain (`aussiefy embedder status` will report the model stale against the bigger dictionary, as
  after every round).

## Golden changes (tests/corpus/golden.yaml)

None. `tests/test_golden.py` passes unchanged: no golden input uses a new trigger, so `scripts/regen_golden.py`
wasn't run.

## Engine findings (not fixed: engine code is out of scope)

- **A match right after a sentence-initial capitalised determiner misses a capitalised word.** "An American
  football coach signed." and "The American football coach signed." don't reach the guard (or GRIDIRON) and
  get "footy"; "We saw an American football coach" and "So an American football coach signed" do. It looks like
  the name check reads "An American" / "The American" as a capitalised run.
- **^person doesn't know many person nouns:** "the apprentice was very eager" is rejected ("'apprentice' isn't
  one"), so keen misses it. Safe, but narrow.
- **Intensity fit is soft:** an entry of intensity 5 on a concept whose trigger is 3 still wins about a quarter of
  the time (keen as mustard for a plain "eager"); a concept of its own is the only firm separation.
- **The dialect table skips any capitalised word as a name**, so "American football" (always capitalised) can't
  be a dialect swap.
- **No exclusion looks back**, so "much ^adj" -> heaps ("much better" -> "heaps better", a very Aussie swap)
  can't be written: "so much better" and "how much bigger" would become "so heaps better" and "how heaps bigger".
- **The round tooling** writes a new concept's description and triggers only, not `not_in` or `person`, and
  drops a concept no entry uses, so HAPPY_SNAP and the guard were written by hand outside the round's section;
  and, as the fairdinkum round found, it can't add a second entry with an existing form (a fair bit's adverb).

## Unsure

- **het up** and **keen as mustard** are Commonwealth rather than only Australian; kept as the Aussie choice over
  "worked up" and "very eager". **knocked for six** likewise (cricket English), and its triggers ("floored",
  "thrown for a loop") are narrower than its use.
- **the odd** covers only "the occasional"; "isolated showers" (a forecast's "the odd shower") is left alone,
  since "isolated" has other senses.
- **go off** has deliberately few triggers (rancid, mouldy, spoils quickly/easily): "go bad" and "spoil" are the
  common plain words but have non-food senses.
- **a lair** is current but leans older; level 4.
- **bathroom cabinet** and **dressing gown**: Australians also say "medicine cabinet" and "bathrobe"; the swap
  is the commoner Australian word, not a correction.
- **easy as** at deadset in instructions ("Assembly is very easy." -> "easy as") reads casual; the level gates it
  (2+).

## Every candidate

From `FINDINGS.md` (F) and `harvest.yaml` (H). "covered" names the entry or rule that already has it.

| candidate | from | decision | entry or rule | why |
|---|---|---|---|---|
| wowser | F | covered | a-wowser | |
| lair | F | add | a-lair | the show-off, on BOASTER; the noun with its article only |
| lurk | F | covered | a-lurk | |
| sheila | F, H | covered | sheila | |
| truckie | F, H | covered | a-truckie | |
| cocky (farmer) | F | skip | | as in the fairdinkum round: "a farmer" -> "a cocky" reads as arrogant |
| tradie | F | covered | tradie | |
| youse | F | covered | youse | |
| hooroo | F | covered | hooroo, say-hooroo | |
| chockers | F, H | covered | chockers | |
| within cooee | F, H | covered | within-cooee | |
| flash (fancy) | F, H | covered | flash | |
| sprung | F, H | covered | sprung | |
| het up | F | add | het-up | "worked up" of a person; not "worked up a sweat" |
| keen as mustard | F | add | keen-as-mustard | its own concept (VERY_EAGER) so a plain "eager" isn't overstated |
| knocked for six | F | add | knocked-for-six, knock-for-six | "floored", "thrown for a loop"; not "devastated" (a devastated town) |
| pull the pin | F, H | covered | pull-the-pin | QUIT; the cancel sense ("cancel the trip") would need "cancel {np}", which a passive ("was cancelled") breaks |
| done and dusted | F | add | done-and-dusted | not "all done for", "done with" or "all done up" |
| a do / shindig | F, H | skip | | general English; "a do" collides with the verb |
| blow-in | F, H | covered | a-blow-in | |
| send-off | F, H | skip | | general English (and the harvest used it for a funeral) |
| time in lieu | F | add (dialect) | comp time, compensatory time | the federal "travel comp time" kept by a guard |
| roster | F | skip | | "schedule" has too many senses, and "roster" is American too |
| hang up the boots | F, H | skip | | general sporting idiom; "retire" is too broad a trigger |
| call time on | F | skip | | British; "put an end to" in news and history would read as pub talk |
| go off (food) | F, H | add | go-off-food | food-only triggers; "the deal went bad" isn't "went off" |
| in cahoots | F | skip | | general English (American too) |
| on the sly | F | skip | | general English |
| pinch (steal) | F, H | covered | STEAL trigger "pinch {obj}" (nick) | as output it is British as much as Aussie |
| the once-over | F, H | skip | | general English |
| easy as | F | add | easy-as | the predicate with nothing after it ("very easy to use" blocked) |
| a feed | F, H | covered | a-feed, have-a-feed | |
| brekkie | F, H | covered | brekkie | |
| fridge | F, H | add | fridge | the appliance; not a refrigerator car or truck |
| tea towel | F | covered (dialect) | dish towel | "dishtowel" added beside it |
| freezer bags | F | skip | | the same words in American English |
| baking tin | F | add (dialect) | baking pan, cake pan, loaf pan | |
| bathroom cabinet | F | add (dialect) | medicine cabinet | |
| punnet | F | skip | | "a pint of strawberries" can't be told from a pint of milk without listing fruit; no corpus use |
| cistern | F, H | covered (dialect) | toilet tank | |
| tap washer | F, H | covered (dialect) | faucet -> tap | "faucet washer" becomes "tap washer" |
| power point | F | add (dialect) | electrical/electric/wall/power outlet | not a bare "outlet" |
| choppers | F, H | skip | | general English (American too) |
| gridiron | F, H | add | gridiron | "American football" only, plus a guard for its compounds |
| rolled oats | F, H | add (dialect) | old-fashioned (rolled) oats | a bare "oatmeal" stays ("bowl of oatmeal" was already porridge) |
| white sugar | F, H | add (dialect) | granulated sugar | |
| Method (recipe heading) | F, H | skip | | a heading; headings keep their place, and "procedure"/"directions" have other senses |
| meant to | H | add | meant-to | every sense of "supposed to" ("what's that meant to mean?") |
| the odd | H | add | the-odd | "the occasional" only |
| keen | H | add | keen | "eager" as a predicate of a person |
| keen on | H | add | keen-on | "enthusiastic about"; not "fond of" (keen on a person is romance) or "passionate about" (understated) |
| reckon | H | covered | reckon (THINK) | think, believe, suppose |
| a fair bit | H | add | a-fair-bit, a-fair-bit-adv | quite a lot / considerably; A_LOT's heaps keeps the big amounts |
| happy snaps | H | add | a-happy-snap | a photo snapshot; not in docs, news or official prose |
| on the blower | H | add | get-on-the-blower | "get on the phone" only; a bare "on the phone" also names where a thing is |
| wouldn't it (rot your socks) | H | reference | wouldnt-it-rot-your-socks | "can you beat that?" is also a challenge to beat a record |
| heaps better (much better) | H | skip | | untriggerable: no exclusion looks back ("so much better"); heaps is in |
| grunt (engine power) | H | skip | | shared with British and NZ, and "horsepower" usually follows a number |
| top-shelf | H | skip | | general (American top-shelf liquor) |
| fair's fair | H | skip | | general English |
| bagging (criticising) | H | covered | bag (CRITICISE) | |
| coppers | H | covered | copper | |
| musos | H | covered | muso | |
| frypan | H | skip | | skillet is already frying pan in the dialect table; the same thing |
| dressing-gown | H | add (dialect) | bathrobe, bath robe | |
| councillor | H | add (dialect) | council member, councilman, councilwoman | |
| full of beans | H | skip | | general British |
| on the cards | H | skip | | general British |
| chinwag | H | covered | have-a-chinwag | |
| yakking | H | skip | | general (American too) |
| gawk, gander | H | skip | | general English |
| bushwalkers | H | covered | a-bushwalker (HIKER) | |
| dud | H | skip | | general English |
| spick and span | H | covered | SPIFFY trigger | |
| quick smart | H | covered | quick-smart | |
| a squiz | H | covered | a-squiz | |
| chuck, bung, whack it (put) | H | covered | chuck, bung-in, whack-in-the-oven (PUT_IN_CASUAL) | |
| stickybeaking | H | covered | stickybeak-around | |
| whinge | H | covered | whinge | |
| twig | H | covered | twig (gated) | |
| suss out | H | covered | suss-out | |
| nick, pinch | H | covered | nick-steal | |
| cop, copped | H | covered | cop | |
| stony broke | H | covered | stony-broke | |
| pulling swifties | H | covered | pulling-a-swifty | |
| get the flick | H | covered | get-the-flick | |
| shockers | H | covered | a-shocker | |
| rabbiting on | H | covered | rabbit-on | |
| muck about | H | covered | muck-around | |
| lob in, rock up | H | covered | lob, rock-up | |
| righto | H | covered | righto | |
| every man and his dog | H | covered | every-man-and-his-dog | |
| choc bits | H | covered | choc-chips | |
| ciggies | H | covered | a-ciggie | |
| to buggery, as buggery | H | covered | smash-to-buggery, slow-as-buggery and kin | |
| doing a runner | H | covered | do-a-runner | |
| a red-hot go | H | covered | a-red-hot-go | |
| taking the piss | H | covered | take-the-piss-out-of | |
| the missus | H | covered | the-missus | |
| hard yakka | H | covered | hard-yakka | |
| veggies, veg | H | covered | veggies | |
| uni | H | covered | uni | |
| punters | H | covered | punters | |
| servos | H | covered | servo | |
| tucker | H | covered | tucker | |
| ice bricks | H | covered | ice-brick | |
| alfoil | H | covered | alfoil | |
| chemists | H | covered (dialect) | drugstore -> chemist | |
| petrol, top up, mobile, five-dollar note | H | covered (dialect) | gasoline, top off the tank, cell phone, five-dollar bill | |
| self-raising, wholemeal, full-cream | H | covered (dialect) | self-rising, whole wheat, whole milk | |
| postgrad, pro rata, three-quarters, kitchen bench | H | covered (dialect) | grad school, prorated, three-fourths, kitchen counter | |
| get a wriggle on | H | covered | get-a-wriggle-on | |
| beaut, bonza, ripper, rapt, crook, strewth, crikey | H | covered | their entries | |
| heaps (of) | H | covered | heaps-np, heaps-adv | |
| arvo, in the arvo | H | covered | arvo | |
| spooked | H | covered | its own concept (from the second-pass fixes) | |
| colour, centre, -ise spellings | H | covered | spelling rules (phonetic.yaml) | |
| cos, till, 'em, ya, s'pose, gonna, -in' | H | covered | drawl (phonetic.yaml) | not dictionary words |
| here's / there's before a plural | H | skip | | a grammar habit (style guide), not a swap |
| I've got (for I have) | H | skip | | general English |
| drapery (dry-goods business) | H | skip | | dated, and "dry goods" now also means non-perishable groceries |
| commercial travellers (drummers) | H | skip | | archaic |
| zack (sixpence) | H | skip | | obsolete coin |
| folding stuff | H | skip | | general British |
| pulling their weight, lend a hand, chipping in, pitching in, roped in | H | skip | | general English |
| sunup | H | skip | | American |
| southerlies, nor'westers | H | skip | | plain weather words |
| how they're tracking | H | skip | | business jargon |
| watch yourself | H | skip | | general English |
| hasn't got a clue | H | skip | | general English |
| self-serve | H | skip | | American too |
| zip-lock bag | H | skip | | ziploc bag -> snap-lock bag is already in the table |

## Review (before merging)

Checked by the session that delegated the round, on sentences that use each new trigger in another sense
(level 4, `-e deadset`): "meant to wait", "the odd Sunday", "easy as", "knocked for six by the news", "a happy
snap from our holiday" (a database snapshot left alone), "the milk will go off" (an alarm left alone) all read
right. Changes made:

- **Dropped two dialect swaps:** medicine cabinet -> bathroom cabinet and bathrobe -> dressing gown. Australians
  say both words, and the dialect table swaps at every level, so a word in everyday Australian use shouldn't be
  in it.
- **"done for the day":** an older trigger ("done for", in two concepts) took "We are all done for the day" ->
  "all down the gurgler the day". Both triggers now exclude what follows the other sense ("the", "now",
  "today", a pronoun: `done for !=the|today|...`).
