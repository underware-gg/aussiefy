"""Shared object reading distinguishes bounded adjuncts without discarding real arguments."""

import pytest


def neutral(translator, source, seed=0):
    return translator.translate(source, level=5, vulgarity=0, embellishment=0, seed=seed,
        document_type='custom', document_config={'profile': {'phonetic': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


@pytest.mark.parametrize('source', [
    'I try every day.', 'Do you try every day?', 'I try each morning.', 'I try every other day.',
    'I try every business day.',
    'I try each day of the week.', 'Do you try each day of the week?', 'I try each day of May.',
    'I try each day of running.',
    'I try once a day.', 'I try twice a week.', 'I try thrice an hour.', 'Do you try once a day?',
    'I try next week.', 'I try last night.', 'I try this time.', 'I try all day.',
    'I try two days.', 'I try three times.', 'I try one more time.', 'I try tomorrow.',
    'I try three times per week.', 'I try two days per month.',
    'I try yesterday.', 'I try time and again to finish it.', 'I try day after day.',
    'I approve every day.', 'I attempt every day.', 'I taste every day.', 'I overcharge every day.',
])
def test_unanchored_temporal_phrases_are_not_invented_objects(source, translator):
    assert neutral(translator, source).text == source


@pytest.mark.parametrize('source,concept,obj', [
    ('I approve every proposal.', 'GO_ALONG', 'every proposal'),
    ('I overcharge every client.', 'OVERCHARGE', 'every client'),
    ('I taste every dish.', 'TRY_OUT', 'every dish'),
    ('I attempt every problem.', 'TRY_OUT', 'every problem'),
])
def test_shared_object_rule_preserves_non_temporal_objects_for_other_verbs(source, concept, obj, translator):
    result = neutral(translator, source)
    assert any(r.substituted and concept in r.det.concepts and obj in r.output for r in result.records)


@pytest.mark.parametrize('source', [
    'I try the tool every day.', 'I try the new tool today.', 'I try the tool time and again.',
    'I try the tool every other day.',
    'I try the tool once a day.',
])
def test_mixed_object_and_time_adjunct_stays_plain_without_span_surgery(source, translator):
    result = neutral(translator, source)
    assert result.text.startswith('I try ')
    assert not any('TRY_OUT' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('source', [
    'I try at home.', 'Do you try at home?', 'I try with a spoon.', 'I try from home.',
    'I try in the morning.',
    'I try at least at home.', 'I try at most carefully.', 'I try at least a bit harder.',
])
def test_preposition_phrases_are_not_noun_objects(source, translator):
    assert neutral(translator, source).text == source


@pytest.mark.parametrize('obj', [
    'every tool', 'each tool', 'this new tool', 'two tools', 'two more tools', 'every day pass',
    'the day cream', 'two day passes', 'every morning shift', 'every night cream', 'the Times',
    'every picture of the day', 'very hard cheese', 'carefully cooked fish', 'running carefully',
    'carefully running', 'running every day', 'being helpful',
    'at least two tools', 'at most two tools',
    'the once a day cream', 'the Once a Day cream', 'thrice cooked fish', 'running once a day',
])
def test_real_objects_and_gerunds_remain_available_with_all_variants(obj, translator):
    seen = set()
    for seed in range(16):
        result = neutral(translator, f'I try {obj}.', seed)
        attempts = [r for r in result.records if r.substituted and 'TRY_OUT' in r.det.concepts]
        assert attempts
        assert all(obj in r.output for r in attempts)
        seen.update(r.chosen.entry.id for r in attempts)
    assert 'give-it-a-burl' in seen


@pytest.mark.parametrize('obj', ['every tool', 'running every day', 'at least two tools', 'at most two tools'])
def test_question_objects_keep_the_question_and_argument(obj, translator):
    result = neutral(translator, f'Do you try {obj}?')
    assert result.text.startswith('Do you ')
    assert result.text.endswith('?')
    assert obj in result.text
    assert any(r.substituted and 'TRY_OUT' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('source,concept,obj', [
    ('Every day irritates me.', 'ANNOY', 'every day'),
    ('I give every day a try.', 'TRY_OUT', 'every day'),
    ('I believe every day to be impossible.', 'DOUBT_IT', 'every day'),
    ('I give at least two tools a try.', 'TRY_OUT', 'at least two tools'),
    ('I give at most two tools a try.', 'TRY_OUT', 'at most two tools'),
])
def test_anchored_argument_roles_keep_temporal_and_quantified_nouns(source, concept, obj, translator):
    records = neutral(translator, source).records
    assert any(concept in r.det.concepts and r.det.captures.get('np') is not None
               and r.det.captures['np'].norm == obj for r in records)


def test_a_real_object_before_a_preposition_keeps_its_existing_boundary(translator):
    result = neutral(translator, 'I try the tool at home.')
    assert result.text == 'I give the tool a burl at home.'
