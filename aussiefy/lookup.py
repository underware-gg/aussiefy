"""Lookup: genuine Aussie options for a plain-English meaning, or what a slang term means.

Ranks dictionary entries by whole-word and phrase matches, character n-grams, and (when a model is available)
meaning similarity against each entry's gloss and its concepts' descriptions. All cards respect the requested
level and cap; direct term discovery remains broader than contextual meaning inference.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from .align import content_words
from .text import Token, tokenize
from . import pos
from .context import TIME_ADVERBS, positive_context
from .detect import DETERMINERS, NOUN_PREPOSITIONS, Detection
from .embed import NgramEmbedder
from .errors import UserError
from .engine import Translator, default_translator
from .model import Dictionary
from .morph import pluralise, verb_forms
from .select import mapping_effects, dial_rejection, semantic_rejection
from .schema import PLACEHOLDER_RE, Entry
from .cards import entry_card, short_card, shows_riffs
from .terms import fold, form_key, strip_markup
from .genre import resolve_document
from .imagery import lookup_images
from .policy import envelope, parse_embellishment



# a word with a negation in it ("not", "nobody", "harmless"): the meaning model puts a word and its opposite side by
# side ("probably" by "absolutely not"), so a model match must agree with the query on it
_NEGATED = re.compile(r"\b(?:no|not|never|nothing|none|nobody|nowhere|without|cannot|harmless|useless|hopeless"
                      r"|pointless|worthless|helpless|clueless|careless|thoughtless|aimless|powerless)\b|n't\b")


@lru_cache(maxsize=None)
def _inflected(form: str, frame: str) -> frozenset[str]:
    """A form with one word inflected, as a query may give it: "coves" for cove, "playing up" for play up, "chucked
    a sickie" for chuck a sickie (morph's plurals and verb forms)."""
    words = form.split()
    out = set()
    positions = [0] if frame == "vp" else [len(words) - 1] if frame == "np" else []
    for i in positions:
        if i < 0 or not words[i].isalpha():
            continue
        variants = {pluralise(words[i])} if frame == "np" else set(verb_forms(words[i]))
        for other in variants - {words[i]}:
            out.add(form_key(" ".join(words[:i] + [other] + words[i + 1:])))
    return frozenset(out)


def _in_order(words: list[str], form: list[str]) -> bool:
    it = iter(form)
    return all(w in it for w in words)


def meaning_texts(e: Entry, d: Dictionary, *, concepts: set[str] | None = None) -> list[str]:
    """What a query is compared with to find an entry by meaning: its gloss and its concepts' descriptions.
    scripts/train_embedder.py scores the bundled model's lookup cut-off on these."""
    paths = set(e.concept) if concepts is None else concepts
    gloss = e.gloss if paths == set(e.concept) else ''
    return [t for t in [gloss, *(d.concepts[c].description for c in e.concept if c in paths and c in d.concepts)] if t]


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


def _scoped_query(tokens: list[Token], readings: list[Detection], tags: list[str]) -> set[str] | None:
    """A recognised head can bound a query; an incidental argument or modifier cannot exhaust it."""
    if not tokens:
        return None
    heads = [r for r in readings if r.frame != 'adv' or r.end == len(tokens)]
    covered = {i for r in heads for i in range(r.start - len(r.degree_qualifier), r.end)}
    for head in heads:
        start = head.start - len(head.degree_qualifier)
        captured = {t.i for t in head.captures.values()}
        if head.subject_noun is not None:
            captured.add(head.subject_noun.i)
        if any(t.norm not in DETERMINERS and t.i not in captured
               and i not in covered for i, t in enumerate(tokens[:start])):
            continue
        # All coordinated heads must be known. A preposition/infinitive may introduce a head's
        # dependent complement; it cannot swallow another independent finite clause or conjunction.
        tail = list(range(head.end, len(tokens)))
        unexplained = [i for i in tail if i not in covered and tokens[i].is_word
                       and tags[i] != 'CC' and tokens[i].norm not in TIME_ADVERBS]
        if not unexplained:
            return {cid for r in heads for cid in r.concepts}
        first = unexplained[0]
        if first == head.end and (tags[first] == 'TO' or tokens[first].norm in NOUN_PREPOSITIONS) and not any(
                tags[i] in {'CC', 'VBD', 'VBP', 'VBZ'} for i in tail) and not any(
                    r is not head and not set(r.concepts) <= set(head.concepts) for r in heads):
            return set(head.concepts)
    return None


