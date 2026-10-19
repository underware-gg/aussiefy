"""Each rendering the changes builder returns is what the engine puts there: a whole re-render with that pick pinned
(tests/_pins.py) has the same text over the spot's region. The rest of the output may differ from the pinned
re-render (later picks and phonetic rolls shift): a swap is local by design (DD-029)."""

from pathlib import Path

import pytest
from _pins import Pins

from aussiefy import changes as C
from aussiefy.markdown import document_changes
from aussiefy.markup import mask
from aussiefy.policy import resolve

ROOT = Path(__file__).resolve().parents[2]
EVERYDAY = sorted((ROOT / "tests" / "corpus" / "everyday").glob("*/*.txt"))
STRESS = dict(level=5, vulgarity=2, embellishment=2, document_config={"profile": {
    "stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6},
    "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10}, "garnish_gap": 0,
    "swearing": {"infix": 6.0, "exclaim": 0.5}}})
SETTINGS = {"larrikin-dad": dict(level=4, vulgarity=1), "swaggie-tradie-troppo": dict(level=5, vulgarity=3, embellishment=2),
            "stress": STRESS}
# ... and the website's Swaggie, where it found a garnish region reaching into a swap (test_changes.py's FAUCET)
COVERS_SETTINGS = {**SETTINGS, "swaggie-dad-dinkum": dict(level=5, vulgarity=1, embellishment=1)}
# State-dependent adjacent swaps must be explicitly reviewed. The former stacked-entry exceptions no
# longer occur with clause-boundary constraints; no exceptions currently remain. Any new one fails.
SHIFTED_PAIRS = set()


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


def _spots(watch, result, builder, translator):
    """Each substitution change (with its id) with its spot and its region's tokens, and what finish() withheld."""
    cs = C.finish(result, builder.drafts(), translator.dictionary)
    for c in (c for c in cs.changes if c["kind"] == "substitution"):
        spot = next(s for s in watch.spots if s.rec.substituted
                    and c["src_span"][0] <= s.rec.span[0] and s.rec.span[1] <= c["src_span"][1])
        toks = spot.sent.tokens
        start = next(i for i, t in enumerate(toks) if t.start == c["src_span"][0])
        end = next(i for i, t in enumerate(toks) if t.end == c["src_span"][1]) + 1
        yield c, spot, start, end, cs.withheld


def _region(translator, text, options, pins, sentence, start, end):
    """The text over a region's tokens in a pinned re-render, mapped through its own passes."""
    watch, result, builder = _build(translator, text, options, Pinned(translator.dictionary, **pins))
    a, b = builder._base_region(builder.sentences[sentence], start, end).final
    return result.text[a:b]


