"""Lookup: genuine Aussie options for a plain-English meaning, or what a slang term means.

Ranks dictionary entries by whole-word and phrase matches, character n-grams, and (when a model is available)
meaning similarity against each entry's gloss and its concepts' descriptions. All cards respect the requested
level and cap; direct term discovery remains broader than contextual meaning inference.
"""

from __future__ import annotations

from .engine import resolve_request

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .align import content_words
from .text import Token, tokenize
from . import pos
from . import discovery_outcomes as outcomes
from .context import NP_DETERMINER_TAGS, TIME_ADVERBS, positive_context
from .detect import DETERMINERS, NOUN_PREPOSITIONS, Detection, check_frame
from .embed import NgramEmbedder, NgramIndex
from .errors import UserError
from .engine import Translator
from .model import Dictionary
from .morph import pluralise, verb_forms
from .select import mapping_effects, dial_rejection, semantic_rejection
from .schema import PLACEHOLDER_RE, HOLDING_CONCEPT, Entry
from .nominal_modifiers import cardinal_at
from .cards import CARD_VERSION
from .cards import full_entry_card, short_card, shows_riffs
from .evidence import register_rejection
from .terms import fold, form_key, strip_markup
from .genre import Embellishment, resolve_document
from .imagery import lookup_images
from .policy import Effective, parse_embellishment



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
_SPELLING_CORPORA = 4
_TERM_FORM_SETS = 4096
GLOSS_FUZZ = (0.7, 0.9)       # n-gram similarity to a gloss, discounted (one word, a phrase)


def _explained(reading: Detection) -> tuple[int, int]:
    """The tokens a reading explains: its span, degree qualifier and assertion words ("fantastic [terrors]"
    is one reading), but not a context object it reads, whose words keep their own senses ("believe [my mate]")."""
    start = min(reading.start - len(reading.degree_qualifier), reading.evidence_extent[0])
    end = reading.evidence_extent[1] if reading.object_start is None else max(reading.end, reading.object_start)
    return start, end


def _scoped_query(tokens: list[Token], readings: list[Detection], tags: list[str]) -> set[str] | None:
    """A recognised head can bound a query; an incidental argument or modifier cannot exhaust it."""
    if not tokens:
        return None
    heads = [r for r in readings if r.frame != 'adv' or r.end == len(tokens)]
    covered = {i for r in heads for i in range(*_explained(r))}
    for head in heads:
        start = head.start - len(head.degree_qualifier)
        captured = {t.i for t in head.captures.values()}
        if head.subject_noun is not None:
            captured.add(head.subject_noun.i)
        if any(t.norm not in DETERMINERS and t.i not in captured
               and not (head.frame == 'np' and (tags[i] in NP_DETERMINER_TAGS or cardinal_at(tokens, i)))
               and i not in covered for i, t in enumerate(tokens[:start])):
            continue
        # All coordinated heads must be known. A preposition/infinitive may introduce a head's
        # dependent complement; it cannot swallow another independent finite clause or conjunction.
        tail = list(range(head.end, len(tokens)))
        unexplained = [i for i in tail if i not in covered and tokens[i].is_word
                       and tags[i] != 'CC' and tokens[i].norm not in TIME_ADVERBS]
        if not unexplained:
            return {cid for r in heads for cid in r.concepts}
        first, lead = unexplained[0], head.end
        # "hard [to] finish": the complement opens right after the span, its marker perhaps the reading's context
        if first in {lead, head.evidence_extent[1]} and lead < len(tokens) and (
                tags[lead] == 'TO' or tokens[lead].norm in NOUN_PREPOSITIONS) and not any(
                tags[i] in {'CC', 'VBD', 'VBP', 'VBZ'} for i in tail) and not any(
                    r is not head and not set(r.concepts) <= set(head.concepts) for r in heads):
            return set(head.concepts)
    return None


@dataclass(frozen=True)
class _TermMatch:
    score: float
    kind: str
    description: str
    whole: bool = False


