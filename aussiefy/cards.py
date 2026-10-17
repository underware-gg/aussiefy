"""Entry cards: what a dictionary entry shows a reader, built once for every surface that shows one (lookup's
results and the entries a `changes` response sends). It reads only Entry fields, so it sits with the dictionary
model and both the engine and the toolkit can use it."""

from __future__ import annotations

from typing import Any

from .schema import Entry


def riff_cards(e: Entry, cap: int) -> list[dict[str, str]]:
    """An entry's riffs under the cap, as the toolkit shows them (best first)."""
    return [{"text": r.text, "tone": r.tone, **({"best": True} if i == 0 else {})}
            for i, r in enumerate(e.riffs_within(cap))]


def short_card(e: Entry) -> dict[str, Any]:
    """Only what an agent checking a choice needs: form, gloss, frame, level and vulgarity (and gating, a dated
    register)."""
    card = {"id": e.id, "form": e.form, "gloss": e.gloss, "frame": e.frame, "level": e.incoherence,
            "vulgarity": e.vulgarity}
    if e.register != "current":
        card["register"] = e.register
    if e.status == "gate":
        card["gated"] = list(e.flags)
    return card


def entry_card(e: Entry, cap: int = 3) -> dict[str, Any]:
    """The full card: meaning, level and vulgarity, register and region, notes, sources and the riffs under the
    vulgarity cap."""
    card = {"id": e.id, "form": e.form, "gloss": e.gloss, "frame": e.frame, "concepts": list(e.concept),
            "level": e.incoherence, "vulgarity": e.vulgarity, "register": e.register}
    if e.placement:
        card["placement"] = e.placement
    if e.riffs_within(cap):
        card["riffs"] = riff_cards(e, cap)
    if e.variants:
        card["variants"] = list(e.variants)
    if e.region:
        card["region"] = list(e.region)
    if e.notes:
        card["notes"] = e.notes
    if e.sources:
        card["sources"] = list(e.sources)
    if e.replaces:
        card["replaces"] = [r.split("@")[0] for r in e.replaces]
    return card
