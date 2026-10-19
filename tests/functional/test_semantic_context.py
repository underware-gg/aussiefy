"""Meaning, arguments and tone constrain the same candidates used by drafts and plans."""

from dataclasses import replace

import pytest

from aussiefy import Translator, harness, translate
from aussiefy.detect import Detection, detect
from aussiefy.matcher import PatternIndex, compile_pattern
from aussiefy.schema import Concept, SchemaError, parse_concept
from aussiefy.select import form_problem
from aussiefy.text import tokenize


def plain(translator, source, seed=0, **kwargs):
    return translator.translate(source, level=5, vulgarity=0, seed=seed, document_type='custom',
        document_config={'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}},
        embellishment=0, **kwargs)


@pytest.mark.parametrize('source', ['I try hard to finish it.', 'I try carefully to finish it.',
    'I attempt once more to finish it.', 'I tried my very best.',
    'I try a bit harder to finish it.', 'I try the tool carefully.'])
def test_adverbial_attempts_are_not_noun_objects(source, translator):
    result = plain(translator, source)
    assert result.text == source
    assert not any('TRY_OUT' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('obj', ['it', 'the new tool', 'hard cheese', 'running carefully', 'carefully running',
    'some', 'a bit of cheese', 'a little hard cheese'])
def test_real_attempt_objects_are_kept_in_every_selected_form(obj, translator):
    seen = set()
    for seed in range(16):
        result = plain(translator, f'I try {obj}.', seed)
        attempts = [r for r in result.records if r.substituted and 'TRY_OUT' in r.det.concepts]
        assert attempts
        assert all(obj in r.output for r in attempts)
        seen.update(r.chosen.entry.id for r in attempts)
    assert 'have-a-lash' in seen


def test_fixed_wording_must_retain_the_actual_argument():
    obj = tokenize('it')[0]
    det = Detection(0, 1, ('TRY_OUT',), 'vp', 3, 'trigger', 'test', captures={'np': obj})
    assert form_problem('give {np} a burl', det) is None
    assert form_problem('give it a burl', det) is None
    assert form_problem('have a lash', det) == 'would discard {np}: it'
    assert form_problem('fit a lid', det) == 'would discard {np}: it'


def test_short_degree_or_nominal_ambiguity_is_preserved(translator):
    assert plain(translator, 'I try a little water.').text == 'I try a little water.'


@pytest.mark.parametrize('source', ['I am hungry for success.', 'I feel hungry to win.',
    'I am hungry—for success.', 'She feels hungry, for power.', 'I am hungry for lunch.'])
def test_unestablished_appetite_complements_are_preserved(source, translator):
    assert plain(translator, source).text == source


def test_complement_rules_are_generic_and_apply_to_direct_entry_triggers(dictionary):
    concepts = {**dictionary.concepts, 'BUSY': replace(dictionary.concepts['BUSY'], unless_after=('for',))}
    translator = Translator(replace(dictionary, concepts=concepts))
    result = plain(translator, 'I am very busy—for hire.')
    assert not any('BUSY' in r.det.concepts for r in result.records)
    assert any('BUSY' in r.det.concepts for r in plain(translator, 'I am very busy.').records)


@pytest.mark.parametrize('tail', ['*for success*', '[for success](https://example.com)', '`for success`'])
def test_incomplete_markdown_units_do_not_establish_appetite(translator, tail):
    source = f'I am hungry {tail}.'
    result = translate(source, translator=translator, level=5, vulgarity=0, markdown=True,
        document_type='custom', document_config={'profile': {'phonetic': 0}}, embellishment=0)
    assert result.text == source


@pytest.mark.parametrize('markup', ['markdown', 'auto', 'mdx'])
def test_opaque_complements_are_unknown_instead_of_absent(translator, markup):
    source = 'I am hungry `for success`.'
    result = translate(source, translator=translator, level=5, vulgarity=0, markup=markup,
        document_type='custom', document_config={'profile': {'phonetic': 0}}, embellishment=0)
    assert result.text == source


def test_similarity_matches_obey_the_same_meaning_boundary():
    pattern = compile_pattern('hungry', 'predicate_adj', ('APPETITE',), 3)
    concepts = {'APPETITE': Concept('APPETITE', '', {}, unless_after=('for',))}
    for text, allowed in [('I am hungryy.', True), ('I am hungryy—for success.', False)]:
        hits = detect(tokenize(text), PatternIndex([]), lambda query: {0: 1}, [pattern], concepts=concepts)
        assert bool(hits) is allowed


@pytest.mark.parametrize('raw', [{'unless_after': ['For']}, {'unless_after': [1]}])
def test_invalid_complement_rules_fail_at_the_data_boundary(raw):
    with pytest.raises(SchemaError, match='unless_after'):
        parse_concept('APPETITE', raw)


def offered(translator, source):
    result = harness.plan(source, translator=translator, level=5, vulgarity=1, document_type='custom',
        document_config={'garnish': ['riff'], 'contextual_riffs': True, 'entry_riffs': False,
            'riff_exaggeration': 2, 'profile': {'frames': [], 'phonetic': 0}})
    return {c['id']: c for group in result['riffs'] for c in group['riffs'] if 'id' in c}


@pytest.mark.parametrize('source,poss', [('I am feeling pretty hungry.', 'my'),
    ('She has been feeling hungry.', 'her'), ('Have they been feeling hungry?', 'their'),
    ('He might have been feeling hungry.', 'his'), ('I might be hungry.', 'my'),
    ('She says I am feeling hungry.', 'my')])
def test_planner_binds_supported_subjects_without_replacing_the_auxiliaries(source, poss, translator):
    images = offered(translator, source)
    assert images['stomach-throat-cut']['text'] == f"{poss} stomach thinks {poss} throat's been cut"
    assert not images['stomach-throat-cut']['automatic']
    result = plain(translator, source)
    for record in result.records:
        if record.substituted and 'HUNGRY' in record.det.concepts:
            assert record.det.captures.get('subj') is None or record.det.frame != 'vp'


@pytest.mark.parametrize('source', ['feeling hungry', 'I am not feeling hungry.',
    'She has never been feeling hungry.', 'I watched her feeling hungry.',
    'Grethel is feeling hungry.',
    'Nobody has been feeling hungry.', 'Neither child has been feeling hungry.',
    'None of us has been feeling hungry.',
    'I am hungry for success.', 'I am hungry—for success.'])
def test_no_speaker_or_positive_appetite_is_invented(source, translator):
    assert not offered(translator, source)


def test_an_unresolved_name_does_not_conflict_with_an_explicit_reflexive(translator):
    assert plain(translator, 'Little Red Riding-Hood undressed herself.').text == 'Little Red Riding-Hood undressed herself.'


def test_object_reference_can_be_realised_as_a_possessive(translator):
    result = translator.translate('She adores him.', level=5, vulgarity=2, embellishment=0)
    assert any('ADORE' in r.det.concepts for r in result.records)
    assert any('objposs' in c.entry.form for r in result.records for c in r.eligible)


def test_positive_indefinite_subjects_still_get_person_images(translator):
    assert offered(translator, 'Someone has been feeling hungry.')


def test_complement_reading_stops_at_clause_boundaries(translator):
    assert 'stomach-throat-cut' in offered(translator, 'She is hungry; to be clear, she wants lunch.')


def test_term_ranking_uses_the_existing_tone_signal(dictionary):
    source = 'He is furious.'
    base = dictionary.entries['ropeable']
    variants = [replace(base, id='tone-plain', tone='plain'), replace(base, id='tone-grim', tone='grim')]
    d = replace(dictionary, entries={e.id: e for e in variants})
    result = plain(Translator(d), source)
    candidates = {c.entry.id: c for r in result.records for c in r.eligible}
    assert candidates['tone-plain'].weight == candidates['tone-grim'].weight * 4
    assert 'tone-fit' in candidates['tone-grim'].why


def test_strict_markdown_units_share_the_documents_tone(translator):
    source = 'We consecrate and hallow this ground in solemn remembrance.\n\nHe died.'
    result = translate(source, translator=translator, markdown=True, level=5, vulgarity=1,
        document_type='custom', document_config={'profile': {'phonetic': 0}}, embellishment=0)
    assert len(result.units) >= 2
    assert all(unit.result.mood == 'solemn' for unit in result.units)
    assert not any(c.entry.tone == 'comic' for u in result.units for r in u.result.records for c in r.eligible)
