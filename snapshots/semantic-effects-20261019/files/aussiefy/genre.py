"""What kind of text this is: a story, something personal (a letter, a forum post, a speech), news, instructions,
technical docs or official prose. Deterministic: cue words and shapes, counted and weighed.

The genre decides the form a text's Aussie takes, and its default embellishment: how much liberty the telling
takes beyond the words (data/genres.yaml). A story is told troppo, with the full garnish of a yarn; a safety
notice or an API reference deadset, with none; and nobody's lightning victim is "some mongrel". The caller may
set the embellishment. The engine reads both; yarn mode puts both, and their guidance, in the brief. A retelling
(yarn mode, or an agent writing with the plan and lint) defaults to genres.yaml's retelling setting instead.
"""

from __future__ import annotations

import re
import math
from dataclasses import asdict, dataclass, replace, field
from functools import cached_property

from .pos import IMPERATIVES
from .policy import EMBELLISHMENT_NAMES, EMBELLISHMENTS, DocumentOverrides
from .errors import UserError
from .schema import GENRES, PLACEMENTS, SchemaError
from .text import DATELINE, MID_SENTENCE_NAME, SCRIPT_LINE

MIN_WORDS = 150
# what a setting's or a genre's garnish may list: the placements, a term's riff, the swear infixes ("a bloody
# great stoush") and the tag-ons that call the listener names ("ya galah")
GARNISH = PLACEMENTS + ("riff", "infix", "insult")
POLICY_KEYS = ("garnish", "openings", "formal_to_rework", "embellishment", "person_swears", "keep_quotes", "guidance")
EMBELLISHMENT_KEYS = ("garnish", "follows_form", "openings", "draft", "keep_share", "max_length", "perform",
                      "guidance")
OPTIONAL_EMBELLISHMENT_KEYS = ("contextual_riffs", "entry_riffs", "riff_exaggeration", "riff_association", "narrator_opinion")

# The cue lexicons and weights stay in code, as context.py's mood lexicons do: they are the classifier, tuned
# together against the corpus (tests/test_genre.py), not vocabulary a dictionary round grows.

TECHNICAL = set("""api apis app apps argument arguments binary branch browser build builds bug cache ciphertext cli
client cluster code command commands commit compile compiler config configuration container containers cookie
cookies data database debug default dependency deploy deployment directory docs encrypt encryption endpoint error
file files function functions git github header headers http https install installation json kernel key keys
kubernetes library linux log logs macos module node nodes package packages parameter parameters plugin port
protocol pull python query release repository request requests runtime rust script sdk server servers session
shell software source string syntax terminal token tokens url user users variable version versions windows yaml""".split())
SAFETY = set("""warning danger dangerous caution hazard hazards risk risks injury injuries emergency deadly fatal
safety unsafe poison poisoning toxic lightning bear bears burn burns shelter avoid illness bacteria""".split())
NEWS = set("""said says announced according reported officials official spokesperson spokesman spokeswoman
statement agency department residents police sheriff today yesterday tonight monday tuesday wednesday thursday
friday saturday sunday percent""".split())
OBITUARY = {"died", "death", "funeral", "survived", "obituary", "passed", "aged", "widow", "widower", "buried"}
OFFICIAL = set("""shall pursuant prior approval gift gifts legal compensatory approved agreement terms liability prohibited eligible eligibility policy policies
applicant applicants committee members voted vote comply compliance required requirement requirements
responsible responsibility account accounts services provision provisions authorized authorised agency federal
employee employees position duties qualifications applicable accordance regulation regulations""".split())
SPEECH = re.compile(r"\((?:laughter|applause|cheers)\.?\)|\bladies and gentlemen\b|\bmy fellow\b|\bthank you all\b"
                    r"|\bgod bless\b", re.I)
LETTER = re.compile(r"^\s*(?:dear|my dear)\b[^\n]{0,40},?\s*$|^\s*(?:yours (?:truly|sincerely|affectionately)|sincerely"
                    r"|love|your (?:loving|affectionate)\b)[^\n]{0,30}$", re.I | re.M)
CODE = re.compile(r"`[^`\n]+`|^\s*(?:```|~~~)|\b\w+\(\)|\b[a-z]+[A-Z]\w*\b|\b\w+_\w+\b|(?:^|\s)--?[a-z][\w-]+", re.M)
STRUCTURE = re.compile(r"\s*(?:#{1,6}\s|[-*+]\s|\d{1,3}[.)]\s|\|)")
QUOTE = re.compile(r"[\"“”]")
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
UNITS = re.compile(r"\b(?:cups?|tsp|tbsp|teaspoons?|tablespoons?|oz|°F|minutes)\b")
FIGURE = re.compile(r"\b\d[\d,.:/]*\b")


