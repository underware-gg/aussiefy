"""Lookup: genuine Aussie options for a plain-English meaning, or what a slang term means.

Ranks dictionary entries by whole-word and phrase matches, character n-grams, and (when a model is available)
meaning similarity against each entry's gloss and its concepts' descriptions. Filtered to the level and cap, so
lookup never offers what lint would reject.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from .embed import NgramEmbedder
from .errors import UserError
from .engine import Translator, default_translator
from .model import Dictionary
from .morph import pluralise, verb_forms
from .select import dial_rejection
from .schema import PLACEHOLDER_RE, Entry
from .terms import fold, form_key, strip_markup



# a word with a negation in it ("not", "nobody", "harmless"): the meaning model puts a word and its opposite side by
# side ("probably" by "absolutely not"), so a model match must agree with the query on it
_NEGATED = re.compile(r"\b(?:no|not|never|nothing|none|nobody|nowhere|without|cannot|harmless|useless|hopeless"
                      r"|pointless|worthless|helpless|clueless|careless|thoughtless|aimless|powerless)\b|n't\b")


@lru_cache(maxsize=None)
def _inflected(form: str) -> frozenset[str]:
    """A form with one word inflected, as a query may give it: "coves" for cove, "playing up" for play up, "chucked
    a sickie" for chuck a sickie (morph's plurals and verb forms)."""
    words = form.split()
    out = set()
    for i, w in enumerate(words):
        if not w.isalpha():
            continue
        for other in {pluralise(w), *verb_forms(w)} - {w}:
            out.add(form_key(" ".join(words[:i] + [other] + words[i + 1:])))
    return frozenset(out)


def _in_order(words: list[str], form: list[str]) -> bool:
    it = iter(form)
    return all(w in it for w in words)


def meaning_texts(e: Entry, d: Dictionary) -> list[str]:
    """What a query is compared with to find an entry by meaning: its gloss and its concepts' descriptions.
    scripts/train_embedder.py scores the bundled model's lookup cut-off on these."""
    return [t for t in [e.gloss, *(d.concepts[c].description for c in e.concept if c in d.concepts)] if t]


def riff_cards(e: Entry, cap: int) -> list[dict[str, str]]:
    """An entry's riffs under the cap, as the toolkit shows them (best first)."""
    return [{"text": r.text, "tone": r.tone, **({"best": True} if i == 0 else {})}
            for i, r in enumerate(e.riffs_within(cap))]


def _short_card(e: Entry) -> dict[str, Any]:
    card = {"form": e.form, "gloss": e.gloss, "frame": e.frame, "level": e.incoherence, "vulgarity": e.vulgarity}
    if e.register != "current":
        card["register"] = e.register
    if e.status == "gate":
        card["gated"] = list(e.flags)
    return card


