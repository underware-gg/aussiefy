# Five retellings, three ways (2026-10-11)

Each text, at level 5:
1. **Base**: the deterministic engine (`aussiefy translate --level 5 --seed 0`), no model in the loop.
2. **Yarn mode (harnessed)**: an agent writing under the yarn-mode system prompt, with the `lookup_slang`, `check_draft` and `submit_yarn` tools (via `yarn_tools.py`, since this container has no API key). Every draft passed validation: LRRH and P&P on the second submit, the others on the first. The tool calls are logged in `harnessed/*.log.jsonl`.
3. **Unharnessed**: an agent told only to retell the text in broad Aussie drawl. It had no dictionary and no tools.

The originals are in `tests/corpus/reference/`. The phrases the unharnessed agents used and the dictionary lacks are in `new_phrases.yaml` (255 candidates, **unverified**).

## What stands out

**Base mode** has the vocabulary but not the voice. It swaps words in place and sprinkles on garnish, so the original syntax stays. It also shows these engine bugs:
- **Honorifics break sentences.** "Mr. Bennet" is split at the full stop, which gives "Mr. Well, Bennet replied" and "Mr, cobber. Bennet made no answer".
- **Intensifiers land in the wrong place:** "give me bloody that straw", "let me bloody come in", "me bloody dear".
- **The wrong sense is swapped in:** "build" becomes *kick off*, "lived" becomes *keep on kickin'*, "thought" (a noun) becomes *reckoned* ("the pale cast of reckoned"), "great pith" becomes *grouse pith*, and "a good mind to" becomes *bonzer*.
- **The fallback matches on spelling, not meaning**, which gives opposites: "discontented" becomes *snug as a bug in a rug* and "less" becomes *rotten*.
- **Plurals are lost:** soldiers become *digger*, men become *bloke*, children become *littlie*.
- **Register is ignored:** "Fuck me dead." closes Hamlet's soliloquy, and LRRH opens "Fair fuckin' dinkum, once upon a bloody time".

**Yarn mode** reads as a real retelling. The tools keep it on dictionary slang and catch problems (one draft in five needed a second pass). The flaw is the rule that keeps 60% of the planned phrases: it drags the engine's wrong-sense picks into the yarn. The lint also had two false positives, which are now fixed. Gated general-English entries made "dear" and "fella" count as flagged, and the over-broad variants "how good?" and "sparrow's" inflated the "repeated" count.

**Since then:** yarn mode's LRRH has "thought the sun shone out of her", which clips the idiom. The full form is "...out of her arse". The dictionary had no entry for it, so the agent improvised the phrase and trimmed it. It's now an entry (`sun-shines-out-of-arse`, under a new concept ADORE: dote on, adore, idolise, worship, think the world of). Its new `{objposs}` slot gives "her", "his", "yer" or "Mary's", and the second verb follows the tense ("thinks the sun shines", "thought the sun shone"). Base mode's LRRH now reads "her grandmother thought the sun shone outta her arse still more". The yarn above is left as it was produced.

Also fixed since: the full stop after an honorific ("Mr. Bennet") no longer ends a sentence, and the possessive "bloody" infix no longer fires after an object pronoun ("give me that straw", "let me come in"). The base outputs below are as they were produced, before these fixes.

**Unharnessed** retellings are the most natural and the most inventive. They restructure sentences, add asides ("Yeah, I know. Bear with me.") and reach well past the dictionary: *cop it sweet*, *couldn't be buggered*, *done up like a pox doctor's clerk*, *hump the swag*, *gutless wonders*, *does yer head in*, *nick over*, *clobber*. They also drift more from the source and occasionally go cruder than it calls for ("shone out of her arse"). They are a good source of candidates, not ground truth: everything in `new_phrases.yaml` goes to the verifier next round.


---

## Little Red Riding Hood

### Base (level 5)

> Fair fuckin' dinkum, once upon a bloody time there lived in a certain village a little country girl, the prettiest creature was ever seen. Her mother was excessively fond of her; and her grandmother doted on her still more. Mate, this beaut sheila had made for her a little red ridin'-hood; which became the girl so bloody well that every man'n his dog called her Little Red Ridin'-Hood.  
>
> One day her mother, havin' made some custards, said to her:  
>
> “Go, me dear, and see how thy grandmamma does, for I hear she's been crook; carry her a custard, and this little pot of butter, mate.”  
>
> Little Red Riding-Hood set out immediately to go to her bloody grandmother, who lived in another village.  
>
> Fuckin' hell, as she was going through the wood, she met with Gaffer Wolf, who had a properly bonzer mind to eat her up, but he dared not, 'cause of some faggot-makers bloody hard by in the bush. Anyway, he asked her whither she was going. Crikey, the poor littlie, who didn't know that it was dangerous to stay and hear a wolf talk, said to him:  
>
> “I'm gonna see me grandmamma'n carry her a custard and a little pot of butter from me bloody mamma.”  
>
> “Does she live far off?” said the Wolf.  
>
> “Oh! ay,” answered Little Red Riding-Hood; “it's beyond that mill ya see there, at the first house in the village, ya drongo.”  
>
> “Well,” said the Wolf, “and I’ll go'n see her too. I’ll go this way'n ya go that, and we'll see who will be there soonest.”  
>
> The Wolf began to run flat chat, takin' the nearest way, and the little girl went by that farthest about, diverting herself in gathering nuts, running after butterflies, and makin' nosegays of such little flowers as she met with. The Wolf wasn't long before he got to the old sheila’s house. Well, he knocked at the door--tap, tap.  
>
> “Who’s there, ya galah?”  
>
> “Yer grandchild, Little Red Ridin'-Hood,” replied the Wolf, counterfeiting her voice; “who has brought ya a custard'n a little pot of butter sent ya by mamma.”  
>
> The beaut grandmother, who was in bed, 'cause she was somewhat ill, cried out:  
>
> “Pull the bobbin, and the latch will go up.”  
>
> The Wolf pulled the bobbin, and the door opened, and then presently he fell upon the beaut sheila and ate her up in a moment, for it was above three days that he hadn't touched a bit. He then shut the door'n went into the grandmother’s bed, reckoning Little Red Riding-Hood, who came some time afterward'n knocked at the door--tap, tap.  
>
> “Who’s there?”  
>
> Little Red Ridin'-Hood, hearin' the big voice of the Wolf, was at first afraid; but reckonin' her grandmother had got a cold and was hoarse, answered:  
>
> “‘Tis yer bloody grandchild, Little Red Riding-Hood, who has brought ya a custard and a little pot of butter mamma sends ya.”  
>
> The Wolf cried out to her, softenin' his voice as much as he could:  
>
> “Pull the bobbin, and the latch will go up.”  
>
> Little Red Ridin'-Hood pulled the bobbin, and the door opened.  
>
> The Wolf, seeing her come in, said to her, hidin' himself under the bed-clothes:  
>
> “Put the custard and the little pot of butter upon the stool, and come and lie down with me.”  
>
> Little Red Riding-Hood undressed herself'n went into bed, where, being greatly amazed to see how her grandmother looked in her night-clothes, she said to her:  
>
> “Grandmamma, what grouse arms you've got!”  
>
> “That's the better to hug thee, me dear.”  
>
> “Grandmamma, what ripper legs you've got!”  
>
> “That's to run the better, my bloody nipper.”  
>
> “Grandmamma, what grouse ears you've got!”  
>
> “That's to hear the better, my little tacker.”  
>
> “Grandmamma, what ripper eyes you've got!”  
>
> “It's to see the better, my ankle biter.”  
>
> “Grandmamma, what beaut teeth you've got!”  
>
> “That's to eat thee up.”  
>
> And, saying these words, this wicked wolf fell upon Little Red Riding-Hood, and ate her all up. Streeeeeewth.  

### Yarn mode (harnessed)

