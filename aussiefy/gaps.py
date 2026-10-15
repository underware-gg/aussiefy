"""Find the dictionary's gaps: the words the engine keeps leaving in plain English.

A maintainer's tool, not an agent's. Run the engine over a corpus and collect the content words in spans it
didn't touch, ranked by how often they appear and whether they read as formal register. For each gap it
guesses the nearest existing concept, so a curator can tell "add a trigger to CRY" from "this needs a new
concept". The guess uses the embedder in use (`aussiefy embedder status`): the bundled Aussie model by default,
which matches meaning rather than spelling, or character n-grams, or an installed sentence-transformers model.

Given an Aussified draft as well (`--draft`), it also lists the lines a writer left in the original wording,
which is where an agent's draft is weakest.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .context import FORMAL_RE
from .embed import Embedder, NgramEmbedder, make_embedder
from .engine import Translator, default_translator
from .model import Dictionary
from .terms import restore_g, strip_markup
from .text import COMMON_STARTERS, capital_is_positional, sentences, tokenize

STOPWORDS = COMMON_STARTERS | set("""
about above after again against all also any around as at away back because before being below between both
by came come down during each even every few for from further get got go going gone into just like made make
more most much near never now of off on once only other out over own same some such than through to too under
until up upon very way while with without yet whose whom one two three four five six seven eight nine ten said says say
""".split())




@dataclass
class Gap:
    word: str
    count: int = 0
    formal: bool = False
    texts: set[str] = field(default_factory=set)
    examples: list[str] = field(default_factory=list)
    concept: str | None = None
    similarity: float = 0.0
    trigger_of: str | None = None   # a concept that already lists this word as a trigger
    confident: float = NgramEmbedder.gaps_confident   # the cut-off of the embedder that guessed

    def to_dict(self) -> dict[str, Any]:
        return {"word": self.word, "count": self.count, "formal": self.formal, "texts": sorted(self.texts),
                "nearest_concept": self.concept, "similarity": round(self.similarity, 2),
                "confident": self.similarity >= self.confident,
                "verdict": self.verdict, "examples": self.examples[:2]}

    @property
    def verdict(self) -> str:
        if self.trigger_of:
            return "already a trigger: guarded or not rolled"
        if self.similarity >= self.confident:
            return "add a trigger to the nearest concept?"
        return "new concept, or leave it plain"


def _lemma(word: str) -> str:
    for suffix, repl in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)] + repl
    return word


def find_gaps(texts: dict[str, str], level: int = 5, translator: Translator | None = None,
              embedder: Embedder | None = None, min_count: int = 1, limit: int = 40) -> list[Gap]:
    """Content words the engine left alone across `texts` ({name: text}), most promising first."""
    tr = translator or default_translator()
    gaps: dict[str, Gap] = {}
    # a word capitalised mid-sentence anywhere is a name ("Moloch", "Goldilocks"), even at a sentence start
    names = {t.text.lower() for text in texts.values() for sent in sentences(tokenize(text))
             for i, t in enumerate(sent) if t.is_word and t.text[:1].isupper() and not capital_is_positional(sent, i)}
    for name, text in texts.items():
        result = tr.translate(text, level=level, seed=0)
        touched = [r.span for r in result.records if r.substituted]
        for sent in sentences(tokenize(text)):
            line = text[sent[0].start:sent[-1].end]
            for i, tok in enumerate(sent):
                if not tok.is_word or any(a <= tok.start < b for a, b in touched):
                    continue
                low = tok.text.lower()
                if low in STOPWORDS or low in names or len(low) < 4 or not low.isalpha():
                    continue
                if tok.text[:1].isupper() and i > 0:      # a name, not a gap
                    continue
                key = _lemma(low)
                gap = gaps.setdefault(key, Gap(key))
                gap.count += 1
                gap.formal = gap.formal or bool(FORMAL_RE.search(low))
                gap.texts.add(name)
                if len(gap.examples) < 2 and line not in gap.examples:
                    gap.examples.append(line)
    ranked = sorted((g for g in gaps.values() if g.count >= min_count),
                    key=lambda g: (-(g.count * (1.5 if g.formal else 1.0) * len(g.texts)), g.word))[:limit]
    _nearest_concepts(ranked, tr, embedder or NgramEmbedder())
    return ranked


def concept_labels(dictionary: Dictionary) -> dict[str, list[str]]:
    """What a gap word is compared with to find its nearest concept: each concept's description, then its first
    triggers per frame as plain words. scripts/train_embedder.py scores the bundled model's gaps cut-off on these."""
    return {cid: [concept.description] + [strip_markup(p) for patterns in concept.triggers.values()
                                          for p in patterns[:6]]
            for cid, concept in dictionary.concepts.items()}


def _nearest_concepts(gaps: list[Gap], tr: Translator, embedder: Embedder) -> None:
    labels = concept_labels(tr.dictionary)
    trigger_words: dict[str, str] = {}
    for cid, ts in labels.items():
        for t in ts[1:]:
            for w in re.findall(r"[a-z]+", t.lower()):
                trigger_words.setdefault(_lemma(w), cid)
    for gap in gaps:
        gap.confident = embedder.gaps_confident
        gap.trigger_of = trigger_words.get(gap.word)
        best = max(((max(embedder.similarity(gap.word, t) for t in ts if t), cid) for cid, ts in labels.items()),
                   default=(0.0, None))
        gap.similarity, gap.concept = best
        if gap.trigger_of:
            gap.concept, gap.similarity = gap.trigger_of, max(gap.similarity, 1.0)


def literal_lines(draft: str, original: str, share: float = 0.6) -> list[dict[str, Any]]:
    """Lines of an Aussified draft still mostly in the original's wording (shared word 3-grams)."""
    def grams(text: str) -> set[tuple[str, ...]]:
        words = re.findall(r"[a-z']+", restore_g(text.lower()))
        return {tuple(words[i:i + 3]) for i in range(len(words) - 2)}

    orig = grams(original)
    # refrains (3-grams the original repeats) are deliberate; keeping them isn't a weakness
    words = re.findall(r"[a-z']+", original.lower())
    counts = Counter(tuple(words[i:i + 3]) for i in range(len(words) - 2))
    refrains = {g for g, n in counts.items() if n >= 3}
    out = []
    for sent in sentences(tokenize(draft)):
        line = draft[sent[0].start:sent[-1].end]
        g = grams(line) - refrains
        if len(g) >= 3:
            kept = len(g & orig) / len(g)
            if kept >= share:
                out.append({"line": line, "original_wording": round(kept, 2)})
    return out


def report(texts: dict[str, str], level: int = 5, embedder_spec: str | None = None, limit: int = 40,
           drafts: dict[str, str] | None = None, translator: Translator | None = None) -> dict[str, Any]:
    tr = translator or default_translator()
    # an explicit --embedder wins; otherwise the translator's meaning model; otherwise n-grams
    embedder = (make_embedder(embedder_spec) if embedder_spec else tr.lookup_embedder) or NgramEmbedder()
    gaps = find_gaps(texts, level=level, translator=tr, embedder=embedder, limit=limit)
    out: dict[str, Any] = {"level": level, "embedder": embedder.name,
                           "gaps": [g.to_dict() for g in gaps]}
    if drafts:
        out["literal_lines"] = {name: literal_lines(draft, texts[name]) for name, draft in drafts.items()}
    return out