@pytest.mark.parametrize("seed", [0, 7])
@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_every_alternative_and_locked_option_is_the_pinned_re_render(translator, setting, seed):
    options, checked = {**SETTINGS[setting], "seed": seed}, 0
    shown = {"stack": 0, "riff": 0, "infix": 0}
    d = translator.dictionary
    for path in EVERYDAY:
        text = cut(path.read_text(encoding="utf-8"))
        watch, result, builder = _build(translator, text, options)
        for c, spot, start, end, withheld in _spots(watch, result, builder, translator):
            assert not withheld, (path.name, withheld)
            assert c["output"] == result.text[slice(*c["out_span"])]
            pick = next(o for o in c["alternatives"] if o["entry_id"] == c["entry_id"])
            assert pick["rendered"] == c["output"], (path.name, c["id"])
            key = (spot.sent.index, spot.rec.det.start, spot.rec.det.pattern)
            for o in c["alternatives"] + c["locked"]:
                entry = d.entries[o["entry_id"]]
                riffed = any(r.text in o["rendered"] for r in entry.riffs)
                shown["riff"] += riffed
                shown["infix"] += o["vulgarity"] > entry.vulgarity
                shown["stack"] += o["rendered"].count(", ") > riffed
                if o["entry_id"] == c["entry_id"]:
                    continue
                got = _region(translator, text, options, {"picks": {key: o["entry_id"]}}, spot.sent.index, start, end)
                assert o["rendered"] == got, (path.name, c["id"], o["entry_id"])
                checked += 1
    assert checked > 50
    if setting != "larrikin-dad":   # the hard paths: stacked idioms, riffs, infixes in a spot
        assert min(shown.values()) >= 3, shown


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
                draft = builder._closer() if k < 0 else builder._garnish(builder.sentences[sentence], k)
                c = draft.change
                assert not draft.withheld, (path.name, seed, c["placement"], draft.withheld)
                a, _ = c["removed"]["out_span"]
                got = translator.translate(text, **options, _observer=Pinned(
                    translator.dictionary, drop={(sentence, op.placement)})).text
                assert got[:a + len(c["removed"]["rendered"])] == result.text[:a] + c["removed"]["rendered"]
                words = {e.id: op.offer.words(e) for e in op.offer.pool}
                for o in [o for o in c["alternatives"] if o["entry_id"] != op.entry.id][:2]:   # two an op bounds it
                    got = translator.translate(text, **options, _observer=Pinned(
                        translator.dictionary, words={(sentence, op.placement): words[o["entry_id"]]})).text
                    a, _ = o["out_span"]
                    assert got[:a + len(o["rendered"])] == result.text[:a] + o["rendered"], (path.name, c["placement"])
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
    first reads as rendered, and so does the second. SHIFTED_PAIRS would record reviewed state-dependent
    exceptions; it is currently empty."""
    pairs, shifted = 0, set()
    for path, seed in ((path, seed) for path in EVERYDAY for seed in (0, 7)):
        text, options = cut(path.read_text(encoding="utf-8")), {**SETTINGS[setting], "seed": seed}
        watch, result, builder = _build(translator, text, options)
        spots = [s for s in _spots(watch, result, builder, translator)
                 if any(o["entry_id"] != s[0]["entry_id"] for o in s[0]["alternatives"])]
        for one, two in zip(spots, spots[1:]):
            if two[1].sent.index - one[1].sent.index > 1:
                continue
            assert one[0]["out_span"][1] <= two[0]["out_span"][0]
            chosen = [(c, spot, start, end, next(o for o in c["alternatives"] if o["entry_id"] != c["entry_id"]))
                      for c, spot, start, end, _ in (one, two)]
            picks = {(spot.sent.index, spot.rec.det.start, spot.rec.det.pattern): o["entry_id"]
                     for c, spot, start, end, o in chosen}
            pinned_watch, pinned, pinned_builder = _build(translator, text, options,
                                                          Pinned(translator.dictionary, picks))
            for n, (c, spot, start, end, o) in enumerate(chosen):
                a, b = pinned_builder._base_region(pinned_builder.sentences[spot.sent.index], start, end).final
                if pinned.text[a:b] != o["rendered"]:
                    there = next(s for s in pinned_watch.spots if s.rec.span == spot.rec.span)
                    assert n and _state(there) != _state(spot), (path.name, c["id"], o["entry_id"])
                    shifted.add((setting, path.name, seed))
            pairs += 1
    assert pairs > 8
    assert shifted == {p for p in SHIFTED_PAIRS if p[0] == setting}


def _regions(change):
    """The regions a change's alternatives, locked options and removal replace."""
    regions = [o["out_span"] for o in change["alternatives"] + change["locked"]]
    return regions + ([change["removed"]["out_span"]] if change.get("removed") else [])


def _overlap(x, y):
    return x[0] < y[1] and y[0] < x[1]


def _check_covers(changes, where) -> int:
    """What covers must hold, whatever builds it: each region takes in its change's output; a change with no region
    covers nothing; covers is in output order; a change covers every other whose (non-empty) output one of its
    regions overlaps, and nothing that shares no text with its regions; and two changes with regions cover each
    other or neither. Returns how many covers are region to region only (the covered change's output lies outside
    every region of the one covering it)."""
    order = {c["id"]: k for k, c in enumerate(changes)}
    by_id = {c["id"]: c for c in changes}
    region_only = 0
    for c in changes:
        regions, (a, b) = _regions(c), c["out_span"]
        assert all(lo <= a <= b <= hi for lo, hi in regions), (where, c["id"])
        if not regions:
            assert c["covers"] == [], (where, c["id"])
            continue
        at = [order[i] for i in c["covers"]]
        assert at == sorted(set(at)) and c["id"] not in c["covers"], (where, c["id"])
        for d in changes:
            if d is not c and d["out_span"][0] < d["out_span"][1] and any(_overlap(r, d["out_span"]) for r in regions):
                assert d["id"] in c["covers"], (where, c["id"], d["id"])
        for d in map(by_id.get, c["covers"]):
            assert not _regions(d) or c["id"] in d["covers"], (where, c["id"], d["id"])
            near = [d["out_span"], *_regions(d)]   # nothing far away: it shares text with a region, or sits in one
            assert any(_overlap(r, x) or r[0] < x[0] == x[1] < r[1] for r in regions for x in near), (where, c["id"])
            region_only += not any(_overlap(r, d["out_span"]) for r in regions)
    return region_only


@pytest.mark.parametrize("setting", sorted(COVERS_SETTINGS))
def test_covers_holds_over_the_everyday_corpus(translator, setting):
    """Swapping a change rewrites the text of every change it covers, so a page knows what a swap disturbs. Through
    their regions, renders of neighbouring spots are independent or listed as covering each other (the state one
    swap leaves for the next is another matter: SHIFTED_PAIRS). Each setting has a pair whose regions alone
    overlap: a garnish region that took in a whole swap, which covers the garnish back."""
    region_only = 0
    for path, seed in ((path, seed) for path in EVERYDAY for seed in (0, 7)):
        cs = C.build(translator, cut(path.read_text(encoding="utf-8")), **COVERS_SETTINGS[setting], seed=seed)
        region_only += _check_covers(cs.changes, (path.name, seed))
    assert region_only >= 1