@lru_cache(maxsize=_TERM_FORM_SETS)
def _term_forms(all_forms: tuple[str, ...], frame: str):
    """Query-independent form facts, shared by ordinary and batched lookup; bounded across dictionaries."""
    forms = tuple(form_key(form) for form in all_forms)
    raw = tuple(fold(PLACEHOLDER_RE.sub('', form)) for form in all_forms)
    inflections = frozenset().union(*(_inflected(form.strip(), frame) for form in raw))
    stems = set()
    for word in (word for form in raw for word in form.split() if len(word) > 3):
        stem = word.rstrip("'").removesuffix("g").removesuffix("in") if word.endswith(("in'", "ing")) else word
        stems |= {stem, stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else stem}
    return forms, inflections, frozenset(stems)


def _term_match(e: Entry, qn: str, slotted: set[str]) -> _TermMatch | None:
    forms, inflections, stems = _term_forms(tuple(e.all_forms), e.frame)
    exact = e.id in slotted or qn in forms
    inflected = not exact and qn in inflections
    if exact or any(qn in form.split() for form in forms):
        return _TermMatch(SCORE_TERM, 'term', "slang term", whole=exact or inflected)
    if inflected:
        return _TermMatch(SCORE_INFLECTED, 'term', "the slang term, inflected", whole=True)
    if len(qn) >= 3 and (any(f" {qn} " in f" {f} " for f in forms) or (" " not in qn and qn in stems)):
        return _TermMatch(SCORE_IN_PHRASE, 'phrase', "part of a phrase")
    if " " in qn and any(_in_order(qn.split(), f.split()) for f in forms):
        return _TermMatch(SCORE_IN_ORDER, 'phrase', "part of a phrase")   # "chuck in" ~ "chuck it in", "give the flick"
    return None


def _object_terms(matches, readings, tokens, tags, dictionary):
    """An unclaimed context object can itself contain Aussie wording worth explaining.

    This is direct dictionary discovery inside that object, not an automatic sense assertion for it.
    """
    objects = [(r.object_start, r.evidence_extent[1]) for r in readings if r.object_start is not None]
    return {m.pattern.entry_id for m in matches
            if any(start <= m.start and m.end <= end for start, end in objects)
            and positive_context(tokens, m.start, m.start)
            and check_frame(m, tokens, dictionary.adjective_nouns, tags, fragment=True) is not None}


@dataclass(frozen=True)
class _LookupCards:
    dictionary: Dictionary
    effective: Effective
    setting: Embellishment
    domains: tuple[str, ...]
    short: bool
    limit: int

    def entry(self, entry: Entry):
        return short_card(entry) if self.short else full_entry_card(entry, self.effective.vulgarity,
            shows_riffs(self.setting), permitted_themes=self.effective.theme_policy,
            registers=self.effective.registers, allow_misreadable=self.effective.allow_misreadable)

    def near(self, concept):
        out = []
        for relation in self.dictionary.concepts[concept].near:
            words = []
            for entry in self.dictionary.idioms_for((relation.concept,)):
                if (dial_rejection(entry, self.effective) or register_rejection(entry, self.effective.registers)
                        or semantic_rejection(entry, narrator_opinion=self.setting.narrator_opinion,
                                              quantity_approximation=self.setting.quantity_approximation)):
                    continue
                words.append(full_entry_card(entry, self.effective.vulgarity, shows_riffs(self.setting),
                    permitted_themes=self.effective.theme_policy, registers=self.effective.registers,
                    allow_misreadable=self.effective.allow_misreadable))
            out.append({'kind': 'near', 'concept': relation.concept,
                        'plain': self.dictionary.concepts[relation.concept].plain,
                        'differs': relation.differs, 'setting': relation.setting, 'words': words[:self.limit]})
        return out

    def ruled_out(self, evidence, original):
        out = []
        for reading in evidence.meanings:
            words = []
            for eid in reading.entries:
                entry = self.dictionary.entries[eid]
                if (dial_rejection(entry, self.effective) or register_rejection(entry, self.effective.registers)
                        or semantic_rejection(entry, narrator_opinion=self.setting.narrator_opinion,
                                              quantity_approximation=self.setting.quantity_approximation)):
                    continue
                words.append(self.entry(entry))
                if len(words) == self.limit:
                    break
            out.append({'kind': 'meaning', 'concept': reading.concept, 'plain': self.dictionary.concepts[reading.concept].plain, 'words': words})
        if evidence.fence.applies(None, self.domains):
            source = tuple(token.norm for token in tokenize(original))
            for swap in evidence.dialect:
                part = tuple(token.norm for token in tokenize(swap.before))
                if any(source[i:i + len(part)] == part for i in range(len(source) - len(part) + 1)):
                    out.append({'kind': 'dialect', 'english': swap.english, 'original': swap.before, 'output': swap.after})
        return out

    def protection(self, query, tokens, start, end, reason, evidence=None):
        offset = len(query) - len(query.lstrip())
        span = [tokens[start].start + offset, tokens[end - 1].end + offset]
        original = query[slice(*span)]
        return {'span': span, 'original': original, 'reason': reason,
                'ruled_out': self.ruled_out(evidence.for_span(query, span), original) if evidence is not None else []}


