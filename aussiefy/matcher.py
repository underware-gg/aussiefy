"""Compile plain-English trigger patterns and match them against token streams.

Pattern syntax (used in concept `triggers` and entry `replaces`):

    swamped            literal word, matched against the normalised token
    run off {poss} feet  {slot} captures a pronoun / verb / possessive
    believe {np} to be   {np} captures a short noun phrase (1-5 words) up to the next anchor
    a|an               alternatives
    really?            optional word
    !war|deal          neither of the next two words may be one of these (zero-width; blocks a
                       sense, so "great !war" skips both "great war" and "great civil war")
    snowed under@4     trailing @N sets the intensity this paraphrase expresses

In `np` patterns the last word also matches its plural; in `vp` patterns the
first word is a verb lemma and matches any inflection ("overreact" matches
"overreacting"). The inflection is recorded so realisation can copy it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import morph
from .text import COMMON_STARTERS, Token, tokenize

INTENSITY_RE = re.compile(r"@([1-5])\s*$")


@dataclass(frozen=True)
class Element:
    kind: str                     # "lit" | "slot" | "not"
    values: frozenset[str] = frozenset()
    optional: bool = False
    slot: str = ""
    role: str = ""                # "head_verb" | "head_noun" | ""
    forms: tuple[tuple[str, str], ...] = ()   # surface -> inflection name, for heads
    reach: int = 2                # "not" only: how many tokens ahead it looks ("!x" two, "!=x" the next one)


@dataclass(frozen=True)
class Pattern:
    text: str
    elements: tuple[Element, ...]
    frame: str
    concepts: tuple[str, ...]
    intensity: int
    entry_id: str | None = None   # set when the pattern comes from an entry's `replaces`
    person_only: bool = False     # "^person": the subject must be a person ("the tank is full" isn't)
    before_modifier: bool = False  # "^adj": the next word must be an adjective or adverb ("really cold", not
                                   # "really think" or "really it was")

    @property
    def slots(self) -> set[str]:
        return {e.slot for e in self.elements if e.kind == "slot"}


@dataclass
class Match:
    pattern: Pattern
    start: int                    # token index (inclusive)
    end: int                      # token index (exclusive)
    captures: dict[str, Token] = field(default_factory=dict)
    inflection: str = ""          # verb form name, or "plural" / "singular" / "written_plural" (a trigger
                                  # written as a plural, "wild horses": its number comes from the entry)


def compile_pattern(text: str, frame: str, concepts: tuple[str, ...], default_intensity: int,
                    entry_id: str | None = None) -> Pattern:
    intensity = default_intensity
    m = INTENSITY_RE.search(text)
    if m:
        intensity = int(m.group(1))
        text = text[: m.start()].rstrip()
    person_only = " ^person" in f" {text}"
    before_modifier = " ^adj" in f" {text}"
    text = text.replace("^person", "").replace("^adj", "").strip()
    raw_parts = text.split()
    last_word = max((i for i, p in enumerate(raw_parts) if not p.startswith("!")), default=0)
    elements: list[Element] = []
    for idx, part in enumerate(raw_parts):
        slot = re.fullmatch(r"\{(\w+)\}", part)
        if slot:
            if slot.group(1) not in SLOT_MATCHERS:
                raise ValueError(f"unknown slot {part} in pattern {text!r}")
            elements.append(Element("slot", slot=slot.group(1)))
            continue
        if part.startswith("!") and len(part) > 1:
            if idx == 0:
                raise ValueError(f"pattern {text!r} cannot start with a negative lookahead")
            reach, body = (1, part[2:]) if part.startswith("!=") else (2, part[1:])
            # each value as the tokeniser reads it ("couldn't" -> could, "it's" -> it), so none silently never matches
            values = frozenset(toks[0].norm for toks in (tokenize(w) for w in body.split("|") if w) if toks)
            elements.append(Element("not", values, reach=reach))
            continue
        optional = part.endswith("?") and len(part) > 1
        part = part.rstrip("?") if optional else part
        # a literal may itself tokenise into several tokens ("you're" -> you + are)
        alts = [a for a in part.split("|") if a]
        tokenised = [[t.norm for t in tokenize(a)] for a in alts]
        if all(len(t) == 1 for t in tokenised):
            values = frozenset(t[0] for t in tokenised)
            role, forms = "", ()
            if frame == "vp" and idx == 0 and len(alts) == 1:
                role = "head_verb"
                forms = tuple(morph.verb_forms(alts[0].lower()).items())
                values = frozenset(s for s, _ in forms)
            elif frame == "np" and idx == last_word and len(alts) == 1:
                role = "head_noun"
                word = alts[0].lower()
                if morph.singular_of(word):
                    # written as a plural ("wild horses", but also "a shambles", "the sticks"): matches only itself,
                    # and spelling can't tell its number, so the entry says (its `plural:`)
                    forms = ((word, "written_plural"),)
                else:
                    forms = ((word, "singular"), (morph.pluralise(word), "plural"))
                    if word.endswith("o"):
                        forms += ((word + "es", "plural"),)
                values = frozenset(s for s, _ in forms)
            elements.append(Element("lit", values, optional, role=role, forms=forms))
        elif len(alts) == 1:
            for norm in tokenised[0]:
                elements.append(Element("lit", frozenset([norm]), optional))
        else:
            raise ValueError(f"alternatives must be single words in pattern {text!r}")
    if not any(e.kind == "lit" and not e.optional for e in elements):
        raise ValueError(f"pattern {text!r} needs at least one required literal word")
    return Pattern(text, tuple(elements), frame, concepts, intensity, entry_id, person_only, before_modifier)


def is_name(tok: Token) -> bool:
    """A capitalised word that isn't a common sentence opener: a name, which can fill a subject or object slot."""
    return tok.text[:1].isupper() and tok.text.isalpha() and tok.norm not in COMMON_STARTERS


