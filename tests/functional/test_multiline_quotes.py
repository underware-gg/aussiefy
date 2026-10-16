"""Quoted documents spanning paragraphs obey the same preservation contract as speech."""

import pytest

from aussiefy import harness, translate
from aussiefy.text import quoted_spans
from aussiefy.yarn import brief, dispatch_tool


@pytest.mark.parametrize("quotes", [('"', '"'), ('“', '”')])
@pytest.mark.parametrize("route", [{}, {"markdown": True}, {"markup": "mdx"}])
def test_multiline_quoted_document_survives_every_check(quotes, route, translator):
    opening, closing = quotes
    source = opening + "Keep the rate at 5 percent.\n\nKeep the color gray." + closing
    config = {"keep_quotes": True, "garnish": []}
    result = translate(source, translator=translator, document_config=config, **route)
    assert result.text == source
    markup = "markdown" if route.get("markdown") else route.get("markup", "text")
    args = dict(translator=translator, document_config=config, markup=markup)
    assert harness.lint(source, original=source, suggest=False, **args)["ok"]
    checked = harness.verify(source, original=source, **args)
    assert checked["ok"], checked["problems"]
    session = brief(source, **args)
    actual, accepted = dispatch_tool(session, "submit", {"text": source, "declined": []})
    assert accepted, actual


def test_unquoted_dialect_still_needs_conversion(translator):
    source = '"Keep the rate at 5 percent.\n\nKeep the color gray." Outside it is 6 percent.'
    result = harness.lint(source, original=source, translator=translator,
                          document_config={"keep_quotes": True}, suggest=False)
    assert [(i["kind"], i["phrase"]) for i in result["issues"]] == [("dialect", "percent")]


@pytest.mark.parametrize("edit", ["change", "drop", "duplicate"])
def test_multiline_quote_preservation_does_not_excuse_edits_or_copies(edit, translator):
    quote = '"Keep the rate at 5 percent.\n\nKeep the color gray."'
    source = quote + " The package works."
    changed = {"change": source.replace("5 percent", "5 per cent"), "drop": "The package works.",
               "duplicate": source + " " + quote}[edit]
    result = harness.lint(changed, original=source, translator=translator,
                          document_config={"keep_quotes": True}, suggest=False)
    assert not result["ok"]
    assert any(i["kind"] == ("dialect" if edit == "duplicate" else "document_changed")
               for i in result["issues"])


def test_keep_quotes_can_still_be_disabled(translator):
    source = '"Keep the rate at 5 percent.\n\nKeep the color gray."'
    result = translate(source, translator=translator, english="us",
                       document_config={"keep_quotes": False, "garnish": []})
    assert "per cent" in result.text and "colour" in result.text and "grey" in result.text


def test_inches_adjacent_quotes_and_drawl_do_not_merge():
    text = 'A 6" pipe. "First quote."\n\n"Second quote." We\'re pursuin\' it, \'cause we can.'
    assert [text[a:b] for a, b in quoted_spans(text)] == ['"First quote."', '"Second quote."']


def test_unclosed_quote_is_not_a_held_document():
    assert quoted_spans('An unclosed "document.\n\nThe package works.') == []
