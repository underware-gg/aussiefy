"""A noun phrase's determiner and number when a term is swapped in: what the article rails keep, drop or refuse."""

import pytest

from aussiefy import morph
from aussiefy.matcher import compile_pattern


@pytest.mark.parametrize("word, singular", [
    ("horses", "horse"), ("ponies", "pony"), ("boxes", "box"), ("churches", "church"), ("men", "man"),
    ("christmas", None), ("chaos", None), ("shambles", None), ("news", None), ("glass", None),
    ("buckley's", None), ("drovers'", None),
])
def test_singular_of(word, singular):
    assert morph.singular_of(word) == singular


def test_a_trigger_written_as_a_plural_matches_only_itself():
    head = compile_pattern("wild horses", "np", ("X",), 3).elements[-1]
    assert head.forms == (("horses", "written_plural"),)
    head = compile_pattern("wild horse", "np", ("X",), 3).elements[-1]
    assert dict(head.forms) == {"horse": "singular", "horses": "plural"}


def _outs(translator, text, levels=(3, 4, 5), seeds=range(8)):
    return [translator.translate(text, level=lv, seed=s).text for lv in levels for s in seeds]


@pytest.mark.parametrize("text, never", [
    ("Merry Christmas to all.", ["Chrissies"]),                          # spelling can't tell the number
    ("The house was a shambles.", ["shemozzles", "was shemozzle", "was dog's"]),
    ("He had forty winks.", ["kips", "nana naps"]),
    ("A young politician spoke.", ["pollies"]),                           # a plural-only term for one
    ("The next time somebody mentions limes, I'll scream.", ["time bugger", "time bastard", "time mongrel"]),
    ("Parson Walker's wife was sick.", ["'s the missus"]),                # a genitive is a determiner
    ("A yell might wake the dead.", ["poor buggers"]),                    # an idiom for noise
    ("The poor old minister tried his best.", ["battlers old"]),          # "poor" is an adjective here
    ("He lives in the sticks.", ["the beyond", "the out in", "the Woop"]),
    ("You have no chance of winning.", ["no Buckley's"]),
    ("Down in the dumps.", ["tips"]),
])
def test_never(translator, text, never):
    for out in _outs(translator, text):
        assert not any(bad in out for bad in never), out


@pytest.mark.parametrize("text, sometimes", [
    ("We mourn the dead.", "the poor buggers"),                          # the article kept
    ("His wife was cooking.", "his missus"),                             # the possessive fills {poss}
    ("They camped by the old waterhole.", "the old billabong"),          # the term's own article goes
    ("The wild horses ran past.", "the brumbies"),                       # the entry's plural
    ("The public were outraged.", "the punters"),                        # a body of people takes a plural
])
def test_sometimes(translator, text, sometimes):
    assert any(sometimes in out.lower() for out in _outs(translator, text))
