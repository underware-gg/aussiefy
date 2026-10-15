# Four more retellings, three ways (2026-10-11, after the classics round)

These are the rest of the new reference texts: Hansel and Gretel, The Raven, The Boy Who Cried Wolf and the Declaration of Independence. Each was retold three ways at level 5, as in `COMPARISON.md`:
- **Base:** the deterministic engine, seed 0.
- **Yarn mode:** an agent working through `yarn_tools.py` (brief, `lookup_slang`, `check_draft`, `submit_yarn`), logged in `harnessed/*.log.jsonl`.
- **Unharnessed:** an agent with only the original text.

The engine now has the classics round's 210 entries and the fixes since the first comparison: "Mr.", the possessive "bloody", stock closers in the guide, and riffs left out of planned phrases. Lookup still uses model 1.2.0.

| text | base | yarn mode | submits | unharnessed |
|---|---|---|---|---|
| Hansel and Gretel (894 words) | 891 | 960 | 1 | 989 |
| The Raven, 6 stanzas (352) | 358 | 511 | 2 | 394 |
| The Boy Who Cried Wolf (141) | 155 | 256 | 2 | 251 |
| Declaration of Independence (337) | 353 | 486 | 2 | 510 |

The 104 phrases the unharnessed agents used that the dictionary lacks are in `new_phrases-2.yaml`. They're unverified, with the agents' own low-confidence items left out. Among them: *be shot of 'em*, *have a lend of*, *bullshit artist*, *within cooee*, *had the hide*, *clapped-out*, *goes feral*, *knock up a new one*, *give it the flick*, *townies*, *doin' it tough*, *rorts*, *a real shocker*.

## What stands out

**The keep-60% rule is now yarn mode's main problem.** It made the agents put the engine's wrong-sense picks back into three of the four yarns:
- **The Declaration:** the first submit kept 19% and was rejected. To pass, the agent reworked *battlers* (for "one people"), *the pollies* (for a form of government), *kicked off* (for "long established") and *the joint* (for "the establishment of a tyranny") back in. It bent them toward their real senses, but the strain shows ("a pollie only gets his say-so from the consent of the punters it's governin'").
- **The Boy Who Cried Wolf:** *the poor battlers* and *the punters down the town* had to come back for "the villagers".
- **Hansel and Gretel** was accepted first time. The agent wrote from scratch and kept enough.

The rule exists so a yarn keeps the dictionary's voice. But it can't tell a good planned phrase from a wrong one, so it enforces the engine's errors too. That's a design call for you; there are options at the end.

**Base mode's wrong senses**, all of which went into the planned phrases:
- **"great" read as excellent:** "a great forest" becomes *a beaut bush*, "a great dearth" becomes *ripper*.
- **"fantastic terrors"** (fanciful) becomes *ripper terrors*.
- **"each separate dying ember"** becomes *each separate carkin' it ember*: a verb phrase used as an adjective.
- **"one people"** becomes *one battlers*; "Government" becomes *pollie*.
- **"long established"** becomes *long kicked off*; "the establishment of" becomes *the joint of*.
- **"be quit of them"** becomes *chuck it in of 'em*.
- **"really"** (in reality) becomes *properly*; "dinner" at noon becomes *tea*.
- **Other slips:**
  - "the people" becomes *the punters* and *the battlers*;
  - "This it is" becomes *This it's*;
  - a stray capital in "Jeez, Surely";
  - *ain't*;
  - tag-ons in narration;
  - "ya flamin' mongrel" on the father's gentle line;
  - stock closers ("Faaaaaark me.", "Too easy." after The Raven).

**The draft checker's false alarms**, reported by all four yarn agents:
- **Capitalised common nouns count as names.** `name_dropped` fires on any capitalised word the yarn leaves out: the Declaration's "Course, Despotism, Form, Powers, Tyranny", The Raven's line-initial "Darkness, Nameless, Thrilled", the fable's "Boy". `name_added` fires on "Dad", "Aussie" and "Tuesday".
- **Gated entries' single-word forms are flagged anywhere.** "blow" (gated, meaning boast) was flagged in "blow over".
- **Suggestions in the wrong sense:**
  - "the willies" (the creeps) read as PENIS;
  - "ya great boofhead" offered *ripper*;
  - "the very things" offered *dead*;
  - "settle down" offered *pull your head in* (rude);
  - "a fair bit", which the guide recommends, offered to swap for *heaps*.
- **A quote spanning several lines** lost its dialogue context, so "It's just the wind, mate." was flagged as a tag in narration.

**Lookup (model 1.2.0) has real misses on plain queries agents actually send:**
- **Antonyms and near-opposites:** "honest" returns *dodgy*, "put up with" returns *chuck it in*.
- **Wrong sense:**
  - "sleep" returns *have a root*;
  - "dying" returns *toey*;
  - "dark" returns *down in the dumps*;
  - "very cold" returns beer (*coldie*, *stubby*);
  - "established" returns *snug as a bug*;
  - "stepmother" returns *nan*;
  - "a prank" returns *a spunkrat*;
  - "fun" returns only mocking words;
  - "kill" returns *ringbark*;
  - "ignore" returns *bludge*.