> Right, so once upon a time, out in some little country town, there's this little girl, the prettiest, most ripper little thing anyone had ever laid eyes on. Her mum was mad about her, and her nan was even worse, thought the sun shone out of her. Now, the old sheila had sewn her a little red riding-hood, and it suited the little ankle biter so bloody well that every man and his dog started callin' her Little Red Riding-Hood.  
>
> Anyway, one day her mum's whipped up a batch of beaut custards, and she goes to her:  
>
> "Off ya go, love, and see how yer nan's goin', 'cause I hear she's been crook as a dog. Take her a custard, and this bonzer little pot of butter, will ya?"  
>
> So Little Red Riding-Hood's out the door straight away, headin' for her nan's, which was over in the next town.  
>
> Well, it's a grouse sort of a day and she's traipsin' through the bush, miles from the nearest servo, when who should she run into but Gaffer Wolf. Now, this mongrel was dyin' to scoff her on the spot, but he didn't have the guts, 'cause there were some blokes choppin' firewood just over the way. So he asks her where she's off to. And the poor littlie, who had no idea it's a dodgy caper to stop and have a yarn with a wolf, goes to him:  
>
> "I'm off to see me nan and take her a custard and a little pot of butter from me mum."  
>
> "She live far off?" goes the Wolf.  
>
> "Oh, yeah, a fair way," says Little Red Riding-Hood. "It's past that mill over there, ya see it? First house in the town."  
>
> "Well," goes the Wolf, "reckon I'll go and see her too. I'll go this way and you go that, and we'll see who gets there first, ay?"  
>
> And the Wolf's off flat chat, takin' the shortest way, while the little girl goes the long way round, muckin' around pickin' nuts, chasin' butterflies and makin' little posies outta whatever flowers she comes across. Didn't take the Wolf long to get to the old sheila's place. He knocks on the door. Tap, tap.  
>
> "Who's that?"  
>
> "It's yer grandkid, Little Red Riding-Hood," says the Wolf, puttin' on her voice, the sneaky bugger. "I've brought ya a custard and a little pot of butter, from Mum."  
>
> Now, her nan, who was in bed 'cause she was a bit crook, sings out:  
>
> "Pull the bobbin, love, and the latch'll go up."  
>
> So the Wolf pulls the bobbin, the door swings open, and next thing ya know he's jumped on the poor old thing and polished her off in about two seconds flat, 'cause he hadn't had a bite of tucker in over three days. Properly starvin', he was. Then he shuts the door, hops into her bed and waits for Little Red Riding-Hood, who rocks up a bit later and knocks on the door. Tap, tap.  
>
> "Who's that?"  
>
> Little Red Riding-Hood hears this big gruff voice and gets a bit spooked at first, but reckonin' her nan's just got a cold and her voice has gone, she answers:  
>
> "It's yer grandkid, Little Red Riding-Hood. I've brought ya a custard and a little pot of butter, from Mum."  
>
> And the Wolf sings out to her, puttin' on the softest voice he can manage:  
>
> "Pull the bobbin, love, and the latch'll go up."  
>
> So Little Red Riding-Hood pulls the bobbin, and the door swings open.  
>
> The Wolf sees her come in, and hidin' himself under the blankets, he goes:  
>
> "Chuck the custard and the little pot of butter on the stool, and come hop in with me, will ya?"  
>
> So Little Red Riding-Hood gets her gear off and climbs into bed, and she's gobsmacked at what her nan looks like in her nightie. And she goes:  
>
> "Nan, what big arms ya got!"  
>
> "All the better to hug ya with, love."  
>
> "Nan, what big legs ya got!"  
>
> "All the better to run with, me little nipper."  
>
> "Nan, what big ears ya got!"  
>
> "All the better to hear ya with, me little tacker."  
>
> "Nan, what big eyes ya got!"  
>
> "All the better to see ya with, me little ankle biter."  
>
> "Nan, what big teeth ya got!"  
>
> "All the better to eat ya up!"  
>
> And with that, the wicked flamin' wolf jumps on Little Red Riding-Hood and gobbles her up, the whole box and dice. Gawd help us.  

### Unharnessed

> Right, so there's this little country sheila, yeah, livin' out in some little town in the back of beyond, and fair dinkum, she was the prettiest little thing anyone'd ever laid eyes on. Her mum was bloody mad about her, and her nan was even worse, thought the sun shone out of her arse. Anyway, the old girl knocks her up this little red ridin' hood, and it suited the kid down to the ground, so everyone just started callin' her Little Red Ridin' Hood. Stuck, it did.  
>
> So one day her mum's whipped up a few custards, and she goes to the kid:  
>
> "Righto, love, nick over and see how yer nan's goin', 'cause I reckon she's been real crook. Take her one of these custards, and this little pot of butter while ya at it."  
>
> So Little Red Ridin' Hood shoots through straight away to see her nan, who lived over in the next town.  
>
> Now she's goin' through the bush, see, and who does she run into but the old Wolf. And this mongrel's thinkin' he'd love to wolf her down then and there, but he hasn't got the guts, 'cause there's a mob of blokes choppin' wood just up the track. So he asks her where she's off to. And the poor little bugger, she's got no idea it's dodgy to stand around yakkin' with a wolf, so she tells him straight:  
>
> "I'm goin' to see me nan, and I'm takin' her a custard and a little pot of butter from me mum."  
>
> "She live far, does she?" goes the Wolf.  
>
> "Oh, yeah, a fair hike," says Little Red Ridin' Hood. "She's out past that mill over there, first house ya come to in the town."  
>
> "Well, too right," says the Wolf, "I might go and say g'day to her meself. Tell ya what, I'll go this way, you go that way, and we'll see who gets there first."  
>
> So the Wolf goes like the clappers, takin' the short cut, and the kid goes the long way round, mucking about pickin' nuts, chasin' butterflies and makin' little posies outta whatever flowers she came across. Didn't take the Wolf long at all to rock up at the old girl's place. He gives the door a knock, tap, tap.  
>
> "Who's that?"  
>
> "It's yer granddaughter, Little Red Ridin' Hood," says the Wolf, puttin' on her voice, cheeky bugger. "I've brought ya a custard and a little pot of butter Mum sent."  
>
> Now the nan, who's crook in bed, sings out:  
>
> "Pull the bobbin, love, and the latch'll go up."  
>
> So the Wolf pulls the bobbin, the door opens, and quick as ya like he's into the old girl and scoffed her down in about two seconds flat, 'cause he hadn't had a feed in over three days. Then he shuts the door and hops into Nan's bed, waitin' for Little Red Ridin' Hood, who rocks up a bit later and gives the door a knock, tap, tap.  
>
> "Who's that?"  
>
> Now Little Red Ridin' Hood hears this big gruff voice and she's a bit spooked at first, but then she reckons Nan's just got a cold and she's gone a bit hoarse, so she sings out:  
>
> "It's yer granddaughter, Little Red Ridin' Hood, and I've brought ya a custard and a little pot of butter Mum sent."  
>
> And the Wolf calls out, puttin' on the softest voice he can manage:  
>
> "Pull the bobbin, love, and the latch'll go up."  
>
> So Little Red Ridin' Hood pulls the bobbin and the door opens.  
>
> The Wolf sees her come in and says to her, hidin' under the blankets:  
>
> "Chuck the custard and the little pot of butter on the stool there, and come and hop in with me."  
>
> So Little Red Ridin' Hood gets her gear off and hops into bed, and she's gobsmacked at how Nan looks in her nightie, so she goes:  
>
> "Strewth, Nan, what big arms ya've got!"  
>
> "All the better to give ya a cuddle, love."  
>
> "Nan, what big legs ya've got!"  
>
> "All the better to run with, darl."  
>
> "Nan, what big ears ya've got!"  
>
> "All the better to hear with, darl."  
>
> "Nan, what big eyes ya've got!"  
>
> "All the better to see with, darl."  
>
> "Nan, what bloody big teeth ya've got!"  
>
> "All the better to eat ya up with."  
>
> And soon as he says it, the dirty rotten mongrel jumps on Little Red Ridin' Hood and gobbles her up, the whole bloody lot. And that's the end of that, mate. Bugger all ya can do about it.  

---

## The Three Little Pigs

### Base (level 5)

> Once upon a bloody time when pigs spoke rhyme  
> And monkeys chewed tobacco,  
> And hens took snuff to make them tough,  
> And ducks went quack, quack, quack, O!  
>
> Anyway, there was an old sow with three little pigs, and as she hadn't enough to keep 'em, she sent 'em out to seek their fortune. Bloody hell, the first that went off met a bloke with a bundle of straw, and said to him:  
>
> “Please, bloke, give me bloody that straw to kick off me a house.”  
>
> Which the bloke did, and the little pig knocked together a house with it. Presently came along a wolf, and knocked at the door, and said:  
>
> “Little pig, little pig, let me bloody come in.”  
>
> To which the pig answered:  
>
> “No, nah, nah, by the hair of me chiny chin chin.”  
>
> The wolf then answered to that:  
>
> “Then I'll huff, and I'll puff, and I'll blow yer house in.”  
>
> So he huffed, and he puffed, and he blew his house in, and scoffed the little pig.  
>
> The second little pig met a bloke with a bundle of furze, and said:  
>
> “Please, bloke, give me that furze to knock together a house, ya know.”  
>
> Which the bloke did, and the pig kicked off his house. Then along came the wolf, and said:  
>
> “Little pig, little pig, let me bloody come in.”  
>
> “No, yeah, nah, by the hair of me chiny chin chin.”  
>
> “Then I'll puff, and I'll huff, and I'll blow yer house in.”  
>
> So he huffed, and he puffed, and he puffed, and he huffed, and at last he blew the house down, and he scoffed the little pig.  
>
> Fuckin' hell, the third little pig met a bloke with a load of bricks, and said:  
>
> “Please, bloke, give me those bricks to kick off a house with.”  
>
> So the bloke gave him the bricks, and he kicked off his house with 'em. So the wolf came, as he did to the other little pigs, and said:  
>
> “Little pig, little pig, let me come in.”  
>
> “No, yeah, but nah, by the hair of me chiny chin chin.”  
>
> “Then I'll huff, and I'll puff, and I'll blow yer house in.”  
>
> Well, he huffed, and he puffed, and he huffed'n he puffed, and he puffed and huffed; but he couldn't get the house down. Aw, when he found that he couldn't, with all his huffin''n puffing, blow the house down, he said:  
>
> “Little pig, I know where there's a beaut paddock of turnips.”  
>
> “Where?” said the little pig.  
>
> “Oh, in Mr. Smith's Home-field, and if you'll be ready tomorrow morning I'll call for ya, and we'll go together, and get some for tea.”  
>
> “Dead well,” said the little pig, “I'll be ready, mate. What time do ya mean to go?”  
>
> “Oh, at six o'clock.”  
>
> Well, the little pig got up at five, and got the turnips before the wolf came (which he did about six) and who said:  
>
> “Little Pig, are ya ready?”  
>
> The little pig said: “Ready! I've been and come back again, and got a beaut potful for tea.”  
>
> The wolf felt spewin' at this, but reckoned that he would be up to the little pig somehow or other, so he said:  
>
> “Little pig, I know where there's a beaut apple-tree.”  
>
> “Where?” said the pig, ya galah.  
>
> “Down at Merry-garden,” replied the wolf, “and if ya won't deceive me I'll come for ya, at five o'clock tomorrow'n get some apples.”  
>
> Well, the little pig bustled up the next morning at four o'clock, and went off for the apples, hoping to get back before the wolf came; but he had further to go, and had to climb the tree, so that just as he was coming down from it, he saw the wolf comin', which, as ya may reckon, spooked him heaps. When the wolf came up he said:  
>
> “Little pig, what! are ya here before me? Buggered if I know. Are they beaut apples?”  
>
> “Yes, very,” said the little pig. “I'll chuck ya down one.”  
>
> And he chucked it so far, that, while the wolf was gone to pick it up, the little pig jumped down'n ran home. The next day the wolf came again, and said to the little pig:  
>
> “Little pig, there's a fair at Shanklin this arvo, will ya go?”  
>
> “Oh yes,” said the pig, “I'll go; what time will ya be ready?”  
>
> “At three,” said the wolf. So the little pig went off before the time as usual, and got to the fair, and bought a butter-churn, which he was going home with, when he saw the wolf coming. Then he couldn't tell what to do. So he got into the churn to hide, and by so doing turned it round, and it rolled down the hill with the pig in it, which spooked the wolf so much, that he ran home without going to the fair. So anyway, he went to the little pig's house, and told him how spooked he had been by a grouse round thing which came down the hill past him. Then the little pig said:  
>
> “Hah, I spooked ya, then. I had been to the fair'n bought a butter-churn, and when I saw ya, I got into it, and rolled down the hill.”  
>
> Then the wolf was filthy indeed, and declared he would scoff the little pig, and that he would get down the chimney after him. When the little pig saw what he was about, he hung on the pot full of water, and made up a blazing fire, and, just as the wolf was comin' down, took off the cover, and in fell the wolf; so the little pig put on the cover again in an instant, boiled him up, and ate him for tea, and kept on kickin' happy ever afterwards. Stone the flamin' crows.  

