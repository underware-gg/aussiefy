"""Masks (O23): each rendering lists the words a page may hide, with where each one's ending starts. Swear-list words,
the compounds the dictionary's rated words build on one, and the mask words an entry authors where its rudeness
isn't a listed word. Innuendo is never masked, and every rated entry yields a masked word at its rating unless its
data marks it as innuendo."""

import pytest

import aussiefy
from aussiefy.masks import masks
from aussiefy.schema import PLACEHOLDER_RE, SchemaError, parse_entry


def _masked(dictionary, text, words=None):
    return [(text[m["span"][0]:m["ending_start"]], text[m["ending_start"]:m["span"][1]], m["vulgarity"])
            for m in masks(text, dictionary.swears, dictionary.swear_compounds, words)]


@pytest.mark.parametrize("text, expected", [
    # (the masked stem, the ending a page keeps, its vulgarity)
    ("fucked", [("fuck", "ed", 2)]),
    ("fuckin'", [("fuck", "in'", 2)]),
    ("arseholes", [("arsehole", "s", 2)]),
    ("bullshit", [("bullshit", "", 2)]),
    ("He's bloody pissed, the bastard's ute", [("bloody", "", 1), ("piss", "ed", 2), ("bastard's", "", 1)]),
    ("a fuckwit in a shitfight", [("fuckwit", "", 2), ("shitfight", "", 2)]),   # compounds: masked whole
    ("bullshitters", [("bullshitters", "", 2)]),
    ("a cocky with a cocktail and a cockatoo", []),   # ordinary words that hold a listed one
])
def test_maskable_words_and_the_endings_they_keep(dictionary, text, expected):
    assert _masked(dictionary, text) == expected


def test_an_entrys_mask_words_keep_their_endings_in_its_renderings(dictionary):
    words = {w: dictionary.entries["wanker"].vulgarity for w in dictionary.entries["wanker"].mask}
    assert _masked(dictionary, "a pack of wankers", words) == [("wanker", "s", 2)]
    assert _masked(dictionary, "a pack of wankers") == []   # mask words belong to their own entry's renderings


def test_compounds_come_from_the_dictionarys_rated_words(dictionary):
    assert {"fuckwit", "shitfight", "bullshitter"} <= set(dictionary.swear_compounds)
    assert not {"cocky", "cocktail", "arsed"} & set(dictionary.swear_compounds)


def _forms(entry):
    return [" ".join(PLACEHOLDER_RE.sub(" ", f).split()) for f in entry.all_forms]


def test_every_rated_entry_yields_a_masked_word_at_its_rating_unless_it_is_innuendo(dictionary):
    """At least one of an entry's forms masks a word at its rating, and any form with a masked word reaches it,
    so a lock never shows a rated term in full. Innuendo ("rooted", "have a root") is never masked."""
    short, weak = [], []
    for e in dictionary.entries.values():
        if e.status != "active" or not e.vulgarity:
            continue
        words = {w: e.vulgarity for w in e.mask}
        strongest = [max((m["vulgarity"] for m in masks(f, dictionary.swears, dictionary.swear_compounds, words)),
                         default=0) for f in _forms(e)]
        if e.innuendo:
            assert not e.mask, e.id
            continue
        if max(strongest) < e.vulgarity:
            short.append(e.id)
        weak += [(e.id, f) for f, s in zip(_forms(e), strongest) if 0 < s < e.vulgarity]
    assert not short, f"rated entries with no masked word at their rating (author `mask` or mark `innuendo`): {short}"
    assert not weak, f"forms whose masked words fall short of the entry's rating: {weak}"


def test_innuendo_is_marked_in_the_data(dictionary):
    assert {e.id for e in dictionary.entries.values() if e.innuendo} >= {"rooted", "have-a-root",
                                                                         "colder-than-a-witchs-tit"}
    assert dictionary.entries["wanker"].mask == ("wanker",)


@pytest.mark.parametrize("raw, message", [
    ({"mask": ["wanker"]}, "rated vulgarity 1 or more"),
    ({"vulgarity": 2, "mask": ["root"], "innuendo": True}, "not both"),
    ({"vulgarity": 2, "mask": ["bludger"]}, "word in one of its forms"),
    ({"vulgarity": 2, "mask": ["Wanker"]}, "lower-case word"),
])
def test_mask_and_innuendo_are_checked_when_loaded(raw, message):
    with pytest.raises(SchemaError, match=message):
        parse_entry({"id": "zz-wanker", "form": "a wanker", "concept": ["WANKER"], "frame": "np", **raw})


def test_a_locked_rendering_carries_its_entrys_masks(translator):
    """End to end: an authored mask word in a locked option at nan, its span in that rendering."""
    cs = aussiefy.translate_changes("That idiot again. Shut up!", translator=translator, level=5, vulgarity=0)
    locked = {o["entry_id"]: o for c in cs.changes for o in c["locked"]}
    for entry, word, vulgarity in (("a-dickhead", "dickhead", 2), ("shut-your-gob", "gob", 1)):
        o = locked[entry]
        assert [(o["rendered"][m["span"][0]:m["span"][1]], m["vulgarity"]) for m in o["masks"]] == [(word, vulgarity)]
    for c in cs.changes:
        for r in c["alternatives"] + c["locked"]:
            for m in r["masks"]:
                a, b = m["span"]
                assert 0 <= a < m["ending_start"] <= b <= len(r["rendered"])
