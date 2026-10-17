"""American and British words Australians say differently: swapped at every level, with their senses kept."""

import pytest

from aussiefy import harness
from aussiefy.dialect import parse_dialect
from aussiefy.schema import SchemaError


def _t(translator, text, **kw):
    return translator.translate(text, level=1, seed=0, **kw).text


@pytest.mark.parametrize("text, want", [
    ("Dice the bell pepper and the courgettes.", "Dice the capsicum and the zucchini."),   # US and British
    ("An elevator was broken.", "A lift was broken."),                                     # the article follows
    ("They stood in line for french fries.", "They queued up for chips."),                 # a verb inflects
    ("Mail them today.", "Post them today."),                                              # a slot carries over
    ("We studied maths.", "We studied maths."),                                            # already Australian
])
def test_words_only_another_english_uses_swap_at_every_level(translator, text, want):
    assert _t(translator, text) == want


@pytest.mark.parametrize("text,want", [
    ("Stop at the yield sign.", "Stop at the give way sign."),
    ("Look for yield signs.", "Look for give way signs."),
    ("The investments yield significant returns.", "The investments yield significant returns."),
    ("The crop yield signals a recovery.", "The crop yield signals a recovery."),
    ("Stop at the give way sign.", "Stop at the give way sign."),
])
@pytest.mark.parametrize("level", range(1, 6))
def test_yield_sign_localises_only_the_road_sign_phrase(translator, text, want, level):
    assert translator.translate(text, level=level, seed=0, vulgarity=0, document_type="custom").text == want


def test_a_capital_mid_sentence_is_a_name_and_stays(translator):
    assert _t(translator, "We bought a Diaper Genie and a diaper.") == "We bought a Diaper Genie and a nappy."


def test_a_word_australians_use_in_another_sense_needs_its_english(translator):
    uk = "She changed her pants and her vest."
    assert _t(translator, uk) == uk                                                  # Australian pants are trousers
    assert _t(translator, uk, english="uk") == "She changed her undies and her singlet."
    us = "She broke her hip in the fall."
    assert _t(translator, us) == us
    assert _t(translator, "We left in the fall.", english="us") == "We left in autumn."
    # two American spelling rules mark a text as American; Oxford -ize and one rule twice don't
    assert "autumn" in _t(translator, "My favorite color is gray. We left in the fall.")
    assert "autumn" not in _t(translator, "She organized and recognized it. We left in the fall.")
    assert "autumn" not in _t(translator, "The gas meter and two water meters. We left in the fall.")


def test_a_term_of_art_stays_in_its_genre(translator):
    tech = ("The server sets a cookie in the HTTP response header. The browser stores cookies and sends them "
            "with each request to the API, so the session token and user data persist across requests.")
    assert "cookie" in _t(translator, tech, document_type="auto") and "biscuit" not in _t(translator, tech, document_type="auto")
    assert _t(translator, "Then eat a cookie.", document_type="auto") == "Then eat a biscuit."


def test_english_none_turns_the_swaps_off(translator):
    assert _t(translator, "Turn off the faucet.", english="none") == "Turn off the faucet."


def test_explain_records_each_swap(translator):
    r = translator.translate("Turn off the faucet.", level=1)
    assert [(d.before, d.after, d.english) for d in r.dialect] == [("faucet", "tap", "us")]
    assert {"kind": "dialect", "english": "us", "before": "faucet", "after": "tap", "span": [13, 19],
            "sentence": 0} in r.to_dict()["explain"]


def test_lint_flags_them_as_the_engine_finds_them(translator):
    issues = harness.lint("Grab the faucets and your cell phone, y'all.", level=3, translator=translator)["issues"]
    found = {(i["phrase"], i["australian"]) for i in issues if i["kind"] == "dialect"}
    assert {("faucets", "taps"), ("cell phone", "mobile"), ("y'all", "youse")} <= found
    pants = "She changed her pants."
    assert not [i for i in harness.lint(pants, translator=translator)["issues"] if i["kind"] == "dialect"]
    assert [i for i in harness.lint(pants, english="uk", translator=translator)["issues"] if i["kind"] == "dialect"]