### Yarn mode (harnessed)

> Once upon a time, when pigs talked in rhyme,  
> And monkeys chewed tobacco,  
> And chooks took snuff to make 'em tough,  
> And ducks went quack, quack, quack, O!  
>
> Right, so there's this old sow with three little piglets, and she's on struggle street, hasn't got a brass razoo to feed the lot of 'em. So she boots 'em out the door to go and make their own way in the world. Tough love, I s'pose.  
>
> Well, the first little pig nicks off down the road and runs into a bloke luggin' a bundle of straw, and he goes:  
>
> "Please, mister, give us that straw so I can knock together a house, will ya?"  
>
> And the bloke hands it over, no worries, and the little pig throws up a house out of it. Straw! Not exactly built to last, is it? Anyway, before long along comes a wolf, bangs on the door, and goes:  
>
> "Little pig, little pig, let me come in."  
>
> And the pig sings out:  
>
> "Nah, nah, not by the hair of me chinny chin chin."  
>
> So the wolf comes back at him:  
>
> "Then I'll huff, and I'll puff, and I'll blow yer house in."  
>
> And he huffed, and he puffed, and he blew the flamin' house in, and scoffed the little pig whole. Gone. Not even a trotter left.  
>
> Now, the second little pig runs into a bloke with a bundle of furze, that prickly gorse stuff, and he goes:  
>
> "Please, mister, give us that furze so I can build a house."  
>
> The bloke hands it over, and the pig knocks his house together. Then along comes the wolf again, and goes:  
>
> "Little pig, little pig, let me come in."  
>
> "Nah, nah, not by the hair of me chinny chin chin."  
>
> "Then I'll puff, and I'll huff, and I'll blow yer house in."  
>
> So he huffed, and he puffed, and he puffed, and he huffed, and in the end he blew the whole bloody thing down and scoffed that little pig too. Two down. Gawd help us.  
>
> Well, the third little pig, he's the smart one. He runs into a bloke with a ute-load of bricks, and goes:  
>
> "Please, mister, give us them bricks so I can build a house with 'em."  
>
> So the bloke gives him the bricks, and he builds himself a proper house, built like a brick shithouse. And sure enough the wolf turns up, same as he did with the other two, and goes:  
>
> "Little pig, little pig, let me come in."  
>
> "Nah, nah, not by the hair of me chinny chin chin."  
>
> "Then I'll huff, and I'll puff, and I'll blow yer house in."  
>
> Well, he huffed, and he puffed, and he huffed and he puffed, and he puffed and he huffed, till he was red in the face and blowin' like a busted bellows, but he couldn't shift that house an inch. Bricks, ya see. So when he figured all his huffin' and puffin' was gettin' him nowhere, he tries a different tack:  
>
> "Little pig, I know where there's a beaut paddock of turnips."  
>
> "Where?" goes the little pig.  
>
> "Oh, down in Mr. Smith's Home-field. If you're ready tomorrow mornin' I'll swing by for ya, and we'll head over together and grab some for tea."  
>
> "Righto," says the little pig, "I'll be ready. What time d'ya reckon on goin'?"  
>
> "Oh, six o'clock."  
>
> Well, the little pig's up at five, nicks over to the paddock, and has the turnips home before the wolf rocks up (which he did, round six), and the wolf goes:  
>
> "Little pig, ya ready?"  
>
> And the pig goes, "Ready? Mate, I've been and come back already, and I've got a beaut potful on for tea."  
>
> Well, the wolf was ropeable, but he reckoned he'd get one over on this little pig somehow or other, so he goes:  
>
> "Little pig, I know where there's a ripper of an apple tree."  
>
> "Where?" goes the pig.  
>
> "Down at Merry-garden," says the wolf, "and if ya don't pull a swifty on me, I'll come round for ya at five tomorrow and we'll grab some apples."  
>
> Well, the little pig's up at sparrow's fart, four o'clock, and shoots through for the apples, hopin' to be home before the wolf turns up. Trouble is, it's a fair hike, and he's got to climb the bloody tree as well, so just as he's comin' down he spots the wolf headin' his way, and, as you can imagine, he's scared stiff. Up rocks the wolf, and goes:  
>
> "Little pig, what! You here before me, are ya? Are they any good, them apples?"  
>
> "Yeah, beauts," says the little pig. "I'll chuck ya one down."  
>
> And he chucks it so flamin' far that while the wolf's off chasin' after it, the little pig jumps down and legs it home like a rat up a drainpipe. Cheeky little bugger.  
>
> Next day the wolf's back again, and he goes to the little pig:  
>
> "Little pig, there's a fair on at Shanklin this arvo. Ya comin'?"  
>
> "Oh, yeah," says the pig, "I'll come. What time'll ya be ready?"  
>
> "Three," says the wolf. So the little pig heads off ahead of time, same as always, gets to the fair, and buys himself a butter-churn, and he's luggin' it home when he spots the wolf comin'. Now he doesn't know what to do. So he hops in the churn to hide, and doin' that tips it over, and it goes rollin' down the hill with the pig inside, and it spooks the wolf so bad he bolts home without even gettin' to the fair. So the wolf goes round to the little pig's place and tells him how he got the fright of his life from this great big round thing that came barrellin' down the hill at him. And the little pig goes:  
>
> "Hah! That was me, ya big sook. I'd been to the fair and bought a butter-churn, and when I saw ya, I hopped in it and rolled down the hill."  
>
> Well, then the wolf was spittin' chips, and he swore blind he'd make a feed of the little pig, and he'd come down the chimney to get him. When the little pig twigged what he was up to, he hung the pot full of water over the fire and got a roarin' fire goin', and just as the wolf was comin' down the chimney he whips the lid off, and in drops the wolf, plop. And quick as a flash the little pig slaps the lid back on, boils him up, and has him for tea. And he lived happy as Larry ever after. Serves the mongrel right.  

### Unharnessed

