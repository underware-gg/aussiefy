"""Entry cards: what a dictionary entry shows a reader, built once for every surface that shows one (lookup's
results and the entries a `changes` response sends). It reads only Entry fields, so it sits with the dictionary
model and both the engine and the toolkit can use it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema import Entry
from .evidence import metadata_dict
from .themes import ThemePermissions

if TYPE_CHECKING:
    from .genre import Embellishment


def shows_riffs(setting: "Embellishment") -> bool:
    """Whether cards show an entry's riffs under an embellishment setting: it takes riffs, and entries' own."""
    return setting.entry_riffs and setting.takes("riff")


def riff_cards(e: Entry, cap: int, permitted_themes: ThemePermissions) -> list[dict[str, Any]]:
    """An entry's riffs under the cap, as the toolkit shows them (best first)."""
    return [{"text": r.text, "tone": r.tone, **metadata_dict(r, derived=True), **({"best": True} if i == 0 else {})}
            for i, r in enumerate(e.riffs_within(cap, permitted_themes))]


def short_card(e: Entry) -> dict[str, Any]:
    """Only what an agent checking a choice needs: form, gloss, frame, level and vulgarity (and gating, a dated
    register)."""
    card = {"id": e.id, "form": e.form, "gloss": e.gloss, "frame": e.frame, "level": e.incoherence,
            "vulgarity": e.vulgarity}
    if e.semantic_effects:
        card["semantic_effects"] = list(e.semantic_effects)
    if e.register != "current":
        card["register"] = e.register
    if e.held_back:
        card["gated"] = list(e.held_back)
    return card


def entry_card(e: Entry, cap: int = 3, riffs: bool = True, *,
               permitted_themes: ThemePermissions) -> dict[str, Any]:
    """The full card: meaning, level and vulgarity, register and region, notes, sources, the riffs under the
    vulgarity cap (riffs: whether the embellishment takes the entry's riffs at all), and a gated entry's flags
    (shown only where the policy unlocked it)."""
    card = {"id": e.id, "form": e.form, "gloss": e.gloss, "frame": e.frame, "concepts": list(e.concept),
            "level": e.incoherence, "vulgarity": e.vulgarity, "register": e.register}
    if e.semantic_effects:
        card["semantic_effects"] = list(e.semantic_effects)
    if e.placement:
        card["placement"] = e.placement
    if riffs and (cards := riff_cards(e, cap, permitted_themes)):
        card["riffs"] = cards
    if e.variants:
        card["variants"] = list(e.variants)
    if e.region:
        card["region"] = list(e.region)
    if e.notes:
        card["notes"] = e.notes
    if e.sources:
        card["sources"] = [s.url for s in e.sources if s.url]
    if e.replaces:
        card["replaces"] = [r.split("@")[0] for r in e.replaces]
    if e.held_back:
        card["gated"] = list(e.held_back)
    return card