- **Nothing found:** "shepherd", "book", "visitor", "tyranny", "king", "tossing and turning".

These are what the training README's next idea asks for ("broaden `reference.yaml` with plain queries agents actually send"). Several belong in it as must-not checks before 1.3.0 is judged.

**The unharnessed retellings** are again the most natural:
- Hansel: *flat broke, hasn't got a brass razoo*, *a real shocker of a drought*.
- The Raven: *bleak as buggery*, *gave me the heebie-jeebies*.
- The Wolf: *have a lend of the locals*, *not a wolf within cooee*.
- The Declaration: *plain as the nose on your face*.

Yarn mode was close behind and sometimes as good: *as much help as a screen door on a submarine*, *stickin' out like a country dunny*, *Butter wouldn't melt in her mouth, would it?*. The stock-closer change worked: no yarn ends on a stock exclamation.

## Proposed fixes (not done yet)

1. **The keep-60% rule.** Options:
   - lower it (to 40%);
   - let the agent decline a planned phrase with a one-line reason, logged and counted as kept;
   - only count planned phrases that pass a sense check: the model's similarity between the original span and the entry's gloss.

   I'd do the second: it keeps the dictionary's voice without forcing errors, and the logged reasons are useful data.
2. **Lint:**
   - only treat a capitalised word as a name if it's capitalised mid-sentence in the original and isn't a dictionary word;
   - don't flag a gated entry's single-word form;
   - keep dialogue context across a multi-line quote.
3. **Engine senses:**
   - narrow "great" (excellent) to predicate and exclamation use, so "a great forest" stays;
   - "fantastic" only as praise;
   - verb-phrase entries never fill an adjective slot ("dying ember");
   - a "one/a + plural form" guard;
   - drop "Government" from the POLITICIAN triggers.
4. **The reference set:** add the lookup misses above as must-not and should checks, then judge 1.3.0 against it.

---

## Hansel and Gretel

### Base (level 5)

> Fair fuckin' dinkum, NEAR a beaut bush there lived a poor woodcutter'n his wife, and his two nippers; the young fella's name was Hansel and the girl's Grethel. They had sweet bugger-all to bite or to sup, and once, when there was ripper dearth in the land, the bloke couldn't even gain the daily bread. Struth, as he lay in bed one night thinking of this, and turning'n chuckin', he sighed heavily, and said to his wife,  
>
> "What will become of us? we can't even feed our bloody littlies; there's bugger all left for ourselves."  
>
> "I'll tell ya what, husband," answered the wife; "we'll take the ankle biters early in the morning into the bush, where it's thickest; we'll make 'em a fire, and we'll give each of 'em a piece of bread, then we'll go to our work and leave 'em alone; they'll never find the way home again, and we'll be chuck it in of 'em."  
>
> "Nah, wife," said the cove, "I can't do that; I can't bloody well find in me bloody ticker to take me little fellas into the bush'n to leave 'em there alone; the wild animals would soon come'n scoff 'em."  
>
> "O ya boofhead," said she, "then we'll all four starve; ya had better get the coffins ready,"--and she left him no peace until he consented, ya drongo.  
>
> "But I bloody pity the poor little tackers," said the bloke.  
>
> Jeez Louise, the two nippers hadn't been able to sleep for hunger, and had heard what their step-mother had said to their old man. Grethel blubbered bitterly, and said to Hansel,  
>
> "It's all over with us."  
>
> "Do be quiet, Grethel," said Hansel, "and don't bloody well fret; I'll manage somethin'." And when the parents had gone to sleep he got up, put on his little coat, opened the back door, and slipped out. Now, the moon was shining brightly, and the white flints that lay in front of the house glistened like pieces of silver. Hansel stooped'n filled the little pocket of his coat as full as it would hold. Then he went back again, and said to Grethel,  
>
> "Be easy, dear little sister, and go to sleep quietly; God won't forsake us," and laid himself down again in his bed, mate.  
>
> When the day was breaking, and before the sun had risen, the wife came and awakened the two littlies, saying,  
>
> "Get up, ya lazy bones; we're going into the bush to cut wood."  
>
> Then she gave each of them a piece of bread, and said,  
>
> "That's for tea, and ya must not eat it before then, for you'll get no more."  
>
> Grethel carried the bread under her apron, for Hansel had his pockets full of the flints. Then they set off all together on their way to the bush. When they had gone a little way Hansel stood still'n looked back towards the house, and this he did again'n again, till his old fella said to him,  
>
> "Hansel, what are ya looking at, ya flamin' mongrel? take care not to forget yer legs."  
>
> "O father," said Hansel, "I'm lookin' at me little white kitten, who's sitting up on the roof to bid me good-bye."  
>
> "Ya young nong," said the sheila, "that ain't yer kitten, but the sunshine on the chimney-pot."  
>
> Of course Hansel hadn't been lookin' at his kitten, but had been taking every now and then a flint from his pocket and dropping it on the frog and toad.  
>
> When they reached the middle of the bush the father told the nippers to collect wood to make a fire to keep 'em warm; and Hansel and Grethel gathered brushwood enough for a little mountain; and it was set on fire, and when the flame was burning quite high the wife said,  
>
> "Now lie down by the fire and rest yourselves, ya littlies, and we'll go'n cut wood; and when we're ready we'll come'n fetch ya."  
>
> So Hansel and Grethel sat by the fire, and at noon they each ate their pieces of bread. They reckoned their father was in the wood all the time, as they seemed to hear the strokes of the axe: but properly it was only a dry branch hangin' to a withered tree that the wind moved to and fro. So when they had stayed there yonks their eyelids closed with weariness, and they went out like a light. When at last they woke it was night, and Grethel began to cry, and said,  
>
> "How will we ever get outta this wood?" But Hansel comforted her, sayin',  
>
> "Wait a little while longer, until the moon rises, and then we can easily find the way home."  
>
> And when the full moon got up Hansel took his little sister by the hand, and followed the way where the flint stones shone like silver, and showed them the road. They walked on the whole night through, and at the break of day they came to their father's house. They knocked at the door, and when the wife opened it'n saw that it was Hansel and Grethel she said,  
>
> "Ya naughty littlies, why did ya sleep so long in the wood? we reckoned ya were never comin' home again!"  
>
> But the father was glad, for it had gone to his ticker to leave them both in the bush alone. Stone the flamin' crows.  

