"""Explicit document presets and exact overrides compose consistently across document operations."""
import json

import pytest

from aussiefy import harness, translate
from aussiefy.errors import UserError
from aussiefy.policy import DocumentOverrides, Policy
from aussiefy.yarn import brief, dispatch_tool


def test_general_is_default_and_does_not_detect(monkeypatch, translator):
    def unexpected(*args, **kwargs):
        raise AssertionError('named types must not classify')
    monkeypatch.setattr('aussiefy.genre.text_genre', unexpected)
    r = translator.translate('Install the package. Read the API documentation.')
    assert r.genre.name == 'general' and r.genre.selected == 'general'
    assert r.embellishment.name == 'dinkum'
    assert r.genre.policy.term_domains == ()


def test_auto_and_explicit_type_resolve_to_the_same_preset(translator):
    text = 'Place cold food in a cooler. Keep the lid closed. Wash your hands. Pack drinks separately.'
    auto = translator.translate(text, document_type='auto')
    named = translator.translate(text, document_type='instructions')
    assert auto.genre.name == 'instructions'
    assert auto.text == named.text
    assert auto.to_dict()['document_type'] == 'auto'
    assert named.to_dict()['document_type'] == 'instructions'


def test_custom_has_only_explicit_behaviours_even_with_dinkum(translator):
    r = translator.translate('You are very tired.', document_type='custom', embellishment='dinkum')
    assert not r.embellishment.garnish and not r.embellishment.openings
    assert not r.embellishment.draft and not r.embellishment.perform
    assert r.embellishment.keep_share == 0 and r.embellishment.max_length == 1
    assert not r.genre.policy.keep_quotes and not r.genre.policy.term_domains


def test_exact_overrides_win_over_a_restrictive_preset(translator):
    conf = {'garnish': ['tag'], 'openings': True, 'keep_quotes': False, 'person_swears': True,
            'term_domains': [], 'command_context': True, 'dateline_context': True,
            'draft': False, 'keep_share': 0, 'max_length': 1.1, 'perform': True,
            'guidance': 'Exact type guidance.', 'embellishment_guidance': 'Exact voice guidance.'}
    r = translator.translate('You are very tired.', document_type='technical',
                             embellishment='deadset', document_config=conf)
    assert r.embellishment.garnish == {'tag'}
    assert r.embellishment.openings and r.embellishment.perform
    assert not r.embellishment.draft and r.embellishment.keep_share == 0
    assert r.genre.policy.term_domains == ()
    assert r.genre.policy.guidance == conf['guidance']
    assert r.embellishment.guidance == conf['embellishment_guidance']
    assert r.to_dict()['document_config']['garnish'] == ['tag']


def test_empty_lists_and_false_disable_inherited_behaviours(translator):
    conf = {'garnish': [], 'openings': False, 'person_swears': False}
    r = translator.translate('You are very tired.', document_config=conf)
    assert not r.embellishment.garnish and not r.embellishment.openings
    assert not r.genre.policy.person_swears


def test_term_domains_protect_concepts_and_dialect_together(translator):
    text = 'The browser uses cookies. The build uses a field.'
    for kind in ['general', 'technical', 'custom']:
        r = translator.translate(text, document_type=kind, document_config={'term_domains': ['technical']}, english='us')
        assert 'cookies' in r.text and 'field' in r.text and 'build' in r.text
        assert 'bickie' not in r.text and 'biscuit' not in r.text


def test_quote_override_is_independent_of_type(translator):
    text = 'The reporter said "I am very tired."'
    for kind in ['general', 'technical', 'custom', 'news']:
        r = translator.translate(text, document_type=kind, document_config={'keep_quotes': True})
        assert '"I am very tired."' in r.text


def test_markdown_resolves_auto_once_and_retains_syntax(monkeypatch, translator):
    from aussiefy.genre import text_genre
    calls = []
    def detect(*args, **kwargs):
        calls.append(args[0])
        return text_genre(*args, **kwargs)
    monkeypatch.setattr('aussiefy.genre.text_genre', detect)
    text = '# Setup\n\nRead the docs.\n\nRun the build.\n\n`pip install aussiefy`\n'
    r = translate(text, markdown=True, translator=translator, document_type='auto',
                  document_config={'garnish': [], 'term_domains': ['technical']})
    assert len(calls) == 1
    assert r.text.startswith('# Setup\n') and '`pip install aussiefy`' in r.text
    assert r.to_dict()['document_type'] == 'auto'


def test_session_tools_keep_exact_configuration(translator):
    conf = {'garnish': [], 'draft': False, 'keep_share': 0, 'max_length': 1.05, 'keep_quotes': True}
    session = brief('I am very tired.', translator=translator, document_type='custom',
                    embellishment='dinkum', document_config=conf)
    assert session.embellishment.max_length == 1.05
    assert 'ENGINE_DRAFT' not in session.payload
    checked, _ = dispatch_tool(session, 'lint', {'text': 'I am very tired.'})
    assert checked['document_config']['max_length'] == 1.05
    assert checked['document_config']['garnish'] == []


