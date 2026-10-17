"""The hooks the changes builder reads the engine through (an observer, render-at-spot, the phonetic trace and
garnish replay) watch a translation without changing it: output is byte-identical with and without them, and
each reproduces what the pass did."""

import json
from pathlib import Path

import pytest
from _pins import Pins

from aussiefy.engine import PassObserver, first_replaced
from aussiefy.garnish import place_garnish
from aussiefy.markup import mask

ROOT = Path(__file__).resolve().parents[2]
EVERYDAY = sorted((ROOT / "tests" / "corpus" / "everyday").glob("*/*.txt"))
STRESS = dict(level=5, vulgarity=2, embellishment=2, document_config={"profile": {
    "stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6},
    "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10}, "garnish_gap": 0,
    "swearing": {"infix": 6.0, "exclaim": 0.5}}})
SETTINGS = [dict(level=4, vulgarity=1), dict(level=5, vulgarity=3, embellishment=2), STRESS]


def _texts(n=2000, every=4):
    return [p.read_text(encoding="utf-8")[:n] for p in EVERYDAY[::every]]


def _same(a, b):
    return a.text == b.text and json.dumps(a.to_dict(), default=str) == json.dumps(b.to_dict(), default=str)


class Recorder(PassObserver):
    """Keeps everything the hooks report (each spot is a snapshot the rest of the pass leaves alone)."""

    def __init__(self):
        self.spots, self.sentences, self.placed, self.trace = [], [], [], None

    def begin(self, run):
        self.run = run

    def spot(self, spot):
        self.spots.append(spot)

    def garnish(self, sentence, entry, form, edit, offer):
        self.placed.append((sentence, offer.placement, form, edit))
        assert entry in offer.pool and offer.words(entry) == form, "the offer the engine picked from"

    def sentence(self, trace):
        self.sentences.append(trace)

    def phonetic(self, joined, trace, final):
        self.joined, self.trace, self.final = joined, trace, final


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("seed", [0, 7])
def test_an_observer_leaves_the_translation_byte_identical(translator, settings, seed):
    for text in _texts():
        assert _same(translator.translate(text, seed=seed, **settings),
                     translator.translate(text, seed=seed, _observer=Recorder(), **settings))


def test_an_observer_leaves_masked_markup_byte_identical(translator):
    text = "Here's [a link](http://x.au) and `code`. I'm very tired, my friend, and the toilet is broken."
    for settings in SETTINGS:
        plain = translator.translate(text, _protected=mask(text, "markdown"), **settings)
        watched = translator.translate(text, _protected=mask(text, "markdown"), _observer=Recorder(), **settings)
        assert _same(plain, watched)


def test_render_at_spot_on_a_copy_of_the_state_gives_the_pick(translator):
    """The builder renders each option at a spot on a copy of the state there; for the pick, that is exactly what
    the pass put in."""
    from dataclasses import replace

    checked = 0
    for text in _texts(every=3):
        for settings in SETTINGS:
            seen = Recorder()
            translator.translate(text, _observer=seen, **settings)
            for spot in (s for s in seen.spots if s.rec.substituted):
                got = translator.render_at_spot(spot.rec.chosen, spot, replace(seen.run, state=spot.state.copy()))
                assert (got.text, got.term, got.riff) == (spot.rec.output, spot.rec.term, spot.rec.riff)
                assert (got.stacked and got.stacked.entry.id) == (spot.rec.stacked and spot.rec.stacked.entry.id)
                checked += 1
    assert checked > 50


def test_the_phonetic_trace_replays_each_rule_pass(translator):
    for text in _texts():
        seen = Recorder()
        r = translator.translate(text, _observer=seen, **STRESS)
        text_now = seen.joined
        fired = 0
        for p in seen.trace.passes:
            assert p.before == text_now and p.starts == sorted(p.starts) and len(p.starts) == len(p.ends)
            for start, end, n in reversed(p.edits):
                assert start in p.starts
                text_now = text_now[:start] + "\0" * n + text_now[end:]
            fired += len(p.edits)
            text_now = _next_before(seen.trace.passes, p, seen.final)
        assert fired == len(r.phonetic) and text_now == seen.final