def _protected_query(query, tokens, readings, exhaustive, cards):
    """Explain a wholly protected query; incidental fences cannot decide its whole outcome."""
    if exhaustive is None or exhaustive - {HOLDING_CONCEPT}:
        return []
    out = []
    for reading in readings:
        fence = reading.source_pattern.fence if reading.source_pattern else None
        if reading.concepts == (HOLDING_CONCEPT,):
            reason = 'The meaning is unclear here, so try adding words around the phrase.'
            evidence = None
        elif fence is not None and not reading.concepts:
            reason = fence.reason
            evidence = cards.dictionary.fence_readings[fence]
        else:
            continue
        out.append(cards.protection(query, tokens, reading.start, reading.end, reason, evidence))
    return out


def _dialect_protected_query(query, tokens, cards):
    out = []
    for match in cards.dictionary.fence_index.find(tokens):
        fence = match.pattern.fence
        if (fence.meanings or not fence.applies(None, cards.domains)
                or match.end != len(tokens) or any(t.norm not in DETERMINERS for t in tokens[:match.start])):
            continue
        evidence = cards.dictionary.fence_readings[fence]
        out.append(cards.protection(query, tokens, match.start, match.end, fence.reason, evidence))
    return out


def _merge_ruled_out(protections, limit):
    meanings, dialects, names = {}, [], {}
    for protection in protections:
        for reading in protection['ruled_out']:
            if reading['kind'] == 'meaning':
                names[reading['concept']] = reading['plain']
                words = meanings.setdefault(reading['concept'], {})
                words.update((word['id'], word) for word in reading['words'])
            elif reading not in dialects:
                dialects.append(reading)
    return ([{'kind': 'meaning', 'concept': cid, 'plain': names[cid], 'words': [words[eid] for eid in sorted(words)[:limit]]}
             for cid, words in sorted(meanings.items())] + dialects)


def _lookup_cards(tr, query, *, level, vulgarity, embellishment, document_type, document_config,
                  include_gated, unlock=None, short=True, limit=50):
    d = tr.dictionary
    genre = resolve_document(query, config=d.genres, document_type=document_type, document_config=document_config)
    setting = genre.setting(parse_embellishment(embellishment) if embellishment is not None else None)
    eff = tr.effective(level=level, vulgarity=vulgarity, unlock=["all"] if include_gated else unlock,
                       embellishment=embellishment, document_type=document_type, document_config=document_config)
    return _LookupCards(d, eff, setting, genre.policy.term_domains, short, limit)


class _LookupIndex:
    """Fixed spelling data shared by bounded batches; scores equal scalar trigram cosine exactly."""
    def __init__(self, patterns, glosses):
        self.patterns = tuple((strip_markup(text), concepts) for text, concepts in patterns)
        self.texts = tuple(sorted({text for text, _ in self.patterns} | set(glosses)))
        self.ngrams = NgramIndex(self.texts)

    def similarities(self, query):
        return {self.texts[i]: score for i, score in self.ngrams.scores(query).items()}


@lru_cache(maxsize=_SPELLING_CORPORA)
def _lookup_index(patterns, glosses):
    # Cache by actual immutable spelling content, not dictionary_id: in-memory derived dictionaries
    # can retain an identity. Four corpora bound retained postings across extension/dictionary reloads.
    return _LookupIndex(patterns, glosses)