> Right, so this one goes back a fair way. Back when pigs talked in rhyme, and monkeys chewed baccy, and hens took snuff to toughen 'emselves up, and ducks went quack, quack, quack, O! Yeah, I know. Bear with me.  
>
> So there's this old sow, yeah, with three little pigs, and she's stony broke, can't afford to feed the lot of 'em, so she boots 'em out to go and make their own way in the world. Fair enough.  
>
> First one heads off and runs into a bloke luggin' a bundle of straw, and the little fella goes, "'Scuse me, mate, any chance I could have that straw to build meself a house?"  
>
> Bloke hands it over, no worries, and the pig knocks himself up a little straw joint. Next thing ya know, along comes this wolf, bangs on the door and goes, "Little pig, little pig, let us in."  
>
> And the pig goes, "No bloody way, not by the hair on me chinny chin chin."  
>
> Wolf goes, "Righto then. I'll huff, and I'll puff, and I'll blow yer house in."  
>
> And fair dinkum, he huffs, and he puffs, and he blows the bloody thing in, and then he scoffs the little pig. Gone. Cactus.  
>
> Now the second little pig, he runs into a bloke with a bundle of furze, gorse, that prickly stuff. "'Scuse me, mate, give us that gorse so I can build a house?"  
>
> Bloke does, and the pig throws his place together. Then, you'll never guess, along rocks the wolf. "Little pig, little pig, let us in."  
>
> "No bloody way, not by the hair on me chinny chin chin."  
>
> "Then I'll puff, and I'll huff, and I'll blow yer house in."  
>
> So he huffs and he puffs, and he puffs and he huffs, and in the end the whole lot comes down, and he wolfs down pig number two an' all. Two from two.  
>
> Third little pig, though, he's got a bit more nous. He runs into a bloke with a load of bricks. "'Scuse me, mate, give us them bricks so I can build a house with 'em?"  
>
> So the bloke hands 'em over and the pig builds himself a proper brick house. Solid as. Then the wolf turns up, same as he did with the other two. "Little pig, little pig, let us in."  
>
> "Not on yer life, not by the hair on me chinny chin chin."  
>
> "Then I'll huff, and I'll puff, and I'll blow yer house in."  
>
> Well, he huffs, and he puffs, and he huffs and he puffs, and he puffs and he huffs, till he's blue in the face, but he can't shift the bugger. Won't budge. When he works out all that huffin' and puffin' is gettin' him nowhere, he changes tack. "Little pig, I know where there's a beaut paddock of turnips."  
>
> "Yeah? Where?" says the pig.  
>
> "Over at Mr Smith's Home-field. If you're ready first thing tomorrow I'll come round and pick ya up, and we'll head over together and grab a few for tea."  
>
> "Too easy," says the pig. "I'll be ready. What time ya thinkin'?"  
>
> "Oh, six o'clock."  
>
> Well, the pig's up at sparrow's fart, five o'clock, nicks off to the paddock, gets the turnips, and he's home before the wolf rocks up round six. "Little pig, ya ready?"  
>
> "Ready? Mate, I've been and come back already, and got a whole potful for tea."  
>
> Now the wolf's spewin', absolutely ropable, but he reckons he'll get one over on the pig one way or another, so he goes, "Little pig, I know where there's a beaut apple tree."  
>
> "Where?" says the pig.  
>
> "Down at Merry-garden," says the wolf, "and if ya don't pull a swifty on me, I'll come get ya at five tomorrow and we'll grab some apples."  
>
> So the pig's up at four the next mornin' and shoots off for the apples, hopin' to be back before the wolf shows. But it's a fair hike, and he's gotta climb the tree, and just as he's comin' down he spots the wolf headin' his way. Well, as you'd imagine, he nearly shits himself. Wolf comes up and goes, "Little pig! What, you beat me here? They any good, them apples?"  
>
> "Yeah, bloody beauty," says the pig. "I'll chuck ya one down."  
>
> And he hoicks it that far that while the wolf's off chasin' it, the pig jumps down and pisses off home.  
>
> Next day the wolf's back again. "Little pig, there's a fair on at Shanklin this arvo. You keen?"  
>
> "Oh yeah, I'm in," says the pig. "What time are ya headin' off?"  
>
> "Three," says the wolf. So, same as always, the pig nicks off early, gets to the fair, and buys himself a butter churn. He's luggin' it home when, strike me pink, he spots the wolf comin'. And he doesn't know what to do with himself. So he hops in the churn to hide, and doin' that he tips it over, and it goes rollin' down the hill with him inside it, and that puts the wind up the wolf so bad he bolts home and never even gets to the fair.  
>
> Then he heads round to the pig's place and tells him how he got the fright of his life from this big round thing that come flyin' down the hill past him. And the pig goes, "Hah! That was me, ya galah. I'd been to the fair and bought a butter churn, and when I saw ya I hopped in and rolled down the hill."  
>
> Well, now the wolf's absolutely filthy. He says he's gonna eat the little pig, and he'll come down the chimney to get him an' all. When the pig sees what he's up to, he hangs the pot on full of water, gets the fire roarin', and just as the wolf's comin' down he whips the lid off, and in drops the wolf. Pig slaps the lid back on quick smart, boils him up, and has him for tea. And he lived happy ever after.  
>
> Wolf for tea. Can't say the bugger didn't have it comin'.  

---

## The Emperor's New Clothes

### Base (level 5)

> Many, yonks ago lived an emperor, who reckoned so much of brand-spankin'-new clothes that he spent all his dosh in order to obtain them; his only ambition was to be always well dressed. He didn't care for his diggers, and the theatre didn't amuse him; the only thing, in fact, he thought anything of was to drive out'n show a brand-spankin'-new suit of clothes. He had a coat for every hour of the day; and as one would say of a king "He's in his cabinet," so one could say of him, "The emperor is in his dressin'-room, ay."  
>
> The beaut city where he resided was bloody gay; every day many strangers from all parts of the globe rocked up. Well, one day two swindlers came to this city; they made punters reckon that they were weavers, and declared they could manufacture the finest cloth to be imagined. Their colours and patterns, they said, weren't only exceptionally bloody beautiful, but the clothes made of their material possessed the ripper quality of being invisible to any bloke who was unfit for his office or unpardonably stupid.  
>
> "Well, bugger me, that must be grouse cloth," reckoned the emperor. "If I were to be dressed in a suit made of this cloth I should be able to find out which blokes in me empire were unfit for their places, and I could distinguish the clever from the bloody stupid. Mind ya, I must have this cloth woven for me without delay." And he gave a large sum of dosh to the swindlers, in advance, that they should set to work without any loss of time. They set up two looms, and pretended to be properly hard at work, but they did bugger all whatever on the looms. They asked for the finest silk'n the most precious gold-cloth; all they got they did away with, and worked at the empty looms till late at night.  
>
> "I should heaps like to know how they're gettin' on with the cloth," reckoned the emperor, mate. But he felt rather uneasy when he remembered that he who wasn't fit for his office couldn't see it. Well, Personally, he was of opinion that he had sweet bugger-all to fear, yet he reckoned it advisable to send some bastard else first to see how matters stood. Every man and his dog in the town knew what a remarkable quality the stuff possessed, and all were toey to see how bad or stupid their neighbours were.  
>
> "I'll send me honest old minister to the weavers," reckoned the emperor, cobber. "He can judge best how the stuff looks, for he's intelligent, and nobody understands his office better than he."  
>
> The beaut old minister went into the room where the swindlers sat before the empty looms. "Heaven preserve us!" he reckoned, and opened his eyes wide, "I can't see anythin' at all," but he didn't say so. Fair fuckin' dinkum, both swindlers requested him to come near, and asked him if he didn't bloody well admire the exquisite pattern'n the beautiful colours, pointing to the empty looms. Mind ya, the poor old minister had a crack at his very best, but he could see nothin', for there was nothin' to be seen. "Far out, Crikey," he reckoned, "can I wouldn't know me arse from me bloody elbow? I should never 'ave reckoned so, and nobody must know it! Is it possible that I'm not fit for my office? Nah, I can't say that I was unable to see the cloth."  
>
> "Now, have ya got nothing to say?" said one of the swindlers, while he pretended to be busily weavin'.  
>
> "Oh, it's flamin' pretty, exceedingly bloody beautiful," replied the old minister lookin' through his glasses. "What a beautiful pattern, what grouse colours! I'll tell the emperor that I like the cloth heaps."  
>
> "We're grinnin' like a shot fox to hear that," said the two weavers, and described to him the colours'n explained the curious pattern. Well, the old minister listened attentively, that he might relate to the emperor what they said; and so he did.  
>
> Now the swindlers asked for more the folding stuff, silk'n gold-cloth, which they required for weaving. Mate, they kept the whole bloody show for themselves, and not a thread came near the loom, but they continued, as hitherto, to work at the empty looms.  
>
> Soon afterwards the emperor sent another honest courtier to the weavers to see how they were gettin' on, and if the cloth was nearly finished. Like the old minister, he looked and looked but could see nothin', as there was nothin' to be seen.  
>
> "Is it not a bloody beautiful piece of cloth?" asked the two swindlers, showing'n explaining the magnificent pattern, which, however, didn't bloody well exist.  
>
> "I'm not fuckin' stupid," said the bloke. "It's therefore my bloody beaut appointment for which I'm not fit. It's dead strange, but I must not let any one know it;" and he praised the cloth, which he didn't see, and expressed his joy at the beautiful colours'n the fine pattern. "It's ripper, bonzer," he said to the emperor.  
>
> Every bloke and sheila in the whole town talked about the precious cloth. At last the emperor wished to see it himself, while it was still on the loom. With a number of courtiers, including the two who had already been there, he went to the two clever swindlers, who now worked as bloody hard as they could, but without using any thread.  
>
> "Is it not magnificent?" said the two old statesmen who had been there before. "Yer Majesty must admire the colours and the pattern." And then they pointed to the empty looms, for they imagined the others could see the cloth.  
>
> "What's this?" reckoned the emperor, "I don't see anythin' at all. That's a shocker! Am I not the full quid? Am I unfit to be emperor? That would indeed be the most dreadful thing that could happen to me."  
>
> "Fair dinkum," he said, turning to the weavers, "yer cloth has our most gracious approval;" and noddin' contentedly he looked at the empty loom, for he didn't bloody well like to say that he saw nothin'. All his attendants, who were with him, looked and looked, and although they couldn't see anythin' more than the others, they said, like the emperor, "It's dead beautiful." And all advised him to wear the brand-spankin'-new magnificent clothes at a grouse procession which was soon to take place. "It's magnificent, beautiful, bonza," one heard 'em say; everybody seemed to be delighted, and the emperor appointed the two swindlers "Imperial Court weavers."  
>
> The whole night previous to the day on which the procession was to take place, the swindlers pretended to work, and burned more than sixteen candles. Punters should see that they were flat out like a lizard drinkin' to finish the emperor's brand-spankin'-new suit. They pretended to take the cloth from the loom, and worked about in the air with bloody big scissors, and sewed with needles without thread, and said at last: "The emperor's brand-spankin'-new suit is ready now."  
>
> The emperor and all his barons then came to the hall; the swindlers held their arms up as if they held something in their mitts'n said: "These are the trousers!" "This is the coat!" and "Here's the cloak!" and so on. "They're all as light as a cobweb, and one must feel as if one had nothin' at all upon the body; but that's just the beauty of 'em."  
>
> "Indeed!" said all the courtiers; but they couldn't see anythin', for there was nothin' to be seen.  
>
> "Does it please yer Majesty now to graciously undress," said the swindlers, "that we may assist yer Majesty in putting on the brand-spankin'-new suit before the large lookin'-glass?"  
>
> The emperor undressed, and the swindlers pretended to put the brand-spankin'-new suit upon him, one piece after another; and the emperor looked at himself in the glass from every side.  
>
> "How well they look! How well they fit!" said all. "What a fuckin' beautiful pattern! What fine colours! That's a magnificent suit of clothes!"  
>
> The master of the ceremonies announced that the bearers of the canopy, which was to be carried in the procession, were ready.  
>
> "I'm ready," said the emperor. "Doesn't bloody well my suit fit me bloody marvellously?" Then he turned once more to the lookin'-glass, that battlers should reckon he admired his garments.  
>
> The chamberlains, who were to carry the train, stretched their bloody mitts to the ground as if they lifted up a train, and pretended to hold something in their mitts; they didn't like battlers to know that they couldn't see anythin'.  
>
> The emperor marched in the procession under the beautiful canopy, and all who saw him in the street'n outta the windows exclaimed: "Indeed, the emperor's brand-spankin'-new suit is incomparable! What a long train he has! How well it fits him!" Nobody wished to let others know he saw nothing, for then he would have been unfit for his office or too stupid. Never emperor's clothes were more admired.  
>
> "But he has nothin' on at all," said a little littlie at last. "Bugger me! listen to the voice of an innocent nipper," said the old fella, and one whispered to the other what the littlie had said. "But he has nothing on at all," cried at last the whole battlers. That made a deep impression upon the emperor, for it seemed to him that they were right; but he reckoned to himself, "Now I must bear up to the end." And the chamberlains walked with still greater dignity, as if they carried the train which didn't exist. Faaaaark me.  

