"""Wrong senses the third everyday pass found (research/embellishment-pass-2026-10-13/FINDINGS.md), fixed in the
dictionary by the third-pass round (research/third-pass-round-2026-10-13/DECISIONS.md), each pinned with the right
sense that must still swap."""

import pytest

from aussiefy import harness


def _seeds(translator, text, n=6, **kw):
    kw = {"level": 4, "embellishment": "dinkum", **kw}
    return [translator.translate(text, seed=s, **kw).text for s in range(n)]


@pytest.mark.parametrize("text, never", [
    # beaut is pleasing to have or look at, not any "good"
    ("They were good friends. Good riddance to him. It was never even a good imitation.", ["beaut", "Beaut"]),
    ("Good work, team. He was a good sport about it. Replace it to ensure a good seal.", ["beaut", "Beaut"]),
    ("It was nice of you. It is nice to meet you. They are lovely people.", ["beaut"]),
    # young fellas are youths, not a man's mates or a team; little fella is a boy, not any child
    ("Lots of the boys here have seen him. One of the boys told me. Regards to all the boys.", ["young fella"]),
    ("Pick up small children immediately. Trying to keep your kid happy backfires.", ["little fella"]),
    # the bush isn't a US land category or an idiom
    ("What is the difference between a national park and a national forest? The national forests are managed by "
     "the Forest Service.", ["bush"]),
    ("In this neck of the woods we walk. We are not out of the woods yet.", ["bush"]),
    # dead set on is determined on, not dedicated (allocated) or devoted to
    ("Half the proceeds were dedicated to liquidity support. He is devoted to his wife. The book is dedicated to "
     "his mother.", ["dead set", "christen"]),
    ("Sir William and Lady Lucas are determined to go.", ["dead set on go"]),
    # swear blind is insisting a thing is true, not resolving (a noun, or sorting out) or vowing
    ("The Committee underlined its continuing resolve to achieve its goals. Efforts to resolve difficult issues "
     "continue. He vowed to return. He told him not to swear.", ["swear blind", "swore blind", "swears blind"]),
    # a goer said of a woman is a slur
    ("But she looked feasible and praiseworthy to the eye.", ["goer"]),
    # the comparative isn't an esky
    ("A cooler airmass will move in. A cooler, drier day follows, with cooler temperatures.", ["esky"]),
    # the public sector isn't the punters
    ("The experience may be gained in either the public, private sector or volunteer service. The public and "
     "private sectors grew.", ["punters"]),
    # a field of study or data isn't a paddock
    ("It needs 15 hours in a social science field(s). RH fields show residual moisture. Experts in the field "
     "agree. She is a leader in her field.", ["paddock"]),
    # "I'm afraid your..." is sorry to say
    ("I am afraid your ideas are wrong. I'm afraid the shop is shut.", ["scared", "spooked"]),
    # come a cropper drops the object of "trip over" and "fall down"
    ("I tripped over the cable. He fell down the stairs.", ["cropper", "gutser", "gutzer", "arse over"]),
    # hold out (endure) takes no object
    ("Hold out your hands. They hold out little hope.", ["battle on", "Battle on"]),
])
def test_never(translator, text, never):
    for out in _seeds(translator, text):
        assert not any(bad in out for bad in never), out


@pytest.mark.parametrize("text, wanted", [
    ("What a lovely day for it. She has a lovely voice.", ["beaut"]),
    ("The boy ran home.", ["young fella"]),
    ("The little boy cried.", ["little fella"]),
    ("We walked in the woods.", ["bush"]),
    ("He was bent on revenge. She was intent on winning.", ["dead set on"]),
    ("I swear that it was him. He swore up and down he was home.", ["swear blind", "swore blind"]),
    ("The plan is feasible.", ["a goer"]),
    ("Put the drinks in the cooler.", ["esky"]),
    ("Members of the public came.", ["unters"]),
    ("The cows were in the field.", ["paddock"]),
    ("She was afraid of the dark.", ["scared stiff", "shit-scared"]),
    ("She fell over in the street.", ["cropper", "gutser", "arse over"]),
])
def test_the_right_sense_still_swaps(translator, text, wanted):
    outs = _seeds(translator, text, n=8, level=5)
    assert any(any(w in o for w in wanted) for o in outs), outs


