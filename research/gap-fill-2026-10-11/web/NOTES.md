# Web research notes: gap-fill 2026-10-11

Output: `findings.yaml` has 124 terms, of which 32 are fillers and discourse markers (or 33 if you count "hang on a tick"). Confidence: 61 high, 52 medium, 11 low. Register: 108 current, 15 dated, 1 rare. 86 terms point at `NEW:` concepts and the rest extend existing concepts.

## Method and an important limitation

- **Direct page fetches were blocked.** WebFetch failed DNS for every host, and curl through the agent proxy got `403 connect_rejected`, the egress policy (anu.edu.au, wiktionary, abc.net.au, sbs, reddit, theconversation, monash, macquarie were all tested). Every attestation therefore comes from the **WebSearch tool, which retrieved and summarised the pages it lists**. I cite only URLs whose returned content supported the term. That is weaker than reading each page myself: quotes and entry IDs come through a summariser.
  - Green's Dictionary of Slang entry IDs for a few terms (stonkered, half-cut/shickered/molo, bullshitter) came from a result set that mixed several entries, so the term-to-entry mapping is unverified. This is flagged in those entries' notes.
  - Macquarie pages are cited only to verify, as the policy allows; no definition text is copied anywhere. All meanings are my own short wording.
- No r/australia threads were reachable, so the "current usage" judgements rest on Australian media, university pages, dictionaries and my own knowledge of the register. They are flagged where the source is thin.

## Searches run (≈95 queries)

Grouped by topic:
- **Discourse and fillers.** Sentence-final "but" in Australian English (Mulder/Thompson). Burridge's "yeah no"/"yeah nah". Australian "eh"/"hey" tags. "look," as an opener (politicians, footballers). Monash Lens discourse markers ("a bit"). Monash top Aussie slang survey. Manns's articles on The Conversation. Queensland "but"/"hey". Wiktionary "but" (adverb). eWAVE features. Utterance-final tags in Aboriginal/non-Aboriginal English (UWA). General extenders ("and stuff/and that/or something"). Quotative "be like"/"goes" (Rodríguez Louro). "but yeah"/"so yeah". "I s'pose"/"dunno". Aussie English podcast episodes (yes/no, good and bad news). "heaps good". "all good". "legend" as thanks. "sweet as" and the adj+as intensifier. "how good is that". "no wukkas". "good on ya". "goodo". "you're not wrong". "to be fair". "fair call". "far out". "tell him he's dreamin'". "pull the other one"/"come off it". "unna". Aboriginal English "deadly"/"gammon"/"shame".
- **Emotions.** "chuck a tanty", "rark up", "spewing/dark on/shitty", "arc up", "crack the shits", "gives me the shits", "filthy/cut", "toey", "having kittens/in a tizz", "chuffed/over the moon", "bored stiff/shitless", "shame job", "chuck a ..." construction (ANDC/OUP blog).
- **Fatigue, money, luck.** "zonked/shattered/done in", "exy", "costs an arm and a leg/a bit steep", "motza", "making a good quid", "on the bones of my arse", "stiff/bad trot", "stiff cheddar", "put the mozz on".
- **Drink and party.** "blotto/trollied/legless/shickered/full as a state school", Macquarie drinking words, "pres/BYO", "piss-up/shindig/doof/rager".
- **Character and looks.** "full bottle (on)", "rough as guts/bags", "up himself", "tickets on himself", "switched on/smart cookie", "no flies on", "shout", "feral", "off with the pixies", "odd bod/queer fish", "dull as dishwater/boring as batshit", "spunk/spunky", "a good sort", "unco", "suss".
- **Physical, weather, time.** "hoon", "hairy/dicey/sketchy", "southerly buster/willy-willy", "blowing a dog off a chain", Weatherzone weather phrases, "cracker/beaut/ripper of a day", "sparrow's fart", "slow as a wet week", "like a wet week", "wide awake".
- **People and places.** "the missus/trouble and strife/hubby/the olds", "the olds/oldies", "hubby/better half", "durry", "ciggie/rollie/dart", "bitzer", "tea" for the evening meal, "little lunch/big lunch", "counter lunch".
- **Actions and chat.** "tell porkies", "bullshit artist", "stir the possum/stirrer", "muck around", "have a barney/argy-bargy", "biffo", "towel up", "perv", "have a stickybeak", "hang on a tick", "a mo/half a mo", "do a bomb/bombie", "hop in", "bags", "suss out", "goss", "furphy", "earbash", "chinwag/chew the fat", "bend your ear/natter", "run off my feet/snowed under", "flat out".

