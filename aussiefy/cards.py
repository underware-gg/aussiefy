"""Entry cards: what a dictionary entry shows a reader, built once for every surface that shows one (lookup's
results and the entries a `changes` response sends). It reads only Entry fields, so it sits with the dictionary
model and both the engine and the toolkit can use it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema import Entry
from .terms import headword_key
from .evidence import metadata_dict
from .errors import SchemaError
from .themes import ThemePolicy

if TYPE_CHECKING:
    from .genre import Embellishment


def shows_riffs(setting: "Embellishment") -> bool:
    """Whether cards show an entry's riffs under an embellishment setting: it takes riffs, and entries' own."""
    return setting.entry_riffs and setting.takes("riff")


def riff_cards(e: Entry, cap: int, permitted_themes: ThemePolicy, *, registers, allow_misreadable=False) -> list[dict[str, Any]]:
    """An entry's riffs under the cap, as the toolkit shows them (best first)."""
    return [{"text": r.text, "tone": r.tone, **metadata(r, permitted_themes), **({"best": True} if i == 0 else {})}
            for i, r in enumerate(e.riffs_within(cap, permitted_themes, registers=registers, allow_misreadable=allow_misreadable))]


def short_card(e: Entry) -> dict[str, Any]:
    """Only what an agent checking a choice needs: form, gloss, frame, level and vulgarity (and gating, a dated
    register)."""
    card = {"id": e.id, "form": e.form, "headword_key": headword_key(e.form), "gloss": e.gloss, "frame": e.frame, "level": e.incoherence,
            "vulgarity": e.vulgarity}
    if e.semantic_effects:
        card["semantic_effects"] = list(e.semantic_effects)
    if e.register != "current":
        card["register"] = e.register
    if e.held_back:
        card["gated"] = list(e.held_back)
    return card


def _entry_fields(e: Entry) -> dict[str, Any]:
    """The full card: meaning, level and vulgarity, register and region, notes, sources, the riffs under the
    vulgarity cap (riffs: whether the embellishment takes the entry's riffs at all), and a gated entry's flags
    (shown only where the policy unlocked it)."""
    card = {"id": e.id, "form": e.form, "headword_key": headword_key(e.form), "gloss": e.gloss, "frame": e.frame, "concepts": list(e.concept),
            "level": e.incoherence, "vulgarity": e.vulgarity, "register": e.register}
    if e.semantic_effects:
        card["semantic_effects"] = list(e.semantic_effects)
    if e.other_sense:
        card['other_sense'] = e.other_sense
    if e.placement:
        card["placement"] = e.placement
    if e.variants:
        card["variants"] = list(e.variants)
    if e.region:
        card["region"] = list(e.region)
    if e.notes:
        card["notes"] = e.notes
    if e.replaces:
        card["replaces"] = [r.split("@")[0] for r in e.replaces]
    if e.held_back:
        card["gated"] = list(e.held_back)
    return card


CARD_VERSION = 4

def provenance(term):
    coiner = term.coined_by
    if term.evidence == 'bulldust':
        coiner = coiner or ('agent' if term.produced_by == 'agent' else None)
        if coiner is None:
            raise SchemaError('bulldust metadata has no attributable maker')
    return {'evidence': term.evidence, 'coined_by': coiner}


def metadata(term, permitted_themes: ThemePolicy, *, vulgarity=None):
    """Presentation attribution does not rewrite who authored or retrieved a stored record."""
    result = metadata_dict(term, derived=True)
    maker = provenance(term)['coined_by']
    if maker is not None:
        result['coined_by'] = maker
    tiers = permitted_themes.tag_tiers(term)
    result['themes'] = [{'name': name, 'tier': tier} for name, tier in tiers.items()]
    result['minimum_vulgarity'] = max([getattr(term, 'vulgarity', 0) if vulgarity is None else vulgarity,
                                     *tiers.values()])
    return result


def entry_card(e, cap=3, riffs=True, *, permitted_themes: ThemePolicy, registers, allow_misreadable=False):
    result = {**_entry_fields(e),
              **metadata(e, permitted_themes), 'type': e.type, 'status': e.status,
              'held_back': list(e.held_back)}
    if riffs:
        cards = riff_cards(e, cap, permitted_themes, registers=registers,
                           allow_misreadable=allow_misreadable)
        if cards:
            result['riffs'] = cards
    return result


full_entry_card = entry_card
