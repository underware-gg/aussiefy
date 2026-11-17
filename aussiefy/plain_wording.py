"""Authored English sentence forms checked against source arguments and reviewed degree."""

from dataclasses import dataclass, replace
import re

from .degree import realised_degree
from .morph import object_of_possessive
from .detect import read_meanings
from .context import AUXILIARIES, NEGATION
from . import morph, pos
from .matcher import phrase_token
from .realise import realise
from .schema import parse_entry
from .select import form_problem, usable_forms
from .text import tokenize



_MODALS = AUXILIARIES - morph.BE_FORMS - morph.HAVE_FORMS - morph.DO_FORMS
_NEGATORS = NEGATION & {'not', "n't", 'never'}


def _finite(token, tag):
    return tag in {'VBD', 'VBP', 'VBZ', 'MD'} or token.norm in morph.BE_FORMS or morph.is_past(token.norm)


def _past(token, tag):
    return tag == 'VBD' or morph.is_past(token.norm)


def _auxiliary(words, tags, i):
    word = words[i].norm
    if word in morph.BE_FORMS:
        return tags[i] not in {'NN', 'NNS', 'VBG'} or i > 0 and words[i-1].norm in AUXILIARIES
    if word not in morph.HAVE_FORMS | morph.DO_FORMS:
        return False
    j = i + 1
    while j < len(words) and words[j].norm in _NEGATORS:
        j += 1
    return j < len(words) and tags[j].startswith('VB')


