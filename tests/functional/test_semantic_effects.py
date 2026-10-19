"""Reviewed meaning additions share one resolved policy across deterministic and writer tools."""

from dataclasses import replace
import json

import jsonschema

import pytest

from aussiefy import Translator, harness, load_dictionary, translate_changes
from aussiefy.cards import entry_card, short_card
from aussiefy.changes import SCHEMA
from aussiefy.errors import UserError
from aussiefy.garnish import garnish_pool
from aussiefy.genre import resolve_document
from aussiefy.policy import DocumentOverrides
from aussiefy.retelling import brief, dispatch_tool
from aussiefy.schema import SchemaError, parse_entry


LUCKY = 'the-lucky-buggers-still-breathin'
ORIGINAL = 'The living.'
TOLD = "The lucky buggers still breathin'."
PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'garnish': {'riff': 0}, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}


@pytest.fixture
def local(dictionary):
    return Translator(dictionary, lookup_embedder=None)


def options(**config):
    return dict(level=5, vulgarity=1, embedder='none', embellishment=0,
                document_config={'profile': PROFILE, **config})


@pytest.mark.parametrize('step, permitted', [(0, False), (1, False), (2, True)])
@pytest.mark.parametrize('kind', ['general', 'story', 'technical', 'custom'])
def test_permission_is_resolved_from_setting_then_exact_overrides(dictionary, kind, step, permitted):
    genre = resolve_document('Anything.', config=dictionary.genres, document_type=kind)
    assert genre.setting(step).narrator_opinion is (permitted and kind != 'custom')
    for explicit in (True, False):
        genre = resolve_document('Anything.', config=dictionary.genres, document_type=kind,
                                 document_config={'narrator_opinion': explicit})
        assert genre.setting(step).narrator_opinion is explicit


@pytest.mark.parametrize('bad', [None, 0, 1, 'true', [], {}])
def test_opinion_override_requires_real_boolean(bad):
    with pytest.raises(UserError, match='narrator_opinion'):
        DocumentOverrides.parse({'narrator_opinion': bad})


def test_effect_schema_round_trip_and_unknown_effects():
    raw = dict(id='fortunate-people', form='fortunate people', concept=['ALIVE'], frame='np',
               semantic_effects=['opinion'])
    entry = parse_entry(raw)
    assert entry.semantic_effects == ('opinion',)
    assert parse_entry(entry.to_dict()).semantic_effects == ('opinion',)
    for invalid in (['erase_roles'], [True], True):
        with pytest.raises(SchemaError, match='semantic_effects'):
            parse_entry({**raw, 'semantic_effects': invalid})


def test_translation_and_plan_inherit_same_permission(local):
    for enabled in (False, True):
        result = local.translate(ORIGINAL, **options(narrator_opinion=enabled))
        ids = {c.entry.id for r in result.records for c in r.eligible}
        assert (LUCKY in ids) is enabled
        if not enabled:
            assert any('narrator_opinion is false' in why for r in result.records for _, why in r.rejected)
        config = {'narrator_opinion': enabled, 'profile': PROFILE}
        planned = harness.plan(ORIGINAL, translator=local, level=5, vulgarity=1, embellishment=0,
                               document_config=config)
        assert planned['document_config']['narrator_opinion'] is enabled
        if not enabled:
            assert all(p['entry'] != LUCKY for p in planned['planned'])
    chosen = next(seed for seed in range(20) if any(r.chosen and r.chosen.entry.id == LUCKY
                  for r in local.translate(ORIGINAL, seed=seed, **options(narrator_opinion=True)).records))
    planned = harness.plan(ORIGINAL, translator=local, seed=chosen, level=5, vulgarity=1, embellishment=0,
                           document_config={'narrator_opinion': True, 'profile': PROFILE})
    assert next(p for p in planned['planned'] if p['entry'] == LUCKY)['semantic_effects'] == ['opinion']


def test_custom_can_enable_opinion_without_enabling_other_optional_behaviour(local):
    result = local.translate(ORIGINAL, document_type='custom', **options(narrator_opinion=True, person_swears=True))
    assert LUCKY in {c.entry.id for r in result.records for c in r.eligible}
    assert not result.embellishment.garnish
    assert result.embellishment.riff_exaggeration == 0


def test_troppo_can_explicitly_disable_opinion(local):
    result = local.translate(ORIGINAL, **{**options(narrator_opinion=False), 'embellishment': 2})
    assert LUCKY not in {c.entry.id for r in result.records for c in r.eligible}


def test_lookup_discovery_is_distinct_from_meaning_offers(local):
    for short in (False, True):
        exact = harness.lookup(TOLD.rstrip('.'), translator=local, embellishment=0, short=short, limit=30)
        card = next(c for c in exact['results'] if c['id'] == LUCKY)
        assert card['semantic_effects'] == ['opinion']
        assert card['effects_permitted'] is False
        assert 'narrator_opinion' in card['effect_rejection']
    for enabled in (False, True):
        found = harness.lookup('the living', translator=local, embellishment=0, limit=100,
                               document_config={'narrator_opinion': enabled})
        assert any(c['id'] == LUCKY for c in found['results']) is enabled


def test_cap_raised_alternatives_do_not_bypass_effect_permission(local):
    # A clean choice creates the substitution spot; the vulgarity cap alone can hold the opinion term back.
    for enabled in (False, True):
        result = translate_changes(ORIGINAL, translator=local, **{
            **options(narrator_opinion=enabled), 'vulgarity': 0})
        choices = [o for c in result.changes for o in c['alternatives'] + c['locked']]
        assert any(o['entry_id'] == LUCKY for o in choices) is enabled
        jsonschema.validate(result.to_dict(), json.loads(SCHEMA.read_text()))
        if enabled:
            assert result.entries[LUCKY]['semantic_effects'] == ['opinion']


