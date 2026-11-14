"""Current emission, request replay and host-only tuning, across document boundaries."""

import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import pytest
from jsonschema import Draft202012Validator

from aussiefy import Translator, UserError, translate, translate_changes
from aussiefy import harness
from aussiefy.changes import SCHEMA
from aussiefy.match_keys import detection_match
from aussiefy.pins import Pins, source_identity
from aussiefy.retelling import brief, dispatch_tool
from aussiefy.v3_contract import validate_response


SOURCES = ["🦘 She was very tired and hungry. He is angry and his car is broken.",
           "Good grief, are you crazy? He lost his tents and chairs. I am exhausted.",
           "# Heading\n\nShe was **very tired**. `She is hungry.`\n\nThe toilet is broken."]


@pytest.mark.parametrize('source', SOURCES)
@pytest.mark.parametrize('document', [False, True])
def test_real_emitter_graphs_and_exact_replay(source, document, translator):
    schema = Draft202012Validator(json.loads(SCHEMA.read_text()))
    for seed in range(12):
        options = dict(translator=translator, seed=seed, level=5, vulgarity=2, embellishment=2,
                       **({'markdown': True} if document else {'markup': 'markdown'}))
        original = translate_changes(source, **options)
        body = original.to_dict()
        schema.validate(body)
        validate_response(body, source, translator.dictionary, result_warnings=original.result.warnings)
        replay = translate_changes(source, pins=original.replay_pins(), **options)
        assert replay.text == original.text
        schema.validate(replay.to_dict())
        validate_response(replay.to_dict(), source, translator.dictionary, result_warnings=replay.result.warnings)


@pytest.mark.parametrize('document', [False, True])
def test_tuned_picks_survive_untuned_replay(document, translator):
    source = 'She was exhausted.\n\nHe was exhausted and his car was broken.'
    options = dict(translator=translator, level=5, vulgarity=2, embellishment=2, seed=4, variety=1,
                   **({'markdown': True} if document else {'markup': 'markdown'}))
    first = translate(source, **options)
    records = [r for u in first.units for r in u.result.records] if document else first.records
    match = detection_match(next(r for r in records if 'TIRED' in r.det.concepts).det).key
    prefs = [{'match': match, 'term': 'stonkered-tired', 'weight': 1e100}]
    tuned = translate(source, popularity=True, preferences=prefs, **options)
    pins = tuned.replay_pins()
    before = deepcopy(pins)
    replay = translate_changes(source, pins=pins, **options)
    assert replay.text == tuned.text and tuned.tuning['preferences'] == 1
    assert replay.result.tuning == {'popularity': False, 'preferences': 0}
    assert pins == before
    assert translate(source, **options).text == first.text


def test_pinned_construction_resolves_complete_recipe_outside_normal_pool(dictionary):
    entries = {key: replace(e, status='omit') if 'HUNGRY' in e.concept else e
               for key, e in dictionary.entries.items()}
    tr = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    options = dict(translator=tr, vulgarity=0, embellishment=2, invention=True,
                   document_config={'garnish': [], 'profile': {'substitution': {'idiom': 1}, 'stack': 0}})
    source = '🦘 She is hungry and he is hungry.'
    made = translate_changes(source, **options)
    assert len(made.constructions) >= 2
    pins = made.replay_pins()
    assert all(p['target']['construction_id'] for p in pins['picks'])
    # Sampling is irrelevant once every typed slot is pinned.
    assert translate_changes(source, pins=pins, variety=1, **options).text == made.text
    with pytest.raises(UserError, match='invention'):
        translate(source, pins=pins, **{**options, 'invention': False})


