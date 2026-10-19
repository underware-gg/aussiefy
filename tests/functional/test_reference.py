"""Property tests over famous public-domain texts (tests/corpus/reference/).

- gettysburg.txt: formal prose with almost nothing to translate. Tests false positives.
- goldilocks.txt: a plain retelling written for this corpus, dense with translatable states. Tests hit rate.
- hare_and_tortoise.txt: Aesop in Townsend's 1867 Victorian English. Tests archaic syntax.
- waltzing_matilda.txt: already Australian verse. Tests that existing slang and line structure survive.
"""

import functools
import re
from pathlib import Path

import pytest
from _checks import assert_well_formed

REF = Path(__file__).parents[1] / "corpus" / "reference"
TEXTS = {p.stem: p.read_text(encoding="utf-8") for p in sorted(REF.glob("*.txt"))}
SEEDS = range(20)


@pytest.fixture(scope="session")
def translated(translator):
    """translated(name, level, seed): TEXTS[name] translated once a session, since several tests sweep the same
    texts, levels and seeds. This historical benchmark explicitly uses Auto. Results are read, never changed."""
    @functools.cache
    def get(name, level, seed):
        return translator.translate(TEXTS[name], level=level, seed=seed, document_type="auto")
    return get


def runs(translated, name, levels=range(1, 6), seeds=SEEDS):
    for level in levels:
        for seed in seeds:
            yield level, seed, translated(name, level, seed)


