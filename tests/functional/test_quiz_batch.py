"""Prepared quiz discovery must preserve scalar lookup's top-50 exclusion evidence."""
from dataclasses import replace
import importlib

import pytest

from aussiefy import Translator, meaning_quiz
from aussiefy.lookup import _LookupBatch, lookup

QUERIES = ('exhausted', 'Hungry.', 'weep', 'wholeheartedly', 'American football',
           'American football game', 'a people', 'rate it four stars', 'Quantum entanglement',
           'A very drunk person.', 'A tired person.', 'A meal at a pub.')


@pytest.mark.parametrize('backend', [None, 'bundled'])
@pytest.mark.parametrize('vulgarity', range(4))
@pytest.mark.parametrize('level,include_gated,document_type,config', [
    (1, False, 'general', None), (5, False, 'general', None),
    (5, True, 'general', {'themes': {'sex': False, 'death': False}}),
    (5, False, 'instructions', None),
])
def test_batch_ids_equal_full_scalar_discovery(dictionary, backend, vulgarity, level, include_gated, document_type, config):
    tr = Translator(dictionary, lookup_embedder=backend)
    options = dict(level=level, vulgarity=vulgarity, embellishment=0, document_type=document_type,
                   document_config=config, include_gated=include_gated)
    batch = _LookupBatch(tr, **options)
    for query in QUERIES:
        expected = {row['id'] for row in lookup(query, translator=tr, short=True, limit=50, **options)['results']}
        assert batch.entry_ids(query) == expected
        assert batch.entry_ids(query) == expected  # Repeated exclusion evidence is request-local and stable.


def test_one_quiz_uses_one_batch_without_full_card_lookups(dictionary, monkeypatch):
    module = importlib.import_module('aussiefy.lookup')
    batches = []
    class Observed(_LookupBatch):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            batches.append(self)
    monkeypatch.setattr(module, '_LookupBatch', Observed)
    def full_lookup(*args, **kwargs):
        pytest.fail('quiz called the full response/card lookup operation')
    monkeypatch.setattr(module, 'lookup', full_lookup)
    body = meaning_quiz(seed=7, translator=Translator(dictionary, lookup_embedder='bundled'), vulgarity=0)
    assert body['outcome'] == 'matched' and len(body['options']) == 4
    assert len(batches) == 1 and len(batches[0].cache) >= 4


def test_spelling_index_uses_actual_content_and_query_results_do_not_cross_requests(dictionary):
    options = dict(level=5, vulgarity=0, embellishment=0, document_type='general', document_config=None, include_gated=False)
    tr = Translator(dictionary, lookup_embedder=None)
    first, second = _LookupBatch(tr, **options), _LookupBatch(tr, **options)
    assert first.index is second.index and first.cache is not second.cache
    first.entry_ids('exhausted')
    assert not second.cache
    old = dictionary.entries['knackered']
    changed = replace(dictionary, entries={**dictionary.entries, old.id: replace(old, gloss='A violet spaceship.')})
    assert changed.identity == dictionary.identity  # Deliberately derived in memory, outside the loader.
    third = _LookupBatch(Translator(changed, lookup_embedder=None), **options)
    assert first.index is not third.index
    assert third.entry_ids('A violet spaceship.') == {row['id'] for row in lookup('A violet spaceship.',
        translator=third.translator, short=True, limit=50, **options)['results']}


def test_id_only_waiting_lookup_does_not_build_near_cards(dictionary, monkeypatch):
    from aussiefy.lookup import _LookupCards
    def rich_near(*args):
        pytest.fail('ID-only quiz discovery constructed response-only near cards')
    monkeypatch.setattr(_LookupCards, 'near', rich_near)
    batch = _LookupBatch(Translator(dictionary, lookup_embedder=None), level=5, vulgarity=0,
                        embellishment=0, document_type='general', document_config=None, include_gated=False)
    assert batch.entry_ids('wholeheartedly') == set()