@dataclass(frozen=True)
class Embellishment:
    """One setting of the embellishment dial: how much liberty the telling takes."""
    step: int                     # 0 deadset, 1 dinkum, 2 troppo
    garnish: frozenset[str]       # the garnish placements it takes (troppo: all of them)
    follows_form: bool            # a genre's form narrows its garnish (not troppo's: a performance); openings and
                                  # name-calling follow the form at every setting
    openings: bool                # yarn mode offers talker's openings
    draft: bool                   # yarn mode's brief carries the engine's draft
    keep_share: float             # the share of the planned phrases a yarn must keep (0: vocabulary only)
    max_length: float             # a retelling over this many times the original (+20 words) is too long
    perform: bool                 # the style guide's "perform it" block applies
    guidance: str                 # yarn mode's note for the setting
    contextual_riffs: bool = False
    entry_riffs: bool = True
    riff_exaggeration: int = 0
    riff_association: int = 0
    narrator_opinion: bool = False

    @property
    def name(self) -> str:
        return EMBELLISHMENT_NAMES[self.step]

    def takes(self, placement: str) -> bool:
        return placement in self.garnish


@dataclass(frozen=True)
class GenrePolicy:
    garnish: frozenset[str]       # the garnish its form allows, at a setting that follows the form
    openings: bool                # a talker's openings suit it (a story, a letter; not a notice)
    formal_to_rework: bool        # its formal sentences are listed for a writer (not docs': terms of art)
    default_embellishment: int    # its own setting, which the caller may override
    person_swears: bool           # "some bastard" for someone, "little buggers" for children
    keep_quotes: bool             # quoted speech and documents stay as said (news, official prose)
    guidance: str                 # yarn mode's note on the genre's form
    term_domains: tuple[str, ...] = ()
    command_context: bool = False
    dateline_context: bool = False
    check_length: bool = True


@dataclass(frozen=True)
class Genre:
    name: str
    scores: dict[str, float]      # each genre's score: explain reports them
    config: "GenreConfig" = field(repr=False, compare=False)

    selected: str = "auto"
    overrides: DocumentOverrides = field(default_factory=DocumentOverrides)

    @cached_property
    def policy(self) -> GenrePolicy:
        base = self.config.policies[self.name]
        keys = set(GenrePolicy.__dataclass_fields__) - {"garnish", "openings"}
        values = {k: v for k, v in self.overrides.values().items() if k in keys}
        if self.overrides.max_length is not None and self.overrides.check_length is None:
            values["check_length"] = True
        return replace(base, **values)

    def setting(self, step: int | None = None) -> Embellishment:
        """The embellishment a text of this genre takes: the caller's step (parsed), or the genre's own, narrowed
        to the genre's form unless the setting is free of it (troppo): a dinkum safety notice takes no opener.
        Two things the form rules out go at every setting, troppo's too: name-calling (nobody calls a safety
        notice's reader a galah) and a storyteller's openings (an obituary doesn't start "Fair dinkum, this
        happened.": the fourth pass's commonest troppo fault)."""
        e = self.config.embellishments[self.policy.default_embellishment if step is None else step]
        if self.name == "custom":
            e = replace(e, garnish=frozenset(), openings=False, draft=False, keep_share=0, max_length=1,
                        perform=False, guidance="", contextual_riffs=False, riff_exaggeration=0, riff_association=0,
                        narrator_opinion=False)
        else:
            e = replace(e, openings=e.openings and self.policy.openings)
            if "insult" not in self.policy.garnish:
                e = replace(e, garnish=e.garnish - {"insult"})
            if e.follows_form:
                e = replace(e, garnish=e.garnish & self.policy.garnish)
        overrides = self.overrides.values()
        values = {k: v for k, v in overrides.items() if k in Embellishment.__dataclass_fields__}
        if "garnish" in values:
            values["garnish"] = frozenset(values["garnish"])
        if "embellishment_guidance" in overrides:
            values["guidance"] = overrides["embellishment_guidance"]
        else:
            values.pop("guidance", None)
        return replace(e, **values)

    def envelope(self, step: int | None = None) -> dict:
        e = self.setting(step)
        policy = asdict(self.policy)
        policy.pop("garnish")
        policy.pop("openings")
        policy.pop("default_embellishment")
        return {"document_type": self.selected, "genre": self.name, "genre_scores": self.scores,
                "document_type_source": "detected" if self.selected == "auto" else "preset",
                "document_overrides": {k: list(v) if isinstance(v, tuple) else v for k, v in self.overrides.values().items()},
                "document_config": {**policy, **{k: v for k, v in asdict(e).items()
                                      if k not in ("step", "follows_form", "guidance")},
                                    "garnish": sorted(e.garnish), "term_domains": list(self.policy.term_domains),
                                    "embellishment_guidance": e.guidance}}


