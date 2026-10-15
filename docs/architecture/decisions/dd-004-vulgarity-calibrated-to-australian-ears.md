# DD-004: Vulgarity calibrated to Australian ears

- **Status:** Accepted; extended by [DD-005](dd-005-orthogonal-level-and-vulgarity.md)
- **Date:** during the initial build; in place by v0.1.0 (2026-10-12, per `CHANGELOG.md`). Recorded
  retrospectively on 2026-10-13 from the old manual's "Decisions on the brief's open questions".

## Context

Australian swearing doesn't map onto American or British ratings. "Bloody" and "bugger" are everyday, and the
c-word, deeply offensive in the US, is often affectionate in Australia ("a good cunt"). A swearing cap rated by
outside standards would either strip out ordinary Australian speech or misjudge the strongest words.

## Decision

Rate every entry's `vulgarity` on a four-tier scale calibrated to Australian ears:

- 0 (`nan`): no swearing.
- 1 (`dad`): mild profanity in everyday use: bloody, bugger, bastard, donger.
- 2 (`uncle-bob`): common but impolite: piss, arse, balls, fuck.
- 3 (`tradie`): strong: the c-word, used the Australian way. Entries in this tier carry a note saying so.

The level sets only a default vulgarity, an explicit vulgarity wins in either direction, and no level defaults
to `tradie`: it has to be asked for.

## Consequences

- Clean output (`nan`) is always available, at any level.
- The strongest tier is opt-in, which protects users who pick a high level without expecting the c-word.
- Ratings are judgements; they are recorded per entry, so they can be reviewed and changed in data.
