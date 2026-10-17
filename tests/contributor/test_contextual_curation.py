"""Follow-up dispositions cover frozen earlier rows and resolve every promoted reference."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT/'research/vocabulary-2026-10-17'


def test_all_previously_unadded_candidates_have_specific_follow_up_dispositions(dictionary):
    original = yaml.safe_load((RESEARCH/'decisions.yaml').read_text())
    pending = {r['id']:r for r in original if r['decision'] in ('not_added', 'rejected')}
    rows = yaml.safe_load((RESEARCH/'contextual-decisions.yaml').read_text())
    assert len(rows) == len(pending) == 163
    assert {r['id'] for r in rows} == pending.keys()
    images = {i.id for i in dictionary.imagery}
    for row in rows:
        assert row['phrase'] == pending[row['id']]['phrase']
        assert row['previous_decision'] == pending[row['id']]['decision']
        assert len(row['reason']) >= 60
        assert row['decision'] in {'entry', 'image', 'covered', 'craft'}
        if row['decision'] in {'entry', 'covered'}:
            assert row['target'] in dictionary.entries
        if row['decision'] == 'image':
            assert row['target'] in images
    corrected = next(r for r in rows if r['id'] == 'uncle_bob-22')
    assert dictionary.entries[corrected['target']].concept == ('DISHONEST',)