### Yarn mode (harnessed)

> Right, so out on the edge of this whoppin' great stretch of bush, miles from the nearest servo, there lives a woodcutter, poor as a church mouse, with his missus and his two nippers. The young fella's called Hansel and the girl's Grethel. They've got sweet bugger-all to eat or drink at the best of times, and then a proper bad trot hits the whole district, a famine, and the poor bloke can't even scrape together the daily bread. So one night he's lyin' in bed chewin' it over, tossin' and turnin', and he lets out a big sigh and goes to his wife,  
>
> "What's gonna become of us, ay? We can't even feed the kids. There's nothin' left over for us."  
>
> "I'll tell ya what, husband," the wife goes. "First thing in the mornin' we take the littlies out into the bush, right where it's thickest. We light 'em a fire, give 'em a bit of bread each, then we nick off to work and leave 'em there. They'll never find their way home, and we'll be shot of 'em."  
>
> "Nah, wife," says the bloke. "I can't do that. I haven't got the ticker to drag me own kids out into the scrub and leave 'em on their own. The wild animals'd be on 'em in no time and scoff the lot."  
>
> "Oh, ya great boofhead," she goes, "then all four of us starve. Ya might as well start knockin' the coffins together." And she earbashes him day and night, never gives him a minute's peace, till the poor mug caves in and says yes.  
>
> "But I feel bloody awful for the poor little tackers," says the bloke. Bit late for the hand-wringin' now.  
>
> Now, the two kids are that starvin' they can't sleep a wink, and they've heard every word their step-mum's said to their old man. Grethel's bawlin' her eyes out, and she goes to Hansel,  
>
> "That's it. We're done for."  
>
> "Shush, Grethel," Hansel goes, "and don't you fret. I'll sort somethin' out." So once the oldies are snorin', he's up, pulls on his little coat, opens the back door and slips out. The moon's shinin' bright as anything, and all these white flints lyin' out the front of the house are glintin' like a pocketful of silver coins. Hansel crouches down and crams the little pocket of his coat till it won't take one more. Then back inside he goes and says to Grethel,  
>
> "Settle down, little sis, and go to sleep. God won't leave us in the lurch," and he hops back into bed. Cool as a cucumber, that kid.  
>
> Day's barely breakin', sun's not even up, when in comes the wife and shakes the pair of 'em awake.  
>
> "Up ya get, ya lazy little bludgers. We're goin' out the bush to cut wood."  
>
> Then she hands 'em a bit of bread each and goes,  
>
> "That's yer lunch, and don't you touch it before then, 'cause there's no more where that came from."  
>
> Grethel stuffs the bread under her apron, since Hansel's pockets are chockers with flints. Then off the whole lot of 'em go, out into the bush. They've only gone a little way when Hansel stops and looks back at the house, and he does it again, and again, and again, till his old fella pipes up,  
>
> "Hansel, what are ya gawkin' at? Watch ya don't forget yer legs, will ya?"  
>
> "Oh, Dad," Hansel goes, "I'm lookin' at me little white kitten. She's sittin' up on the roof wavin' me goodbye."  
>
> "Ya young nong," says the woman, "that's not yer kitten, that's the sun on the chimney-pot."  
>
> Course, Hansel's not lookin' at any kitten. Every few steps he's been fishin' a flint outta his pocket and droppin' it on the track. Clever little bugger.  
>
> When they get to the middle of the bush, the father tells the kids to gather up some wood for a fire to keep 'em warm, and Hansel and Grethel pile up enough brushwood for a little mountain. They light it, and once the flames are roarin' good and high, the wife goes,  
>
> "Now lie down by the fire and take a spell, you two, and we'll go and cut some wood. When we're done we'll come back and fetch ya."  
>
> So Hansel and Grethel sit by the fire, and come midday they each eat their bit of bread. They reckon their dad's out there in the bush the whole time, 'cause they keep hearin' the thwack of his axe. But nah, it's only a dry old branch hangin' off a dead gum, and the wind's knockin' it back and forth. Anyway, they sit there for yonks, till their eyelids get too heavy, and they go out like a light. When they finally wake up it's blacker than a dog's guts, and Grethel starts to cry and goes,  
>
> "How are we ever gonna get outta this bush?" But Hansel calms her down.  
>
> "Hang on a bit longer, till the moon comes up, and then we'll find our way home, easy."  
>
> And sure enough, when the full moon's up, Hansel grabs his little sister by the hand and follows the trail where the flints are shinin' like silver, showin' 'em the way. They walk the whole night through, and at sunup they fetch up at their dad's place. They knock on the door, and when the wife opens it and sees it's Hansel and Grethel standin' there, she goes,  
>
> "Ya naughty little buggers, what were ya doin' sleepin' that long out in the bush? We reckoned ya were never comin' home!"  
>
> Butter wouldn't melt in her mouth, would it? But the father's rapt, 'cause it'd fair broken his heart to leave the pair of 'em out there on their own.  

