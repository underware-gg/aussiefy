## deadset

- Only one planned phrase: "Nah, nah" for "No." in "Can I delegate my FOLD...? No." It means a firm-but-friendly no, which is right, and I kept it. In technical docs a single "Nah." might sit better than the doubled form, but it's not wrong.
- The engine left the US spellings "misbehavior" and "fulfill" in its draft (the prose isn't code); I wrote "misbehaviour" and rephrased "fulfill". Lint didn't flag either.
- Lookups wrong: "anyone" returned "a punter" (glossed as a gambler); "on purpose" returned "keen on"; "a share" returned "bring a plate"; "help" returned "keen". Empty: "set up", "penalty", "get in touch".
- The MARKUP guard worked: in a scratch test, a changed code span (`1787148023`) and a changed heading ("## Support") were both rejected with `markup_changed`. The system prompt's "a heading's words may be Aussified" contradicts MARKUP's "keep every heading exactly" for md/mdx, though.
- It wasn't clear whether a component's children text (the LinkCard blurbs) and the front matter `description` count as prose. I left both untouched, to be safe.
- Accepted on the first submit.

## dinkum

- Lint suggested "a squiz" for "a look" in "have a look at [Ciphernode Operators]", which fit and I took it.
- Lookups empty: "ticking over", "pull its weight".
- OPENINGS ("Listen to this.", "Here's one for ya.", "Back in the day,") are wrong for an FAQ, so I used none.
- Accepted on the first submit.

## troppo

- Lint suggested "heaps" for "lots" in "The questions come in three lots" (the noun meaning batch or group). Wrong sense: the A_LOT meaning shouldn't fire on "N lots". It also suggested "dosh" for "money" in the fixed idiom "putting your money where your mouth is", and "beaut" for "good" in "Now the good bit".
- Lookups empty for genuine phrases I used: "get a guernsey" (be selected), "the whole box and dice", "first in, best dressed", "skin in the game" (returned "game": plucky). Wrong: "lowdown" returned "down in the dumps"; "muck up" returned only "muck around" (the verb "muck up", to make a mistake, is missing); "yakka" returned only "hard yakka".
- Clarity: troppo in technical docs was the hardest call. "No slang for a technical term" plus "keep list steps exact" leaves the colour all in the connecting prose. I riffed on facts already there ("a whole 23 seconds after the gates opened", from 14:00 to 14:00:23).
- Accepted on the first submit, at 839 vs 669 words.
