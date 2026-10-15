"""Caller policy: level, seed and the filters layered over a level profile."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields
from typing import Any, Sequence

from .dialect import ENGLISHES
from .errors import UserError
from .model import Dictionary, LevelProfile, SwearProfile
from .schema import FLAGS, REGISTERS


# The dials, by number or by name. Names are aliases: everything inside works in numbers. The level is how thick
# the slang, vulgarity how strong the language, embellishment how much liberty the telling takes (garnish, a
# talker's colour, a yarn's elaboration: data/genres.yaml).
LEVELS = {"tourist": 1, "blow-in": 2, "local": 3, "larrikin": 4, "swaggie": 5}
VULGARITIES = {"nan": 0, "dad": 1, "uncle-bob": 2, "tradie": 3}
EMBELLISHMENTS = {"deadset": 0, "dinkum": 1, "troppo": 2}
LEVEL_NAMES = {v: k for k, v in LEVELS.items()}
VULGARITY_NAMES = {v: k for k, v in VULGARITIES.items()}
EMBELLISHMENT_NAMES = {v: k for k, v in EMBELLISHMENTS.items()}


def _parse(value: int | str, names: dict[str, int], what: str) -> int:
    if isinstance(value, str):
        key = "-".join(value.strip().lower().replace("_", " ").split())
        if key.isdigit():
            value = int(key)
        elif key in names:
            return names[key]
        else:
            raise UserError(f"unknown {what} {value!r}: use {_choices(names)}")
    if not isinstance(value, int) or isinstance(value, bool) or value not in names.values():
        raise UserError(f"{what} must be {_choices(names)}, not {value!r}")
    return value


def _choices(names: dict[str, int]) -> str:
    return ", ".join(f"{n} ({name})" for name, n in names.items())


def parse_level(value: int | str) -> int:
    """1-5, or tourist, blow-in, local, larrikin, swaggie (any case; spaces or underscores for the hyphen)."""
    return _parse(value, LEVELS, "level")


def parse_vulgarity(value: int | str) -> int:
    """0-3, or nan, dad, uncle-bob, tradie (any case; spaces or underscores for the hyphen)."""
    return _parse(value, VULGARITIES, "vulgarity")


def parse_embellishment(value: int | str) -> int:
    """0-2, or deadset, dinkum, troppo (any case)."""
    return _parse(value, EMBELLISHMENTS, "embellishment")


DOCUMENT_TYPES = ("general", "custom", "auto", "story", "personal", "news", "instructions", "technical", "official")


@dataclass(frozen=True)
class DocumentOverrides:
    """Exact overrides on a document preset. None means inherit; false and empty lists are explicit."""
    garnish: tuple[str, ...] | None = None
    openings: bool | None = None
    formal_to_rework: bool | None = None
    person_swears: bool | None = None
    keep_quotes: bool | None = None
    check_length: bool | None = None
    term_domains: tuple[str, ...] | None = None
    command_context: bool | None = None
    dateline_context: bool | None = None
    guidance: str | None = None
    draft: bool | None = None
    keep_share: float | None = None
    max_length: float | None = None
    perform: bool | None = None
    embellishment_guidance: str | None = None

    @classmethod
    def parse(cls, raw):
        import math
        from .schema import GENRES, PLACEMENTS

        if isinstance(raw, cls):
            raw = raw.values()
        if raw is None:
            return cls()
        if not isinstance(raw, dict):
            raise UserError("document_config must be an object of behaviour overrides")
        names = {f.name for f in fields(cls)}
        if any(not isinstance(k, str) for k in raw):
            raise UserError("document_config setting names must be strings")
        if set(raw) - names:
            raise UserError(f"unknown document_config settings: {', '.join(sorted(set(raw) - names))}")
        data = dict(raw)
        booleans = {"openings", "formal_to_rework", "person_swears", "keep_quotes", "command_context",
                    "dateline_context", "draft", "perform", "check_length"}
        for key, value in data.items():
            if key in booleans and type(value) is not bool:
                raise UserError(f"document_config.{key} must be true or false")
            if key in ("guidance", "embellishment_guidance") and not isinstance(value, str):
                raise UserError(f"document_config.{key} must be text")
            if key in ("garnish", "term_domains"):
                allowed = (*PLACEMENTS, "riff", "infix", "insult") if key == "garnish" else GENRES
                if not isinstance(value, (list, tuple)) or any(not isinstance(v, str) or v not in allowed for v in value):
                    raise UserError(f"document_config.{key} must be a list from {', '.join(allowed)}")
                data[key] = tuple(dict.fromkeys(value))
            if key in ("keep_share", "max_length"):
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise UserError(f"document_config.{key} must be a finite number")
                if (key == "keep_share" and not 0 <= value <= 1) or (key == "max_length" and value < 1):
                    raise UserError(f"document_config.{key} must be {'between 0 and 1' if key == 'keep_share' else 'at least 1'}")
        return cls(**data)

    def values(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}


@dataclass(frozen=True)
class Policy:
    level: int | str = 5
    seed: int = 0
    vulgarity: int | str | None = None    # None: the level's own (profiles.yaml); set, it wins either way
    registers: tuple[str, ...] | None = None
    regions: tuple[str, ...] = ()         # prefer/limit regional entries (e.g. "qld")
    unlock: tuple[str, ...] = ()          # gated entries become eligible when all their flags are unlocked
    embedder: str | None = "ngram"
    similarity_threshold: float = 0.72
    variety: int = 0                      # 0: weighted pick over every eligible entry; N: only the N best fits
    english: str = "auto"                 # the source's English (dialect.ENGLISHES): us, uk, auto, none
    embellishment: int | str | None = None   # None: the text's genre's own (genres.yaml); set, it wins

    document_type: str = "general"
    document_config: DocumentOverrides | dict | None = None

    def __post_init__(self):
        if self.document_type not in DOCUMENT_TYPES:
            raise UserError(f"document_type must be one of {', '.join(DOCUMENT_TYPES)}")
        object.__setattr__(self, "document_config", DocumentOverrides.parse(self.document_config))
        object.__setattr__(self, "level", parse_level(self.level))
        if self.vulgarity is not None:
            object.__setattr__(self, "vulgarity", parse_vulgarity(self.vulgarity))
        if self.embellishment is not None:
            object.__setattr__(self, "embellishment", parse_embellishment(self.embellishment))
        if self.variety < 0:
            raise UserError("variety must be 0 (all eligible) or a positive top-N")
        if self.english not in ENGLISHES:
            raise UserError(f"english must be one of {', '.join(ENGLISHES)}, got {self.english!r}")
        for name in ("registers", "regions", "unlock"):   # a value object: lists in, tuples kept
            value = getattr(self, name)
            if isinstance(value, str):   # tuple("current") would be its letters
                raise UserError(f"{name} must be a list, e.g. [{value!r}], not a string")
            if value is not None:
                object.__setattr__(self, name, tuple(value))
        _closed_set("register", self.registers or (), REGISTERS)
        _closed_set("unlock flag", self.unlock, (*FLAGS, "all"))

    @classmethod
    def from_mapping(cls, raw: dict[str, Any], **overrides) -> "Policy":
        """The dictionary's policy defaults (profiles.yaml `policy:`), with the caller's non-None overrides."""
        known = {f for f in cls.__dataclass_fields__}
        data = {k: v for k, v in (raw or {}).items() if k in known}
        data.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**data)


def _closed_set(what: str, values: tuple, allowed: tuple[str, ...]) -> None:
    bad = [v for v in values if v not in allowed]
    if bad:
        raise UserError(f"unknown {what}(s) {', '.join(map(repr, bad))}: use {', '.join(allowed)}")


def envelope(level: int, vulgarity: int, warnings: Sequence[str]) -> dict[str, Any]:
    """What every toolkit result reports about the policy it ran under."""
    return {"level": level, "level_name": LEVEL_NAMES[level], "vulgarity": vulgarity,
            "vulgarity_name": VULGARITY_NAMES[vulgarity], "policy_warnings": list(warnings)}


@dataclass(frozen=True)
class Effective:
    """The policy resolved against a level profile; what selection actually checks."""
    level: int
    profile: LevelProfile
    vulgarity: int                        # the strongest language allowed: the caller's, or the level's own
    registers: tuple[str, ...]
    regions: tuple[str, ...]
    unlock: frozenset[str]
    warnings: tuple[str, ...] = ()
    swearing: SwearProfile = SwearProfile()   # how often swearing comes at this vulgarity

    def envelope(self) -> dict[str, Any]:
        return envelope(self.level, self.vulgarity, self.warnings)


def resolve(policy: Policy, dictionary: Dictionary) -> Effective:
    """The level and vulgarity are independent dials: the level sets a default vulgarity (profiles.yaml) and an
    explicit vulgarity wins in either direction ("swaggie" but "nan", or "local" but "tradie")."""
    profile = dictionary.profiles[policy.level]
    vulgarity = profile.vulgarity if policy.vulgarity is None else policy.vulgarity
    registers = policy.registers if policy.registers is not None else profile.registers
    return Effective(policy.level, profile, vulgarity, tuple(registers), tuple(policy.regions),
                     frozenset(policy.unlock), _warnings(policy, dictionary),
                     swearing=dictionary.swearing.get(vulgarity, SwearProfile()))


def _warnings(policy: Policy, dictionary: Dictionary) -> tuple[str, ...]:
    """Settings that are valid but that this dictionary gives nothing to act on."""
    out = [f"no entry is tagged with region {r!r} (tagged: {', '.join(sorted(dictionary.regions)) or 'none'})"
           for r in policy.regions if r not in dictionary.regions]
    out += [f"no gated entry carries the flag {f!r}, so unlocking it changes nothing"
            for f in policy.unlock if f != "all" and f not in dictionary.gate_flags]
    return tuple(out)


def roll(seed: int, *parts: object) -> float:
    """Deterministic uniform [0, 1) keyed by seed and context, stable across runs and platforms."""
    key = "\x1f".join([str(seed), *map(str, parts)]).encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big") / 2**64


def weighted_index(weights: Sequence[float], r: float) -> int:
    """The index a roll r in [0, 1) lands on, each item as likely as its weight (the last on rounding)."""
    target, acc = r * sum(weights), 0.0
    for i, w in enumerate(weights):
        acc += w
        if target < acc:
            return i
    return len(weights) - 1


def pick_form(forms: Sequence[str], seed: int, *key: object) -> str:
    """One of an entry's forms (its form and variants), by a roll keyed by seed and context."""
    return forms[int(roll(seed, "variant", *key) * len(forms))]
