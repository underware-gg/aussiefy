"""The agent toolkit: lookup, lint, guide, plan, translate, verify.

Language models are very good at Aussie English when they have good source material and clear guidance. These six
operations give any agent both. They are plain Python and return JSON-ready dicts, and every surface is a thin
adapter over them: the Python API (`aussiefy.lookup` ...), the CLI (`aussiefy lookup|lint|guide|plan|verify|translate`),
the MCP server (`aussiefy-mcp`: aussie_lookup ...), yarn mode's tools (`aussiefy.yarn`) and the Claude Code skill.

- lookup(query):     plain-English meaning or slang term -> dictionary entries with gloss, level, vulgarity
- lint(text):        a draft's issues (flagged phrases, swearing over the cap, US spelling, US and British words),
                      warnings, suggestions
- guide(level):      the craft rules for a level, distilled from what reads well
- plan(text):        the rule engine's draft, its planned phrases, and the sentences it found too formal
- translate(text):   the deterministic rule-engine output
- verify(text):      a translation checked against its original: problems with severity, and metrics
"""
from __future__ import annotations

from typing import Any

from .context import RIFF_TONES_FOR
from . import translation
from .engine import Result, Translator, default_translator
from .genre import retelling_step
from .guide import guide, openings, style_guide_data
from .lint import fidelity, lint
from .lookup import lookup, riff_cards
from .verify import verify

__all__ = ["lookup", "lint", "guide", "plan", "translate", "verify", "fidelity", "openings"]


def translate(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
              variety: int = 0, registers: list[str] | None = None, regions: list[str] | None = None,
              unlock: list[str] | None = None, markdown: bool = False, markup: str = "text", english: str | None = None,
              embellishment: int | str | None = None, translator: Translator | None = None) -> dict[str, Any]:
    """The deterministic rule-engine translation: the same text, level and seed give the same output. variety N
    picks among the N best-fitting terms only (1 = always the best fit; 0 weighs every eligible term). registers
    (current, dated, archaic), regions (e.g. qld) and unlock (flags whose gated entries become eligible) narrow
    or widen what the level allows. markup (markdown, mdx, auto) translates only the prose and keeps code, tags,
    links, front matter and headings exactly as they were. english (us, uk, auto, none) is the English the
    text is in, for the US and UK words swapped at every level (faucet -> tap; British pants -> undies only for uk).
    embellishment (deadset, dinkum, troppo; None = the text's genre's own) is how much garnish the telling takes."""
    tr = translator or default_translator()
    r = translation.translate(text, level=level, seed=seed, vulgarity=vulgarity, variety=variety,
                         registers=registers, regions=regions, unlock=unlock, markdown=markdown, markup=markup, english=english,
                         embellishment=embellishment, translator=tr)
    if markdown:
        return r.to_dict()
    return {"text": r.text, "seed": seed, "variety": variety, **r.envelope(), **_embellished(r)}


def _embellished(r: Result) -> dict[str, Any]:
    """The embellishment a result took (the caller's, or its genre's) and the genre that set its form."""
    return {"genre": r.genre.name, "embellishment": r.embellishment.step,
            "embellishment_name": r.embellishment.name}


def plan(text: str, *, level: int | str = 5, seed: int = 0, vulgarity: int | str | None = None,
         variety: int = 0, registers: list[str] | None = None, regions: list[str] | None = None,
         unlock: list[str] | None = None, markup: str = "text", english: str | None = None,
         embellishment: int | str | None = None, translator: Translator | None = None) -> dict[str, Any]:
    """The engine's draft, what it planned, and which sentences it couldn't carry (best done by hand).
    markup and english as for translate. embellishment as for translate, except that None is a retelling's
    (genres.yaml's retelling, dinkum), not the genre's: the plan is for a writer; pass the genre's own setting
    to match translate's output."""
    tr = translator or default_translator()
    embellishment = retelling_step(embellishment, tr.dictionary.genres)

    r = translation.run(text, translator=tr, level=level, seed=seed, vulgarity=vulgarity,
                     variety=variety, registers=registers, regions=regions, unlock=unlock, markup=markup,
                     english=english, embellishment=embellishment)
    decided = r.decisions()
    for g in decided["garnish"]:
        g["sentence_text"] = r.sentence_text(g["sentence"])
    return {
        "draft": r.text,
        **r.envelope(),
        **_embellished(r),
        "seed": seed,
        # a riff is optional colour: the planned phrase is the term, not "bush, miles from the nearest servo"
        "planned": [{"original": r.source[slice(*x.out_span)], "span": list(x.out_span), "entry": x.chosen.entry.id,
                     "aussie": x.term, "gloss": x.chosen.entry.gloss or ""} for x in r.records if x.substituted],
        "garnish": decided["garnish"],
        # plain Australian for US and British words (faucet -> tap): not slang, so not planned phrases
        "dialect": decided["dialect"],
        # riffs only where the setting, narrowed by the form, takes them: none at deadset, and none below troppo
        # in news, docs or official prose, where a picture of a real thing is a claim
        "riffs": _riff_offers(r) if r.embellishment.takes("riff") else [],
        # a talker's openings only for a telling with some liberty in it (dinkum, troppo), not a deadset one
        "openings": openings(text, seed, r.mood) if r.embellishment.openings else [],
        "mood": r.mood,
        # the genre's form and the embellishment's liberty, for an agent writing its own version
        "guidance": {"genre": r.genre.policy.guidance, "embellishment": r.embellishment.guidance},
        # not where the formal words are the form's own terms of art (docs, official prose: genres.yaml)
        "difficult_sentences": [{"original": d.original, "draft": d.draft, "reason": d.reason} for d in r.difficult]
                               if r.genre.policy.formal_to_rework else [],
        "untouched_sentences": [r.sentence_text(i) for i in r.untouched],
        "note": style_guide_data().plan_note,
    }


def _riff_offers(r: Result) -> list[dict[str, Any]]:
    """The images the text's Aussie terms call up (wheelie bin -> bin chickens raiding it), for every term the
    engine used or could have used: the chosen one first, each term once."""
    offers: dict[str, dict[str, Any]] = {}
    for x in r.records:
        for c in sorted(x.eligible, key=lambda c: (c.entry.id != (x.chosen.entry.id if x.chosen else ""), c.entry.id)):
            cards = riff_cards(c.entry, r.vulgarity)
            if cards and c.entry.form not in offers:
                offers[c.entry.form] = {"term": c.entry.form, "for": x.text, "riffs": [
                    {**card, "suits_mood": card["tone"] in RIFF_TONES_FOR[r.mood]}
                    for card in cards]}
    return list(offers.values())
