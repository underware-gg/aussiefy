"""Explicit dictionary discovery, independent of contextual replacement selection."""

from __future__ import annotations

from string import ascii_lowercase

from .engine import resolve_request
from .cards import CARD_VERSION

from . import discovery_outcomes as outcomes
from .cards import full_entry_card, shows_riffs
from .engine import Translator, default_translator
from .errors import UserError
from .evidence import register_rejection
from .genre import resolve_document
from .policy import dial_rejection, parse_embellishment, roll

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
INITIALS = tuple(ascii_lowercase + "#")


def _context(translator, level, vulgarity, embellishment, document_type, document_config):
    tr = translator or default_translator()
    genre = resolve_document(None, config=tr.dictionary.genres, document_type=document_type,
                             document_config=document_config)
    setting = genre.setting(parse_embellishment(embellishment) if embellishment is not None else None)
    eff = tr.effective(level=level, vulgarity=vulgarity, embellishment=embellishment,
                       document_type=document_type, document_config=document_config)
    return tr.dictionary, eff, setting, {**eff.envelope(), "card_version": CARD_VERSION, **genre.envelope(setting.step),
                                        'dictionary_id': tr.dictionary.identity}


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
    return full_entry_card(entry, eff.vulgarity, shows_riffs(setting), permitted_themes=eff.theme_policy,
                           registers=eff.registers, allow_misreadable=eff.allow_misreadable)


def _page(items, offset, limit):
    """A stable page of items: the page, and the next offset if any items remain."""
    if type(offset) is not int or offset < 0:
        raise UserError("offset must be a non-negative integer")
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
        raise UserError(f"limit must be an integer from 1 to {MAX_PAGE_SIZE}")
    page = items[offset:offset + limit]
    return page, offset + len(page) if offset + len(page) < len(items) else None


def _outcome(page, items):
    return outcomes.MATCHED if page else outcomes.PAGE_EXHAUSTED if items else outcomes.NOTHING_FITS


def list_entries(*, concept: str | None = None, theme: str | None = None, initial: str | None = None, offset: int = 0,
                 limit: int = DEFAULT_PAGE_SIZE, level: int | str = 5, vulgarity: int | str | None = None,
                 include_gated: bool = False, embellishment: int | str | None = None,
                 document_type: str = "general", document_config: dict | None = None, themes: dict[str, bool] | None = None, invention: bool | None = None,
                 translator: Translator | None = None) -> dict:
    """List a stable page; concept, theme and ID initial filters intersect. Counts respect all other filters."""
    if initial is not None and (not isinstance(initial, str) or initial not in INITIALS):
        raise UserError("initial must be a lowercase letter a-z or #")
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    concept, theme = _filters(d, concept, theme)
    entries = _entries(d, eff, concept, theme, include_gated)
    buckets = {letter: [] for letter in INITIALS}
    for entry in entries:
        buckets[entry.id[0] if entry.id[0] in ascii_lowercase else "#"].append(entry)
    initial_counts = {letter: len(items) for letter, items in buckets.items()}
    if initial is not None:
        entries = buckets[initial]
    page, next_offset = _page(entries, offset, limit)
    return {**envelope, "concept": concept, "theme": theme, "initial": initial, "initial_counts": initial_counts,
            "offset": offset, "limit": limit, "total": len(entries), "next_offset": next_offset, "outcome": _outcome(page, entries),
            "results": [_card(entry, eff, setting) for entry in page]}


def list_wordless_meanings(*, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE,
                           translator: Translator | None = None) -> dict:
    """List a stable page of the meanings the dictionary recognises but has no Aussie word for yet, each with
    its plain wording and reviewed example sentences. Guards and the holding concept never appear."""
    d = (translator or default_translator()).dictionary
    page, next_offset = _page(d.wordless_meanings, offset, limit)
    return {"dictionary_id": d.identity, "tuning": {"popularity": False, "preferences": 0}, "offset": offset, "limit": limit, "total": len(d.wordless_meanings), "next_offset": next_offset,
            "outcome": _outcome(page, d.wordless_meanings),
            "results": [{"concept": cid, "plain": d.concepts[cid].plain, "examples": list(d.concepts[cid].examples)}
                        for cid in page]}


def get_entry(entry_id: str, *, level: int | str = 5, vulgarity: int | str | None = None,
              include_gated: bool = False, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None, themes: dict[str, bool] | None = None, invention: bool | None = None,
              translator: Translator | None = None) -> dict:
    """Fetch one entry card under the caller's dials and discovery permissions."""
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    if not isinstance(entry_id, str) or not entry_id:
        raise UserError("entry_id must be a non-empty string")
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    entry = d.entries.get(entry_id)
    if entry is None or entry.status == "omit":   # an omitted entry is never shown, nor its flags
        return {**envelope, "entry_id": entry_id, "entry": None, "outcome": outcomes.NOT_IN_DICTIONARY}
    reason = dial_rejection(entry, eff, include_gated=include_gated) or register_rejection(entry, eff.registers)
    if reason:
        return {**envelope, "entry_id": entry_id, "entry": None, "outcome": outcomes.NOTHING_FITS, "reason": str(reason)}
    return {**envelope, "entry_id": entry_id, "entry": _card(entry, eff, setting), "outcome": outcomes.MATCHED}


def random_entry(*, seed: int = 0, concept: str | None = None, theme: str | None = None,
                 level: int | str = 5, vulgarity: int | str | None = None, include_gated: bool = False,
                 embellishment: int | str | None = None, document_type: str = "general",
                 document_config: dict | None = None, themes: dict[str, bool] | None = None, invention: bool | None = None, translator: Translator | None = None) -> dict:
    """Pick uniformly from all eligible entries, using a stable seeded roll rather than a page."""
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    if type(seed) is not int:
        raise UserError("seed must be an integer")
    d, eff, setting, envelope = _context(translator, level, vulgarity, embellishment, document_type, document_config)
    concept, theme = _filters(d, concept, theme)
    entries = _entries(d, eff, concept, theme, include_gated)
    chosen = entries[int(roll(seed, "dictionary-random", concept or "", theme or "") * len(entries))] if entries else None
    return {**envelope, "seed": seed, "concept": concept, "theme": theme,
            "outcome": outcomes.MATCHED if chosen else outcomes.NOTHING_FITS, "entry": _card(chosen, eff, setting) if chosen else None}


def suggest_name(*, seed: int = 0, shape: str | None = None, translator: Translator | None = None) -> dict:
    """Suggest a clean Aussie handle; the caller checks uniqueness and retries with a different seed."""
    from .names import generate_name
    dictionary = (translator or default_translator()).dictionary
    return {**generate_name(dictionary, seed=seed, shape=shape), 'dictionary_id': dictionary.identity, 'tuning': {'popularity': False, 'preferences': 0}}