class _LookupBatch:
    """One request-local lookup batch, evaluated lazily for adaptive quiz exclusions.

    Reuses policy and fixed spelling data, invokes the ordinary scoring kernel, and projects IDs only.
    Query results are request-local; the bounded spelling index is shared by actual content.
    It creates no new public operation or response contract.
    """
    def __init__(self, translator, *, level, vulgarity, embellishment, document_type, document_config, include_gated):
        self.translator = translator
        self.cards = _lookup_cards(translator, None, level=level, vulgarity=vulgarity, embellishment=embellishment,
            document_type=document_type, document_config=document_config, include_gated=include_gated)
        dictionary = translator.dictionary
        self.index = _lookup_index(tuple((pattern.text, pattern.concepts) for pattern in dictionary.patterns),
                                   tuple(entry.gloss.lower() for entry in dictionary.idioms + dictionary.garnish if entry.gloss))
        self.include_gated = include_gated
        self.cache = {}

    def entry_ids(self, query):
        if query not in self.cache:
            self.cache[query] = frozenset(_query(query, self.translator, self.cards, self.include_gated,
                                                index=self.index, ids_only=True))
        return self.cache[query]


def lookup(query: str, *, level: int | str = 5, vulgarity: int | str | None = None, limit: int = 8,
           include_gated: bool = False, short: bool = False, embellishment: int | str | None = None,
           document_type: str = "general", document_config: dict | None = None, themes: dict[str, bool] | None = None, invention: bool | None = None,
           unlock: list[str] | None = None, translator: Translator | None = None) -> dict[str, Any]:
    """Find Aussie options for a plain-English meaning ("very busy"), or explain a slang term ("goog").
    short: compact cards with match-kind codes for an agent checking a choice.

    Applies the requested level and vulgarity to every route. Explicit term searches explain vocabulary;
    they do not certify it as a replacement for the source context.
    `include_gated` also returns entries held back for doubtful origin or meaning (marked as such).
    """
    translator, document_config = resolve_request(translator, document_config, themes=themes, invention=invention)
    if not isinstance(query, str) or not query.strip():
        raise UserError("query must be a non-empty string")
    if type(limit) is not int or limit < 1:
        raise UserError(f"limit must be 1 or more, not {limit}")
    tr = translator
    cards = _lookup_cards(tr, query, level=level, vulgarity=vulgarity, embellishment=embellishment,
        document_type=document_type, document_config=document_config, include_gated=include_gated,
        unlock=unlock, short=short, limit=limit)
    return _query(query, tr, cards, include_gated)