### Unharnessed

> Right, so get this. Out on the edge of this flamin' great stretch of bush there's this woodcutter bloke, flat broke, hasn't got a brass razoo, and he lives there with his missus and his two little tackers. The young fella's called Hansel and the girl's Grethel. Now they've got bugger-all to eat or drink at the best of times, and then a real shocker of a drought hits, the whole country's doin' it tough, and this poor bastard can't even scrape together the day's bread. So he's lyin' in bed one night chewin' it over, tossin' and turnin', and he lets out this big heavy sigh and says to the missus,  
>
> "Strewth, love, what's gonna become of us? We can't even feed the kids, and there's sweet f.a. left for us."  
>
> "Tell you what, mate," says the missus. "First thing in the mornin' we take the kids out into the bush, right out where it's thickest. We light 'em a fire, give 'em a bit of bread each, then we nick off to work and leave 'em to it. They'll never find their way home, not in a month of Sundays, and we'll be shot of 'em."  
>
> "Nah, love," says he, "fair go, I can't do that. I haven't got it in me to take me own kids out the bush and leave 'em there on their pat. The wild animals'd be into 'em before you could say knife."  
>
> "Oh, you great galah," says she, "then all four of us'll cark it. You might as well start knockin' up the coffins," -- and she was in his ear, naggin' like a blowfly at a barbie, and wouldn't give him a minute's peace till he caved.  
>
> "But I feel real crook about it for the poor little buggers," says the bloke.  
>
> Now the two kids hadn't got a wink of sleep, their bellies were rumblin' that bad, and they'd heard every word the stepmother said to their old man. Grethel's bawlin' her eyes out, and she says to Hansel,  
>
> "We're cactus."  
>
> "Pipe down, Grethel," says Hansel, "and don't get your knickers in a knot; I'll sort somethin' out." And once the olds have nodded off he gets up, chucks on his little coat, opens the back door and slips out. The moon's shinin' bright as, and the white flint stones lyin' out the front of the house are glintin' like bits of silver. Hansel bends down and stuffs his little coat pocket as full as it'll go. Then back inside he goes, and says to Grethel,  
>
> "She'll be right, little sis, go back to sleep. God won't leave us in the lurch," and he hops back into bed.  
>
> Next mornin', crack of sparrow's, before the sun's even up, the missus comes in and rousts the two kids, sayin',  
>
> "Up you get, ya lazy little sods; we're headin' out the bush to cut wood."  
>
> Then she hands 'em a bit of bread each and says,  
>
> "That's your lunch, and don't you go scoffin' it before then, 'cause there's no more where that came from."  
>
> Grethel carries the bread under her apron, since Hansel's pockets are chockers with the flints. Then off they all trot together for the bush. They've only gone a little way when Hansel stops and has a squiz back at the house, and he keeps doin' it, again and again, till his dad says to him,  
>
> "Oi, Hansel, what're you gawkin' at? Watch you don't forget your legs, mate."  
>
> "Aw, Dad," says Hansel, "I'm lookin' at me little white kitten, sittin' up on the roof sayin' hooroo to me."  
>
> "You young drongo," says the woman, "that's not your kitten, that's the sun on the chimney pot."  
>
> Course, Hansel wasn't lookin' at any kitten, was he? Every now and then he'd been fishin' a flint out of his pocket and droppin' it on the track.  
>
> So they get right into the guts of the bush and the old man tells the kids to grab some wood for a fire to keep 'em warm, and Hansel and Grethel rake up enough brush to make a little mountain of it. They put a match to it, and when the flames are goin' good and high the missus says,  
>
> "Righto, you kids, lie down by the fire and have a bit of a rest, and we'll go cut wood; and when we're done we'll come back and pick yous up."  
>
> So Hansel and Grethel sit by the fire, and come midday they each knock off their bit of bread. They reckon their old man's out in the scrub the whole time, 'cause they reckon they can hear the whack of the axe -- only it's not him, is it? It's just a dead branch hangin' off a clapped-out old tree, and the wind's knockin' it back and forth. So after they've been sittin' there for yonks, their eyelids get heavy, they're stuffed, and they drop off to sleep. When they finally come to it's dark as, and Grethel starts bawlin' and says,  
>
> "How are we ever gonna get outta this bush?" But Hansel settles her down, sayin',  
>
> "Hang on a tick, just till the moon's up, and then we'll find our way home, no worries."  
>
> And when the full moon came up Hansel took his little sister by the hand and followed the track where the flint stones were shinin' like silver and showin' 'em the road. They hoofed it the whole night through, and at sparrow's fart they rocked up at their old man's place. They bang on the door, and when the missus opens it and sees it's Hansel and Grethel she goes,  
>
> "You naughty little buggers, what'd you sleep so long out the bush for? We thought you were never comin' home!"  
>
> But the old man was stoked, 'cause it'd cut him up somethin' terrible to leave the pair of 'em out in the bush on their own.  

