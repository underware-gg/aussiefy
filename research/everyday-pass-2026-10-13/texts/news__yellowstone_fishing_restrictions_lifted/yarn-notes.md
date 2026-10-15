
## Yarn pass (agent, 2026-10-13)

- Accepted on the first submit; the one planned phrase, "creeks" for "streams", fit. Riff "bone dry half the year" not used: it would add a claim about Yellowstone's streams that the notice doesn't make.
- Engine draft broke the news genre: talker openers on paragraphs ("Mate, full fishing closures", "Now, Staff will", "Mind ya, Update:", "Well, the full closures", "Anyway, Staff"), one glued onto a headline. At level 5 the opener riffs should be off for news/notices.
- Lint false positives: warning `repeated` "a bit full" x3, triggered by "full closures" (the draft never says "a bit full"; same bug as in the Ford manual text). name_dropped "Effective Friday" / name_added "From Friday": a sentence-initial capitalised phrase treated as a name.
- Lint suggestion wrong-sense: the adjective "Cooler" (weather) -> "esky".