def _query(query, tr, cards, include_gated, *, index=None, ids_only=False):
    d, eff, setting = cards.dictionary, cards.effective, cards.setting
    short, limit = cards.short, cards.limit
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
    from .detect import read_meanings
    tags = pos.tag([t.text for t in tokens]) if tokens else []
    interpreted = read_meanings(tokens, d, tags=tags, fragment=True)
    readings = interpreted.detections
    readings = [r for r in readings if positive_context(tokens, r.start, r.start)]
    named = set(d.named_meanings.get(fold(query.replace("_", " ")), ()))
    exhaustive = named or _scoped_query(tokens, readings, tags)
    established = named | {cid for det in readings for cid in det.concepts}
    from .detect import applicable_concepts
    from .degree import degree_matches, realised_degree
    raw_matches = d.index.find(tokens)
    # ruled out: a sense said only of people of a thing, or one a wider reading superseded
    blocked = set(interpreted.ruled_out).union(*(det.supersedes for det in readings))
    for matched in raw_matches:
        possible = applicable_concepts(matched.pattern.concepts, d.concepts, tokens, matched.end, noun_use=None)
        blocked.update(set(matched.pattern.concepts) - set(possible))
        if not positive_context(tokens, matched.start, matched.start):
            blocked.update(matched.pattern.concepts)
        # words a reading holds carry only its senses: "fantastic" in "fantastic terrors" is no exclamation
        for held in readings:
            if held.start <= matched.start and matched.end <= held.end:
                blocked.update(set(matched.pattern.concepts) - set(held.concepts))

    out = {"query": query, "card_version": CARD_VERSION,
           **eff.envelope(profile=False)}
    waiting = sorted(set(d.wordless_meanings).intersection(established))
    if waiting and not ids_only:
        out.update(outcome=outcomes.NO_WORD_YET,
                   meanings=[{"concept": cid, "plain": d.concepts[cid].plain, "near": cards.near(cid)} for cid in waiting],
                   note="The dictionary recognises this meaning but has no Aussie word for it yet. "
                        "Consider proposing one.")
    form_matches = d.form_index.find(tokens)
    object_terms = _object_terms(form_matches, readings, tokens, tags, d) if waiting else set()
    object_concepts = {cid for eid in object_terms for cid in d.entries[eid].concept}
    if waiting and not established.difference(waiting) and not object_terms:
        if ids_only:
            return set()
        images, _ = lookup_images(d, query, eff, setting, limit, tokens=tokens, readings=readings, named=named)
        return {**out, "results": [], **({"imagery": images} if images else {})}

    qn = form_key(q)
    slotted = {m.pattern.entry_id for m in form_matches
               if m.start == 0 and m.end == len(tokens) and m.pattern.slots}
    term_matches = {e.id: matched for e in d.idioms + d.garnish if e.status != 'omit'
                    and (matched := _term_match(e, qn, slotted))}
    whole_terms = any(match.whole for match in term_matches.values())
    if not waiting and not named and not whole_terms:
        protections = _protected_query(query, tokens, readings, exhaustive, cards)
        if not protections and (not established or exhaustive is None):
            protections = _dialect_protected_query(query, tokens, cards)
        if protections:
            if ids_only:
                return set()
            return {**out, 'outcome': outcomes.LEFT_AS_WRITTEN, 'results': [], 'protections': protections,
                    'ruled_out': _merge_ruled_out(protections, limit),
                    'note': ' '.join(dict.fromkeys(p['reason'] for p in protections if p['reason']))}

    sim = NgramEmbedder()
    indexed = index.similarities(q) if index else None
    def similarity(text):
        return indexed.get(text, 0.0) if indexed is not None else sim.similarity(q, text)
    model = None if waiting else tr.lookup_embedder
    if waiting:
        exhaustive = named or established | object_concepts

    def degree_fits(entry, concepts):
        paths = [(cid, det) for det in readings for cid in concepts.intersection(det.degree_concepts)]
        if not paths:
            return True
        for cid, det in paths:
            if cid in det.degree_conflicts:
                continue
            source = realised_degree(det.semantic_degree.get(cid), det.degree_qualifier)
            if degree_matches(source, entry.semantic_degree.get(cid), relational=det.result_clause):
                return True
        return False
    def effects_for(entry):
        connected = [det for det in readings if set(entry.concept).intersection(det.concepts)]
        return tuple(sorted(set(entry.semantic_effects).union(*(mapping_effects(entry, det,
            narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation)
            for det in connected))))

    concept_score: dict[str, float] = {}
    patterns = index.patterns if index else ((strip_markup(p.text), p.concepts) for p in d.patterns)
    for text, concepts in patterns:
        score = 1.0 if text == q else similarity(text) * fuzz
        for c in concepts:
            concept_score[c] = max(concept_score.get(c, 0.0), score)
    for det in readings:
        if exhaustive is not None or det.frame not in {'np', 'adv'}:
            for cid in set(det.concepts).intersection(established):
                concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    for cid in object_concepts:
        concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    whole_query = [m for m in raw_matches if m.start == 0 and m.end == len(tokens)]
    for matched in whole_query:
        for cid in matched.pattern.concepts:
            concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    if one_word:   # "cry": the concept's own description names it even where no trigger does
        variants = {q, re.sub(r"ying$", "y", q), re.sub(r"ing$", "", q), re.sub(r"ing$", "e", q),
                    re.sub(r"ies$", "y", q), re.sub(r"s$", "", q)}
        for cid, concept in d.concepts.items():
            if variants & set(re.findall(r"[a-z']+", (concept.description or "").lower())):
                concept_score[cid] = max(concept_score.get(cid, 0.0), DESCRIPTION_NAMES_IT)
    for cid in named:
        concept_score[cid] = max(concept_score.get(cid, 0), 1.0)
    scored: list[tuple[float, Entry, str, str]] = []
    parsed_concepts = {cid for eid in slotted for cid in d.entries[eid].concept}
    negative_anchors = {w[:-4] if w.endswith("less") else w for w in content_words(q)}
    def score_entry(e, term_match, use_model=True):
        if waiting and not set(e.concept).intersection(exhaustive):
            return None
        if e.id in object_terms:
            return SCORE_TERM, e, 'term', "slang term in context object"
        if term_match:
            return term_match.score, e, term_match.kind, term_match.description
        paths = set(e.concept)
        if exhaustive is not None:
            paths.intersection_update(exhaustive)
        if paths.intersection(blocked):
            paths.intersection_update(established)
        if not paths or not degree_fits(e, paths):
            return None
        if parsed_concepts and not parsed_concepts.intersection(e.concept):
            return None
        best = max((concept_score.get(c, 0.0) for c in paths), default=0.0)
        if e.gloss and paths == set(e.concept):
            gloss = e.gloss.lower()
            hit = one_word and q in re.findall(r"[a-z']+", gloss)
            best = max(best, GLOSS_NAMES_IT if hit else similarity(gloss) * GLOSS_FUZZ[not one_word])
        if model is not None and use_model:
            # the local model: meaning where n-grams only see spelling. Scored for every entry, not just the
            # ones n-grams missed: otherwise a weak n-gram match (knackered for "very tired", 0.65) keeps its weak
            # score while a model-only one (maggoted, from "Very drunk.") gets the model's, and outranks it
            texts = meaning_texts(e, d, concepts=paths)
            m = max((model.similarity(q, t) for t in texts if t and bool(_NEGATED.search(t.lower())) == negated
                     and (not negated or negative_anchors & {
                         w[:-4] if w.endswith("less") else w for w in content_words(t)})),
                    default=0.0)
            if m >= model.lookup_threshold and MEANING_FLOOR + (m - model.lookup_threshold) > best:
                return (round(MEANING_FLOOR + (m - model.lookup_threshold), 3), e,
                        'model' if best < MEANING_FLOOR else 'meaning', "meaning (local model)")
        if best >= MEANING_FLOOR:
            return best, e, 'meaning', "meaning"
        return None

    recognised = exhaustive is not None
    deferred = []
    for e in d.idioms + d.garnish:
        if e.status == "omit":
            continue
        if dial_rejection(e, eff, include_gated=include_gated):
            deferred.append(e)   # term-matched only if nothing is offered: most entries, at the lowest dials
            continue
        term_match = term_matches.get(e.id)
        recognised |= term_match is not None
        if not term_match and semantic_rejection(e, narrator_opinion=setting.narrator_opinion,
                quantity_approximation=setting.quantity_approximation, effects=effects_for(e)):
            deferred.append(e)
        elif match := score_entry(e, term_match):
            scored.append(match)
    scored.sort(key=lambda t: (-t[0], t[1].incoherence, t[1].id))
    if ids_only:
        return {entry.id for _, entry, _, _ in scored[:limit]}
    results = [{**cards.entry(e), 'match_kind': kind, **({} if short else {'match': how, 'score': round(s, 2)})}
               for s, e, kind, how in scored[:limit]]
    for card in results:
        entry = d.entries[card["id"]]
        effects = effects_for(entry)
        if effects:
            card["semantic_effects"] = list(effects)
        reason = semantic_rejection(entry, narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation, effects=effects)
        if reason:
            card.update(effects_permitted=False, effect_rejection=reason)
    # a lookup reads no profile settings, so its envelope is the dials alone (no profile_config)
    out["results"] = results
    images, recognised_image = lookup_images(d, query, eff, setting, limit, tokens=tokens, readings=readings, named=named)
    recognised |= recognised_image
    if not results and not images and not recognised:
        # cheapest evidence first: a held term itself, then its meaning by spelling, then by the model
        recognised = (any(e.id in term_matches for e in deferred)
                      or any(score_entry(e, None, use_model=False) for e in deferred)
                      or any(score_entry(e, None) for e in deferred))
    if images:
        out["imagery"] = images
    out["outcome"] = (outcomes.NO_WORD_YET if waiting else outcomes.MATCHED if results or images
                      else outcomes.NOTHING_FITS if recognised else outcomes.NOT_IN_DICTIONARY)
    if not results and not images and not waiting:
        out["note"] = {
            outcomes.NOTHING_FITS: "The dictionary recognises this meaning but has no compatible suggestion at these "
                            "settings. Try another wording or look up a specific term.",
            outcomes.NOT_IN_DICTIONARY: "No entry. If you're sure Australians say it, it's probably fine but unvetted; "
                                 "otherwise rephrase. Consider proposing it for the dictionary."}[out["outcome"]]
    return out
