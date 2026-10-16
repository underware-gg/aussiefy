"""The dinkum-check round (research/dinkum-check-round-2026-10-14/DECISIONS.md): the new entries in and out of their
sense, and the wrong senses the dinkum check's yarn agents found (research/dinkum-check-2026-10-14/texts/*/
yarn-notes.md) and testing turned up, fixed in the dictionary, each pinned with the right sense that must still swap."""

from pathlib import Path

import pytest

from aussiefy import harness, translate

ROOT = Path(__file__).resolve().parents[2]
TEXTS = ROOT / "research" / "dinkum-check-2026-10-14" / "texts"


def _seeds(translator, text, n=8, **kw):
    kw = {"level": 5, "embellishment": "dinkum", **kw}
    return [translator.translate(text, seed=s, **kw).text for s in range(n)]


@pytest.mark.parametrize("text, wanted", [
    ("I messed up.", "stuffed up"),
    ("He botched the job.", "stuffed up the job"),
    ("They screwed up the order.", "stuffed up the order"),
    ("She screwed it up again.", "stuffed it up"),
    ("Don't make a mess of it.", "stuff it up"),
    ("There was a mix-up with the tickets.", "a stuff-up"),
    ("I'm under a lot of pressure at work.", "under the pump"),
    ("She is under pressure.", "under the pump"),
    ("I don't know him from Adam.", "wouldn't know him from a bar of soap"),
    ("It's drizzling.", "spitting"),
    ("The forecast is all over the map.", "all over the shop"),
    ("He retired in 2020 after twelve seasons.", "pulled the pin in 2020"),
    ("When I retire, I'll go fishing.", "pull the pin"),
    ("She has won a slew of awards.", "swag of awards"),
])
def test_the_rounds_new_entries(translator, text, wanted):
    assert any(wanted in o for o in _seeds(translator, text)), wanted


@pytest.mark.parametrize("text, never", [
    # screwing up a face or the eyes is squinting; messing up a room is untidying it
    ("She screwed up her eyes against the sun. He screwed up his face.", ["stuff"]),
    ("He messed up the kitchen.", ["stuff"]),
    # the object keeps its place: never "stuffed up again" for "screwed it up again", nor "stuff up it"
    ("She screwed it up again. Don't make a mess of it.", ["stuffed up again", "stuff up it"]),
    # a gas or a pipe under pressure is physics (prices or the dollar "under the pump" is said in Australia)
    ("The gas is under pressure. The pipe is under pressure.", ["pump"]),
    # drizzling something over food isn't rain
    ("She was drizzling honey over the toast.", ["spitting"]),
    # "don't know" would contract to "dunno"
    ("I don't know him from Adam.", ["dunno him"]),
    # retiring to bed, retiring hurt, retiring a thing, and being retired (a state or a passive)
    ("She retired to bed early. The batsman retired hurt. They retired the jersey.", ["pin"]),
    ("She is retired now. They are retired. The ship was retired in 1990. Both men are retired.", ["pin"]),
    # retiring is also shy, and a glossary's "to retire; to withdraw" is leaving
    ("She was shy and retiring. Stand-orf: retiring; reticent. Fade away, to: to retire; to withdraw.", ["pin"]),
    # pouring the tea, and tears pouring down a face, aren't rain
    ("She is pouring the tea. Tears were pouring down her face.", ["bucketing", "pissing", "pissin'", "cow"]),
    # only the weather's it rains: fans and water pour somewhere, tears pour down, and she drizzles in a temper
    ("Fans were pouring onto the field. Water was pouring across the floor. Tears were pouring down.",
     ["bucketing", "pissing", "pissin'", "cow"]),
    ("She was drizzling and he was fuming.", ["spitting"]),
    # a counted number of lots is groups, not a large amount
    ("The questions are split into four lots: the auction and the claim.", ["heaps"]),
    # a raft of floating stuff is a raft
    ("They floated down on a raft of logs. A raft of pumice drifted ashore.", ["swag"]),
    # a range isn't the whole lot
    ("He has played everything from country rock to jazz.", ["box and dice", "shebang", "bloody show"]),
])
def test_the_rounds_new_entries_keep_to_their_sense(translator, text, never):
    for out in _seeds(translator, text):
        assert not any(bad in out for bad in never), out


@pytest.mark.parametrize("text, wanted", [
    # the right senses still swap
    ("It is pouring outside.", ["bucketing", "pissing", "pissin'", "cow"]),
    # the trigger's own "it" is the form's subject: "it's brass monkeys", not "yer brass monkeys"
    ("It's freezing today.", ["It's brass monkeys"]),
    ("It was pouring down all night.", ["It was bucketing", "It was pissing", "It was pissin'", "It was raining like"]),
    ("We had loads of fun.", ["heaps"]),
    ("They took everything.", ["box and dice", "shebang", "bloody show"]),
    ("Everyone came to the barbie.", ["every man and his dog", "every bugger", "every bastard", "every bloke"]),
    ("My father is a farmer.", ["old man", "old fella"]),
    ("The kid ran home.", ["littlie", "ankle biter", "tacker", "nipper"]),
])
def test_the_right_sense_still_swaps(translator, text, wanted):
    outs = _seeds(translator, text)
    assert any(any(w in o for w in wanted) for o in outs), outs


def _texts(translator, path, n=3):
    text = path.read_text(encoding="utf-8")
    markup = "auto" if path.suffix in (".md", ".mdx") else "text"
    return [translate(text, translator=translator, level=lv, seed=s, markup=markup, document_type="auto").text for lv in (2, 4) for s in range(n)]


def test_report_and_policy_prose(translator):
    # an obituary's father isn't the old man or the old fella; a policy's "a friend's kid" isn't a littlie; a doc's
    # "one price for everyone" isn't every man and his dog
    for out in _texts(translator, TEXTS / "news__wilbur_crafts_obituary_1922" / "original.txt"):
        assert "old man" not in out and "old fella" not in out, out
    for out in _texts(translator, TEXTS / "workplace__github_gifts_policy" / "original.md"):
        assert not any(w in out for w in ("littlie", "ankle biter", "tacker", "nipper")), out
    for out in _texts(translator, TEXTS / "interfold__faq_auction" / "original.mdx"):
        assert not any(w in out for w in ("every man", "every bastard", "every bugger", "heaps")), out


def test_lookup_finds_the_new_senses():
    def forms(q):
        return [r["form"] for r in harness.lookup(q)["results"]]
    assert "stuff up" in forms("stuff up")
    assert "a stuff-up" in forms("a stuff-up")
    assert "under the pump" in forms("under the pump")


def test_the_object_form_is_its_own_entry(dictionary):
    # by hand, outside the round (see the note at the end of entries/dinkumcheck.yaml): re-applying the round drops it
    e = dictionary.entries["stuff-it-up"]
    assert e.form == "stuff {obj} up" and e.concept == ("BOTCH_IT",) and e.origin_file == "idioms.yaml"


@pytest.mark.parametrize("text", [
    "The waitress poured the tea. It was pouring onto the floor.",
    "The water leaked. It was pouring from the pipe.",
    "The juice overflowed. It was pouring down the drain.",
])
def test_literal_it_does_not_make_liquid_pouring_weather(translator, text):
    for out in _seeds(translator, text, n=3, embedder="none"):
        assert not any(word in out for word in ("bucketing", "pissing", "pissin'", "cow")), out