def test_cards_report_effects_without_claiming_grammatical_applicability(dictionary):
    entry = dictionary.entries[LUCKY]
    assert entry_card(entry)['semantic_effects'] == ['opinion']
    assert short_card(entry)['semantic_effects'] == ['opinion']


def test_known_new_opinion_is_checked_in_lint_verify_and_submit(local):
    config = {'profile': PROFILE}
    for enabled in (False, True):
        config['narrator_opinion'] = enabled
        lint = harness.lint(TOLD, original=ORIGINAL, translator=local, embellishment=0, vulgarity=1,
                            document_config=config, suggest=False)
        assert any(i['kind'] == 'semantic_effect' for i in lint['issues']) is (not enabled)
        verified = harness.verify(TOLD, original=ORIGINAL, translator=local, embellishment=0, vulgarity=1,
                                  document_config=config)
        assert any(i['kind'] == 'semantic_effect' and i['severity'] == 'major'
                   for i in verified['problems']) is (not enabled)
        session = brief(ORIGINAL, translator=local, embellishment=0, vulgarity=1, document_config=config)
        outcome, accepted = dispatch_tool(session, 'submit', {'text': TOLD, 'declined': []})
        assert accepted is enabled, outcome
        assert session.payload['DOCUMENT_CONFIG']['narrator_opinion'] is enabled
        assert 'narrator_opinion' in session.system


def test_source_occurrences_are_preserved_but_additional_uses_are_checked(local):
    unchanged = harness.lint(TOLD, original=TOLD, translator=local, embellishment=0, vulgarity=1, suggest=False)
    assert not any(i['kind'] == 'semantic_effect' for i in unchanged['issues'])
    repeated = harness.lint(TOLD + ' ' + TOLD, original=TOLD, translator=local, embellishment=0,
                            vulgarity=1, suggest=False)
    assert sum(i['kind'] == 'semantic_effect' for i in repeated['issues']) == 1


def test_role_and_sympathy_mappings_do_not_add_or_drop_facts(local, dictionary):
    assert dictionary.entries['brave-bastards'].concept == ('BRAVE',)
    assert dictionary.entries['poor-buggers'].concept == ('UNLUCKY_PERSON',)
    for text, excluded in [('The soldiers.', 'brave-bastards'), ('The dead.', 'poor-buggers')]:
        for enabled in (False, True):
            result = local.translate(text, **options(narrator_opinion=enabled))
            assert excluded not in {c.entry.id for r in result.records for c in r.eligible}
    for text, wanted in [('The brave men.', 'brave-bastards'), ('The poor devils.', 'poor-buggers')]:
        result = local.translate(text, **options())
        assert wanted in {c.entry.id for r in result.records for c in r.eligible}
    assert 'SOLDIERS' not in {cid for r in local.translate('The brave men.', **options()).records
                              for cid in r.det.concepts}


def test_extensions_cannot_bypass_permission_through_garnish(dictionary, local):
    opinion = replace(next(e for e in dictionary.garnish if e.placement == 'opener' and e.status == 'active' and e.register == 'current'),
                      semantic_effects=('opinion',), when=('any',))
    eff = local.effective(level=5, vulgarity=3)
    for enabled in (False, True):
        pool, rejected = garnish_pool('opener', [opinion], eff, {}, {'any'}, narrator_opinion=enabled)
        assert bool(pool) is enabled
        assert bool(rejected) is (not enabled)


@pytest.mark.parametrize('form', [TOLD, 'The lucky buggers still breathing.'])
def test_reviewed_opinion_spelling_forms_share_known_term_checks(local, form):
    report = harness.lint(form, original=ORIGINAL, translator=local, embellishment=0, vulgarity=1, suggest=False)
    assert any(i['kind'] == 'semantic_effect' for i in report['issues'])
    retained = harness.lint(form, original=form, translator=local, embellishment=0, vulgarity=1, suggest=False)
    assert not any(i['kind'] == 'semantic_effect' for i in retained['issues'])


def test_annotated_garnish_extension_is_checked_in_writer_tools(tmp_path):
    extra = tmp_path / 'editorial.yaml'
    extra.write_text("""- id: editorial-opener
  form: what lucky souls
  frame: interjection
  type: garnish
  placement: opener
  when: [any]
  semantic_effects: [opinion]
""")
    translator = Translator(load_dictionary([extra]), lookup_embedder=None)
    told = 'What lucky souls, they arrived.'
    original = 'They arrived.'
    for enabled in (False, True):
        checked = harness.lint(told, original=original, translator=translator, embellishment=0,
                               document_config={'narrator_opinion': enabled}, suggest=False)
        assert any(i['kind'] == 'semantic_effect' and i['entry'] == 'editorial-opener'
                   for i in checked['issues']) is (not enabled)
        session = brief(original, translator=translator, embellishment=0,
                        document_config={'narrator_opinion': enabled})
        result, accepted = dispatch_tool(session, 'submit', {'text': told, 'declined': []})
        assert accepted is enabled, result
    checked = harness.lint(told, original=told, translator=translator, embellishment=0, suggest=False)
    assert not any(i['kind'] == 'semantic_effect' for i in checked['issues'])