@dataclass(frozen=True)
class WordingScope:
    tokens: tuple
    tags: tuple
    start: int
    end: int
    predicate: int | None
    possessor: tuple[int, int] | None

    @classmethod
    def read(cls, detection, tokens, tags=None):
        tags = tags or pos.tag([token.text for token in tokens])
        start, end = detection.start, detection.end
        predicate = next((i for i in range(start, end) if i > start and _finite(tokens[i], tags[i])), None) if detection.frame == 'np' else None
        possessor = None
        if start and tokens[start-1].norm in morph.POSSESSIVES:
            possessor = (start-1, start)
        elif start >= 2 and tags[start-1] == 'POS' and tags[start-2] == 'NNP':
            owner = start-2
            if owner == 0 or tags[owner-1] not in {'NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'DT', 'CC', 'POS'}:
                possessor = (owner, start)
        return cls(tuple(tokens), tuple(tags), start, end, predicate, possessor)

    def bind(self, form, detection):
        captures = dict(detection.captures)
        start = detection.start
        if ('{poss}' in form and 'poss' not in captures and self.possessor is None
                and self.start and self.tags[self.start-1] == 'POS'):
            return None
        if '{subj}' in form and 'subj' not in captures:
            if self.predicate is None or self.possessor is None:
                return None
            a, b = self.possessor
            owner = phrase_token(list(self.tokens[a:b]))
            subject = morph.subject_of_possessive(owner.text)
            if subject is None:
                return None
            captures['subj'] = replace(owner, text=subject, norm=subject.casefold())
            start = a
        if '{poss}' in form and 'poss' not in captures and self.possessor:
            a, b = self.possessor
            captures['poss'] = phrase_token(list(self.tokens[a:b]))
            start = a
        if self.predicate is not None:
            if self.predicate <= self.start:
                return None
            if '{np}' in form and 'np' not in captures:
                captures['np'] = phrase_token(list(self.tokens[self.start:self.predicate]))
        # Surface auxiliaries include adjacent grammatical negation, not a guessed agreement subject.
        for key in ('be', 'have', 'do'):
            token = captures.get(key)
            if token is None:
                continue
            at = next((i for i in range(self.start, self.end) if self.tokens[i].start == token.start), None)
            if at is None:
                if '{' + key + '}' in form:
                    return None
                continue
            end = at + 1
            if not re.search(r'\{' + key + r'\}\s+(?:not|never)\b', form):
                while end < self.end and self.tokens[end].norm in _NEGATORS:
                    end += 1
            if detection.question and end > at + 1:
                return None  # Inverted negative clauses need a separately supported scope.
            words = [t.norm for t in self.tokens[at:end]]
            if start < detection.start and 'subj' in captures and 'subj' not in detection.captures:
                words[0] = morph.agree(key, captures['subj'].norm, morph.tense_of(token.norm))
            surface = ' '.join(words)
            captures[key] = replace(token, text=surface, end=self.tokens[end-1].end)
        return replace(detection, start=start, captures=captures,
                       inflection='' if self.predicate is not None else detection.inflection)

    def compatible(self, text, reading):
        source = list(self.tokens[reading.start:self.end])
        target = tokenize(text)
        source_tags = list(self.tags[reading.start:self.end])
        target_tags = pos.tag([token.text for token in target])
        if self.predicate is not None:
            target_finite = next((i for i, (t, tag) in enumerate(zip(target, target_tags))
                                  if tag in {'VBD', 'VBP', 'VBZ', 'MD'} or t.norm in morph.BE_FORMS), None)
            if target_finite is None:
                return False
            def progressive(words, tags):
                return any(word.norm in morph.BE_FORMS and any(tag == 'VBG' for tag in tags[i+1:])
                           for i, word in enumerate(words))
            if progressive(source, source_tags) != progressive(target, target_tags):
                return False
            source_verb = self.tokens[self.predicate]
            if source_verb.norm not in _MODALS and _past(source_verb, self.tags[self.predicate]) != _past(
                    target[target_finite], target_tags[target_finite]):
                return False
        if (self.possessor or self.start and self.tags[self.start-1] == 'POS') and reading.start == self.start and target and (
                target[0].norm in {'a', 'an', 'the'} or target_tags[0].startswith('VB') or target_tags[0] == 'MD'):
            return False  # The external owner remains; an extra determiner would duplicate its role.
        arguments = {key: (tuple(t.norm for t in self.tokens if value.start <= t.start and t.end <= value.end),
                           tuple(t.norm for t in tokenize(value.text))) for key, value in reading.captures.items()
                     if (key in {'np', 'obj', 'objposs'} or key in {'poss', 'subj'} and reading.start < self.start) and value.start >= self.tokens[reading.start].start
                     and value.end <= self.tokens[self.end-1].end}
        has_auxiliary = any(_auxiliary(source, source_tags, i) for i in range(len(source)))
        rebound = reading.start < self.start and 'subj' in reading.captures
        def operator(word):
            if rebound:
                for lemma, forms in (('be', morph.BE_FORMS), ('have', morph.HAVE_FORMS), ('do', morph.DO_FORMS)):
                    if word in forms and word not in {'be', 'been', 'being'}:
                        return lemma, morph.tense_of(word)
            return word
        def signature(words, tags, side):
            norms = tuple(t.norm for t in words)
            spans = {}
            for key, pair in arguments.items():
                value = pair[side]
                hits = [i for i in range(len(words)-len(value)+1) if norms[i:i+len(value)] == value]
                if len(hits) != 1:
                    return None
                i = hits[0]
                if any(i < b and a < i+len(value) for a, b in spans.values()):
                    return None
                spans[key] = (i, i+len(value))
            marks = {a: (key, b) for key, (a, b) in spans.items()}
            out, i = [], 0
            while i < len(words):
                if i in marks:
                    key, i = marks[i]
                    out.append(('argument', key))
                    continue
                norm = norms[i]
                if norm in _NEGATORS:
                    carrier = norms[i-1] if i else ''
                    out.append((norm, operator(carrier)))
                elif norm in _MODALS or has_auxiliary and _auxiliary(words, tags, i):
                    out.append((operator(norm), 'operator'))
                i += 1
            return tuple(out)
        before, after = signature(source, source_tags, 0), signature(target, target_tags, 1)
        return before is not None and before == after


def plain_entry(concept, detection, dictionary, *, tokens, tags=None):
    scope = WordingScope.read(detection, tokens, tags)
    forms = concept.plain_forms.get(detection.frame, concept.plain if detection.frame != 'clause' else '')
    forms = (forms,) if isinstance(forms, str) else forms
    for form in forms:
        reading = scope.bind(form, detection)
        if reading is None:
            continue
        if '{obj}' in form and 'obj' not in reading.captures and 'objposs' in reading.captures:
            captured = reading.captures['objposs']
            object_text = object_of_possessive(captured.text)
            if object_text is not None:
                captures = {key: value for key, value in reading.captures.items() if key != 'objposs'}
                captures['obj'] = replace(captured, text=object_text, norm=object_text.lower())
                reading = replace(reading, captures=captures)
        if not form or form_problem(form, reading):
            continue
        entry = parse_entry({'id': concept.id.lower().replace('_', '-'), 'form': form,
                             'frame': 'clause' if form.startswith('{subj} ') else detection.frame, 'concept': [concept.id]})
        english = realise(entry, form, reading, source_auxiliaries=True)
        if not scope.compatible(english, reading):
            continue
        if detection.degree_concepts or detection.degree_conflicts:
            readings = read_meanings(tokenize(english), dictionary, fragment=True).detections
            grades = {realised_degree(reading.semantic_degree.get(concept.id), reading.degree_qualifier)
                      for reading in readings if concept.id in reading.concepts}
            grades.discard(None)
            if len(grades) == 1:
                entry = replace(entry, semantic_degree={concept.id: grades.pop()})
        if usable_forms(entry, reading):
            return entry, reading
    return None
