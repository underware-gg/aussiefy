"""Modifier ownership is shared by selection, splicing, discovery and verification."""
import pytest
import yaml

from aussiefy import Translator, harness, load_dictionary, lookup, translate_changes

OPTIONS = {'level': 5, 'vulgarity': 3, 'embellishment': 0, 'embedder': 'none',
           'document_type': 'custom', 'document_config': {'profile': {
               'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
               'stack': 0, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}}}


@pytest.mark.parametrize('source,band', [('She is very hungry.', 'strong'),
    ('She is slightly hungry.', 'mild'), ('She is absolutely starving.', 'strong'),
    ('She is really starving.', 'strong')])
def test_reviewed_compositions_offer_flavour_without_changing_grade(translator, source, band):
    for seed in (0, 1, 42):
        result = translator.translate(source, seed=seed, **OPTIONS)
        record = next(r for r in result.records if 'HUNGRY' in r.det.concepts)
        assert record.chosen and result.text != source
        assert all(c.entry.semantic_degree['HUNGRY'] == band for c in record.eligible)
        assert 'very starvin' not in result.text
        assert 'slightly peckish' not in result.text
        assert not any(i['kind'] == 'semantic_degree' for i in harness.lint(
            result.text, original=source, translator=translator, suggest=False)['issues'])


@pytest.mark.parametrize('source', ['She is hungry enough to eat anything.',
                                   'She is so hungry that she could cry.'])
def test_relational_appetite_keeps_its_unmarked_predicate(translator, source):
    result = translator.translate(source, **OPTIONS)
    assert result.text == source
    assert not next(r for r in result.records if 'HUNGRY' in r.det.concepts).eligible


def test_discovery_and_verification_share_relational_grade(translator):
    found = lookup('hungry enough to eat anything', translator=translator, vulgarity=3)['results']
    assert all(translator.dictionary.entries[e['id']].semantic_degree.get('HUNGRY') == 'unmarked' for e in found
               if 'HUNGRY' in translator.dictionary.entries[e['id']].concept)
    issues = harness.lint('She is peckish enough to eat anything.',
        original='She is hungry enough to eat anything.', translator=translator, suggest=False)['issues']
    assert any(i['kind'] == 'semantic_degree' for i in issues)
    assert lookup('absolutely starving', translator=translator, vulgarity=3)['results']


@pytest.fixture
def graded_translator(tmp_path):
    path = tmp_path / 'degree.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'ZZ_SCALE': {'description': 'A synthetic graded state.',
            'triggers': {'predicate_adj': ['zzstate', 'zzstrong']},
            'trigger_degrees': {'predicate_adj': {'zzstate': 'unmarked', 'zzstrong': 'strong'}}}},
        'add_entries': [
            {'id': 'zz-plain', 'form': 'zzplain', 'concept': ['ZZ_SCALE'], 'frame': 'predicate_adj',
             'semantic_degree': {'ZZ_SCALE': 'unmarked'}},
            {'id': 'zz-strong', 'form': "zzstrong'", 'variants': ['zzstrong as anything'],
             'concept': ['ZZ_SCALE'], 'frame': 'predicate_adj', 'semantic_degree': {'ZZ_SCALE': 'strong'}},
            {'id': 'zz-mild', 'form': 'zzmild', 'concept': ['ZZ_SCALE'], 'frame': 'predicate_adj',
             'semantic_degree': {'ZZ_SCALE': 'mild'}}]}))
    return Translator(load_dictionary([path]), lookup_embedder=None)


@pytest.mark.parametrize('source', ['She is very zzstate.', 'She is VERY  zzstate.',
                                   'Is she very zzstate?', 'She is really zzstrong.'])
