"""Validate the data boundary for reviewed construction families and their ingredients."""

from __future__ import annotations

import math
import re
from collections.abc import Callable

from .constructions import ConstructionCatalog, ConstructionFamily, Ingredient, template_fragments
from .errors import SchemaError
from .evidence import METADATA_KEYS, TermMetadata, parse_metadata
from .schema import FRAMES, RIFF_TONES, parse_degrees


def _record(raw, allowed, owner):
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw) or set(raw) - set(allowed):
        raise SchemaError(f"{owner}: expected fields {', '.join(sorted(allowed))}")
    return raw


def _identifier(value, owner):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", value):
        raise SchemaError(f"{owner}: expected a lower-case identifier")
    return value


def _integer(value, low, high, owner):
    if type(value) is not int or not low <= value <= high:
        raise SchemaError(f"{owner}: expected an integer from {low} to {high}")
    return value


def _number(value, owner):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise SchemaError(f"{owner}: expected a finite non-negative number")
    return value


def parse_catalog(raw, entries, concepts, rate_text: Callable[[str], int],
                  assessed: Callable[[TermMetadata], TermMetadata]) -> ConstructionCatalog | None:
    if raw == {}:
        return None
    _record(raw, {"version", "settings", "ingredients", "families"}, "constructions.yaml")
    if raw.get("version") != "aussiefy-constructions/v1":
        raise SchemaError("constructions.yaml: expected version aussiefy-constructions/v1")
    settings = _record(raw.get("settings"), {"search_budget", "max_results", "cadence_penalty"}, "construction settings")
    if set(settings) != {"search_budget", "max_results", "cadence_penalty"}:
        raise SchemaError("construction settings: every setting is required")
    _integer(settings["search_budget"], 1, 1024, "construction search_budget")
    _integer(settings["max_results"], 5, 100, "construction max_results")
    _number(settings["cadence_penalty"], "construction cadence_penalty")
    if not isinstance(raw.get("ingredients"), list) or not isinstance(raw.get("families"), list):
        raise SchemaError("constructions.yaml: ingredients and families must be lists")
    ingredients, ids = [], set()
    for row in raw["ingredients"]:
        _record(row, {"id", "kind", "entry_id", "text", "level", "vulgarity", "weight", *METADATA_KEYS}, "ingredient")
        pid = _identifier(row.get("id"), "ingredient id")
        if pid in ids:
            raise SchemaError(f"duplicate ingredient id {pid!r}")
        ids.add(pid)
        kind = _identifier(row.get("kind"), f"ingredient {pid}.kind")
        if "entry_id" in row:
            if set(row) != {"id", "kind", "entry_id"}:
                raise SchemaError(f"{pid}: an entry-backed ingredient inherits all its wording, evidence and limits")
            entry_id = row["entry_id"]
            if not isinstance(entry_id, str) or entry_id not in entries:
                raise SchemaError(f"{pid}: unknown ingredient entry {entry_id!r}")
            if "{" in entries[entry_id].form or "}" in entries[entry_id].form:
                raise SchemaError(f"{pid}: an ingredient needs a fixed entry form")
            ingredients.append(Ingredient(pid, kind, entry_id=entry_id))
            continue
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            raise SchemaError(f"{pid}: an ingredient needs text or entry_id")
        level = _integer(row.get("level", 1), 1, 5, f"{pid}.level")
        vulgarity = max(rate_text(text), _integer(row.get("vulgarity", 0), 0, 3, f"{pid}.vulgarity"))
        weight = _number(row.get("weight", 1), f"{pid}.weight")
        metadata = assessed(TermMetadata(**parse_metadata(row, pid)))
        ingredients.append(Ingredient(pid, kind, text, metadata=metadata, level=level, vulgarity=vulgarity, weight=weight))
    kinds = {part.kind for part in ingredients}
    families, ids = [], set()
    for row in raw["families"]:
        _record(row, {"id", "template", "slots", "concept", "frame", "level", "vulgarity", "weight",
                      "exaggeration", "tone", "preferred_words", "placement", "semantic_degree", *METADATA_KEYS}, "family")
        fid = _identifier(row.get("id"), "family id")
        if fid in ids:
            raise SchemaError(f"duplicate family id {fid!r}")
        ids.add(fid)
        slots = row.get("slots")
        if (not isinstance(slots, dict) or not slots or any(not isinstance(name, str)
                or not re.fullmatch(r"[a-z][a-z0-9_]*", name) for name in slots)):
            raise SchemaError(f"{fid}: slots must map names to ingredient kinds")
        if any(not isinstance(kind, str) or kind not in kinds for kind in slots.values()):
            raise SchemaError(f"{fid}: unknown ingredient kind in slots")
        template = row.get("template")
        if not isinstance(template, str) or not template.strip():
            raise SchemaError(f"{fid}: template must be non-empty text")
        fragments = template_fragments(template, tuple(slots.items()))
        concept, frame = row.get("concept"), row.get("frame")
        if not isinstance(concept, str) or concept not in concepts:
            raise SchemaError(f"{fid}: unknown concept {concept!r}")
        if not isinstance(frame, str) or frame not in FRAMES:
            raise SchemaError(f"{fid}: unknown frame {frame!r}")
        level = _integer(row.get("level", 5), 1, 5, f"{fid}.level")
        vulgarity = max(max((rate_text(literal) for literal, _ in fragments), default=0), _integer(row.get("vulgarity", 0), 0, 3, f"{fid}.vulgarity"))
        weight = _number(row.get("weight", 1), f"{fid}.weight")
        exaggeration = _integer(row.get("exaggeration", 1), 0, 2, f"{fid}.exaggeration")
        tone = row.get("tone", "comic")
        if tone not in RIFF_TONES:
            raise SchemaError(f"{fid}: unknown tone {tone!r}")
        words = row.get("preferred_words", [6, 12])
        if (not isinstance(words, list) or len(words) != 2 or any(type(n) is not int or n < 1 for n in words)
                or words[0] > words[1]):
            raise SchemaError(f"{fid}: preferred_words needs an ordered pair of positive integers")
        placement = row.get("placement")
        if placement is not None and placement != "opener":
            raise SchemaError(f"{fid}: only opener construction garnish is supported")
        if placement == "opener" and frame != "interjection":
            raise SchemaError(f"{fid}: an opener needs an interjection frame")
        degrees = parse_degrees(row.get("semantic_degree", {}), fid)
        if set(degrees) - {concept}:
            raise SchemaError(f"{fid}: semantic_degree must describe the family's concept")
        metadata = assessed(TermMetadata(**parse_metadata(row, fid)))
        families.append(ConstructionFamily(fid, template, tuple(slots.items()), fragments, concept, frame,
                                           metadata, level, vulgarity, weight, exaggeration, tone, tuple(words),
                                           placement, tuple(degrees.items())))
    return ConstructionCatalog(tuple(ingredients), tuple(families), **settings)
