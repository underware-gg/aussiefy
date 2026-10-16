"""Sentence alignment: which sentences of a retelling stand for each sentence of its original. Pure; verify reads
it to find what a translation dropped, and yarn mode to check a planned phrase sits where it was planned."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .text import sentences, tokenize

_STOP = set("""a an the and or but if so of to in on at by for with from as is are was were be been being am it its
this that these those he she they we you i me him her them us my your his our their not no do does did have has
had will would can could shall should may might must there here then than too very just""".split())


BAND_MAX = 40   # sentences either side of an original sentence's place that may hold its counterpart


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Where the text's sentences that have words in them start and end."""
    return [(s[0].start, s[-1].end) for s in sentences(tokenize(text)) if any(t.is_word for t in s)]


def sentence_texts(text: str) -> list[str]:
    """The text's sentences that have words in them."""
    return [text[a:b] for a, b in sentence_spans(text)]


def content_words(sentence: str) -> set[str]:
    """What a sentence is about: its words of three letters or more, less the commonest."""
    return {w for w in re.findall(r"[a-z0-9]+", sentence.lower()) if w not in _STOP and len(w) > 2}


@dataclass(frozen=True)
class Counterpart:
    """An original sentence's best counterpart in the translation: up to three consecutive sentences near where
    it should be (retellings split, merge and shuffle sentences locally)."""
    start: int                # first translation sentence of the window
    end: int                  # one past the last
    retained: float           # share of the original's content words the window keeps
    similarity: float | None  # meaning similarity (None without a meaning model)


def counterparts(original: list[str], translation: list[str], embedder=None, *,
                 max_sentences: int = 3) -> list[Counterpart | None]:
    """For each original sentence, its best counterpart (None if the translation is empty)."""
    n, m = len(original), len(translation)
    if not m:
        return [None] * n
    words = [content_words(s) for s in translation]
    # retellings shuffle locally: look a fifth of the way either side of where it should be, but no further
    # than BAND_MAX sentences, so a long document doesn't search most of itself for each sentence
    band = min(max(6, m // 5), BAND_MAX)
    windows = {(j, k): set().union(*words[j:k]) for j in range(m) for k in range(j + 1, min(m, j + max_sentences) + 1)}
    found = []
    for i, sentence in enumerate(original):
        want = content_words(sentence)
        centre = round(i * m / max(n, 1))
        best: tuple[float, int, int] | None = None
        for j in range(max(0, centre - band), min(m, centre + band + 1)):
            for k in range(j + 1, min(m, j + max_sentences) + 1):
                got = windows[j, k]
                retained = len(want & got) / len(want) if want else float(not got)
                # Prefer retained words, then tight windows, then the expected sentence position.
                if best is None or (retained, -(k - j), -abs(j - centre)) > (
                        best[0], -(best[2] - best[1]), -abs(best[1] - centre)):
                    best = (retained, j, k)
        retained, j, k = best
        sim = embedder.similarity(sentence, " ".join(translation[j:k])) if embedder else None
        found.append(Counterpart(j, k, retained, sim))
    return found
