"""When two spellings are the same term: the one rule lookup, yarn mode's declined phrases and the research
rounds share. (The scrape pipeline merges raw scraped variants with its own, looser scrape.normalise.merge_key.)
Also the text-level forms of the rule: a form as plain words (strip_markup), the dropped g put back (restore_g),
and whether a rewrite kept a planned phrase (phrase_kept).

form_key("Chuck {poss} wobbly") == form_key("chuck your wobbly") == form_key("a chuck yer wobbly"), and
"spruiking", "spruikin'" and "spruikin" are one term. Slots, trigger markup (@4, !exclusions), possessives,
a leading article, curly quotes, punctuation, "'n" and the dropped g all fall away.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable

from .schema import PLACEHOLDER_RE

if TYPE_CHECKING:
    from .model import PhoneticRule

POSSESSIVES = r"(?:his|her|their|my|your|yer|its|our|me|one's)"


def fold(text: str) -> str:
    """Lower case, straight apostrophes, single spaces: the comparison every other rule starts from."""
    t = str(text).lower().replace("’", "'").replace("‘", "'")
    return " ".join(t.split())


def _pattern_text(text: str) -> str:
    return re.sub(r"@\d|(?<!\w)(?:!\S+|\^\w+)", " ", fold(text))


def strip_markup(text: str) -> str:
    """A trigger or form as plain words: no intensity ("great@4"), sense exclusions ("!war|wars") or slots."""
    t = _pattern_text(text)
    return " ".join(PLACEHOLDER_RE.sub(" ", t).split())


def restore_g(text: str) -> str:
    """The dropped g put back ("spruikin'" -> "spruiking", "goin' on" -> "going on"), so a drawled word matches its
    plain spelling. Only with the apostrophe: a bare "noggin" is its own word."""
    return re.sub(r"\b(\w+)in'(?!\w)", r"\1ing", text)


def form_key(text: str) -> str:
    """The spelling-insensitive key of a term or dictionary form."""
    t = _pattern_text(text)
    t = re.sub(r"\{poss\}self", "self", t)                      # top {poss}self ~ top yourself
    t = PLACEHOLDER_RE.sub(" ", t)
    t = re.sub(r"\b(?:your|my|him|her|them|our|it)sel(?:f|ves)\b", "self", t)
    t = re.sub(r"[,.!?;:\"()]", " ", t)
    t = re.sub(rf"\b{POSSESSIVES}\b", " ", t)                    # off his tree ~ off {poss} tree
    t = re.sub(r"(?<=\s)'n'?(?=\s)", "and", f" {t} ")             # kit 'n caboodle ~ kit and caboodle
    t = re.sub(r"\b(\w{3,})(?:ing|in')(?=\s|$)", r"\1in", t)       # spruiking ~ spruikin' ~ spruikin
    t = re.sub(r"^(?:the|a|an|some) ", "", " ".join(t.split()))
    return t.strip(" '")


def _words(text: str) -> list[str]:
    """A text's words in form_key spelling, with any dropped g put back first ("goin'" is "going")."""
    return re.findall(r"[a-z0-9]+", form_key(restore_g(fold(text))))


def phrase_kept(text: str, phrase: str, phonetic: Iterable[PhoneticRule]) -> bool:
    """Whether a rewrite kept a planned phrase: every content word of it (four letters or more, in form_key
    spelling) starts a word of the text, so drawl ("pull yer head in"), the dropped g ("carryin' on") and
    inflection ("chucked a wobbly") still count. A word the dictionary's phonetic rules may respell away (have ->
    'ave, kind of -> kinda) is no evidence either way, so it isn't required."""
    have, words = _words(text), _words(phrase)
    respelt: set[str] = set()
    for rule in phonetic:
        drawled = rule.pattern.sub(rule.replace, phrase)
        if drawled != phrase:
            respelt |= set(words) - set(_words(drawled))
    for word in words:
        if len(word) < 4 or word in respelt:
            continue
        stem = word[:-2] if word.endswith("in") and len(word) >= 5 else word   # drinkin ~ drinks
        if not any(w.startswith(stem) for w in have):
            return False
    return True
