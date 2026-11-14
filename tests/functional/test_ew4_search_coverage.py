"""Every stored term has an honest, scoped search record; documentary witnesses stay distinct."""

from collections import Counter
import json
from pathlib import Path


def test_ew4_annotations_cover_terms_retain_scoped_historical_search_dates(dictionary):
    ledger = json.loads((Path(__file__).parents[2] / 'research/gate4-evidence-2026-11-14/searched-reconciliation.json').read_text())
    terms = [*dictionary.entries.values(), *(r for e in dictionary.entries.values() for r in e.riffs), *dictionary.imagery]
    assert len(terms) == 1409 and all(t.searched for t in terms)
    assert len(ledger['proposals']) == 1369 and len(ledger['preserved']) == 40 and not ledger['remaining']
    assert Counter((r['kind'], r['id'], r.get('text', '')) for r in ledger['proposals']).most_common(1)[0][1] == 1
    followthrough = json.loads((Path(__file__).parents[2] / 'research/gate4-evidence-2026-11-14/followthrough-integration.json').read_text())
    overrides = {r['id']: r['after'] for r in followthrough['search_overrides']}
    assert len(overrides) == 125
    for r in ledger['proposals']:
        e = dictionary.entries[r['id']]
        term = e if r['kind'] == 'entry' else next(x for x in e.riffs if x.text == r['text'])
        expected = overrides.get(r['id'], r) if r['kind'] == 'entry' else r
        assert term.searched.date == expected['date'] and term.searched.outcome == expected['outcome']
    assert dictionary.entries['properly-adv'].searched.outcome == 'inconclusive'
    assert dictionary.entries['hang-out-for'].searched.date == '2026-10-27'
    assert dictionary.entries['puffed'].searched.date == '2026-11-14'
    assert dictionary.entries['running-on-smell-oily-rag'].searched.outcome == 'inconclusive'
