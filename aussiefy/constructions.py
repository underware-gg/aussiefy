"""Seeded composition of reviewed idiom families, with evidence retained on each part."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, fields, replace
from math import gcd, prod
from string import Formatter
from typing import TYPE_CHECKING

from .context import tone_weight
from .errors import SchemaError
from .masks import profanity_rating
from .evidence import TermMetadata, assess, metadata_dict, metadata_rejections, theme_rejection, register_rejection
from .policy import policy_rejection, roll, weighted_index
from .terms import form_key
from .text import tokenize

if TYPE_CHECKING:
    from .genre import Embellishment
    from .model import Dictionary
    from .policy import Effective
    from .schema import Entry
    from .themes import ThemePermissions

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
    converted_parts: tuple[tuple[str, str], ...] = ()


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

    def to_dict(self, permitted_themes=None) -> dict:
        part = self.ingredient
        return {"role": self.role, "ingredient_id": part.id, "entry_id": part.entry_id,
                "text": part.text, "out_span": list(self.span), "level": part.level,
                "vulgarity": part.vulgarity, **_presentation(part.metadata, permitted_themes, vulgarity=part.vulgarity)}


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

    @property
    def usage_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.id, *(part.ingredient.entry_id for part in self.parts
                                              if part.ingredient.entry_id))))

    def to_dict(self, permitted_themes=None) -> dict:
        return {"construction_id": self.id, "entry_id": None, "family": self.family.id,
                "text": self.text, "concepts": [self.family.concept], "frame": self.family.frame,
                "level": self.level, "vulgarity": self.vulgarity, "cadence": self.cadence,
                **_presentation(self.metadata, permitted_themes, vulgarity=self.vulgarity),
                "parts": [part.to_dict(permitted_themes) for part in self.parts]}


def _presentation(term, permitted_themes, *, vulgarity):
    if permitted_themes is None:
        return metadata_dict(term, derived=True)
    from .cards import metadata
    return metadata(term, permitted_themes, vulgarity=vulgarity)


@dataclass(frozen=True)
class Generation:
    candidates: tuple[Construction, ...]
    attempts: int
    rejected: tuple[tuple[str, str], ...]


def _rejection(metadata: TermMetadata, level: int, vulgarity: int, eff: Effective) -> str | None:
    if reason := theme_rejection(metadata, eff.theme_policy):
        return reason
    held = metadata_rejections(metadata, allow_misreadable=eff.allow_misreadable)
    if held:
        return "held back: " + ", ".join(held)
    if level > eff.level:
        return f"needs level {level}"
    if vulgarity > eff.vulgarity:
        return f"vulgarity {vulgarity} exceeds cap {eff.vulgarity}"
    return register_rejection(metadata, eff.registers)


def composite_metadata(family: ConstructionFamily, parts, dictionary: Dictionary) -> TermMetadata:
    tiers = {}
    starts = dict(dictionary.theme_starts)
    for term in (family.metadata, *(part.metadata for part in parts)):
        explicit = dict(term.theme_tiers)
        for theme in term.themes:
            tiers[theme] = max(tiers.get(theme, 0), explicit.get(theme, starts[theme]))
    metadata = TermMetadata(coined_by="constructor", themes=tuple(sorted(tiers)),
                            theme_tiers=tuple(sorted(tiers.items())))
    assessment = assess(metadata, dictionary.evidence_weights)
    metadata = replace(metadata, attestation=assessment.attestation, evidence=assessment.evidence,
                       first_attested=assessment.first_attested)
    return metadata


def construction_identity(family: ConstructionFamily, chosen: dict[str, Ingredient]) -> str:
    """Content identity, independent of seed, weights, sampling order and request state."""
    identity = [(name, chosen[name].id, chosen[name].text) for _, name in family.fragments if name is not None]
    payload = json.dumps(["construction-expression/v1", family.id, family.template, identity],
                         ensure_ascii=False, separators=(",", ":")).encode()
    return "construction/" + family.id + "/" + hashlib.sha256(payload).hexdigest()[:24]


def compose(family: ConstructionFamily, chosen: dict[str, Ingredient], dictionary: Dictionary,
            eff: Effective, mood: str = "light") -> Construction:
    """A canonical expression; ingredient text is opaque, and spans are code-point offsets in it."""
    kinds = dict(family.slots)
    chunks, parts = [], []
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
    text = "".join(chunks)
    cid = construction_identity(family, chosen)
    metadata = composite_metadata(family, chosen.values(), dictionary)
    words = sum(token.is_word for token in tokenize(text))
    lo, hi = family.preferred_words
    distance = max(lo - words, 0, words - hi)
    cadence = 1 / (1 + dictionary.construction_catalog.cadence_penalty * distance)
    part_weight = prod(part.weight * eff.metadata_weight(part.metadata) for part in chosen.values())
    weight = family.weight * eff.metadata_weight(family.metadata) * part_weight * tone_weight(family.tone, mood)
    return Construction(cid, family, text, tuple(parts), metadata,
                        max(family.level, *(part.level for part in chosen.values())),
                        max(family.vulgarity, *(part.vulgarity for part in chosen.values()),
                            profanity_rating(text, dictionary, canonical_spans=[
                                (*part.span, part.ingredient.vulgarity) for part in parts if part.ingredient.entry_id])),
                        cadence, weight)


def rendering_entry(construction: Construction, dictionary: Dictionary) -> Entry:
    """A transient view for shared entry fit checks, never inserted in the dictionary or sent as an entry card."""
    from .schema import Entry
    c = construction
    facts = {f.name: getattr(c.metadata, f.name) for f in fields(TermMetadata)}
    return Entry(id=c.id, form=c.text, concept=(c.family.concept,), frame=c.family.frame,
                 incoherence=c.level, vulgarity=c.vulgarity, weight=c.weight, cls="idiom",
                 semantic_degree=dict(c.family.semantic_degree), tone=c.family.tone,
                 gloss=dictionary.concepts[c.family.concept].description, **facts)


def family_rejection(pattern, eff, setting, mood="light"):
    reason = _rejection(pattern.metadata, pattern.level, pattern.vulgarity, eff)
    if reason is None and not pattern.weight:
        reason = "zero construction weight"
    if reason is None and pattern.exaggeration > setting.riff_exaggeration:
        reason = "exceeds riff_exaggeration"
    if reason is None and pattern.tone == "comic" and mood == "solemn" and not setting.solemn_comic_terms:
        reason = "a comic construction in solemn text; solemn_comic_terms is false"
    return reason


def ingredient_pools(pattern, catalog, dictionary, eff, requested=None):
    requested = requested or {}
    pools, rejected = [], []
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
    return pools, rejected


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
        reason = family_rejection(pattern, eff, setting, mood)
        if reason:
            rejected.append((pattern.id, reason))
            continue
        pools, excluded = ingredient_pools(pattern, catalog, dictionary, eff, requested)
        rejected.extend(excluded)
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
            if candidate.vulgarity > eff.vulgarity:
                rejected.append((candidate.id, f"vulgarity {candidate.vulgarity} exceeds cap {eff.vulgarity}"))
                continue
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


@dataclass(frozen=True)
class ConstructionPattern:
    family: ConstructionFamily
    steps: tuple[tuple[tuple[re.Pattern, Ingredient | None], ...], ...]


def _literal_pattern(text: str) -> str:
    normalized = text.replace("’", "'")
    return (r"\s*" if normalized.startswith("'") else "") + "".join(
        r"\s+" if chunk.isspace() else re.escape(chunk) for chunk in re.split(r"(\s+)", normalized))


def construction_patterns(dictionary: Dictionary) -> tuple[ConstructionPattern, ...]:
    catalog = dictionary.construction_catalog
    if catalog is None:
        return ()
    pools = defaultdict(list)
    for spec in catalog.ingredients:
        part = spec.resolve(dictionary.entries)
        pools[part.kind].append((re.compile(_literal_pattern(part.text), re.I), part))
    patterns = []
    for family in catalog.families:
        kinds, steps = dict(family.slots), []
        for literal, name in family.fragments:
            if literal:
                steps.append(((re.compile(_literal_pattern(literal), re.I), None),))
            if name is not None:
                steps.append(tuple(pools[kinds[name]]))
        patterns.append(ConstructionPattern(family, tuple(steps)))
    return tuple(patterns)


def _step_matches(options, text, position):
    for pattern, part in options:
        match = pattern.match(text, position)
        if match is None:
            continue
        first_end = match.end()
        if pattern.pattern.endswith(r"\s+"):
            # Leave possible whitespace for the next step instead of committing to a greedy split.
            while first_end > position and text[first_end - 1].isspace():
                first_end -= 1
            first_end += 1
        for end in range(first_end, match.end() + 1):
            yield end, part


def construction_matches(text: str, dictionary: Dictionary, permitted: ThemePermissions):
    """Match recipes by text position, merging ambiguous paths rather than enumerating combinations.

    At each step/position, an allowed reading dominates a blocked one: adding later parts can only
    raise theme tiers. Transition work is cached per call and bounded by text length and recipe size.
    """
    normalized = text.replace("’", "'")
    for recipe in dictionary.construction_patterns:
        transitions = {}
        blocked = {part.id: bool(theme_rejection(part.metadata, permitted))
                   for step in recipe.steps for _, part in step if part is not None}
        family_blocked = bool(theme_rejection(recipe.family.metadata, permitted))
        for start in range(len(normalized)):
            if start and re.match(r"\w", normalized[start - 1]):
                continue
            states = {start: (family_blocked, ())}
            for stage, options in enumerate(recipe.steps):
                next_states = {}
                for position, (held, chosen) in states.items():
                    key = stage, position
                    if key not in transitions:
                        transitions[key] = tuple(_step_matches(options, normalized, position))
                    for end, part in transitions[key]:
                        path = held or (part is not None and blocked[part.id]), chosen + ((part,) if part else ())
                        previous = next_states.get(end)
                        if previous is None or previous[0] and not path[0]:
                            next_states[end] = path
                states = next_states
                if not states:
                    break
            for end, (_, chosen) in states.items():
                if end > start and (end == len(normalized) or not re.match(r"\w", normalized[end])):
                    yield start, end, composite_metadata(recipe.family, chosen, dictionary)
