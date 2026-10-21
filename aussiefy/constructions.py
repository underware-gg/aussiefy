"""Seeded composition of reviewed idiom families, with evidence retained on each part."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from math import gcd, prod
from string import Formatter
from typing import TYPE_CHECKING

from .context import tone_weight
from .errors import SchemaError
from .evidence import TermMetadata, assess, metadata_dict, metadata_rejections, theme_rejection
from .policy import policy_rejection, roll, weighted_index
from .terms import form_key
from .text import tokenize

if TYPE_CHECKING:
    from .genre import Embellishment
    from .model import Dictionary
    from .policy import Effective
    from .schema import Entry

DEFAULT_LIMIT = 5


@dataclass(frozen=True)
class Ingredient:
    id: str
    kind: str
    text: str = ""
    entry_id: str | None = None
    metadata: TermMetadata = TermMetadata()
    level: int = 1
    vulgarity: int = 0
    weight: float = 1.0

    def resolve(self, entries: dict[str, Entry]) -> Ingredient:
        if self.entry_id is None:
            return self
        entry = entries[self.entry_id]
        return Ingredient(self.id, self.kind, entry.form, self.entry_id, entry,
                          entry.incoherence, entry.vulgarity, entry.weight)


def template_fragments(template: str, slots: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str | None], ...]:
    try:
        parsed = tuple(Formatter().parse(template))
    except ValueError as exc:
        raise SchemaError(f"invalid construction template: {exc}") from exc
    names = [name for _, name, _, _ in parsed if name is not None]
    if len(names) != len(set(names)) or set(names) != {name for name, _ in slots}:
        raise SchemaError("a construction template must use every declared slot exactly once")
    if any(spec or conversion for _, _, spec, conversion in parsed):
        raise SchemaError("construction templates do not accept format directives")
    return tuple((literal, name) for literal, name, _, _ in parsed)


@dataclass(frozen=True)
class ConstructionFamily:
    id: str
    template: str
    slots: tuple[tuple[str, str], ...]
    fragments: tuple[tuple[str, str | None], ...]
    concept: str
    frame: str
    metadata: TermMetadata = TermMetadata()
    level: int = 5
    vulgarity: int = 0
    weight: float = 1.0
    exaggeration: int = 1
    tone: str = "comic"
    preferred_words: tuple[int, int] = (6, 12)
    placement: str | None = None
    semantic_degree: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ConstructionCatalog:
    ingredients: tuple[Ingredient, ...] = ()
    families: tuple[ConstructionFamily, ...] = ()
    search_budget: int = 64
    max_results: int = 20
    cadence_penalty: float = 0.1


@dataclass(frozen=True)
class ConstructionPart:
    role: str
    ingredient: Ingredient
    span: tuple[int, int]

    def to_dict(self) -> dict:
        part = self.ingredient
        return {"role": self.role, "ingredient_id": part.id, "entry_id": part.entry_id,
                "text": part.text, "out_span": list(self.span), "level": part.level,
                "vulgarity": part.vulgarity, **metadata_dict(part.metadata, derived=True)}


@dataclass(frozen=True)
class Construction:
    id: str
    family: ConstructionFamily
    text: str
    parts: tuple[ConstructionPart, ...]
    metadata: TermMetadata
    level: int
    vulgarity: int
    cadence: float
    weight: float

    def to_dict(self) -> dict:
        return {"construction_id": self.id, "entry_id": None, "family": self.family.id,
                "text": self.text, "concepts": [self.family.concept], "frame": self.family.frame,
                "level": self.level, "vulgarity": self.vulgarity, "cadence": self.cadence,
                **metadata_dict(self.metadata, derived=True),
                "parts": [part.to_dict() for part in self.parts]}


@dataclass(frozen=True)
class Generation:
    candidates: tuple[Construction, ...]
    attempts: int
    rejected: tuple[tuple[str, str], ...]


def _rejection(metadata: TermMetadata, level: int, vulgarity: int, eff: Effective) -> str | None:
    if reason := theme_rejection(metadata, eff.theme_policy):
        return reason
    held = metadata_rejections(metadata, allow_misreadable=bool({"misreadable", "all"} & eff.unlock))
    if held:
        return "held back: " + ", ".join(held)
    if level > eff.level:
        return f"needs level {level}"
    if vulgarity > eff.vulgarity:
        return f"vulgarity {vulgarity} exceeds cap {eff.vulgarity}"
    if metadata.register not in eff.registers:
        return f"register {metadata.register!r} not allowed"
    return None


def compose(family: ConstructionFamily, chosen: dict[str, Ingredient], dictionary: Dictionary,
            eff: Effective, mood: str = "light") -> Construction:
    """A canonical expression; ingredient text is opaque, and spans are code-point offsets in it."""
    kinds = dict(family.slots)
    chunks, parts, identity = [], [], []
    position = 0
    for literal, name in family.fragments:
        chunks.append(literal)
        position += len(literal)
        if name is None:
            continue
        part = chosen[name]
        if part.kind != kinds[name]:
            raise SchemaError(f"{family.id}.{name}: incompatible ingredient {part.id!r}")
        chunks.append(part.text)
        parts.append(ConstructionPart(name, part, (position, position + len(part.text))))
        position += len(part.text)
        identity.append((name, part.id, part.text))
    text = "".join(chunks)
    payload = json.dumps(["construction-expression/v1", family.id, family.template, identity],
                         ensure_ascii=False, separators=(",", ":")).encode()
    cid = "construction/" + family.id + "/" + hashlib.sha256(payload).hexdigest()[:24]
    tiers = {}
    starts = dict(dictionary.theme_starts)
    for term in (family.metadata, *(part.metadata for part in chosen.values())):
        explicit = dict(term.theme_tiers)
        for theme in term.themes:
            tiers[theme] = max(tiers.get(theme, 0), explicit.get(theme, starts[theme]))
    metadata = TermMetadata(coined_by="constructor", themes=tuple(sorted(tiers)),
                            theme_tiers=tuple(sorted(tiers.items())))
    assessment = assess(metadata, dictionary.evidence_weights)
    metadata = replace(metadata, attestation=assessment.attestation, evidence=assessment.evidence,
                       first_attested=assessment.first_attested)
    words = sum(token.is_word for token in tokenize(text))
    lo, hi = family.preferred_words
    distance = max(lo - words, 0, words - hi)
    cadence = 1 / (1 + dictionary.construction_catalog.cadence_penalty * distance)
    part_weight = prod(part.weight * eff.metadata_weight(part.metadata) for part in chosen.values()) ** (1 / len(chosen))
    weight = family.weight * eff.metadata_weight(family.metadata) * part_weight * tone_weight(family.tone, mood)
    return Construction(cid, family, text, tuple(parts), metadata,
                        max(family.level, *(part.level for part in chosen.values())),
                        max(family.vulgarity, *(part.vulgarity for part in chosen.values())), cadence, weight)


def generate(dictionary: Dictionary, eff: Effective, setting: Embellishment, *, seed: int = 0,
             concept: str | None = None, family: str | None = None, parts: dict[str, str] | None = None,
             limit: int = DEFAULT_LIMIT, placement: str | None = None, mood: str = "light") -> Generation:
    catalog = dictionary.construction_catalog
    if catalog is None:
        return Generation((), 0, ())
    requested = parts or {}
    found, rejected, attempts, seen = [], [], 0, set()
    for pattern in catalog.families:
        if (concept is not None and pattern.concept != concept or family is not None and pattern.id != family
                or placement is not None and pattern.placement != placement
                or not set(requested) <= {name for name, _ in pattern.slots}):
            continue
        reason = _rejection(pattern.metadata, pattern.level, pattern.vulgarity, eff)
        if reason is None and not pattern.weight:
            reason = "zero construction weight"
        if reason is None and pattern.exaggeration > setting.riff_exaggeration:
            reason = "exceeds riff_exaggeration"
        if reason is None and pattern.tone == "comic" and mood == "solemn" and not setting.solemn_comic_terms:
            reason = "a comic construction in solemn text; solemn_comic_terms is false"
        if reason:
            rejected.append((pattern.id, reason))
            continue
        pools = []
        for name, kind in pattern.slots:
            pool = []
            for spec in catalog.ingredients:
                if spec.kind != kind or name in requested and requested[name] != spec.id:
                    continue
                part = spec.resolve(dictionary.entries)
                reason = (policy_rejection(dictionary.entries[part.entry_id], eff) if part.entry_id else
                          _rejection(part.metadata, part.level, part.vulgarity, eff))
                if reason is None and not part.weight:
                    reason = "zero ingredient weight"
                if reason:
                    rejected.append((part.id, reason))
                else:
                    pool.append(part)
            pools.append(sorted(pool, key=lambda part: part.id))
        if any(not pool for pool in pools):
            continue
        size = prod(len(pool) for pool in pools)
        offset = int(roll(seed, "construction-offset", pattern.id) * size)
        stride = int(roll(seed, "construction-stride", pattern.id) * size) | 1
        if gcd(stride, size) != 1:
            stride = 1
        for ordinal in range(min(size, catalog.search_budget)):
            attempts += 1
            index, chosen = (offset + ordinal * stride) % size, {}
            for (name, _), pool in zip(reversed(pattern.slots), reversed(pools), strict=True):
                index, remainder = divmod(index, len(pool))
                chosen[name] = pool[remainder]
            candidate = compose(pattern, chosen, dictionary, eff, mood)
            key = form_key(candidate.text)
            if key in dictionary.known_construction_forms or key in seen:
                continue
            seen.add(key)
            found.append(candidate)
    found.sort(key=lambda candidate: (-candidate.cadence, candidate.id))
    ranked = []
    while found and len(ranked) < limit:
        group = [candidate for candidate in found if candidate.cadence == found[0].cadence]
        pick = weighted_index([candidate.weight for candidate in group], roll(seed, "construction-rank", len(ranked)))
        candidate = group[pick]
        ranked.append(candidate)
        found.remove(candidate)
    return Generation(tuple(ranked), attempts, tuple(dict.fromkeys(rejected)))
