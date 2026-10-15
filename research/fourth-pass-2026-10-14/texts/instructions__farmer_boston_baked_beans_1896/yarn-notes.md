## dinkum

- Accepted on the first submit, with nothing declined. The planned phrases ("snags", "chucked", "meant to", "dead") were all in the right sense.
- Engine draft "Yellow-eyed beans are dead fuckin' good" put swearing into a recipe; the instructions genre says no colour like that. Ignored.
- Lint warned "repeated: cut (3 times)". That's a false positive: "cut" is the recipe's plain verb, not slang. "chuck (3 times)" was fair, so I varied it.
- Lint suggestions in the wrong sense: "of course" (in-sentence adverb) offered "too right", "nah, yeah", "bloody oath", which are replies, not adverbs.
- Lookups: "stomach" came back empty, with no "guts" for the belly ("easier on the guts"); "guts" only finds the idioms. "broken" offered "fucked" first for a busted pot; at vulgarity 2 it's allowed, but it's the wrong register for a recipe.
- Genre detection called it instructions, as the task said. There's no `--genre` flag to confirm it with.

## troppo

- Accepted on the first submit.
- Lint suggestions in the wrong sense: "pot belly" (the bean pot's bulging sides) offered "a verandah over the toy shop",
  which is a man's beer gut. "honest" (in "let's be honest") offered "fair dinkum" twice (a duplicate in the list) and "ridgy-didge".
  Good ones: "swear blind", and "bung" for the busted pot.
- Lookup "sausage sizzle" only found "snag", though it's a staple Aussie term and worth its own entry (the
  Bunnings or school fundraiser BBQ). "dud" (a bad one, here a bad bean) came back empty.
- The instructions genre held the performance in check: every step, quantity and unit stays, and the colour goes
  into the asides and connectives. The setting read clearly here.