def _next_before(passes, p, final):
    i = passes.index(p)
    return passes[i + 1].before if i + 1 < len(passes) else final


@pytest.mark.parametrize("placement, form, text, words", [
    ("opener", "strewth", "The bloke left.", "Strewth, "),
    ("connective", "anyway", "She found it.", "Anyway, "),
    ("tag", "mate", "Pass the salt.", ", mate"),
    ("tag", "mate", '"Hand it over." he said.', ", mate"),
    ("tail", "the whole box and dice", "We took the tent, chairs and esky.", ", the whole box and dice"),
    ("aside", "fair dinkum", "It was big", ". Fair dinkum."),
    ("closer", "that's my two bob's worth", "That's it.  ", " That's my two bob's worth."),
])
def test_placed_garnish_says_where_its_words_went(placement, form, text, words):
    new, (start, end, n) = place_garnish(text, placement, form, frozenset({"the", "she"}))
    assert start == end and new[start:start + n] == words
    assert (new[:start] + new[start + n:]).lower() == text.lower()


def test_garnish_replay_reproduces_each_sentence(translator):
    replayed = 0
    for text in _texts():
        for settings in SETTINGS:
            seen = Recorder()
            translator.translate(text, _observer=seen, **settings)
            for st in seen.sentences:
                ops = [(p, f) for s, p, f, _ in seen.placed if s == st.sent.index and p != "closer"]
                first = first_replaced(st.records, st.sent.tokens)
                out, edits = translator.replay_garnish(st.spliced, st.sent, seen.run, ops, first)
                assert out == st.garnished and None not in edits
                assert edits == [e for s, p, _, e in seen.placed if s == st.sent.index and p != "closer"]
                replayed += len(ops)
    assert replayed > 20


def test_pins_force_a_pick_and_leave_out_a_garnish(translator, dictionary):
    text = "I'm exhausted and the toilet is broken. Thanks for breakfast, my friend."
    seen = Recorder()
    base = translator.translate(text, level=5, seed=0, _observer=seen)
    spot = next(s for s in seen.spots if s.rec.substituted and len(s.keep) > 1)
    other = next(c.entry.id for c in spot.keep if c.entry.id != spot.rec.chosen.entry.id)
    pinned = translator.translate(text, level=5, seed=0, _observer=Pins(
        dictionary, {(spot.sent.index, spot.rec.det.start, spot.rec.det.pattern): other}))
    assert [r.chosen.entry.id for r in pinned.records if r.det.start == spot.rec.det.start
            and r.sentence == spot.sent.index] == [other]
    placed = [(g.sentence, g.placement) for g in base.garnish if g.entry_id and g.placement != "riff"]
    if placed:
        dropped = translator.translate(text, level=5, seed=0, _observer=Pins(dictionary, drop=placed[:1]))
        assert dropped.text != base.text


def test_a_copy_of_the_state_copies_every_field():
    """The builder spends from a copy of the state at each spot; nothing it does may reach the pass's own."""
    from collections import Counter
    from dataclasses import fields

    from aussiefy.engine import TextState

    state = TextState()
    for f in fields(state):
        value = getattr(state, f.name)
        value.update({"x": 1} if isinstance(value, (dict, Counter)) else {"x"})
    copy = state.copy()
    assert copy == state
    for f in fields(copy):
        value = getattr(copy, f.name)
        value.update({"y": 2} if isinstance(value, (dict, Counter)) else {"y"})
        assert "y" not in getattr(state, f.name), f.name


def test_an_observer_gets_a_snapshot_of_each_spot(translator):
    """What an observer keeps of a spot is what the spot was: the rest of the pass leaves it as it was."""
    text = "I'm exhausted and the toilet is broken. You are very tired and hungry, and your car is broken."
    seen = Recorder()
    translator.translate(text, level=5, vulgarity=2, _observer=seen)
    spots = [s for s in seen.spots if s.rec.substituted]
    later = [s for s in spots if s.sent.index == spots[-1].sent.index]
    assert len(later) >= 2 and not later[0].replaced and later[-1].replaced
    assert sum(later[0].state.entry_uses.values()) < sum(later[-1].state.entry_uses.values())
