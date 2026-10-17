"""Masks (O23): each rendering lists the words a page may hide, with where each one's ending starts. Swear-list words,
the compounds the dictionary's rated words build on one, and the mask words an entry authors where its rudeness
isn't a listed word. Only profanity is masked: innuendo, insults and crude words show in full, and every rated entry
yields a masked word at its rating unless its data marks it `profane: false`."""

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


# Rated 2, while their only listed word, "bugger", is rated 1 in swears.yaml: whether to lower the entries or mask
# "bugger" at 2 on them is a content call put to Rob. Until then they are held to their listed word's rating only.
RATED_ABOVE_THEIR_SWEAR = {"bugger-me-dead", "g-bugger-me-dead"}


def test_every_rated_entry_yields_a_masked_word_at_its_rating_unless_nothing_in_it_is_profane(dictionary):
    """At least one of an entry's forms masks a word at its rating, and any form with a masked word reaches it,
    so a lock never shows a rated term's profanity in full. An entry marked `profane: false` (innuendo, an insult,
    a crude word: "rooted", "mongrel", "gob") is never masked."""
    short, weak = [], []
    for e in dictionary.entries.values():
        if e.status != "active" or not e.vulgarity:
            continue
        words = {w: e.vulgarity for w in e.mask}
        strongest = [max((m["vulgarity"] for m in masks(f, dictionary.swears, dictionary.swear_compounds, words)),
                         default=0) for f in _forms(e)]
        if not e.profane:
            assert not e.mask, e.id
            continue
        rating = 1 if e.id in RATED_ABOVE_THEIR_SWEAR else e.vulgarity
        if max(strongest) < rating:
            short.append(e.id)
        weak += [(e.id, f) for f, s in zip(_forms(e), strongest) if 0 < s < rating]
    assert not short, f"rated entries with no masked word at their rating (author `mask` or mark `profane: false`): {short}"
    assert not weak, f"forms whose masked words fall short of the entry's rating: {weak}"


def test_the_exception_still_holds(dictionary):
    """Drop RATED_ABOVE_THEIR_SWEAR once the call is made and the data agrees."""
    for i in RATED_ABOVE_THEIR_SWEAR:
        e = dictionary.entries[i]
        assert e.vulgarity == 2 and not e.mask and dictionary.swears["bugger"] == 1


def test_entries_with_nothing_profane_are_marked_in_the_data(dictionary):
    unmasked = {e.id for e in dictionary.entries.values() if not e.profane}
    assert unmasked >= {"rooted", "have-a-root", "colder-than-a-witchs-tit", "mongrel", "shut-your-gob"}
    assert {e.id for e in dictionary.entries.values() if e.mask} == {"wanker", "a-dickhead", "bare-arsed",
                                                                     "tight-arsed", "blue-arsed-fly"}


@pytest.mark.parametrize("raw, message", [
    ({"mask": ["wanker"]}, "rated vulgarity 1 or more"),
    ({"profane": False}, "rated vulgarity 1 or more"),
    ({"vulgarity": 2, "mask": ["wanker"], "profane": False}, "not both"),
    ({"vulgarity": 2, "profane": "no"}, "true or false"),
    ({"vulgarity": 2, "mask": ["bludger"]}, "word in one of its forms"),
    ({"vulgarity": 2, "mask": ["Wanker"]}, "lower-case word"),
])
def test_mask_and_profane_are_checked_when_loaded(raw, message):
    with pytest.raises(SchemaError, match=message):
        parse_entry({"id": "zz-wanker", "form": "a wanker", "concept": ["WANKER"], "frame": "np", **raw})


def test_a_locked_rendering_carries_its_entrys_masks(translator):
    """End to end at nan: an authored mask word in a locked option is masked, its span in that rendering; an entry
    with nothing profane ("shut yer gob") shows in full."""
    cs = aussiefy.translate_changes("That idiot again. Shut up!", translator=translator, level=5, vulgarity=0)
    locked = {o["entry_id"]: o for c in cs.changes for o in c["locked"]}
    o = locked["a-dickhead"]
    assert [(o["rendered"][m["span"][0]:m["span"][1]], m["vulgarity"]) for m in o["masks"]] == [("dickhead", 2)]
    assert locked["shut-your-gob"]["masks"] == []
    for c in cs.changes:
        for r in c["alternatives"] + c["locked"]:
            for m in r["masks"]:
                a, b = m["span"]
                assert 0 <= a < m["ending_start"] <= b <= len(r["rendered"])