---

## The Raven (stanzas 1-6)

### Base (level 5)

> Crikey, once upon a midnight dreary, while I pondered, weak'n weary,  
> Over many a quaint and curious volume of forgotten lore,  
> While I nodded, nearly nappin', suddenly there came a tapping,  
> As of some one gently rappin', rapping at my chamber door.  
> "'T is some visiter," I muttered, "tappin' at me bloody chamber door--  
> Only this, and bugger all more, mate."  
>
> Ah, distinctly I remember it was in the bleak December,  
> And each separate carkin' it ember wrought its ghost upon the floor.  
> Eagerly I wished the morrow:--vainly I had sought to borrow  
> From my books surcease of sorrow--sorrow for the lost Lenore--  
> For the rare'n radiant maiden whom the angels name Lenore--  
> Nameless here for evermore.  
>
> Struth, and the silken sad uncertain rustling of each purple curtain  
> Thrilled me--filled me with ripper terrors never felt before;  
> So that now, to still the beating of my ticker, I stood repeating  
> "'T is some visiter entreatin' entrance at my chamber door  
> Some late visiter entreatin' entrance at my chamber door;--  
> This it's, and sweet bugger-all more."  
>
> Presently my soul grew stronger; hesitatin' then no longer,  
> "Sir," said I, "or Madam, truly yer forgiveness I implore;  
> But the fact is I was nappin', and so gently ya came rappin',  
> And so faintly ya came tappin', tappin' at me bloody chamber door,  
> That I scarce was sure I heard ya"--here I opened wide the door;--  
> Darkness there, and nothing more.  
>
> Deep into that darkness peerin', long I stood there wondering, fearing,  
> Doubting, dreaming dreams no mortal ever dared to dream before;  
> But the silence was unbroken, and the darkness gave no token,  
> And the only word there spoken was the whispered word, "Lenore!"  
> This I whispered, and an echo murmured back the word, "Lenore!"  
> Merely this and nothin' more.  
>
> Well, back into the chamber turning, all my soul within me burning,  
> Soon again I heard a tappin', somewhat louder than before.  
> "Jeez, Surely," said I, "surely that's somethin' at me window lattice;  
> Let me see, then, what thereat is, and this mystery explore--  
> Let me ticker be still a moment'n this mystery explore;--  
> 'T is the wind'n nothin' more!" Too easy.  

### Yarn mode (harnessed)

