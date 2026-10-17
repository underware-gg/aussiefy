"""The test-only pin hook (W2's minimal form): a PassObserver that forces a pick at chosen spots, or leaves a
placed garnish's words out, so a whole re-render can be compared with what the changes builder renders in place."""

from __future__ import annotations

from aussiefy.engine import PassObserver
from aussiefy.select import Candidate


class Pins(PassObserver):
    """picks: {(sentence index, detection start, pattern): entry id}, including an entry the cap rules out (a locked
    option). drop: {(sentence index, placement)} garnish whose words stay out of the text."""

    def __init__(self, dictionary, picks=None, drop=()):
        self.dictionary, self.picks, self.drop = dictionary, dict(picks or {}), set(drop)

    def choose(self, sent, det, keep, choice):
        pinned = self.picks.get((sent.index, det.start, det.pattern))
        if pinned is None:
            return choice
        return next((c for c in keep if c.entry.id == pinned), None) or Candidate(
            self.dictionary.entries[pinned], 0.0, "pinned")

    def placing(self, sentence, placement, entry):
        return (sentence, placement) not in self.drop
