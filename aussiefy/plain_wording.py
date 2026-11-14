"""Authored English sentence forms checked against source arguments and reviewed degree."""

from dataclasses import replace

from .degree import realised_degree
from .morph import object_of_possessive
from .detect import read_meanings
from .realise import realise
from .schema import parse_entry
from .select import form_problem, usable_forms
from .text import tokenize


def plain_entry(concept, detection, dictionary):
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
            return entry, reading
    return None
