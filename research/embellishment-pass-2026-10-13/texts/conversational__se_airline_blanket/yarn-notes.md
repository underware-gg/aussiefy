## deadset

- Wrong-sense planned phrase: "a shocker" for "felt terrible" gives "I felt a shocker"; it's a noun (a terrible thing), not a feeling. Declined, used "felt rotten".
- "flamin'" planned for "very" in "very new" ("flamin' new") reads as annoyance, not degree; I used "dead new" there and kept "flamin' guilty" for "really guilty".
- Lint false positive: `name_dropped` "Naturally" (a sentence-initial adverb read as a name). Fires at every setting.
- Lint suggestion "I dunno" for "no idea" in "having no idea that I was meant to" doesn't fit the grammar.
- Accepted on the first submit.

## dinkum

- Validation false positive: "dead" was planned for "really" (in "really guilty"); I used "dead guilty", but submit rejected it because a "really" I'd added elsewhere ("weren't really with it") counted as the planned "really" still being there. It matches the word anywhere, not the original's span. Rephrased to "weren't all there"; accepted on the second submit.
- Lint suggested "flog" for "pinching it": "pinch" is already everyday Australian for steal, so the suggestion only swaps one for another.
- "a shocker" declined again, same reason.

## troppo

- Lookups that came back empty: "twigged" (twig = cotton on, realise), "cheap as chips", "pinch" (only "nick" and "flog" for "steal"). "nicked" doesn't find "nick" (no inflection handling) and returns "get knotted".
- Lookup "not alert, half asleep" offered "gone walkabout", which is a different sense (gone missing) and a culturally loaded term.
- Lookup "telephone someone" gave "get on the blower" but not plain "ring" / "give someone a ring".
- `name_added` warning for "Irish" in "The Irish mob" (a riff on Aer Lingus); fine at troppo, though the warning doesn't know that.
- Accepted on the first submit. The setting was clear; the guidance on tag-ons ("mate" where someone is spoken to) helped place them.
