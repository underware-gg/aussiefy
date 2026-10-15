# Swearing round, 2026-10-12: level and vulgarity made orthogonal

**The problem.** The two dials were meant to be independent, with level setting only a default vulgarity, but
swearing tracked the level. Swears per 100 words over the reference texts and `sentences.txt`, seeds 0-4
(`sweargrid.py`; in brackets, swears at the tier asked for):

| level | nan | dad | uncle-bob | tradie |
|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0.13 | 0.14 (0.01) | 0.14 (0) |
| 5 | 0 | 1.25 | 1.63 (0.40) | 1.65 (0.02) |

Three things tied swearing to the level:
1. Rude entries' minimum level (`incoherence`) was set by rudeness: every f-word and c-word entry needed level 5.
2. Sweary openers and closers came with the level's garnish, which is off below level 4.
3. The swear infixes were drawl rules with `min_level: 5`.

**The fix.**
- **A.** 65 rude entries were re-tagged so their level says how hard they are to follow, judged against clean
  entries for the same concept and frame, never by how rude they are. `fuck me`, `piss off` and `prick` moved
  to 2; similes like "a hatful of arseholes" stayed at 4-5. Round-owned entries carry the change in their
  round's `entry_fixes.yaml`.
- **B.** Swearing became its own channel. `profiles.yaml` `swearing:` sets, by vulgarity, the rate of sweary
  garnish, closers and infixes, and a lean on rude swaps. The level's garnish is clean. A swear a tier below
  the one asked for comes through at half strength.
- **C.** 71 plain-word swears were added in `entries/swearing.yaml`, with three `fuckin'` infixes, an "as
  fuck" post-intensifier rule (`hot as fuck`) and seven new concepts (`NOBODY`, `BACKSIDE`, and the people
  `LEGEND`, `FUNNY_PERSON`, `WILD_ONE`, `SHADY_PERSON`, `CLEVER_PERSON`). They were drawn from three unharnessed "swearing like a dockie" retellings by subagents
  (`retellings/`, `*_terms.yaml`: 150 terms, 96 new to the dictionary). Terms the retellings marked doubtful,
  or that aren't distinctively Australian, were left out.

**After:**

| level | nan | dad | uncle-bob | tradie |
|---|---|---|---|---|
| 1 | 0 | 0.56 | 1.26 (0.62) | 1.47 (0) |
| 2 | 0 | 0.98 | 1.68 (0.69) | 1.94 (0.03) |
| 3 | 0 | 0.95 | 1.66 (0.66) | 2.01 (0.13) |
| 4 | 0 | 0.98 | 1.65 (0.58) | 1.98 (0.12) |
| 5 | 0 | 0.95 | 1.66 (0.59) | 1.99 (0.10) |

Each column is flat across levels 2-5. Level 1 swaps little of anything, so its swears come mostly from the
channel. The c-word stays rare even at `tradie`, because it fits few places. `tests/test_engine.py` pins the
orthogonality.

**Best cunts to worst cunts.** The c-word also describes, and the description carries the verdict. Thirteen
are in the dictionary, best to worst: a sick cunt (a legend), a funny cunt, a good cunt, a mad cunt (fond), a
loose cunt (a wild one), a cooked cunt, a weird cunt, a suss cunt, a dumb cunt, a fucked cunt, a dodgy cunt, a
shit cunt, a dog cunt (one who'd betray you). Each is a `tradie` (3) swap for the plain description it
matches: "a wonderful person" can come out as "a sick cunt", "a con man" as "a dodgy cunt". "A good cunt" and
"a mad cunt" were already in `phrases.yaml`. The milder people ("a funny bugger", "a cheeky bastard", "a
cocky bastard", "a sneaky bastard") cover the same ground at `dad` and `uncle-bob`.

**Left out**, of the retellings' 96 new terms:

- Not distinctively Australian: "holy shit", "Jesus Christ", "the hell".
- One-off constructions that don't fit a slot: "buggered if", "got fuck all on", "good fuckin' riddance",
  "fuck it", "what the fuck to do", "arse first", "shits himself", "full of shit", "mangy old bastard",
  "tight bastard", "ya cunts", "lucky cunts", "ya old bugger".
- Already made by rules or infixes: "absolutely fuckin'", "fuckin' gobsmacked", "out like a bloody light".
- "One ugly bastard" was tried and dropped. It read badly in coordination.

The c-word still comes rarely, even at `tradie`. A swap needs a plain description of a person to replace,
and ordinary prose has few of them.
