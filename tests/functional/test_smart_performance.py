"""Meaning fallback keeps exact scores and decisions while skipping impossible pattern shapes."""

import pytest

from aussiefy import Translator
from aussiefy.detect import fallback_scorer
from aussiefy.embed import NgramEmbedder, similarity_scorer
from aussiefy.matcher import compile_pattern
from aussiefy.static import bundled


def test_meaning_scorer_preserves_original_indices_and_skips_impossible_shapes():
    patterns = [compile_pattern(text, "predicate_adj", ("TIRED",), 3)
                for text in ("exhausted", "tired", "sleepy", "very tired", "weary !of", "tired|weary")]

    class RecordingEmbedder:
        def __init__(self):
            self.calls = []

        def similarity(self, query, text):
            self.calls.append((query, text))
            return 0.75

    emb = RecordingEmbedder()
    scores = fallback_scorer(emb, patterns)("weary")
    assert list(scores) == [1, 2, 4, 5]
    assert list(scores.values()) == [0.75] * 4
    assert emb.calls == [("weary", patterns[i].text) for i in [1, 2, 4, 5]]


def test_fallback_ngram_scores_are_unchanged(dictionary):
    patterns = dictionary.fallback_patterns
    emb = NgramEmbedder()
    reference = similarity_scorer(emb, [p.text for p in patterns])
    scorer = fallback_scorer(emb, patterns)
    for query in ("exhaustedd", "under the", "less", "not working", "日本語", ""):
        assert scorer(query) == reference(query)


def test_static_dot_product_scores_are_exact(dictionary):
    emb = bundled()
    for query in ("exhaustedd", "under the", "less", "not working", "café", "日本語", ""):
        query_vector = emb.encode(query)
        for p in dictionary.fallback_patterns:
            expected = sum(x * y for x, y in zip(query_vector, emb.encode(p.text)))
            assert emb.similarity(query, p.text) == expected


@pytest.mark.parametrize("text", [
    "He was exhaustedd. She is lethargic today. I am discombobulated and apprehensive.",
    "I'm not tired. He was working. She is less happy. They are under the table.",
    "He is exhaustedd, but the plan is crazy. Are you weary?",
    "He was very tierd and utterly worn out. She is tired of waiting.",
    "I'm very tired. Let's go to the pub for a beer after work. You're crazy!",
])
@pytest.mark.parametrize("level,seed", [(2, 0), (5, 42)])
def test_bundled_translation_matches_exhaustive_scores(dictionary, text, level, seed):
    emb = bundled()

    class ReferenceEmbedder:
        def similarity(self, query, pattern):
            return sum(x * y for x, y in zip(emb.encode(query), emb.encode(pattern)))

    reference = Translator(dictionary, lookup_embedder=None)
    reference._scorers["bundled"] = similarity_scorer(
        ReferenceEmbedder(), [p.text for p in dictionary.fallback_patterns])
    optimised = Translator(dictionary, lookup_embedder=None)
    options = dict(level=level, seed=seed, vulgarity=1, embellishment=1, embedder="bundled")
    assert optimised.translate(text, **options).to_dict() == reference.translate(text, **options).to_dict()
