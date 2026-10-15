# Fairdinkum round, 2026-10-13: decisions

The project owner supplied 615 headwords (614 distinct) with their part of speech, taken from
fairdinkumslang.au. That site is **reference-only** in `aussiefy/data/source_policy.yaml`: the headwords were
used as a list of candidates and nothing else. The site was never fetched, none of its definitions, examples or
stories were seen, and every gloss, frame and trigger here is written from our own knowledge. `sources` cite
Wiktionary (CC BY-SA) where a page for the sense exists; where none was found the entry has no source
(`evidence: own` in its verdict), as in earlier rounds. The list itself is credited in the header of
`entries/fairdinkum.yaml`, never as a definition's source.

The brief was judgement, not ingestion: add a term only where a plain-English trigger can be caught reliably in
that sense and the Aussie term reads as genuine and current; keep genuinely Australian terms with no safe
trigger for lookup; skip the rest.

## How it was run

1. Every headword was checked against the dictionary (forms and variants, then `lookup` and `show`).
2. Each candidate was judged by hand: sense, gloss, frame, level, vulgarity, register, and which other senses its
   triggers must not catch. The verdicts are in `verify/verdicts-fairdinkum.yaml`, in the everyday round's
   verifier format (`../everyday-round-2026-10-13/verify/BRIEF.md`).
3. `aussiefy dev round research/fairdinkum-round-2026-10-13 --write` (configured by `round.yaml`) wrote
   `entries/fairdinkum.yaml` and a section of `concepts.yaml`.
4. Every entry was tested: a positive sentence and wrong-sense sentences for each, at level 5 over 12 seeds
   (vulgarity tradie), then every substitution the new entries make over the everyday, reference and classics
   corpora (97 texts, 3 seeds) was read. What they caught is under "What testing changed".
5. Extensions to existing entries, and fixes to existing triggers, were made by hand (the round tooling only
   adds entries and appends triggers).

## Counts

| decision | headwords |
|---|---|
| add | 128 (147 entries in `entries/fairdinkum.yaml`, some headwords sharing one, some adding a sibling) |
| extend | 11 (variants on 10 existing entries, plus the new "done for" sense of cooked) |
| reference (lookup only) | 11 (plus Tassie and Brissie, active on narrow triggers only) |
| already covered | 217 (in the dictionary, or swapped by the dialect table) |
| skip | 247 (73 of them proper names and nicknames) |

148 entries in all (147 from the round, 1 by hand), 1 gated (laid-back, `not_aussie`, as asked), under 121 new
concepts and 1 hand-added concept (DONE_FOR).

