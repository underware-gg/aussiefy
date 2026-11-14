"""Curated one-way stand-ins, preserving the waiting source reading."""

from dataclasses import replace

from .match_keys import detection_match
from .select import narrow
from .tuning import Tuning


def eligible_near(translator, detection, sentence, run, taken):
    dictionary = translator.dictionary
    if not run.embellishment.near_meanings:
        return [], []
    if not detection.concepts or not set(detection.concepts) <= set(dictionary.wordless_meanings):
        return [], []
    if detection.source_pattern is not None and detection.source_pattern.fence is not None:
        return [], []
    checking = replace(run, pol=replace(run.pol, variety=0), tuning=Tuning(), preferences_used=set())
    found, rejected = [], []
    for source in detection.concepts:
        for relation in dictionary.concepts[source].near:
            if relation.minimum > run.embellishment.near_meanings:
                continue
            target = replace(detection, concepts=(relation.concept,), direct=set(), mapping_effects={},
                             semantic_degree={}, degree_concepts=frozenset(), degree_conflicts=frozenset())
            keep, failures = translator.eligible(target, sentence, checking, run.eff, run.state, taken,
                                                 dictionary.idioms_for((relation.concept,)))
            rejected.extend(failures)
            for candidate in keep:
                candidate.near = relation
                candidate.reading = candidate.reading or target
                found.append(candidate)
    # One rendering can occur through several relations; retain one cited, deterministic path.
    choices = {}
    for candidate in found:
        choices.setdefault(candidate.entry.id, candidate)
    found = list(choices.values())
    preference = run.tuning.apply(found, detection_match(detection), level=run.eff.level,
                                 vulgarity=run.eff.vulgarity, embellishment=run.embellishment.step)
    found = narrow(found, rejected, run.pol.variety, run.state)
    if preference is not None and any(c.entry.id == preference.term and c.weight > 0 for c in found):
        run.preferences_used.add(preference.position)
    return found, rejected
