"""Explicit dictionary discovery, independent of contextual replacement selection."""

from __future__ import annotations

from .cards import entry_card, shows_riffs
from .engine import Translator, default_translator
from .errors import UserError
from .evidence import metadata_dict, register_rejection
from .genre import resolve_document
from .policy import dial_rejection, parse_embellishment, roll

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _context(translator, level, vulgarity, embellishment, document_type, document_config):
    tr = translator or default_translator()
    genre = resolve_document(None, config=tr.dictionary.genres, document_type=document_type,
                             document_config=document_config)
    setting = genre.setting(parse_embellishment(embellishment) if embellishment is not None else None)
    eff = tr.effective(level=level, vulgarity=vulgarity, embellishment=embellishment,
                       document_type=document_type, document_config=document_config)
    return tr.dictionary, eff, setting, {**eff.envelope(), **genre.envelope(setting.step)}


def _filters(dictionary, concept, theme):
    if concept is not None:
        if not isinstance(concept, str) or concept.upper() not in dictionary.concepts:
            raise UserError("concept must be a dictionary concept ID")
        concept = concept.upper()
    if theme is not None and (not isinstance(theme, str) or theme not in dict(dictionary.theme_starts)):
        raise UserError("theme must be a registered dictionary theme")
    return concept, theme


def _entries(dictionary, eff, concept, theme, include_gated):
    return sorted((entry for entry in dictionary.entries.values()
                   if (concept is None or concept in entry.concept)
                   and (theme is None or theme in entry.themes)
                   and not dial_rejection(entry, eff, include_gated=include_gated)
                   and not register_rejection(entry, eff.registers)), key=lambda entry: entry.id)


def _card(entry, eff, setting):
    return {**entry_card(entry, eff.vulgarity, shows_riffs(setting), permitted_themes=eff.theme_policy,
                         registers=eff.registers),
            **metadata_dict(entry, derived=True), "type": entry.type, "status": entry.status,
            "held_back": list(entry.held_back)}


def list_entries(*, concept: str | None = None, theme: str | None = None, offset: int = 0,
                 limit: int = DEFAULT_PAGE_SIZE, level: int | str = 5, vulgarity: int | str | None = None,
                 include_gated: bool = False, embellishment: int | str | None = None,
                 document_type: str = "general", document_config: dict | None = None,
                 translator: Translator | None = None) -> dict:
    """List a stable page of entries; concept and theme filters intersect. Omitted entries never appear."""
    if type(offset) is not int or offset < 0:
        raise UserError("offset must be a non-negative integer")
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
        raise UserError(f"limit must be an integer from 1 to {MAX_PAGE_SIZE}")
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    concept, theme = _filters(d, concept, theme)
    entries = _entries(d, eff, concept, theme, include_gated)
    page = entries[offset:offset + limit]
    next_offset = offset + len(page) if offset + len(page) < len(entries) else None
    return {**envelope, "concept": concept, "theme": theme, "offset": offset, "limit": limit,
            "total": len(entries), "next_offset": next_offset,
            "outcome": "matched" if page else "page_exhausted" if entries else "nothing_fits",
            "results": [_card(entry, eff, setting) for entry in page]}


def get_entry(entry_id: str, *, level: int | str = 5, vulgarity: int | str | None = None,
              include_gated: bool = False, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
              translator: Translator | None = None) -> dict:
    """Fetch one entry card under the caller's dials and discovery permissions."""
    if not isinstance(entry_id, str) or not entry_id:
        raise UserError("entry_id must be a non-empty string")
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    entry = d.entries.get(entry_id)
    reason = (dial_rejection(entry, eff, include_gated=include_gated)
              or register_rejection(entry, eff.registers)) if entry is not None else None
    card = _card(entry, eff, setting) if entry is not None and reason is None else None
    return {**envelope, "entry_id": entry_id, "entry": card,
            "outcome": "matched" if card else "nothing_fits" if entry is not None else "not_in_dictionary",
            **({"reason": str(reason)} if reason else {})}


def random_entry(*, seed: int = 0, concept: str | None = None, theme: str | None = None,
                 level: int | str = 5, vulgarity: int | str | None = None, include_gated: bool = False,
                 embellishment: int | str | None = None, document_type: str = "general",
                 document_config: dict | None = None, translator: Translator | None = None) -> dict:
    """Pick uniformly from all eligible entries, using a stable seeded roll rather than a page."""
    if type(seed) is not int:
        raise UserError("seed must be an integer")
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    concept, theme = _filters(d, concept, theme)
    entries = _entries(d, eff, concept, theme, include_gated)
    chosen = entries[int(roll(seed, "dictionary-random", concept or "", theme or "") * len(entries))] if entries else None
    return {**envelope, "seed": seed, "concept": concept, "theme": theme,
            "outcome": "matched" if chosen else "nothing_fits", "entry": _card(chosen, eff, setting) if chosen else None}


def suggest_name(*, seed: int = 0, shape: str | None = None, translator: Translator | None = None) -> dict:
    """Suggest a clean Aussie handle; the caller checks uniqueness and retries with a different seed."""
    from .names import generate_name
    return generate_name((translator or default_translator()).dictionary, seed=seed, shape=shape)
