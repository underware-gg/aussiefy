"""American and British words Australians say differently (faucet -> tap, courgette -> zucchini): plain
Australian English, swapped at every level like spelling. The table is data (data/dialect.yaml); this module
reads it, tells which English a text is in where it can, and finds the swaps in a sentence.

A word only another English uses (faucet, courgette) swaps whatever the text. A word that is ordinary
Australian in another sense (British pants are undies; Australian pants are trousers) swaps only once the text
is known to be in that English: by the `english` dial, or for American, by its spelling (color, gray).
British spelling is Australian spelling (and -ize is Oxford British too), so a British text can't be told
from an Australian one: "uk" is only ever the caller's say-so.

A swap whose Australian is its own pattern ("petroleum jelly: petroleum jelly") is a guard: it claims its
words, so a shorter swap inside it ("jelly" -> jam) can't take them. The table's way to see a word before.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import morph
from .matcher import Pattern, PatternIndex, compile_pattern
from .schema import FRAMES, SchemaError, parse_not_in
from .text import Token, capital_is_positional, tokenize

ENGLISHES = ("auto", "us", "uk", "none")   # the dial: auto reads American spelling; none turns the pass off
SECTIONS = ("both", "us", "uk")
SWAP_KEYS = ("to", "frame", "plural", "known_only", "not_in")
AMERICAN_RULES_FOR_US = 2   # distinct American spelling rules a text must trip to count as American
# spelling rules that don't mark a text as American: -ize is Oxford British too
NOT_AMERICAN_MARKERS = frozenset({"spell-ise"})


@dataclass(frozen=True)
class DialectSwap:
    english: str                  # "us", "uk" or "both": which English uses the word
    pattern: Pattern
    to: str
    plural: str | None = None     # the Australian's plural, when it isn't regular
    known_only: bool = False      # swaps only in a text known to be in this English
    not_in: frozenset[str] = frozenset()   # genres where the word is a term of art

    def applies(self, english: str | None, genre: str | tuple[str, ...]) -> bool:
        """Whether this swap may go in a text in this English (None: not known) and genre."""
        domains = (genre,) if isinstance(genre, str) else genre
        if self.not_in.intersection(domains):
            return False
        return not self.known_only or english == self.english

    def realise(self, inflection: str, captures: dict[str, Token]) -> str:
        """The Australian, inflected as the matched words were (plural, past tense) and with its slots filled."""
        out = self.to
        if inflection == "plural":   # a pattern written as a plural ("crisps: chips") keeps its `to` as written
            words = out.split()
            out = self.plural or " ".join(words[:-1] + [morph.pluralise(words[-1])])
        elif inflection and self.pattern.frame == "vp":
            head, _, rest = out.partition(" ")
            out = morph.inflect(head, inflection) + (" " + rest if rest else "")
        return re.sub(r"\{(\w+)\}", lambda m: captures[m.group(1)].text, out)


@dataclass(frozen=True)
class Found:
    start: int                    # token span in the sentence
    end: int
    text: str                     # the Australian, inflected
    swap: DialectSwap


class DialectTable:
    def __init__(self, swaps: list[DialectSwap], lint_only: dict[str, str]):
        self.swaps = tuple(swaps)
        self.lint_only = lint_only
        # by identity: two sections can hold equal patterns ("vest" in us and uk) for different swaps
        self._by_pattern = {id(s.pattern): s for s in self.swaps}
        self._index = PatternIndex([s.pattern for s in self.swaps])

    def find(self, tokens: list[Token], english: str | None, genre: str | tuple[str, ...], taken: set[int] = frozenset()) -> list[Found]:
        """The swaps in one sentence: longest first where they overlap ("trash can" before "the trash"), none
        on a taken token, a guard's words, or a capital that marks a name or title ("Parking Lot B")."""
        def named(span: range) -> bool:
            return any(tokens[i].text[:1].isupper() and not capital_is_positional(tokens, i)
                       and not tokens[i].text.isupper() for i in span)

        out = [Found(m.start, m.end, text, swap) for m, swap in self._claims(tokens, english, genre, taken, named)
               # a guard's Australian is its own words, as is a word already Australian
               if (text := swap.realise(m.inflection, m.captures)).lower() != _surface(tokens[m.start:m.end]).lower()]
        return sorted(out, key=lambda f: f.start)

    def spans(self, tokens: list[Token], english: str | None, genre: str | tuple[str, ...]) -> list[tuple[int, int]]:
        """Every span the table claims in a sentence, guards included: where a shorter dictionary match inside
        one ("cookie" in "cookie jar", "jelly" in "petroleum jelly") must give way."""
        return [(m.start, m.end) for m, _ in self._claims(tokens, english, genre)]

    def _claims(self, tokens: list[Token], english: str | None, genre: str | tuple[str, ...], taken: set[int] = frozenset(),
                skip=lambda span: False):
        """The matches the table claims, longest first where they overlap, each with its swap: none on a taken
        token, none that doesn't apply to this English and genre, none `skip` turns down (left for a shorter
        match). find and spans both claim this way, so the engine yields to exactly the swaps it makes."""
        used = set(taken)
        for m in sorted(self._index.find(tokens), key=lambda m: (m.start - m.end, m.start)):
            span = range(m.start, m.end)
            swap = self._by_pattern[id(m.pattern)]
            if used.intersection(span) or not swap.applies(english, genre) or skip(span):
                continue
            used.update(span)
            yield m, swap

    def check_outputs(self) -> list[str]:
        """Swaps whose Australian another swap would always take (realtor -> real estate agent, and British
        estate agent -> real estate agent again): the engine's output would fail its own lint. A known-only word
        may be another's Australian (flip-flop -> thong; British thong -> g-string): the engine never swaps
        twice, and lint, given the original, flags a known-only word only where the original had it."""
        problems = []
        for s in self.swaps:
            tokens = tokenize(re.sub(r"\{\w+\}", "it", s.to))
            for english in ("us", "uk"):
                hits = [f for f in self.find(tokens, english, "story") if not f.swap.known_only]
                if hits:
                    problems.append(f"dialect.yaml: {s.pattern.text!r} -> {s.to!r}, which {english} "
                                    f"{hits[0].swap.pattern.text!r} would swap again (add a guard)")
                    break
        return problems


