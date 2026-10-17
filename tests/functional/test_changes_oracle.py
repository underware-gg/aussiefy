"""Each rendering the changes builder returns is what the engine puts there: a whole re-render with that pick pinned
(tests/_pins.py) has the same text over the spot's region. The rest of the output may differ from the pinned
re-render (later picks and phonetic rolls shift): a swap is local by design (DD-029)."""

from pathlib import Path

import pytest
from _pins import Pins

from aussiefy import changes as C
from aussiefy.markup import mask

ROOT = Path(__file__).resolve().parents[2]
EVERYDAY = sorted((ROOT / "tests" / "corpus" / "everyday").glob("*/*.txt"))
STRESS = dict(level=5, vulgarity=2, embellishment=2, document_config={"profile": {
    "stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6},
    "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10}, "garnish_gap": 0,
    "swearing": {"infix": 6.0, "exclaim": 0.5}}})
SETTINGS = {"larrikin-dad": dict(level=4, vulgarity=1), "swaggie-tradie-troppo": dict(level=5, vulgarity=3, embellishment=2),
            "stress": STRESS}


class Pinned(Pins, C.Watch):
    """The builder's watch with the test-only pins: a pinned re-render the oracle reads regions from."""


def cut(text: str, n: int = 2000) -> str:
    if len(text) <= n:
        return text
    head = text[:n]
    k = max(head.rfind(". "), head.rfind(".\n"), head.rfind("? "), head.rfind("! "))
    return head[:k + 1] if k > n // 2 else head


def _build(translator, text, options, watch=None):
    watch = watch or C.Watch()
    result = translator.translate(text, **options, _observer=watch)
    return watch, result, C._Builder(translator, watch, result)


def _spots(watch, builder):
    """Each substitution change with its spot and its region's tokens."""
    for c in (c for c in builder.changes() if c["kind"] == "substitution"):
        spot = next(s for s in watch.spots if s.rec.substituted
                    and c["src_span"][0] <= s.rec.span[0] and s.rec.span[1] <= c["src_span"][1])
        toks = spot.sent.tokens
        start = next(i for i, t in enumerate(toks) if t.start == c["src_span"][0])
        end = next(i for i, t in enumerate(toks) if t.end == c["src_span"][1]) + 1
        yield c, spot, start, end


def _region(translator, text, options, pins, sentence, start, end):
    """The text over a region's tokens in a pinned re-render, mapped through its own passes."""
    watch, result, builder = _build(translator, text, options, Pinned(translator.dictionary, **pins))
    a, b = builder._base_region(builder.sentences[sentence], start, end).final
    return result.text[a:b]


@pytest.mark.parametrize("seed", [0, 7])
@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_every_alternative_and_locked_option_is_the_pinned_re_render(translator, setting, seed):
    options, checked = {**SETTINGS[setting], "seed": seed}, 0
    for path in EVERYDAY:
        text = cut(path.read_text(encoding="utf-8"))
        watch, result, builder = _build(translator, text, options)
        for c, spot, start, end in _spots(watch, builder):
            assert c["output"] == result.text[slice(*c["out_span"])]
            pick = next(o for o in c["alternatives"] if o["entry_id"] == c["entry_id"])
            assert pick["rendered"] == c["output"], (path.name, c["id"])
            key = (spot.sent.index, spot.rec.det.start, spot.rec.det.pattern)
            for o in c["alternatives"] + c["locked"]:
                if o["entry_id"] == c["entry_id"]:
                    continue
                got = _region(translator, text, options, {"picks": {key: o["entry_id"]}}, spot.sent.index, start, end)
                assert o["rendered"] == got, (path.name, c["id"], o["entry_id"])
                checked += 1
    assert checked > 50


