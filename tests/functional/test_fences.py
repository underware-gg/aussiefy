"""Fences preserve a whole expression without making it a meaning waiting for a word."""

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.dialect import parse_dialect
from aussiefy.fences import parse_fences
from aussiefy.schema import HOLDING_CONCEPT, SchemaError
from aussiefy.text import tokenize
from aussiefy.detect import Detection, read_meanings, resolve_overlaps
from aussiefy.matcher import compile_pattern
from aussiefy.lookup import lookup
from aussiefy.engine import Translator


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
    assert 'EAGER_FOR' not in dictionary.concepts
    assert {'HEARTBREAK', 'FREEDOM', 'FEEL_SORRY', 'UNEMPLOYED', 'GET_EXCITED', 'GIFT_TALENT'} <= set(dictionary.wordless_meanings)


def test_partial_entry_cannot_discard_a_crossing_phrase_fence(dictionary):
    text = 'They repaired the road pavement.'
    tr = Translator(dictionary, lookup_embedder=None)
    result = tr.translate(text, level=5, vulgarity=3, embellishment=0, embedder='none', english='us')
    assert result.text == text
    readings = read_meanings(tokenize(text), dictionary).detections
    assert not {'ROAD', 'PAVEMENT'} & {cid for reading in readings for cid in reading.concepts}
    assert not {'footpath', 'on-the-frog-and-toad'} & {r['id'] for r in lookup(text, translator=tr)['results']}


def test_whole_phrase_entry_can_own_the_protected_expression():
    fence = parse_fences([row()])[0]
    protected = Detection(1, 3, (), 'np', 3, 'trigger', fence.phrase, source_pattern=fence.pattern)
    partial = Detection(0, 2, ('PARTIAL',), 'np', 3, 'entry', 'the petroleum')
    whole = Detection(0, 3, ('WHOLE',), 'np', 3, 'entry', 'the petroleum jelly')
    assert resolve_overlaps([partial, protected, whole]) == [whole]
    assert 'PARTIAL' not in whole.concepts


def test_reading_context_does_not_freeze_its_independent_object():
    fence = parse_fences([row(phrase='believe ?=a+liar', frame='vp')])[0]
    protected = Detection(0, 1, (), 'vp', 3, 'trigger', fence.phrase,
                          source_pattern=fence.pattern, context=(0, 3))
    object_reading = Detection(2, 3, ('LIAR',), 'np', 3, 'trigger', 'liar',
                               source_pattern=compile_pattern('liar', 'np', ('LIAR',), 3))
    assert resolve_overlaps([protected, object_reading]) == [protected, object_reading]


def test_overlapping_fences_retain_the_senses_they_ruled_out():
    first, second = parse_fences([row(), row(phrase='jelly jar')])
    left = Detection(0, 2, (), 'np', 3, 'trigger', first.phrase, source_pattern=first.pattern)
    right = Detection(1, 3, (), 'np', 3, 'trigger', second.phrase, source_pattern=second.pattern)
    component = Detection(2, 3, ('CONTAINER',), 'np', 3, 'entry', 'jar')
    kept = resolve_overlaps([left, right, component])
    assert len(kept) == 1
    assert 'CONTAINER' in kept[0].supersedes



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