def _surface(span: list[Token]) -> str:
    """A span's words as written, with their own spacing ("high-vis vest")."""
    out = span[0].text
    for prev, tok in zip(span, span[1:]):
        out += (" " if tok.start > prev.end else "") + tok.text
    return out


def parse_dialect(raw: dict[str, Any] | None) -> DialectTable:
    """dialect.yaml's table, checked: known sections and keys, patterns that compile, slots the pattern fills,
    and no Australian that the table would swap again."""
    raw = {} if raw is None else raw
    if not isinstance(raw, dict):
        raise SchemaError("dialect.yaml: expected a mapping")
    unknown = set(raw) - set(SECTIONS) - {"lint_only"}
    if unknown:
        raise SchemaError(f"dialect.yaml: unknown sections {sorted(unknown)} (use {', '.join(SECTIONS)}, lint_only)")
    swaps = []
    for section in SECTIONS:
        rows = raw.get(section, {})
        if not isinstance(rows, dict):
            raise SchemaError(f"dialect.yaml: {section}: expected a mapping")
        for text, value in rows.items():
            spec = value if isinstance(value, dict) else {"to": value}
            where = f"dialect.yaml: {section}: {text!r}"
            bad = set(spec) - set(SWAP_KEYS)
            if bad or not spec.get("to"):
                raise SchemaError(f"{where}: needs `to`, and only {', '.join(SWAP_KEYS)}")
            if not isinstance(text, str) or not text.strip() or not isinstance(spec["to"], str) or not spec["to"].strip():
                raise SchemaError(f"{where}: pattern and to must be non-empty text")
            if "plural" in spec and (not isinstance(spec["plural"], str) or not spec["plural"].strip()):
                raise SchemaError(f"{where}: plural must be non-empty text")
            if "known_only" in spec and not isinstance(spec["known_only"], bool):
                raise SchemaError(f"{where}: known_only must be a boolean")
            frame = spec.get("frame", "np")
            if not isinstance(frame, str) or frame not in FRAMES:
                raise SchemaError(f"{where}: unknown frame {frame!r}")
            if frame == "vp" and spec.get("plural"):
                raise SchemaError(f"{where}: a verb phrase has no plural")
            try:
                pattern = compile_pattern(text, frame, ("DIALECT",), 3)
            except ValueError as exc:
                raise SchemaError(f"{where}: {exc}") from None
            missing = set(re.findall(r"\{(\w+)\}", spec["to"])) - pattern.slots
            if missing:
                raise SchemaError(f"{where}: `to` uses {sorted(missing)}, which the pattern doesn't capture")
            swaps.append(DialectSwap(section, pattern, spec["to"], spec.get("plural"),
                                     bool(spec.get("known_only")), parse_not_in(where, spec.get("not_in"))))
    lint_only = raw.get("lint_only", {})
    if not isinstance(lint_only, dict) or any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
                                             for k, v in lint_only.items()):
        raise SchemaError("dialect.yaml: lint_only must map non-empty text to non-empty text")
    table = DialectTable(swaps, lint_only)
    problems = table.check_outputs()
    if problems:
        raise SchemaError("\n  ".join(problems))
    return table


def text_english(dial: str, text: str, spelling: dict[str, re.Pattern]) -> str | None:
    """The English a text is in, for the known-only swaps: the dial's, or for auto, "us" when the text trips
    two distinct American spelling rules (color and gray, not meter and meters), else None (not known).
    spelling maps a spelling rule's id to its pattern."""
    if dial not in ENGLISHES:   # an invariant: Policy has already refused an unknown dial, as a UserError
        raise ValueError(f"english must be one of {ENGLISHES}, got {dial!r}")
    if dial in ("us", "uk"):
        return dial
    if dial == "none":
        return None
    tripped = {rid for rid, rule in spelling.items() if rid not in NOT_AMERICAN_MARKERS and rule.search(text)}
    return "us" if len(tripped) >= AMERICAN_RULES_FOR_US else None
