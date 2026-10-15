"""Similarity backends: for the engine's concept-detection fallback, and for lookup and gaps.

The default backend uses character trigrams. It has no dependencies and is deterministic, and it catches
spelling and morphological variants ("crazzy", "knackerd"). For meaning, the bundled static model (static.py)
or an installed sentence-transformers model (models.py; `embedder="st:all-MiniLM-L6-v2"` names one directly).
"""

from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache
from typing import Callable, Protocol, Sequence

from .errors import UserError
from .static import bundled


class Embedder(Protocol):
    name: str
    lookup_threshold: float    # the similarity above which lookup trusts a match on meaning
    gaps_confident: float      # the similarity above which gaps trusts its nearest-concept guess

    def similarity(self, a: str, b: str) -> float: ...


@lru_cache(maxsize=16384)
def _ngrams(text: str, n: int) -> tuple[Counter, float]:
    """A text's character n-gram counts and their norm, shared by every NgramEmbedder."""
    padded = f"  {text.lower()}  "
    grams = Counter(padded[i:i + n] for i in range(len(padded) - n + 1))
    return grams, math.sqrt(sum(v * v for v in grams.values()))


class NgramEmbedder:
    name = "char-trigram"
    lookup_threshold = 1.0     # n-grams measure spelling, not meaning: lookup never takes them for a meaning match
    # Measured with scripts/train_embedder.py calibrate on 30 trigger words (leave-one-out) and 30 words no concept
    # covers: with n-grams 7% of unrelated words and 20% of right guesses reach 0.6; with all-MiniLM-L6-v2 no
    # unrelated word did (the highest, "chair" -> SIT_DOWN, scored 0.58) while 53% of right guesses did.
    gaps_confident = 0.6

    def __init__(self, n: int = 3):
        self.n = n

    def _vec(self, text: str) -> tuple[Counter, float]:
        return _ngrams(text, self.n)

    def similarity(self, a: str, b: str) -> float:
        va, na = self._vec(a)
        vb, nb = self._vec(b)
        if not na or not nb:
            return 0.0
        dot = sum(v * vb.get(k, 0) for k, v in va.items())
        return dot / (na * nb)


class NgramIndex:
    """The n-gram cosine of a query against many fixed texts, computed through an inverted index of their grams,
    so only texts sharing a gram with the query are touched. Scores equal NgramEmbedder.similarity's exactly
    (gram counts are integers, so the dot products are exact)."""

    def __init__(self, texts: Sequence[str], n: int = 3):
        self.n = n
        self.norms: list[float] = []
        self.postings: dict[str, list[tuple[int, int]]] = {}
        for i, text in enumerate(texts):
            grams, norm = _ngrams(text, n)
            self.norms.append(norm)
            for g, count in grams.items():
                self.postings.setdefault(g, []).append((i, count))

    def scores(self, query: str) -> dict[int, float]:
        grams, norm = _ngrams(query, self.n)
        if not norm:
            return {}
        dots: dict[int, int] = {}
        for g, q in grams.items():
            for i, count in self.postings.get(g, ()):
                dots[i] = dots.get(i, 0) + q * count
        return {i: dot / (norm * self.norms[i]) for i, dot in dots.items() if self.norms[i]}


def similarity_scorer(embedder: Embedder, texts: Sequence[str]) -> Callable[[str], dict[int, float]]:
    """A function from a query to its similarity with each of texts (by index; absent means 0). Indexed for
    n-grams; one similarity call per text for a model."""
    if isinstance(embedder, NgramEmbedder):
        return NgramIndex(texts, embedder.n).scores
    return lambda query: {i: embedder.similarity(query, t) for i, t in enumerate(texts)}


class SentenceTransformerEmbedder:
    # Calibrated on all-MiniLM-L6-v2 with scripts/train_embedder.py calibrate: a plain trigger scores a median 0.62
    # against its own entry, while a random unrelated entry never passed 0.33; but a query meets the whole
    # dictionary, and its best wrong match there has a median of 0.47. At 0.50 two thirds of right matches pass
    # and 4 in 30 queries let a wrong one in. Another model needs its own calibration.
    lookup_threshold = 0.50
    gaps_confident = 0.6

    def __init__(self, model: str, cache_size: int = 8192):
        from sentence_transformers import SentenceTransformer  # optional dependency

        self.name = f"st:{model}"
        self._model = SentenceTransformer(model)
        # bounded, and owned by the instance: a long-lived MCP server sees endless distinct queries
        self._encode = lru_cache(maxsize=cache_size)(self._encode_uncached)

    def _encode_uncached(self, text: str):
        return self._model.encode(text, normalize_embeddings=True)

    def similarity(self, a: str, b: str) -> float:
        return float(self._encode(a) @ self._encode(b))


def make_embedder(spec: str | None) -> Embedder | None:
    if spec in (None, "", "none"):
        return None
    if spec == "ngram":
        return NgramEmbedder()
    if spec.startswith("st:"):
        return SentenceTransformerEmbedder(spec[3:])
    if spec == "bundled":
        emb = bundled()
        if emb is None:
            raise UserError("this install doesn't carry the bundled model (aussiefy/data/model)")
        return emb
    if spec == "configured":   # what this machine is set up for: an installed model, the bundled one, or none
        from .models import local_embedder

        return local_embedder()
    if spec == "local":   # asked for by name: the installed model or an error, never a quiet stand-in
        from .models import installed_embedder

        return installed_embedder()
    raise UserError(f"unknown embedder {spec!r} (use ngram, none, bundled, local, configured or st:<model>)")