def resolve_document(text: str | None, layout: str | None = None, *, config: "GenreConfig",
                     document_type: str = "general", document_config=None) -> Genre:
    overrides = DocumentOverrides.parse(document_config)
    if document_type == "auto":
        if text is None:
            raise UserError("document_type auto requires source text; choose a named type for guide")
        return replace(text_genre(text, layout, config=config), overrides=overrides)
    if document_type not in config.policies:
        raise UserError(f"unknown document_type {document_type!r}")
    return Genre(document_type, {}, config, document_type, overrides)


def form_removes(genre: "Genre", placement: str, step: int) -> bool:
    """Whether the setting takes a placement and this genre's form takes it away (an infix in a safety notice)."""
    return genre.config.embellishments[step].takes(placement) and not genre.setting(step).takes(placement)


def _missing(where: str, raw: dict, keys: tuple[str, ...]) -> None:
    if not isinstance(raw, dict):
        raise SchemaError(f"genres.yaml: {where}: expected a mapping")
    missing = [k for k in keys if k not in raw]
    if missing:
        raise SchemaError(f"genres.yaml: {where}: missing {', '.join(missing)}")


def _garnish(where: str, garnish: list[str] | str) -> frozenset[str]:
    """A setting's or genre's garnish: a list of placements, or "all". A misspelt placement would silently
    switch that garnish off, so it's refused."""
    if garnish == "all":
        return frozenset(GARNISH)
    if not isinstance(garnish, list) or any(not isinstance(p, str) for p in garnish):
        raise SchemaError(f"genres.yaml: {where}: garnish must be a list of placements or all")
    unknown = set(garnish) - set(GARNISH)
    if unknown:
        raise SchemaError(f"genres.yaml: {where}: unknown garnish {sorted(unknown)} (use {', '.join(GARNISH)}, or all)")
    return frozenset(garnish)


def _typed_fields(where: str, raw: dict, booleans: tuple[str, ...]) -> None:
    for key in booleans:
        if not isinstance(raw[key], bool):
            raise SchemaError(f"genres.yaml: {where}: {key} must be a boolean")
    if not isinstance(raw["guidance"], str) or not raw["guidance"].strip():
        raise SchemaError(f"genres.yaml: {where}: guidance must be non-empty text")


def parse_embellishments(data: dict) -> dict[int, Embellishment]:
    """Each embellishment setting, from data/genres.yaml, checked: every setting, every key, known placements
    only (a misspelt placement would silently switch that garnish off)."""
    raw = data.get("embellishments")
    if not isinstance(raw, dict):
        raise SchemaError("genres.yaml: embellishments must be a mapping")
    if set(raw) != set(EMBELLISHMENTS):
        raise SchemaError(f"genres.yaml: embellishments must be exactly {list(EMBELLISHMENTS)}, got {list(raw)}")
    out = {}
    for name, e in raw.items():
        _missing(name, e, EMBELLISHMENT_KEYS)
        try:
            optional = DocumentOverrides.parse({k: e[k] for k in OPTIONAL_EMBELLISHMENT_KEYS if k in e}).values()
        except UserError as exc:
            raise SchemaError(f"genres.yaml: {name}: {exc}") from exc
        _typed_fields(name, e, ("follows_form", "openings", "draft", "perform"))
        for key in ("keep_share", "max_length"):
            if isinstance(e[key], bool) or not isinstance(e[key], (int, float)) or not math.isfinite(e[key]):
                raise SchemaError(f"genres.yaml: {name}: {key} must be a finite number")
        if not 0 <= e["keep_share"] <= 1 or e["max_length"] < 1:
            raise SchemaError(f"genres.yaml: {name}: keep_share is 0-1 and max_length at least 1")
        step = EMBELLISHMENTS[name]
        out[step] = Embellishment(step, _garnish(name, e["garnish"]), e["follows_form"], e["openings"],
                                  e["draft"],
                                  float(e["keep_share"]), float(e["max_length"]), e["perform"],
                                  " ".join(e["guidance"].split()), **optional)
    return out


