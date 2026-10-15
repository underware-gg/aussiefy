from aussiefy.gaps import find_gaps, literal_lines


def test_gaps_skip_names_and_stopwords_and_flag_known_triggers(translator):
    texts = {"story": "Moloch sat in the chair. The chair was old. Then Moloch saw the chair break. "
                      "\"Help!\" Moloch screamed at the porridge."}
    gaps = {g.word: g for g in find_gaps(texts, translator=translator)}
    assert "chair" in gaps and gaps["chair"].count == 3
    assert "moloch" not in gaps and "then" not in gaps


def test_literal_lines_ignore_refrains():
    original = "Moloch whose eyes are blind! Moloch whose mind is machinery! Moloch whose love is oil!"
    draft = "Moloch whose eyes are blind! Moloch whose noggin's nothin' but cogs! Moloch whose love is oil!"
    lines = [x["line"] for x in literal_lines(draft, original)]
    assert "Moloch whose eyes are blind!" in lines
    assert not any("noggin" in line for line in lines)


def test_known_triggers_are_recognised_by_word_not_similarity(translator):
    gaps = {g.word: g for g in find_gaps({"t": '"Help!" she screamed. "Go!" he screamed.'},   # speech verbs: guarded
                                         translator=translator)}
    assert gaps["scream"].trigger_of == "SCREAM" and gaps["scream"].verdict.startswith("already a trigger")
