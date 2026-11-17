"""Site-reviewed v4 contract amendments and explicit plain-source replay."""
import asyncio
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from aussiefy import suggest_selection, translate_changes
from aussiefy.cards import short_card
from aussiefy.errors import UserError
from aussiefy.mcp_server import build_server

BASE = {'level': 5, 'vulgarity': 0, 'embellishment': 0, 'embedder': 'none'}
SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'aussiefy/data/selection.schema.json').read_text())


def test_mixed_selection_explains_each_group_at_its_own_dials(translator):
    body = suggest_selection('She is exhausted and he is hungry.', span=[0, 31], translator=translator, **(BASE | {'level': 1}))
    Draft202012Validator(SCHEMA).validate(body)
    groups = {group['reading']['concept']: group for group in body['suggestions'] if group['reading']}
    assert body['outcome'] == 'matched'
    assert groups['TIRED']['outcome'] == 'matched'
    assert groups['HUNGRY']['outcome'] == 'outside_dials'
    assert groups['HUNGRY']['options'] == []
    assert all('locked' in group and 'outcome' in group for group in body['suggestions'])
    waiting = suggest_selection('Loyalty.', span=[0, 7], translator=translator, **BASE)
    assert waiting['suggestions'][0]['outcome'] == 'no_word_yet'


def test_selection_locks_use_the_change_contract_and_local_coordinates(translator):
    source = 'She is exhausted.'
    cs = translate_changes(source, translator=translator, **BASE)
    body = suggest_selection(source, span=[0, len(cs.text)], translator=translator, **BASE)
    Draft202012Validator(SCHEMA).validate(body)
    assert any(group['locked'] for group in body['suggestions'])
    for group in body['suggestions']:
        for option in group['locked']:
            assert 'weight' not in option and option['vulgarity'] > 0
            assert option['entry_id'] in cs.entries
            assert 0 <= option['out_span'][0] <= option['out_span'][1] <= len(body['text'])
            for mask in option['masks']:
                assert 0 <= mask['span'][0] <= mask['ending_start'] <= mask['span'][1] <= len(option['rendered'])


def test_kept_selection_drops_entry_that_repeats_the_source(translator):
    source = "He's a bludger."
    cs = translate_changes(source, translator=translator, **BASE)
    body = suggest_selection(source, span=[0, len(cs.text)], translator=translator, **BASE)
    group = next(group for group in body['suggestions'] if group['origin'] == 'kept')
    own = next(option for option in group['options'] if option['kind'] == 'source')
    a, b = own['out_span']
    owned_text = body['text'][:a] + own['rendered'] + body['text'][b:]
    for option in group['options'] + group['locked']:
        if option['kind'] != 'entry':
            continue
        a, b = option['out_span']
        assert body['text'][:a] + option['rendered'] + body['text'][b:] != owned_text


@pytest.mark.parametrize('source', ['Stop complaining.', 'They were arguing.'])
def test_null_target_replays_and_recaptures_the_exact_plain_source(translator, source):
    options = BASE | {'embellishment': 2, 'seed': 0, 'document_config': {'garnish': []}}
    cs = translate_changes(source, translator=translator, **options)
    change = next(change for change in cs.changes if change['kind'] == 'substitution')
    plain = next(option for option in change['alternatives'] if option['key'] == 'plain:source')
    pins = cs.replay_pins({change['id']: 'plain:source'})
    assert next(pick for pick in pins['picks'] if pick['kind'] == 'substitution')['target'] is None
    replay = translate_changes(source, pins=pins, translator=translator, **options)
    a, b = plain['out_span']
    assert replay.text == cs.text[:a] + plain['rendered'] + cs.text[b:]
    assert translate_changes(source, pins=replay.replay_pins(), translator=translator, **options).text == replay.text


