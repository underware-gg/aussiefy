# DD-005: Level and vulgarity are orthogonal dials

- **Status:** Accepted; extends [DD-004](dd-004-vulgarity-calibrated-to-australian-ears.md)
- **Date:** 2026-10-12, the swearing round (`research/swearing-2026-10-12/README.md`).

## Context

The two dials were meant to be independent, with the level setting only a default vulgarity, but measurement
showed swearing tracked the level: at level 1 there was none at any vulgarity, and at level 3 a `dad` text got
about 0.13 swears per 100 words against 1.25 at level 5. Three things tied them together. Rude entries'
minimum level was set by rudeness (every f-word and c-word entry needed level 5), sweary openers and closers
came with the level's garnish (off below level 4), and the swear infixes were drawl rules gated at level 5.

## Decision

Make the dials orthogonal. The level is how intensively a text is Aussified; the vulgarity is how rude it may
be and how often the swearing comes.

- An entry's level says how hard it is to follow, never how rude it is; rude entries were re-tagged on that
  basis.
- Swearing is its own channel: `swearing:` in `aussiefy/data/profiles.yaml` sets, per vulgarity, the rate of
  sweary garnish, closers and infixes, and a lean towards rude swaps. The level's own garnish is clean.
- A swear a tier below the one asked for comes through at half strength, so each vulgarity sounds like its
  tier.
- Plain-word swears were added (`aussiefy/data/entries/swearing.yaml`) so every level has rude options.

## Consequences

- Swears per 100 words are flat across levels 2-5 at each vulgarity, so `-l swaggie --vulgarity nan` and
  `-l tourist --vulgarity tradie` both mean what they say.
- Results report both dials, and every surface takes both.
- Swearing rates are tuned in data, per vulgarity, rather than per level.
