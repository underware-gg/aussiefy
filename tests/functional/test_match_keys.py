"""Source identities survive candidate expansion and never contain the caller's captured words."""

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.detect import detect, resolve_overlaps
from aussiefy.errors import UserError
from aussiefy.match_keys import detection_match, known_match, make_match_key, make_match_root, parse_match_key
from aussiefy.matcher import compile_pattern
from aussiefy.text import tokenize


def matches(source, dictionary):
    return resolve_overlaps(detect(tokenize(source), dictionary.index, concepts=dictionary.concepts,
                                  degree_index=dictionary.degree_index, person_nouns=dictionary.person_nouns))


@pytest.mark.parametrize('source', ['He is dishonest.', 'He is untrustworthy.', 'She is shattered.',
                                    'You are a good man.', 'She is hungry.', 'She is really hungry.',
                                    'She is slightly hungry.', 'He is legless.'])
def test_emitted_identity_is_a_known_dictionary_match(source, dictionary):
    found = matches(source, dictionary)
    assert found
    for det in found:
        match = detection_match(det)
        assert known_match(match.key, dictionary), match
        assert parse_match_key(match.key) == match


def test_qualifier_keeps_the_same_root(dictionary):
    def hunger(source):
        return detection_match(next(d for d in matches(source, dictionary) if 'HUNGRY' in d.concepts))
    plain, strong, mild = map(hunger, ['She is hungry.', 'She is really hungry.', 'She is slightly hungry.'])
    assert plain.root == strong.root == mild.root
    assert plain.key == plain.root
    assert strong.degree == 'strong' and mild.degree == 'mild'


def test_combining_candidates_does_not_change_the_winning_pattern_identity(dictionary):
    det = next(d for d in matches('He is dishonest.', dictionary) if 'DISHONEST' in d.concepts)
    assert {'DISHONEST', 'DODGY'} <= set(det.concepts)
    assert len(det.source_concepts) == 1
    assert known_match(detection_match(det).key, dictionary)


def test_dictionary_validation_is_separate_from_contextual_degree_derivation(dictionary):
    det = next(d for d in matches('Energy and enthusiasm.', dictionary) if 'PERSONAL_ENERGY' in d.concepts)
    root = detection_match(det).root
    assert known_match(root, dictionary)
    assert detection_match(det).degree is None
    key = make_match_key(root, degree='strong')
    assert parse_match_key(key).degree == 'strong'
    assert known_match(key, dictionary)  # dormant until a real detection emits the exact key


def test_unknown_degree_is_not_inferred_from_stylistic_intensity(dictionary):
    det = next(d for d in matches('She is really tired.', dictionary) if 'TIRED' in d.concepts)
    assert detection_match(det).degree is None  # TIRED certificates belong to the slice6 coverage review


def test_roots_are_canonical_and_do_not_expose_a_captured_person():
    root = make_match_root(('THINK', 'ACCEPT_AS_TRUE'), 'vp', 'believe ?={np}')
    assert root.startswith('ACCEPT_AS_TRUE+THINK/vp/')
    assert 'believe' not in root
    assert make_match_key(root, degree='unmarked') == root


@pytest.mark.parametrize('suffix', [';degree=unmarked', ';degree=unknown', ';tone=solemn',
                                     ';degree=strong;degree=mild'])
def test_noncanonical_or_unknown_qualifiers_are_rejected(suffix):
    root = make_match_root(('HUNGRY',), 'predicate_adj', 'hungry')
    with pytest.raises(UserError):
        parse_match_key(root + suffix)


