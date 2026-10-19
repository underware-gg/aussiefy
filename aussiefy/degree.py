"""Reviewed degree and the qualifiers which must survive a predicate substitution."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .detect import Detection
    from .schema import Entry


QUALIFIED_BANDS = {
    ('very',): 'strong', ('extremely',): 'strong',
    ('slightly',): 'mild', ('a', 'bit'): 'mild', ('a', 'little'): 'mild',
    ('mildly',): 'mild',
}
RELATIONAL = {('so',), ('too',)}
QUALIFIER_WORDS = frozenset({'mildly', 'barely', 'lightly', 'somewhat', 'almost', 'nearly', 'only'})


def realised_degree(band: str | None, qualifier: tuple[str, ...]) -> str | None:
    if not qualifier:
        return band
    if qualifier in RELATIONAL:
        return band
    if band == 'unmarked':
        return QUALIFIED_BANDS.get(qualifier)
    return None


def degree_problem(entry: Entry, det: Detection, form: str) -> str | None:
    if not (det.degree_concepts or det.degree_conflicts):
        return None
    shared = set(entry.concept) & set(det.concepts)
    if shared & det.degree_conflicts:
        return 'conflicting source degree evidence'
    for cid in shared & det.degree_concepts:
        lexical = det.semantic_degree.get(cid)
        if lexical is None and not det.degree_qualifier:
            continue
        if lexical is None:
            return f'{cid}: source degree is unknown; preserve its qualifier and predicate'
        source = realised_degree(lexical, det.degree_qualifier)
        if det.degree_qualifier:
            if source is None:
                return 'unsupported degree composition: keep the source qualifier and predicate'
            if entry.frame not in {'adj', 'predicate_adj'} or not re.fullmatch(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", form):
                return 'retained degree qualifier requires a compatible single-word predicate'
        if source == 'unmarked' and not det.degree_qualifier:
            continue
        target = realised_degree(entry.semantic_degree.get(cid), det.degree_qualifier)
        if target is None:
            return f'{cid}: target degree is unknown for this realised form'
        if source != target:
            return f'{cid}: source degree {source}, realised target degree {target}'
    return None
