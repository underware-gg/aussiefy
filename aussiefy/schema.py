"""Dictionary schema: entry, concept and profile types plus validation.

The dictionary is data. Nothing in the engine names a slang phrase; it only
understands the fields defined here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .errors import UserError
from .text import MASK_WORD_RE, normalise_word

FRAMES = (
    "predicate_adj",  # complement of a linking verb: "he's [flat out like a lizard drinking]"
    "np",             # noun phrase: "[brekkie]", "[a dog's breakfast]"
    "adj",            # single attributive/predicative adjective: "[ripper]"
    "adv",            # adverb / intensifier: "[bloody] good"
    "vp",             # verb phrase, inflected on its head: "[carrying on like a pork chop]"
    "clause",         # whole clause with its own subject: "{subj} {have} a kangaroo loose..."
    "interjection",   # stands alone at clause start: "[no worries]"
    "imperative",     # command at clause start: "[rack off]"
    "tag",            # garnish tag-on: ", mate"
)
STATUSES = ("active", "gate", "omit")
REGISTERS = ("current", "dated", "archaic")
FLAGS = ("not_aussie", "slur", "dubious_meaning", "archaic", "fabricated", "untagged")
TYPES = ("idiom", "garnish")
CLASSES = ("lexical", "phrase", "idiom")
PLACEMENTS = ("connective", "opener", "tag", "aside", "tail", "closer")
GARNISH_KEYS = (*PLACEMENTS, "riff")   # rate and per-text-limit keys in level profiles
GENRES = ("story", "personal", "news", "instructions", "technical", "official")   # genre.py reads a text as one
# Sentence contexts a garnish entry may require (`when`); see context.sentence_contexts.
CONTEXTS = ("narration", "dialogue", "question", "exclamation", "second_person", "opinion", "fragment",
            "paragraph_end", "action_end", "any")
DEFAULT_WHEN = {
    "connective": ("narration",),                                    # "Anyway, she ..." moves a yarn along
    "opener": ("any",),
    "tag": ("dialogue", "question", "second_person"),                # ", mate" needs someone addressed
    "aside": ("paragraph_end",),                                     # "What a shocker!" after a stanza of a chant
    "tail": ("any",),                                                # "...their brains and imagination, the lot"
    "closer": ("any",),
}
SLOT_KINDS = {
    "subj": "pronoun",
    "be": "verb_agree",
    "have": "verb_agree",
    "do": "verb_agree",
    "poss": "possessive",
    "obj": "object_pronoun",
    "objposs": "object_possessive",   # the object's possessive: "her" / "his" / "Mary's" (needs {obj} matched)
    "np": "noun_phrase",      # a short noun phrase copied as-is ("her assertion")
    "will": "modal",          # will / would, by tense
}
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
# Frames whose entries replace a whole meaning-chunk and bring their own grammar.
IDIOM_FRAMES = ("predicate_adj", "vp", "clause")


class SchemaError(UserError):
    """The dictionary (or an entry) doesn't validate."""


RIFF_TONES = ("comic", "grim", "plain")


@dataclass(frozen=True)
class Riff:
    """The image a term calls up ("wheelie bins" -> "overflowin', bin chickens fightin' over the scraps")."""
    text: str
    vulgarity: int = 0
    tone: str = "plain"   # comic | grim | plain


@dataclass(frozen=True)
class Imagery:
    id: str
    text: str
    concepts: tuple[str, ...]
    usage: str
    form: str = "suffix"          # suffix: engine can append; rewrite: writer must weave it in
    frames: tuple[str, ...] = ("predicate_adj", "clause", "vp")
    subject: str = "any"
    related: tuple[str, ...] = ()   # looser associations, available only when explicitly enabled
    unless_after: tuple[str, ...] = ()  # exclude figurative/complement senses after optional punctuation
    exaggeration: int = 1
    level: int = 3
    tone: str = "comic"
    origin: str = "original"
    vulgarity: int = 0