def parse_genre_policies(data: dict) -> dict[str, GenrePolicy]:
    """Each genre's policy, from data/genres.yaml, checked: every genre, every key, a known default setting and
    known garnish."""
    raw = data.get("genres")
    if not isinstance(raw, dict):
        raise SchemaError("genres.yaml: genres must be a mapping")
    if set(raw) != set(GENRES) | {"general", "custom"}:
        raise SchemaError(f"genres.yaml: genres must include General, Custom and {list(GENRES)}, got {list(raw)}")
    out = {}
    for name, g in raw.items():
        _missing(name, g, POLICY_KEYS)
        _typed_fields(name, g, ("openings", "formal_to_rework", "person_swears", "keep_quotes"))
        if not isinstance(g["embellishment"], str) or g["embellishment"] not in EMBELLISHMENTS:
            raise SchemaError(f"genres.yaml: {name}: embellishment must be one of {', '.join(EMBELLISHMENTS)}")
        for key in ("command_context", "dateline_context", "check_length"):
            if type(g.get(key, key == "check_length")) is not bool:
                raise SchemaError(f"genres.yaml: {name}.{key} must be a boolean")
        domains = g.get("term_domains", [])
        if not isinstance(domains, list) or any(not isinstance(v, str) or v not in GENRES for v in domains):
            raise SchemaError(f"genres.yaml: {name}.term_domains must list known detected types")
        out[name] = GenrePolicy(_garnish(name, g["garnish"]), g["openings"], g["formal_to_rework"],
                                EMBELLISHMENTS[g["embellishment"]],
                                g["person_swears"], g["keep_quotes"], " ".join(g["guidance"].split()),
                                tuple(g.get("term_domains", ())), g.get("command_context", False), g.get("dateline_context", False), g.get("check_length", True))
    return out


@dataclass(frozen=True)
class Features:
    """What the classifier counts in a text. Rates are per 100 words, over at least MIN_WORDS: in a short text
    one cue word ("bears", "said") is no evidence. A lexicon's rate is scaled by its breadth: it counts in full
    from three distinct cues, since one word repeated ("shall" in a poem, "said" in a rant) is no evidence."""
    technical: float      # TECHNICAL rate x breadth
    code: float           # code spans, identifiers, flags: rate
    imperative: float     # share of sentences opening on a command, from two commands over four sentences
    safety: float         # SAFETY rate
    questions: float      # share of lines asking, from two (an FAQ asks on several lines, not once)
    units: float          # cups, teaspoons, minutes: rate
    news: float           # NEWS rate x breadth
    datelines: int
    names: float          # distinct capitalised words inside sentences: rate
    figures: float        # dates, ages, amounts: rate
    obituary: float       # OBITUARY rate x breadth
    official: float       # OFFICIAL rate x breadth
    structure: float      # share of lines that are headings, list items, table rows (a story is paragraphs)
    letter: int           # salutations and sign-offs
    speech: int           # "(Applause)", "ladies and gentlemen"
    first_person: float   # I, me, my: rate
    pronouns: float       # he, she, they: rate
    quotes: float         # quote marks: rate
    script: float         # share of lines that are a speaker's label (a play)
    verse: float          # share of a paragraph's follow-on lines that open on a capital mid-sentence (a poem)
    addressed: float      # you, your, we, our: rate (a letter or a talk speaks to someone)
    words: int            # how long the text is