> Right, so it's midnight, dead of night and dreary as, and I'm sittin' up broodin', knackered and flat as a tack,  
> noggin buried in a stack of weird old books, the dusty sort full of stuff the whole world's forgotten.  
> And I'm noddin' off, right on the edge of a kip, when outta nowhere there's this tappin'.  
> Like someone's gently knockin', knock knock knock, on me bedroom door.  
> "Just some visitor," I mutter, "tappin' on me door, that's all.  
> That's it. Nothin' more to it."  
>
> Now, I remember it clear as day. It was a bleak December, and not the Aussie kind with the barbie goin' and the cricket on, the grim, freezin' northern kind.  
> And every last ember in the fire was carkin' it, one by one, throwin' its little ghost of a shadow across the floor.  
> I was hangin' out for the mornin'. I'd been tryin' to bury me sorrows in them books, and they were about as much help as a screen door on a submarine.  
> Sorrow for me Lenore, see. Lost her, didn't I.  
> A rare, radiant beaut of a girl, the angels call her Lenore up there,  
> but down here she's got no name at all, not ever again.  
>
> Then the curtains start up. Purple ones, silky, sad, rustlin' about all uncertain like,  
> and they fair put the wind up me, gave me the willies like nothin' I'd ever felt before.  
> Me ticker's goin' like the clappers, so to settle it I stand there sayin' it over and over:  
> "It's just some visitor wantin' in at me door.  
> Some late visitor, beggin' to be let in at me door.  
> That's all it is. Sweet bugger-all else."  
>
> Well, after a bit me nerve comes good, and I stop ditherin'.  
> "Sir," I go, "or Madam, look, I'm real sorry, hand on heart.  
> Fact is I was havin' a bit of a doze, and you knocked so soft,  
> and tapped so flamin' quiet on me door,  
> I was hardly sure I'd heard ya." And with that I fling the door wide open.  
> Dark out there. Blacker than a dog's guts. And that's the lot.  
>
> So I'm starin' deep into that dark, standin' there a fair while, wonderin', scared stiff,  
> doubtin' meself, dreamin' the kind of dreams no bugger alive ever had the guts to dream before.  
> But nothin' breaks the quiet. Not a bloody peep. The dark doesn't give us a single sign.  
> And the only word spoken, the whole time, is a whisper: "Lenore?"  
> That's me whisperin' it, and an echo murmurs it straight back: "Lenore."  
> Just that. Nothin' else, I reckon.  
>
> Back into the room I go, me insides burnin' up somethin' awful,  
> and before long there's that tappin' again, a fair bit louder this time.  
> "Righto," I go, "that's somethin' at me window, gotta be.  
> Let's have a squiz, then, see what's out there, sort this mystery out.  
> Settle down a sec, ticker, and let's get to the bottom of it.  
> It's only the wind, ya big sook. That's all it is. Just the bloody wind."  

### Unharnessed

> Righto, so it's midnight, dead-set dreary, and I'm cooked and flamin' weary,  
> Starin' at this stack of dusty old books chockers with forgotten lore,  
> Noddin' off, just about havin' a kip, when outta nowhere — tap-tap, tippin',  
> Like some bloke was softly knockin', knockin' at me chamber door.  
> "Aw, it's just some visitor," I mumbles, "knockin' at me chamber door —  
> That's all it is, and nothin' more."  
>
> Fair dinkum, I remember — bleak as buggery, December,  
> And every little dyin' ember chucked its ghost across the floor.  
> Couldn't wait for flamin' mornin' — I'd been tryin', no good, borrowin'  
> From me books a spell from sorrow — sorrow for me lost Lenore —  
> Ripper of a girl, she was, a stunner, angels call her Lenore —  
> Round here she's got no name, no more.  
>
> And the silky, sad, uncertain rustle of each purple curtain  
> Gave me the heebie-jeebies — frights like I'd never had before;  
> So to stop me ticker hammerin', I stood there, stammerin' and yammerin',  
> "It's some visitor, wants in, mate, knockin' at me chamber door —  
> Some late visitor, wants in, mate, knockin' at me chamber door; —  
> That's all it is, and nothin' more."  
>
> Then me guts got a bit stronger; didn't muck about no longer,  
> "Mate," I says, "or missus — sorry; I'm beggin' ya, don't get sore;  
> Thing is, I was havin' a kip, see, and you come knockin' soft as anythin',  
> So quiet, tappin', tappin', tappin' at me chamber door,  
> I was barely sure I heard ya" — and I flung wide open the door; —  
> Black as the inside of a dog out there, and nothin' more.  
>
> Into that darkness squintin', stood there yonks just wonderin', scared stiff,  
> Doubtin', dreamin' dreams no bloke had ever had the hide to dream before;  
> But the quiet never cracked, mate, and the dark gave bugger-all back, mate,  
> And the only word got spoken was a whisper — just "Lenore!"  
> I whispered that, and an echo mumbled back at me, "Lenore!"  
> Just that, and nothin' flamin' more.  
>
> Back inside the room I'm turnin', with me whole soul in me burnin',  
> Not long after, more tappin' — bit louder than before.  
> "Strewth," I says, "that's somethin', surely, rattlin' at me window lattice;  
> Let's have a squiz, then, what that is, and suss this mystery, for sure —  
> Let me ticker settle half a tick and suss this mystery, for sure; —  
> It's the wind, mate, nothin' more!"  

---

