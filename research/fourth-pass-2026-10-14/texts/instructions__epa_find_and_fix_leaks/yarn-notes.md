## dinkum

- Wrong-sense planned phrases: "Give a stuff about" for "Pay attention to" (negative-only idiom, and rude as an order to the reader); "rocks up" for "shows up" (a person arriving, not dye appearing in the bowl); "heaps" for "loads" in "60 loads of dishes" (a count of dishwasher loads, not "lots").
- Engine draft also put "bloody" on "a good seal" in an instructions text; harmless at vulgarity 1 but odd in an EPA guide.
- Lint flagged my "a doddle" as `dubious_meaning` (fair: British more than Australian); swapped for "dead easy".
- Lint false positive: `repeated_phrase` "gallons about litres" (5 times): that's the metric-in-brackets the system prompt asks for, not a repeated slang phrase.
- Brief didn't flag that "a colder month, such as January or February" is summer in Australia; kept as the original says (instructions keep facts), but a localising rewrite could trip on it.

## troppo

- Same wrong-sense phrases declined ("Give a stuff about", "rocks up"); used "heaps" in its right sense ("heaps of tutorials").
- Riff "out the back with a redback under the seat" for "dunny" doesn't fit: this is an indoor cistern toilet with a flapper; skipped.
- Setting was clear: colour went into reactions ("Every single day!", "One drip a second!", the flush-on-its-own aside), steps and numbers untouched. No lint issues.