def features(text: str, layout: str | None = None, vocabulary: frozenset[str] = frozenset()) -> Features:
    """text's cues. layout (the source, markup and all, when text is its masked prose) gives the shape cues:
    headings, list items, code. The words come from text."""
    layout = text if layout is None else layout
    words = [w.lower() for w in WORD.findall(text)]
    vocab = set(words)
    n = max(MIN_WORDS, len(words))
    lines = [ln for ln in text.splitlines() if ln.strip()]
    shape = [ln for ln in layout.splitlines() if ln.strip()]
    sents = [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if WORD.search(s)]

    def rate(count: int) -> float:
        return count * 100 / n

    def lexicon(words_in: set[str]) -> float:
        return rate(sum(w in words_in for w in words)) * min(1.0, len(words_in & vocab) / 3)

    commands = sum(WORD.search(s).group().lower() in IMPERATIVES for s in sents)
    asked = sum(ln.rstrip().endswith("?") for ln in lines)
    return Features(
        technical=lexicon(TECHNICAL), code=rate(len(CODE.findall(layout))),
        imperative=commands / max(4, len(sents)) if commands >= 2 else 0.0,
        safety=rate(sum(w in SAFETY for w in words)),
        questions=asked / max(4, len(lines)) if asked >= 2 else 0.0,
        units=rate(len(UNITS.findall(text))),
        news=lexicon(NEWS), datelines=len(DATELINE.findall(text)),
        # an ordinary word capitalised ("the Wife" in a fable that Capitalises its Nouns) isn't a name
        names=rate(len({m.group() for m in MID_SENTENCE_NAME.finditer(text)} - _common_titles(vocabulary))),
        figures=rate(len(FIGURE.findall(text))),
        obituary=lexicon(OBITUARY), official=lexicon(OFFICIAL),
        structure=sum(bool(STRUCTURE.match(ln)) for ln in shape) / max(1, len(shape)),
        letter=len(LETTER.findall(text)), speech=len(SPEECH.findall(text)),
        first_person=rate(sum(w in ("i", "me", "my") for w in words)),
        pronouns=rate(sum(w in ("he", "she", "they", "him", "her", "his") for w in words)),
        quotes=rate(len(QUOTE.findall(text))), script=len(SCRIPT_LINE.findall(text)) / max(1, len(lines)),
        verse=_verse(text), addressed=rate(sum(w in ("you", "your", "we", "our") for w in words)), words=len(words))


def _common_titles(vocabulary: frozenset[str]) -> frozenset[str]:
    return frozenset(w.title() for w in vocabulary)


def _verse(text: str) -> float:
    """Of the lines that carry on a paragraph mid-sentence, the share opening on a capital: a poem's lines do
    ("Once upon a midnight dreary, while I pondered, weak and weary, / Over many a quaint ..."), wrapped prose's
    mostly don't. Only lines of words count (an address or a list isn't verse); 0 for a text with fewer than
    eight such lines."""
    follow = caps = 0
    for para in re.split(r"\n\s*\n", text):
        lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
        for before, line in zip(lines, lines[1:]):
            if before[-1:] in ".!?" or not (_verse_line(before) and _verse_line(line)):
                continue
            follow += 1
            caps += line[:1].isupper()
    return caps / follow if follow >= 8 else 0.0


def _verse_line(line: str) -> bool:
    """A line that could be verse: words, not a list's or an address's entry ("Level 3, 100 George Street")."""
    return len(line.split()) >= 4 and not re.search(r"\d", line)


def scores(f: Features) -> dict[str, float]:
    return {
        "technical": f.technical * 0.6 + f.code * 1.5,
        "instructions": f.imperative * 12 + f.safety * 0.8 + f.questions * 6 + f.units * 1.5,
        "news": f.news * 0.9 + f.datelines * 3 + min(f.names, 8) * 0.25 + f.figures * 0.2 + f.obituary * 1.2,
        "official": f.official * 1.3 + f.structure * 1.5,
        "personal": f.letter * 3 + f.speech * 2.5 + f.first_person * 0.45 + f.addressed * 0.12,
        # a short text with no cues is a story; a long one has to show it (pronouns, dialogue, verse)
        "story": f.pronouns * 0.35 + f.quotes * 0.4 + f.script * 8 + f.verse * 3 - f.structure * 3
                 + (1.0 if f.words < 2 * MIN_WORDS else 0.3),
    }


def text_genre(text: str, layout: str | None = None, *, config: "GenreConfig" | None = None) -> Genre:
    """The genre a text reads as, by its cues (layout: see features). A text with too few cues for any other (a
    short one, most often) reads as a story."""
    s = scores(features(text, layout, config.vocabulary if config is not None else frozenset()))
    name = max(GENRES, key=lambda g: (s[g], -GENRES.index(g)))
    return Genre(name, {g: round(v, 2) for g, v in s.items()}, config)


@dataclass(frozen=True)
class GenreConfig:
    policies: dict[str, GenrePolicy]
    embellishments: dict[int, Embellishment]
    vocabulary: frozenset[str] = frozenset()

    @classmethod
    def from_mapping(cls, data: dict, vocabulary: frozenset[str] = frozenset()) -> "GenreConfig":
        if not isinstance(data, dict):
            raise SchemaError("genres.yaml: expected a mapping")
        settings = parse_embellishments(data)
        return cls(parse_genre_policies(data), settings, vocabulary=vocabulary)