## The Boy Who Cried Wolf

### Base (level 5)

> Far out, a Shepherd's young fella was tendin' his flock near a village, and reckoned it would be ripper, grouse fun to hoax the villagers by pretendin' that a Wolf was attackin' the sheep: so he shouted out, "Wolf! wolf!" and when the punters came running up he paid out on them for their pains. He did this more than once, and every time the villagers found they had been hoaxed, for there was no Wolf at all. At last a Wolf flamin' did come, and the Boy cried, "Wolf, ay! wolf!" as loud as he could: but the battlers were so used to hearing him call that they took no notice of his cries for help. And so the Wolf had it all his own way, and killed off sheep after sheep at his leisure.  
>
> Ya can't reckon a bullshitter even when he tells the truth, no matter what some drongo reckons. Faaaaaark me.  

### Yarn mode (harnessed)

> Right, so there's this shepherd's young fella, barely out of short pants, mindin' a mob of jumbucks just out of town. Bored as, he is. And he reckons it'd be a ripper bit of fun to pull a swifty on the locals, make out a wolf's gettin' stuck into the sheep. So he cups his mitts and he goes, "Wolf! Wolf!" And the whole town comes peltin' up the paddock with shovels 'n pitchforks 'n whatever else they could grab, and what's the little bugger do? Stands there pissin' himself laughin'. Paid out on 'em somethin' shockin' for their trouble.  
>
> Well, he pulls that one more than once, doesn't he. And every time the poor battlers puff their way up the hill, they cotton on they've been had again. No wolf. Not a whisker of one.  
>
> Anyway, one arvo a wolf rocks up, fair dinkum this time, and the young fella's screamin' his lungs out, "Wolf! WOLF! Oi, I'm not muckin' about!" But the punters down the town have heard him carry on like a galah that many times they don't give two hoots. Nobody so much as looks up from their coldies.  
>
> So the wolf's got the place to himself, hasn't he, and he goes through them sheep one after the other, takin' his own sweet time about it, like a bloke workin' his way down the snags at a barbie. Cried wolf one too many times, the flamin' little dill.  
>
> And the moral? Ya can't believe a bullshitter even when he's tellin' the truth.  

### Unharnessed

> Righto, so there's this young fella, shepherd's kid, yeah, out mindin' a mob of sheep not far off from a little town. Bored stupid, he reckons it'd be a top laugh to have a lend of the locals, make out there's a wolf gettin' stuck into the sheep. (A wolf, mind you, not a dingo.) So he lets rip, "Wolf! Wolf!", and the whole town comes up the paddock flat out like a lizard drinkin', puffin' and blowin', and the little bugger just cacks himself laughin' at 'em for their trouble.  
>
> And he didn't just do it the once, either. Pulled the same stunt again, and again, and every flamin' time the poor buggers rocked up to find they'd been had. Not a wolf within cooee. Not a sniff of one.  
>
> Then, wouldn't ya know it, a wolf turns up, fair dinkum this time. And the kid's goin' off like a frog in a sock, screamin' "Wolf! Wolf!" loud as he bloody can. But the townies had heard him carry on that many times they didn't bat an eyelid. Couldn't give a rat's. Took no notice of him at all, no matter how hard he hollered for help.  
>
> So the wolf's got the whole joint to himself, hasn't he, and he just moseys through the mob knockin' off sheep after sheep, takin' his sweet time about it, no worries in the world.  
>
> Moral of the story, mate: you can't believe a bullshit artist, even when he's tellin' ya the dinkum truth.  

---

## The Declaration of Independence (opening)

### Base (level 5)

> When in the Course of human events, it becomes necessary for one battlers to dissolve the political bands which have connected them with another, and to assume, among the Powers of the earth, the separate'n equal station to which the Laws of Nature and of Nature's God entitle 'em, a decent respect to the opinions of mankind requires that they should declare the causes which impel 'em to the separation, no matter what some drongo reckons.  
>
> We hold these truths to be self-evident, that every bloke's as bloody good as the next, that they're endowed by their Creator with certain unalienable Rights, that among these are Life, a fair shake, and the pursuit of Happiness.--That to secure these rights, the pollies are instituted among blokes, deriving their just powers from the consent of the governed,--That whenever any Form of pollie becomes destructive of these ends, it's the Right of the punters to alter or to abolish it, and to institute brand-spankin'-new pollie, standin' about like stunned mullets, layin' its foundation on such principles'n organizin' its powers in such form, as to 'em will seem most likely to effect their Safety and Happiness, the lot. Prudence, indeed, will dictate that pollies long kicked off shouldn't be changed for light and transient causes; and accordingly all experience hath shown, that mankind are more disposed to suffer, while evils are sufferable, than to right themselves by abolishing the forms to which they're accustomed. But when a long train of abuses'n usurpations, pursuin' invariably the same Object evinces a design to reduce them under absolute Despotism, it's their right, it's their duty, to chuck off such pollie, and to provide brand-spankin'-new Guards for their future security.--Such's been the patient sufferance of these Colonies; and such is now the necessity which constrains them to alter their former Systems of pollie. Now, the history of the present King of Great Britain is a history of repeated injuries'n usurpations, all having in direct object the joint of an absolute Tyranny over these States. Bloody hell, to prove this, let Facts be submitted to a candid world. Bugger me bloody dead.  