@pytest.mark.parametrize('conflict', [False, True])
def test_co_matching_patterns_share_detection_degree_evidence(tmp_path, conflict):
    degrees = {'zzword|zzother': 'strong' if conflict else 'unmarked'}
    if conflict:
        degrees['zzword'] = 'unmarked'
    path = tmp_path / 'source-alternatives.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'ZZ_SCALE': {'description': 'A synthetic graded state.',
            'triggers': {'predicate_adj': ['zzword', 'zzword|zzother']},
            'trigger_degrees': {'predicate_adj': degrees}}}}))
    dictionary = load_dictionary([path])
    found = [next(d for d in matches(source, dictionary) if 'ZZ_SCALE' in d.concepts)
             for source in ['She is zzword.', 'She is really zzword.', 'She is slightly zzword.']]
    keys = [detection_match(det) for det in found]
    assert len({key.root for key in keys}) == 1
    assert all(known_match(key.key, dictionary) for key in keys)
    assert [key.degree for key in keys] == ([None] * 3 if conflict else [None, 'strong', 'mild'])


def test_an_unknown_authored_root_is_rejected(dictionary):
    assert not known_match(make_match_root(('HUNGRY',), 'predicate_adj', 'not an authored pattern'), dictionary)


@pytest.mark.parametrize('source', ['I believe the stories people tell.', 'I believe the bus driver lied.',
                                    'He thought nothing of her.'])
def test_an_unresolved_reading_never_names_a_rejected_meaning(source, dictionary):
    det = next(d for d in matches(source, dictionary) if d.concepts == ('UNRESOLVED_SENSE',))
    assert detection_match(det) is None


@pytest.mark.parametrize('source,wanted,excluded', [
    ('Fantastic terrors.', 'FANCIFUL', 'EXCELLENT'),
    ('She does not think the world of herself.', 'REGARD_HIGHLY', 'CONCEITED')])
def test_a_contextual_winner_does_not_key_the_superseded_reading(source, wanted, excluded, dictionary):
    det = next(d for d in matches(source, dictionary) if wanted in d.concepts)
    key = detection_match(det)
    assert key and key.root.split('/')[0] == wanted and excluded in det.supersedes
    assert known_match(key.key, dictionary)


@pytest.mark.parametrize('left,right,frame', [
    ('believe ?={np}', 'believe ?={ing}', 'vp'),
    ('think ?=what|how', 'think ?=what|how ^start', 'vp'),
    ('?<=only think ?=what|how ^start', '?<=not think ?=what|how ^start', 'vp'),
    ('drunk', 'drunk ^person', 'predicate_adj')])
def test_context_constraints_are_part_of_pattern_identity(left, right, frame):
    left, right = (compile_pattern(text, frame, ('TEST',), 3) for text in (left, right))
    assert make_match_root(('TEST',), frame, left) != make_match_root(('TEST',), frame, right)


def test_equivalent_pattern_spelling_and_intensity_do_not_rekey_the_meaning():
    assert make_match_root(('THINK',), 'vp', 'BELIEVE   ?={np}@5') == make_match_root(
        ('THINK',), 'vp', 'believe ?={np}@3')


def test_dictionary_context_keys_never_include_a_captured_name(dictionary):
    keys = [detection_match(next(d for d in matches(source, dictionary) if 'ACCEPT_AS_TRUE' in d.concepts))
            for source in ['I believe Mavis.', 'I believe Aloysius.']]
    assert keys[0] == keys[1] and keys[0] is not None
    assert 'mavis' not in keys[0].key.lower() and 'aloysius' not in keys[0].key.lower()


def test_a_context_restriction_removes_its_sense_from_the_key(tmp_path):
    path = tmp_path / 'source-senses.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {
            'ZZ_ALLOWED': {'description': 'An allowed synthetic reading.'},
            'ZZ_EXCLUDED': {'description': 'A restricted synthetic reading.', 'unless_after': ['for']}},
        'add_entries': [{'id': 'zz-senses', 'form': 'zzform', 'concept': ['ZZ_ALLOWED', 'ZZ_EXCLUDED'],
                         'frame': 'predicate_adj', 'replaces': ['zzsource']}]}))
    dictionary = load_dictionary([path])
    det = next(d for d in matches('She is zzsource for now.', dictionary) if 'ZZ_ALLOWED' in d.concepts)
    assert 'ZZ_EXCLUDED' not in det.concepts and 'ZZ_EXCLUDED' in det.source_concepts
    key = detection_match(det)
    assert key and key.root.startswith('ZZ_ALLOWED/') and known_match(key.key, dictionary)