### Yarn mode (harnessed)

> Right, so yonks ago there's this emperor, and he's that mad keen on brand-spankin'-new clothes he blows every cent of his dosh on 'em. All he ever wants is to be done up flash as a rat with a gold tooth, every day of the week. Couldn't give a stuff about his diggers, and the theatre bores him rigid; the only thing that gets him goin' is a drive round town to show off a new suit. He's got a coat for every hour of the day. And where you'd say of any other king, "He's in with his ministers," with this bloke you'd say, "The emperor's in his dressin'-room." Every time.  
>
> Now, the big city he lives in is a lively old joint, and every day there's strangers rockin' up from all over the shop. Well, one day two con men roll into town. They tell everyone they're weavers, and they make out they can whip up the finest cloth you ever laid eyes on. The colours and patterns, they say, aren't just a bit of all right, they're bloody beautiful, and here's the kicker: anything made out of it can't be seen by any bloke who isn't up to his job, or who's a few snags short of a barbie. Dead set.  
>
> "Strewth, that'd be ripper cloth," thinks the emperor. "Get meself a suit outta that and I'd find out which blokes in me empire aren't up to their jobs, and I could tell the smart ones from the drongos. I've gotta have that stuff woven for me, pronto." So he hands the swindlers a motza up front, so they'll get crackin' straight away. They set up two looms and make out they're flat out like a lizard drinkin', but they're doin' sweet bugger-all on 'em. They ask for the finest silk and the dearest gold-cloth, stick the lot in their own pockets, and sit there workin' the empty looms till all hours. Cheeky ratbags.  
>
> "I'd love to know how they're goin' with that cloth," thinks the emperor. But he gets a bit toey when he remembers that a bloke who's no good at his job can't see it. Mind you, he reckons he's got nothin' to worry about himself, but he figures it's smarter to send some other poor bugger first to have a squiz. Every man and his dog in town knows what this cloth can do, and they're all itchin' to find out how useless or dim their neighbours are.  
>
> "I'll send me honest old minister down to the weavers," thinks the emperor. "He's the best judge of how it looks. He's got a good head on him, and nobody knows his job better."  
>
> So the good old minister wanders into the room where the two swindlers are sittin' in front of the empty looms. "Gawd help us!" he thinks, and his eyes go wide as saucers. "I can't see a flamin' thing!" But he keeps his trap shut. The two of 'em wave him over and ask him if he isn't just rapt with the gorgeous pattern and the lovely colours, pointin' at the empty looms. The poor old minister stares till his eyes water, but he sees nothin', 'cause there's nothin' there to see. "Oh, crikey," he thinks, "am I really that thick? Never would've picked it, and no bastard can ever find out! Could I be no good at me job? Nah, nah, I can't go sayin' I couldn't see the cloth."  
>
> "Well, cat got yer tongue, has it?" goes one of the swindlers, makin' out he's weavin' like mad.  
>
> "Oh, it's lovely, it's a real beauty," says the old minister, peerin' through his specs. "What a pattern, what cracker colours! I'll tell the emperor I'm stoked with it."  
>
> "Good on ya, we're rapt to hear it," say the two weavers, and they go through all the colours and explain the fancy pattern to him. The old minister hangs off every word, so he can tell the emperor exactly what they said. And that's just what he does.  
>
> Now the swindlers put their hands out for more dosh, more silk and gold-cloth, for the weavin', so they say. They pocket the whole bloody show, and not one thread goes near the loom, but they keep on workin' away at the empty looms same as before.  
>
> Not long after, the emperor sends another honest courtier to the weavers to see how they're goin', and whether the cloth's nearly done. Same as the old minister, he looks and looks and sees nothin', 'cause there's nothin' there to see.  
>
> "Isn't it a beaut bit of cloth?" ask the two swindlers, showin' him and explainin' the magnificent pattern, which, of course, doesn't exist.  
>
> "I'm not stupid," thinks the bloke. "So it must be me nice little job I'm not fit for. Bloody strange, but no one can know." And he raves about the cloth he can't see, and carries on about how happy he is with the lovely colours and the fine pattern. "It's an absolute ripper," he tells the emperor.  
>
> Every bloke and sheila in town's yakkin' about this fancy cloth. In the end the emperor wants to see it himself while it's still on the loom. So he takes a mob of courtiers, includin' the two who've already been, and goes round to the two clever swindlers, who are now workin' flat chat, but without a single thread.  
>
> "Isn't it magnificent?" say the two old pollies who've been there before. "Yer Majesty's gotta admire the colours and the pattern." And they point at the empty looms, 'cause they figure everyone else can see the cloth.  
>
> "What's goin' on here?" thinks the emperor. "I can't see a bloody thing! This is a shocker! Am I not the full quid? Am I not fit to be emperor? That'd be the worst thing that could ever happen to me."  
>
> "Oh, it's grouse," he goes, turnin' to the weavers, "it's got the royal tick of approval." And he stands there noddin' away, happy as Larry, starin' at the empty loom, 'cause there's no way he's gonna admit he can't see a thing. All his hangers-on look and look, and they can't see any more than the others, but they all go, same as the emperor, "Oh, it's beautiful." And they all tell him he oughta wear the magnificent new gear in the big parade that's comin' up. "Magnificent! Beautiful! Bonza!" you can hear 'em sayin'; everyone's grinnin' like a shot fox, and the emperor makes the two swindlers "Imperial Court Weavers." Gawd help us.  
>
> The whole night before the parade, the swindlers make out they're workin', and they burn more than sixteen candles, so everyone can see they're bustin' their guts to get the emperor's new suit finished. They make out they're takin' the cloth off the loom, they snip away at thin air with big scissors, they sew with needles with no thread, and at last they go, "There ya go, the emperor's new suit's ready."  
>
> Then the emperor and all his barons rock up to the hall, and the swindlers hold their arms up like they've got somethin' in their mitts and go, "Here's the strides!" "Here's the coat!" "And here's the cloak!" and so on and so forth. "They're all as light as a cobweb. Ya'd swear ya had nothin' on at all, but that's the beauty of 'em, see."  
>
> "Fair dinkum!" say all the courtiers, but they can't see a thing, 'cause there's nothin' there to see.  
>
> "Now, would Yer Majesty be so good as to get yer kit off," say the swindlers, "so we can help ya into yer new suit in front of the big mirror?"  
>
> So the emperor strips off, and the swindlers make out they're puttin' the new suit on him, one bit at a time, and the emperor's turnin' this way and that in the mirror, checkin' himself out from every side.  
>
> "Don't they look good! Don't they fit nice!" they all go. "What a pattern! What colours! Now that's a magnificent suit of clothes!"  
>
> Then the master of ceremonies announces the blokes carryin' the canopy for the parade are good to go.  
>
> "I'm ready," says the emperor. "Fits me a treat, doesn't it?" And he has one more twirl in front of the mirror, so everyone'll think he's admirin' his gear.  
>
> The chamberlains who are meant to carry the train reach their hands down to the floor like they're liftin' it up, and walk along makin' out they're holdin' somethin'; no way are they lettin' anyone know they can't see a thing.  
>
> So off the emperor marches in the parade under the beautiful canopy, and everyone in the street and hangin' out the windows is goin', "Strike me pink, the emperor's new suit's a cracker! Look at the length of that train! Doesn't it fit him nice!" Not one of 'em wants anyone knowin' they can't see anythin', 'cause that'd mean they're no good at their job or thick as a brick. Never were an emperor's clothes so carried on about.  
>
> "But he's got nothin' on!" says a littlie at last. "Struth, listen to the nipper, would ya, he's tellin' it straight," says his old man, and it gets whispered from one to the next what the kid said. "But he's got nothin' on!" the whole crowd's yellin' in the end. Well, that hits the emperor right in the guts, 'cause he reckons they've got a point. But he thinks to himself, "I've gotta see this through to the bitter end now." And the chamberlains walk along even more stuck-up than before, carryin' a train that isn't there. And him starkers as the day he was born. What a dog's breakfast.  

