"""Retained phase-B cases: forbidden candidate exposure and functioning positive controls differ."""

import json
from pathlib import Path

import pytest

from aussiefy import Translator

DATA = Path(__file__).parents[1] / 'corpus' / 'ed16'
CASES = json.loads((DATA / 'phase-b-labels.json').read_text())['cases']
CONTROLS = json.loads((DATA / 'phase-b-controls.json').read_text())


@pytest.fixture(scope='module')
def engine(dictionary):
    return Translator(dictionary, lookup_embedder=None)


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_retained_phase_b_case(engine, case):
    result = engine.translate(case['text'], level=5, vulgarity=3, embellishment=0, seed=0, embedder='none')
    if case['expect'] == 'must_not_swap_meaning':
        for record in result.records:
            if record.span[0] >= case['span'][1] or record.span[1] <= case['span'][0]:
                continue
            assert not any(set(candidate.entry.concept) & set(case['bad_concepts']) for candidate in record.eligible)
    elif case['expect'] == 'must_allow_meaning':
        baseline = CONTROLS[case['id']]
        eligible = {candidate.entry.id for record in result.records for candidate in record.eligible}
        if case['id'] == 'control-beer-garden':
            start = case['text'].lower().index('beer garden')
            end = start + len('beer garden')
            assert 'beer garden' in result.text.lower() or any(r.substituted and r.det.frame == 'np'
                and r.span[0] <= start and end <= r.span[1] for r in result.records)
        elif baseline['eligible']:
            assert eligible & set(baseline['eligible'])
        else:
            # Eleven historical controls never had an eligible word. Preserve their observed meaning
            # recognition; do not count them as successful substitutions. E2 permits unchanged beer garden.
            meanings = {cid for record in result.records for cid in record.det.concepts}
            assert set(baseline['concepts']) <= meanings
    else:
        assert case['expect'] == 'preserve_argument'
        assert case['argument'] in result.text
