import pytest

from aussiefy.detect import detect, resolve_overlaps
from aussiefy.matcher import PatternIndex, compile_pattern, match_at
from aussiefy.text import sentences, tokenize


def dets(text, dictionary):
    sent = sentences(tokenize(text))[0]
    return sent, resolve_overlaps(detect(sent, dictionary.index))


def test_tokenizer_splits_contractions_and_keeps_offsets():
    text = "You're mad, aren't you? He's got it."
    toks = tokenize(text)
    assert [t.norm for t in toks][:3] == ["you", "are", "mad"]
    assert all(text[t.start:t.end] == t.text for t in toks)
    assert [t.norm for t in toks if t.text == "'s"] == ["has"]
    assert len(sentences(toks)) == 2


def test_vp_pattern_matches_inflections():
    p = compile_pattern("overreact", "vp", ("OVERREACT",), 3)
    toks = tokenize("they are overreacting")
    m = match_at(p, toks, 2)
    assert m and m.inflection == "ing"
    assert match_at(p, tokenize("he overreacted"), 1).inflection == "past"


def test_np_pattern_matches_plural():
    p = compile_pattern("biscuit", "np", ("BISCUIT",), 3)
    assert match_at(p, tokenize("biscuits"), 0).inflection == "plural"


def test_slots_and_optional_words():
    p = compile_pattern("run off {poss} feet", "predicate_adj", ("BUSY",), 4)
    m = match_at(p, tokenize("run off my feet"), 0)
    assert m.captures["poss"].text == "my"
    q = compile_pattern("really? tired@2", "predicate_adj", ("TIRED",), 3)
    assert q.intensity == 2
    assert match_at(q, tokenize("tired"), 0) and match_at(q, tokenize("really tired"), 0)


def test_index_finds_slot_first_patterns():
    p = compile_pattern("{subj} {be} kidding", "clause", ("TEASE",), 3)
    found = PatternIndex([p]).find(tokenize("you are kidding"))
    assert found and found[0].captures["subj"].text == "you"


def test_predicate_needs_a_linking_verb(dictionary):
    _, d = dets("He is very busy today.", dictionary)
    busy = [x for x in d if "BUSY" in x.concepts]
    assert [(x.frame, x.intensity) for x in busy] == [("predicate_adj", 4)]
    assert "flat-out-lizard" in busy[0].direct  # its own `replaces` ("very busy@4") matched
    _, d = dets("The busy road was loud.", dictionary)
    assert not [x for x in d if "BUSY" in x.concepts]


def test_negated_predicate_is_left_alone(dictionary):
    _, d = dets("I'm not tired.", dictionary)
    assert not [x for x in d if "TIRED" in x.concepts]


def test_intensifier_absorbed_and_boosts(dictionary):
    sent, d = dets("I'm extremely tired.", dictionary)
    tired = next(x for x in d if "TIRED" in x.concepts)
    assert sent[tired.start].text == "extremely" and tired.intensity == 4


def test_question_inversion_detected(dictionary):
    _, d = dets("Are you crazy?", dictionary)
    crazy = next(x for x in d if "CRAZY" in x.concepts)
    assert crazy.question and crazy.captures["subj"].text == "you"


def test_coordinated_predicate_borrows_verb(dictionary):
    _, d = dets("You're stupid and all talk.", dictionary)
    assert {c for x in d for c in x.concepts} >= {"STUPID", "ALL_TALK"}


def test_interjection_must_stand_alone(dictionary):
    _, d = dets("No problem, I'll do it.", dictionary)
    assert any("NO_PROBLEM" in x.concepts for x in d)
    _, d = dets("It's no problem for me to do it.", dictionary)
    assert not any("NO_PROBLEM" in x.concepts for x in d)


def test_embedding_fallback_catches_misspelling(dictionary):
    from aussiefy.embed import NgramEmbedder, similarity_scorer

    sent = sentences(tokenize("He is exhaustedd."))[0]
    scorer = similarity_scorer(NgramEmbedder(), [p.text for p in dictionary.fallback_patterns])
    found = detect(sent, dictionary.index, scorer, dictionary.fallback_patterns)
    hit = [x for x in found if x.method == "embedding"]
    assert hit and "TIRED" in hit[0].concepts and hit[0].score >= 0.72
    assert not [x for x in detect(sent, dictionary.index) if x.method == "embedding"]


def test_ngram_index_scores_equal_the_embedders(dictionary):
    from aussiefy.embed import NgramEmbedder, NgramIndex

    texts = [p.text for p in dictionary.fallback_patterns]
    emb, index = NgramEmbedder(), NgramIndex(texts)
    for query in ("exhaustedd", "very tierd", "knackered", "x"):
        scores = index.scores(query)
        for i, t in enumerate(texts):
            assert scores.get(i, 0.0) == emb.similarity(query, t), (query, t)


def test_idioms_for_is_every_idiom_carrying_a_concept_once_in_dictionary_order(dictionary):
    for concepts in [("TIRED",), ("TIRED", "BUSY"), ("NO_SUCH_CONCEPT",)] + [tuple(e.concept) for e in dictionary.idioms[:50]]:
        scanned = [e for e in dictionary.idioms if set(concepts) & set(e.concept)]
        assert dictionary.idioms_for(concepts) == scanned, concepts


@pytest.mark.parametrize("text,entry_id", [
    ("She reimbursed him yesterday.", "square-person-up"),
    ("They are queasy.", "crook-in-the-guts"),
    ("It is just right.", "just-the-shot"),
    ("He is exhausted.", "out-on-poss-feet"),
    ("They toiled all day.", "work-like-billy-o"),
    ("Start work.", "get-cracking"),
])
def test_persona_vocabulary_reaches_its_reviewed_meaning(translator, text, entry_id):
    result = translator.translate(text, level=5, seed=0, embellishment="deadset")
    assert entry_id in {c.entry.id for record in result.records for c in record.eligible}
    if entry_id == "square-person-up":
        assert any(record.term == "squared him up" for record in result.records)


@pytest.mark.parametrize("text,entry_id", [
    ("I will repay your kindness.", "square-person-up"),
    ("She squared up for a fight.", "square-person-up"),
    ("The fumes are nauseous.", "crook-in-the-guts"),
    ("She is sick.", "crook-in-the-guts"),
    ("The battery is exhausted.", "out-on-poss-feet"),
    ("She is a perfect square.", "just-the-shot"),
    ("The engine started working.", "get-cracking"),
    ("They begin work tomorrow.", "get-cracking"),
])
def test_persona_vocabulary_does_not_expand_to_unreviewed_senses(translator, text, entry_id):
    result = translator.translate(text, level=5, seed=0, embellishment="deadset")
    assert entry_id not in {c.entry.id for record in result.records for c in record.eligible}