def test_near_names_are_authored_on_the_change_and_each_option(translator):
    cs = translate_changes('She loved him wholeheartedly.', translator=translator,
        **(BASE | {'embellishment': 2, 'seed': 0, 'document_config': {'garnish': [], 'profile': {'phonetic': 0,
             'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}}))
    owners = [owner for change in cs.changes for owner in [change, *change['alternatives']] if owner.get('near')]
    assert owners
    for owner in owners:
        assert owner['near']['plain'] == translator.dictionary.concepts[owner['near']['concept']].plain


@pytest.mark.parametrize('limit', [60, None])
def test_host_can_raise_or_remove_its_own_personal_hook_cap(translator, limit):
    terms = [{'phrase': f'widget{i}', 'term': f'gadget{i}'} for i in range(51)]
    calls = []
    def hook(**dials):
        calls.append(dials)
        return terms
    server = build_server(translator=translator, personal_terms_hook=hook, max_personal_terms=limit)
    args = {'text': 'The widget50.', 'level': 1, 'vulgarity': 0, 'embellishment': 0}
    result = asyncio.run(server.call_tool('aussie_translate', args)).structured_content
    assert result['personal_terms'] == {'provided': 51, 'applied': 1}
    assert result['text'] == 'The gadget50.' and len(calls) == 1
    from aussiefy.personal_terms import prepare
    with pytest.raises(UserError, match='50'):
        prepare(terms, translator.dictionary)


def test_terminal_period_is_omitted_from_the_key_without_renaming_a_form(dictionary):
    entries = [entry for entry in dictionary.entries.values() if entry.form == 'fair dinkum.']
    assert entries
    assert all(short_card(entry)['headword_key'] == 'fair dinkum' and entry.form == 'fair dinkum.' for entry in entries)


def test_withheld_alternatives_cannot_be_selected_through_a_hidden_plain_pin(translator, monkeypatch):
    from aussiefy.changes import _Builder, PICK_DIFFERS
    monkeypatch.setattr(_Builder, '_withheld', lambda *args: PICK_DIFFERS)
    cs = translate_changes('She is exhausted.', translator=translator, **BASE)
    change = next(change for change in cs.changes if change['kind'] == 'substitution')
    assert all(option['key'] != 'plain:source' for option in change['alternatives'])
    with pytest.raises(UserError, match='not an offered alternative'):
        cs.replay_pins({change['id']: 'plain:source'})


def test_unsettled_selection_region_is_not_reported_as_a_dial_rejection(translator, monkeypatch):
    from aussiefy.changes import _Builder
    real = _Builder._render_spot
    monkeypatch.setattr(_Builder, '_render_spot', lambda self, *args: (real(self, *args)[0], True))
    body = suggest_selection('She is exhausted.', span=[0, 15], translator=translator, **(BASE | {'level': 1}))
    assert body['suggestions']
    assert all(group['outcome'] == 'nothing_fits' and not group['options'] and not group['locked']
               for group in body['suggestions'])


def test_frozen_bundle_manifest_and_all_response_examples_validate():
    import hashlib
    root = Path(__file__).resolve().parents[2] / 'docs/contracts/v4'
    manifest = json.loads((root / 'manifest.json').read_text())
    for name, expected in manifest.items():
        data = (root / name).read_bytes()
        assert expected == {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    for stem in ('changes', 'cards', 'lookup-cards', 'selection', 'discovery', 'personal-terms'):
        name = stem + '.schema.json'
        assert (root / name).read_bytes() == (root.parents[2] / 'aussiefy/data' / name).read_bytes()
    for filename, schema in [('examples.json', 'changes'), ('selection-examples.json', 'selection'),
                             ('lookup-examples.json', 'lookup-cards')]:
        validator = Draft202012Validator(json.loads((root / (schema + '.schema.json')).read_text()))
        for example in json.loads((root / filename).read_text())['examples']:
            validator.validate(example['response'])
    validator = Draft202012Validator(json.loads((root / 'discovery.schema.json').read_text()))
    for body in json.loads((root / 'discovery-examples.json').read_text()).values():
        validator.validate(body)