def test_constructor_garnish_and_riffs_are_present_in_replay_coverage(translator):
    constructors = riffs = imagery = 0
    for seed in range(35):
        source = 'She is hungry. The toilet is broken. He is an idiot. He lost his tents and chairs.'
        options = dict(translator=translator, seed=seed, vulgarity=2, embellishment=2,
                       document_config={'profile': {'garnish': {'opener': 1, 'riff': 1},
                                                   'garnish_gap': 0, 'max_garnish': {'riff': 20, 'opener': 20}}})
        result = translate(source, **options)
        pins = result.replay_pins()
        constructors += sum(bool(p.get('target') and p['target']['construction_id']) for p in pins['picks'])
        riffs += sum(bool(p.get('riff')) for p in pins['picks'])
        imagery += sum(p['kind'] == 'imagery' for p in pins['picks'])
        assert translate(source, pins=pins, **options).text == result.text
    assert min(riffs, imagery) > 0
    # The reviewed constructor can be the only opener without weakening its gates.
    tr = Translator(replace(translator.dictionary, entries={k: e for k, e in translator.dictionary.entries.items()
                                                           if e.type != 'garnish'}), lookup_embedder=None)
    source = 'The river is flowing through the valley.'
    options = dict(translator=tr, vulgarity=2, embellishment=2, seed=2,
                   document_config={'garnish': ['opener'], 'profile': {'garnish': {'opener': 1},
                                    'max_garnish': {'opener': 1}, 'swearing': {'exclaim': 1}}})
    original = translate(source, **options)
    pins = original.replay_pins()
    assert any(p['target']['construction_id'] for p in pins['picks'] if p.get('target'))
    assert translate(source, pins=pins, **options).text == original.text


@pytest.fixture
def pin_request(translator):
    source = 'She is very tired.'
    options = dict(translator=translator, vulgarity=0, embellishment=0, english='none')
    result = translate(source, **options)
    return source, options, result.replay_pins()


@pytest.mark.parametrize('fault', ['dictionary', 'source', 'seed', 'duplicate', 'unused', 'match',
                                   'unknown_target', 'form', 'extra', 'bad_span', 'bad_version', 'bad_weight'])
def test_invalid_or_unconsumed_pins_fail(pin_request, fault):
    source, options, raw = pin_request
    pins = deepcopy(raw)
    pick = pins['picks'][0]
    if fault == 'dictionary': pins['dictionary_id'] = 'sha256:' + '0'*64
    elif fault == 'source': source += '!'
    elif fault == 'seed': pins['seed'] = 1
    elif fault == 'duplicate': pins['picks'].append(deepcopy(pick))
    elif fault == 'unused': pick['span'] = [0, 1]
    elif fault == 'match': pick['match'] = 'not-a-match'
    elif fault == 'unknown_target': pick['target']['entry_id'] = 'missing-term'
    elif fault == 'form': pick['target']['form'] = 'words I just made up'
    elif fault == 'extra': pick['mystery'] = True
    elif fault == 'bad_span': pick['span'][0] = False
    elif fault == 'bad_version': pins['version'] = True
    elif fault == 'bad_weight': pick['target']['weight'] = 100
    with pytest.raises(UserError):
        translate(source, pins=pins, **options)


def test_pins_cannot_raise_caps_themes_or_touch_protections(translator):
    source = 'The toilet is broken.'
    options = dict(translator=translator, vulgarity=3, embellishment=2, seed=0,
                   document_config={'garnish': []})
    r = translate(source, **options)
    pins = r.replay_pins()
    term = next(p for p in pins['picks'] if p['kind'] == 'substitution' and p['match'].startswith('TOILET'))
    term['target'].update(entry_id='dunny', form='dunny')
    with pytest.raises(UserError):
        translate(source, pins=pins, themes={'bodily_functions': False}, **options)
    # Even a valid identity packet cannot force an opaque code span.
    opaque = '`She is very tired.`'
    p = translate('She is very tired.', translator=translator, embellishment=0).replay_pins()
    p.update(source_id=source_identity(opaque))
    for row in p['picks']: row['span'] = [x+1 for x in row['span']]
    with pytest.raises(UserError, match='could not be applied'):
        translate(opaque, translator=translator, embellishment=0, markup='markdown', pins=p)


