# Rails audit: which guards reject good swaps

Asked for: "whether any of our tests/rails are rejecting otherwise reasonable/good swaps, e.g. are any over
zealous / overly restrictive."

Method: every corpus text (classics, reference, everyday) through the engine at level 4, seed 1, with every
rejection reason tallied for the spans that were left untouched. Each frequent reason was then read in context
to see whether it stopped a wrong swap or a good one.

## Before

1,246 swaps, 482 spans kept. The reasons, most frequent first (spans where nothing was eligible):

| Count | Reason | Verdict |
|---|---|---|
| 111 | a multi-word term already used in this text | **right**: see below |
| 100 | needs level N | right (the level dial) |
| 45 | vulgarity over the cap | right (the vulgarity dial) |
| 43 + 7 | person idiom, but the subject isn't a person | **over-strict**: the subject finder took the verb, "and" or "going" for the subject |
| 36 | cannot fill {poss} | **over-strict**: judged on every variant, not the form used; "his wife" never became "his missus" |
| 36, 24, 14 | gated (not_aussie, archaic, dubious_meaning) | right (dictionary review decisions) |
| 27 | register 'dated' | right (the level's registers) |
| 17 | the phrase's article would be lost | **over-strict**: "the dead" could be "the poor buggers" |
| 14 | the term brings its own article | **over-strict**: "the waterhole" could be "the billabong" |
| 12 | a swear for a person, in a genre that doesn't take it | right (genre policy) |
| 9 | said only of people (a tank, a handkerchief) | right |

## Fixes

- **Forms by slot.** An entry is rejected only when none of its forms can fill the span; the engine picks
  among the forms that can. A leading possessive fills {poss} ("his wife" -> "his missus"), as does a person
  pronoun before a verb phrase ("she sits down" -> "she plonks herself down"), without becoming the subject
  later slots agree with.
- **Articles fitted, not refused.** The phrase's own determiner is kept when the term has none ("the dead" ->
  "the poor buggers", "his wife" -> "his missus"), and the term's article goes when the phrase already has one
  ("the waterhole" -> "the billabong") or is plural ("wild horses" -> "brumbies"). Kept: the, this, that,
  these, those and possessives; not "no" or "a", which the term carries ("no chance" -> "Buckley's", not "no
  Buckley's").
- **What the old article rule was really guarding.** Lifting it exposed "the poor old minister" -> "the
  battlers old minister": the trigger "the poor" (the noun) caught the adjective. A swap that keeps the
  determiner now needs the noun phrase to end with the span (punctuation, a verb, a preposition or
  conjunction next).
- **Plural triggers.** A trigger written as a plural ("wild horses") was read as singular, so its term came
  out singular ("The brumby ran"). It now reads as plural, and a term that is already plural ("strides",
  "the olds") or a mass noun (`plural: clobber`) stays as it is.
- **The subject finder** walks back past the verb chain ("you are not going to get rich", "everybody seemed
  to be delighted", "you don't feel thirsty") and stops at a clause join ("and was comfortably dozing": the
  subject is in the clause before, so it isn't guessed). Everybody, somebody and the rest count as people.
- **Form slots.** A form whose {np} nothing fills is no longer chosen ("they were dirty about" -> "they were
  dirty").

## What the design review caught, and the fixes

The first cut read a noun's number from its spelling: any trigger ending in -s matched as a plural. That
turned "a merry Christmas" into "Chrissies", "a shambles" into "shemozzles", "forty winks" into "kips". Number
now comes from the data: a trigger written as a plural keeps the term as written unless the entry gives its
`plural:` (a brumby: brumbies), and a term plural in sense (the pollies, punters, the olds) is marked
`number: plural` and doesn't stand for one ("a young politician" is never "a young pollies"), except for a body
of people ("the public" -> "the punters", "the dead" -> "the poor buggers"). Also:

- "some" is never dropped ("the next time somebody" is never "the next time bugger").
- A genitive is a determiner ("Parson Walker's missus", not "Walker's the missus").
- A span that opens with its own article keeps the term's ("was a shambles" -> "was a shemozzle").
- A determiner isn't put before a phrase or a name ("in the sticks" -> "in beyond the black stump", "in Woop
  Woop").
- Guard concepts hold "wake the dead" (noise) and "in the dumps" (low spirits) away from the dead and the tip.
- The noun-phrase grammar (kept determiners, phrase ends, number) lives in realise.py, beside the realisation it
  serves, with its own tests (tests/test_noun_phrase.py, which check the bad outputs on every seed).

## Kept as they are

- **Once per text for a multi-word term.** Letting a term back after a gap (six sentences, three uses) was
  tried: the Emperor's New Clothes then said "bugger all" and "sweet bugger-all" six times, and Goldilocks
  gave every "Someone has been..." a different swear, against the style guide's "keep a deliberate pattern".
  The rail is doing its job; reverted.
- The level, vulgarity, register, gate and genre rails are the dials and the dictionary's review decisions,
  working as meant.
- The person-subject rejections left are right: "It was lonely", "the tank may be drained", "the radiator
  jackets are full", "the estimate was too high".

## After

1,264 swaps (from 1,246), 461 spans kept. {poss} rejections 36 -> 12 (the rest are verb phrases with no
subject before them: "Let's sit down", dictionary glosses). Article rejections 31 -> 0, with 12 new and correct
"the phrase goes on" refusals. Person-subject rejections 50 -> 35.