## Sources relied on most

1. **Green's Dictionary of Slang** (greensdictofslang.com): regional labels and Australian citations for about 35 terms.
2. **Macquarie Dictionary blog / Aussie Word of the Week**, used to verify only: arc up, no flies on you, bad trot / mozz, stir the possum, pres / kick on / skol, chuck a bombie, unco, goss, no wukkas, spit the dummy / chuck a micky, and the Australian Word Map.
3. **Wiktionary** (Australian-labelled senses): exy, durry, bitzer, goss, toey, unco, bags, chinwag, biffo, barney, suss, perv, furphy, deadly, my arse.
4. **Linguistics research**:
   - Mulder, Thompson & Penry Williams (final but)
   - eWAVE atlas (clause-final but; Aboriginal English invariant tags)
   - Burridge & Florey 2002 (yeah-no)
   - Monash Lens / Burridge & Manns ("a bit", the spunk family, the Aussie slang survey)
   - Cambridge *English Today* (adj + as)
   - UWA (Fraiese, Rodríguez Louro & Collard on utterance-final tags; Rodríguez Louro on quotatives; Louro & Collard on Aboriginal English)
5. **ANU Australian National Dictionary Centre** pages, seen only through search: tickets on yourself, earbash, put the mozz on, hoon (Word of the Month PDF), chuck a wobbly (OUP blog).
6. **Others.** Aussie English podcast (Pete Smissen): far out, fair call, bad trot, bummer/bugger, biffo, sparrow's fart. Australian institutions: BOM (southerly buster), NFSA, Screen Australia and The Conversation (The Castle), SBS (deadly, gammon), Charles Sturt University (cracker of a day), Weatherzone.

## Rejected or left out, and why

| Term | Reason |
|---|---|
| chuck a tanty | Not attested. Only "tanty" and the "chuck a ..." pattern were found. |
| rark up | Not attested (the search only turned up "rock up"). |
| dark on (angry) | Not attested. |
| filthy (angry) | Not attested in the search, though it is already in ANGRY. |
| rough as guts | The variant very likely exists, but I couldn't confirm a definition. It's mentioned in the notes of "rough as bags". |
| smart cookie | American (Dictionary of American Slang), not Australian. |
| switched on | Not labelled Australian anywhere I found. |
| chuffed | Every source labels it British. |
| over the moon, on cloud nine | General English. |
| blotto, trollied, legless, shattered, knackered | Labelled British. Knackered is already in TIRED anyway. |
| "daylight robbery", "a bit steep" | British teaching lists only. |
| shindig, rager | General English and US. |
| snowed under | General English with no Australian angle. For the busy gap, the fix is a trigger ("run off {poss} feet" → BUSY), not a new form. |
| have kittens, in a tizz | Labelled UK, or originally US. |
| bored stiff, bored out of my brain | General English. |
| as boring as batshit | Not attested. |
| on the bones of my arse | Not attested in any source. |
| stiff cheddar | Not attested. "Stiff (luck)" was kept. |
| you're not wrong | General English. |
| to be fair | No Australian-specific source. Heard a lot here, but unproven. |
| "yeah, look" / "look," as an opener | Widely seen as an Australian political and sporting tic, but I found **no** source (only a forum aside), so it was left out. Worth re-checking if ABC/Crikey pages become reachable. |
| "but yeah" / "so yeah" trailing closers | No source. Plausible but unattested. |
| I s'pose | No source found. |
| ciggie | Only content-farm sources. It is common in Aus and UK, so treat it as low priority. |
| fag | British, and a slur in the US. Excluded. |
| bullshit artist | Documented use is American. "Bullshitter" was kept instead. |
| bull's wool artist | Dated and obscure. |
| happy as a bastard on Father's Day | Real (Wilkes), but it means unhappy, which doesn't fit the gaps. |
| "must have killed a Chinaman" (unlucky) | Real but an ethnic slur. Excluded. |
| bogan | Not searched. It's classist, and no inventory gap needs it. |
| awake as a possum / any "wide awake" idiom | Nothing found. |
| shrimp on the barbie and other tourist fakes | Not considered. |

