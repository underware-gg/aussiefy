"""Strict Markdown is one document for garnish, despite its source-preserving units."""

from dataclasses import replace

import pytest

from aussiefy import Translator, translate


@pytest.fixture
def loud_document_translator(dictionary):
    profile = replace(
        dictionary.profiles[5],
        garnish={"opener": 1.0, "closer": 1.0},
        max_garnish={"opener": 2, "closer": 1},
        garnish_gap=1,
    )
    return Translator(replace(dictionary, profiles={**dictionary.profiles, 5: profile}))


def selected(result, placement):
    return [
        (i, g)
        for i, unit in enumerate(result.units)
        for g in unit.result.garnish
        if g.placement == placement and g.entry_id
    ]


def test_garnish_limits_and_spacing_apply_to_whole_markdown(loud_document_translator):
    source = "\n\n".join(["The river is flowing through the valley."] * 6 + ["That is my opinion."]) + "\n"
    result = translate(
        source, markdown=True, level=5, vulgarity=0, embellishment="troppo", translator=loud_document_translator
    )
    openers = selected(result, "opener")
    assert len(openers) == 2
    assert openers[1][0] - openers[0][0] > 1
    closers = selected(result, "closer")
    assert len(closers) == 1 and closers[0][0] == len(result.units) - 1
    assert (
        result.text
        == translate(
            source, markdown=True, level=5, vulgarity=0, embellishment="troppo", translator=loud_document_translator
        ).text
    )


@pytest.mark.parametrize(
    "source,has_leading_opener",
    [
        ("Work happens on `dev`. `main` holds releases only.\n", True),
        ("The river runs through the valley\nand reaches the bay without turning.\n", True),
        ("The **river** reaches the valley.\n", False),
        ("The [river](https://example.com) reaches the valley.\n", False),
    ],
)
def test_only_safe_source_starts_receive_garnish_openers(source, has_leading_opener, loud_document_translator):
    result = translate(
        source,
        markdown=True,
        level=5,
        vulgarity=0,
        embellishment="dinkum",
        document_config={"garnish": ["opener"]},
        translator=loud_document_translator,
    )
    openers = selected(result, "opener")
    assert bool(openers) == has_leading_opener
    assert all(index == 0 for index, _ in openers)
    assert all(
        source[a:b] == result.text[c:d]
        for p in result.protected
        for a, b in [p.source_span]
        for c, d in [p.output_span]
    )


def test_complete_sentence_after_an_inline_fragment_can_still_take_opener(loud_document_translator):
    source = "Use `dev` for changes. The river is flowing through the valley.\n"
    result = translate(
        source,
        markdown=True,
        level=5,
        vulgarity=0,
        embellishment="dinkum",
        document_config={"garnish": ["opener"]},
        translator=loud_document_translator,
    )
    openers = selected(result, "opener")
    assert len(openers) == 1
    assert openers[0][1].sentence == 1  # offsets and sentence records remain local to the unit
