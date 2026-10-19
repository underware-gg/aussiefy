"""Context, grammar, configurable breadth and shared riff budgets, independently of word swaps."""
from dataclasses import replace

import pytest
import yaml

from aussiefy import harness, load_dictionary, translate
from aussiefy.errors import UserError
from aussiefy.imagery import image_offers
from aussiefy.schema import SchemaError, parse_imagery
from aussiefy.select import Detection
from aussiefy.text import tokenize


def config(**overrides):
    return {"garnish": ["riff"], "contextual_riffs": True, "entry_riffs": False,
            "riff_exaggeration": 2, "riff_association": 1,
            "profile": {"frames": [], "phonetic": 0, "garnish": {"riff": 1},
                        "max_garnish": {"riff": 3}, "garnish_gap": 0}, **overrides}


def images(plan):
    return {i["id"]: i for group in plan["riffs"] for i in group["riffs"] if "id" in i}


def test_suffix_without_a_vocabulary_substitution_is_truthfully_recorded(translator):
    r = translator.translate("He was working in vain.", document_type="custom", document_config=config())
    assert r.text == "He was working in vain, like a bloke sweeping dust in a sandstorm."
    assert not any(s.substituted for s in r.records)
    assert r.decisions()["garnish"] == [{"placement": "riff", "sentence": 0, "entry": None,
        "text": "like a bloke sweeping dust in a sandstorm", "image_id": "sandstorm-sweeper"}]
    assert r == translator.translate("He was working in vain.", document_type="custom", document_config=config())


@pytest.mark.parametrize("source", ["He is busy.", "He is not hungry.", "He isn't hungry.",
    "He was never working in vain.", "The motor is breathless.", "The tank is hungry.", "He was not, in fact, hungry.", "He is hungry—for success.",
    "He is hungry for success.", "He is breathless with excitement."])
def test_unestablished_meanings_negation_and_nonpeople_do_not_get_images(source, translator):
    p = harness.plan(source, translator=translator, document_type="custom", document_config=config())
    assert not images(p)


def test_conditional_related_images_are_never_automatically_inserted(translator):
    c = config()
    p = harness.plan("He is tired.", translator=translator, document_type="custom", document_config=c)
    found = images(p)
    assert found['compressor-split-hose']['association'] == 'related'
    assert not found['compressor-split-hose']['automatic']
    assert 'physical' in found['compressor-split-hose']['usage'].lower()
    assert p['draft'] == 'He is tired.'
    c['riff_association'] = 0
    assert not images(harness.plan("He is tired.", translator=translator, document_type="custom", document_config=c))


def test_direct_rewrites_still_require_a_writer(translator):
    p = harness.plan("He is angry.", translator=translator, document_type="custom", document_config=config())
    assert images(p)['chew-nails']['form'] == 'rewrite'
    assert not images(p)['chew-nails']['automatic'] and p['draft'] == 'He is angry.'


@pytest.mark.parametrize("kind", ["general", "custom", "technical", "news", "instructions"])
def test_exact_imagery_overrides_apply_to_every_preset(kind, translator):
    c = config(riff_exaggeration=1)
    p = harness.plan("He is out of breath.", translator=translator, document_type=kind, document_config=c)
    assert 'busted-bellows' in images(p) and 'compressor-split-hose' not in images(p)
    c['contextual_riffs'] = False
    assert not images(harness.plan("He is out of breath.", translator=translator, document_type=kind, document_config=c))


def test_dials_and_custom_defaults(translator):
    for e, expected in [('deadset', set()), ('dinkum', {'busted-bellows'}),
                        ('troppo', {'busted-bellows', 'compressor-split-hose'})]:
        p = harness.plan('He is out of breath.', embellishment=e, translator=translator)
        assert images(p).keys() == expected
    p = harness.plan('He is out of breath.', embellishment='troppo', document_type='custom', translator=translator)
    assert not images(p)
    p = harness.plan('He is hungry.', level=2, document_type='custom', document_config=config(), translator=translator)
    assert images(p).keys() == {'could-do-with-a-feed', 'wouldnt-say-no-to-some-tucker'}
    p = harness.plan('He is hungry.', level=1, document_type='custom', document_config=config(), translator=translator)
    assert not images(p)


