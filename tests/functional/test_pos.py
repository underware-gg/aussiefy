"""Part-of-speech tags, and what the engine does with them; the a/an rule; swear infixes by genre."""

import pytest

from aussiefy import pos
from aussiefy.text import indefinite_article, tokenize


def test_the_tagger_gives_nltks_tags():
    words = "You are not going to get rich that way .".split()
    assert pos.tag(words) == ["PRP", "VBP", "RB", "VBG", "TO", "VB", "JJ", "DT", "NN", "."]
    assert pos.tag("Residents said it .".split())[0] == "NNS" and pos.tag("Smith said it .".split())[0] == "NNP"


@pytest.mark.parametrize("word, article", [
    ("ute", "a"), ("U-turn", "a"), ("uni", "a"), ("u-ey", "a"), ("one-off", "a"), ("euro", "a"),
    ("FBI", "an"), ("NSW", "an"), ("RSL", "an"), ("SUV", "an"), ("HTML", "an"), ("UFO", "a"), ("CSIRO", "a"),
    ("NASA", "a"), ("ANZAC", "an"), ("hour", "an"), ("esky", "an"), ("arvo", "an"), ("unusual", "an"),
    ("HAT", "a"), ("MAN", "a"), ("UGLY", "an"), ("unanimous", "a"), ("onesie", "a"), ("usage", "a"),
    ("8-year-old", "an"), ("18th", "an"), ("100", "a"),
])
def test_indefinite_article(word, article):
    assert indefinite_article(word) == article


def _outs(translator, text, **kw):
    return [translator.translate(text, seed=s, **kw).text for s in range(8)]


def test_a_verb_idiom_doesnt_take_a_noun(translator):
    for out in _outs(translator, "It has more taste than beer. Is sicklied o'er with the pale cast of thought.", level=4):
        assert "pale cast of reckoned" not in out and "more have a crack" not in out, out


def test_a_noun_term_doesnt_take_a_verb(translator):
    for out in _outs(translator, "Me, that kids meself, I reckon.", level=4):
        assert "kids meself" in out, out


@pytest.mark.parametrize("name", ["Smith", "Roberts", "Bunnings", "Aussies", "Constable Harris", "New South Wales"])
def test_an_opener_keeps_a_names_capital(translator, name):
    outs = [translator.translate(f"The storm hit hard. {name} said the river rose.", level=5, seed=s).text
            for s in range(30)]
    assert not any(f", {name[0].lower()}{name[1:]}" in o for o in outs)


def test_an_opener_lower_cases_an_ordinary_word(translator):
    outs = [translator.translate("The storm hit hard. Residents said the river rose.", level=5, seed=s).text
            for s in range(30)]
    assert any(", residents said" in o for o in outs) and not any(", Residents said" in o for o in outs)
    story = [translator.translate("The Geebung boys got going.", level=5, seed=s).text for s in range(12)]
    assert not any(", The Geebung" in o for o in story)


@pytest.mark.parametrize("text, keep", [
    ("Add eggs one at a time.", None),                       # plurals the tagger calls verbs
    ("Alright, guys, on this side.", None),
    ("I'm gonna complain to the boss.", "whinge"),           # casual contractions
    ("I'd rather laugh than complain.", "whinge"),           # "than" isn't a preposition before a noun
])
def test_the_part_of_speech_guards_dont_refuse_good_swaps(translator, text, keep):
    outs = _outs(translator, text, level=4)
    if keep:
        assert any(keep in o for o in outs), outs


def test_swear_infixes_go_only_where_the_embellishment_takes_them(translator):
    tech = ("Run the build command. If the server returns an error, check the config file and the API key. "
            "The deploy is a big problem when the cache is stale. Restart the node and check the logs.")
    tech += " The cache is really stale and the build is very slow."
    for out in _outs(translator, tech, level=5, vulgarity="tradie"):
        assert not any(w in out for w in ("fuckin'", "bloody")), out   # flamin' is clean (vulgarity 0)
    r = translator.translate(tech, level=5, seed=1, vulgarity="tradie")
    assert any("deadset (the technical text's own) takes no swear infixes" in w for w in r.warnings)
    told = translator.translate(tech, level=5, seed=1, vulgarity="tradie", embellishment="troppo")
    assert not any("takes no swear infixes" in w for w in told.warnings)
    story = "It was a great big stone. He couldn't believe it."
    assert any("bloody" in o or "fuckin'" in o for o in _outs(translator, story, level=5, vulgarity="tradie"))


def test_the_tags_follow_our_tokens():
    words = [t.text for t in tokenize("I don't think the kids'll eat it, mate. \u201cRight,\u201d she said.")]
    tags = pos.tag(words)
    assert len(tags) == len(words) and tags[words.index("n't")] == "RB" and tags[words.index("\u201c")] == "``"
    assert pos.tag("I 'm gonna complain .".split())[2:4] == ["MD", "VB"]