def changed_words(a: str, b: str) -> int:
    import difflib
    sm = difflib.SequenceMatcher(a=a.split(), b=b.split(), autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")


@pytest.mark.parametrize("name", sorted(TEXTS))
def test_well_formed_at_every_level(translated, name):
    for level, seed, r in runs(translated, name):
        assert_well_formed(TEXTS[name], r, f"{name} L{level} s{seed}")


# The meanings the Gettysburg Address really contains. Anything else is a misreading.
GETTYSBURG_SENSES = {"LONG_AGO", "FATHER", "FREEDOM", "MAN", "WAR", "ENDURE", "FIELD", "DIE", "REASONABLE",
                     "SOLDIERS", "STRUGGLE", "PEOPLE", "WORK", "SANCTIFY", "COMMITTED", "DEVOTION", "RESOLVE",
                     "NATION", "HEREABOUTS", "FOUND", "IN_THE_MIDDLE", "GOD_WILLING", "EQUALITY", "DEAD_PEOPLE",
                     "ALIVE", "BRAND_NEW", "LIVE_ON", "IN_THE_END", "SECOND_CHANCE", "IN_VAIN", "BRAVE"}


def test_gettysburg_only_its_real_meanings(translated):
    src = TEXTS["gettysburg"]
    for level, seed, r in runs(translated, "gettysburg"):
        for x in r.records:
            if x.substituted:
                assert set(x.det.concepts) & GETTYSBURG_SENSES, f"L{level} s{seed}: misread {x.text!r} -> {x.output!r}"
        assert not re.search(r"(ripper|beaut|grouse|bonza|bonzer) (civil|battle|task)", r.text)
        assert "battle-field" in r.text, "hyphenated compounds stay whole"
        assert " A fair go" not in r.text, "mid-sentence capitals don't carry over"
        if level <= 2:
            assert changed_words(src, r.text) <= len(src.split()) * 0.05, f"L{level} s{seed}: too much at a low level"


def test_gettysburg_level_five_covers_most_meanings(translated):
    for seed in SEEDS:
        r = translated("gettysburg", 5, seed)
        hit = {c for x in r.records if x.substituted for c in x.det.concepts} & GETTYSBURG_SENSES
        assert len(hit) >= 15, f"s{seed}: only {sorted(hit)}"
        # Full drawl contracts ordinary auxiliaries; shall retains its modal force (DD-026).
        assert not re.search(r"\b(can not|we are|it is|we have come)\b", r.text), r.text
        assert len(re.findall(r"\bshall\b", r.text)) == len(re.findall(r"\bshall\b", TEXTS['gettysburg']))


def test_drawl_starts_at_level_four(translated):
    for seed in SEEDS:
        assert "can not" in translated("gettysburg", 3, seed).text
    l4 = [translated("gettysburg", 4, s).text for s in SEEDS]
    assert any("can't" in t for t in l4) and any("can not" in t for t in l4), "level 4 drawls about half the time"


def test_waltzing_matilda_keeps_its_own_slang(translated):
    keep = ["swagman", "billabong", "coolibah", "jumbuck", "tucker bag", "squatter", "troopers", "billy",
            "Matilda"]
    for level, seed, r in runs(translated, "waltzing_matilda"):
        for word in keep:
            assert word in r.text, f"L{level} s{seed}: lost {word!r}"
        assert not [x for x in r.records if x.substituted], f"L{level} s{seed}: nothing here needs translating"


def test_goldilocks_hit_rate_rises_with_level(translated):
    def mean_swaps(level):
        rs = [translated("goldilocks", level, s) for s in SEEDS]
        return sum(len([x for x in r.records if x.substituted]) for r in rs) / len(rs)
    means = [mean_swaps(level) for level in range(1, 6)]
    assert means == sorted(means), means
    assert means[0] >= 1 and means[4] >= 6, means


def test_goldilocks_senses(translated):
    for level, seed, r in runs(translated, "goldilocks"):
        assert "sheila" not in r.text, "girl is not sheila (a grown woman)"
        assert "Goldilocks" in r.text and "Father Bear" in r.text


def test_fast_asleep_is_not_speed(translated):
    for level, seed, r in runs(translated, "hare_and_tortoise"):
        assert "flat chat asleep" not in r.text and "like a rat up a drainpipe asleep" not in r.text


def test_historical_gettysburg_target_wording_coverage(translated):
    """Hold the historical 60% wording gate fixed as dictionary descriptions change.

    These were heuristic target spans, including ordinary English, not curated slang labels.
    Their 25 anchor sets are frozen from 7eae354; do not retune them to current outputs.
    """
    import hashlib
    import yaml
    from aussiefy.scrape.harvest import harvest_pairs
    from aussiefy.terms import fold, restore_g

    source = REF / 'gettysburg.txt'
    target = REF.parent / 'targets/gettysburg_level5.txt'
    frozen = yaml.safe_load((REF.parents[1] / 'fixtures/gettysburg-wording-anchors.yaml').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == frozen['source_sha256']
    assert hashlib.sha256(target.read_bytes()).hexdigest() == frozen['target_sha256']
    pairs = {(a, b) for a, b, _ in harvest_pairs(source.read_text(), target.read_text())}
    anchors = frozen['anchors']
    assert len(anchors) == 25
    for a in anchors:
        assert (a['source'], a['target']) in pairs
        assert a['content'] and set(a['content']) <= set(a['target'].lower().replace('-', ' ').split())
    outputs = [restore_g(fold(translated("gettysburg", 5, s).text)).replace('-', ' ') for s in range(10)]
    hits = [any(all(restore_g(w) in out for w in a['content']) for out in outputs) for a in anchors]
    coverage = sum(hits) / len(anchors)
    assert coverage >= 0.6, f"historical wording coverage {coverage:.0%}: " + ", ".join(
        a['target'] for a, hit in zip(anchors, hits) if not hit)


def test_goldilocks_benchmark_vocabulary_overlap(translator, translated):
    """The agent's Goldilocks extends the story, so compare vocabulary rather than aligned spans."""
    from aussiefy.scrape.harvest import vocabulary_overlap
    target = (REF.parent / "targets" / "goldilocks_level5.txt").read_text(encoding="utf-8")
    outputs = [translated("goldilocks", 5, s).text for s in range(10)]
    rows = vocabulary_overlap(target, outputs, translator.dictionary)
    share = sum(h for _, h in rows) / len(rows)
    assert share >= 0.6, f"{share:.0%}; missing " + ", ".join(p for p, h in rows if not h)


def test_story_flow(translated):
    """Narration gets connectives, not tag-ons; tags go inside dialogue; few repeats or pile-ups."""
    from collections import Counter
    import re as _re
    repeats = stacks = 0
    for s in SEEDS:
        r = translated("goldilocks", 5, s)
        for g in r.garnish:
            if g.placement == "tag" and g.text:
                assert g.sentence in (10, 12), f"s{s}: tag on a narration sentence {g.sentence}"
            if g.placement == "connective" and g.text:
                assert g.sentence != 0
        assert not _re.search(r'said, (mate|ay|cobber)', r.text), "tags belong inside the quote"
        used = Counter(x.chosen.entry.id for x in r.records if x.substituted)
        used.update(x.stacked.entry.id for x in r.records if x.stacked)
        repeats += sum(v > 1 for v in used.values())
        stacks += sum(1 for x in r.records if x.stacked)
        assert "scoffed." not in r.text, "scoff on its own drops 'the lot'"
    assert repeats / len(SEEDS) <= 0.6 and stacks / len(SEEDS) <= 1.5, (repeats, stacks)
