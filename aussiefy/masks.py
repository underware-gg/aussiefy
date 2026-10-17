"""Masks (O23): the words in a rendering a reader may not want shown in full, with where each one's ending starts, so
a page can hide the stem and keep the ending ("f$%&ed") without a swear list of its own. Only actual profanity is
masked: the dictionary's swear list (swears.yaml)."""

from __future__ import annotations

import re
from typing import Any

from .model import swear_strength

# the endings a masked word keeps, after a stem that is itself a listed swear (O23's fixed set), longest first
ENDINGS = ("ers", "ing", "in'", "es", "ed", "er", "in", "s", "y")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’]*")


def masks(text: str, swears: dict[str, int]) -> list[dict[str, Any]]:
    """Each maskable word in text: its span, where its ending starts (its end, where it keeps none) and the
    vulgarity it needs."""
    out = []
    for m in WORD_RE.finditer(text):
        word = _word(m.group())
        strength = swear_strength(swears, word)
        if not strength:
            continue
        start = m.start()
        out.append({"span": [start, start + len(word)], "ending_start": start + _stem_length(word, swears),
                    "vulgarity": strength})
    return out


def _word(token: str) -> str:
    """The word without a closing quote mark after it; a dropped g keeps its apostrophe ("fuckin'")."""
    bare = token.rstrip("'’")
    return token if bare.lower().endswith("in") and bare != token else bare


def _stem_length(word: str, swears: dict[str, int]) -> int:
    low = word.lower().replace("’", "'")
    for ending in ENDINGS:
        if low.endswith(ending) and swears.get(low[:-len(ending)]):
            return len(word) - len(ending)
    return len(word)
