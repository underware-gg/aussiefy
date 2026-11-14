"""Real v4 emission, source ownership and request-local wording across the shared pass."""

import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from aussiefy import Translator, translate_changes
from aussiefy.selection import suggest_selection
from aussiefy.v3_contract import validate_response

BASE = {'level': 1, 'vulgarity': 0, 'embellishment': 0, 'embedder': 'none'}
SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'aussiefy/data/changes.schema.json').read_text())


def checked(translator, source, **options):
    result = translate_changes(source, translator=translator, **(BASE | options))
    jsonschema.Draft202012Validator(SCHEMA).validate(result.to_dict())
    validate_response(result.to_dict(), source, translator.dictionary, result_warnings=result.result.warnings)
    return result


@pytest.mark.parametrize('level', [1, 3, 5])
def test_source_swears_are_kept_exact_and_unmasked_at_nan(translator, level):
    source = 'Bugger me sideways!'
    result = checked(translator, source, level=level, embellishment=2)
    kept = next(change for change in result.changes if change['kind'] == 'kept')
    assert kept['original'] == kept['output'] == 'Bugger me sideways'
    assert not kept['masks']
    own = next(option for option in kept['alternatives'] if option['key'] == kept['option_key'])
    assert own['kind'] == 'source' and not own['masks']
    assert all(option['vulgarity'] == 0 for option in kept['alternatives'] if option['kind'] != 'source')
    assert kept['alternatives'][-1]['kind'] == 'plain'
    assert kept['alternatives'][-1]['weight'] == 0


def test_only_wordless_readings_are_held(translator):
    result = checked(translator, 'She wept. She was exhausted.')
    assert [(c['original'], c['reading']['concept']) for c in result.changes if c['kind'] == 'held'] == [('wept', 'CRY')]
    held = next(c for c in result.changes if c['kind'] == 'held')
    assert held['output'] == held['original'] and held['option_key'] is None
    assert not held['alternatives'] and not held['locked'] and not held['masks']


def test_source_marking_does_not_spend_usage_or_shift_another_roll(dictionary):
    ordinary = replace(dictionary, entries={key: replace(entry, reads_as='general')
                                            for key, entry in dictionary.entries.items()})
    source = 'We saw mozzies. She was exhausted.'
    for seed in range(5):
        marked = Translator(dictionary, lookup_embedder=None).translate(source, seed=seed, **BASE)
        plain = Translator(ordinary, lookup_embedder=None).translate(source, seed=seed, **BASE)
        def tired(result):
            return [(record.roll, record.p, record.output) for record in result.records if 'TIRED' in record.det.concepts]
        assert tired(marked) == tired(plain)


@pytest.mark.parametrize('source,terms,expected,applied', [
    ('The cats chased a cat.', [{'phrase': 'cat', 'term': 'moggie'}], 'The moggies chased a moggie.', 2),
    ('She adores Jane.', [{'phrase': 'adore Jane', 'term': 'love the boss'}], 'She loves the boss.', 1),
    ('He saw a big widget.', [{'phrase': 'big widget', 'term': 'bloody gadget'},
                            {'phrase': 'widget', 'term': 'gadget'}], 'He saw a big gadget.', 1),
    ('Rob saw Rob.', [{'phrase': 'Rob', 'term': 'the boss'}], 'The boss saw the boss.', 2),
])
def test_personal_terms_are_literal_request_choices_not_dictionary_entries(translator, source, terms, expected, applied):
    result = checked(translator, source, personal_terms=terms)
    assert result.text == expected
    assert result.result.personal_terms == {'provided': len(terms), 'applied': applied}
    assert all(c['entry_id'] is None and c['evidence'] is None and c['coined_by'] is None
               for c in result.changes if c['kind'] == 'personal')
    assert not any(key.startswith('personal') for key in result.entries)
    assert result.result.tuning == {'popularity': False, 'preferences': 0}
    assert all(not p.get('target', {}).get('entry_id', '').startswith('personal')
               for p in result.result.replay_pins()['picks'])


def test_document_personal_hook_is_once_per_call_and_code_stays_literal(translator):
    calls = []
    def hook(**dials):
        calls.append(dials)
        return [{'phrase': 'spreadsheet', 'term': 'number wrangler'}]
    result = checked(translator, 'A spreadsheet.\n\n`spreadsheet`\n\nAnother spreadsheet.',
                     markdown=True, _personal_terms_hook=hook)
    assert len(calls) == 1
    assert result.result.personal_terms == {'provided': 1, 'applied': 2}
    assert result.text == 'A number wrangler.\n\n`spreadsheet`\n\nAnother number wrangler.'


def test_selection_maps_back_through_a_personal_edit(translator):
    result = suggest_selection('A spreadsheet.', span=[4, 8], translator=translator, **BASE,
                              personal_terms=[{'phrase': 'spreadsheet', 'term': 'number wrangler'}])
    assert result['src_span'] == [0, 13] and result['out_span'] == [0, 17]
    assert result['text'] == 'A number wrangler.'
    assert result['suggestions'][0]['options'][0]['kind'] == 'personal'


