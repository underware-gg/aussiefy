"""Reviewed degree and ownership of qualifiers in a predicate substitution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .morph import single_word_form

if TYPE_CHECKING:
    from .detect import Detection
    from .schema import Entry


QUALIFIED_BANDS = {
    ('very',): 'strong', ('extremely',): 'strong', ('really',): 'strong',
    ('slightly',): 'mild', ('a', 'bit'): 'mild', ('a', 'little'): 'mild',
    ('mildly',): 'mild',
}
STRONG_QUALIFIERS = {('absolutely',), ('completely',), ('totally',), ('utterly',), ('really',)}
RELATIONAL = {('so',), ('too',)}
QUALIFIER_WORDS = frozenset({'mildly', 'barely', 'lightly', 'somewhat', 'almost', 'nearly', 'only'})


@dataclass(frozen=True)
class DegreePlan:
    """An eligible form either retains the owned qualifier or expresses its degree itself."""
    absorb: bool = False
    problem: str | None = None


def realised_degree(band: str | None, qualifier: tuple[str, ...]) -> str | None:
    if not qualifier or qualifier in RELATIONAL:
        return band
    if band == 'strong' and qualifier in STRONG_QUALIFIERS:
        return 'strong'
    if band == 'unmarked':
        return QUALIFIED_BANDS.get(qualifier)
    return None


def degree_matches(source: str | None, target: str | None, *, relational: bool = False) -> bool:
    """Unspecified degree is permissive only outside a threshold-bearing construction."""
    return source == 'unmarked' and not relational or source is not None and source == target


def degree_plan(entry: Entry, det: Detection, form: str) -> DegreePlan:
    if not (det.degree_concepts or det.degree_conflicts):
        return DegreePlan()
    shared = set(entry.concept) & set(det.concepts)
    if shared & det.degree_conflicts:
        return DegreePlan(problem='conflicting source degree evidence')
    readings = []
    for cid in shared & det.degree_concepts:
        lexical = det.semantic_degree.get(cid)
        if lexical is None and not det.degree_qualifier and not det.result_clause:
            continue
        source = realised_degree(lexical, det.degree_qualifier)
        if source is None:
            return DegreePlan(problem=f'{cid}: unsupported source degree; preserve its qualifier and predicate')
        readings.append((cid, source, entry.semantic_degree.get(cid)))
    if not readings:
        return DegreePlan()
    retained = (not det.degree_qualifier or entry.frame in {'adj', 'predicate_adj'} and single_word_form(form))
    if retained and all(degree_matches(source, realised_degree(target, det.degree_qualifier),
                                      relational=det.result_clause) for _, source, target in readings):
        return DegreePlan()
    # Only a reviewed, non-relational modifier can be expressed by the target's own certificate.
    # Every shared graded reading must agree: one convenient sense cannot discard another's modifier.
    if det.degree_qualifier and not det.result_clause and entry.frame in {'adj', 'predicate_adj'} and all(
            source in {'mild', 'strong'} and source == target for _, source, target in readings):
        return DegreePlan(absorb=True)
    return DegreePlan(problem='target cannot preserve the source degree and dependent construction')
