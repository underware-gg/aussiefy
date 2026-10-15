## dinkum

- Accepted on the first submit.
- Wrong-sense planned phrase: "quid" for "bucks" inside "an American might say, 'I need 50 bucks on pump number 1'".
  The line quotes an American, so "bucks" has to stay. The engine also doesn't know that "quid" leans British/dated for dollars. Declined.
- The genre came out as "story" for a travel-guide passage of practical advice (the task gives the same). Instructions
  would have fit better: it carries a warning ("Do not mix them up", the heavy fines).
- Lint warned "name_added: Yanks". That's a false positive: "Yank" is in the dictionary as a common noun for an American.
- Engine draft had "yer bloody using" and "cobber" tagged onto a fact; ignored.
- Lookups that came back empty: "rural" (no "the bush", "out in the sticks" or "the country"); "rent a car" ("hire" is the Aussie word,
  and the US->AU swap didn't catch "renting").
- The suggestion of "the Big Smoke" for "the cities" isn't quite right, since the Big Smoke is one specific big city.

## troppo

- Accepted on the first submit, with "quid" declined again (it sits in a quoted American's line).
- Lint was right on "ya'll" (American; I meant "you'll"), on "a doddle" (flagged dubious_meaning; it's more British anyway), and on my opener
  "Righto, so", which counts as the stock "Right, so" opener.
- False positives from lint's "name_added" check: "European" (from the original's "Europe"), and "Tuesday", which comes from the
  brief's own servo riff ("with a pie that's been in the warmer since Tuesday"). Lint warns about a riff the brief offered.
- The openings ("Fair dinkum, this happened.", "True story, this.") are story openers, and they don't suit a travel guide. That
  follows from the genre being detected as story.
- "doddle" lookup came back empty (it got flagged only at lint).
