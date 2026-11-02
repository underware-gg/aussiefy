"""The agent-neutral constructor operation; every adapter calls this boundary."""

from __future__ import annotations

from . import discovery_outcomes as outcomes

from .constructions import DEFAULT_LIMIT, generate
from .engine import Translator, default_translator
from .errors import UserError
from .genre import resolve_document
from .policy import parse_embellishment


def bulldust(concept: str | None = None, *, family: str | None = None, parts: dict[str, str] | None = None,
             level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None, limit: int = DEFAULT_LIMIT,
             registers: list[str] | None = None, regions: list[str] | None = None, unlock: list[str] | None = None,
             embellishment: int | str | None = None, document_type: str = "general", document_config: dict | None = None,
             translator: Translator | None = None) -> dict:
    """Construct seeded Australian-sounding idioms from reviewed families. Results are labelled bulldust.

    concept is a dictionary concept ID (for example HUNGRY); omit it to sample compatible families.
    family restricts the construction pattern. parts pins named slots to ingredient IDs from a previous
    result, such as {"stem": "bugger-sideways"}; unpinned slots vary. Each result retains its part evidence
    and canonical output spans. Collision checks cover this dictionary, not every expression ever spoken.
    """
    tr = translator or default_translator()
    if type(seed) is not int:
        raise UserError("seed must be an integer")
    dictionary, requested = tr.dictionary, parts or {}
    catalog = dictionary.construction_catalog
    if concept is not None:
        if not isinstance(concept, str) or concept.upper() not in dictionary.concepts:
            raise UserError("concept must be a dictionary concept ID, for example HUNGRY")
        concept = concept.upper()
    if family is not None and (not isinstance(family, str) or catalog is None
                               or family not in {pattern.id for pattern in catalog.families}):
        raise UserError(f"unknown construction family {family!r}")
    if parts is not None and (not isinstance(parts, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                                                for k, v in parts.items())):
        raise UserError("parts must map slot names to ingredient IDs")
    if catalog:
        families = [pattern for pattern in catalog.families if family is None or family == pattern.id]
        roles = {name for pattern in families for name, _ in pattern.slots}
        if set(requested) - roles:
            raise UserError("unknown construction slots: " + ", ".join(sorted(set(requested) - roles)))
        ids = {part.id for part in catalog.ingredients}
        if set(requested.values()) - ids:
            raise UserError("unknown ingredients: " + ", ".join(sorted(set(requested.values()) - ids)))
    maximum = catalog.max_results if catalog else 20
    if type(limit) is not int or not 1 <= limit <= maximum:
        raise UserError(f"limit must be an integer from 1 to {maximum}")
    genre = resolve_document(None, config=dictionary.genres, document_type=document_type, document_config=document_config)
    setting = genre.setting(parse_embellishment(embellishment) if embellishment is not None else None)
    eff = tr.effective(level=level, vulgarity=vulgarity, registers=registers, regions=regions, unlock=unlock,
                       embellishment=embellishment, document_type=document_type, document_config=document_config)
    generated = generate(dictionary, eff, setting, seed=seed, concept=concept, family=family, parts=requested, limit=limit)
    return {**eff.envelope(), **genre.envelope(setting.step), "seed": seed,
            "embellishment": setting.step, "embellishment_name": setting.name,
            "outcome": "constructed" if generated.candidates else "no-compatible-construction",
            "results": [candidate.to_dict() for candidate in generated.candidates], "attempts": generated.attempts,
            "rejected": [{"id": pid, "reason": reason} for pid, reason in generated.rejected]}


def variations(family: str, *, parts: dict[str, str], level: int | str = 5, seed: int = 0,
               vulgarity: int | str | None = None, registers: list[str] | None = None,
               regions: list[str] | None = None, unlock: list[str] | None = None,
               embellishment: int | str | None = None, document_type: str = "general",
               document_config: dict | None = None, translator: Translator | None = None) -> dict:
    """Vary one part of a construction while keeping every other part fixed.

    Pass the family and complete role-to-ingredient mapping from a constructed expression. Each option is
    a complete, validated construction, including its evidence and spans; it is not a word to splice blindly.
    """
    if not isinstance(family, str) or not family or not isinstance(parts, dict):
        raise UserError("variations needs a family ID and a complete parts mapping")
    tr = translator or default_translator()
    options = dict(level=level, seed=seed, vulgarity=vulgarity, registers=registers, regions=regions,
                   unlock=unlock, embellishment=embellishment, document_type=document_type,
                   document_config=document_config, translator=tr)
    base = bulldust(family=family, parts=parts, limit=1, **options)
    pattern = next(pattern for pattern in tr.dictionary.construction_catalog.families if pattern.id == family)
    if set(parts) != {role for role, _ in pattern.slots}:
        raise UserError("variations needs every slot in the construction family")
    ingredients = {part.id: part for part in tr.dictionary.construction_catalog.ingredients}
    if any(ingredients[parts[role]].kind != kind for role, kind in pattern.slots):
        raise UserError("parts contains an ingredient incompatible with its slot")
    groups = []
    for role, kind in pattern.slots:
        choices = []
        for ingredient in sorted(ingredients.values(), key=lambda part: part.id):
            if ingredient.kind != kind:
                continue
            result = bulldust(family=family, parts={**parts, role: ingredient.id}, limit=1, **options)
            if result["results"]:
                choices.append({"ingredient_id": ingredient.id, **result["results"][0]})
        groups.append({"role": role, "current": parts[role], "options": choices})
    return {key: value for key, value in base.items() if key not in {"results", "attempts", "rejected", "outcome"}} | {
        'dictionary_id': tr.dictionary.identity,
        "family": family, "parts": parts, "variations": groups,
        "outcome": outcomes.MATCHED if any(group["options"] for group in groups) else outcomes.NOTHING_FITS}
