"""Harness fixes from the fourth everyday pass (research/fourth-pass-2026-10-14/FINDINGS.md)."""

from pathlib import Path

import pytest

from aussiefy import harness
from aussiefy.guide import style_guide_data

CORPUS = Path(__file__).resolve().parents[1] / "corpus"


def test_a_people_or_place_the_original_names_is_no_new_name(translator):
    original = "Officials said 20 million more Americans now have insurance. Team Colombia won in Europe."
    draft = "Officials said 20 million more Yanks now have insurance. The Colombian team won over in Europe. Then Gladys Smith turned up."
    added = [w["phrase"] for w in harness.lint(draft, original=original, level=5, translator=translator)["warnings"]
             if w["kind"] == "name_added"]
    assert added == ["Gladys Smith"]
    # a new name that only starts like one of the original's isn't let through (Theodore after "Then")
    original = "Then the storm came. Anna saw it, with Smith, in New England and in Japan."
    draft = "Then the storm came. Anna saw it with Theodore, Smithers, the New Englanders and the Japanese."
    added = [w["phrase"] for w in harness.lint(draft, original=original, level=5, translator=translator)["warnings"]
             if w["kind"] == "name_added"]
    assert added == ["Smithers", "Theodore"]


def test_a_unit_conversion_is_no_repeat(translator):
    original = "Use two gallons. Add three gallons. Then five gallons. It was 60F, then 61F, then 62F."
    draft = ("Use two gallons (about 7.5 litres). Add three gallons (about 11 litres). Then five gallons (about 19 "
             "litres). It was 60F (around 16C), then 61F (around 16C), then 62F (around 17C).")
    warnings = harness.lint(draft, original=original, level=3, translator=translator)["warnings"]
    assert not [w for w in warnings if w["kind"] == "repeated_phrase"]
    # a bracket that isn't a measurement still counts
    said = "Mix it well (see step 2 below). Stir it well (see step 2 below). Beat it well (see step 2 below)."
    warnings = harness.lint(said, original="Mix it. Stir it. Beat it.", level=3, translator=translator)["warnings"]
    assert [w for w in warnings if w["kind"] == "repeated_phrase"]


def test_docs_list_no_formal_sentences_to_rework(translator):
    """Their formal words are terms of art the form keeps: the fourth pass's FAQ had 58 listed."""
    faq = (CORPUS / "everyday" / "interfold" / "faq_fold_token.mdx").read_text(encoding="utf-8")
    plan = harness.plan(faq, level=4, markup="mdx", translator=translator)
    assert plan["genre"] in ("technical", "official") and plan["difficult_sentences"] == []
    speech = (CORPUS / "reference" / "gettysburg.txt").read_text(encoding="utf-8")
    assert harness.plan(speech, level=5, translator=translator)["difficult_sentences"]   # a speech still lists them


def test_okay_so_is_no_opening():
    assert all(not text.startswith("Okay, so") for text, _ in style_guide_data().openings)


def test_no_swear_infix_in_a_safety_notice(translator):
    """The fourth pass's dinkum drafts said "far too fuckin' long" in a lightning notice."""
    notice = (CORPUS / "everyday" / "instructions" / "nws_lightning_safety.txt").read_text(encoding="utf-8")
    for seed in range(3):
        r = translator.translate(notice, level=5, seed=seed, vulgarity=2, embellishment="dinkum")
        assert not r.embellishment.takes("infix")
        assert not [p for p in r.phonetic if any(w in p.after for w in ("bloody", "fuckin", "flamin"))]
    warned = translator.translate(notice, level=5, vulgarity=2, embellishment="dinkum").warnings
    assert any("the instructions form takes no swear infixes" in w for w in warned), warned


def test_a_kept_quote_keeps_its_words_but_not_its_spelling(translator):
    # official prose keeps a quoted document's words, as the engine does ("percent" stays); spelling is the
    # house's, so a US spelling inside it is still flagged, and a US word outside it too
    original = ('The Committee raised the rate today, officials said.\n\nThe statement read: "The Committee decided '
                'to raise the target range to 5 percent and will standardize its reporting." The board meets again '
                'next month to review the labor data, which is up 2 percent.')
    issues = harness.lint(original, original=original, level=3, translator=translator)["issues"]
    said = [(i["kind"], i["phrase"]) for i in issues]
    assert ("dialect", "percent") in said and said.count(("dialect", "percent")) == 1
    assert ("spelling", "standardize") in said


def test_a_quote_the_draft_adds_is_the_writers_own(translator):
    original = "Residents complained that the faucet in the town hall leaked all week, officials said Tuesday."
    draft = 'Residents complained: "The faucet in the town hall leaked all week," officials said Tuesday.'
    issues = harness.lint(draft, original=original, level=3, translator=translator)["issues"]
    assert ("dialect", "faucet") in [(i["kind"], i["phrase"]) for i in issues]


def test_a_mentioned_word_keeps_its_words():
    # a post about the word "faucet" is about "faucet", whatever the Aussie for it
    text = 'The word "faucet" is American. Fill the bucket at the faucet.'
    said = [(i["kind"], i["phrase"]) for i in harness.lint(text, original=text, level=3)["issues"]]
    assert said.count(("dialect", "faucet")) == 1


def test_a_form_about_real_things_is_offered_no_riffs_below_troppo(translator):
    # "creeks, bone dry half the year" is a claim about Yellowstone; a story's creek can take it
    news = ("YELLOWSTONE NATIONAL PARK, Wyo. - Park officials said Tuesday that fishing restrictions on rivers and "
            "streams have been lifted after cooler weather.")
    assert harness.plan(news, embellishment="dinkum", translator=translator)["riffs"] == []
    assert harness.plan(news, embellishment="troppo", translator=translator)["riffs"]
    story = "Once upon a time an old man walked down to the stream behind his hut and sat there all day."
    assert harness.plan(story, embellishment="dinkum", translator=translator)["riffs"]



@pytest.mark.parametrize("original,draft,want", [
    ('The word "faucet" is American.', 'The word "faucet" is American.', 0),
    ('The word "faucet" is American.', 'The words "faucets" are American.', 1),
    ('The word "faucet" is American.', 'The word "faucet" is American. The word "faucet" is also printed.', 1),
    ('The word "faucet" is American. The word "faucet" is printed.',
     'The word "faucet" is American. The word "faucet" is printed.', 0),
])
def test_kept_dialect_words_require_original_surface_and_count(original, draft, want, translator):
    issues = harness.lint(draft, original=original, english="us", translator=translator, suggest=False)["issues"]
    assert len([i for i in issues if i["kind"] == "dialect"]) == want


def test_a_held_dialect_slot_cannot_excuse_a_changed_slot(translator):
    issues = harness.lint('The phrase "his purse" is American.', original='The phrase "her purse" is American.',
                          english="us", translator=translator, suggest=False)["issues"]
    assert any(i["kind"] == "dialect" and i["phrase"] == "his purse" for i in issues)