def _entry_card(e: Entry, cap: int = 3) -> dict[str, Any]:
    card = {"form": e.form, "gloss": e.gloss, "frame": e.frame, "concepts": list(e.concept),
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
    if e.replaces:
        card["replaces"] = [r.split("@")[0] for r in e.replaces]
    return card



# Ranking. A query that is itself slang beats one inside a phrase, which beats a match on meaning; meaning
# matches need MEANING_FLOOR (n-gram similarity of the query to a concept's triggers or the entry's gloss),
# and a model match enters at the floor plus how far it clears the model's threshold.
SCORE_TERM = 2.0              # the query is the term, or one of its words ("goog")
SCORE_INFLECTED = 1.6         # the query is the term inflected ("coves", "playing up"): below the term itself
SCORE_IN_PHRASE = 1.5         # the query is a whole word or stem of a longer form ("kip" in "have a kip")
SCORE_IN_ORDER = 1.3          # the query's words appear in order in a form ("chuck in" ~ "chuck it in")
MEANING_FLOOR = 0.62
DESCRIPTION_NAMES_IT = 0.9    # a one-word query found in a concept's description ("cry")
GLOSS_NAMES_IT = 0.75         # a one-word query found in the entry's gloss
ONE_WORD_FUZZ = 0.85          # one word is where character n-grams mislead most (lonely ~ lovely, miser)
GLOSS_FUZZ = (0.7, 0.9)       # n-gram similarity to a gloss, discounted (one word, a phrase)


def lookup(query: str, *, level: int | str = 5, vulgarity: int | str | None = None, limit: int = 8,
           include_gated: bool = False, short: bool = False, translator: Translator | None = None) -> dict[str, Any]:
    """Find Aussie options for a plain-English meaning ("very busy"), or explain a slang term ("goog").
    short: each result as only its form, gloss, frame, level and vulgarity (and gating, a dated register), for
    an agent checking a choice.

    Uses the same vulgarity as lint, so lookup never offers what lint would reject.
    `include_gated` also returns entries held back for doubtful origin or meaning (marked as such).
    """
    if limit < 1:
        raise UserError(f"limit must be 1 or more, not {limit}")
    tr = translator or default_translator()
    d: Dictionary = tr.dictionary
    eff = tr.effective(level=level, vulgarity=vulgarity, unlock=["all"] if include_gated else None)
    cap = eff.vulgarity
    sim = NgramEmbedder()
    model = tr.lookup_embedder   # a meaning model (the bundled one, unless set otherwise); None: n-grams only
    q = query.lower().strip()
    # one word ("lonely") is where character n-grams mislead most (lovely, miser), so for a single word trust
    # whole-word hits and discount fuzzy ones
    one_word = " " not in q
    negated = bool(_NEGATED.search(q))   # a model match must agree with the query on negation
    fuzz = ONE_WORD_FUZZ if one_word else 1.0
    concept_score: dict[str, float] = {}
    for p in d.patterns:
        text = strip_markup(p.text)
        score = 1.0 if text == q else sim.similarity(q, text) * fuzz
        for c in p.concepts:
            concept_score[c] = max(concept_score.get(c, 0.0), score)
    if one_word:   # "cry": the concept's own description names it even where no trigger does
        variants = {q, re.sub(r"ying$", "y", q), re.sub(r"ing$", "", q), re.sub(r"ing$", "e", q),
                    re.sub(r"ies$", "y", q), re.sub(r"s$", "", q)}
        for cid, concept in d.concepts.items():
            if variants & set(re.findall(r"[a-z']+", (concept.description or "").lower())):
                concept_score[cid] = max(concept_score.get(cid, 0.0), DESCRIPTION_NAMES_IT)
    scored: list[tuple[float, Entry, str]] = []
    qn = form_key(q)
    for e in d.idioms + d.garnish:
        if dial_rejection(e, eff):
            continue
        forms = [form_key(f) for f in e.all_forms]
        if qn in forms or any(qn in f.split() for f in forms):
            scored.append((SCORE_TERM, e, "slang term"))
            continue
        if any(qn in _inflected(fold(PLACEHOLDER_RE.sub("", f)).strip()) for f in e.all_forms):
            scored.append((SCORE_INFLECTED, e, "the slang term, inflected"))
            continue
        stems = set()
        raw = [fold(PLACEHOLDER_RE.sub("", f)) for f in e.all_forms]
        for w in (w for f in raw for w in f.split() if len(w) > 3):
            st = w.rstrip("'").removesuffix("in") if w.endswith(("in'", "ing")) else w
            st = st.removesuffix("g") if w.endswith("ing") else st
            stems |= {st, st[:-1] if len(st) > 2 and st[-1] == st[-2] else st}   # kippin' -> kipp -> kip
        if len(qn) >= 3 and (any(f" {qn} " in f" {f} " for f in forms) or (" " not in qn and qn in stems)):
            scored.append((SCORE_IN_PHRASE, e, "part of a phrase"))
            continue
        if " " in qn and any(_in_order(qn.split(), f.split()) for f in forms):
            scored.append((SCORE_IN_ORDER, e, "part of a phrase"))   # "chuck in" ~ "chuck it in", "give the flick"
            continue
        best = max((concept_score.get(c, 0.0) for c in e.concept), default=0.0)
        if e.gloss:
            gloss = e.gloss.lower()
            hit = one_word and q in re.findall(r"[a-z']+", gloss)
            best = max(best, GLOSS_NAMES_IT if hit else sim.similarity(q, gloss) * GLOSS_FUZZ[not one_word])
        if model is not None:
            # the local model: meaning where n-grams only see spelling. Scored for every entry, not just the
            # ones n-grams missed: otherwise a weak n-gram match (knackered for "very tired", 0.65) keeps its weak
            # score while a model-only one (maggoted, from "Very drunk.") gets the model's, and outranks it
            texts = [e.gloss] if e.gloss else []
            texts += [d.concepts[c].description for c in e.concept if c in d.concepts]
            m = max((model.similarity(q, t) for t in texts if t and bool(_NEGATED.search(t.lower())) == negated),
                    default=0.0)
            if m >= model.lookup_threshold and MEANING_FLOOR + (m - model.lookup_threshold) > best:
                scored.append((round(MEANING_FLOOR + (m - model.lookup_threshold), 3), e, "meaning (local model)"))
                continue
        if best >= MEANING_FLOOR:
            scored.append((best, e, "meaning"))
    scored.sort(key=lambda t: (-t[0], t[1].incoherence, t[1].id))
    if short:
        results = [_short_card(e) for _, e, _ in scored[:limit]]
    else:
        results = [{**_entry_card(e, cap), "match": how, "score": round(s, 2),
                    **({"gated": list(e.flags)} if e.status == "gate" else {})} for s, e, how in scored[:limit]]
    out = {"query": query, **eff.envelope(),
           "results": results}
    if not results:
        out["note"] = ("No entry. If you're sure Australians say it, it's probably fine but unvetted; "
                       "otherwise rephrase. Consider proposing it for the dictionary.")
    return out