def test_complete_empty_packet_retains_source_and_partial_packet_allows_automatic_picks(pin_request):
    source, options, pins = pin_request
    pins['picks'] = []
    assert not any(r.substituted for r in translate(source, pins=pins, **options).records)
    pins['complete'] = False
    assert translate(source, pins=pins, **options).text == translate(source, **options).text


def test_pins_are_snapshotted_and_payload_has_no_response_local_riff_index(pin_request):
    source, options, raw = pin_request
    prepared = Pins.prepare(raw, source, options['translator'].dictionary, 0)
    original = prepared.to_dict()
    raw['picks'][0]['target']['form'] = 'mutated'
    assert prepared.to_dict() == original
    assert 'riff_index' not in json.dumps(original)


def test_host_preferences_hook_uses_resolved_dials_once_and_is_never_a_client_argument(translator):
    from aussiefy.mcp_server import build_server
    calls = []
    def preferences_hook(**dials):
        calls.append(dials)
        return []
    server = build_server(translator=translator, allow_document_config=False, allow_tuning=False,
                          preferences_hook=preferences_hook, tools=['aussie_translate'])
    tools = asyncio.run(server.list_tools())
    fields = tools[0].input_schema['properties']
    assert {'themes', 'invention', 'pins'} <= fields.keys()
    assert not {'preferences', '_preferences_hook', 'popularity', 'document_config'} & fields.keys()
    result = asyncio.run(server.call_tool('aussie_translate', {'text': 'She is **tired**.', 'markdown': True,
                         'level': 5, 'vulgarity': 0, 'embellishment': 2, 'invention': False}))
    assert not result.is_error
    assert calls == [{'level': 5, 'vulgarity': 0, 'embellishment': 2}]


def test_scaffold_is_shared_with_yarn_and_explicit_misreadable_permission(translator):
    plan = harness.plan('She is hungry.', translator=translator, embellishment=2, vulgarity=0)
    session = brief('She is hungry.', translator=translator, embellishment=2, vulgarity=0)
    scaffold = plan['scaffold']
    assert scaffold['invention'] and scaffold['families'] and scaffold['ingredients'] and scaffold['meanings']
    assert session.payload['CONSTRUCTION_SCAFFOLD']['constraints']['allow_misreadable']
    assert not scaffold['constraints']['allow_misreadable']
    assert all(isinstance(t, dict) for f in scaffold['families'] for t in f['themes'])
    reply, _ = dispatch_tool(session, 'lint', {'text': session.plan['draft']})
    assert not any(i['kind'] == 'flagged' for i in reply['issues'])


def test_top_permissions_override_per_key_and_respect_loaded_defaults(dictionary):
    defaults = {**dictionary.policy_defaults, 'document_config': {'themes': {'drinking': False}, 'invention': False}}
    tr = Translator(replace(dictionary, policy_defaults=defaults), lookup_embedder=None)
    result = harness.plan('She is hungry.', translator=tr, embellishment=2, themes={'violence': True})
    assert result['theme_permissions']['drinking'] is False and result['theme_permissions']['violence'] is True
    assert result['scaffold']['invention'] is False
    assert harness.plan('She is hungry.', translator=tr, embellishment=2)['scaffold']['invention'] is False