### Yarn mode (harnessed)

> Right, so. Every now and then, the way things go in this world, one mob of people gets to the point where they've gotta cut the ties that've had 'em hitched to another mob, and stand up on their own two feet among the big nations of the earth, separate and every bit as good as the rest of 'em, which is what the laws of Nature and Nature's God reckon they've got comin' to 'em. And when ya do a thing like that, common decency says ya owe the rest of the world an explanation. Ya tell 'em why yer packin' up and leavin'. Fair enough, too.  
>
> Now, here's what we hold to be self-evident, stickin' out like a country dunny: that all men are created equal, every bloke's as good as the next. That their Creator's handed every one of 'em certain rights nobody can take off 'em, and among those are life, liberty, a fair shake, and the pursuit of happiness. That's the deal. And to keep those rights safe, blokes set up governments, the pollies, and a pollie only gets his say-so from the consent of the punters it's governin'. Nobody else's. So whenever any government starts wreckin' the very things it was put there to look after, the battlers have every right to change it or give it the flick altogether, and knock up a brand-spankin'-new one, built on whatever principles and run whatever way they reckon's most likely to keep 'em safe and happy.  
>
> Mind you, common sense says ya don't go turfin' out pollies who've been runnin' the show since it kicked off donkey's years back over some piddly little thing that'll be forgotten by next week. And fair dinkum, history shows people'll crack hardy and cop a fair bit while it's still bearable, sooner than fix things up by tearin' down the setup they're used to. Better the devil ya know, I s'pose.  
>
> But when there's a long bloody string of abuses and power grabs, one after the other, all headin' the same way, and it's plain as day the plan is to crush the lot of 'em under a tyrant's boot, then it's their right, it's their duty, to chuck that government out on its ear and put up new fences to keep 'em safe from here on in. And that's how these Colonies have copped it, patient as ya like. And that's why they've got no choice now but to change the way they've been governed.  
>
> Because the story of the current King of Great Britain, the greedy mongrel, is one injury and power grab after another, every flamin' one of 'em aimed straight at settin' himself up as an absolute tyrant over these States, lordin' it over the joint like he owns it. Don't believe us? Fair enough. Here's the facts, laid out for any honest bugger in the world to have a squiz at.  

### Unharnessed

> Right, so here's the thing. Every now and then in the whole long yarn of human history, one mob of people reckons it's time to cut the ties that've had 'em lashed to another mob, politically speakin', and to go off and take their own spot among the big players of the world. A separate spot, mind, and a fair-dinkum equal one, the kind the laws of nature and nature's God reckon they've got comin' to 'em. And if you're gonna pull a stunt like that, mate, common decency says you don't just piss off without a word. You owe the rest of the world a fair explanation of why you're packin' up and shootin' through.  
>
> Now, we reckon this lot's as plain as the nose on your face: that all men are created equal, fair go for everyone, and that their Maker's handed every one of 'em a few rights nobody can take off 'em, no way, no how. And right up the top of that list you've got life, you've got liberty, and you've got havin' a red-hot go at bein' happy. To keep those rights safe, people set up governments, and a government's only got any real say-so 'cause the folks it's runnin' have given it the nod. So whenever any government goes feral and starts wreckin' the very things it was set up to look after, the people've got every right to give it a good overhaul or chuck the whole bloody thing out, and knock up a new one, built on whatever principles and laid out whatever way looks to them like the best bet for keepin' 'em safe and happy. Now, fair's fair. Common sense says you don't go pullin' down a government that's been around for donkey's years over some piddly little thing that'll blow over by smoko. And truth be told, history shows people'd rather cop a fair bit of rough treatment, long as it's bearable, than go and sort it out by tearin' down the setup they're used to. She'll be right, they tell themselves. But when you get a long string of rorts and grabs at power, one after the other, all headin' the same flamin' direction, and it's clear as day somebody's angling to have you right under the thumb of a full-blown despot, well, then it's your right, it's your duty, to give that government the flick and put up some new fences to keep yourselves safe down the track. And that's just how long these Colonies have copped it on the chin, patient as you like; and that's why they've got Buckley's but to scrap the old way of runnin' things. The present King of Great Britain? Strewth. His record's one long list of dirty tricks and power grabs, over and over, and every last one of 'em aimed at the one thing: makin' himself the out-and-out tyrant over these States. And don't just take our word for it, either. Here's the facts, laid out for any fair-minded bugger on the planet to have a squiz at.  
