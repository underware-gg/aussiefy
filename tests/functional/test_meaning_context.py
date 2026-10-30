"""Reviewed meaning conditions retain examples and reject contextually unsupported aliases."""

import pytest

from aussiefy import Translator, load_dictionary
from aussiefy.detect import read_meanings
from aussiefy.lookup import lookup
from aussiefy.meaning_context import parse_meaning_context
from aussiefy.schema import HOLDING_CONCEPT, SchemaError
from aussiefy.text import tokenize


def test_all_reviewed_positive_and_negative_examples(dictionary):
    for cid, concept in dictionary.concepts.items():
        if not concept.negative_examples:
            continue
        for text in concept.examples:
            meanings = {c for det in read_meanings(tokenize(text), dictionary).detections for c in det.concepts}
            assert cid in meanings, (cid, text)
        for text in concept.negative_examples:
            meanings = {c for det in read_meanings(tokenize(text), dictionary).detections for c in det.concepts}
            assert cid not in meanings, (cid, text)


@pytest.mark.parametrize('cid', ['FEEL_SORRY', 'GIFT_TALENT', 'UNEMPLOYED'])
def test_unsupported_readings_do_not_invite_a_word_for_the_wrong_meaning(dictionary, cid):
    tr = Translator(dictionary, lookup_embedder=None)
    for text in dictionary.concepts[cid].negative_examples:
        result = lookup(text, translator=tr)
        assert cid not in {m['concept'] for m in result.get('meanings', [])}


@pytest.mark.parametrize('text', ['I feel terrible for my neighbour.', 'I feel bad about seeing her cry.',
                                  'She has a gift for music lovers.'])
def test_uncertain_context_cannot_fall_back_to_a_component_meaning(dictionary, text):
    tr = Translator(dictionary, lookup_embedder=None)
    result = tr.translate(text, level=5, vulgarity=3, embellishment=0, embedder='none',
                          document_type='custom', document_config={'profile': {'phonetic': 0}})
    assert result.text == text
    assert any(HOLDING_CONCEPT in r.det.concepts for r in result.records)


def test_meaning_context_is_validated_and_not_just_a_substitution_patch(data_copy):
    import yaml
    path = data_copy / 'concepts.yaml'
    raw = yaml.safe_load(path.read_text())
    raw['GIFT_TALENT']['source_context']['heads'] = ['MUSIC']
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match='source_context.heads'):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize('occasion', ['my birthday', 'her wedding', 'Christmas', 'their anniversary'])
def test_clear_occasion_evidence_restores_the_present_reading(dictionary, occasion):
    text = f'She has a gift for {occasion}.'
    meanings = {cid for d in read_meanings(tokenize(text), dictionary).detections for cid in d.concepts}
    assert 'PRESENT' in meanings and 'GIFT_TALENT' not in meanings and HOLDING_CONCEPT not in meanings


@pytest.mark.parametrize('raw', [False, {'preposition': 'for', 'argument': 'any'},
    {'preposition': 'for', 'argument': 'np', 'person': 'no'},
    {'preposition': 'about', 'argument': 'ing', 'actions': ['lie ^adj']},
    {'preposition': 'for', 'argument': 'np', 'heads': ['music'], 'not_heads': ['music']},
    {'preposition': 'for', 'argument': 'np', 'control': 'subject'}])
def test_invalid_source_context_has_a_named_error(raw):
    with pytest.raises(SchemaError, match='example:'):
        parse_meaning_context(raw, 'example')


@pytest.mark.parametrize('cid', ['FEEL_SORRY', 'GIFT_TALENT', 'FELLOW_MAN'])
def test_an_unrelated_curation_fix_preserves_meaning_metadata(tmp_path, data_copy, cid):
    from aussiefy.rounds import RoundConfig, base_dictionary, plan_round
    directory = tmp_path / 'round'
    directory.mkdir()
    (directory / 'round.yaml').write_text('name: metadata\noutput: metadata.yaml\n')
    config = RoundConfig.load(directory)
    original = base_dictionary(config, data_copy).concepts[cid]
    config.concept_fixes = {cid: {'description': original.description + ' Reviewed.'}}
    updated = plan_round(config, base_dictionary(config, data_copy)).write(data_copy).concepts[cid]
    assert updated.source_context == original.source_context
    assert updated.nominal_roles == original.nominal_roles
    assert updated.negative_examples == original.negative_examples
