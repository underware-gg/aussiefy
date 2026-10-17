"""The dictionary as data: entries, concepts, level profiles, phonetic rules and what's derived from them.

No I/O: loader.py reads and validates the YAML into these; the engine, policy and toolkit read them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from . import morph
from .dialect import DialectTable
from .matcher import Pattern, PatternIndex
from .schema import Concept, Entry, Imagery
from .text import COMMON_STARTERS
from .terms import fold


# the endings a masked word keeps after a stem that is itself a listed swear or a mask word (O23's fixed set)
MASK_ENDINGS = ("ers", "ing", "in'", "es", "ed", "er", "in", "s", "y")


def _find_all(word: str, part: str) -> list[int]:
    return [i for i in range(len(word) - len(part) + 1) if word.startswith(part, i)]


def swear_strength(swears: dict[str, int], word: str) -> int:
    """How strong a swear a word is: as listed, with a dropped g ("fuckin'", "pissin" -> pissing) or a plural
    ("pricks") or a possessive ("bastard's") read as the listed word."""
    w = word.lower().replace("\u2019", "'")
    bare = w.rstrip("'")
    for cand in (w, bare, bare + "g" if bare.endswith("in") else "", bare[:-1] if bare.endswith("s") else "",
                 bare[:-2] if bare.endswith("'s") else ""):   # "the bastard's dog"
        if cand and swears.get(cand):
            return swears[cand]
    return 0


@dataclass(frozen=True)
class RewriteThresholds:
    """When a sentence is too formal for the dictionary to carry (profiles.yaml `rewrite:`): at min_level and
    up, a sentence of min_words or more with min_formal_words formal words of formal_length letters the
    dictionary left alone, or any such word where it covered no more than max_coverage of the sentence."""
    min_level: int = 3
    min_words: int = 6
    min_formal_words: int = 2
    max_coverage: float = 0.1
    formal_length: int = 7


# how many of a garnish placement one text may carry, where profiles.yaml `max_garnish` doesn't say
DEFAULT_GARNISH_LIMITS = {"closer": 1, "riff": 1}
UNLIMITED = 99


@dataclass(frozen=True)
class SwearProfile:
    """How often swearing comes at one vulgarity, whatever the level (profiles.yaml `swearing:`)."""
    exclaim: float = 0.0      # per-sentence probability of a sweary opener, aside, tag or tail
    closer: float = 0.0       # probability the text ends on a sweary closer
    infix: float = 0.0        # multiplier on the swear infix rules' own probabilities
    lean: float = 1.0         # weight on swears where a swap has clean and swearing options


@dataclass(frozen=True)
class LevelProfile:
    level: int
    substitution: dict[str, float]      # class -> probability
    frames: tuple[str, ...]
    vulgarity: int                      # the default vulgarity at this level (an explicit one wins)
    registers: tuple[str, ...]
    garnish: dict[str, float]           # placement -> probability per sentence
    max_garnish: dict[str, int]         # placement -> max per text
    garnish_gap: int                    # sentences that must pass before a placement repeats
    garnish_per_sentence: int           # most garnish items one sentence may carry
    rewrite: RewriteThresholds          # when a sentence is too formal for the dictionary
    stack: float
    phonetic: float
    stretch: tuple[int, int]

    def limit(self, placement: str) -> int:
        """How many of a garnish placement one text may carry."""
        return self.max_garnish.get(placement, DEFAULT_GARNISH_LIMITS.get(placement, UNLIMITED))


@dataclass(frozen=True)
class PhoneticRule:
    id: str
    pattern: re.Pattern
    replace: str
    prob: float
    min_level: int
    notes: str = ""
    vulgarity: int = 0          # respects the policy's vulgarity ("bloody well" is 1)
    kind: str = "drawl"         # drawl (scaled by the level's `phonetic`) | spelling (always, from min_level)
    dialogue_prob: float | None = None  # probability inside quoted speech, which drawls broader than narration
    reads_as: str | None = None         # canonical wording for lint's refrain comparison; literal drawl only
    unless_before: re.Pattern | None = None   # refuse a match following this grammatical context
    unless_question: bool = False       # refuse matches in a question, using the shared sentence tokenizer


@dataclass
class Dictionary:
    entries: dict[str, Entry]
    concepts: dict[str, Concept]
    profiles: dict[int, LevelProfile]
    phonetic: list[PhoneticRule]
    policy_defaults: dict[str, Any]
    patterns: list[Pattern]                     # plain-English triggers and entries' replaces
    index: PatternIndex                         # ... indexed: plain English -> concepts (detection)
    form_index: PatternIndex                    # the Aussie forms themselves -> entries (lint finds slang)
    swears: dict[str, int]                      # word -> vulgarity 1-3 (swears.yaml)
    dialect: DialectTable                       # US and UK words Australians say differently (dialect.yaml)
    warnings: list[str] = field(default_factory=list)
    swearing: dict[int, SwearProfile] = field(default_factory=dict)   # vulgarity -> how often swearing comes

    genres: Any = None
    pos_words: frozenset[str] = frozenset()
    person_roles: frozenset[str] = frozenset()
    adjective_nouns: dict[str, frozenset[str]] = field(default_factory=dict)
    name_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    imagery: tuple[Imagery, ...] = ()

    def swear_strength(self, word: str) -> int:
        """How strong a swear a word is (0 for none), dropped g and plurals read as the listed word."""
        return swear_strength(self.swears, word)

    # --- derived once, on first use ---------------------------------------------------------------------------

    @cached_property
    def swear_compounds(self) -> dict[str, int]:
        """The words in rated entries and riffs that hold a listed swear inside them, with more than an ending
        around it ("fuckwit", "shitfight", "bullshitter"), and how strong the strongest one held is. Read from
        the dictionary's own rated words, so an ordinary word that happens to hold one ("cocktail", "Scunthorpe",
        "cocky") is never taken for one."""
        stems = {w: v for w, v in self.swears.items() if len(w) >= 4 and v}
        texts = [f for e in self.entries.values() if e.vulgarity and e.status != "omit" for f in e.all_forms]
        texts += [r.text for e in self.entries.values() for r in e.riffs if r.vulgarity]
        out: dict[str, int] = {}
        for word in {w.lower().replace("\u2019", "'").strip("'") for t in texts for w in re.findall(r"[A-Za-z'\u2019]+", t)}:
            if swear_strength(self.swears, word):
                continue
            held = []
            for stem, strength in stems.items():
                for i in _find_all(word, stem):
                    before, after = word[:i], word[i + len(stem):]
                    if len(before) >= 2 or (len(after) >= 2 and after not in MASK_ENDINGS):
                        held.append(strength)
            if held:
                out[word] = max(held)
        return out

    @cached_property
    def plain_words(self) -> frozenset[str]:
        """Ordinary English: every word the dictionary itself writes in lower case (triggers, replaces, glosses,
        concept descriptions) plus common sentence starters. Names never appear there in lower case, so this
        answers "is this capitalised word a name?" (lint) and "may it be lower-cased after an opener?" (garnish),
        and what isn't slang inside an idiom (dev fragments)."""
        texts = [e.gloss or "" for e in self.entries.values()] + [" ".join(e.replaces) for e in self.entries.values()]
        texts += [c.description or "" for c in self.concepts.values()]
        texts += [" ".join(ps) for c in self.concepts.values() for ps in c.triggers.values()]
        # a trigger's "!" exclusions are contexts, names among them ("granny !smith"): only those the tagger's
        # lower-case vocabulary knows, or the dictionary writes elsewhere, count
        bare = [re.sub(r"(?<!\S)![^\s\"',\]]+", " ", t) for t in texts]
        words = {w for t in bare for w in re.findall(r"\b[a-z][a-z'-]*\b", t)}
        # Compilation folds capitals and expands inflections. Only a lower-case source pattern can supply
        # lower-case evidence for its inferred forms; "an Australian" must not make "australian" ordinary.
        words |= {v for p in self.patterns if p.text.islower() for e in p.elements if e.kind == "lit" for v in e.values}
        excluded = {v for p in self.patterns for e in p.elements if e.kind == "not" for v in e.values}
        words |= excluded & self.pos_words
        return frozenset(words | COMMON_STARTERS)

    @cached_property
    def person_concepts(self) -> frozenset[str]:
        return frozenset(c.id for c in self.concepts.values() if c.person)

    @cached_property
    def drawl_readings(self) -> dict[str, str]:
        return {fold(r.replace): r.reads_as for r in self.phonetic if r.reads_as is not None}

    @cached_property
    def us_spellings(self) -> dict[str, re.Pattern]:
        """The spelling rules' patterns by id: each match is an American spelling (color, organize)."""
        return {r.id: r.pattern for r in self.phonetic if r.kind == "spelling"}

    @cached_property
    def neutral_person_concepts(self) -> frozenset[str]:
        return frozenset(c.id for c in self.concepts.values() if c.neutral_person)

    @cached_property
    def person_nouns(self) -> frozenset[str]:
        """Nouns that name people: the person concepts' own noun triggers (child, kids, mate ...), with their
        plurals, and common roles. What a predicate about a person may have as its subject."""
        words = set(self.person_roles)
        for c in self.concepts.values():
            if c.person:
                for trigger in c.triggers.get("np", ()):
                    bare = re.sub(r"@\d+$", "", trigger).split("!")[0].split()
                    if len(bare) == 2 and bare[0] in {"a", "an", "the"}:
                        bare = bare[1:]
                    if len(bare) == 1 and bare[0].isalpha():
                        words |= {bare[0], morph.pluralise(bare[0])}
        return frozenset(words)

    @cached_property
    def fallback_patterns(self) -> list[Pattern]:
        """Slot-free predicate-adjective triggers: what the similarity fallback compares spans against."""
        return [p for p in self.patterns if p.frame == "predicate_adj" and not p.slots and not any(e.optional for e in p.elements)]

    @cached_property
    def tag_forms(self) -> frozenset[str]:
        """Tag-ons that address someone ("mate", "ya galah"); narration's own jibes (`when: action_end`) don't."""
        return frozenset(f.lower() for e in self.garnish if e.placement == "tag" and "action_end" not in e.when
                         for f in e.all_forms)

    @cached_property
    def closer_forms(self) -> list[str]:
        """Every stock exclamation that can end a text or a stanza (closers and asides)."""
        return [f for e in self.garnish if e.placement in ("closer", "aside") for f in e.all_forms]

    @cached_property
    def idioms(self) -> list[Entry]:
        return [e for e in self.entries.values() if e.type == "idiom"]

    @cached_property
    def garnish(self) -> list[Entry]:
        return [e for e in self.entries.values() if e.type == "garnish"]

    @cached_property
    def idioms_by_concept(self) -> dict[str, list[Entry]]:
        """Concept -> the idioms that carry it, in dictionary order."""
        out: dict[str, list[Entry]] = {}
        for e in self.idioms:
            for c in dict.fromkeys(e.concept):
                out.setdefault(c, []).append(e)
        return out

    def idioms_for(self, concepts: tuple[str, ...]) -> list[Entry]:
        """The idioms that carry any of these concepts, each once, in dictionary order."""
        if len(concepts) == 1:
            return self.idioms_by_concept.get(concepts[0], [])
        wanted = {e.id for c in concepts for e in self.idioms_by_concept.get(c, ())}
        return [e for e in self.idioms if e.id in wanted]

    @cached_property
    def regions(self) -> frozenset[str]:
        """Every region tag an entry carries."""
        return frozenset(r for e in self.entries.values() for r in e.region)

    @cached_property
    def gate_flags(self) -> frozenset[str]:
        """Every flag a gated entry carries: what unlocking can act on."""
        return frozenset(f for e in self.entries.values() if e.status == "gate" for f in e.flags)