### Unharnessed

> Righto, so get this. Donkey's years ago there was this emperor, yeah, and the bloke was absolutely mad about his clobber. Spent every last cent he had on new gear, the lot. All he ever wanted was to be done up like a pox doctor's clerk, every day of the week. Didn't give a stuff about his soldiers, couldn't be buggered with the theatre - the only thing he gave a rat's about was goin' out for a drive so everyone could get a squiz at his latest suit. Had a different coat for every hour of the day, fair dinkum. And ya know how with a king they'd say, "Sorry, he's in with his ministers"? Well, with this fella it was always, "Sorry, mate, the emperor's in his dressin' room."  
>
> Now the big city he lived in was a lively joint, always heaps goin' on, blow-ins turnin' up every day from all over the shop. And one day these two shonky blokes rock up. Con men, the pair of 'em, but they reckon they're weavers, and they're spruikin' that they can make the best cloth you ever laid eyes on. Colours and patterns a real treat, they reckon - but here's the kicker: anything made outta their stuff was invisible to any bloke who wasn't up to his job, or who was just thick as two short planks.  
>
> "Strewth, that'd be ripper cloth," the emperor thinks. "If I had a suit outta that, I'd know straight off which of me blokes weren't up to scratch, and I could sort the smart ones from the drongos. Gotta get some of that woven up, pronto." So he forks out a motza to the two shysters, up front, so they'd get crackin' straight away. They set up two looms and carry on like they're flat chat, but they're doin' bugger all on 'em. Then they ask for the finest silk and the flashest gold cloth goin', and whatever they got went straight in their own pockets - and then there they are, workin' back at the empty looms till all hours.  
>
> "Wonder how they're goin' with that cloth," the emperor thinks. But then he gets the wind up a bit, rememberin' that any bloke who wasn't fit for his job couldn't see it. Now, personally, he reckoned he had nothin' to worry about - but still, best send some other poor bugger first to see how things were travellin'. Meanwhile the whole town had heard about this magic cloth, and every stickybeak in the place was itchin' to find out how useless or thick their neighbours were.  
>
> "I'll send me honest old minister down to the weavers," the emperor reckons. "He'll know what the stuff looks like - he's got a good head on his shoulders, and nobody knows his job better than him."  
>
> So the good old minister fronts up to the room where the two shonks are sittin' at the empty looms. "Hell's bells," he thinks, eyes out on stalks, "I can't see a bloody thing!" - but he keeps his trap shut. The two of 'em wave him over and ask him isn't the pattern just gorgeous and the colours just beaut, pointin' at the empty looms. The poor old bugger tries his hardest, but he can't see nothin', 'cause there's nothin' there to see. "Oh, jeez," he thinks, "am I really that thick? Never would've picked it - and nobody can find out! Am I not fit for me job? Nah, nah, I can't go sayin' I couldn't see the cloth."  
>
> "Well, ya gunna say somethin' or what?" says one of the con men, makin' out he's busy weavin'.  
>
> "Oh, it's very nice, absolutely beautiful," says the old minister, peerin' through his specs. "What a pattern, what colours! I'll tell the emperor I'm rapt with it."  
>
> "Good to hear," say the two weavers, and they go through the colours and the fancy pattern with him, chapter and verse. The old minister listens real careful so he can tell the emperor the lot - and that's just what he does.  
>
> Then the con men put the bite on for more cash, more silk and more gold cloth - for the weavin', y'see. Pocketed the lot, they did, not one thread went near the loom, and they kept on workin' away at the empty looms same as before.  
>
> Not long after, the emperor sends another honest bloke from the court to see how they're goin' and whether the cloth's nearly done. Same as the old minister, he looks and he looks, but he can't see a thing, 'cause there's nothin' to see.  
>
> "Isn't that a beaut bit of cloth?" ask the two shonks, showin' him and explainin' this magnificent pattern - which, mind you, wasn't there.  
>
> "I'm not thick," says the bloke. "So it must be me cushy job I'm not fit for. Bloody weird, but I can't let anyone know." So he talks up the cloth he can't see, and goes on about how much he loves the gorgeous colours and the fancy pattern. "It's an absolute ripper," he tells the emperor.  
>
> Next thing the whole town's yappin' about this precious cloth. In the end the emperor wants a squiz himself while it's still on the loom. So he grabs a mob of his courtiers - includin' the two who'd already been - and heads down to the two crafty buggers, who are goin' hammer and tongs now, flat chat, but without a single thread.  
>
> "Isn't it magnificent?" say the two old pollies who'd been there before. "Your Majesty's gotta admire the colours and the pattern." And they point at the empty looms, 'cause they figured everyone else could see the cloth.  
>
> "What the hell's this?" the emperor thinks. "I can't see a fuckin' thing. This is a shocker! Am I thick? Am I not fit to be emperor? That'd be about the worst thing that could ever happen to me."  
>
> "Yeah, really," he says, turnin' to the weavers, "your cloth has our most gracious tick of approval," and he stands there noddin' away, happy as Larry, starin' at the empty loom, 'cause there's no way he's lettin' on he can't see nothin'. All his hangers-on who'd come along looked and looked, and they couldn't see any more than the rest, but they all say, same as the emperor, "Very beautiful." And the whole mob of 'em reckon he oughta wear the flash new gear in the big parade that was comin' up. "Magnificent! Beautiful! Top shelf!" - that's all ya heard; everyone was rapt, and the emperor goes and makes the two shysters "Imperial Court Weavers," no less.  
>
> The whole night before the parade, the con men are makin' out they're workin', and they burn more than sixteen candles so everyone could see they were flat out finishin' the emperor's new suit. They pretend to take the cloth off the loom, go snippin' at thin air with big scissors, sewin' with needles with no thread in 'em, and finally they say, "Righto - the emperor's new suit's done."  
>
> Then the emperor and all his barons rock up to the hall, and the con men hold their arms up like they're carryin' somethin' and go, "Here's the strides!" "Here's the coat!" "And here's the cloak!" and so on and so forth. "Light as a cobweb, the lot of it - feels like ya got nothin' on at all. But that's the beauty of it, see."  
>
> "Too right!" say all the courtiers - but they couldn't see a thing, 'cause there was nothin' to see.  
>
> "Now, if Yer Majesty'd be so good as to get yer gear off," say the con men, "we'll help ya into the new suit in front of the big mirror."  
>
> So the emperor strips off, and the con men make out they're puttin' the new suit on him, one bit at a time, and the emperor's checkin' himself out in the mirror from every angle.  
>
> "Don't they look a treat! Don't they fit like a glove!" says everyone. "What a pattern! What colours! Now that's a bloody magnificent suit!"  
>
> Then the master of ceremonies sings out that the blokes carryin' the canopy in the parade were ready to roll.  
>
> "I'm ready," says the emperor. "Doesn't me suit fit a treat?" And he has one more turn in front of the mirror, so people'd think he was admirin' his gear.  
>
> The chamberlains who were meant to carry the train bend down with their hands to the ground like they're pickin' it up, and make out they're holdin' somethin' - no way they wanted anyone knowin' they couldn't see a thing.  
>
> So off the emperor goes, marchin' in the parade under his fancy canopy, and everyone in the street and hangin' out the windows is singin' out, "Fair dinkum, the emperor's new suit is second to none! Look at the length of that train! Fits him like a glove!" Nobody wanted to let on they couldn't see nothin', 'cause then they'd be no good at their job or too thick for words. No emperor's clobber ever got such a big wrap.  
>
> "But he's got nothin' on!" says a little tacker in the end. "Strewth, listen to the kid - innocent as they come," says his old man, and what the kid said gets whispered round from one to the next. "But he's got nothin' on!" the whole crowd's yellin' in the end. Well, that really rattled the emperor, 'cause it looked to him like they were dead right - but he thinks to himself, "Well, I've gotta tough it out to the bitter end." And the chamberlains marched on with their noses even higher in the air, carryin' a train that wasn't even bloody there.  

---

## Pride and Prejudice, chapter 1

### Base (level 5)