@pytest.mark.parametrize('document', [False, True])
def test_editor_options_build_precise_source_pins_and_refuse_locked_choices(document, translator):
    source = '🦘 She was tired.\n\nHe is hungry.'
    options = dict(translator=translator, level=5, vulgarity=1, embellishment=0,
                   **({'markdown': True} if document else {}))
    cs = translate_changes(source, **options)
    sidecar = cs.replay_options()
    assert 'replay_pins' not in cs.to_dict() and 'current' in sidecar
    checked = refused = 0
    for change in cs.changes:
        if change['kind'] != 'substitution':
            continue
        for option in change['alternatives'] + change['locked']:
            key = option['key']
            if option['kind'] == 'plain':
                replay = translate(source, pins=cs.replay_pins({change['id']: key}), **options)
                assert replay.text == cs.text[:option['out_span'][0]] + option['rendered'] + cs.text[option['out_span'][1]:]
                continue
            pins = cs.replay_pins({change['id']: key})
            if option in change['locked']:
                with pytest.raises(UserError):
                    translate(source, pins=pins, **options)
                refused += 1
            else:
                replay = translate_changes(source, pins=pins, **options)
                actual = next(c for c in replay.changes if c['kind'] == 'substitution'
                              and c['match']['key'] == change['match']['key'])
                assert actual['option_key'] == key
                checked += 1
    assert checked > 3 and refused > 0
    with pytest.raises(UserError):
        cs.replay_pins({'missing-change': 'missing-option'})
    # Sidecars are detached value snapshots.
    sidecar['current']['picks'].clear()
    assert cs.replay_pins()['picks']


def test_constructor_editor_alternatives_and_removal_replay(translator):
    source = 'The river is flowing through the valley.'
    options = dict(translator=translator, vulgarity=2, embellishment=2,
                   document_config={'garnish': ['opener'], 'profile': {'garnish': {'opener': 0},
                          'max_garnish': {'opener': 1}, 'swearing': {'exclaim': 1}}})
    cs = translate_changes(source, **options)
    change = next(c for c in cs.changes if c.get('construction_id'))
    for option in change['alternatives']:
        key = option['key']
        replay = translate_changes(source, pins=cs.replay_pins({change['id']: key}), **options)
        selected = next(c for c in replay.changes if c.get('placement') == 'opener')
        assert 'construction:' + selected['construction_id'] == key if selected.get('construction_id') else 'entry:' + selected['entry_id'] == key
    removed = translate(source, pins=cs.replay_pins({change['id']: None}), **options)
    assert not any(g.text for g in removed.garnish)


def test_frozen_v4_schemas_match_the_snapshot_and_real_fixtures(translator):
    from pathlib import Path
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'scripts'))
    from regen_changes_fixtures import CASES, build
    for name in ('changes.schema.json', 'cards.schema.json', 'lookup-cards.schema.json',
                 'selection.schema.json', 'discovery.schema.json', 'personal-terms.schema.json'):
        active = json.loads((root / 'aussiefy/data' / name).read_text())
        accepted = json.loads((root / 'docs/contracts/v4' / name).read_text())
        Draft202012Validator.check_schema(active)
        assert {k: v for k, v in active.items() if k not in {'title', '$comment', 'description'}} == {
            k: v for k, v in accepted.items() if k not in {'title', '$comment', 'description'}}
    schema = Draft202012Validator(json.loads(SCHEMA.read_text()))
    pins_schema = Draft202012Validator(json.loads((root / 'aussiefy/data/pins.schema.json').read_text()))
    cards_schema = Draft202012Validator(json.loads((root / 'aussiefy/data/lookup-cards.schema.json').read_text()))
    Draft202012Validator.check_schema(pins_schema.schema)
    for name, (_, request) in CASES.items():
        fixture = build(name, translator)
        schema.validate(fixture['response'])
        cs = translate_changes(request['text'], translator=translator,
                               **{k: v for k, v in request.items() if k != 'text'})
        validate_response(fixture['response'], request['text'], translator.dictionary,
                          result_warnings=cs.result.warnings)
        pins_schema.validate(cs.replay_pins())
    constructed = build('v3-construction', translator)['response']
    assert any(c.get('construction_id') for c in constructed['changes'])
    pictured = build('v3-imagery', translator)['response']
    assert pictured['imagery'] and any(c.get('image_id') for c in pictured['changes'])
    for query in ('knackered', 'quantum entanglement'):
        cards_schema.validate(harness.lookup(query, translator=translator))


