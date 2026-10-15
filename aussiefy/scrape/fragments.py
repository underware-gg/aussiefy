"""Harvest slang fragments embedded in existing idioms.

"stick out like a country dunny" contains "dunny", and "full as a goog" contains
"goog". This step finds words and short phrases inside entry forms that have no
entry of their own, and stages them with their parent idiom as context. The
usual `tag` then `review` steps infer their meaning, frame and flags. Plain
English words ("like", "out", "lizard") are dropped up front where we can tell,
and the tagger flags the rest.
"""

from __future__ import annotations

import re

from ..model import Dictionary
from ..schema import PLACEHOLDER_RE
from ..text import COMMON_STARTERS
from .normalise import Staged, dictionary_keys, merge_key, unique_id

STOP = COMMON_STARTERS | set("""
a an the of to in on at by for with and or but as like than then so is are was were be been being am
it its his her their my your our out up off over down into from about not no yes some any all
have has had do does did go goes went get got make made take give put come say said see keep
very more most much many few lot lots bit full half short long old new good bad big small
""".split())
JOINERS = {"and", "of", "a", "the"}   # allowed inside multi-word fragments: "frog and toad", "fair suck of the sav"


def _words(form: str) -> list[str]:
    form = PLACEHOLDER_RE.sub(" | ", form)
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*|\|", form)]


def candidate_fragments(form: str, plain: set[str]) -> list[str]:
    """Slang-looking words and 2-4 word runs inside one form."""
    words = _words(form)
    out: list[str] = []

    def slangy(w: str) -> bool:
        lw = w.lower().strip("'")
        return w != "|" and lw not in STOP and lw not in plain and len(lw) > 2

    for i, w in enumerate(words):
        if slangy(w):
            out.append(w)
        # runs that start and end on a slangy word, joined only by small words: "frog and toad"
        for n in (2, 3, 4):
            run = words[i:i + n]
            if len(run) == n and slangy(run[0]) and slangy(run[-1]) and all(
                    x.lower() in JOINERS or slangy(x) for x in run[1:-1]) and "|" not in run:
                out.append(" ".join(run))
    return out


def extract_fragments(dictionary: Dictionary) -> list[Staged]:
    keys, _ = dictionary_keys(dictionary)
    plain = dictionary.plain_words
    staged: dict[str, Staged] = {}
    used_ids = set(dictionary.entries)
    for entry in sorted(dictionary.entries.values(), key=lambda e: e.id):
        if entry.status == "omit" or len(entry.form.split()) < 2:
            continue
        for form in entry.all_forms:
            for frag in candidate_fragments(form, plain):
                key = merge_key(frag)
                if not key or key in keys or key == merge_key(entry.form):
                    continue
                if re.sub(r"(?:'s|s)$", "", key) in keys or key.replace("ing", "e") in keys:
                    continue  # "snags", "dingo's", "whingeing": an inflection of something we have
                item = staged.get(key)
                if item is None:
                    item = staged[key] = Staged(unique_id(frag, used_ids), frag)
                src = f"fragment-of:{entry.id}"
                if src not in item.sources:
                    item.sources.append(src)
                    item.usage.append(entry.form)
                    if entry.gloss:
                        item.source_meanings.append(f"{entry.form}: {entry.gloss}")
    return sorted(staged.values(), key=lambda s: (-len(s.sources), s.form.lower()))
