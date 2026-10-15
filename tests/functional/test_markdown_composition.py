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
    "source",
    [
        "Work happens on `dev`. `main` holds releases only.\n",
        "The river runs through the valley\nand reaches the bay without turning.\n",
        "The **river** reaches the valley.\n",
        "The [river](https://example.com) reaches the valley.\n",
    ],
)
def test_partial_sentences_cannot_receive_garnish_openers(source, loud_document_translator):
    result = translate(
        source,
        markdown=True,
        level=5,
        vulgarity=0,
        embellishment="dinkum",
        document_config={"garnish": ["opener"]},
        translator=loud_document_translator,
    )
    assert not selected(result, "opener")
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