def test_alternatives_in_masked_markup_are_the_pinned_re_render(translator):
    """The markup route: protected spans masked through the pass and restored after (the same length), so the
    builder's offsets and renderings hold there too."""
    text = ("I'm exhausted and the toilet is broken, see `make fix` and <b>the shed</b>. "
            "You are very tired and hungry, my friend, and [your car](http://x.au) is broken.")
    options = dict(level=5, vulgarity=2, embellishment=2, _protected=mask(text, "markdown"))
    watch, result, builder = _build(translator, text, options)
    checked = 0
    for c, spot, start, end, _ in _spots(watch, result, builder, translator):
        key = (spot.sent.index, spot.rec.det.start, spot.rec.det.pattern)
        for o in c["alternatives"] + c["locked"]:
            if o["entry_id"] != c["entry_id"]:
                assert o["rendered"] == _region(translator, text, options, {"picks": {key: o["entry_id"]}},
                                                spot.sent.index, start, end)
                checked += 1
    assert checked > 5 and "`make fix`" in result.text


DOCUMENT = ("# Notes\n\nI'm exhausted and the toilet is broken. See `make test` and [the docs](http://x.au/a_b).\n\n"
            "Then we lost the tent, the chairs and the esky (really)! You are very tired and hungry, my friend.\n\n"
            "- Your car is broken.\n- The faucet in my apartment is broken, mate.\n")


@pytest.mark.parametrize("seed", [0, 3])
def test_the_document_route_is_the_pinned_re_render(translator, seed):
    """A Markdown document's changes, units composed and escaped: each swap, garnish removal and garnish swap reads
    in the document as a whole re-render with it pinned inside its unit (the watch hook) has it."""
    policy = translator.policy(level=5, seed=seed, vulgarity=2, embellishment=2, english="us",
                               document_config=STRESS["document_config"])
    effective = resolve(policy, translator.dictionary)
    units: list = []

    def watch(i):
        units.append(C.Watch())
        return units[i]

    base = document_changes(DOCUMENT, translator, policy, effective, _watch=watch)

    def pinned(unit, **pins):
        return document_changes(DOCUMENT, translator, policy, effective,
                                _watch=lambda i: Pinned(translator.dictionary, **pins) if i == unit else C.Watch())

    checked = {"substitution": 0, "removed": 0, "garnish": 0}
    for i, w in enumerate(units):
        offset = base.result.units[i].source_span[0]
        for spot in (s for s in w.spots if s.rec.substituted):
            key = (spot.sent.index, spot.rec.det.start, spot.rec.det.pattern)
            c = next(c for c in base.changes if c["kind"] == "substitution"
                     and c["src_span"][0] <= offset + spot.rec.span[0] < c["src_span"][1])
            for o in c["alternatives"] + c["locked"]:
                if o["entry_id"] != c["entry_id"]:
                    again = {d["id"]: d for d in pinned(i, picks={key: o["entry_id"]}).changes}
                    assert again[c["id"]]["output"] == o["rendered"], (c["id"], o["entry_id"])
                    checked["substitution"] += 1
        garnish = [c for c in base.changes if c["kind"] == "garnish" and c.get("placement") != "riff"
                   and base.result.units[i].output_span[0] <= c["out_span"][0] <= base.result.units[i].output_span[1]]
        for sentence, ops in w.ops.items():
            for op in ops:
                c = next(c for c in garnish if c["placement"] == op.placement and c["entry_id"] == op.entry.id)
                assert c["id"] not in {x["id"] for x in base.withheld}, (c["id"], base.withheld)
                a, _ = c["removed"]["out_span"]
                got = pinned(i, drop={(sentence, op.placement)}).text
                assert got[:a + len(c["removed"]["rendered"])] == base.text[:a] + c["removed"]["rendered"], c["id"]
                checked["removed"] += 1
                o = next((o for o in c["alternatives"] if o["entry_id"] != op.entry.id), None)
                if o is not None:
                    other = next(e for e in op.offer.pool if e.id == o["entry_id"])
                    got = pinned(i, words={(sentence, op.placement): op.offer.words(other)}).text
                    a, _ = o["out_span"]
                    assert got[:a + len(o["rendered"])] == base.text[:a] + o["rendered"], c["id"]
                    checked["garnish"] += 1
    assert min(checked.values()) >= 1, checked
    _check_covers(base.changes, ("document", seed))