def _suggested(text, word):
    return [s for s in harness.lint(text, level=4)["suggestions"] if s["text"].lower() == word]


def test_lint_leaves_compounds_verbs_and_idioms_alone():
    assert not _suggested("She gave the kids their pocket money.", "money")      # not "pocket dosh"
    assert not _suggested("The CCA hands tokens out. It hands you back a ciphertext.", "hands")   # the verb
    assert not _suggested("He was a good sport about it.", "good")
    assert not _suggested("This neck of the woods is quiet.", "woods")
    docs = ("Run the build command. If a node falls over, the scheduler restarts its pods on another node. You "
            "might trip over bugs in the API server.")
    assert not _suggested(docs, "falls over") and not _suggested(docs, "trip over")   # a crash, not a tumble
    # and the plain senses are still suggested
    assert _suggested("I need some money.", "money") and _suggested("She fell over in the street.", "fell over")


@pytest.mark.parametrize("text, wanted", [
    ("They called off the search at dusk.", "pulled the pin on the search"),
    ("The council keeps dragging its feet on the bridge.", "dragging the chain"),
    ("We need to figure out how to fix it.", "nut out how"),
    ("Give me a call tomorrow.", "Give me a "),
    ("It's first come, first served.", "first in, best dressed"),
    ("My coworker brought cake.", "workmate"),
    ("The tickets were dirt cheap.", "cheap as chips"),
    ("The plan went horribly wrong.", "went pear-shaped"),
    ("She lived a long and full life.", "had a good innings"),
    ("Quite a few people turned up.", "fair few"),
    ("Take an umbrella.", "brolly"),
    ("They live out in the sticks.", "out bush"),
    ("The toddler threw a hissy fit.", "chucked a tanty"),
])
def test_the_rounds_new_entries(translator, text, wanted):
    assert any(wanted in o for o in _seeds(translator, text, n=8, level=5)), wanted


@pytest.mark.parametrize("text, never", [
    ("The match was called off.", ["pin"]),                                     # no object: grammar would break
    ("It is an umbrella term. He works for an umbrella organisation.", ["brolly"]),
    ("The room was in total darkness.", ["all up"]),
    ("You can't go wrong with this.", ["pear-shaped"]),
    ("What is the deal worth?", ["the go"]),
    ("African Americans and Native Americans voted. Black Americans marched.", ["Yank"]),
    ("He lost his temper.", ["tanty"]),
])
def test_the_rounds_new_entries_keep_to_their_sense(translator, text, never):
    for out in _seeds(translator, text, n=8, level=5):
        assert not any(bad in out for bad in never), out


def test_no_fishos_or_yanks_in_the_news(translator):
    from pathlib import Path
    news = (Path(__file__).resolve().parents[1] / "corpus" / "everyday" / "news" / "yellowstone_fishing_restrictions_lifted.txt")
    for out in _seeds(translator, news.read_text(encoding="utf-8"), n=4, level=5):
        assert "fisho" not in out.lower(), out
    assert any("fishos" in o for o in _seeds(translator, "The fishermen came home with a big catch.", level=5))
    report = "WASHINGTON (AP) — Officials said 20 million more Americans now have health insurance, the agency said."
    for out in _seeds(translator, report, n=4, level=5):
        assert "yank" not in out.lower(), out


def test_punnets_but_not_pints_of_milk(translator):
    out = translator.translate("Buy two pints of strawberries and a pint of milk.", level=2, english="us").text
    assert "punnets of strawberries" in out and "pint of milk" in out, out
