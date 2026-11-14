"""Source-owned Australian terms, checked by the same grammatical reader as replacements."""

from copy import deepcopy
from dataclasses import dataclass, replace

from . import pos
from .detect import Detection, detect, read_meanings, resolve_overlaps, check_frame
from .grammar import grammar_problem
from .realise import number_problem
from .schema import Entry
from .text import capital_is_positional


@dataclass(frozen=True)
class OwnedTerm:
    entry: Entry
    detection: Detection


def read_owned(tokens, dictionary, *, tags=None, complete=True, readings=None):
    tags = tags if tags is not None else pos.tag([token.text for token in tokens])
    readings = (read_meanings(tokens, dictionary, tags=tags, complete=complete).detections
                if readings is None else readings)
    forms = detect(tokens, dictionary.owned_index, tags=tags, complete=complete,
                   adjective_nouns=dictionary.adjective_nouns, concepts=dictionary.concepts,
                   degree_index=dictionary.degree_index, person_nouns=dictionary.person_nouns)
    supported = []
    for det in forms:
        entry = dictionary.entries[det.source_pattern.entry_id]
        if (entry.status == 'omit' or entry.reads_as != 'australian'
                or not set(det.concepts).intersection(entry.concept)):
            continue
        if (det.frame == 'np' and tags[det.start] in pos.NAMES and entry.form[:1].islower()
                and not capital_is_positional(tokens, det.start)):
            continue
        if (grammar_problem(entry, det, tokens, tags, complete=complete)
                or number_problem(entry, det, tokens, tags)):
            continue
        independent = [r for r in readings if r.start <= det.start and det.end <= r.end
                       and r.source_pattern is not None and r.source_pattern.fence is None and r.method != "embedding"
                       and set(r.concepts).intersection(entry.concept)]
        # A shorter Australian form cannot overturn a settled larger source meaning.
        if any(r.start <= det.start and det.end <= r.end and (r.start, r.end) != (det.start, det.end)
               and r.concepts and not set(r.concepts).intersection(entry.concept)
               and r.source_pattern is not None and r.method != 'embedding' for r in readings):
            continue
        if (entry.other_sense or entry.plain_sense) and not independent:
            continue
        supported.append(det)
    for matched in dictionary.owned_index.find(tokens):
        entry = dictionary.entries[matched.pattern.entry_id]
        if (entry.concept or entry.type != 'garnish' or entry.status == 'omit'
                or entry.reads_as != 'australian' or entry.other_sense or entry.plain_sense):
            continue
        det = check_frame(matched, tokens, dictionary.adjective_nouns, tags, complete=complete)
        if det is not None and not grammar_problem(entry, det, tokens, tags, complete=complete):
            supported.append(det)
    fences = [deepcopy(r) for r in readings if r.source_pattern is not None and r.source_pattern.fence is not None]
    resolved = resolve_overlaps([*fences, *supported])
    out = []
    for det in resolved:
        if det.source_pattern.entry_id is None:
            continue
        entries = [dictionary.entries[eid] for eid in sorted(det.direct)
                   if dictionary.entries[eid].status != 'omit' and dictionary.entries[eid].reads_as == 'australian']
        if entries:
            entry = entries[0]
            concepts = tuple(cid for cid in det.concepts if any(cid in item.concept for item in entries))
            out.append(OwnedTerm(entry, replace(det, concepts=concepts)))
    return out