## Gaps with no genuine Aussie alternative (Australians just say the plain word)

- **Things.**
  - chair, bowl, table, door, bedroom, upstairs, blanket ("doona" already covers a quilt), beds, porridge, bear, shower, house.
  - house: "the place", "my place", "round at Dave's" are idiomatic but not slang; PLACE "the joint" already exists.
  - beach: just "the beach"; at most "down the beach" with the preposition dropped, which is unattested here.
- **People.**
  - girl: "sheila" (WOMAN) is for adult women, and "littlie/little tacker" (CHILD) are gender-neutral. No genuine Aussie word for a girl.
  - husband: only the general "hubby", and "the old man" clashes with FATHER.
- **Fable and speech vocabulary.** Conceive, government, proposition, portion, cause, civil, final, highly, increase, advance, appoint, rather, goal, pace, steady, moment (beyond "a tick"), agree (GO_ALONG exists), answer, choose ("bags" covers claiming only), decide, forget, earth, ground ("the deck", as in "hit the deck", is plausible but unsearched), inside, happily ("happy as Larry" exists), comfortably ("snug as a bug" exists).
- **States with no attested Aussie form.**
  - jealous ("jelly" is international youth slang); worried (beyond "toey"); tiny; wet/soaked ("like a drowned rat" is general English).
  - noisy (only "hoon" for loud louts and cars); difficult ("a bastard/bugger of a job" are plausible combinations of existing words, but unattested).
  - generous (only "shout" for paying); boring; handsome specifically (the spunk family covers it).
  - slow/slowly (only the weakly attested "slow as a wet week"); late; nearby ("just up the road" is general English; HEREABOUTS exists).
  - wide awake (known failure: no idiom found; suggest a plain AWAKE concept, or leave it untranslated).
- **Actions.** wake up, tidy up and cry (CRY is already well covered) have nothing new. jump has only the narrow "chuck a bombie" for jumping into water.

## Suggestions that need no new form (triggers on existing concepts)

- **TIRED**: add weary, fatigued, fatigue, exhausted.
- **DRUNK**: add inebriated, intoxicated, tipsy.
- **ANGRY**: add irate, enraged, incensed.
- **SAD**: add despondent, dejected, downcast, glum.
- **HAPPY**: add elated, jubilant, overjoyed, thrilled.
- **BROKE**: add destitute, impoverished, penniless, hard up.
- **STRUGGLE** ("do it tough"): add "live in poverty".
- **SCARED**: add petrified, terrified.
- **BUSY**: add "run off {poss} feet" and "rushed off {poss} feet".
- **RICH**: add "a heap of money", "rolling in money", "a pile of cash", "made of money" (the forms "rollin' in it", "cashed up" and "loaded" already fit).
- **CHAT**: add chinwag, chatting, natter, "chew the fat".
- **FIGHT**: add argument, row, quarrel, argue ("a blue" is often a verbal argument).
- **NOSY_PERSON**: add gossip (the person) and busybody.
- **The existing garnish tag "ay"** is the same particle as "eh". The inventory lists "eh" as missing, but a spelling variant may be all that's needed.
