"""Checks shared by the reference-text tests (tests/corpus/reference/ and the local copyrighted texts)."""

import re

# Words that drop to lower case after an opener ("Strewth, the wolf...", not "Strewth, The wolf...").
_LOWER_AFTER_OPENER = {"once", "under", "up", "down", "the", "then", "when", "on", "at", "but", "and", "nobody",
                       "someone", "she", "he", "it", "they", "we", "you", "where", "a", "settle", "piss", "get"}


def assert_well_formed(src: str, r, where: str) -> None:
    """A translation of src keeps its line structure, punctuation, a/an agreement and garnish spacing."""
    out = r.text
    assert out.count("\n") == src.count("\n"), f"{where}: line structure changed"
    assert not re.search(r"[.!?,]\s*[.,]|,\s*[!?]|\.\"\.|\s,", out), f"{where}: broken punctuation: {out}"
    assert not re.search(r"\b[Aa] [aeiou]\w", out.replace("a one", "")), f"{where}: a/an: {out}"
    for placement in ("opener", "tag"):
        at = sorted(g.sentence for g in r.garnish if g.placement == placement and g.text)
        assert all(b - a > 1 for a, b in zip(at, at[1:])), f"{where}: adjacent {placement}s"
    for g in r.garnish:
        if g.placement == "opener" and g.text:
            after = re.search(re.escape(g.text[:1].upper() + g.text[1:]) + r", (\S+)", out)
            if after:
                word = after.group(1)
                assert not (word[0].isupper() and word.lower().strip(",.") in _LOWER_AFTER_OPENER), \
                    f"{where}: opener not followed by lower case: {out[:120]}"