def test_selection_distinguishes_passed_over_kept_and_wordless(translator):
    for source, span, origin, concept, outcome in [
        ('She is exhausted.', [8, 12], 'passed_over', 'TIRED', 'matched'),
        ('He is a bludger.', [9, 12], 'kept', 'LAZY', 'matched'),
        ('She wept.', [5, 7], 'lookup', 'CRY', 'no_word_yet'),
    ]:
        response = suggest_selection(source, span=span, translator=translator, **BASE)
        assert response['outcome'] == outcome
        assert response['suggestions'][0]['origin'] == origin
        assert response['reading']['concept'] == concept


def test_ruled_out_words_are_real_at_spot_options(translator):
    result = checked(translator, 'He believes a liar.', level=5, embellishment=2)
    words = [word for change in result.changes for reading in change['ruled_out'] for word in reading['words']]
    assert any('reckon' in word['rendered'] for word in words)
    assert all(0 <= word['weight'] <= 1 for word in words)
    assert all(word['entry_id'] in result.entries for word in words if word['entry_id'])


@pytest.mark.parametrize('source,wordings', [
    ('He is stonkered.', {'drunk', 'tired'}),
    ('They flogged my car.', {'sold', 'stole'}),
    ('I am full as a goog.', {'very drunk', 'full after eating'}),
])
def test_ambiguous_australian_forms_keep_all_supported_senses(translator, source, wordings):
    result = checked(translator, source)
    kept = next(change for change in result.changes if change['kind'] == 'kept')
    assert kept['reading'] is None and 'match' not in kept
    assert {option['rendered'] for option in kept['alternatives'] if option['kind'] == 'plain'} == wordings


@pytest.mark.parametrize('source,plain', [
    ('He is taking the piss out of her.', 'making fun of her'),
    ('They were taking the piss.', 'They were teasing'),
    ('He bends her ear.', 'talks at length to her'),
    ('He is off his face.', 'very drunk'),
])
def test_plain_choices_preserve_bound_people_tense_and_degree(translator, source, plain):
    result = checked(translator, source)
    assert any(option['rendered'] == plain for change in result.changes
               for option in change['alternatives'] if option['kind'] == 'plain')


@pytest.mark.parametrize('preserve', [False, True])
def test_whole_sentence_rewrites_preserve_and_relocate_owned_literals(translator, preserve):
    from aussiefy.protected import protected_runs
    class Rewrite:
        model = 'offline-test'
        def rewrite(self, original, draft, planned, **settings):
            return ('Everyone is ' + protected_runs(draft)[0] + '.' if preserve else 'Everyone is working.'), 'ok'
    result = translator.translate('Widget.', level=5, vulgarity=0, embellishment=2, embedder='none',
        rewrite_mode='all', rewriter=Rewrite(), personal_terms=[{'phrase': 'widget', 'term': 'working'}])
    assert "workin'" not in result.text
    assert result.rewrites[0].outcome == ('applied' if preserve else 'fell_back')
    assert result.text.startswith('Everyone is Working.' if preserve else 'Working.')


@pytest.mark.parametrize('preserve', [True, False])
def test_surface_rewrite_protects_owned_words_after_phonetic_offsets(translator, monkeypatch, preserve):
    from aussiefy import llm
    from aussiefy.protected import INLINE_RUN
    import re
    result = translator.translate('I was working with a widget. She was exhausted.',
        level=5, vulgarity=0, embellishment=0, embedder='none',
        personal_terms=[{'phrase': 'widget', 'term': 'working'}])
    owned = [result.text[a:b] for a, b in result._owned_spans]
    assert owned == ['a working']
    before = result.text
    def reply(*args, **kwargs):
        payload = json.loads(kwargs['prompt'])
        assert 'working' not in payload['PLANNED']
        assert re.search(INLINE_RUN, payload['DRAFT'])
        return {'text': 'Yes, ' + (payload['DRAFT'] if preserve else re.sub(INLINE_RUN, 'changed', payload['DRAFT']))}
    monkeypatch.setattr(llm.claude, 'call_json', reply)
    llm.surface_rewrite(result, client=object(), translator=translator)
    assert result.surface['outcome'] == ('applied' if preserve else 'fell_back')
    assert result.text == ('Yes, ' + before if preserve else before)
    assert [result.text[a:b] for a, b in result._owned_spans] == owned
    personal = next(row for row in result.decisions()['substitutions'] if row['kind'] == 'personal')
    assert personal['entry'] is None and personal['key'].startswith('personal:')


def test_sentence_rewriter_does_not_require_hidden_personal_words_in_plan(translator):
    from aussiefy.llm import ClaudeRewriter
    from conftest import FakeClaude, json_reply
    from aussiefy.literal_spans import mask_literals
    draft = mask_literals('This is working.', [(8, 15)]).text
    writer = ClaudeRewriter(client=FakeClaude(json_reply({'text': draft})), cache=False, translator=translator)
    result = translator.translate('This is a widget.', level=5, embellishment=0, vulgarity=0,
        embedder='none', rewrite_mode='all', rewriter=writer,
        personal_terms=[{'phrase': 'a widget', 'term': 'working'}])
    assert result.text == 'This is working.'
    assert result.rewrites[0].outcome == 'applied'


