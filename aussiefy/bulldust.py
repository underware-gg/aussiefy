"""The agent-neutral constructor operation; every adapter calls this boundary."""

from __future__ import annotations

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
