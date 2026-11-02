"""Protected-phrase explanations come from counterfactual readings, not reason text."""

from dataclasses import replace

import pytest

from aussiefy.fence_readings import derive_fence_readings
from aussiefy.fences import parse_fences
from aussiefy.matcher import PatternIndex
from aussiefy.schema import HOLDING_CONCEPT, SchemaError


@pytest.fixture(scope='module')
def evidence(dictionary):
    return {row.fence.phrase: row for row in derive_fence_readings(dictionary)}


@pytest.mark.parametrize('phrase,concept,entry', [
    ('national forest', 'FOREST', 'the-bush'),
    ('coin toss', 'THROW', 'chuck'),
    ('bottle of beer', 'BEER', 'amber-fluid'),
    ('jet stream', 'STREAM', 'creek'),
    ('the jet stream', 'STREAM', 'creek'),
])
def test_explanations_establish_the_blocked_reading_and_eligible_headwords(evidence, phrase, concept, entry):
    assert any(row.concept == concept and entry in row.entries for row in evidence[phrase].meanings)


def test_overlap_is_evidence_not_a_reason_to_delete_a_protection(evidence):
    assert any(trial.effect == 'overlap' for trial in evidence['the jet stream'].trials)


def test_deliberately_retained_protection_can_have_no_exact_reading(evidence, dictionary):
    row = evidence['a people']
    assert row.meanings == row.dialect == ()
    assert row.needs_audit
    assert {trial.effect for trial in row.trials} == {'no_source_pattern'}
    assert row.fence in dictionary.fences
    assert row.fence.reason


def test_dialect_fence_names_the_guarded_swap_not_a_fake_meaning(evidence):
    row = evidence['real estate agent']
    assert not row.meanings
    assert {(swap.english, swap.before, swap.after) for swap in row.dialect} == {
        ('uk', 'estate agent', 'real estate agent'), ('uk', 'estate agents', 'real estate agents')}


def test_wordless_ruled_out_reading_keeps_its_id(dictionary):
    fence = parse_fences([{'phrase': 'her freedom', 'frame': 'np', 'kind': 'other_sense',
                          'scope': {'meanings': True, 'dialect': [], 'not_in': []},
                          'reason': 'This wording is deliberately kept.'}])[0]
    custom = replace(dictionary, fences=(fence,),
                     index=PatternIndex([*dictionary.patterns, fence.pattern]))
    row, = derive_fence_readings(custom)
    assert any(meaning.concept == 'FREEDOM' and meaning.entries == () for meaning in row.meanings)
    assert not row.needs_audit


def test_every_protection_gets_an_audit_record_without_mutation(evidence, dictionary):
    assert len(evidence) == len(dictionary.fences)
    assert {row.fence for row in evidence.values()} == set(dictionary.fences)
    assert all(row.trials for row in evidence.values())
    assert all(HOLDING_CONCEPT != meaning.concept for row in evidence.values() for meaning in row.meanings)
    assert all(meaning.concept in dictionary.concepts for row in evidence.values() for meaning in row.meanings)
    assert all(eid in dictionary.entries for row in evidence.values() for meaning in row.meanings for eid in meaning.entries)


def test_generated_possessive_examples_preserve_token_spacing(evidence):
    assert any(trial.text == "dog's breakfast" for trial in evidence["dog's breakfast"].trials)


@pytest.mark.parametrize('examples', [None, 'petroleum jelly', [''], ['same', 'same'], ['unrelated words']])
def test_authored_examples_must_be_distinct_and_match_the_protection(examples):
    with pytest.raises(SchemaError, match='example'):
        parse_fences([{'phrase': 'petroleum jelly', 'frame': 'np', 'kind': 'set_phrase',
                      'scope': {'meanings': True, 'dialect': [], 'not_in': []},
                      'reason': 'Petroleum jelly is an ointment.', 'examples': examples}])


def test_authored_examples_can_supply_context_without_changing_the_protection(dictionary):
    original = next(fence for fence in dictionary.fences if fence.phrase == 'bottle of beer')
    fence, = parse_fences([{'phrase': original.phrase, 'frame': original.frame, 'kind': original.kind,
                           'scope': {'meanings': original.meanings, 'dialect': sorted(original.dialect),
                                     'not_in': sorted(original.not_in)},
                           'reason': original.reason, 'examples': ['She bought a bottle of beer.']}])
    custom = replace(dictionary, fences=(fence,),
                     index=PatternIndex([p for p in dictionary.patterns if p.fence != original] + [fence.pattern]))
    row, = derive_fence_readings(custom)
    assert any(trial.text == fence.examples[0] and trial.effect == 'direct' for trial in row.trials)
    assert fence.reason == original.reason