NP_STOP = {"and", "or", "but", "to", "that", "which", "who", "is", "are", "was", "were", "be", "not"}
NP_BOUNDARY = {"and", "or", "but", "that", "which", "who", "when", "while", "because", "so", "then", "as", "if",
               "before", "after", "until", "with", "without", "at", "in", "on", "for", "from", "by", "into",
               "about", "over", "under", "to"}   # "of" stays inside: "the last full measure of devotion"


def phrase_token(span: list[Token]) -> Token:
    """One pseudo-token standing for a multi-word phrase, with its original spacing."""
    text = span[0].text
    for prev, tok in zip(span, span[1:]):
        text += (" " if tok.start > prev.end else "") + tok.text
    return Token(text, span[0].start, span[-1].end, text.lower(), span[0].sent, span[0].i)


SLOT_MATCHERS = {
    "subj": lambda t: t.norm in morph.PRONOUNS or is_name(t),
    "be": lambda t: t.norm in morph.BE_FORMS,
    "have": lambda t: t.norm in morph.HAVE_FORMS,
    "do": lambda t: t.norm in morph.DO_FORMS,
    "poss": lambda t: t.norm in morph.POSSESSIVES,
    "obj": lambda t: t.norm in morph.OBJECT_PRONOUNS or is_name(t),
    "objposs": lambda t: t.norm in morph.POSSESSIVES or t.norm.endswith(("'s", "\u2019s")),
    "np": lambda t: False,   # multi-token; handled in match_at
    "will": lambda t: t.norm in ("will", "would", "shall"),
}


def match_at(pattern: Pattern, tokens: list[Token], pos: int) -> Match | None:
    """Match pattern starting at tokens[pos]; tokens is one sentence."""
    captures: dict[str, Token] = {}
    inflection = ""

    def rec(ei: int, ti: int) -> int | None:
        nonlocal inflection
        if ei == len(pattern.elements):
            return ti
        el = pattern.elements[ei]
        if el.kind == "not":
            for ahead in tokens[ti:ti + el.reach]:
                if ahead.norm in el.values:   # a word, or a mark the pattern names ("of course !,")
                    return None
                if ahead.is_punct:
                    break
            return rec(ei + 1, ti)
        if ti < len(tokens):
            tok = tokens[ti]
            if el.kind == "slot" and el.slot == "np":
                last = ei == len(pattern.elements) - 1
                for n in range(1, 6):
                    span = tokens[ti:ti + n]
                    if len(span) < n or span[-1].is_punct or span[0].norm in NP_STOP:
                        break
                    nxt = tokens[ti + n] if ti + n < len(tokens) else None
                    if last and not (nxt is None or nxt.is_punct or nxt.norm in NP_BOUNDARY):
                        continue  # a trailing {np} runs to a natural boundary, not one word
                    captures["np"] = phrase_token(span)
                    end = rec(ei + 1, ti + n)
                    if end is not None:
                        return end
                    captures.pop("np", None)
            elif el.kind == "slot":
                if SLOT_MATCHERS[el.slot](tok):
                    captures[el.slot] = tok
                    end = rec(ei + 1, ti + 1)
                    if end is not None:
                        return end
                    captures.pop(el.slot, None)
            elif tok.norm in el.values:
                saved = inflection
                if el.forms:
                    inflection = dict(el.forms).get(tok.norm, "")
                end = rec(ei + 1, ti + 1)
                if end is not None:
                    return end
                inflection = saved
        if el.optional:
            return rec(ei + 1, ti)
        return None

    end = rec(0, pos)
    if end is None or end == pos:
        return None
    # a clause written with its subject ("it {be} freezing": the weather's it, not fans or tears) has that
    # subject, as a {subj} would, so the form's {subj} and its verb agree with it
    if pattern.frame == "clause" and "subj" not in captures and pattern.elements[0].kind == "lit" \
            and tokens[pos].norm in morph.PRONOUNS:
        captures["subj"] = tokens[pos]
    return Match(pattern, pos, end, dict(captures), inflection)


class PatternIndex:
    """All patterns, indexed by the literal values of their first element. A sentence is checked against a
    pattern only if it has a word for every literal the pattern requires (most patterns fail that at once)."""

    def __init__(self, patterns: list[Pattern]):
        self.patterns = patterns
        self.by_first: dict[str, list[tuple[Pattern, tuple[frozenset[str], ...]]]] = {}
        self.unindexed: list[tuple[Pattern, tuple[frozenset[str], ...]]] = []
        for p in patterns:
            needs = tuple(e.values for e in p.elements if e.kind == "lit" and not e.optional)
            first = p.elements[0]
            if first.kind == "lit" and not first.optional:
                for v in first.values:
                    self.by_first.setdefault(v, []).append((p, needs[1:]))
            else:
                self.unindexed.append((p, needs))

    def find(self, tokens: list[Token]) -> list[Match]:
        norms = {t.norm for t in tokens}
        unindexed = [p for p, needs in self.unindexed if all(v & norms for v in needs)]
        out: list[Match] = []
        for pos, tok in enumerate(tokens):
            for p in [p for p, needs in self.by_first.get(tok.norm, ()) if all(v & norms for v in needs)] + unindexed:
                m = match_at(p, tokens, pos)
                if m:
                    out.append(m)
        return out