def test_bulldust_is_never_an_unlabelled_secondary_stack(dictionary):
    from aussiefy.engine import PassObserver
    primary = dictionary.entries['knackered']
    invented = replace(primary, id='fixture-invented', form='worn right out', variants=(),
                       sources=(), evidence='bulldust', coined_by='person')
    tr = Translator(replace(dictionary, entries={primary.id: primary, invented.id: invented}), lookup_embedder=None)
    class Primary(PassObserver):
        def choose(self, sent, det, keep, choice):
            return next(c for c in keep if c.entry.id == primary.id)
    options = dict(level=5, vulgarity=0, embellishment=0,
                   document_config={'profile': {'stack': 1, 'substitution': {'lexical': 1, 'idiom': 1}}})
    result = tr.translate('She was very tired.', _observer=Primary(), **options)
    assert any(r.chosen for r in result.records)
    assert not any(r.stacked for r in result.records)
    pins = result.replay_pins()
    row = next(p for p in pins['picks'] if p['kind'] == 'substitution')
    row['stack'] = {**row['target'], 'entry_id': invented.id, 'form': invented.form}
    with pytest.raises(UserError, match='stacked pin'):
        tr.translate(result.source, pins=pins, **options)


def test_hosted_clients_cannot_supply_preferences_or_hidden_popularity(translator):
    from aussiefy.mcp_server import build_server
    calls = []
    server = build_server(translator=translator, allow_tuning=False,
                          preferences_hook=lambda **dials: calls.append(dials) or [])
    match = detection_match(translate('She is tired.', translator=translator).records[0].det).key
    args = {'text': 'She is tired.', 'preferences': [{'match': match, 'term': 'stonkered-tired', 'weight': 1e100}],
            'popularity': True}
    result = asyncio.run(server.call_tool('aussie_translate', args))
    assert not result.is_error and result.structured_content['tuning'] == {'popularity': False, 'preferences': 0}
    assert len(calls) == 1


@pytest.mark.parametrize('names', ['aussie_translate', ['unknown_tool'], [['aussie_translate']], iter(['aussie_translate'])])
def test_host_tool_allowlist_rejects_invalid_configuration(names):
    from aussiefy.mcp_server import build_server
    with pytest.raises(UserError):
        build_server(tools=names)


def test_lookup_and_tuned_replay_fixtures_are_real_current_emission(translator):
    from pathlib import Path
    from scripts.regen_changes_fixtures import support
    root = Path(__file__).resolve().parents[2]
    actual = support(translator)
    for name, body in actual.items():
        assert json.loads((root / 'tests/fixtures/v3' / name).read_text()) == body
    cards = Draft202012Validator(json.loads((root / 'aussiefy/data/lookup-cards.schema.json').read_text()))
    for case in actual['lookup.json']['cases']:
        cards.validate(case['response'])
    replay = actual['replay.json']
    pins = replay['untuned_request']['pins']
    Draft202012Validator(json.loads((root / 'aussiefy/data/pins.schema.json').read_text())).validate(pins)
    assert replay['untuned_response']['text'] == replay['tuned_response']['text']
    assert replay['tuned_response']['tuning']['preferences'] == 1
    assert replay['untuned_response']['tuning'] == {'popularity': False, 'preferences': 0}


@pytest.mark.parametrize('query', ['knackered', 'quantum entanglement', 'national forest', 'think in circles'])
@pytest.mark.parametrize('short', [False, True])
def test_every_lookup_outcome_reports_neutral_tuning_and_policy_warnings(query, short, translator):
    from aussiefy.errors import warning_details
    result = harness.lookup(query, short=short, translator=translator, unlock=['slur'])
    assert result['dictionary_id'] == translator.dictionary.identity and result['card_version'] == 4
    assert result['tuning'] == {'popularity': False, 'preferences': 0}
    assert result['warnings'] == result['policy_warnings']
    assert result['warning_details'] == warning_details(result['warnings'])
    assert 'profile_config' not in result


