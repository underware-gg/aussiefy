"""Curated stand-ins are explicit directions, not inferred synonym links."""

import pytest

from aussiefy.schema import parse_concept, SchemaError


@pytest.mark.parametrize('near', [None, {}, 'CRY', [None],
    [{'concept': 'CRY', 'differs': 'Louder.', 'setting': 'dinkum'}],
    [{'concept': 'NOISY_CRY', 'differs': '', 'setting': 'dinkum'}],
    [{'concept': 'NOISY_CRY', 'differs': 'Louder.', 'setting': 'deadset'}],
    [{'concept': 'NOISY_CRY', 'differs': 'Louder.', 'setting': True}],
    [{'concept': 'NOISY_CRY', 'differs': 'Louder.', 'setting': 'dinkum', 'weight': 1}],
    [{'concept': 'NOISY_CRY', 'differs': 'Louder.', 'setting': 'dinkum'}] * 2,
])
def test_invalid_near_curation_fails_at_the_boundary(near):
    with pytest.raises(SchemaError, match='near'):
        parse_concept('CRY', {'near': near})


def test_approved_directions_are_complete_and_do_not_invent_reverse_relations(dictionary):
    relations = {(cid, r.concept, r.setting) for cid, c in dictionary.concepts.items() for r in c.near}
    assert len(relations) == 13
    assert sum(bool(c.near) for c in dictionary.concepts.values()) == 10
    assert ('CRY', 'NOISY_CRY', 'dinkum') in relations
    assert ('CRY', 'SULK', 'troppo') in relations
    assert not dictionary.concepts['NOISY_CRY'].near
    assert not dictionary.concepts['UNEMPLOYED'].near
    assert not dictionary.concepts['FREEDOM'].near
    for cid, c in dictionary.concepts.items():
        for r in c.near:
            assert r.concept in dictionary.concepts and r.concept != cid
            assert r.differs and r.minimum in {1, 2}


def test_exact_rate_entry_still_expresses_regard_highly(dictionary):
    assert dictionary.concepts['REGARD_HIGHLY'].near
    assert 'REGARD_HIGHLY' not in dictionary.wordless_meanings
    assert 'rate-highly' in {e.id for e in dictionary.idioms_for(('REGARD_HIGHLY',))}