def test_lookup_exposes_unbound_templates_and_honours_settings(translator):
    p = harness.lookup('selfish', translator=translator, document_config=config(), short=True)
    image = p['imagery'][0]
    assert '{poss}' in image['text'] and image['template'] and not image['automatic']
    assert 'imagery' not in harness.lookup('selfish', translator=translator, document_config=config(contextual_riffs=False))
    p = harness.lookup('drongo', translator=translator, document_config=config(entry_riffs=False))
    assert all('riffs' not in x for x in p['results'])
    p = harness.lookup('busted bellows', translator=translator, document_config=config())
    assert p['imagery'][0]['id'] == 'busted-bellows'


def test_slot_templates_require_actual_captures(dictionary):
    # Use the public configuration resolver, then probe the grammatical boundary directly.
    from aussiefy.genre import resolve_document
    setting = resolve_document('', config=dictionary.genres, document_type='custom', document_config=config()).setting(2)
    det = Detection(0, 1, ('SELFISH',), 'imperative', 3, 'trigger', 'test', captures={})
    assert not image_offers(dictionary, det, tokenize('selfish'), 5, 3, setting)
    image = next(i for i in dictionary.imagery if i.id == 'decency-shoes')
    d = replace(dictionary, imagery=(replace(image, frames=('predicate_adj',)),))
    det = Detection(0, 1, ('SELFISH',), 'predicate_adj', 3, 'trigger', 'test', captures={'subj':tokenize('she')[0]})
    offered = image_offers(d, det, tokenize('selfish'), 5, 3, setting)
    assert offered[0].text.endswith('her shoes')


def test_shared_budget_and_no_repeated_image_across_markdown_units(translator):
    source = 'He was working in vain.\n\nShe was working in vain.\n\nHe is hungry.\n'
    r = translate(source, markdown=True, translator=translator, document_type='custom', document_config=config())
    gs = [g for u in r.units for g in u.result.garnish if g.image_id]
    assert [g.image_id for g in gs].count('sandstorm-sweeper') == 1
    c = config(entry_riffs=True)
    c['profile']['max_garnish']['riff'] = 1
    c['profile']['frames'] = ['np', 'predicate_adj', 'clause']
    legacy_seen = False
    # At this seed a legacy riff lands first; contextual images must consume the same allowance.
    for seed in range(8):
        r = translator.translate('He is furious. He is hungry. She is out of breath.', seed=seed,
                                 document_type='custom', document_config=c)
        legacy_seen |= any(s.riff for s in r.records)
        assert len([g for g in r.garnish if g.image_id]) + sum(bool(s.riff) for s in r.records) <= 1
    assert legacy_seen


@pytest.mark.parametrize('source', ['`He is hungry.`\n', '# He is hungry\n',
    'He is hungry `now` and waiting.\n', '"He is hungry."\n'])
def test_protected_and_prefix_units_do_not_get_contextual_insertions(source, translator):
    r = translate(source, markdown=True, translator=translator, document_type='custom',
                  document_config=config(keep_quotes=True))
    assert not any(g.image_id for u in r.units for g in u.result.garnish)


@pytest.mark.parametrize('bad', [dict(concepts=['MISSING']), dict(frames=['nonsense']), dict(form='clause'),
    dict(text='{subj} grunts'), dict(text='bad {poss'), dict(exaggeration=True), dict(level=6),
    dict(usage=''), dict(related='TIRED'), dict(vulgarity=0)])
def test_imagery_schema_rejects_invalid_conditions(bad, dictionary):
    raw = dict(id='test', text='like a mower', concepts=['BUSY'], usage='A comparison.', **{})
    raw.update(bad)
    with pytest.raises(SchemaError):
        parse_imagery(raw, dictionary.concepts, lambda w: 0)