def test_owned_inner_word_cannot_overturn_a_larger_settled_source_meaning(translator):
    source = 'My friend works at the service station.'
    result = checked(translator, source, level=5, seed=0)
    assert not any(change['kind'] == 'kept' and change['original'] == 'station' for change in result.changes)
    assert any('SERVICE_STATION' in record.det.concepts for record in result.result.records)


@pytest.mark.parametrize('fault', ['meaning', 'plain_name', 'headword', 'masked_source', 'source_region', 'fake_literal_card', 'key_prefix'])
def test_semantic_checks_reject_invalid_owned_choice_contracts(translator, fault):
    from copy import deepcopy
    from aussiefy.errors import SchemaError
    result = checked(translator, 'Bugger me sideways!')
    body = deepcopy(result.to_dict())
    kept = next(change for change in body['changes'] if change['kind'] == 'kept')
    source = next(option for option in kept['alternatives'] if option['kind'] == 'source')
    plain = next(option for option in kept['alternatives'] if option['kind'] == 'plain')
    if fault == 'meaning':
        kept['reading']['concept'] = 'UNKNOWN_CONCEPT'
    elif fault == 'plain_name':
        kept['reading']['plain'] = 'internal label'
    elif fault == 'headword':
        body['entries'][kept['entry_id']]['headword_key'] = 'different'
    elif fault == 'masked_source':
        kept['masks'] = [{'span': [0, 6], 'ending_start': 6, 'vulgarity': 1}]
    elif fault == 'source_region':
        source['out_span'] = [0, 1]
    elif fault == 'fake_literal_card':
        plain['entry_id'] = kept['entry_id']
    elif fault == 'key_prefix':
        source['key'] = 'entry:' + source['entry_id']
    with pytest.raises(SchemaError):
        validate_response(body, 'Bugger me sideways!', translator.dictionary, result_warnings=result.result.warnings)


def test_semantic_checks_reject_an_invented_near_relation(translator):
    from copy import deepcopy
    from aussiefy.errors import SchemaError
    result = checked(translator, 'She loved him wholeheartedly.', level=5, embellishment=2, seed=0,
        document_config={'garnish': [], 'profile': {'phonetic': 0, 'stack': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    body = deepcopy(result.to_dict())
    change = next(change for change in body['changes'] if change.get('near'))
    change['near']['differs'] = 'A made-up relation'
    with pytest.raises(SchemaError):
        validate_response(body, 'She loved him wholeheartedly.', translator.dictionary, result_warnings=result.result.warnings)



def test_explicit_ruled_out_pick_preserves_inferred_and_selected_readings(translator):
    source = 'He believes a liar.'
    original = checked(translator, source, level=5)
    held = next(change for change in original.changes if change['kind'] == 'held')
    reading = next(row for row in held['ruled_out'] if row['concept'] == 'THINK')
    word = next(word for word in reading['words'] if word['entry_id'] == 'reckon')
    pins = original.replay_pins({held['id']: word['key']})
    selected = checked(translator, source, level=5, pins=pins)
    change = next(change for change in selected.changes if change.get('selected_reading'))
    assert change['reading'] == held['reading']
    assert change['selected_reading'] == {'concept': 'THINK', 'plain': translator.dictionary.concepts['THINK'].plain}
    assert change['entry_id'] == 'reckon' and 'reckons' in selected.text
    assert translate_changes(source, translator=translator, **(BASE | {'level': 5, 'pins': selected.replay_pins()})).text == selected.text



def test_held_marker_keeps_words_exact_while_existing_suffix_imagery_stays_outside(translator):
    result = checked(translator, 'He was working in vain.', level=5, document_type='custom',
        document_config={'garnish': ['riff'], 'contextual_riffs': True, 'entry_riffs': False,
            'riff_exaggeration': 2, 'riff_association': 1,
            'profile': {'frames': [], 'phonetic': 0, 'garnish': {'riff': 1}, 'max_garnish': {'riff': 3}, 'garnish_gap': 0}})
    held = next(change for change in result.changes if change['kind'] == 'held')
    assert held['output'] == held['original'] and not held['masks']
    assert result.text == 'He was working in vain, like a bloke sweeping dust in a sandstorm.'
    assert any(change.get('image_id') == 'sandstorm-sweeper' for change in result.changes)



@pytest.mark.parametrize('source', ['She bought a Barbie doll.', 'She bought a barbie doll.',
    'Barbie won the award.', 'We drove past the railway station.',
    'We drove past the railway stations.', 'They visited the police stations.', 'The flat strap held the load.',
    'They tied a flat strap.', 'They tied a flat-strap.'])
def test_source_owned_controls_keep_other_senses_unlabelled(translator, source):
    result = checked(translator, source)
    assert not any(change['kind'] == 'kept' for change in result.changes)
    assert result.text == source


@pytest.mark.parametrize('source', ['He works on a station.', 'She ran flat strap.', 'She was flat strap.'])
def test_source_owned_controls_retain_ordinary_australian_uses(translator, source):
    assert any(change['kind'] == 'kept' for change in checked(translator, source).changes)
