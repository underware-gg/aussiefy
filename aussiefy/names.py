"""Seeded clean handles from a reviewed name catalogue, without account or uniqueness state."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import SchemaError, UserError
from .masks import profanity_rating
from .policy import roll
from .schema import PLACEHOLDER_RE
from .text import sentences, tokenize
from .terms import name_slug as _slug

SHAPES = ("descriptive", "place", "phrase")
NAME_SEARCH_BUDGET = 32
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class NameCatalog:
    descriptors: tuple[str, ...]
    things: tuple[str, ...]
    nicknames: tuple[str, ...]
    places: tuple[str, ...]
    phrases: tuple[tuple[str, ...], ...]


def _safe(text, dictionary):
    words = text.replace("-", " ")
    return (not profanity_rating(words, dictionary)
            and not any(dictionary.name_safety_index.find(sentence) for sentence in sentences(tokenize(words))))



def parse_name_catalog(raw, dictionary):
    if raw == {}:
        return None
    keys = {"version", "descriptors", "things", "nicknames", "places", "phrases"}
    if not isinstance(raw, dict) or set(raw) != keys or raw.get("version") != "aussiefy-names/v1":
        raise SchemaError("names.yaml: expected aussiefy-names/v1 and every catalogue field")

    def words(key):
        values = raw[key]
        if (not isinstance(values, list) or not values or any(not isinstance(v, str) or not SLUG.fullmatch(v)
                                                            for v in values) or len(set(values)) != len(values)):
            raise SchemaError(f"names.yaml: {key} must be a non-empty list of distinct lower-case name parts")
        return tuple(values)

    def entry_id(value):
        entry = dictionary.entries.get(value) if isinstance(value, str) else None
        if entry is None:
            raise SchemaError(f"names.yaml: unknown entry {value!r}")
        return value

    descriptors = raw["descriptors"]
    if (not isinstance(descriptors, list) or not descriptors or any(not isinstance(v, str) for v in descriptors)
            or len(set(descriptors)) != len(descriptors)):
        raise SchemaError("names.yaml: descriptors must be a non-empty list of distinct entry IDs")
    descriptors = tuple(entry_id(value) for value in descriptors)
    phrases = raw["phrases"]
    if not isinstance(phrases, list) or not phrases:
        raise SchemaError("names.yaml: phrases must contain reviewed lists of entry IDs")
    resolved = []
    for phrase in phrases:
        if not isinstance(phrase, list) or not phrase:
            raise SchemaError("names.yaml: each phrase needs entry IDs")
        ids = tuple(entry_id(value) for value in phrase)
        if ids in resolved:
            raise SchemaError("names.yaml: phrase is duplicated")
        resolved.append(ids)
    return NameCatalog(descriptors, words("things"), words("nicknames"), words("places"), tuple(resolved))


def _eligible(entry, dictionary):
    return (entry.status == "active" and not entry.held_back and entry.vulgarity == 0 and not entry.themes
            and not entry.insult and entry.reads_as == "australian" and not PLACEHOLDER_RE.search(entry.form)
            and bool(SLUG.fullmatch(_slug(entry.form))) and _safe(_slug(entry.form), dictionary))


def _eligible_catalog(catalog, dictionary):
    return NameCatalog(
        tuple(value for value in catalog.descriptors if dictionary.entries[value].frame in {"adj", "predicate_adj"}
              and _eligible(dictionary.entries[value], dictionary)),
        *(tuple(value for value in values if _safe(value, dictionary))
          for values in (catalog.things, catalog.nicknames, catalog.places)),
        tuple(ids for ids in catalog.phrases if all(_eligible(dictionary.entries[value], dictionary) for value in ids)))


def generate_name(dictionary, *, seed: int = 0, shape: str | None = None) -> dict:
    """Suggest a clean Aussie handle; the caller checks uniqueness and retries with another seed."""
    if type(seed) is not int:
        raise UserError("seed must be an integer")
    if shape is not None and (not isinstance(shape, str) or shape not in SHAPES):
        raise UserError(f"shape must be one of {', '.join(SHAPES)}")
    catalog = dictionary.name_catalog
    result = {"seed": seed, "shape": shape, "vulgarity": 0, "themes": [], "name": None,
              "outcome": "nothing_fits"}
    if catalog is None:
        return result
    catalog = _eligible_catalog(catalog, dictionary)
    selected = shape or SHAPES[int(roll(seed, "name-shape") * len(SHAPES))]
    sizes = {"descriptive": len(catalog.descriptors) * len(catalog.things),
             "place": len(catalog.nicknames) * len(catalog.places), "phrase": len(catalog.phrases)}
    size = sizes[selected]
    if not size:
        return {**result, "shape": selected}
    start = int(roll(seed, "name", selected) * size)
    for step in range(min(NAME_SEARCH_BUDGET, size)):
        index = (start + step) % size
        if selected == "descriptive":
            left, right = divmod(index, len(catalog.things))
            name = _slug(dictionary.entries[catalog.descriptors[left]].form) + "-" + catalog.things[right]
        elif selected == "place":
            left, right = divmod(index, len(catalog.places))
            name = catalog.nicknames[left] + "-from-" + catalog.places[right]
        else:
            name = "-".join(_slug(dictionary.entries[value].form) for value in catalog.phrases[index])
        if _safe(name, dictionary):
            return {**result, "shape": selected, "name": name, "outcome": "matched"}
    return {**result, "shape": selected}