def test_guide_rejects_auto_without_text(translator):
    with pytest.raises(UserError, match='requires source text'):
        harness.guide(document_type='auto', translator=translator)


@pytest.mark.parametrize('raw', [[], {'unknown': True}, {'garnish': 'tag'}, {'garnish': ['bogus']},
                                {'keep_quotes': None}, {'openings': 1}, {'max_length': 0.5},
                                {'keep_share': float('nan')}, {'term_domains': ['unknown']},
                                {'guidance': False}])
def test_bad_configuration_is_rejected_at_the_boundary(raw):
    with pytest.raises(UserError, match='document_config'):
        Policy(document_config=raw)


def test_input_is_snapshotted_without_mutation():
    raw = {'garnish': ['tag']}
    p = Policy(document_config=raw)
    raw['garnish'].append('opener')
    assert p.document_config.garnish == ('tag',)
    assert DocumentOverrides.parse(p.document_config) == p.document_config


def test_cli_uses_the_same_configuration(capsys):
    from aussiefy.cli import main
    conf = {'garnish': [], 'keep_quotes': True}
    assert main(['translate', '--json', '--document-type', 'custom', '--document-config', json.dumps(conf),
                 'I am very tired.']) == 0
    r = json.loads(capsys.readouterr().out)
    assert r['document_type'] == 'custom' and r['document_config']['keep_quotes']


def test_session_snapshot_and_brief_contract(translator):
    raw = {'max_length': 1.1, 'keep_quotes': True, 'garnish': []}
    s = brief('I am very tired.', translator=translator, document_config=raw)
    raw['max_length'] = 2.0
    raw['garnish'].append('opener')
    checked, _ = dispatch_tool(s, 'lint', {'text': s.text})
    assert checked['document_config']['max_length'] == 1.1
    assert checked['document_config']['garnish'] == []
    assert s.payload['DOCUMENT_CONFIG']['keep_quotes'] is True
    assert 'takes precedence' in s.system


@pytest.mark.parametrize('config,expected', [({}, False), ({'max_length': 1}, True),
                                           ({'max_length': 1, 'check_length': False}, False)])
def test_custom_length_is_opt_in(config, expected, translator):
    checked = harness.lint('One ' * 80, original='One.', document_type='custom', document_config=config,
                           translator=translator, suggest=False)
    assert any(w['kind'] == 'too_long' for w in checked['warnings']) == expected


def test_constructed_override_cannot_bypass_validation():
    with pytest.raises(UserError, match='garnish'):
        Policy(document_config=DocumentOverrides(garnish=('bogus',)))


def test_verify_and_explain_report_effective_contract(translator):
    from aussiefy.explain import format_explain
    config = {'keep_quotes': True, 'garnish': []}
    r = translator.translate('I am very tired.', document_type='auto', document_config=config)
    explanation = format_explain(r)
    assert 'auto -> story' in explanation and '"keep_quotes": true' in explanation
    checked = harness.verify(r.text, original=r.source, document_type='auto', document_config=config,
                             translator=translator)
    assert checked['document_type'] == 'auto' and checked['document_config']['keep_quotes']


def test_quote_preservation_is_enforced_by_checks(translator):
    source = 'She said "I am very tired."'
    checked = harness.verify('She said "I am knackered."', original=source, translator=translator,
                             document_config={'keep_quotes': True})
    assert not checked['ok'] and any(p['kind'] == 'document_changed' for p in checked['problems'])
    relaxed = harness.lint('She said "I am knackered."', original=source, translator=translator,
                           document_config={'keep_quotes': False}, suggest=False)
    assert not any(p['kind'] == 'document_changed' for p in relaxed['issues'])


@pytest.mark.parametrize('source', ['She said "The color is gray."', 'She said “The color is gray.”'])
@pytest.mark.parametrize('mode', [{}, {'markdown': True}, {'markup': 'markdown'}])
def test_kept_quote_spelling_round_trips(source, mode, translator):
    config = {'keep_quotes': True, 'garnish': []}
    r = translate(source, translator=translator, document_config=config, **mode)
    assert r.text == source
    checked = harness.verify(r.text, original=source, translator=translator, document_config=config,
                             markup='markdown' if mode else 'text')
    assert checked['ok'], checked['problems']


@pytest.mark.parametrize('quote', ['"I am **very tired**."', '"I am `very tired`."',
                                   '"I am [very tired](https://example.org)."'])
def test_kept_markdown_quotes_span_inline_boundaries(quote, translator):
    source = 'She said ' + quote + '\n\nI am very busy.\n'
    r = translate(source, markdown=True, translator=translator,
                  document_config={'keep_quotes': True, 'garnish': []})
    assert quote in r.text
    assert r.text != source
