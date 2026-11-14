"""Source recognition respects grammatical reading, ambiguity and Australian wording."""

from copy import deepcopy
from dataclasses import replace

import pytest

from aussiefy.detect import read_meanings
from aussiefy.recognition import read_owned
from aussiefy.schema import parse_entry, SchemaError
from aussiefy.text import tokenize


@pytest.mark.parametrize('source,eid', [
    ('He is a bludger.', 'a-bludger-pred'),
    ('Bugger me sideways!', 'bugger-me-sideways'),
    ('We saw mozzies.', 'mozzie'),
    ('They are flat strap.', 'flat-strap-busy'),
])
def test_whole_inflected_terms_are_recognised_by_their_real_frame(dictionary, source, eid):
    tokens = tokenize(source)
    owned = read_owned(tokens, dictionary)
    assert eid in {item.entry.id for item in owned}
    item = next(item for item in owned if item.entry.id == eid)
    assert item.detection.concepts and set(item.detection.concepts) <= set(item.entry.concept)
    assert source[tokens[item.detection.start].start:tokens[item.detection.end - 1].end]


@pytest.mark.parametrize('source', ['I am puffed.', 'She wore thongs.', 'Tea is ready.',
    'The plant is rooted in the soil.'])
def test_general_or_unclear_everyday_readings_are_unmarked(dictionary, source):
    assert not read_owned(tokenize(source), dictionary)


def test_recognition_preserves_the_ordinary_readers_evidence(dictionary):
    tokens = tokenize('The American football game was a ripper.')
    readings = read_meanings(tokens, dictionary).detections
    snapshot = deepcopy(readings)
    read_owned(tokens, dictionary, readings=readings)
    assert readings == snapshot


@pytest.mark.parametrize('value', [None, False, 1, '', ' ', 'other\nsense'])
def test_other_sense_is_a_curator_note_not_an_unchecked_truthy_flag(value):
    with pytest.raises(SchemaError, match='other_sense'):
        parse_entry({'id': 'sample', 'form': 'sample', 'concept': ['TEST'], 'frame': 'np', 'other_sense': value})


def test_dial_eligibility_does_not_erase_a_source_owned_term(dictionary):
    entries = {**dictionary.entries, 'mozzie': replace(dictionary.entries['mozzie'], status='gate', vulgarity=3)}
    changed = replace(dictionary, entries=entries)
    assert 'mozzie' in {item.entry.id for item in read_owned(tokenize('We saw mozzies.'), changed)}
    omitted = replace(changed, entries={**entries, 'mozzie': replace(entries['mozzie'], status='omit')})
    assert 'mozzie' not in {item.entry.id for item in read_owned(tokenize('We saw mozzies.'), omitted)}


def test_unresolved_context_cannot_be_marked_as_an_owned_reading(dictionary):
    entry = parse_entry({'id': 'test-talent-word', 'form': 'talentword',
                         'concept': ['GIFT_TALENT'], 'frame': 'np'})
    changed = replace(dictionary, entries={**dictionary.entries, entry.id: entry})
    for source in ('He has a talentword.', 'He has a talentword for Christmas.'):
        assert entry.id not in {item.entry.id for item in read_owned(tokenize(source), changed)}
    owned = read_owned(tokenize('He has a talentword for music.'), changed)
    assert [(item.entry.id, item.detection.concepts) for item in owned] == [(entry.id, ('GIFT_TALENT',))]


@pytest.mark.parametrize('source,expected', [
    ('She was hanging out for the weekend.', 'hang-out-for'),
    ('She was hanging out to see her mates.', 'hang-out-to'),
    ('She was hanging out.', None),
    ('She was hanging out with her friends.', None),
    ('He was hanging out the washing.', None),
])
def test_owned_terms_keep_their_authored_grammar_requirements(dictionary, source, expected):
    entries = {item.entry.id for item in read_owned(tokenize(source), dictionary)}
    matches = entries & {'hang-out-for', 'hang-out-to'}
    assert matches == ({expected} if expected else set())


def test_an_ordinary_physical_stiffness_is_not_an_unlucky_reading(dictionary):
    assert 'stiff-unlucky' not in {item.entry.id for item in read_owned(tokenize('The mattress is stiff.'), dictionary)}
