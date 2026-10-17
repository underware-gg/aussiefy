"""Masks (O23): the words in a rendering a reader may not want shown in full, with where each one's ending starts, so
a page can hide the stem and keep the ending ("f$%&ed") without a swear list of its own. Only actual profanity is
masked: the dictionary's swear list (swears.yaml), the compounds its rated words build on a listed swear
(Dictionary.swear_compounds: "fuckwit", "shitfight"), and the mask words an entry authors where its rudeness isn't a
listed word ("wanker"). Innuendo is never masked."""

from __future__ import annotations

import re
from typing import Any

from .model import MASK_ENDINGS, swear_strength

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’]*")


def masks(text: str, swears: dict[str, int], compounds: dict[str, int] | None = None,
          words: dict[str, int] | None = None) -> list[dict[str, Any]]:
    """Each maskable word in text: its span, where its ending starts (its end, where it keeps none) and the
    vulgarity it needs. words: the mask words of the entries rendered in text, with their entries' vulgarity. A
    word keeps its ending (-s, -es, -ed, -er, -ers, -ing, -in', -in, -y) only after a stem that is itself a listed
    swear or a mask word; any other, a compound included, is masked whole after its first letter."""
    compounds, words = compounds or {}, words or {}
    out = []
    for m in WORD_RE.finditer(text):
        word = _word(m.group())
        low = word.lower().replace("’", "'")
        strength = max(swear_strength(swears, low), _inflected(low, compounds), _inflected(low, words))
        if strength:
            start = m.start()
            out.append({"span": [start, start + len(word)], "ending_start": start + _stem_length(low, swears, words),
                        "vulgarity": strength})
    return out


def _word(token: str) -> str:
    """The word without a closing quote mark after it; a dropped g keeps its apostrophe ("fuckin'")."""
    bare = token.rstrip("'’")
    return token if bare.lower().endswith("in") and bare != token else bare


def _inflected(low: str, table: dict[str, int]) -> int:
    """How strong a word is as one of table's, or one of them with an ending ("wankers", "bullshitters")."""
    found = table.get(low, 0)
    for ending in MASK_ENDINGS:
        if low.endswith(ending):
            found = max(found, table.get(low[:-len(ending)], 0))
    return found


def _stem_length(low: str, swears: dict[str, int], words: dict[str, int]) -> int:
    for ending in MASK_ENDINGS:
        stem = low[:-len(ending)]
        if low.endswith(ending) and (swears.get(stem) or stem in words):
            return len(stem)
    return len(low)
