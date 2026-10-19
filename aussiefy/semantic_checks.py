"""Bounded source-aware checks for reviewed semantic mappings and predicate changes."""

from __future__ import annotations

import re
from typing import Iterable

from .degree import realised_degree
from .detect import detect, predicate_lead, resolve_overlaps
from .genre import Embellishment
from .model import Dictionary
from .schema import Entry
from .select import mapping_effects, semantic_rejection
from .text import Token, sentences, tokenize


def _readings(candidates: Iterable[list[Token]], dictionary: Dictionary):
    for sentence in candidates:
        detections = resolve_overlaps(detect(sentence, dictionary.index, concepts=dictionary.concepts,
            adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index))
        for det in detections:
            yield sentence, det


def degree_issues(text: str, original: str | None, spans: list[tuple[int, int, Entry]],
                  dictionary: Dictionary) -> list[dict]:
    """Known degree changes inside one unambiguous local predicate edit; unknown evidence stays unknown."""
    if original is None or text == original or not any(e.semantic_degree for _, _, e in spans):
        return []
    candidates = (s for s in sentences(tokenize(original)) if dictionary.degree_index.find(s))
    sources = []
    for sentence, det in _readings(candidates, dictionary):
        for cid, lexical in det.semantic_degree.items():
            if cid in det.degree_conflicts:
                continue
            band = realised_degree(lexical, det.degree_qualifier)
            if band not in {'mild', 'strong'} and not (band == 'unmarked' and det.result_clause):
                continue
            start = det.start - len(det.degree_qualifier)
            sources.append((cid, band, tuple(t.norm for t in sentence[:start]),
                            tuple(t.norm for t in sentence[det.end:])))
    groups = {}
    for sentence in sentences(tokenize(text)):
        starts = {t.start: i for i, t in enumerate(sentence)}
        for start, end, entry in spans:
            if not sentence[0].start <= start < end <= sentence[-1].end:
                continue
            at = starts[start]
            lead = predicate_lead(sentence, at, reviewed_degree=True)
            if lead.negated:
                continue
            qualifier = tuple(t.norm for t in sentence[lead.start:at])
            before = tuple(t.norm for t in sentence[:lead.start])
            after = tuple(t.norm for t in sentence if t.start >= end)
            for cid in entry.concept:
                paired = [(band, prefix, tail) for meaning, band, prefix, tail in sources
                          if meaning == cid and before == prefix and after == tail]
                if len(paired) != 1:
                    continue
                band = paired[0][0]
                key = sentence[lead.start].start, end, cid, band
                groups.setdefault(key, set()).add(realised_degree(entry.semantic_degree.get(cid), qualifier))
    issues = []
    for (start, end, cid, source), targets in groups.items():
        if None in targets or source in targets:
            continue
        issues.append({'kind': 'semantic_degree', 'phrase': text[start:end],
                       'why': f'{cid}: source degree {source}, recognised target degree {", ".join(sorted(targets))}'})
    return issues


def composition_issues(text: str, original: str | None, spans: list[tuple[int, int, Entry]],
                        dictionary: Dictionary) -> list[dict]:
    """A local predicate expansion before the source's unchanged result tail, not general grammar checking."""
    if original is None or text == original:
        return []
    suspects = [(a, b, entry) for a, b, entry in spans if entry.frame in {'adj', 'predicate_adj'}
                and re.search(r'\benough\b', text[a:b], re.I)
                and re.match(r'\s+enough\b', text[b:], re.I)]
    if not suspects:
        return []

    sources = []
    candidates = (s for s in sentences(tokenize(original)) if any(t.norm == 'enough' for t in s))
    for sentence, det in _readings(candidates, dictionary):
        if det.result_clause and det.end < len(sentence) and sentence[det.end].norm == 'enough':
            sources.append((det, tuple(t.norm for t in sentence[:det.start]),
                            tuple(t.norm for t in sentence[det.end:])))
    found = {}
    for sentence in sentences(tokenize(text)):
        for start, end, entry in suspects:
            if not sentence[0].start <= start < end <= sentence[-1].end:
                continue
            prefix = tuple(t.norm for t in sentence if t.end <= start)
            tail = tuple(t.norm for t in sentence if t.start >= end)
            paired = [det for det, before, after in sources if before == prefix and after == tail
                      and set(entry.concept).intersection(det.concepts)]
            if len(paired) == 1:
                found[start, end] = {'kind': 'predicate_composition', 'phrase': text[start:end],
                    'why': "a local predicate replacement inserted its own 'enough' complement before the source's unchanged 'enough' continuation"}
    return list(found.values())


def mapping_issues(text: str, original: str | None, spans: list[tuple[int, int, Entry]],
                    dictionary: Dictionary, setting: Embellishment) -> tuple[list[dict], list[tuple[int, int]]]:
    """Check reviewed source mappings paired inside a single unambiguous local edit, not arbitrary paraphrases."""
    from difflib import SequenceMatcher

    if original is None:
        return [], []
    candidates = (s for s in sentences(tokenize(original)) if dictionary.mapping_index.find(s))
    source = [(sentence[d.start].start, sentence[d.end-1].end, d)
              for sentence, d in _readings(candidates, dictionary) if d.mapping_effects]
    if not source:
        return [], []
    old, new = tokenize(original), tokenize(text)
    issues, approximated = [], []
    paired = set()
    for tag, i, j, k, l in SequenceMatcher(None, [t.norm for t in old], [t.norm for t in new], autojunk=False).get_opcodes():
        if tag != 'replace' or i == j or k == l:
            continue
        a, b, c, d = old[i].start, old[j-1].end, new[k].start, new[l-1].end
        sources = [(s,t,det) for s,t,det in source if s < b and a < t]
        if len(sources) != 1:
            continue
        s, t, det = sources[0]
        targets = {}
        for u, v, entry in spans:
            if u < d and c < v and set(entry.concept).intersection(det.mapping_effects):
                targets.setdefault((u,v), []).append(entry)
        if len(targets) != 1:
            continue
        (u,v), entries = next(iter(targets.items()))
        if (s,t,u,v) in paired:
            continue
        paired.add((s,t,u,v))
        paths = [(mapping_effects(entry, det, narrator_opinion=setting.narrator_opinion,
                                 quantity_approximation=setting.quantity_approximation), entry) for entry in entries]
        effects, entry = min(paths, key=lambda path: (bool(semantic_rejection(path[1],
            narrator_opinion=setting.narrator_opinion, quantity_approximation=setting.quantity_approximation,
            effects=path[0])), len(path[0]), path[1].id))
        reason = semantic_rejection(entry, narrator_opinion=setting.narrator_opinion,
                                    quantity_approximation=setting.quantity_approximation, effects=effects)
        if reason:
            issues.append({'kind': 'semantic_effect', 'phrase': text[u:v], 'entry': entry.id,
                           'semantic_effects': list(effects), 'why': reason})
        elif 'quantity_approximation' in effects:
            approximated.append((s,t))
    return issues, approximated