def test_each_editor_option_owns_its_modifier_exactly_once(graded_translator, source):
    result = translate_changes(source, translator=graded_translator, **OPTIONS)
    changes = [c for c in result.changes if c['kind'] == 'substitution' and c['entry_id'].startswith('zz-')]
    assert len(changes) == 1
    change = changes[0]
    options = {o['entry_id']: o['rendered'] for o in change['alternatives'] + change['locked']}
    assert 'zz-strong' in options
    assert all(not any(bad in rendered.lower() for bad in ['very very', 'very zzstrong', 'really really'])
               for rendered in options.values())
    a, b = change['src_span']
    assert 'very' in source[a:b].lower() or 'really' in source[a:b].lower()
    if 'zz-plain' in options:
        prefix = 'VERY  ' if 'VERY  ' in source else 'really ' if 'really ' in source else 'very '
        assert options['zz-plain'] == prefix + 'zzplain'


def test_relational_policy_works_for_new_dictionary_families(graded_translator):
    result = graded_translator.translate('She is zzstate enough to stop.', **OPTIONS)
    record = next(r for r in result.records if 'ZZ_SCALE' in r.det.concepts)
    assert {c.entry.id for c in record.eligible} == {'zz-plain'}
    assert result.text == 'She is zzplain enough to stop.'


def test_dropped_final_letter_is_a_single_word_not_a_clause(graded_translator):
    result = graded_translator.translate('She is absolutely zzstrong.', **OPTIONS)
    record = next(r for r in result.records if 'ZZ_SCALE' in r.det.concepts)
    assert {c.entry.id for c in record.eligible} == {'zz-strong'}
    assert 'absolutely absolutely' not in result.text


def test_relational_grade_still_filters_each_variant(graded_translator):
    from aussiefy.select import usable_forms
    result = graded_translator.translate('She is zzstrong enough to stop.', **OPTIONS)
    record = next(r for r in result.records if 'ZZ_SCALE' in r.det.concepts)
    assert {c.entry.id for c in record.eligible} == {'zz-strong'}
    assert usable_forms(record.eligible[0].entry, record.det) == ["zzstrong'"]


@pytest.mark.parametrize('modifier', ['always', 'still', 'getting'])
def test_modifier_absorption_does_not_enable_a_clause_that_discards_other_source_material(tmp_path, modifier):
    path = tmp_path / 'clause.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'ZZ_CLAUSE_GRADE': {'description': 'A graded test state.',
            'triggers': {'predicate_adj': ['zzbase']},
            'trigger_degrees': {'predicate_adj': {'zzbase': 'unmarked'}}}},
        'add_entries': [{'id': 'zz-clause', 'form': '{subj} {be} zzstrong', 'frame': 'clause',
                         'concept': ['ZZ_CLAUSE_GRADE'], 'semantic_degree': {'ZZ_CLAUSE_GRADE': 'strong'}}]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    source = f'She is {modifier} very zzbase.'
    result = translate_changes(source, translator=tr, **OPTIONS)
    assert result.text == source
    assert not any(o['entry_id'] == 'zz-clause' for c in result.changes
                   for o in c['alternatives'] + c['locked'])


@pytest.mark.parametrize('second_band,eligible', [('strong', True), ('mild', False), (None, False)])
def test_modifier_absorption_requires_every_shared_meaning_to_agree(tmp_path, second_band, eligible):
    path = tmp_path / 'multiple-meanings.yaml'
    grades = {'ZZ_ONE': 'strong', **({'ZZ_TWO': second_band} if second_band else {})}
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {cid: {'description': 'A synthetic graded meaning.',
            'triggers': {'predicate_adj': ['zzdual']},
            'trigger_degrees': {'predicate_adj': {'zzdual': 'unmarked'}}} for cid in ['ZZ_ONE', 'ZZ_TWO']},
        'add_entries': [{'id': 'zz-candidate', 'form': 'zzcandidate', 'frame': 'predicate_adj',
                         'concept': ['ZZ_ONE', 'ZZ_TWO'], 'semantic_degree': grades}]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = tr.translate('She is very zzdual.', **OPTIONS)
    record = next(r for r in result.records if 'ZZ_ONE' in r.det.concepts)
    assert bool(record.eligible) == eligible
    assert result.text == ('She is zzcandidate.' if eligible else 'She is very zzdual.')