def lookup(query: str, *, level: int | str = 5, vulgarity: int | str | None = None, limit: int = 8,
           include_gated: bool = False, short: bool = False, embellishment: int | str | None = None,
           document_type: str = "general", document_config: dict | None = None,
           translator: Translator | None = None) -> dict[str, Any]:
    """Find Aussie options for a plain-English meaning ("very busy"), or explain a slang term ("goog").
    short: each result as only its form, gloss, frame, level and vulgarity (and gating, a dated register), for
    an agent checking a choice.

    Applies the requested level and vulgarity to every route. Explicit term searches explain vocabulary;
    they do not certify it as a replacement for the source context.
    `include_gated` also returns entries held back for doubtful origin or meaning (marked as such).
    """
    if limit < 1:
        raise UserError(f"limit must be 1 or more, not {limit}")
    tr = translator or default_translator()
    d: Dictionary = tr.dictionary
    genre = resolve_document(query, config=d.genres, document_type=document_type, document_config=document_config)
    setting = genre.setting(parse_embellishment(embellishment) if embellishment is not None else None)
    eff = tr.effective(level=level, vulgarity=vulgarity, unlock=["all"] if include_gated else None,
                       embellishment=embellishment, document_type=document_type, document_config=document_config)
    cap = eff.vulgarity
    sim = NgramEmbedder()
    model = tr.lookup_embedder   # a meaning model (the bundled one, unless set otherwise); None: n-grams only
    q = query.lower().strip()
    # one word ("lonely") is where character n-grams mislead most (lovely, miser), so for a single word trust
    # whole-word hits and discount fuzzy ones
    one_word = " " not in q
    negated = bool(_NEGATED.search(q))   # a model match must agree with the query on negation
    fuzz = ONE_WORD_FUZZ if one_word else 1.0
    tokens = tokenize(query.strip())
    while tokens and tokens[0].is_punct:
        tokens.pop(0)
    while tokens and tokens[-1].is_punct:
        tokens.pop()
    from .detect import detect, resolve_overlaps
    tags = pos.tag([t.text for t in tokens]) if tokens else []
    readings = resolve_overlaps(detect(tokens, d.index, concepts=d.concepts, adjective_nouns=d.adjective_nouns,
                                        degree_index=d.degree_index, tags=tags, fragment=True))
    readings = [r for r in readings if positive_context(tokens, r.start, r.start)]
    exhaustive = _scoped_query(tokens, readings, tags)
    established = {cid for det in readings for cid in det.concepts
                   if det.frame != 'adv' or det.end == len(tokens)}
    from .detect import applicable_concepts
    from .degree import realised_degree
    raw_matches = d.index.find(tokens)
    blocked = set()
    for matched in raw_matches:
        possible = applicable_concepts(matched.pattern.concepts, d.concepts, tokens, matched.end, noun_use=None)
        blocked.update(set(matched.pattern.concepts) - set(possible))
        if not positive_context(tokens, matched.start, matched.start):
            blocked.update(matched.pattern.concepts)

    def degree_fits(entry, concepts):
        paths = [(cid, det) for det in readings for cid in concepts.intersection(det.degree_concepts)]
        if not paths:
            return True
        for cid, det in paths:
            if cid in det.degree_conflicts:
                continue
            source = realised_degree(det.semantic_degree.get(cid), det.degree_qualifier)
            if source == 'unmarked' or source in {'mild', 'strong'} and source == entry.semantic_degree.get(cid):
                return True
        return False
    def effects_for(entry):
        connected = [det for det in readings if set(entry.concept).intersection(det.concepts)]
        return tuple(sorted(set(entry.semantic_effects).union(*(mapping_effects(entry, det,
            narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation)
            for det in connected))))

    concept_score: dict[str, float] = {}
    for p in d.patterns:
        text = strip_markup(p.text)
        score = 1.0 if text == q else sim.similarity(q, text) * fuzz
        for c in p.concepts:
            concept_score[c] = max(concept_score.get(c, 0.0), score)
    for det in readings:
        if exhaustive is not None or det.frame not in {'np', 'adv'}:
            for cid in set(det.concepts).intersection(established):
                concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    for matched in raw_matches:
        if matched.start == 0 and matched.end == len(tokens):
            for cid in matched.pattern.concepts:
                concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    if one_word:   # "cry": the concept's own description names it even where no trigger does
        variants = {q, re.sub(r"ying$", "y", q), re.sub(r"ing$", "", q), re.sub(r"ing$", "e", q),
                    re.sub(r"ies$", "y", q), re.sub(r"s$", "", q)}
        for cid, concept in d.concepts.items():
            if variants & set(re.findall(r"[a-z']+", (concept.description or "").lower())):
                concept_score[cid] = max(concept_score.get(cid, 0.0), DESCRIPTION_NAMES_IT)
    scored: list[tuple[float, Entry, str]] = []
    qn = form_key(q)
    slotted = {m.pattern.entry_id for m in d.form_index.find(tokens)
               if m.start == 0 and m.end == len(tokens) and m.pattern.slots}
    parsed_concepts = {cid for eid in slotted for cid in d.entries[eid].concept}
    negative_anchors = {w[:-4] if w.endswith("less") else w for w in content_words(q)}
    for e in d.idioms + d.garnish:
        if dial_rejection(e, eff):
            continue
        forms = [form_key(f) for f in e.all_forms]
        if e.id in slotted or qn in forms or any(qn in f.split() for f in forms):
            scored.append((SCORE_TERM, e, "slang term"))
            continue
        if any(qn in _inflected(fold(PLACEHOLDER_RE.sub("", f)).strip(), e.frame) for f in e.all_forms):
            scored.append((SCORE_INFLECTED, e, "the slang term, inflected"))
            continue
        stems = set()
        raw = [fold(PLACEHOLDER_RE.sub("", f)) for f in e.all_forms]
        for w in (w for f in raw for w in f.split() if len(w) > 3):
            st = w.rstrip("'").removesuffix("g").removesuffix("in") if w.endswith(("in'", "ing")) else w
            stems |= {st, st[:-1] if len(st) > 2 and st[-1] == st[-2] else st}   # kippin' -> kipp -> kip
        if len(qn) >= 3 and (any(f" {qn} " in f" {f} " for f in forms) or (" " not in qn and qn in stems)):
            scored.append((SCORE_IN_PHRASE, e, "part of a phrase"))
            continue
        if " " in qn and any(_in_order(qn.split(), f.split()) for f in forms):
            scored.append((SCORE_IN_ORDER, e, "part of a phrase"))   # "chuck in" ~ "chuck it in", "give the flick"
            continue
        if semantic_rejection(e, narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation, effects=effects_for(e)):
            continue
        paths = set(e.concept)
        if exhaustive is not None:
            paths.intersection_update(exhaustive)
        if paths.intersection(blocked):
            paths.intersection_update(established)
        if not paths or not degree_fits(e, paths):
            continue
        if parsed_concepts and not parsed_concepts.intersection(e.concept):
            continue
        best = max((concept_score.get(c, 0.0) for c in paths), default=0.0)
        if e.gloss and paths == set(e.concept):
            gloss = e.gloss.lower()
            hit = one_word and q in re.findall(r"[a-z']+", gloss)
            best = max(best, GLOSS_NAMES_IT if hit else sim.similarity(q, gloss) * GLOSS_FUZZ[not one_word])
        if model is not None:
            # the local model: meaning where n-grams only see spelling. Scored for every entry, not just the
            # ones n-grams missed: otherwise a weak n-gram match (knackered for "very tired", 0.65) keeps its weak
            # score while a model-only one (maggoted, from "Very drunk.") gets the model's, and outranks it
            texts = meaning_texts(e, d, concepts=paths)
            m = max((model.similarity(q, t) for t in texts if t and bool(_NEGATED.search(t.lower())) == negated
                     and (not negated or negative_anchors & {
                         w[:-4] if w.endswith("less") else w for w in content_words(t)})),
                    default=0.0)
            if m >= model.lookup_threshold and MEANING_FLOOR + (m - model.lookup_threshold) > best:
                scored.append((round(MEANING_FLOOR + (m - model.lookup_threshold), 3), e, "meaning (local model)"))
                continue
        if best >= MEANING_FLOOR:
            scored.append((best, e, "meaning"))
    scored.sort(key=lambda t: (-t[0], t[1].incoherence, t[1].id))
    if short:
        results = [short_card(e) for _, e, _ in scored[:limit]]
    else:
        riffs = shows_riffs(setting)
        results = [{**entry_card(e, cap, riffs), "match": how, "score": round(s, 2)} for s, e, how in scored[:limit]]
    for card in results:
        entry = d.entries[card["id"]]
        effects = effects_for(entry)
        if effects:
            card["semantic_effects"] = list(effects)
        reason = semantic_rejection(entry, narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation, effects=effects)
        if reason:
            card.update(effects_permitted=False, effect_rejection=reason)
    # a lookup reads no profile settings, so its envelope is the dials alone (no profile_config)
    out = {"query": query, **envelope(eff.level, eff.vulgarity, eff.warnings), "results": results}
    images = lookup_images(d, query, eff.level, cap, setting, limit)
    if images:
        out["imagery"] = images
    if not results and not images:
        out["note"] = ("The dictionary recognises this meaning but has no compatible suggestion at these settings. "
                       "Try another wording or look up a specific term." if exhaustive is not None else
                       "No entry. If you're sure Australians say it, it's probably fine but unvetted; "
                       "otherwise rephrase. Consider proposing it for the dictionary.")
    return out
