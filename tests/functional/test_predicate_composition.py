"""Dependent complements and clause continuations survive every rendered form."""

from dataclasses import replace

import pytest

from aussiefy import Translator, harness, load_dictionary, translate, translate_changes
from aussiefy.detect import Detection
from aussiefy.schema import Entry
from aussiefy.select import usable_forms


PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'stack': 1, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}
OPTIONS = {'level': 5, 'vulgarity': 3, 'embellishment': 0, 'embedder': 'none',
           'document_type': 'custom', 'document_config': {'profile': PROFILE}}


@pytest.mark.parametrize('backend', ['none', 'ngram', 'bundled'])
@pytest.mark.parametrize('source,tail', [
    ('I feel hungry enough to eat anything.', 'enough to eat anything.'),
    ('She is tired enough to sleep anywhere.', 'enough to sleep anywhere.'),
    ('He is so tired that he cannot drive.', 'that he cannot drive.'),
    ('She was too tired to work.', 'to work.'),
    ('He is so hungry and tired that he cannot work.', 'that he cannot work.'),
    ('He is too hungry and tired to calibrate the sensor.', 'to calibrate the sensor.'),
    ('She is hungry **enough** to eat anything.', 'to eat anything.'),
])
def test_dependent_complements_survive_without_a_second_predicate_tail(translator, source, tail, backend):
    for seed in (0, 1, 42):
        result = translator.translate(source, **{**OPTIONS, 'embedder': backend}, seed=seed)
        assert result.text.endswith(tail)
        for record in result.records:
            if record.substituted and record.det.result_clause:
                assert ' ' not in record.output
                assert record.stacked is None
        if source.startswith('He is so'):
            assert result.text.startswith('He is so ')
        if source.startswith('He is too'):
            assert result.text.startswith('He is too ')


@pytest.mark.parametrize('marker', ['**enough**', '*enough*', '`enough`'])
def test_markup_cannot_hide_a_predicate_complement(translator, marker):
    source = f'She is hungry {marker} to eat anything.'
    result = translate(source, translator=translator, markdown=True,
                       **{k: v for k, v in OPTIONS.items() if k != 'embedder'}, seed=42)
    assert result.text == source


def test_form_compatibility_filters_variants_instead_of_the_entry_class():
    det = Detection(0, 1, ('TIRED',), 'predicate_adj', 3, 'trigger', 'test', result_clause=True)
    entry = Entry('test', 'worn out', ('TIRED',), 'predicate_adj', variants=('shattered', "starvin'"))
    assert usable_forms(entry, det) == ['shattered', "starvin'"]
    assert usable_forms(replace(entry, form='shattered', variants=('worn out',)), det) == ['shattered']


@pytest.mark.parametrize('source', [
    'The engineer who was very tired checked the valve.',
    'She was tired after work.',
    'She was tired—after working all day.',
    'She was tired (after work).',
])
def test_stacks_do_not_split_unfinished_clauses(translator, source):
    result = translator.translate(source, **OPTIONS, seed=42)
    assert any(record.substituted for record in result.records)
    assert all(record.stacked is None for record in result.records)


def test_stacking_remains_available_at_a_complete_clause(translator):
    result = translator.translate('She was tired.', **OPTIONS, seed=42)
    assert any(record.stacked for record in result.records)


def test_plans_and_automatic_alternatives_share_complement_constraints(translator):
    source = 'I feel hungry enough to eat anything.'
    planned = harness.plan(source, translator=translator, **{k: v for k, v in OPTIONS.items() if k != 'embedder'}, seed=42)
    assert planned['draft'].count('enough to') == 1
    built = translate_changes(source, translator=translator, **OPTIONS, seed=42)
    assert built.text.count('enough to') == 1
    for change in built.changes:
        for choice in change['alternatives']:
            assert 'enough to' not in choice['rendered']


def test_direct_triggers_and_long_primary_forms_cannot_bypass_the_tail(tmp_path):
    path = tmp_path / 'composition.yaml'
    path.write_text('- {id: test-long-primary, form: "hungry enough to eat a horse", '
                    'variants: [ravenous], concept: [HUNGRY], frame: predicate_adj, '
                    'replaces: [hungry], class: lexical}\n')
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = tr.translate('She is hungry enough to eat anything.', **OPTIONS, seed=42)
    record = next(r for r in result.records if 'HUNGRY' in r.det.concepts)
    assert any(c.entry.id == 'test-long-primary' for c in record.eligible)
    assert usable_forms(next(c.entry for c in record.eligible if c.entry.id == 'test-long-primary'), record.det) == ['ravenous']


def test_verification_rejects_the_reproduced_duplicate_complement(translator):
    source = 'I feel hungry enough to eat anything.'
    bad = "I feel hungry enough to eat the arse out of a low-flyin' duck enough to eat anything."
    checked = harness.verify(bad, original=source, translator=translator, level=5, vulgarity=3)
    assert not checked['ok']
    assert any(p['kind'] == 'predicate_composition' and p['severity'] == 'major' for p in checked['problems'])


@pytest.mark.parametrize('text', [
    "I feel hungry enough to eat the arse out of a low-flyin' duck.",
    'He is tall enough to be heavy enough to sink the boat.',
    'I am hungry enough to eat anything.',
])
def test_legitimate_result_constructions_are_not_flagged(translator, text):
    checked = harness.lint(text, translator=translator, level=5, vulgarity=3, suggest=False)
    assert not any(i['kind'] == 'predicate_composition' for i in checked['issues'])


@pytest.mark.parametrize('tail', ['enough times to wear him out.', 'enough to make him run.'])
def test_recognised_idioms_can_have_legitimate_nested_continuations(translator, tail):
    text = 'I am hungry enough to eat a horse and chase the jockey ' + tail
    for original in (None, text, 'He said something else entirely.'):
        checked = harness.lint(text, original=original, translator=translator, level=5, vulgarity=3, suggest=False)
        assert not any(i['kind'] == 'predicate_composition' for i in checked['issues'])


def test_an_ambiguous_or_changed_result_tail_does_not_establish_a_bad_local_edit(translator):
    source = 'I feel hungry enough to eat anything. I feel hungry enough to eat anything.'
    bad = "I feel hungry enough to eat a horse and chase the jockey enough to eat anything."
    checked = harness.lint(bad, original=source, translator=translator, level=5, vulgarity=3, suggest=False)
    assert not any(i['kind'] == 'predicate_composition' for i in checked['issues'])
