"""Fences preserve a whole expression without making it a meaning waiting for a word."""

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.dialect import parse_dialect
from aussiefy.fences import parse_fences
from aussiefy.schema import HOLDING_CONCEPT, SchemaError
from aussiefy.text import tokenize


def row(**changes):
    return {'phrase': 'petroleum jelly', 'frame': 'np', 'kind': 'set_phrase',
            'scope': {'meanings': True, 'dialect': ['unknown', 'us', 'uk'], 'not_in': []},
            'reason': 'Petroleum jelly is an ointment, not jam.', **changes}


@pytest.mark.parametrize('changes', [
    {'kind': 'guard'}, {'reason': ''}, {'scope': {}}, {'frame': 'noun'},
    {'scope': {'meanings': 'yes', 'dialect': [], 'not_in': []}},
    {'scope': {'meanings': False, 'dialect': [], 'not_in': []}},
    {'scope': {'meanings': False, 'dialect': ['auto'], 'not_in': []}},
    {'scope': {'meanings': True, 'dialect': ['us', 'us'], 'not_in': []}},
    {'scope': {'meanings': True, 'dialect': [], 'not_in': ['techincal']}},
])
def test_fences_require_complete_valid_copy_and_scope(changes):
    with pytest.raises(SchemaError, match='fences.yaml'):
        parse_fences([row(**changes)])


def test_duplicates_must_combine_scopes():
    with pytest.raises(SchemaError, match='duplicate fence'):
        parse_fences([row(), row(scope={'meanings': False, 'dialect': ['us'], 'not_in': []})])


def test_fences_cannot_repeat_dialect_swaps():
    with pytest.raises(SchemaError, match='self-swaps belong in fences.yaml'):
        parse_dialect({'us': {'petroleum jelly': 'petroleum jelly'}})
    with pytest.raises(SchemaError, match='repeats a dialect fence'):
        parse_dialect({'us': {'petroleum jelly': 'ointment'}}, parse_fences([row()]))


@pytest.mark.parametrize('english,domain,guarded', [('us', 'general', True), ('uk', 'general', False),
                                                  (None, 'general', False), ('us', 'technical', False)])
def test_dialect_fences_keep_their_english_and_document_conditions(english, domain, guarded):
    fences = parse_fences([row(scope={'meanings': False, 'dialect': ['us'], 'not_in': ['technical']})])
    table = parse_dialect({'us': {'jelly': 'jam'}}, fences)
    hits = table.find(tokenize('petroleum jelly'), english, domain)
    assert [h.text for h in hits] == ([] if guarded else ['jam'])


@pytest.mark.parametrize('english', [None, 'us', 'uk'])
def test_migrated_dialect_fences_preserve_observed_scope(dictionary, english):
    assert dictionary.dialect.find(tokenize('petroleum jelly'), english, 'general') == []


def test_meaning_fence_does_not_disable_a_legitimate_dialect_swap(dictionary):
    hits = dictionary.dialect.find(tokenize('parking lots'), 'us', 'general')
    assert [h.text for h in hits] == ['car parks']


def test_core_concepts_are_meanings_and_one_named_abstention(dictionary):
    assert not {'WEB_COOKIE', 'A_PEOPLE', 'FELLOW_BEFORE_NAME'} & dictionary.concepts.keys()
    assert HOLDING_CONCEPT not in dictionary.wordless_meanings
    assert not dictionary.concepts[HOLDING_CONCEPT].no_entries
    assert {c.id for c in dictionary.concepts.values() if c.no_entries} == {
        'HEARTBREAK', 'FREEDOM', 'FEEL_SORRY', 'UNEMPLOYED', 'GET_EXCITED', 'GIFT_TALENT', 'EAGER_FOR'}


def test_deliberate_partial_entry_overlaps_are_reported_across_frames(dictionary):
    assert any(w.startswith('dogs-breakfast:') for w in dictionary.warnings)
    assert any(w.startswith('down-in-the-dumps:') for w in dictionary.warnings)


def test_fence_entry_overlap_is_allowed_but_reported(data_copy):
    path = data_copy / 'fences.yaml'
    rows = yaml.safe_load(path.read_text())
    rows.append(row(phrase='extremely busy@4', frame='predicate_adj'))
    path.write_text(yaml.safe_dump(rows))
    (data_copy / 'entries' / 'fence-test.yaml').write_text(yaml.safe_dump([
        {'id': 'fence-test', 'form': 'busy as a test', 'concept': ['BUSY'], 'frame': 'predicate_adj',
         'replaces': ['extremely busy@4']}]))
    dictionary = load_dictionary(data_dir=data_copy)
    assert any('overlaps a phrase fence' in warning for warning in dictionary.warnings)