def parse_imagery(raw, concepts, strength) -> Imagery:
    if not isinstance(raw, dict) or any(not isinstance(k, str) for k in raw):
        raise SchemaError("imagery record must be a mapping")
    allowed = set(Imagery.__dataclass_fields__) - {"vulgarity"}
    if set(raw) - allowed:
        raise SchemaError(f"imagery: unknown fields {sorted(set(raw) - allowed)}")
    data = dict(raw)
    owner = data.get("id")
    if not isinstance(owner, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", owner):
        raise SchemaError("imagery id must be kebab-case")
    for key in ("text", "usage"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise SchemaError(f"{owner}: {key} must be non-empty text")
    for key in ("concepts", "related", "frames"):
        values = data.get(key, getattr(Imagery, key, ()))
        if not isinstance(values, (list, tuple)) or any(not isinstance(x, str) for x in values):
            raise SchemaError(f"{owner}: {key} must be a list of strings")
        known = FRAMES if key == "frames" else concepts
        if any(x not in known for x in values) or (key in ("concepts", "frames") and not values):
            raise SchemaError(f"{owner}: {key} must name known, non-empty anchors")
        data[key] = tuple(dict.fromkeys(values))
    for key, choices in (("form", ("suffix", "rewrite")), ("subject", ("any", "person")),
                         ("tone", RIFF_TONES), ("origin", ("original", "familiar"))):
        if data.get(key, getattr(Imagery, key)) not in choices:
            raise SchemaError(f"{owner}: {key} must be one of {choices}")
    exclusions = data.get("unless_after", ())
    if not isinstance(exclusions, (list, tuple)) or any(not isinstance(x, str) or not re.fullmatch(r"[a-z]+", x) for x in exclusions):
        raise SchemaError(f"{owner}: unless_after must be a list of lowercase words")
    data["unless_after"] = tuple(dict.fromkeys(exclusions))
    for key, low, high in (("exaggeration", 0, 2), ("level", 1, 5)):
        value = data.get(key, getattr(Imagery, key))
        if type(value) is not int or not low <= value <= high:
            raise SchemaError(f"{owner}: {key} must be an integer {low}–{high}")
    slots = set(PLACEHOLDER_RE.findall(data["text"]))
    # Suffixes have no finite verb to conjugate. Free rewrites remain writer suggestions.
    if slots - {"poss", "objposs", "np"} or data["text"].count("{") != len(PLACEHOLDER_RE.findall(data["text"])) or "}" in PLACEHOLDER_RE.sub("", data["text"]):
        raise SchemaError(f"{owner}: imagery slots must be poss, objposs or np")
    data["vulgarity"] = max((strength(w) for w in re.findall(r"[a-z']+", data["text"].lower())), default=0)
    return Imagery(**data)



@dataclass(frozen=True)
class Entry:
    id: str
    form: str
    concept: tuple[str, ...]
    frame: str
    variants: tuple[str, ...] = ()
    insult: bool = False              # a garnish that calls someone names, fond or not ("ya galah", "ya old
                                      # bastard"), which a genre's form may rule out (genres.yaml garnish: insult)
    spellings: tuple[str, ...] = ()   # the variants that only spell the form another way (bickie for bikkie): a
                                      # text keeps the first it uses
    intensity: int = 3
    vulgarity: int = 0
    mask: tuple[str, ...] = ()      # words a page may hide in its renderings, at its vulgarity, where none of its
                                    # rudeness is a listed swear ("wanker"); see masks.py
    profane: bool = True            # False: rated above nan, but nothing in it is profanity (innuendo, an insult or
                                    # a crude word: "rooted", "mongrel", "gob"), so nothing in it is masked (O23)
    incoherence: int = 1
    register: str = "current"
    region: tuple[str, ...] = ()
    replaces: tuple[str, ...] = ()
    status: str = "active"
    flags: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    gloss: str = ""
    slots: dict[str, str] = field(default_factory=dict)
    type: str = "idiom"
    plural: str | None = None
    number: str = "any"             # np only: "plural" for a term that names many (the pollies, punters), which
                                    # doesn't stand for one; "any" for the rest (togs and strides are one garment)
    weight: float = 1.0
    plain_sense: bool = False       # the form has an ordinary English sense too ("shame", "a bit rough"): lint
                                    # doesn't flag it when gated, since it can't tell the senses apart
    cls: str | None = None          # lexical | phrase | idiom; derived when absent
    placement: str | None = None    # garnish only: connective | opener | tag | aside | tail | closer
    when: tuple[str, ...] = ()      # garnish only: sentence contexts it suits (defaults by placement)
    stretch: bool = False           # garnish only: stretch the first vowel ("faaaark")
    tone: str = "plain"             # comic | grim | plain: comic garnish skips dark and solemn texts, and a comic
                                    # term ("carked it") skips solemn ones (an obituary)
    notes: str = ""
    key_sha256: str | None = None   # for redacted omit entries (e.g. slurs) so re-scrapes stay blocked
    origin_file: str = ""
    riffs: tuple["Riff", ...] = ()   # the images it calls up, from riffs.yaml

    @property
    def substitution_class(self) -> str:
        if self.cls:
            return self.cls
        if self.frame in IDIOM_FRAMES or len(self.form.split()) > 3:
            return "idiom"
        if len(self.form.split()) > 1:
            return "phrase"
        return "lexical"

    def riffs_within(self, cap: int) -> tuple["Riff", ...]:
        """The riffs offered under a vulgarity cap, best first (riffs.yaml lists the best first)."""
        return tuple(r for r in self.riffs if r.vulgarity <= cap)

    @property
    def spelling_group(self) -> frozenset[str]:
        """The form and its other spellings, if it has any: one word, spelt more than one way."""
        return frozenset((self.form,) + self.spellings) if self.spellings else frozenset()

    @property
    def all_forms(self) -> tuple[str, ...]:
        return (self.form,) + self.variants

    def to_dict(self) -> dict[str, Any]:
        """Canonical, minimal dict for writing back to YAML: defaults omitted, keys in ENTRY_KEYS order."""
        out: dict[str, Any] = {}
        defaults = Entry(id="", form="", concept=(), frame="np")
        for key in ENTRY_KEYS:
            name = "cls" if key == "class" else key
            value = getattr(self, name)
            if key not in ("id", "form", "concept", "frame") and value == getattr(defaults, name):
                continue
            out[key] = list(value) if isinstance(value, tuple) else value
        return out


@dataclass(frozen=True)
class Concept:
    id: str
    description: str
    triggers: dict[str, tuple[str, ...]]  # frame -> plain-English patterns ("swamped@4")
    person: bool = False                  # concept describes a person (enables clause idioms)
    neutral_person: bool = False          # names people neutrally (someone, children, the dead): a swear for
                                          # it only goes where the genre allows person swears
    not_in: frozenset[str] = frozenset()  # genres where its triggers are terms of art (a browser's cookie, a
                                          # struct's field, a build): left as they are there


# Every key an entry may carry, in the order a written entry lists them.
ENTRY_KEYS = (
    "id", "form", "variants", "spellings", "insult", "concept", "frame", "class", "plural", "number", "slots", "intensity", "vulgarity",
    "mask", "profane", "incoherence", "register", "region", "replaces", "status", "flags", "plain_sense", "type", "placement", "when",
    "stretch",
    "tone", "weight", "gloss", "notes", "sources", "key_sha256",
)


def _tuple(value: Any, name: str, entry_id: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise SchemaError(f"{entry_id}: '{name}' must be a list of strings, got {value!r}")
    return tuple(value)


def _bool(raw: dict, name: str, owner: str) -> bool:
    value = raw.get(name, False)
    if not isinstance(value, bool):
        raise SchemaError(f"{owner}: '{name}' must be true or false, got {value!r}")
    return value


def _int_range(raw: dict, name: str, lo: int, hi: int, default: int, entry_id: str) -> int:
    value = raw.get(name, default)
    if not isinstance(value, int) or not lo <= value <= hi:
        raise SchemaError(f"{entry_id}: '{name}' must be an integer {lo}-{hi}, got {value!r}")
    return value


def _number(raw: dict, entry_id: str) -> str:
    number = raw.get("number", "any")
    if number not in ("any", "plural"):
        raise SchemaError(f"{entry_id}: 'number' must be any or plural, got {number!r}")
    return number


def parse_entry(raw: dict, origin: str = "") -> Entry:
    if not isinstance(raw, dict):
        raise SchemaError(f"{origin}: entry must be a mapping, got {type(raw).__name__}")
    entry_id = raw.get("id")
    if not entry_id or not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry_id):
        raise SchemaError(f"{origin}: entry id must be kebab-case, got {entry_id!r}")
    unknown = set(raw) - set(ENTRY_KEYS)
    if unknown:
        raise SchemaError(f"{entry_id}: unknown field(s) {sorted(unknown)}")
    form = raw.get("form")
    if not form or not isinstance(form, str):
        raise SchemaError(f"{entry_id}: 'form' is required")

    frame = raw.get("frame")
    if frame not in FRAMES:
        raise SchemaError(f"{entry_id}: frame must be one of {FRAMES}, got {frame!r}")
    etype = raw.get("type", "idiom")
    if etype not in TYPES:
        raise SchemaError(f"{entry_id}: type must be one of {TYPES}")
    status = raw.get("status", "active")
    if status not in STATUSES:
        raise SchemaError(f"{entry_id}: status must be one of {STATUSES}")
    register = raw.get("register", "current")
    if register not in REGISTERS:
        raise SchemaError(f"{entry_id}: register must be one of {REGISTERS}")
    flags = _tuple(raw.get("flags"), "flags", entry_id)
    bad = set(flags) - set(FLAGS)
    if bad:
        raise SchemaError(f"{entry_id}: unknown flag(s) {sorted(bad)}")
    cls = raw.get("class")
    if cls is not None and cls not in CLASSES:
        raise SchemaError(f"{entry_id}: class must be one of {CLASSES}")
    placement = raw.get("placement")
    if etype == "garnish":
        if placement not in PLACEMENTS:
            raise SchemaError(f"{entry_id}: garnish entries need placement in {PLACEMENTS}")
    elif placement is not None:
        raise SchemaError(f"{entry_id}: 'placement' is only valid on garnish entries")
    when = _tuple(raw.get("when"), "when", entry_id)
    if set(when) - set(CONTEXTS):
        raise SchemaError(f"{entry_id}: 'when' must be from {CONTEXTS}")

    slots = raw.get("slots") or {}
    if not isinstance(slots, dict):
        raise SchemaError(f"{entry_id}: 'slots' must be a mapping")
    slots = dict(slots)
    variants = _tuple(raw.get("variants"), "variants", entry_id)
    spellings = _tuple(raw.get("spellings"), "spellings", entry_id)
    if set(spellings) - set(variants):
        raise SchemaError(f"{entry_id}: spellings must be among its variants: {sorted(set(spellings) - set(variants))}")
    for text in (form,) + variants:
        for name in PLACEHOLDER_RE.findall(text):
            if name not in SLOT_KINDS:
                raise SchemaError(f"{entry_id}: unknown slot {{{name}}} in {text!r}")
            slots.setdefault(name, SLOT_KINDS[name])
    for name, kind in slots.items():
        if SLOT_KINDS.get(name) != kind:
            raise SchemaError(f"{entry_id}: slot {name} must be of kind {SLOT_KINDS.get(name)!r}")
    if frame == "clause" and PLACEHOLDER_RE.search(form) and not form.startswith(("{subj}", "there ")):
        raise SchemaError(f"{entry_id}: clause forms with slots must start with {{subj}} or 'there'")
    if frame != "clause" and "subj" in slots:
        raise SchemaError(f"{entry_id}: only clause frames may use {{subj}}")

    concept = _tuple(raw.get("concept"), "concept", entry_id)
    if not concept and etype != "garnish" and "untagged" not in flags:
        raise SchemaError(f"{entry_id}: at least one concept is required")
    if "untagged" in flags and status == "active":
        raise SchemaError(f"{entry_id}: untagged entries cannot be active")
    if "slur" in flags and status != "omit":
        raise SchemaError(f"{entry_id}: entries flagged 'slur' must have status omit")

    tone = raw.get("tone", "plain")
    if tone not in RIFF_TONES:
        raise SchemaError(f"{entry_id}: tone must be one of {RIFF_TONES}")

    mask = _tuple(raw.get("mask"), "mask", entry_id)
    profane = raw.get("profane", True)
    if not isinstance(profane, bool):
        raise SchemaError(f"{entry_id}: 'profane' must be true or false")
    if (mask or not profane) and not raw.get("vulgarity"):
        raise SchemaError(f"{entry_id}: 'mask' and 'profane: false' are for an entry rated vulgarity 1 or more")
    if mask and not profane:
        raise SchemaError(f"{entry_id}: an entry with nothing profane has nothing to mask; give it 'mask' or "
                          "'profane: false', not both")
    for word in mask:
        if not MASK_WORD_RE.fullmatch(word) or word != normalise_word(word) or not any(
                re.search(rf"(?<![a-z]){re.escape(word)}", f.lower()) for f in (form,) + variants):
            raise SchemaError(f"{entry_id}: mask word {word!r} must be a lower-case word in one of its forms")

    weight = raw.get("weight", 1.0)
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise SchemaError(f"{entry_id}: weight must be a positive number")

    return Entry(
        id=entry_id,
        form=form,
        variants=variants,
        spellings=spellings,
        insult=bool(raw.get("insult", False)),
        concept=concept,
        frame=frame,
        intensity=_int_range(raw, "intensity", 1, 5, 3, entry_id),
        vulgarity=_int_range(raw, "vulgarity", 0, 3, 0, entry_id),
        incoherence=_int_range(raw, "incoherence", 1, 5, 1, entry_id),
        register=register,
        region=_tuple(raw.get("region"), "region", entry_id),
        replaces=_tuple(raw.get("replaces"), "replaces", entry_id),
        status=status,
        flags=flags,
        sources=_tuple(raw.get("sources"), "sources", entry_id),
        gloss=raw.get("gloss", "") or "",
        slots=dict(slots),
        type=etype,
        plural=raw.get("plural"),
        number=_number(raw, entry_id),
        weight=float(weight),
        cls=cls,
        placement=placement,
        when=when,
        stretch=_bool(raw, "stretch", entry_id),
        plain_sense=_bool(raw, "plain_sense", entry_id),
        mask=mask,
        profane=profane,
        tone=tone,
        notes=raw.get("notes", "") or "",
        key_sha256=raw.get("key_sha256"),
        origin_file=origin,
    )


def parse_not_in(where: str, raw: Any) -> frozenset[str]:
    """The genres where something is a term of art (a concept's triggers, a dialect swap). A misspelt genre would
    silently switch the guard off, so it's refused."""
    not_in = frozenset(raw or ())
    if not_in - set(GENRES):
        raise SchemaError(f"{where}: not_in has unknown genres {sorted(not_in - set(GENRES))} (use {', '.join(GENRES)})")
    return not_in


def parse_concept(cid: str, raw: dict) -> Concept:
    if not isinstance(cid, str):
        raise SchemaError(f"concept id {cid!r} is not a string (YAML reads bare YES/NO/ON/OFF as booleans)")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", cid):
        raise SchemaError(f"concept id must be UPPER_SNAKE, got {cid!r}")
    triggers = raw.get("triggers") or {}
    if not isinstance(triggers, dict):
        raise SchemaError(f"concept {cid}: 'triggers' must be a mapping of frame to patterns")
    for frame in triggers:
        if frame not in FRAMES:
            raise SchemaError(f"concept {cid}: unknown trigger frame {frame!r}")
    not_in = parse_not_in(f"concept {cid}", raw.get("not_in"))
    return Concept(
        id=cid,
        description=raw.get("description", ""),
        triggers={f: _tuple(v, f"triggers.{f}", f"concept {cid}") for f, v in triggers.items()},
        person=_bool(raw, "person", f"concept {cid}"),
        neutral_person=_bool(raw, "neutral_person", f"concept {cid}"),
        not_in=not_in,
    )