@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_every_garnish_removal_and_alternative_is_the_pinned_re_render(translator, setting):
    """Garnish removed (the pin hook leaves it out) or swapped (it says another's words) reads as the builder
    renders it, with everything before it unchanged."""
    checked = 0
    for path in EVERYDAY[::4]:
        text = cut(path.read_text(encoding="utf-8"))
        for seed in (0, 7):
            options = {**SETTINGS[setting], "seed": seed}
            watch, result, builder = _build(translator, text, options)
            ops = [(s.trace.sent.index, k, s.ops[k]) for s in builder.sentences for k in range(len(s.ops))]
            if watch.closer:
                ops.append((len(builder.sentences) - 1, -1, watch.closer))
            for sentence, k, op in ops:
                c = builder._closer() if k < 0 else builder._garnish(builder.sentences[sentence], k)
                a, _ = c["removed"]["out_span"]
                got = translator.translate(text, **options, _observer=Pinned(
                    translator.dictionary, drop={(sentence, op.placement)})).text
                assert got[:a + len(c["removed"]["rendered"])] == result.text[:a] + c["removed"]["rendered"]
                words = {e.id: form for e, form, _ in builder._pool(sentence, op)}
                for o in [o for o in c["alternatives"] if o["entry_id"] != op.entry.id][:2]:   # two an op bounds it
                    got = translator.translate(text, **options, _observer=Pinned(
                        translator.dictionary, words={(sentence, op.placement): words[o["entry_id"]]})).text
                    a, _ = o["out_span"]
                    assert got[:a + len(o["rendered"])] == result.text[:a] + o["rendered"], (path.name, c["id"])
                    checked += 1
    assert checked > 50


def _state(spot):
    """What a spot's rendering reads from earlier in the text: used entries (repeats, stack and once-a-text
    eligibility), riffs, spellings and imagery."""
    st = spot.state
    return (dict(st.entry_uses), st.riffed, st.riffed_sentences, dict(st.spellings), st.imagery_used,
            dict(st.last_placed))


@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_adjacent_swaps_agree_with_a_pinned_re_render(translator, setting):
    """Two swaps in one sentence, or in neighbouring ones, both pinned at once: their regions don't touch, the
    first reads as rendered, and so does the second wherever the first leaves the state it reads alone. Where it
    doesn't (the first swap used an entry the second's stack or riff would have), the second can read otherwise:
    the accepted locality of a swap (later picks shift), which these pairs count."""
    pairs, shifted = 0, 0
    for path, seed in ((path, seed) for path in EVERYDAY for seed in (0, 7)):
        text, options = cut(path.read_text(encoding="utf-8")), {**SETTINGS[setting], "seed": seed}
        watch, result, builder = _build(translator, text, options)
        spots = [s for s in _spots(watch, builder)
                 if any(o["entry_id"] != s[0]["entry_id"] for o in s[0]["alternatives"])]
        for one, two in zip(spots, spots[1:]):
            if two[1].sent.index - one[1].sent.index > 1:
                continue
            assert one[0]["out_span"][1] <= two[0]["out_span"][0]
            chosen = [(c, spot, start, end, next(o for o in c["alternatives"] if o["entry_id"] != c["entry_id"]))
                      for c, spot, start, end in (one, two)]
            picks = {(spot.sent.index, spot.rec.det.start, spot.rec.det.pattern): o["entry_id"]
                     for c, spot, start, end, o in chosen}
            pinned_watch, pinned, pinned_builder = _build(translator, text, options,
                                                          Pinned(translator.dictionary, picks))
            for n, (c, spot, start, end, o) in enumerate(chosen):
                a, b = pinned_builder._base_region(pinned_builder.sentences[spot.sent.index], start, end).final
                there = next(s for s in pinned_watch.spots if s.rec.span == spot.rec.span)
                if n and _state(there) != _state(spot) and pinned.text[a:b] != o["rendered"]:
                    shifted += 1
                    continue
                assert pinned.text[a:b] == o["rendered"], (path.name, c["id"], o["entry_id"])
            pairs += 1
    assert pairs > 8 and shifted <= pairs // 4


def test_alternatives_in_masked_markup_are_the_pinned_re_render(translator):
    """The markup route: protected spans masked through the pass and restored after (the same length), so the
    builder's offsets and renderings hold there too."""
    text = ("I'm exhausted and the toilet is broken, see `make fix` and <b>the shed</b>. "
            "You are very tired and hungry, my friend, and [your car](http://x.au) is broken.")
    options = dict(level=5, vulgarity=2, embellishment=2, _protected=mask(text, "markdown"))
    watch, result, builder = _build(translator, text, options)
    checked = 0
    for c, spot, start, end in _spots(watch, builder):
        key = (spot.sent.index, spot.rec.det.start, spot.rec.det.pattern)
        for o in c["alternatives"] + c["locked"]:
            if o["entry_id"] != c["entry_id"]:
                assert o["rendered"] == _region(translator, text, options, {"picks": {key: o["entry_id"]}},
                                                spot.sent.index, start, end)
                checked += 1
    assert checked > 5 and "`make fix`" in result.text