> Look, it's a truth universally acknowledged, that a single bloke in possession of a beaut fortune must be in want of a wife.  
>
> However little known the feelings or views of such a bloke may be on his first enterin' a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he's considered as the rightful property of some one or other of their daughters.  
>
> “Bloody hell, me bloody dear Mr. Bennet,” said his sheila to him one day, “have ya heard that Netherfield Park is let at last?”  
>
> Mr. Well, Bennet replied that he hadn't.  
>
> “But it's,” returned she; “for Mrs. Long has just been here, and she told me all about it.”  
>
> Mr, cobber. Bennet made no answer.  
>
> “Aw, don't ya want to know who has taken it?” cried his wife, impatiently.  
>
> “Ya want to tell me, and I 'ave no objection to hearin' it.”  
>
> This was invitation enough.  
>
> “Why, me dear, ya must know, Mrs, ay. So anyway, long says that Netherfield is taken by a young fella of large fortune from the north of England; that he came down on Monday in a chaise'n four to see the joint, like they owned the place, and was so much delighted with it that he agreed with Mr. Morris immediately; that he's to take possession before Michaelmas, and some of his bloody servants are to be in the house by the end of next week.”  
>
> “What's his name?”  
>
> “Bingley.”  
>
> “Is he married or single?”  
>
> “Oh, single, me dear, to be sure! Anyway, a single bloke of large fortune; four or five thousand a year. What a fine thing for our girls!”  
>
> “How so, ya flamin' mongrel? how can it affect 'em?”  
>
> “Me dear Mr. Bennet,” replied his wife, “how can ya be so tiresome? Mind ya, ya must know that I'm thinkin' of his bloody marryin' one of 'em.”  
>
> “Is that his design in settlin' here?”  
>
> “Design? Bulldust, how can ya talk so! But it's flamin' likely that he may fall in love with one of 'em, and therefore ya must visit him as soon as he comes.”  
>
> “I see no occasion for that. Ya'n the girls may go--or ya may send 'em by themselves, which perhaps will be still better; for as yer spunky as any of 'em, Mr. Bingley might like ya the best of the party.”  
>
> “My dear, ya flatter me. I defo have had my share of beauty, but I don't pretend to be anything extraordinary now. When a sheila has five grown-up daughters, she oughta give over thinking of her own beauty.”  
>
> “In such cases, a sheila hasn't often much beauty to think of.”  
>
> “But, my dear, ya must indeed go'n see Mr. Bingley when he comes into the neighbourhood.”  
>
> “It's more than I engage for, I assure ya.”  
>
> “But consider yer daughters. Only reckon what an establishment it would be for one of 'em. Sir William and Lady Lucas are dead set on go, merely on that account; for in general, ya know, they visit no brand-spankin'-new comers. Mind ya, Indeed ya must go, for it'll be impossible for us to visit him, if ya don't.”  
>
> “Yer over scrupulous, surely. I dare say Mr. Bingley will be properly glad to see ya; and I'll send a few lines by ya to assure him of me bloody hearty consent to his marryin' whichever he chooses of the girls--though I must chuck in a beaut word for my little Lizzy.”  
>
> “I desire you'll do no such thing. Lizzy ain't a bit better than the others: and I'm sure she isn't half so handsome as Jane, nor half so bloody good-humoured as Lydia. But yer bloody always givin' her bloody the preference.”  
>
> “They have none of 'em much to recommend 'em,” replied he: “they're all silly and ignorant like other girls; but Lizzy has somethin' more of quickness than her bloody sisters.”  
>
> “Mr. Bennet, how can ya abuse yer own littlies in such a way? Ya take delight in vexin' me. Ya have no compassion on me poor nerves.”  
>
> “Ya mistake me, me dear. I have a high respect for yer bloody nerves. They're me old mates. Mind ya, I have heard ya mention 'em with consideration these twenty years at least.”  
>
> “Ah, ya dunno what I suffer.”  
>
> “But I hope you'll get over it, and keep on kickin' to see many young men of four thousand a year come into the neighbourhood.”  
>
> “It'll be no use to us, if twenty such should come, since ya won't visit 'em.”  
>
> “Depend upon it, me dear, that when there are twenty, I'll visit 'em all.”  
>
> Mr. Bennet was so odd a mixture of quick parts, sarcastic humour, reserve, and caprice, that the experience of three-and-twenty years had been insufficient to make his wife understand his character. Her mind was rotten, maggoted difficult to develope. She was a sheila of mean understanding, little information, and uncertain temper. When she was snug as a bug in a rug, she fancied herself nervous. The business of her life was to get her daughters married: its solace was visiting'n news. Fuck me dead.  

### Yarn mode (harnessed)

> Right, so it's a truth everyone and their dog knows: a single bloke who's loaded must be on the lookout for a missus.  
>
> Now, nobody's got a clue what a bloke like that actually feels or thinks when he first rocks up in a neighbourhood. Doesn't matter. The families round about have got this truth stuck in their noggins so firm that he's counted as the rightful property of one or other of their daughters. Signed, sealed, delivered, before he's even unpacked.  
>
> So one day Mrs. Bennet goes to her husband, "Mr. Bennet, love, have ya heard Netherfield Park's finally been let?"  
>
> Mr. Bennet says nah, he hadn't.  
>
> "Well, it has," she goes, "'cause Mrs. Long's just been round, and she gave me the whole goss."  
>
> Mr. Bennet doesn't say a word. Not a peep.  
>
> "Don't ya wanna know who's took it?" she cries, toey as a racehorse.  
>
> "You wanna tell me, and I've got no problem hearin' it."  
>
> Well, that was all the invite she needed.  
>
> "Well, darl, ya gotta know, Mrs. Long says Netherfield's been taken by a young bloke up from the north of England with a bloody great fortune; he come down Monday in a chaise and four to suss the joint out, and he was so rapt with it he shook on it with Mr. Morris then and there; he's movin' in before Michaelmas, and some of his servants'll be in the house by the end of next week."  
>
> "What's his name?"  
>
> "Bingley."  
>
> "Is he married or single?"  
>
> "Oh, single, love, course he is! A single bloke with a big fortune, four or five thousand a year. What a beaut thing for our girls!"  
>
> "How's that? What's it got to do with them?"  
>
> "Oh, Mr. Bennet," his wife goes, "how can ya be such a pain in the arse? Ya must know I'm thinkin' of him marryin' one of 'em."  
>
> "Is that his plan, movin' here?"  
>
> "Plan? Bulldust! What a thing to say! But he's pretty likely to fall for one of 'em, so ya gotta go call on him the minute he gets here."  
>
> "Don't see any need for that. You and the girls can go, or ya could send 'em on their own, which might be even better, 'cause you're as good-lookin' as any of 'em, and Mr. Bingley might pick you out of the whole mob."  
>
> "Oh, go on, you're havin' me on. I've defo had me share of looks, fair enough, but I don't make out I'm anythin' special now. When a sheila's got five grown-up daughters, she oughta give up worryin' about her own looks."  
>
> "In that case, a sheila hasn't usually got much in the way of looks to worry about."  
>
> "But, love, ya properly gotta go and see Mr. Bingley when he moves into the neighbourhood."  
>
> "That's more than I'll sign up for, I promise ya."  
>
> "But think of yer daughters. Just think what a set-up it'd be for one of 'em, house, money, the whole box and dice. Sir William and Lady Lucas are dead set on goin', just for that; and ya know they don't normally bother with brand-spankin'-new folks. Ya flamin' well gotta go, 'cause there's no way we can call on him if you don't."  
>
> "You're a bit too fussy about the rules, surely. I reckon Mr. Bingley'll be stoked to see ya; and I'll send a note along with ya tellin' him he's got me full blessin' to marry whichever of the girls he likes, though I'll have to chuck in a good word for me little Lizzy."  
>
> "Don't ya dare. Lizzy's not a skerrick better than the others: and I'm sure she's not half as pretty as Jane, nor half as good-humoured as Lydia. But you're always playin' favourites with her."  
>
> "None of 'em's got much goin' for 'em," he goes, "they're all silly and know nothin', like other girls; but Lizzy's a bit quicker on the uptake than her sisters."  
>
> "Mr. Bennet, fair dinkum, what sorta father bags his own littlies like that? Ya love windin' me up. Ya got no pity for me poor nerves."  
>
> "Ya got me wrong, love. I've got a lot of respect for yer nerves. They're old mates of mine. I've heard ya bangin' on about 'em with great respect for twenty years at least."  
>
> "Ah, ya dunno what I go through."  
>
> "Well, I hope ya get over it, and keep on kickin' long enough to see heaps of young blokes on four thousand a year rock up in the neighbourhood."  
>
> "It'll be no use to us if twenty of 'em come, since ya won't go and see 'em."  
>
> "Bet on it, darl: when there's twenty, I'll go and see the lot."  
>
> Now, Mr. Bennet was such a weird mix of quick wits, dry sarcastic humour, keepin' to himself and doin' whatever took his fancy, that twenty-three years of marriage hadn't been enough for his wife to suss him out. Poor bugger. She, on the other hand, was no great mystery. She was a sheila who was a few snags short of a barbie, didn't know much, and her temper could go either way. When she was cranky, she reckoned it was her nerves. Her whole job in life was gettin' her daughters married off: and what kept her goin' was droppin' in on the neighbours and a good goss. Gawd help us.  

### Unharnessed

