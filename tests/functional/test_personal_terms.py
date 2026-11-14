"""Per-call terms use the package word rating without entering its dictionary."""

import pytest

from aussiefy.errors import UserError
from aussiefy.personal_terms import prepare


@pytest.mark.parametrize('value', [False, {}, 'x', [{}], [{'phrase': '', 'term': 'ok'}], [{'phrase': "'quoted'", 'term': 'ok'}], [{'phrase': 'ok', 'term': "bad''"}],
    [{'phrase': 'ok', 'term': '<b>word</b>'}], [{'phrase': 'ok', 'term': '{obj}'}],
    [{'phrase': 'ok', 'term': 'word', 'vulgarity': True}],
    [{'phrase': 'ok', 'term': 'word', 'vulgarity': 4}],
    [{'phrase': 'ok', 'term': 'word', 'entry_id': 'injected'}],
    [{'phrase': 'x', 'term': 'y'}] * 51,
    [{'phrase': 'one ' * 12 + 'more', 'term': 'word'}],
    [{'phrase': 'source', 'term': 'x' * 121}],
    [{'phrase': 'SHEET', 'term': 'first'}, {'phrase': 'sheet', 'term': 'second'}],
])
def test_invalid_or_ambiguous_personal_wording_is_a_user_error(dictionary, value):
    with pytest.raises(UserError, match='personal_terms'):
        prepare(value, dictionary)


def test_free_text_rating_and_explicit_tier_are_distinct(dictionary):
    parsed = prepare([{'phrase': 'spreadsheet', 'term': 'the bloody spreadsheet'},
                      {'phrase': 'document', 'term': 'the bloody document', 'vulgarity': 0}], dictionary)
    assert parsed.provided == 2
    assert [term.vulgarity for term in parsed.items] == [1, 0]
    assert parsed.items[0].rendering_entry('np').form == 'the bloody spreadsheet'


def test_preparing_personal_terms_cannot_change_dictionary_identity_or_entries(dictionary):
    identity, entries = dictionary.identity, dict(dictionary.entries)
    raw = [{'phrase': 'spreadsheet', 'term': 'the weekly numbers'}]
    first, second = prepare(raw, dictionary), prepare(raw, dictionary)
    assert first == second and first.items[0].key.startswith('personal:')
    assert dictionary.identity == identity and dictionary.entries == entries
    assert first.items[0].rendering_entry('np').id not in entries


def test_redundant_identical_phrase_is_unambiguous_and_counts_supplied_items(dictionary):
    item = {'phrase': 'sheet', 'term': 'the numbers'}
    parsed = prepare([item, {**item, 'phrase': 'SHEET'}], dictionary)
    assert parsed.provided == 2 and len(parsed.items) == 1


@pytest.mark.parametrize('phrase,term', [("teachers' lounge", "staffroom"),
    ("working", "workin'"), ("teachers’ lounge", "staffroom"), ("working", "workin’")])
def test_ordinary_terminal_apostrophes_are_valid_personal_words(dictionary, phrase, term):
    parsed = prepare([{'phrase': phrase, 'term': term}], dictionary)
    assert parsed.items[0].term == term
