"""Fixes from the third everyday pass (research/embellishment-pass-2026-10-13/FINDINGS.md)."""

import re
from pathlib import Path

from aussiefy import harness
import pytest

from aussiefy.schema import SchemaError, parse_entry
from aussiefy.text import DATELINE, mentioned_spans

CORPUS = Path(__file__).resolve().parents[1] / "corpus"


def test_a_text_keeps_one_spelling(translator):
    text = ("I baked biscuits for the kids. The biscuits were gone by noon. More biscuits arrived later, and the "
            "biscuits were eaten too.")
    swapped = 0
    for seed in range(6):
        out = translator.translate(text, level=4, seed=seed).text
        spellings = {m.lower().rstrip("s") for m in re.findall(r"\bbi(?:kk|ck)ies?\b", out)}
        assert len(spellings) <= 1, out
        swapped += bool(spellings)
    assert swapped


def test_only_a_listed_spelling_is_kept_throughout(translator):
    """Spellings are data: an entry's `spellings` (bickie for bikkie), never "go walkabout" for "gone
    walkabout" or "a stirrer" for "a shit-stirrer"."""
    d = translator.dictionary
    assert d.entries["bikkie"].spelling_group == {"bikkie", "bickie"}
    assert not d.entries["gone-walkabout"].spelling_group and not d.entries["shit-stirrer"].spelling_group
    with pytest.raises(SchemaError, match="spellings"):
        parse_entry({"id": "x", "form": "x", "concept": "X", "frame": "np", "spellings": ["y"]})


def test_a_text_about_words_holds_its_candidates():
    """The forum post weighing words for 'guys' lists its candidates in quotes and as list items: each is the word
    under discussion, not one to Aussify."""
    text = (CORPUS / "everyday" / "conversational" / "se_feminine_guys.txt").read_text(encoding="utf-8")
    held = {text[a:b].rstrip(".").lower() for a, b in mentioned_spans(text)}
    assert {"guys", "boys", "ladies", "everyone, you all", "gals", "guys and gals"} <= held
    assert mentioned_spans('She called "Help!" and ran. "Very tired," he said.') == []


def test_lookup_finds_an_inflected_term_and_not_its_opposite(translator):
    def forms(q):
        return [r["form"] for r in harness.lookup(q, level=5, short=True, translator=translator)["results"]]

    assert "cove" in forms("coves") and "play up" in forms("playing up")
    assert not [f for f in forms("probably") if "no " in f or "not " in f]
    assert "a mean bastard" not in forms("harmless")


def test_a_name_stays_capitalised_after_an_opener(translator):
    story = ("Cook sailed into the bay in 1770. The crew were very tired and hungry. Cook went ashore with a few "
             "men. They found water and fresh food. Cook was pleased with the place.")
    for seed in range(10):
        assert not re.search(r", cook\b", translator.translate(story, level=5, seed=seed, embellishment="troppo").text)


def test_a_dateline_is_a_dateline():
    for line in ("PARIS (AP) — Talks", "MAMMOTH HOT SPRINGS, Wyo. – The park", "WASHINGTON, Dec. 27.—The",
                 "DETROIT, Dec. 13 (AP).—Henry"):
        assert DATELINE.match(line), line
    for line in ("COVID-19 cases rose", "NASA-funded work", "I -- I don't know"):
        assert not DATELINE.match(line), line


def test_dialogue_in_a_text_with_one_mention_stays_speech():
    text = ('He never liked the word "mate". "Run." "I know." "Stop it." "Good morning." The kids\' toy and the '
            'dogs\' bowls. "Mate," he said.')
    assert [text[a:b] for a, b in mentioned_spans(text)] == ["mate"]


def test_troppo_calls_no_safety_reader_names(translator):
    bears = (CORPUS / "everyday" / "instructions" / "nps_bear_safety.txt").read_text(encoding="utf-8")
    r = translator.translate(bears, level=5, vulgarity=3, embellishment="troppo")
    assert r.embellishment.takes("opener") and not r.embellishment.takes("insult")
    story = (CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8")
    assert translator.translate(story, level=5, embellishment="troppo").embellishment.takes("insult")


def test_a_term_plural_in_form_takes_no_a(translator):
    def out(text):
        return {translator.translate(text, level=5, seed=s, regions=["qld"], embellishment="deadset").text
                for s in range(3)}

    assert not [o for o in out("I bought a swimsuit.") if "a togs" in o]
    assert any("togs" in o for o in out("Pack your swimsuits."))
    # the span's own "a" goes with it, and a word that doesn't change in the plural takes "a"
    assert "It took yonks." in out("It took a long time.") and "We ate heaps of tucker." in out("We ate a lot of food.")
    assert "I caught a barra." in out("I caught a barramundi.") and "It cost a quid." in out("It cost a dollar.")
    assert any("thongs" in o for o in out("A man in sunglasses and flip-flops walked in."))


def test_every_setting_carries_the_general_craft(translator):
    for setting in ("deadset", "dinkum", "troppo"):
        craft = harness.guide(level=5, embellishment=setting, translator=translator)["craft"]
        assert "pile up" in craft and "Australian spelling" in craft and "talk broader than narrators" in craft


def test_a_closed_output_pipe_is_no_error():
    """`aussiefy show "" | head -1`: the reader leaves after one line, and the CLI stops quietly."""
    import subprocess
    import sys

    cli = subprocess.Popen([sys.executable, "-m", "aussiefy.cli", "show", ""], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    cli.stdout.readline()
    cli.stdout.close()   # the reader leaves, as head does
    err = cli.stderr.read().decode()
    assert cli.wait(timeout=60) == 0 and "Traceback" not in err, err


def test_a_subject_stops_at_its_preposition():
    """detect.PREPOSITIONS was defined twice, and the second (for part of speech) hid "near" and "inside" from
    the subject rule."""
    from aussiefy.detect import _noun_before
    from aussiefy.text import tokenize

    for text in ("Everyone near home is lazy", "Everyone inside work is lazy", "Everyone at university is lazy"):
        toks = tokenize(text)
        assert _noun_before(toks, next(t for t in toks if t.norm == "is")) is None, text
    toks = tokenize("The dog is lazy")
    assert _noun_before(toks, toks[2]).text == "dog"
