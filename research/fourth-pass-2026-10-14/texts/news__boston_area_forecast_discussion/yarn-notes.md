## dinkum
- Both planned phrases were wrong-sense: "creek" for "stream" in "northern stream shortwave trough" (the jet stream's northern branch, a term of art), and "do it tough" for "struggle" in "Highs will likely struggle to get out of the 40s" (gloss is people going through hard times). Declined both. The engine draft also put "bloody" into "a bit too bloody early to say the 'S word'".
- Lint false positive: repeated_phrase "s around c" (3 times), a tokenising artefact of my metric brackets "(around 16C)", "(around 10-11C)", "(around -2C)".
- Lint suggestions in the wrong sense: "battle" -> "stoush" (WAR) for the verb "battle to get out of the 40s"; "keep going" -> "battle on" (ENDURE) for rain continuing overnight.
- I first wrote "Expect a cold one Saturday night" and caught that it reads as a beer; lint didn't flag it. Lookup "very cold weather" gave "brass monkey weather", used instead. The DIFFICULT_SENTENCES list is 22 of the text's sentences, mostly terms of art the genre keeps ("guidance", "advection", "elevation"), which made it noise here. Accepted after 2 submits (the second only my own fix).

## troppo
- OPENINGS "True story, this." and "Okay, so." are story openers that don't suit a forecast discussion; "Pull up a stool." worked as a forecaster talking to the room.
- Same two wrong-sense phrases declined; "battle" -> "stoush" suggestion again. The riff for "creek" ("bone dry half the year") came from the wrong-sense match, so it was unusable too.
- Troppo here meant reactions after each beat ("Jumper weather.", "Rug up.", "Barely worth getting the brolly out") with every number and term kept. Accepted after 1 submit.
