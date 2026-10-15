"""Harvest candidate entries from an Aussified rewrite of a plain text.

Give it the original and a rewrite (from an agent, the --rewrite cache, or a person). A word-level diff
pairs each changed span with what replaced it ("arrived" -> "rocked up"). Pairs whose new side contains
words the dictionary doesn't already have become staged candidates, with the plain-English side as the
meaning and the sentence as usage. `tag` and `review` take it from there, as for scraped phrases.
"""

from __future__ import annotations

import difflib
import re

from .. import morph
from ..model import Dictionary
from ..terms import fold, restore_g, strip_markup
from .fragments import STOP
from .normalise import Staged, dictionary_keys, merge_key, unique_id

# numbers are words too, so "Oct. 11" against "the 11th of October" lines up instead of leaving "the th"
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text.replace("’", "'"))


def harvest_pairs(original: str, rewrite: str, max_words: int = 8) -> list[tuple[str, str, str]]:
    """(plain span, slang span, slang context) for each changed region of a word-level diff."""
    a, b = _words(original), _words(rewrite)
    sm = difflib.SequenceMatcher(a=[w.lower() for w in a], b=[w.lower() for w in b], autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op not in ("replace", "insert") or not 0 < j2 - j1 <= max_words or i2 - i1 > max_words:
            continue
        context = " ".join(b[max(0, j1 - 4):j2 + 4])
        out.append((" ".join(a[i1:i2]), " ".join(b[j1:j2]), context))
    return out


def _inflected_keys(dictionary: Dictionary) -> set[str]:
    """Keys for every inflection of verb-phrase entries ("rocked up" for "rock up")."""
    out = set()
    for e in dictionary.entries.values():
        if e.frame != "vp":
            continue
        for form in e.all_forms:
            head, _, rest = strip_markup(form).partition(" ")
            for surface in morph.verb_forms(head):
                out.add(merge_key(f"{surface} {rest}"))
    return out


def harvest(original: str, rewrite: str, dictionary: Dictionary, source: str = "harvest") -> list[Staged]:
    keys, _ = dictionary_keys(dictionary)
    keys = set(keys) | _inflected_keys(dictionary)
    plain = dictionary.plain_words
    staged: dict[str, Staged] = {}
    used = set(dictionary.entries)
    for before, after, context in harvest_pairs(original, rewrite):
        new_words = [w for w in after.lower().split() if w not in STOP and w not in plain
                     and not any(ch.isdigit() for ch in w)]
        key = merge_key(after)
        if not new_words or not key or key in keys:
            continue  # nothing slangy, or we already have it
        item = staged.get(key)
        if item is None:
            item = staged[key] = Staged(unique_id(after, used), after, sources=[source])
        meaning = f"replaces: {before}" if before else "added (no plain-English counterpart)"
        if meaning not in item.source_meanings:
            item.source_meanings.append(meaning)
        item.usage.append(context)
    return list(staged.values())


def target_recall(original: str, target: str, outputs: list[str], dictionary: Dictionary) -> list[tuple[str, str, bool]]:
    """For each slang span the target introduced, whether any engine output also has it.

    A span counts as reproduced when all its content words appear in one output, so inflection,
    drawl and word order around it don't matter. The result is (plain, slang, reproduced) rows:
    a benchmark for how close the dictionary gets to a good human or LLM translation.
    """
    plain_vocab = dictionary.plain_words
    rows = []
    seen = set()
    lowered = [restore_g(fold(o)).replace("-", " ") for o in outputs]
    for before, after, _ in harvest_pairs(original, target):
        content = [w for w in after.lower().replace("-", " ").split()
                   if w not in STOP and w not in plain_vocab and len(w) > 2]
        if not content or after.lower() in seen:
            continue
        seen.add(after.lower())
        hit = any(all(restore_g(w) in o for w in content) for o in lowered)
        rows.append((before, after, hit))
    return rows


def vocabulary_overlap(target: str, outputs: list[str], dictionary: Dictionary) -> list[tuple[str, bool]]:
    """Dictionary phrases the target uses, and whether the engine's outputs use them too.

    Robust to targets that restructure or extend the text (no alignment needed).
    """
    def norm(t: str) -> str:
        t = fold(t).replace("-", " ")
        return " " + restore_g(re.sub(r"[^a-z' ]+", " ", t)) + " "

    tgt = norm(target)
    outs = [norm(o) for o in outputs]
    rows = {}
    for e in dictionary.entries.values():
        if e.status == "omit":
            continue
        for form in e.all_forms:
            f = norm(strip_markup(form)).strip()
            if len(f) < 4 or f in rows or f" {f} " not in tgt:
                continue
            rows[f] = any(f" {f} " in o for o in outs)
    return sorted(rows.items())
