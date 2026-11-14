"""Browse-by-meaning counts use the same dictionary eligibility as entry pages."""
from collections import Counter
from dataclasses import replace
import json

import pytest

from aussiefy import Translator, list_concepts, list_entries
from aussiefy.cli import main
from aussiefy.errors import UserError
from aussiefy.schema import Entry, HOLDING_CONCEPT
from aussiefy.terms import fold


def pages(function, **options):
    rows, offset = [], 0
    while offset is not None:
        response = function(offset=offset, limit=100, **options)
        rows.extend(response['results'])
        offset = response['next_offset']
    assert response['total'] == len(rows)
    return rows


@pytest.mark.parametrize('options', [
    {'level': 1, 'vulgarity': 0}, {'level': 5, 'vulgarity': 2},
    {'level': 5, 'vulgarity': 0, 'themes': {'drinking': False}},
    {'level': 5, 'vulgarity': 2, 'include_gated': True},
])
def test_all_concept_counts_equal_the_public_entry_listing(translator, options):
    entries = pages(list_entries, translator=translator, **options)
    counts = Counter(cid for row in entries for cid in row['concepts'])
    rows = pages(list_concepts, translator=translator, **options)
    assert [row['concept'] for row in rows] == sorted(row['concept'] for row in rows)
    assert all(row['entry_count'] == counts[row['concept']] for row in rows)
    assert all(set(row) == {'concept', 'plain', 'entry_count'} and row['plain'] for row in rows)
    assert not set(translator.dictionary.wordless_meanings) & {row['concept'] for row in rows}
    assert HOLDING_CONCEPT not in {row['concept'] for row in rows}


def test_blocked_meanings_stay_at_zero_and_omissions_never_create_rows(dictionary):
    entries = {'a': Entry('a', 'alpha', ('HUNGRY',), 'adj'),
               'b': Entry('b', 'beta', ('THIRSTY',), 'adj', incoherence=5),
               'c': Entry('c', 'gamma', ('FREEDOM',), 'adj', status='omit'),
               'd': Entry('d', 'delta', ('DISHONEST',), 'adj', status='gate')}
    tr = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    low = list_concepts(level=1, translator=tr)
    assert {r['concept']: r['entry_count'] for r in low['results']} == {
        'DISHONEST': 0, 'HUNGRY': 1, 'THIRSTY': 0}
    assert low['outcome'] == 'matched'
    assert list_concepts(offset=3, translator=tr)['outcome'] == 'page_exhausted'
    held = list_concepts(level=1, include_gated=True, translator=tr)
    assert next(r for r in held['results'] if r['concept'] == 'DISHONEST')['entry_count'] == 1
    reverse = Translator(replace(tr.dictionary, entries=dict(reversed(list(entries.items())))), lookup_embedder=None)
    assert list_concepts(translator=tr) == list_concepts(translator=reverse)
    empty = Translator(replace(dictionary, entries={}), lookup_embedder=None)
    assert list_concepts(translator=empty)['outcome'] == 'nothing_fits'


@pytest.mark.parametrize('options', [{'offset': -1}, {'offset': True}, {'limit': 0},
                                    {'limit': 101}, {'limit': True}])
def test_concept_pagination_validates_like_entry_pagination(translator, options):
    with pytest.raises(UserError):
        list_concepts(translator=translator, **options)


def test_cli_concepts_returns_the_engine_page(capsys):
    assert main(['concepts', '--json', '--limit', '2', '--offset', '1', '--level', '1', '--vulgarity', '0']) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == list_concepts(limit=2, offset=1, level=1, vulgarity=0)


def test_every_ordinary_meaning_has_a_distinct_reader_name_and_search_words(dictionary):
    meanings = [c for c in dictionary.concepts.values() if c.id != HOLDING_CONCEPT]
    assert len({fold(c.plain) for c in meanings}) == len(meanings)
    for concept in meanings:
        assert concept.plain == concept.plain.strip() and 0 < len(concept.plain.split()) <= 6
        assert not any(token in concept.plain for token in (';', '{', '}', '^'))
        assert concept.search_words
        assert all(concept.id in dictionary.named_meanings[fold(word)] for word in concept.search_words)
