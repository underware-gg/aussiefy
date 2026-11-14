"""Authored English sentence forms checked against source arguments and reviewed degree."""

from dataclasses import replace

from .degree import realised_degree
from .morph import object_of_possessive
from .detect import VERB_LEADERS, read_meanings
from .realise import realise
from .schema import parse_entry
from .select import form_problem, usable_forms
from .text import tokenize


def plain_entry(concept, detection, dictionary):
    # A display noun cannot replace a consumed finite predicate while its possessive subject stays
    # outside the span ("Her heart was broken" -> "Her heartbreak"). An explicit authored form may
    # address that scope; otherwise abstain and preserve source rather than guessing a sentence.
    if detection.frame == 'np' and 'be' in detection.captures and 'np' not in concept.plain_forms:
        return None
    forms = concept.plain_forms.get(detection.frame, concept.plain if detection.frame != 'clause' else '')
    forms = (forms,) if isinstance(forms, str) else forms
    for form in forms:
        reading = detection
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
                             'frame': detection.frame, 'concept': [concept.id]})
        if detection.degree_concepts or detection.degree_conflicts:
            english = realise(entry, form, reading)
            readings = read_meanings(tokenize(english), dictionary, fragment=True).detections
            grades = {realised_degree(reading.semantic_degree.get(concept.id), reading.degree_qualifier)
                      for reading in readings if concept.id in reading.concepts}
            grades.discard(None)
            if len(grades) == 1:
                entry = replace(entry, semantic_degree={concept.id: grades.pop()})
        if usable_forms(entry, reading):
            # A display name must not turn a required source "could" into "can". Check only
            # unambiguous required modal literals; optional/mixed pattern words assert no such fact.
            modals = VERB_LEADERS - {'to', 'not', 'never'}
            required = [element.values for element in detection.source_pattern.elements
                        if element.kind == 'lit' and not element.optional and element.values
                        and element.values <= modals] if detection.source_pattern else []
            if required:
                words = {token.norm for token in tokenize(realise(entry, form, reading))}
                if any(not values & words for values in required):
                    continue
            return entry, reading
    return None