def test_loader_validates_duplicates_and_derives_swear_cap(data_copy):
    p = data_copy/'imagery.yaml'
    record = dict(id='test', text='like a fucking mower', concepts=['BUSY'], usage='Test.')
    p.write_text(yaml.safe_dump([record]))
    d = load_dictionary(data_dir=data_copy)
    assert d.imagery[0].vulgarity == 2
    p.write_text(yaml.safe_dump([record, record]))
    with pytest.raises(SchemaError, match='duplicate'):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize('bad', [{'contextual_riffs': 1}, {'entry_riffs': 'no'}, {'riff_exaggeration': 3},
    {'riff_exaggeration': True}, {'riff_association': -1}])
def test_invalid_advanced_imagery_configuration_is_rejected(bad, translator):
    with pytest.raises(UserError):
        translator.translate('Hi.', document_config=bad)


def test_corrected_idiom_sense_and_lexical_additions(dictionary, translator):
    e = dictionary.entries['as-crooked-as-a-dogs-hind-leg']
    assert e.concept == ('DISHONEST',)
    for s in ['He is angry.', 'The chair is poorly made.', 'The road is crooked.']:
        p = harness.plan(s, embellishment='deadset', translator=translator)
        assert not any(x['entry'] == e.id for x in p['planned'])
    assert dictionary.entries['pack-it-in-command'].frame == 'imperative'
    assert dictionary.entries['get-up-and-go'].concept == ('PERSONAL_ENERGY',)


@pytest.mark.parametrize('source', ['He worked in vain.', 'He was working in vain.'])
def test_both_actor_bindings_allow_person_imagery(source, translator):
    p = harness.plan(source, translator=translator, document_type='custom', document_config=config())
    assert images(p)['sandstorm-sweeper']['automatic']


def test_session_lookup_inherits_imagery_controls(translator):
    from aussiefy.retelling import brief, dispatch_tool
    session = brief('He is tired.', document_type='custom', document_config=config(riff_association=0), translator=translator)
    out, done = dispatch_tool(session, 'lookup', {'query': 'tired'})
    assert not done and 'imagery' not in out
    session = brief('He is tired.', document_type='custom', document_config=config(riff_association=1), translator=translator)
    out, done = dispatch_tool(session, 'lookup', {'query': 'tired'})
    assert not done and {i['id'] for i in out['imagery']} >= {'busted-bellows'}


@pytest.mark.parametrize('root', ['false', '3', '{}', 'text'])
def test_imagery_root_is_validated_at_loader_boundary(root, data_copy):
    (data_copy/'imagery.yaml').write_text(root)
    with pytest.raises(SchemaError, match='imagery.yaml: top level must be a list'):
        load_dictionary(data_dir=data_copy)


def test_imagery_does_not_bypass_swear_cap(dictionary):
    from aussiefy.genre import resolve_document
    setting = resolve_document('', config=dictionary.genres, document_type='custom', document_config=config()).setting(2)
    image = parse_imagery(dict(id='strong', text='like a fucking mower', concepts=['BUSY'], usage='Test.'),
                          dictionary.concepts, lambda w: 2 if w == 'fucking' else 0)
    d = replace(dictionary, imagery=(image,))
    det = Detection(0, 1, ('BUSY',), 'predicate_adj', 3, 'trigger', 'test', captures={'subj':tokenize('he')[0]})
    assert not image_offers(d, det, tokenize('busy'), 5, 1, setting)
    assert image_offers(d, det, tokenize('busy'), 5, 2, setting)


def test_lookup_cli_reports_images_and_uses_the_same_configuration(capsys):
    import json
    from aussiefy.cli import main
    assert main(['lookup', 'busted bellows', '-e', 'troppo', '--json']) == 0
    out = json.loads(capsys.readouterr().out)
    assert out['imagery'][0]['id'] == 'busted-bellows'
    code = main(['lookup', 'busted bellows', '-e', 'troppo', '--document-config', '{"contextual_riffs":false}', '--json'])
    out = json.loads(capsys.readouterr().out)
    assert 'imagery' not in out
    assert code == (0 if out['results'] else 1)


def test_empty_or_missing_optional_imagery_library_is_compatible(data_copy):
    p = data_copy/'imagery.yaml'
    p.write_text('null')
    assert not load_dictionary(data_dir=data_copy).imagery
    p.unlink()
    assert not load_dictionary(data_dir=data_copy).imagery