@pytest.mark.parametrize("raw, why", [
    ({"us": {"faucet": {"to": "tap", "color": "red"}}}, "only"),
    ({"us": {"faucet": {"plural": "taps"}}}, "needs `to`"),
    ({"canada": {"toque": "beanie"}}, "unknown sections"),
    ({"us": {"stand in line": {"to": "queue", "frame": "verb"}}}, "unknown frame"),
    ({"us": {"faucet": {"to": "tap {obj}"}}}, "doesn't capture"),
    ({"us": {"broil": {"to": "grill", "frame": "vp", "plural": "grills"}}}, "no plural"),
    ({"us": {"realtor": "estate agent"}, "uk": {"estate agent": "real estate agent"}}, "swap again"),
])
def test_the_table_is_checked(raw, why):
    with pytest.raises(SchemaError, match=why):
        parse_dialect(raw)


@pytest.mark.parametrize("text, want", [
    ("Buy a cookie cutter and a cookie jar.", "biscuit cutter"),      # the compound beats the dictionary's cookie
    ("Take out the trash can.", " bin"),                              # the longer swap wins, not "rubbish can"
    ("Rub on petroleum jelly.", "Rub on petroleum jelly."),           # a guard keeps its words
    ("She sprinkles salt on the fortune cookie.", "She sprinkles salt on the fortune cookie."),
    ("Put it on airplane mode and practise your elevator pitch.", "airplane mode"),
])
def test_compounds_and_guards_win_at_every_level(translator, text, want):
    for level in (1, 5):
        out = translator.translate(text, level=level, seed=0).text
        assert want in out or out.startswith(want), (level, out)


def test_the_engines_output_passes_its_own_dialect_lint(translator):
    texts = ["Hand me the flip-flops and the jello; the realtor took an appetizer.",
             "The server sets a cookie in the HTTP response header. The browser stores cookies and sends them "
             "with each request to the API, so the session token and user data persist across requests."]
    for text in texts:
        for english in ("auto", "us", "uk"):
            out = translator.translate(text, level=1, english=english).text
            issues = harness.lint(out, original=text, english=english, translator=translator)["issues"]
            assert not [i for i in issues if i["kind"] == "dialect"], (english, out)


def test_explain_shows_the_dialect_swaps(translator):
    from aussiefy.explain import format_explain
    out = format_explain(translator.translate("Turn off the faucet.", level=1))
    assert '"faucet" -> "tap" (us)' in out


def test_plan_lists_them(translator):
    plan = harness.plan("Turn off the faucet.", level=1, translator=translator)
    assert plan["dialect"] == [{"before": "faucet", "after": "tap", "english": "us"}]


def test_an_unknown_english_is_refused(translator):
    from aussiefy.errors import UserError
    with pytest.raises(UserError):
        harness.lint("Turn the faucet.", english="british", translator=translator)


def test_a_misspelt_genre_in_not_in_is_refused():
    """A typo'd guard ("techincal") would silently let the swap through in docs."""
    import pytest

    from aussiefy.dialect import parse_dialect
    from aussiefy.schema import SchemaError

    with pytest.raises(SchemaError, match="techincal"):
        parse_dialect({"us": {"faucet": {"to": "tap", "not_in": ["techincal"]}}})


@pytest.mark.parametrize("raw", [
    [], {"us": []}, {"us": {"truck": {"to": "ute", "known_only": "false"}}},
    {"us": {"truck": {"to": 7}}}, {"us": {"truck": {"to": "ute", "plural": 7}}},
    {"lint_only": {"y'all": 7}}, {"lint_only": []},
])
def test_dialect_configuration_rejects_wrong_types(raw):
    with pytest.raises(SchemaError, match="dialect.yaml"):
        parse_dialect(raw)
