import pytest

from aussiefy.matcher import PatternIndex, compile_pattern, match_at
from aussiefy.schema import parse_concept, SchemaError
from aussiefy.terms import strip_markup, form_key
from aussiefy.text import tokenize


def test_positive_context_assertion_preserves_inflection_and_destination():
    p = compile_pattern("walk ?=home|there", "vp", ("WALK",), 3)
    m = match_at(p, tokenize("They walked home."), 1)
    assert m and m.end == 2 and m.inflection == "past"
    assert not match_at(p, tokenize("They walked the dog."), 1)
    assert not match_at(p, tokenize("They walked."), 1)
    assert not match_at(p, tokenize("They walked the dog."), 1, exact=False)
    assert strip_markup("walk ?=home|there") == "walk"
    assert form_key("walk ?=home|there") == "walk"


@pytest.mark.parametrize("text", ["?=home walk", "walk ?=", "walk ?=home|", "walk ?=you're"])
def test_invalid_positive_assertions_are_rejected(text):
    with pytest.raises(ValueError):
        compile_pattern(text, "vp", ("WALK",), 3)


def test_context_assertion_does_not_steal_noun_head():
    p = compile_pattern("radio antenna ?=outside", "np", ("ANTENNA",), 3)
    for plural in ["antennas", "antennae"]:
        m = match_at(p, tokenize(f"radio {plural} outside"), 0)
        assert m and m.end == 2 and m.inflection == "plural"


def test_object_directive_requires_a_slot():
    with pytest.raises(ValueError, match="requires"):
        compile_pattern("been eating ^object", "adv", ("EATING",), 3)
    assert compile_pattern("been eating {np} ^object", "adv", ("EATING",), 3).object_argument


@pytest.mark.parametrize("value", ["true", 1, None, []])
def test_lookup_only_is_an_exact_boolean(value):
    with pytest.raises(SchemaError, match="lookup_only"):
        parse_concept("X", {"lookup_only": value})


def test_person_noun_derived_vocabulary_uses_canonical_pattern_cleaning(dictionary):
    from dataclasses import replace

    concept = parse_concept("TEST_PERSON", {"person": True, "triggers": {"np": ["testperson ?=here"]}})
    local = replace(dictionary, concepts={**dictionary.concepts, concept.id: concept})
    assert {"testperson", "testpersons"} <= local.person_nouns


def test_preceding_context_is_nonconsuming_and_preserves_number():
    p = compile_pattern("?<=radio|car antenna", "np", ("ANTENNA",), 3)
    tokens = tokenize("The radio antennae broke.")
    m = match_at(p, tokens, 2)
    assert m and (m.start, m.end, m.inflection) == (2, 3, "plural")
    assert not match_at(p, tokenize("The ant antennae broke."), 2)
    assert not match_at(p, tokenize("antennae broke."), 0, exact=False)
    assert strip_markup("?<=radio|car antenna") == "antenna"


@pytest.mark.parametrize("verb,inflection", [("walk", "base"), ("walked", "past"), ("walking", "ing")])
def test_preceding_assertion_preserves_verb_inflection(verb, inflection):
    p = compile_pattern("?<=they walk", "vp", ("WALK",), 3)
    m = match_at(p, tokenize(f"they {verb}"), 1)
    assert m and m.inflection == inflection


def test_following_assertion_cannot_be_preceded_only_by_an_assertion():
    with pytest.raises(ValueError):
        compile_pattern("?<=they ?=walk walk", "vp", ("WALK",), 3)


def test_preceding_assertion_cannot_bypass_verb_noun_context_checks():
    from aussiefy.detect import detect

    p = compile_pattern("?<=the taste", "vp", ("TASTE",), 3)
    assert not detect(tokenize("The taste was odd."), PatternIndex([p]))


def test_preceding_assertion_preserves_literal_clause_subject():
    p = compile_pattern("?<=said we {be} tired", "clause", ("TIRED",), 3)
    m = match_at(p, tokenize("They said we were tired."), 2)
    assert m and m.captures["subj"].norm == "we" and m.captures["be"].norm == "were"