**Requested terms.** dinkum, grouse, dodgy, chockers, feral, spewing (spewin') and buggered were already in, with
the senses asked for. deadset is added as a standalone adjective (an utter disaster -> a deadset disaster); the
adverb (I deadset thought...) would share its form, which the round refuses, and dead-set-q already covers the
"honestly" interjection. laid-back is added gated `not_aussie`, with a genuinely Aussie entry beside it (a
she'll-be-right attitude, for a relaxed/laid-back attitude). go troppo is untouched.

**Reference only** works as the classics round's lookup-only concepts did: an active entry under a concept
whose description says "lookup only" and whose one trigger is a periphrasis that almost never occurs, so
`lookup` finds it ("drop bear", "someone from Queensland", "a sea breeze in Perth") and the engine leaves text
alone. They are a-banana-bender, a-croweater, a-drop-bear, aerial-ping-pong, a-grey-nomad, the-fremantle-doctor,
schoolies, an-eshay, on-the-tools, a-wigwam-for-a-gooses-bridle and a-joe-blake.

## Extensions to existing entries (by hand)

| entry | file | change |
|---|---|---|
| beauty | phrases.yaml | variants "you bewdy", "bewdy" |
| catch-ya-later | phrases.yaml | variant "catch ya" |
| fair-shake-of-the-sauce-bottle | phrases.yaml | variant "fair suck of the sauce bottle" |
| shell-be-apples | phrases.yaml | variant "she's apples" |
| mad-as-a-gumtree | idioms.yaml | variant "as mad as a gumtree full of galahs" |
| cozzie | lexical.yaml | variant "cossie" |
| rellos | lexical.yaml | variant "rellie" |
| chrissie | lexical.yaml | variant "Chrissy" |
| sparrows-fart | gapfill.yaml | variant "at sparrow fart" |
| no-wukkas | gapfill.yaml | variant "no wuckers" |
| cooked-done-for (new) | gapfill.yaml | cooked, "done for" (we're cooked), beside the gated tired sense whose note pointed at it; concept DONE_FOR (done for, doomed, toast ^person, in deep trouble), level 3, vulgarity 0 |

Variants are output as well as matched (the engine picks among an entry's forms), so each was chosen to read
well as output.

## Fixes to existing triggers (by hand, in concepts.yaml)

| concept | was | now | why |
|---|---|---|---|
| HAVE_BEER | have a beer | have a beer !belly\|bellies\|gut\|guts\|garden\|gardens | "he has a beer belly" was having a beer (stop a pot) |
| LOOK | a glance@2 | a quick glance@2 | "took in the situation at a glance" became "at a squiz" (and at a Captain Cook) |
| LOOK | a look | a look !of\|on | "a look of horror on her face" |
| HOON | a hooligan, a lout | hooligan, lout (+ yob, by the round) | the article was required, so "some hooligan" and "the louts" went unseen |

## What testing changed

- **Articles.** An np trigger written "a bachelor party" doesn't match "the bachelor party"; bare nouns do and
  keep the source's determiner and number. Most np triggers were made bare.
- **Taken out or narrowed:** "make the cut" (a recipe's "make the cut 2 cm deep"), "caught out" (caught out in
  the rain), "cancel at the last minute" (a cancelled concert isn't piking), "lean on {obj} for {np}" (lean on
  me for support), "a sweetheart deal", "minor crash" (a minor crash in prices), "finish work by Friday" (a
  job, not knocking off), "the football field" (American gridiron isn't an oval), "absolute" before political
  and technical nouns (the Declaration's "absolute Despotism" and "an absolute Tyranny" had become deadset).
- **Moved to concepts of their own:** the ant's pants (from EXCELLENT, which put it in "it would be great fun"),
  hooley dooley (from SURPRISE, which took "Oh dear," he thought), pig's bum (from DISAGREE's bare "no" to
  DREAM_ON), tell him he's dreamin' (from DREAM_ON, which is said to "you").
- **Made lookup-only:** Joe Blake ("he's a snake" is a traitor, and "the snake" lost its article); Tassie and
  Brissie keep only "the island state" and "the Queensland capital" (a bare Tasmania made "the University of
  Tassie").
- **veggo** became a predicate of a person ("she is vegetarian"), since "a vegetarian lasagne" and "a
  vegetarian chef" took the np.
- **Glosses reworded for the embedder's reference set** (`tests/test_static.py`): the tuckshop's ("counter"
  pulled "a cold one at the pub"), old mate's and your blood's worth bottling's (both pulled "a good mate of
  mine"). All 33 required checks pass without a retrain; `aussiefy embedder status` will report the model
  stale against the bigger dictionary, as after every round.

Accepted after a look: "Thank you all for coming" -> "Thank youse for comin'" (broad, but right), "the sun is
full-on today", "there was chunder on the floor" (chunder is a noun too), "a lairy colour".

## Golden changes (tests/corpus/golden.yaml, regenerated)

18 outputs changed; every one is a fix or neutral:

| input | level/seed | change | verdict |
|---|---|---|---|
| I'm exhausted and the toilet is broken. | L4s1, L5s0 | the dunny is cactus (, rooted) -> bung | fine: the new entry, right sense |
| | L5s1 | rooted -> cactus | neutral |
| Hello everyone! Grab your sunglasses, swimsuit... | L4s0, L5s0 | cozzie -> cossie | neutral (the new variant) |
| Wow, that was a great game of football! | L5s0 | opener Crikey -> Fuck me | neutral reshuffle (L5's default vulgarity) |
| Take a look at this mess. | L2s0, L3s0 | a look -> a squiz | gain |
| | L4s0/s1, L5s0/s1 | a squiz -> a Captain Cook | neutral (genuine; the weights are near even) |
| They were furious and told him off. | L4s0, L5s0 | gave him a serve -> gave him a bit of curry | fine, same sense |
| | L4s1, L5s1 | tore strips off -> roused on | neutral |
| The Emperor's New Clothes | L5s0 | "Bugger me!" -> "Bugger me dead!" | neutral |
| Goldilocks | L4s0, L5s0 | the chair "had carked it" -> "was cactus" | fix: a chair is broken, not dead |

## Engine findings (not fixed: engine code is out of scope)

- **A predicate read before a noun.** "it would be great fun" and "there was great dearth" are taken as a
  predicate "great" though a noun follows, so a multi-word predicate form lands before the noun ("the duck's
  nuts fun"; pre-existing, and why the ant's pants moved off EXCELLENT). The same span treats "great dearth"
  (a big famine) as excellent.
- **Openers lower-case a name.** After "Well," the form "Blind Freddy" became "blind Freddy": the tagger doesn't
  see the capitalised form as a name.
- **^person counts "dog" as a person** (the dictionary's "a dog", the betrayer, makes it a person noun), so
  "the dog is loyal" becomes "true blue".
- **Clause triggers need a pronoun subject**, so "the council is completely incompetent" doesn't reach "couldn't
  organise a chook raffle" (only "they are completely incompetent" does).
- **The round tooling** can't add a second sense with an existing form (cooked, deadset as adverb, the tinnie
  boat), and can't take out a trigger on an existing concept; both were done by hand.
- **Dialect-table candidate:** "yield sign" -> "give way sign" (dialect.yaml was left alone).

## Unsure

- Region-tagged entries (bevan, the tuckshop, a middy) fire everywhere unless `--region` is given, so a
  Victorian text can get "the tuckshop"; acceptable since they're understood nationally.
- old mate, rort, full-on, schmick and lolly water have triggers narrower than their use; true blue and
  happy little Vegemite are idiomatic but lean on a person subject the engine guesses at.
- Vulgarity calls: verandah over the toy shop and off like a bride's nightie are innuendo with no swear word,
  rated 1; pig's bum rated 0 ("bum" is nursery-mild); piss weak 2 (piss).
- Some Wiktionary pages have the sense without an "Australia" label (billycart, schmick, tuckshop, youse and a
  few more); they are cited as the term's own page.

## Every headword

| headword | pos | decision | entry | why |
|---|---|---|---|---|
| a few roos loose in the top paddock | idiom | already covered | roos-top-paddock | already a variant of the kangaroo-loose idiom |
| a few snags short of a barbie | idiom | already covered | snags-short-of-a-barbie |  |
| a wigwam for a goose's bridle | idiom | reference | a-wigwam-for-a-gooses-bridle | dated fob-off answer; no plain trigger |
| acca | noun | skip |  | campus slang for an academic; niche, and 'academic' is mostly an adjective |
| ace | adjective | skip |  | general English (UK and US) for excellent; adds no Aussie flavour |
| addo | nickname | skip |  | a proper name or nickname |
| aerial ping pong | noun | reference | aerial-ping-pong | a jibe at Aussie rules: swapping the game's name would mock every match report |
| aggro | adjective | add | aggro | aggressive (of people only, via ^person) |
| akubra | noun | skip |  | a brand |
| alf | noun | skip |  | dated and derogatory; bogan and ocker cover it |
| ambit claim | noun | skip |  | a historical or political term of art (industrial relations) |
| ambo | noun | already covered | ambo |  |
| ant's pants | phrase | add | the-ants-pants | on its own concept (the bee's knees and kin): on EXCELLENT it landed in 'great fun' |
| anzac | noun | skip |  | a historical or political term of art |
| anzac bikkie | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| anzac biscuit | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| arvo | noun | already covered | arvo |  |
| arvo shift | noun | already covered | arvo | compositional: afternoon shift -> arvo shift |
| arvo tea | noun | already covered | arvo | compositional: afternoon tea -> arvo tea |
| as game as ned kelly | idiom | already covered | game-as-ned-kelly |  |
| aussie | noun | add | an-aussie | the noun with its article only, so institutions' names stay |
| aussie aussie aussie oi oi oi | exclamation | skip |  | a chant; nothing to translate |
| australia | proper noun | skip |  | a proper name or nickname |
| back of bourke | phrase | already covered | back-of-bourke |  |
| bag of fruit | rhyming slang | add | a-bag-of-fruit | rhyming slang for a suit; level 5, dated, clothing triggers only |
| baggy green | noun | skip |  | a proper name or nickname (the Test cap) |
| banana bender | noun | reference | a-banana-bender | a state nickname; 'Queenslander' is also a house style |
| banksia man | noun | skip |  | a literary character / seed cone |
| barbecue stopper | noun | add | a-barbecue-stopper | hot-button issue |
| barbie | noun | already covered | barbie |  |
| barcoo | noun | skip |  | archaic (barcoo rot, barcoo grass) |
| barra | noun | add | barra | the clipping of barramundi, as croc for crocodile |
| barrack for | phrase | already covered | barrack-for |  |
| barramundi | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap; barra is the swap |
| barrier rise | noun | skip |  | a racing term of art |
| bash | noun | skip |  | general English (a party; give it a bash), ambiguous |
| bathers | noun | already covered | bathers |  |
| battler | noun | already covered | battlers | battlers (STRUGGLERS) covers it |
| bazza | nickname | skip |  | a proper name or nickname |
| beauty | exclamation | already covered | beauty |  |
| benny | nickname | skip |  | a proper name or nickname |
| berley | noun | add | berley | groundbait; not 'chum', which is also a friend |
| better than a poke in the eye | idiom | already covered | better-than-a-poke-in-the-eye |  |
| bevan | noun | add | a-bevan | Queensland's bogan, region-tagged |
| bevo | nickname | skip |  | a proper name or nickname |
| bewdy | exclamation | extend | beauty | variants 'bewdy' and 'you bewdy' |
| beyond the black stump | idiom | already covered | beyond-the-black-stump |  |
| bickies | noun | already covered | bikkie | bikkie has the variant bickie |
| biffo | noun | already covered | biffo |  |
| big note yourself | phrase | already covered | big-note-oneself |  |
| big-noting | verb | already covered | big-note-oneself |  |
| bikie | noun | add | a-bikie | biker, not biker shorts or a biker jacket |
| bikkie | noun | already covered | bikkie |  |
| bilby | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| billabong | noun | already covered | a-billabong |  |
| billo | nickname | skip |  | a proper name or nickname |
| billy | noun | already covered | billy |  |
| billycart | noun | add | a-billycart | soapbox cart |
| bindi-eye | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| bingle | noun | add | a-bingle | minor car crash; not 'a minor crash in prices' |
| bit of a curry | phrase | add | give-a-bit-of-curry | give someone a hard time |
| bitzer | noun | already covered | a-bitzer |  |
| black stump | noun | already covered | beyond-the-black-stump | lives in its idiom |
| blind freddy | idiom | add | blind-freddy | any fool (could see that) |
| bloke | noun | already covered | bloke |  |
| bloody oath | exclamation | already covered | bloody-oath |  |
| blouse | verb | skip |  | niche footy slang (to win narrowly) |
| blow-in | noun | already covered | a-blow-in |  |
| blowie | noun | add | a-blowie | blowfly |
| bludge | verb | already covered | bludge |  |
| bludger | noun | already covered | bludger |  |
| bluebottle | noun | add | a-bluebottle | Portuguese man o' war |
| bluey | noun | skip |  | too many senses (redhead's nickname, swag, summons, heeler, the cartoon) |
| boardies | noun | add | boardies | board shorts |
| bodgie | noun | skip |  | dated (1950s youth; shoddy); DODGY has dodgy and shonky |
| bogan | noun | add | a-bogan | redneck, chav |
| bogey | verb | skip |  | dated (a swim), and collides with golf and bogeys |
| bombora | noun | skip |  | a surf term of art with no plain equivalent |
| bonzer | adjective | already covered | bonza |  |
| boobook | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| boofhead | noun | already covered | boofhead |  |
| boomerang | noun | skip |  | the thing's own name |
| bottle-o | noun | already covered | bottle-o |  |
| bottler | noun | add | you-little-bottler | as the exclamation 'you little bottler'; dated |
| bottom of the harbour | noun | skip |  | a historical or political term of art (a tax scheme) |
| boundary rider | noun | skip |  | a historical occupation's name |
| bozza | nickname | skip |  | a proper name or nickname |
| braddo | nickname | skip |  | a proper name or nickname |
| branch stacking | noun | skip |  | a historical or political term of art |
| brass monkeys | phrase | add | brass-monkeys, brass-monkey-weather | weather only: 'it's freezing' (clause, subject it), never 'I'm freezing' |
| brass razoo | phrase | already covered | a-brass-razoo |  |
| brekkie | noun | already covered | brekkie |  |
| bretto | nickname | skip |  | a proper name or nickname |
| brickie | noun | add | a-brickie | bricklayer |
| brigalow | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| bring a plate | phrase | add | bring-a-plate | bring a dish to share |
| brissie | noun | add | brissie | narrow trigger only ('the Queensland capital'); a bare Brisbane is in too many names |
| brolga | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| brumby | noun | already covered | a-brumby |  |
| bucketing | verb | already covered | bucketing-down |  |
| buckley's chance | idiom | already covered | buckleys-chance |  |
| bucks | noun | add | a-bucks-night (+ a-hens-night) | bachelor/stag party; its counterpart added with it |
| budgie | noun | add | a-budgie | budgerigar |
| budgie smugglers | noun | add | budgie-smugglers | swim briefs, speedos |
| bugalug | noun | skip |  | dated term of endearment |
| buggered | adjective | already covered | buggered | requested; already in (TIRED, BROKEN, vulgarity 1) |
| bulldust | noun | already covered | bulldust |  |
| bung | adjective | add | bung-broken | broken (predicate) |
| bunya | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| bunyip | noun | skip |  | a creature of Aboriginal tradition; not a swap |
| burr up | verb | skip |  | unclear currency |
| cactus | adjective | already covered | cactus |  |
| canberra bashing | noun | skip |  | a historical or political term of art |
| captain cook | rhyming slang | add | a-captain-cook | rhyming slang for a look (LOOK) |
| captain's pick | noun | skip |  | a historical or political term of art (a leader's override) |
| cark | verb | already covered | cark-it |  |
| carn | exclamation | skip |  | a barracking cry; 'come on' has too many other uses |
| carry on like a pork chop | phrase | already covered | carry-on-like-a-pork-chop |  |
| carton | noun | skip |  | plain English; slab covers the 24-pack |
| catch ya | phrase | extend | catch-ya-later | variant 'catch ya' |
| chado | nickname | skip |  | a proper name or nickname |
| chalkie | noun | skip |  | dated, and would swap every teacher |
| chardonnay socialist | noun | add | a-chardonnay-socialist | champagne socialist |
| checkout chick | noun | skip |  | gendered; and 'cashier' is broad |
| chewie | noun | add | chewie | chewing gum (never bare 'gum') |
| chiko roll | noun | skip |  | a brand |
| chippy | noun | add | a-chippy | carpenter |
| chock-a-block | adjective | already covered | chock-a-block |  |
| chockers | adjective | already covered | chockers | requested; already in (CROWDED: completely full, packed) |
| chook | noun | already covered | chook |  |
| chrissie | nickname | skip |  | a proper name or nickname |
| chrisso | nickname | skip |  | a proper name or nickname |
| chrissy | noun | extend | chrissie | variant 'Chrissy' |
| chuck a sickie | phrase | already covered | chuck-a-sickie |  |
| chuck a wobbly | phrase | already covered | chuck-a-wobbly |  |
| chunder | verb | add | chunder | vomit, throw up (not 'throw up a wall') |
| clayton's | adjective | skip |  | brand-derived and dated |
| cleanskins | noun | skip |  | a wine-trade (or stock) term of art |
| cobber | noun | already covered | cobber |  |
| cocky | noun | skip |  | a farmer or cockatoo, but readers take it as 'arrogant' |
| come a gutser | phrase | add | come-a-gutser | fall over heavily |
| connors | nickname | skip |  | a proper name or nickname |
| convict | noun | skip |  | plain English |
| cooee | exclamation | add | within-cooee | within earshot |
| cooked | adjective | extend | cooked-done-for | the 'done for' sense (we're cooked), by hand beside the gated tired sense |
| coolamon | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| coolibah | noun | already covered | coolibah-tree |  |
| corroboree | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| cossie | noun | extend | cozzie | variant 'cossie' |
| couldn't organise a chook raffle | idiom | add | couldnt-organise-a-chook-raffle | completely incompetent (pronoun subjects) |
| cranky | adjective | already covered | cranky |  |
| crikey | exclamation | already covered | crikey |  |
| croc | noun | already covered | croc |  |
| crook | adjective | already covered | crook |  |
| crook in tallarook | phrase | skip |  | dated; crook covers it |
| croweater | noun | reference | a-croweater | a state nickname; 'a South Australian' starts many other phrases |
| cumbungi | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| cup of tea, a bex, and a good lie down | phrase | add | cup-of-tea-bex-lie-down | calm down; level 5, dated |
| cuppa | noun | already covered | cuppa |  |
| currawong | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| currency lad and lass | noun | skip |  | a historical or political term of art |
| dag | noun | already covered | dag |  |
| daggy | adjective | already covered | daggy |  |
| dagwood dog | noun | add | a-dagwood-dog | corn dog |
| damper | noun | add | damper | campfire bread |
| danno | nickname | skip |  | a proper name or nickname |
| davo | nickname | skip |  | a proper name or nickname |
| dazza | nickname | skip |  | a proper name or nickname |
| dead horse | noun | skip |  | dated rhyming slang; the dialect table already makes ketchup tomato sauce |
| deadset | adjective | add | deadset-adj | requested standalone: the adjective (utter, absolute); the adverb shares its form and dead-set-q covers 'honestly' |
| defo | adverb | already covered | defo |  |
| devo | adjective | already covered | devo |  |
| dial | noun | skip |  | ambiguous (a face; a phone dial) |
| didgeridoo | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| didn't come down in the last shower | phrase | add | didnt-come-down-in-the-last-shower | wasn't born yesterday |
| digger | noun | already covered | diggers |  |
| dill | noun | already covered | dill |  |
| dilly bag | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| dim sim | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| dingo | noun | already covered | dingo |  |
| dinkum | adjective | already covered | dinkum | requested; already in (GENUINE) |
| do a bradbury | phrase | add | do-a-bradbury | win against all odds |
| do a harold holt | phrase | skip |  | dated rhyming slang, and makes light of a drowning |
| do a melba | phrase | skip |  | dated |
| dob in | phrase | already covered | dob-in |  |
| dobber | noun | add | a-dobber | snitch, tattletale |
| dodgy | adjective | already covered | dodgy | requested; already in (DODGY) |
| dog and bone | rhyming slang | skip |  | Cockney rhyming slang, not Australian |
| donkey vote | noun | skip |  | a historical or political term of art (voting) |
| donno | nickname | skip |  | a proper name or nickname |
| doona | noun | already covered | doona |  |
| dorothy dixer | noun | skip |  | a historical or political term of art |
| dosh | noun | already covered | dosh |  |
| dreamtime | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| drongo | noun | already covered | drongo |  |
| drop bear | noun | reference | a-drop-bear | a tourist leg-pull; nothing to translate |
| drop-kick | noun | add | a-drop-kick | a loser |
| drover's dog | phrase | skip |  | a historical or political term of art (a 1983 quip) |
| dry as a bone | idiom | skip |  | general English |
| dry as a dead dingo's donger | idiom | already covered | dry-as-a-dead-dingo | already rated vulgarity 1 |
| ducks on the pond | phrase | skip |  | dated shearing-shed warning |
| dunny | noun | already covered | dunny |  |
| durry | noun | already covered | a-durry |  |
| earbash | verb | already covered | earbash |  |
| echidna | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| economic rationalism | noun | skip |  | a historical or political term of art |
| emu bob | verb | add | an-emu-bob | litter pick (variant emu parade) |
| eshay | noun | reference | an-eshay | a youth subculture; no plain equivalent |
| esky | noun | already covered | esky |  |
| ezza | nickname | skip |  | a proper name or nickname |
| fair dinkum | adjective | already covered | fair-dinkum-adj |  |
| fair go | phrase | already covered | fair-go |  |
| fair suck of the sauce bottle | phrase | extend | fair-shake-of-the-sauce-bottle | variant |
| fair suck of the sav | exclamation | already covered | fair-suck-of-the-sav |  |
| fairy bread | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| fairy floss | noun | already covered |  | the dialect table already swaps cotton candy and candy floss |
| female factory | noun | skip |  | a historical or political term of art |
| feral | adjective | already covered | feral | requested; already in (UNCOUTH) |
| fezza | nickname | skip |  | a proper name or nickname |
| firie | noun | already covered | firey | firey has the variant firie |
| flash as a rat with a gold tooth | phrase | already covered | flash-as-a-rat |  |
| flat chat | adverb | already covered | flat-chat |  |
| flat out | idiom | already covered | flat-out |  |
| flat out like a lizard drinking | idiom | already covered | flat-out-lizard |  |
| footy | noun | already covered | footy |  |
| footy oval | noun | add | the-footy-oval | the sports field/ground (not 'a level playing field') |
| fossick | verb | add | fossick-around, fossick-through | rummage around / through |
| fremantle doctor | noun | reference | the-fremantle-doctor | WA only: a sea breeze elsewhere isn't it |
| frog and toad | rhyming slang | already covered | the-frog-and-toad |  |
| full as a goog | phrase | already covered | full-as-a-goog |  |
| full-on | adjective | add | full-on | intense, hectic |
| funnel-web | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| furphy | noun | already covered | a-furphy |  |
| g'day | exclamation | already covered | gday |  |
| galah | noun | already covered | galah |  |
| gang-gang | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| garbo | noun | already covered | garbo |  |
| gazza | nickname | skip |  | a proper name or nickname |
| geebung | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| geek | verb | already covered | a-geek |  |
| get knotted | phrase | add | get-knotted | go away (clean); dated |
| gibber | noun | skip |  | a landscape term of art |
| gilgai | noun | skip |  | a landscape term of art |
| gillo | nickname | skip |  | a proper name or nickname |
| give it a burl | phrase | already covered | give-it-a-burl |  |
| give way | phrase | skip |  | road-rule wording; 'yield' as a verb is ambiguous (a dialect-table candidate: yield sign -> give way sign) |
| glory box | noun | add | a-glory-box | hope chest; dated |
| going off like a frog in a sock | idiom | already covered | go-off-like-a-frog-in-a-sock |  |
| good drop | noun phrase | add | a-good-drop | a good wine |
| good oil | noun phrase | already covered | the-good-oil |  |
| good on ya | interjection | already covered | good-on-ya |  |
| good sort | noun phrase | already covered | a-good-sort | gated |
| googy egg | noun | already covered | goog | goog covers it |
| goon | noun | add | goon | cask wine |
| goon bag | noun | add | a-goon-bag | a wine cask (variant goon sack) |
| goon sack | noun | add | a-goon-bag | variant of goon bag |
| got a guernsey | phrase | add | get-a-guernsey | make the team |
| govvo | nickname | skip |  | a proper name or nickname |
| green ban | noun | skip |  | a historical or political term of art |
| greggo | nickname | skip |  | a proper name or nickname |
| grey nomad | noun | reference | a-grey-nomad | no plain phrase worth swapping |
| grog | noun | already covered | grog |  |
| grouse | adjective | already covered | grouse | requested; already in (EXCELLENT, dated) |
| grub | noun | add | a-grub | a lowlife (SCOUNDREL) |
| gunyah | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| gymea lily | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| happy as a pig in mud | idiom | skip |  | general English |
| happy as larry | phrase | already covered | happy-as-larry |  |
| happy little vegemite | idiom | add | happy-little-vegemite | content; a brand, but the idiom is the language's |
| hard word | phrase | add | put-the-hard-word-on | hit someone up for something |
| hard yakka | noun | already covered | hard-yakka |  |
| hard yards | noun phrase | add | do-the-hard-yards | do the hard work, the groundwork |
| have a bogey | phrase | skip |  | dated (see bogey) |
| having a yarn | phrase | already covered | have-a-yarn |  |
| hazza | nickname | skip |  | a proper name or nickname |
| heaps | adverb | already covered | heaps-adv |  |
| hills hoist | noun | skip |  | a brand (genericised, but still the brand) |
| hip pocket nerve | phrase | skip |  | political journalese; the gated 'the hip pocket' covers it |
| hooley dooley | exclamation | add | hooley-dooley | amazement (its own concept, so 'oh dear' isn't caught) |
| hoon | noun | already covered | a-hoon | its triggers made bare so 'some hooligan' and 'the louts' count |
| hooning | verb | add | hoon-around | drive recklessly |
| hooroo | exclamation | already covered | hooroo |  |
| hot chips | noun | already covered |  | the dialect table already swaps fries for chips |
| hughie | phrase | add | send-her-down-hughie | 'let it rain'; level 5, dated |
| humpy | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect (a shelter) |
| ice block | noun | already covered |  | the dialect table already swaps popsicle and ice lolly (for icy pole) |
| illywhacker | noun | skip |  | dated and literary |
| iron lung | phrase | skip |  | unclear sense and currency |
| jackaroo | noun | skip |  | the name of the job; no plain equivalent |
| jacko | nickname | skip |  | a proper name or nickname |
| jacky howe | noun | skip |  | dated; singlet covers it |
| jarrah | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| jazza | nickname | skip |  | a proper name or nickname |
| jenny | nickname | skip |  | a proper name or nickname |
| joe blake | rhyming slang | reference | a-joe-blake | lookup only: 'he's a snake' is a traitor, and 'the snake' lost its article |
| joey | noun | add | a-joey | baby kangaroo, wallaby, koala... |
| johnno | nickname | skip |  | a proper name or nickname |
| johno | nickname | skip |  | a proper name or nickname |
| jumbuck | noun | already covered | a-jumbuck |  |
| jumper | noun | already covered | jumper |  |
| kangaroo | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap; roo is the swap |
| kazza | nickname | skip |  | a proper name or nickname |
| kenny | nickname | skip |  | a proper name or nickname |
| kevo | nickname | skip |  | a proper name or nickname |
| kevvo | nickname | skip |  | a proper name or nickname |
| king-hit | noun | add | a-king-hit | sucker punch |
| knackered | adjective | already covered | knackered |  |
| knees-up | noun | skip |  | British |
| knock off | verb | add | knock-off-work | finish work, call it a day |
| koala | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| kookaburra | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| koori | noun | skip |  | an Aboriginal people's name for themselves; never a swap |
| kurrajong | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| kylie | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect (a WA boomerang) |
| lairy | adjective | add | lairy | loud, flashy (SHOWY), garish, gaudy |
| lamington | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| larrikin | noun | already covered | larrikin |  |
| laters | phrase | skip |  | general slang |
| lay-by | noun | add | lay-by | layaway |
| lazza | nickname | skip |  | a proper name or nickname |
| legend | noun | already covered | a-legend |  |
| leggo | nickname | skip |  | a proper name or nickname |
| lenny | nickname | skip |  | a proper name or nickname |
| levo | nickname | skip |  | a proper name or nickname |
| life wasn't meant to be easy | phrase | skip |  | a historical or political term of art (a quotation) |
| light on the hill | phrase | skip |  | a historical or political term of art (a Labor slogan) |
| like a stunned mullet | idiom | already covered | like-a-stunned-mullet |  |
| little aussie battler | noun | already covered | battlers |  |
| lollies | noun | already covered | lollies |  |
| lolly water | noun | add | lolly-water | sugary drinks (not 'soft drink', which the dialect table writes) |
| lozza | nickname | skip |  | a proper name or nickname |
| macca | nickname | skip |  | a proper name or nickname |
| maccas | noun | already covered | maccas |  |
| mad as a cut snake | idiom | already covered | mad-as-a-cut-snake |  |
| mad as a gumtree full of galahs | idiom | extend | mad-as-a-gumtree | variant 'as mad as a gumtree full of galahs' |
| maggot | adjective | already covered | maggoted | maggoted covers it |
| magic pudding | noun | skip |  | a literary title |
| mallee | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| mallee bull | idiom | add | strong-as-a-mallee-bull | strong as an ox, fit as a fiddle |
| manchester | noun | add | manchester-linen | household linen |
| mando | nickname | skip |  | a proper name or nickname |
| manno | nickname | skip |  | a proper name or nickname |
| marn grook | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| marri | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| mate | noun | already covered | mate |  |
| matilda | noun | already covered | go-waltzing-matilda |  |
| may your chooks turn into emus and kick your dunny down | phrase | skip |  | a jocular curse with nowhere to go in a translation |
| mazza | nickname | skip |  | a proper name or nickname |
| mia-mia | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| middy | noun | add | a-middy | a half-pint of beer; region nsw, wa |
| millo | nickname | skip |  | a proper name or nickname |
| milo | noun | skip |  | a brand |
| miserable as a bandicoot | idiom | add | miserable-as-a-bandicoot | SAD; level 5, dated |
| moolah | noun | skip |  | general (US) slang |
| motza | noun | already covered | a-motza |  |
| mozza | nickname | skip |  | a proper name or nickname |
| mozzie | noun | already covered | mozzie |  |
| mufti day | noun | add | a-mufti-day | non-uniform day |
| mulga | noun | already covered | the-mulga |  |
| munted | adjective | skip |  | more New Zealand than Australian |
| muster | noun | already covered | muster |  |
| nah yeah | phrase | already covered | nah-yeah |  |
| nando | nickname | skip |  | a proper name or nickname |
| nasho | noun | skip |  | a historical or political term of art (national service) |
| nature strip | noun | add | the-nature-strip | the grass verge (not 'on the verge of') |
| neenish tart | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| nello | nickname | skip |  | a proper name or nickname |
| nevo | nickname | skip |  | a proper name or nickname |
| nezza | nickname | skip |  | a proper name or nickname |
| nipper | noun | already covered | nipper |  |
| no dramas | phrase | already covered | no-dramas |  |
| no worries | phrase | already covered | no-worries |  |
| no wuckers | phrase | extend | no-wukkas | variant 'no wuckers' |
| noah's ark | rhyming slang | skip |  | dated rhyming slang |
| nong | noun | already covered | nong |  |
| not a drama | phrase | add | not-a-drama | no problem |
| not know if you're arthur or martha | idiom | add | arthur-or-martha | completely confused, all at sea |
| not the full quid | idiom | already covered | not-the-full-quid |  |
| not within a bull's roar | idiom | add | not-within-a-bulls-roar | nowhere near the (place or goal), not degree |
| nulla-nulla | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| numbat | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| ocker | noun | add | ocker-adj | as the adjective: a broad Australian accent -> an ocker accent |
| off like a bride's nightie | idiom | add | off-like-a-brides-nightie | off like a shot; innuendo, vulgarity 1 |
| offsider | noun | already covered | offsider |  |
| old mate | noun | add | old-mate | some random guy |
| on the sheep's back | phrase | skip |  | a historical or political term of art |
| on the tools | phrase | reference | on-the-tools | no safe plain trigger |
| on the turps | phrase | add | on-the-turps | on a bender |
| on the wallaby | phrase | skip |  | archaic; TRAMP_ROADS has go waltzing Matilda |
| op shop | noun | already covered |  | the dialect table already swaps thrift store/shop |
| outback | noun | skip |  | the name of the region; FAR_AWAY covers the remote sense |
| owyagoin | phrase | already covered | how-ya-goin |  |
| oz | noun | skip |  | a bare 'Australia' trigger would wreck Western Australia, Australia Post and the rest |
| p-plater | noun | add | a-p-plater (+ an-l-plater) | provisional driver; the learner counterpart added with it |
| pademelon | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| pash | verb | add | pash-obj | make out with someone (not bare 'make out') |
| pat malone | rhyming slang | already covered | on-pat-malone |  |
| pavlova | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap |
| peggo | nickname | skip |  | a proper name or nickname |
| penny | nickname | skip |  | a proper name or nickname |
| phildo | nickname | skip |  | a proper name or nickname |
| pie | noun | skip |  | plain English |
| pig's bum | exclamation | add | pigs-bum | a dismissal (DREAM_ON), not a bare 'no' |
| piker | noun | add | pike-out, a-piker | chicken out / a flake |
| piss weak | adjective | add | piss-weak | pathetic, feeble; vulgarity 2 |
| piss-up | noun | already covered | piss-up | already rated vulgarity 2 |
| plonk | noun | add | plonk | cheap wine |
| pokies | noun | already covered | the-pokies |  |
| pollie | noun | already covered | pollie |  |
| pommy | noun | already covered | pommy | gated |
| porky | rhyming slang | add | a-porky | a lie, a fib (the noun; tell porkies was in) |
| postie | noun | already covered | postie |  |
| pot | noun | skip |  | ambiguous (cooking pot, marijuana, a pot belly; the Victorian beer glass) |
| potato scallop | noun | skip |  | the name of a dish or food, no plain-English equivalent to swap (regional name) |
| potoroo | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| pozza | nickname | skip |  | a proper name or nickname |
| prezzie | noun | already covered | pressie |  |
| prezzy | noun | already covered | pressie | a spelling of pressie |
| public servant | noun | add | a-public-servant (+ the-public-service) | civil servant; plain Australian English |
| put the acid on | phrase | add | put-the-acid-on | hit someone up for something; dated |
| put the moz on | phrase | already covered | put-the-mozz-on |  |
| quandong | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| queenslander | noun | skip |  | a house style or a person: ambiguous |
| quid | noun | already covered | quid |  |
| quokka | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| quoll | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| rack off | phrase | already covered | rack-off |  |
| rando | nickname | skip |  | general slang (a random person) |
| rapt | adjective | already covered | rapt |  |
| rashie | noun | add | a-rashie | rash vest |
| ratbag | noun | already covered | ratbag |  |
| raw prawn | phrase | add | dont-come-the-raw-prawn | don't try to fool me |
| razor gang | noun | skip |  | a historical or political term of art |
| recess | noun | already covered | little-lunch | plain Australian English; RECESS is a concept already |
| reckon | verb | already covered | reckon |  |
| redback | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| rego | noun | add | rego | car registration |
| rellies | noun | extend | rellos | variant 'rellie' |
| ricko | nickname | skip |  | a proper name or nickname |
| ridgy-didge | adjective | already covered | ridgy-didge |  |
| rip | noun | skip |  | ambiguous (a rip current, to rip) |
| ripper | adjective | already covered | ripper |  |
| ripsnorter | noun | skip |  | dated; ripper covers it |
| robba | nickname | skip |  | a proper name or nickname |
| robbo | nickname | skip |  | a proper name or nickname |
| rogaining | noun | skip |  | a sport's name |
| ronno | nickname | skip |  | a proper name or nickname |
| roo | noun | already covered | roo |  |
| rooted | adjective | already covered | rooted |  |
| ropeable | adjective | already covered | ropeable |  |
| rort | noun | add | a-rort, rort-the-system | a misuse of public funds; game the system (not 'a scam') |
| rough as guts | phrase | add | rough-as-guts | crude (UNCOUTH) |
| rough end of the pineapple | phrase | add | rough-end-of-the-pineapple | get a raw deal |
| rsl | noun | skip |  | a proper name or nickname (an institution) |
| sammo | nickname | skip |  | a proper name or nickname |
| sando | nickname | skip |  | a proper name or nickname |
| sanga | noun | already covered | sanga |  |
| sanger | noun | already covered | sanga |  |
| sav | noun | already covered | sav |  |
| schmick | adjective | add | schmick | spick and span, immaculate |
| school of the air | noun | skip |  | a proper name or nickname (an institution) |
| schoolies | noun | reference | schoolies | spring break and senior week are other things |
| schooner | noun | skip |  | its size differs by state (425 ml in NSW, 285 ml in SA) |
| scorcher | noun | already covered | a-scorcher |  |
| scull | verb | already covered | skol | skol has the variant scull |
| seachange | noun | skip |  | collides with the general idiom 'a sea change' |
| secret business | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| seppo | rhyming slang | skip |  | derogatory |
| servo | noun | already covered | servo |  |
| servo pie | noun | skip |  | compositional |
| shano | nickname | skip |  | a proper name or nickname |
| shazza | nickname | skip |  | a proper name or nickname |
| she'll be right | phrase | already covered | shell-be-right |  |
| she's apples | phrase | extend | shell-be-apples | variant "she's apples" |
| sheila | noun | already covered | sheila |  |
| shindig | noun | skip |  | general English |
| shoey | verb | add | do-a-shoey | drink out of a shoe |
| shonky | adjective | already covered | shonky |  |
| shoot through | phrase | already covered | shoot-through |  |
| shoot through like a bondi tram | idiom | already covered | shoot-through-like-a-bondi-tram |  |
| shout | verb | already covered | your-shout |  |
| show pony | noun | add | a-show-pony | a show-off |
| shrapnel | noun | add | shrapnel-change | loose change |
| sick | adjective | skip |  | global youth slang, and the plain sense |
| sickie | noun | already covered | sickie |  |
| singlet | noun | already covered | singlet |  |
| skip | noun | skip |  | fraught (a slur for Anglo-Australians), and ambiguous |
| skite | phrase | already covered | skite |  |
| slab | noun | already covered | slab |  |
| sledging | verb | add | sledging | trash talk (the noun; sledge was in) |
| sleepout | noun | add | a-sleep-out | sleeping porch |
| smashed avo | noun | already covered | avo | compositional |
| smithy | nickname | skip |  | a proper name or nickname |
| smoko | noun | already covered | smoko |  |
| snag | noun | already covered | snag |  |
| sook | noun | already covered | sook |  |
| sorry day | noun | skip |  | a historical or political term of art |
| sparky | noun | add | a-sparky | electrician |
| sparrow fart | noun | extend | sparrows-fart | variant 'at sparrow fart' |
| spewing | adjective | already covered | spewin | requested; already in (spewin', DISAPPOINTED, ANGRY) |
| spit the dummy | phrase | already covered | spit-the-dummy |  |
| sports carnival | noun | add | a-sports-carnival (+ a-swimming-carnival) | sports day; swim meet added with it |
| sprung | adjective | add | sprung | caught red-handed |
| spud | noun | skip |  | general English |
| spunk | noun | already covered | a-spunk |  |
| squatter | noun | already covered | squatter |  |
| stands out like a shag on a rock | idiom | already covered | like-a-shag-on-a-rock | the shag simile is in (LONELY); CONSPICUOUS has its own |
| station | noun | already covered | station |  |
| steak and kidney | rhyming slang | skip |  | dated rhyming slang (Sydney) |
| stevo | nickname | skip |  | a proper name or nickname |
| stickybeak | noun | already covered | stickybeak |  |
| stinger suit | noun | skip |  | the thing's own name |
| stinker | noun | already covered | a-stinker |  |
| stir the possum | phrase | already covered | stir-the-possum |  |
| stoked | adjective | already covered | stoked |  |
| stolen generations | noun | skip |  | a historical or political term of art |
| stone the crows | exclamation | already covered | stone-the-crows |  |
| stoush | noun | already covered | a-stoush |  |
| straight to the pool room | idiom | add | straight-to-the-pool-room | I'll treasure it forever |
| strewth | exclamation | already covered | strewth |  |
| strife | noun | already covered | in-strife |  |
| struggle street | noun | already covered | struggle-street |  |
| stubby | noun | already covered | stubby |  |
| stubby cooler | noun | add | a-stubby-holder | koozie, can cooler (variant stubby cooler) |
| stubby short of a six-pack | phrase | already covered | stubby-short-of-a-six-pack |  |
| stuffed | adjective | already covered | stuffed |  |
| such is life | phrase | skip |  | general English (and Ned Kelly's reputed last words) |
| sunnies | noun | already covered | sunnies |  |
| super duper | adjective | skip |  | general English |
| suss out | phrase | already covered | suss-out |  |
| swag | noun | already covered | a-swag |  |
| sweet as | adjective | already covered | sweet-as |  |
| tacker | noun | already covered | little-tacker |  |
| taipan | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| tall poppy | noun | add | a-tall-poppy | a high achiever |
| tart | noun | skip |  | plain English (a pastry), and offensive of a woman |
| tassie | noun | add | tassie | narrow trigger only ('the island state'): a bare Tasmania made 'the University of Tassie' |
| tell him he's dreamin | idiom | add | tell-him-hes-dreamin | third person only (tell him to dream on) |
| tezza | nickname | skip |  | a proper name or nickname |
| the big smoke | noun | already covered | the-big-smoke |  |
| the block | noun | skip |  | ambiguous (a block of land; do the Block is in) |
| the bush | noun | already covered | the-bush |  |
| the full bottle | phrase | already covered | full-bottle-on | gated |
| the g | noun | skip |  | a proper name or nickname (the MCG) |
| the tip | noun | already covered | the-tip |  |
| thommo | nickname | skip |  | a proper name or nickname |
| thongs | noun | already covered | thongs |  |
| tickets on yourself | phrase | already covered | tickets-on-yourself |  |
| tim tam | noun | skip |  | a brand |
| tinnie | noun | already covered | tinnie | the beer; the boat sense would need the same form |
| toey | adjective | already covered | toey |  |
| togs | noun | already covered | togs |  |
| tonno | nickname | skip |  | a proper name or nickname |
| too easy | exclamation | already covered | too-easy |  |
| too right | exclamation | already covered | too-right |  |
| tops | adjective | skip |  | dated, general |
| trackie daks | noun | add | trackies | variant of trackies |
| trackies | noun | add | trackies | sweatpants, track pants |
| tradie | noun | already covered | tradie |  |
| trevo | nickname | skip |  | a proper name or nickname |
| troppo | adjective | already covered | troppo |  |
| truckie | noun | add | a-truckie | truck driver |
| true blue | adjective | add | true-blue | loyal (of people) |
| tucker | noun | already covered | tucker |  |
| tuckshop | noun | add | the-tuckshop | school cafeteria/canteen; region qld, wa |
| two-pot screamer | idiom | add | a-two-pot-screamer | a cheap drunk |
| two-up | noun | skip |  | a game's name |
| uey | phrase | add | chuck-a-uey | make a U-turn |
| ugg boots | noun | add | ugg-boots | sheepskin boots; generic in Australia |
| unreal | adjective | add | unreal | the exclamation (GREAT_EXCLAIM) |
| ute | noun | already covered | ute |  |
| vegemite | noun | skip |  | a brand |
| veggies | noun | already covered | veggies |  |
| veggo | noun | add | a-veggo | vegetarian, as a predicate of a person |
| verandah over the toy shop | idiom | add | verandah-over-the-toy-shop | a beer belly; innuendo, vulgarity 1 |
| waddy | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect (a club) |
| wag | verb | add | wag-school | skip school |
| walkabout | noun | already covered | gone-walkabout | with its sensitivity note |
| wallaby | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| wallaroo | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| waltz matilda | idiom | already covered | go-waltzing-matilda |  |
| waratah | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| wazza | nickname | skip |  | a proper name or nickname |
| we'll all be rooned | phrase | already covered | well-all-be-rooned |  |
| weetbix | noun | skip |  | a brand |
| westie | noun | skip |  | classist and regional |
| what do you think this is, bush week? | phrase | add | bush-week | do you take me for a fool? |
| wicko | nickname | skip |  | a proper name or nickname |
| wide brown land | idiom | skip |  | a poetic phrase (Mackellar) |
| widgie | noun | skip |  | dated (1950s) |
| willo | nickname | skip |  | a proper name or nickname |
| willy-willy | noun | already covered | a-willy-willy |  |
| witchetty grub | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect (bush food) |
| wobbegong | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| wog | noun | skip |  | has a slur sense |
| wombat | noun | skip |  | the thing's own name (flora or fauna), no plain-English swap |
| woolies | noun | skip |  | a brand |
| woomera | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| woop woop | noun | already covered | woop-woop |  |
| wowser | noun | add | a-wowser | a killjoy, a prude |
| wurley | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| x-ray | noun | skip |  | no distinctively Australian sense |
| yabber | verb | add | yabber-on | talk on (TALK_ON) |
| yabby | noun | add | a-yabby | crawfish, crawdad |
| yank | noun | skip |  | general English, and a verb |
| yarn | noun | add | a-yarn | a tall tale, an anecdote (have a yarn was in) |
| yeah nah | phrase | already covered | yeah-nah |  |
| yidaki | noun | skip |  | an Aboriginal cultural or sacred term: never a slang swap, out of respect |
| yobbo | noun | add | a-yobbo | a lout (HOON) |
| your blood's worth bottling | phrase | add | your-bloods-worth-bottling | high praise (WELL_DONE); dated |
| youse | pronoun | add | youse | you guys, y'all, you lot (level 4) |
| yowie | noun | skip |  | a creature of Aboriginal tradition and folklore; swapping bigfoot would change the referent |
| zac | noun | skip |  | dated (sixpence) |
| zinc | noun | skip |  | would hit the metal |

## The entries added

Level is the entry's minimum level (incoherence); triggers are its concept's (shared with any older entries on it) and its own replaces.

| id | form | frame | concept: triggers | level | vulgarity | notes |
|---|---|---|---|---|---|---|
| an-aussie | an Aussie | np | AUSTRALIAN_PERSON: an Australian | 1 | 0 |  |
| a-bogan | a bogan | np | BOGAN: redneck; chav | 1 | 0 |  |
| a-bevan | a bevan | np | BOGAN: redneck; chav | 4 | 0 | qld |
| a-yobbo | a yobbo | np | HOON: hooligan; lout; a reckless driver; a boy racer; yob | 2 | 0 |  |
| a-grub | a grub | np | SCOUNDREL: scoundrel; lowlife; rotter; troublemaker | 2 | 0 |  |
| a-drop-kick | a drop-kick | np | LOSER: a loser; a deadbeat; a hopeless case; a born loser | 2 | 0 |  |
| a-show-pony | a show pony | np | BOASTER: show-off; braggart; boaster; big talker | 3 | 0 |  |
| a-wowser | a wowser | np | KILLJOY: a killjoy; a spoilsport; a wet blanket; a party pooper / replaces: a prude; a teetotaller; a teetotaler; a moraliser; a moralizer | 3 | 0 |  |
| a-dobber | a dobber | np | TELLTALE: a snitch; a tattletale; a tattle-tale; a telltale !sign\|signs\|mark\|marks\|trace\|traces\|heart\|smell\|clue\|clues | 2 | 0 |  |
| old-mate | old mate | np | SOME_BLOKE: some random guy; this random guy; a random guy; some random bloke; some random dude; this random dude | 3 | 0 |  |
| a-tall-poppy | a tall poppy | np | HIGH_ACHIEVER: a high achiever; a high-flyer; a high flyer | 3 | 0 |  |
| a-chardonnay-socialist | a chardonnay socialist | np | CHAMPAGNE_SOCIALIST: a champagne socialist; a limousine liberal; a latte liberal | 3 | 0 |  |
| a-two-pot-screamer | a two-pot screamer | np | LIGHTWEIGHT_DRINKER: a cheap drunk; a lightweight drinker | 4 | 0 |  |
| a-p-plater | a P-plater | np | PROVISIONAL_DRIVER: provisional driver; newly licensed driver; newly-licensed driver; probationary driver | 2 | 0 |  |
| an-l-plater | an L-plater | np | LEARNER_DRIVER: learner driver; student driver | 2 | 0 |  |
| a-brickie | a brickie | np | BRICKLAYER: bricklayer | 1 | 0 |  |
| a-sparky | a sparky | np | ELECTRICIAN: electrician | 1 | 0 |  |
| a-chippy | a chippy | np | CARPENTER: carpenter | 2 | 0 |  |
| a-truckie | a truckie | np | TRUCK_DRIVER: truck driver; trucker | 1 | 0 |  |
| a-public-servant | a public servant | np | PUBLIC_SERVANT: civil servant; a civil servant; government employee | 1 | 0 |  |
| the-public-service | the public service | np | PUBLIC_SERVICE: the civil service | 1 | 0 |  |
| knock-off-work | knock off | vp | FINISH_WORK: finish work !on\|for\|in\|with\|by\|before; clock off; knock off work; call it a day; finish up for the day | 2 | 0 |  |
| do-the-hard-yards | do the hard yards | vp | WORK_HARD: break {poss} backs; break {poss} back; work {poss} fingers to the bone; slave away; toil / replaces: do the hard work; put in the hard work; do the groundwork; do the legwork | 2 | 0 |  |
| on-the-turps | on the turps | predicate_adj | ON_THE_DRINK: on a bender; on a binge; on a drinking binge; on the booze; drinking heavily | 3 | 0 |  |
| a-rort | a rort | np | RORT: a misuse of public funds; an abuse of the system; an expenses scandal | 2 | 0 |  |
| rort-the-system | rort the system | vp | GAME_SYSTEM: game the system; exploit the system; abuse the system; cheat the system; milk the system; rip off the system | 2 | 0 |  |
| a-barbecue-stopper | a barbecue stopper | np | HOT_BUTTON_ISSUE: hot-button issue; hot button issue; hot-button topic; divisive issue | 4 | 0 |  |
| shrapnel-change | shrapnel | np | LOOSE_CHANGE: loose change; spare change | 3 | 0 |  |
| lay-by | lay-by | np | LAYAWAY: layaway; a layaway plan | 1 | 0 |  |
| rego | rego | np | CAR_REGISTRATION: car registration; vehicle registration; the car registration; the vehicle registration | 1 | 0 |  |
| berley | berley | np | GROUNDBAIT: groundbait; ground bait | 3 | 0 |  |
| barra | barra | np | BARRAMUNDI: barramundi | 2 | 0 |  |
| chewie | chewie | np | CHEWING_GUM: chewing gum | 1 | 0 |  |
| a-dagwood-dog | a dagwood dog | np | CORN_DOG: corn dog; corndog | 2 | 0 |  |
| damper | damper | np | DAMPER: campfire bread; bush bread; camp bread | 2 | 0 |  |
| goon | goon | np | CASK_WINE: boxed wine; box wine; cask wine | 2 | 0 |  |
| a-goon-bag | a goon bag | np | WINE_CASK: a box of wine; a wine cask; a cask of wine | 2 | 0 |  |
| plonk | plonk | np | CHEAP_WINE: cheap wine !list\|lists\|bar\|bars\|glass\|glasses\|shop\|shops\|store\|stores; rotgut wine | 2 | 0 |  |
| a-good-drop | a good drop | np | GOOD_WINE: a good wine; a nice wine; a fine wine; a decent wine; a great wine; a lovely wine | 2 | 0 |  |
| lolly-water | lolly water | np | SUGARY_DRINK: sugary drinks; a sugary drink; sugary soft drink | 4 | 0 |  |
| bring-a-plate | bring a plate | vp | BRING_A_PLATE: bring a dish to share; bring food to share; bring something to share; bring a potluck dish | 2 | 0 |  |
| a-bikie | a bikie | np | BIKIE: biker !shorts\|jacket\|jackets\|boots\|chick\|chicks\|bar\|bars; biker gang; a motorcycle gang member | 1 | 0 |  |
| a-billycart | a billycart | np | SOAPBOX_CART: soapbox cart; soapbox racer; soapbox car; box cart | 2 | 0 |  |
| a-bingle | a bingle | np | FENDER_BENDER: fender bender; fender-bender; minor car accident; minor car crash; minor collision | 2 | 0 |  |
| a-blowie | a blowie | np | BLOWFLY: blowfly | 1 | 0 |  |
| a-bluebottle | a bluebottle | np | MAN_O_WAR: Portuguese man o' war; Portuguese man-of-war; a Portuguese man o' war; a Portuguese man-of-war | 2 | 0 |  |
| boardies | boardies | np | BOARDSHORTS: board shorts; boardshorts | 1 | 0 |  |
| budgie-smugglers | budgie smugglers | np | SWIM_BRIEFS: swim briefs; swimming briefs; speedos | 2 | 0 |  |
| a-budgie | a budgie | np | BUDGERIGAR: budgerigar; pet parakeet | 1 | 0 |  |
| a-bucks-night | a bucks night | np | BUCKS_NIGHT: bachelor party; stag party; stag night; stag do | 1 | 0 |  |
| a-hens-night | a hens night | np | HENS_NIGHT: bachelorette party; hen party; hen night; hen do | 1 | 0 |  |
| the-footy-oval | the footy oval | np | SPORTS_OVAL: the sports field; the sports ground; the school sports field; the school playing field | 2 | 0 |  |
| a-glory-box | a glory box | np | HOPE_CHEST: hope chest; dowry chest | 3 | 0 | dated |
| manchester-linen | manchester | np | HOUSEHOLD_LINEN: bed linen; household linen; bed linens; household linens | 3 | 0 |  |
| the-nature-strip | the nature strip | np | VERGE: the grass verge; the road verge; the tree lawn; the parking strip; the curb strip; the kerb strip | 2 | 0 |  |
| a-rashie | a rashie | np | RASH_VEST: rash guard; rash vest; rashguard; swim shirt | 1 | 0 |  |
| a-sleep-out | a sleep-out | np | SLEEPING_PORCH: sleeping porch; enclosed porch | 3 | 0 |  |
| a-sports-carnival | a sports carnival | np | SPORTS_DAY: sports day; school sports day; track and field day | 1 | 0 |  |
| a-swimming-carnival | a swimming carnival | np | SWIM_MEET: swim meet; swimming meet; swimming gala; swim gala | 1 | 0 |  |
| a-mufti-day | a mufti day | np | MUFTI_DAY: casual clothes day; non-uniform day; dress-down day; free dress day | 3 | 0 |  |
| a-stubby-holder | a stubby holder | np | CAN_COOLER: koozie; beer koozie; can cooler; beer cozy; can cozy; can koozie | 1 | 0 |  |
| trackies | trackies | np | SWEATPANTS: sweatpants; track pants; tracksuit pants; tracksuit bottoms; jogging pants | 1 | 0 |  |
| ugg-boots | ugg boots | np | SHEEPSKIN_BOOTS: sheepskin boots; shearling boots | 1 | 0 |  |
| the-tuckshop | the tuckshop | np | SCHOOL_CANTEEN: the school cafeteria; the school canteen; the school lunchroom | 2 | 0 | qld/wa |
| a-middy | a middy | np | MIDDY_BEER: a half-pint of beer; a half pint of beer; a small glass of beer | 3 | 0 | nsw/wa |
| a-yabby | a yabby | np | FRESHWATER_CRAYFISH: crawfish; crawdad; freshwater crayfish | 2 | 0 |  |
| a-joey | a joey | np | JOEY: baby kangaroo; baby wallaby; baby koala; baby wombat; baby possum | 1 | 0 |  |
| a-joe-blake | a Joe Blake | np | SNAKE: a slithering snake | 5 | 0 | dated |
| a-yarn | a yarn | np | TALL_TALE: a tall tale; a tall story; an anecdote | 1 | 0 |  |
| verandah-over-the-toy-shop | a verandah over the toy shop | np | BEER_GUT: beer belly; beer gut; pot belly; potbelly; paunch | 5 | 1 |  |
| aggro | aggro | predicate_adj | AGGRESSIVE: aggressive ^person; belligerent ^person; combative ^person; confrontational ^person | 2 | 0 |  |
| the-ants-pants | the ant's pants | predicate_adj | BEES_KNEES: the bee's knees; the cat's pyjamas; the cat's pajamas; the cat's whiskers | 3 | 0 |  |
| brass-monkeys | {subj} {be} brass monkeys | clause | COLD_WEATHER: it {be} freezing; it {be} freezing cold; it {be} bitterly cold; it {be} absolutely freezing; it {be} perishing | 3 | 0 |  |
| brass-monkey-weather | brass monkey weather | np | FREEZING_WEATHER: freezing weather; bitterly cold weather; freezing cold weather | 3 | 0 |  |
| bung-broken | bung | predicate_adj | BROKEN: broken; ruined@4; busted; not working@2; beyond repair@5; wrecked@4 | 3 | 0 |  |
| give-a-bit-of-curry | give {obj} a bit of curry | vp | SCOLD: tell {obj} off; yell at {obj}; get angry at {obj}; have a go at {obj}; scold {obj}; shout at {obj} / replaces: give {obj} a hard time; give {obj} grief; give {obj} heaps of grief | 4 | 0 |  |
| blind-freddy | Blind Freddy | np | ANY_FOOL: any fool; anyone with half a brain; anybody with half a brain; anyone with eyes; anybody with eyes | 4 | 0 |  |
| chunder | chunder | vp | VOMIT: vomit; puke; throw up !a\|an\|the\|his\|her\|their\|its\|our\|my\|your\|some\|any\|this\|that\|these\|those\|new\|questions\|walls\|barriers\|obstacles\|roadblocks\|hands\|arms\|dust\|ideas | 2 | 0 |  |
| come-a-gutser | come a gutser | vp | FALL_OVER: fall on the floor; fall onto the floor; fall over; fall down; trip over; fall flat | 3 | 0 |  |
| within-cooee | within cooee | adv | WITHIN_EARSHOT: within earshot; within shouting distance; within calling distance; within hailing distance | 3 | 0 |  |
| couldnt-organise-a-chook-raffle | {subj} couldn't organise a chook raffle | clause | INCOMPETENT: {subj} {be} completely incompetent; {subj} {be} totally incompetent; {subj} {be} utterly incompetent; {subj} {be} hopelessly disorganised; {subj} {be} hopelessly disorganized; {subj} {be} completely disorganised; {subj} couldn't organise a piss-up in a brewery; {subj} couldn't organize a piss-up in a brewery | 3 | 0 |  |
| cup-of-tea-bex-lie-down | have a cup of tea, a Bex and a good lie-down | imperative | CALM_DOWN: calm down; settle down; relax; take it easy; chill out; cool it | 5 | 0 | dated |
| deadset-adj | deadset | adj | UTTER: utter; out-and-out; absolute !value\|values\|zero\|majority\|terms\|power\|powers\|pitch\|humidity\|path\|paths\|address\|monarchy\|monarch\|monarchs\|minimum\|maximum\|temperature\|magnitude\|threshold\|risk\|number\|numbers\|despotism\|tyranny\|tyrant\|tyrants\|rule\|ruler\|rulers\|authority\|control\|sovereignty\|dictatorship\|dictator\|discretion\|freedom\|liberty\|right\|rights\|silence\|priority\|necessity\|requirement\|limit\|limits\|position\|location\|reference\|error\|deviation\|advantage\|poverty\|truth\|confidence\|trust\|ownership\|immunity\|ban\|bans\|privilege\|and | 3 | 0 |  |
| didnt-come-down-in-the-last-shower | {subj} didn't come down in the last shower | clause | NOT_NAIVE: {subj} wasn't born yesterday; {subj} weren't born yesterday; {subj} {be} not naive; {subj} {be} no fool | 3 | 0 |  |
| do-a-bradbury | do a Bradbury | vp | WIN_FROM_NOWHERE: win against all odds; win against the odds; come from nowhere to win; snatch an unlikely victory | 4 | 0 |  |
| an-emu-bob | an emu bob | np | LITTER_PICK: litter pick; litter pick-up; litter patrol; litter sweep | 4 | 0 |  |
| fossick-around | fossick around | vp | RUMMAGE: rummage around; rummage about; root around; root about | 3 | 0 |  |
| fossick-through | fossick through {np} | vp | RUMMAGE_THROUGH: rummage through {np}; root through {np}; rifle through {np} | 3 | 0 |  |
| full-on | full-on | predicate_adj | INTENSE: intense; really intense; hectic; a lot to deal with; a lot to handle | 2 | 0 |  |
| get-knotted | get knotted | imperative | GO_AWAY: go away; get lost; leave me alone; buzz off; clear off; get out of here; shoo | 3 | 0 | dated |
| get-a-guernsey | get a guernsey | vp | GET_SELECTED: make the team; get picked for the team; get selected for the team | 4 | 0 |  |
| happy-little-vegemite | a happy little Vegemite | predicate_adj | CONTENT: content; comfortable; settled; snug; perfectly happy; happy as can be@4; at ease; contented | 4 | 0 |  |
| put-the-hard-word-on | put the hard word on {obj} for {np} | vp | HIT_UP_FOR: hit {obj} up for {np}; tap {obj} for {np} | 4 | 0 |  |
| put-the-acid-on | put the acid on {obj} for {np} | vp | HIT_UP_FOR: hit {obj} up for {np}; tap {obj} for {np} | 5 | 0 | dated |
| hooley-dooley | hooley dooley | interjection | AMAZED: wow; good heavens; goodness me; holy cow; well I never; golly; gosh; my goodness | 4 | 0 |  |
| hoon-around | hoon around | vp | HOON_DRIVE: drive recklessly; go joyriding; do burnouts; drive like a maniac; drive like a lunatic | 2 | 0 |  |
| send-her-down-hughie | send her down, Hughie | interjection | LET_IT_RAIN: let it rain; bring on the rain | 5 | 0 | dated |
| a-king-hit | a king hit | np | SUCKER_PUNCH: sucker punch; sucker-punch | 2 | 0 |  |
| lairy | lairy | adj | SHOWY: swanky; flashy; showy; ostentatious@4; dressed to the nines@4 / replaces: garish; gaudy | 3 | 0 |  |
| strong-as-a-mallee-bull | as strong as a Mallee bull | predicate_adj | STRONG_FIT: strong as an ox; as strong as an ox; strong as a horse; as strong as a horse; fit as a fiddle; as fit as a fiddle | 4 | 0 |  |
| miserable-as-a-bandicoot | as miserable as a bandicoot | predicate_adj | SAD: sad; unhappy; miserable@4; depressed@4; glum; gloomy; feeling down; feeling low; despondent@4; dejected; downcast@3; down in the mouth | 5 | 0 | dated |
| not-a-drama | not a drama | interjection | NO_PROBLEM: no problem; no problem at all; you're welcome; don't worry; don't worry about it; not a problem; it's no trouble; that's fine; it's fine; that's okay; no trouble; never mind; it's all good; all good | 2 | 0 |  |
| arthur-or-martha | {subj} {do}n't know if {subj} {be} Arthur or Martha | clause | FLUSTERED: {subj} {be} completely confused; {subj} {be} totally confused; {subj} {be} all at sea; {subj} {be} in a complete muddle; {subj} {do}n't know whether {subj} {be} coming or going | 4 | 0 |  |
| not-within-a-bulls-roar | not within a bull's roar of the | adv | NOWHERE_NEAR: nowhere near the !same\|level\|standard\|quality\|amount\|number\|size\|kind | 4 | 0 |  |
| ocker-adj | ocker | adj | BROAD_AUSSIE: broad Australian; stereotypically Australian | 3 | 0 |  |
| off-like-a-brides-nightie | off like a bride's nightie | predicate_adj | OFF_IN_A_FLASH: off like a shot; off in a flash; gone in a flash; gone like a shot | 4 | 1 |  |
| pash-obj | pash {obj} | vp | MAKE_OUT: make out with {obj}; snog {obj}; kiss {obj} passionately | 2 | 0 |  |
| pigs-bum | pig's bum | interjection | DREAM_ON: you must be joking; you've got to be kidding; in your dreams; dream on | 4 | 0 |  |
| pike-out | pike out | vp | BACK_OUT: pull out at the last minute; chicken out | 3 | 0 |  |
| a-piker | a piker | np | FLAKE: a flake !of; a flaky friend; a no-show | 3 | 0 |  |
| piss-weak | piss weak | predicate_adj | PATHETIC: pathetic; feeble; pitiful; a poor effort; weak as water | 3 | 2 |  |
| a-porky | a porky | np | A_LIE: a fib; a lie !detector\|detectors\|down\|in\|to | 3 | 0 |  |
| dont-come-the-raw-prawn | don't come the raw prawn with me | imperative | DONT_FOOL_ME: don't try to fool me; don't try to con me; don't try to trick me; don't play dumb with me; don't take me for a fool; do you think I'm stupid; do you take me for a fool; do you think I'm an idiot; what do you take me for | 3 | 0 |  |
| bush-week | what do ya think this is, bush week? | interjection | DONT_FOOL_ME: don't try to fool me; don't try to con me; don't try to trick me; don't play dumb with me; don't take me for a fool; do you think I'm stupid; do you take me for a fool; do you think I'm an idiot; what do you take me for | 4 | 0 |  |
| rough-as-guts | rough as guts | predicate_adj | UNCOUTH: uncouth; crude; coarse; ill-mannered; rough around the edges; badly behaved; unruly | 3 | 0 |  |
| rough-end-of-the-pineapple | get the rough end of the pineapple | vp | RAW_DEAL: get a raw deal; get the short end of the stick; get the rough end of the stick | 3 | 0 |  |
| schmick | schmick | predicate_adj | SPIFFY: spick and span; immaculate; spiffy; snazzy; in mint condition | 3 | 0 |  |
| do-a-shoey | do a shoey | vp | SHOEY: drink out of a shoe; drink from a shoe; drink beer out of a shoe; drink champagne out of a shoe | 3 | 0 |  |
| sledging | sledging | np | TRASH_TALK: trash talk; trash-talk; trash talking; trash-talking | 2 | 0 |  |
| sprung | sprung | predicate_adj | CAUGHT_OUT: caught red-handed; caught in the act | 2 | 0 |  |
| straight-to-the-pool-room | that's going straight to the pool room | interjection | TREASURE_IT: I'll treasure it forever; I'll treasure it always; I will treasure it forever; I'll treasure this forever | 4 | 0 |  |
| tell-him-hes-dreamin | tell him he's dreamin' | interjection | TELL_HIM_DREAMING: tell him to dream on; tell them to dream on | 3 | 0 |  |
| true-blue | true blue | predicate_adj | LOYAL: loyal ^person; fiercely loyal ^person; utterly loyal ^person; dependable ^person; staunch ^person | 2 | 0 |  |
| chuck-a-uey | chuck a uey | vp | U_TURN: make a U-turn; do a U-turn; pull a U-turn; hang a U-turn; make a u-turn; do a u-turn | 2 | 0 |  |
| unreal | unreal | interjection | GREAT_EXCLAIM: great; excellent; brilliant; wonderful; fantastic; perfect; lovely | 2 | 0 |  |
| a-veggo | a veggo | predicate_adj | VEGETARIAN: vegetarian ^person; a vegetarian ^person !chef\|chefs\|cook\|cooks\|restaurant\|restaurants\|cafe\|cafes\|option\|options\|meal\|meals\|dish\|dishes\|diet\|diets\|lasagne\|lasagna\|burger\|burgers\|pizza\|menu\|menus\|recipe\|recipes\|alternative\|version\|society\|activist\|activists\|household\|family\|place | 2 | 0 |  |
| wag-school | wag school | vp | TRUANT: skip school; play hooky; play truant; ditch school; bunk off school; skip class; cut class | 2 | 0 |  |
| yabber-on | yabber on | vp | TALK_ON: ramble; go on and on; talk at length; babble; prattle; drone on; talk {poss} ear off; natter on | 3 | 0 |  |
| your-bloods-worth-bottling | your blood's worth bottling | interjection | WELL_DONE: well done; good for you; nice one; bravo; good job | 4 | 0 | dated |
| youse | youse | np | YOU_PLURAL: you guys; y'all; you lot; you all !right\|alright\|good | 4 | 0 |  |
| you-little-bottler | you little bottler | interjection | GREAT_EXCLAIM: great; excellent; brilliant; wonderful; fantastic; perfect; lovely | 4 | 0 | dated |
| a-captain-cook | a Captain Cook | np | LOOK: a look !of\|on; a quick look; a peek@2; a quick glance@2 | 4 | 0 |  |
| a-bag-of-fruit | a bag of fruit | np | SUIT_CLOTHES: suit and tie; business suit; three-piece suit | 5 | 0 | dated |
| laid-back | laid-back | predicate_adj | EASYGOING: easygoing ^person; easy-going ^person; relaxed ^person; mellow ^person | 1 | 0 | gated not_aussie |
| a-shell-be-right-attitude | a she'll-be-right attitude | np | RELAXED_ATTITUDE: a laid-back attitude; a relaxed attitude; a carefree attitude; a laid back attitude | 3 | 0 |  |
| tassie | Tassie | np | TASMANIA: the island state | 2 | 0 |  |
| brissie | Brissie | np | BRISBANE: the Queensland capital | 3 | 0 |  |
| a-banana-bender | a banana bender | np | QUEENSLANDER: a person from Queensland | 5 | 0 |  |
| a-croweater | a croweater | np | SOUTH_AUSTRALIAN: a person from South Australia | 5 | 0 |  |
| a-drop-bear | a drop bear | np | DROP_BEAR: a killer koala; a carnivorous koala | 4 | 0 |  |
| aerial-ping-pong | aerial ping-pong | np | AUSSIE_RULES: Aussie rules football; as its detractors call it | 5 | 0 |  |
| a-grey-nomad | a grey nomad | np | GREY_NOMAD: a retired caravanner; retired caravanners | 3 | 0 |  |
| the-fremantle-doctor | the Fremantle Doctor | np | FREO_DOCTOR: Perth's afternoon sea breeze | 4 | 0 | wa |
| schoolies | Schoolies | np | SCHOOLIES: the school leavers' celebration week | 2 | 0 |  |
| an-eshay | an eshay | np | ESHAY: a member of the eshay subculture | 5 | 0 |  |
| on-the-tools | on the tools | predicate_adj | ON_THE_TOOLS: doing hands-on trade work | 3 | 0 |  |
| a-wigwam-for-a-gooses-bridle | a wigwam for a goose's bridle | np | MIND_YOUR_OWN: a thingamajig for a whatsit | 5 | 0 | dated |
| cooked-done-for | cooked | predicate_adj | DONE_FOR: done for; doomed; toast ^person; in deep trouble@4 | 3 | 0 |  |

## Review (before merging)

Checked by the session that delegated the round:

- **Wording.** The glosses were compared, for a sample, with the site's definitions: each is in its own words, and
  where they agree it is on facts (285 ml, Steven Bradbury, the Fremantle Doctor's timing), not on phrasing.
- **Wrong senses, tested on sentences that use each risky trigger otherwise** (levels 2 and 4, seed 1):
  - `bung` joined BROKEN, whose bare "broken" trigger (older than this round) also took "his heart was broken" ->
    "ticker was bung" and "the silence was broken" -> "stuffed". A guard concept, BROKEN_OTHER_SENSE, now holds
    the figurative senses (a heart, a silence, a record, a promise, the law, the ice, the news).
  - `full-on`: "intense" took "the pain was intense" -> "full-on". "intense" and "really intense" are out of
    INTENSE's triggers; "hectic" and "a lot to deal with" stay.
  - `chunder` moved from level 2 to 3: "If you vomit, call a doctor" -> "chunder" at level 2 is too crude for
    "light, still clean".
  - Fine as they are: "met an Aussie at the pub" ("an Australian company" left alone), "aggro with the staff"
    ("aggressive treatment" left alone), "the washing machine is bung", "my mate is true blue".
- **Left as noted:** "the dog is loyal" -> "true blue" (the people-only marker counts "dog"; an engine issue),
  the regional entries firing without a region, and the innuendo ratings (vulgarity 1).
- **Golden:** the 18 changed outputs, each a fix or neutral, as listed above.
