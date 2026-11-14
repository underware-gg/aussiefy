"""Selection boundaries and source grammatical roles, using the real shared emitter."""

import json
from pathlib import Path

import jsonschema
import pytest

from aussiefy import suggest_selection, translate_changes

SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'aussiefy/data/selection.schema.json').read_text())
BASE = {'level': 5, 'vulgarity': 0, 'embellishment': 0, 'embedder': 'none'}


@pytest.mark.parametrize('source,span,options', [
    ('We have many dogs.', [8, 12], {}),
    ('American football game', [0, 8], {}),
    ('café', [1, 2], {}),
    ('She is exhausted and he is hungry.', [0, 31], {'level': 1}),
    ('🦘 A **spreadsheet**. `spreadsheet`', [9, 13], {'markdown': True,
        'personal_terms': [{'phrase': 'spreadsheet', 'term': 'number wrangler'}]}),
])
def test_selection_schema_regions_and_local_annotations(translator, source, span, options):
    response = suggest_selection(source, span=span, translator=translator, **(BASE | options))
    jsonschema.Draft202012Validator(SCHEMA).validate(response)
    a, b = response['src_span']
    assert 0 <= a <= b <= len(source)
    a, b = response['out_span']
    assert 0 <= a < b <= len(response['text'])
    for group in response['suggestions']:
        for option in group['options']:
            a, b = option['out_span']
            assert 0 <= a <= b <= len(response['text'])
            for mark in [*option['masks'], *option.get('parts', []), *option.get('riffs', [])]:
                a, b = mark.get('span', mark.get('out_span'))
                assert 0 <= a <= b <= len(option['rendered'])
                if 'text' in mark:
                    assert option['rendered'][a:b] == mark['text']


def test_fallback_does_not_turn_a_quantifier_into_an_adverb(translator):
    response = suggest_selection('We have many dogs.', span=[8, 12], translator=translator, **BASE)
    assert not any(option['entry_id'] == 'heaps-adv' for group in response['suggestions'] for option in group['options'])
    assert all(response['text'][:option['out_span'][0]] + option['rendered'] + response['text'][option['out_span'][1]:]
               != 'We have heaps dogs.' for group in response['suggestions'] for option in group['options'])


def test_multi_meaning_selection_has_no_combined_reading_or_closed_class_guess(translator):
    response = suggest_selection('She is exhausted and he is hungry.', span=[0, 31], translator=translator, **(BASE | {'level': 1}))
    assert response['reading'] is None
    assert {group['reading']['concept'] for group in response['suggestions'] if group['reading']} == {'TIRED', 'HUNGRY'}
    assert not any(option['entry_id'] == 'alfoil' for group in response['suggestions'] for option in group['options'])


def test_fenced_selection_and_unicode_fragments_stay_unoffered(translator):
    assert suggest_selection('American football game', span=[0, 8], translator=translator, **BASE)['outcome'] == 'left_as_written'
    result = suggest_selection('café', span=[1, 2], translator=translator, **BASE)
    assert result['out_span'] == [0, 4] and result['reading'] is None
    assert all(option['out_span'] == [0, 4] for group in result['suggestions'] for option in group['options'])


def test_selection_on_generated_garnish_returns_its_actual_choices(translator):
    source = 'The river is flowing through the valley.'
    options = BASE | {'embellishment': 2, 'vulgarity': 2, 'document_config': {'garnish': ['opener'],
        'profile': {'garnish': {'opener': 0}, 'max_garnish': {'opener': 1}, 'swearing': {'exclaim': 1}}}}
    cs = translate_changes(source, translator=translator, **options)
    change = next(change for change in cs.changes if change['kind'] == 'garnish')
    response = suggest_selection(source, span=[change['out_span'][0], change['out_span'][0] + 1], translator=translator, **options)
    group = next(group for group in response['suggestions'] if group['origin'] == 'existing')
    assert group['options'] == change['alternatives']


def test_fallback_keeps_a_whole_nominal_prepositional_complement(translator):
    response = suggest_selection('We enjoyed a meal at a pub.', span=[13, 26], translator=translator, **BASE)
    option = next(option for group in response['suggestions'] for option in group['options']
                  if option['entry_id'] == 'a-counter-meal')
    a, b = option['out_span']
    assert response['text'][:a] + option['rendered'] + response['text'][b:] == 'We enjoyed a counter meal.'



def test_standalone_auxiliary_is_not_fuzzy_substitution_content(translator):
    response = suggest_selection('She was tired.', span=[4, 7], translator=translator, **BASE)
    assert not any(option['entry_id'] in {'stuff-up', 'see-the-job-through'}
                   for group in response['suggestions'] for option in group['options'])