def test_riff_wording_is_an_unambiguous_persistent_selector(data_copy):
    import yaml
    from aussiefy import SchemaError, load_dictionary
    path = data_copy / 'riffs.yaml'
    raw = yaml.safe_load(path.read_text())
    entry_id = next(key for key, values in raw.items() if values)
    raw[entry_id].append(deepcopy(raw[entry_id][0]))
    path.write_text(yaml.safe_dump(raw, sort_keys=False))
    with pytest.raises(SchemaError, match='duplicate riff text'):
        load_dictionary(data_dir=data_copy)


def test_replay_pins_retain_configured_riff_limits(translator):
    source = 'She is hungry. He is hungry.'
    config = {'garnish': ['riff'], 'entry_riffs': False,
              'profile': {'garnish': {'riff': 1}, 'max_garnish': {'riff': 2}, 'garnish_gap': 0}}
    options = dict(translator=translator, vulgarity=0, embellishment=2, document_config=config)
    original = translate(source, **options)
    pins = original.replay_pins()
    assert sum(p['kind'] == 'imagery' for p in pins['picks']) == 2
    assert translate(source, pins=pins, **options).text == original.text
    for changes in ({'max_garnish': {'riff': 1}}, {'garnish_gap': 1}):
        limited = {**config, 'profile': {**config['profile'], **changes}}
        with pytest.raises(UserError, match='could not be applied'):
            translate(source, pins=pins, **{**options, 'document_config': limited})


def test_pinned_riff_reuse_cannot_evade_occurrence_limits(translator):
    from aussiefy.pins import target
    config = {'garnish': ['riff'], 'profile': {'garnish': {'riff': 1},
              'max_garnish': {'riff': 3}, 'garnish_gap': 0}}
    source = 'The toilet is broken. The toilet is broken.'
    options = dict(translator=translator, vulgarity=0, embellishment=2, document_config=config)
    pins = translate(source, **options).replay_pins()
    entry = translator.dictionary.entries['cactus']
    riff = entry.riffs_within(0, translator.effective(vulgarity=0).theme_policy, registers=('current',))[0]
    rows = [p for p in pins['picks'] if p['kind'] == 'substitution' and p['match'].startswith('BROKEN/')]
    assert len(rows) == 2
    for row in rows:
        row.update(target=target(entry, entry.form).to_dict(), stack=None, riff=riff.text)
    with pytest.raises(UserError, match='already used'):
        translate(source, pins=pins, **options)
    source = 'She is hungry. He is hungry.'
    image_options = {**options, 'document_config': {**config, 'entry_riffs': False}}
    pins = translate(source, **image_options).replay_pins()
    images = [p for p in pins['picks'] if p['kind'] == 'imagery']
    assert len(images) == 2
    images[1]['image_id'] = images[0]['image_id']
    with pytest.raises(UserError):
        translate(source, pins=pins, **image_options)


def test_pinned_constructor_keeps_its_own_option_when_renderings_are_withheld(translator, monkeypatch):
    from aussiefy import changes as C
    source = 'The river is flowing through the valley.'
    options = dict(translator=translator, vulgarity=2, embellishment=2,
        document_config={'garnish': ['opener'], 'profile': {'garnish': {'opener': 0},
          'max_garnish': {'opener': 1}, 'swearing': {'exclaim': 1}}})
    original = translate_changes(source, **options)
    real = C._Builder._phonetic_region
    def differs(self, text, bounds, flags, annotations=None, **kwargs):
        output, infix = real(self, text, bounds, flags, annotations, **kwargs)
        return (output + '?' if output else output), infix
    monkeypatch.setattr(C._Builder, '_phonetic_region', differs)
    replay = translate_changes(source, pins=original.replay_pins(), **options)
    body = replay.to_dict()
    Draft202012Validator(json.loads(SCHEMA.read_text())).validate(body)
    validate_response(body, source, translator.dictionary, result_warnings=replay.result.warnings)
    change = next(c for c in replay.changes if c.get('construction_id'))
    assert change['id'] in {w['id'] for w in replay.withheld}
    assert [o['construction_id'] for o in change['alternatives']] == [change['construction_id']]