> Now everyone knows this, right, it's just how it is: a single bloke who's rollin' in it has gotta be on the lookout for a missus.  
>
> Doesn't matter if nobody's got a clue what the fella actually thinks when he first rocks up in a new neighbourhood. The local families have got it locked in their heads that he's already spoken for, and he belongs to one of their daughters, they just haven't sorted out which one yet.  
>
> So one day Mrs Bennet goes to her old man, "Mr Bennet, love, have ya heard? Somebody's finally taken Netherfield Park."  
>
> Mr Bennet reckons he hadn't heard.  
>
> "Well they have," she goes, "'cause Mrs Long's just been round and she gave me the full rundown."  
>
> Mr Bennet doesn't say a bloody word.  
>
> "Don't ya wanna know who's taken it?" she yells at him, gettin' all toey.  
>
> "You're dyin' to tell me, and I'm not gonna stop ya."  
>
> Well, that's all the green light she needed.  
>
> "Righto, so Mrs Long reckons Netherfield's been snapped up by a young bloke from up north of England, absolutely loaded he is. Come down Monday in a flash carriage with four horses to have a squiz at the place, and he was that rapt with it he shook on it with Mr Morris then and there. He's movin' in before Michaelmas, and some of his staff'll be in the house by the end of next week."  
>
> "What's his name?"  
>
> "Bingley."  
>
> "Married or single?"  
>
> "Oh, single, love, too right he is! A single bloke with a motza, four or five grand a year. What a ripper for our girls!"  
>
> "How d'ya figure that? What's it got to do with them?"  
>
> "Mr Bennet," she goes, "how can ya be such a pain in the arse? Ya know bloody well I'm thinkin' he'll marry one of 'em."  
>
> "Oh, is that what he's movin' here for, is it? That's his plan?"  
>
> "Plan? Don't talk rubbish! But it's a fair bet he'll fall for one of 'em, so ya gotta go round and see him the minute he lands."  
>
> "Can't see why I'd bother. You and the girls can go, or send the girls on their own, that'd be better again, 'cause you're as good a sort as any of 'em and Bingley might end up keenest on you."  
>
> "Oh stop it, ya big flatterer. I was a bit of a looker in me day, I'll give ya that, but I'm not kiddin' meself I'm anything special now. Once a woman's got five grown-up daughters she oughta give up worryin' about her own looks."  
>
> "Usually by then she hasn't got a lot of looks left to worry about anyway."  
>
> "Yeah, but love, ya really gotta go and see Mr Bingley when he gets here."  
>
> "I'm promisin' nothin', I'll tell ya that for free."  
>
> "But think of yer daughters! Just think what a set-up it'd be for one of 'em. Sir William and Lady Lucas are goin', and that's the only reason, 'cause ya know they never bother visitin' new people. Ya've gotta go, 'cause there's no way we can visit him if you don't."  
>
> "Fair go, you're too fussy by half. I reckon Bingley'll be stoked to see ya. And I'll give ya a note to take him sayin' he's got my blessin' to marry whichever one of the girls he fancies. Mind you, I'll have to put in a good word for my little Lizzy."  
>
> "Don't you bloody dare. Lizzy's not one bit better than the others. She's not half as pretty as Jane, and nowhere near as good-natured as Lydia. But she's always yer favourite."  
>
> "Look, none of 'em are much chop," he goes. "They're all as silly and as clueless as any other girls. But Lizzy, there's no flies on her, she's sharper than her sisters."  
>
> "Mr Bennet! How can ya bag yer own kids like that? Ya just love stirrin' me up. Ya've got no sympathy for me poor nerves."  
>
> "Ya've got me all wrong, love. I've got heaps of respect for yer nerves. Me and them go way back. I've heard ya bangin' on about 'em for twenty years at least."  
>
> "Ah, ya've got no idea what I go through."  
>
> "Well, I hope ya get over it, and live to see heaps of young blokes on four grand a year rock up round here."  
>
> "Won't do us a scrap of good if twenty of 'em turn up, 'cause you won't visit 'em."  
>
> "Don't you worry, love. When there's twenty, I'll visit the bloody lot."  
>
> Thing is, Mr Bennet was such a weird mix of quick wits, a dry sense of humour, keepin' to himself and doin' whatever took his fancy, that after twenty-three years of marriage his missus still couldn't pick him. She, on the other hand, was dead easy to work out. Not the full quid, didn't know much about anything, and her moods went up and down like a yo-yo. Any time she was cranky she'd reckon it was her nerves playin' up. Her whole job in life was gettin' her daughters married off, and what kept her goin' was visitin' and a good goss.  

---

## Hamlet: "To be, or not to be"

### Base (level 5)

> Strewth, to be, or not to be, that's the question:  
> Whether ’tis nobler in the mind to suffer  
> The slings'n arrows of outrageous fortune,  
> Or to take arms against a sea of troubles,  
> And by opposing end them? To cark it—to sleep,  
> No more; and by a sleep to say we end  
> The heart-ache, and the thousand natural shocks  
> That flesh is heir to: ’tis a consummation  
> Devoutly to be wish’d. To cark it, to sleep.  
> Jeez, to sleep, perchance to dream—ay, there’s the rub,  
> For in that sleep of death what dreams may come,  
> When we've shuffled off this mortal coil,  
> Must give us pause. Well, there’s the respect  
> That makes calamity of so long life.  
> For who would bear the whips and scorns of time,  
> The oppressor’s wrong, the proud bloke’s contumely,  
> The pangs of dispriz’d love, the law’s delay,  
> The insolence of office, and the spurns  
> That patient merit of the unworthy takes,  
> When he himself might his quietus make  
> With a bare bodkin? Buggered if I know. Bloody hell, who would these fardels bear,  
> To grunt'n sweat under a weary life,  
> But that the dread of somethin' after death,  
> The undiscover’d country, from whose bourn  
> No traveller returns, puzzles the will,  
> And makes us rather bear those ills we have  
> Than fly to others that we know not of?  
> Thus conscience does make cowards of us all,  
> And thus the native hue of resolution  
> Is sicklied o’er with the pale cast of reckoned,  
> And enterprises of grouse pith and moment,  
> With this regard their currents turn awry  
> And lose the name of action. Fuck me dead.  

### Yarn mode (harnessed)

> Right, so. To be, or not to be, that's the question, ay.  
> Is it the better man who grits his teeth 'n just cops  
> every rock 'n spear that rotten luck chucks at him,  
> or the one who rolls his sleeves up 'n has a proper crack  
> at a whole bloody ocean of strife, and by havin' a go, finishes it off?  
> To cark it, to have a kip, that's all there is to it;  
> and if one good kip means we're done with  
> the heartache, and the thousand knocks  
> that come free with the meat 'n bones we're walkin' round in, well, that's a finish  
> ya'd get down on yer knees 'n pray for. To cark it, to have a kip.  
> To kip, and maybe dream. Yeah, there's the catch,  
> 'cause in that last long kip, what dreams might rock up  
> once we've shuffled off this mortal coil?  
> That's what stops a bloke in his tracks. That's the very thing  
> that keeps us doin' it tough for so flamin' long.  
> For who'd put up with the floggin's 'n sneers the years dish out,  
> the boss cocky stompin' all over ya, the big-noter lookin' down his nose,  
> the ache of a love that got tossed aside like an empty tinnie, the courts draggin' their feet,  
> the pollies 'n pen-pushers bein' up themselves, and all the kicks  
> a decent, patient bloke cops from a pack of useless mongrels,  
> when he could square the whole lot up himself  
> with nothin' but a bare little blade? Who'd lug this load about,  
> gruntin' 'n sweatin' through a life that's got him stuffed,  
> if it weren't for bein' scared stiff of whatever comes after ya go to meet yer maker,  
> the undiscovered country, way out past the black stump, where not one traveller  
> ever makes it home? That's what's got us scratchin' our noggins,  
> and makes us rather put up with the crook lot we've got  
> than shoot through to some other mess we know bugger all about.  
> So yer conscience turns the lot of us into sooks,  
> and the good honest colour of a bloke's guts  
> goes all pasty 'n crook from too much reckonin',  
> and big plans with real grunt behind 'em  
> get sidetracked worryin' about all that, wander off course like a ute with a flat,  
> and never get to be action. Gawd help us.  

### Unharnessed

> Righto, here's the thing, eh. Do ya keep goin', or do ya pack it in? That's the question, mate.  
>
> Is it more the decent thing, in yer own head, to just cop it sweet, wearin' every rotten bloody break that rough luck chucks at ya? Or do ya get stuck into the whole flamin' ocean of strife, have a go at it, and by havin' a go, put an end to the lot?  
>
> Carkin' it. That's just havin' a kip, eh. Nothin' more. And if a kip puts a stop to the heartache and the thousand knocks that come standard with bein' flesh and blood, well, bloody oath ya'd want that. Ya'd be on yer knees prayin' for it.  
>
> Cark it. Have a kip. A kip, and maybe a dream. Yeah, nah, there's the catch, see. 'Cause in that big sleep, once we've shrugged off all this mortal carry-on, who knows what dreams might turn up? That's what pulls ya up short. That's the bit that keeps us hangin' round, coppin' strife for the long haul.  
>
> 'Cause who'd put up with the hidings and the sledgin' that life dishes out? The boss with his boot on yer neck, the big-noter lookin' down his nose at ya, the gut-ache of bein' knocked back by someone ya love, the courts takin' their sweet bloody time, the jumped-up pen-pushers with their attitude, and the kicks in the guts a decent battler cops off no-hopers, when he could just call it quits himself with nothin' more than a bare little blade? Who'd hump this swag, gruntin' and sweatin' his way through a dog of a life?  
>
> Nobody, mate, if it weren't for bein' shit-scared of what comes after ya cark it. That's the Never Never out there that no bugger's ever come back from, and that's what does yer head in. That's why we'd sooner put up with the crap we've already got than shoot through to some other mess we know bugger all about.  
>
> So thinkin' too hard turns the whole lot of us into gutless wonders. The fair dinkum fire in yer belly goes all pale and crook once ya start chewin' it over, and big plans, the real serious, heavy stuff, they get sidetracked by all the mullin', go off the rails, and end up bein' nothin' but talk. Never get done, do they.  
