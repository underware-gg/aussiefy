"""Calibration is validated corpus data, including overlays and research-round rewriting."""

from types import SimpleNamespace

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.rounds import RoundConfig, RoundPlan, plan_round, base_dictionary
from aussiefy.schema import SchemaError, parse_concept, parse_entry


def test_unmarked_is_explicit_evidence_in_entry_round_trip():
    raw = {'id': 'graded', 'form': 'graded', 'concept': ['GRADE'], 'frame': 'predicate_adj',
           'semantic_degree': {'GRADE': 'unmarked'}}
    assert parse_entry(raw).to_dict()['semantic_degree'] == {'GRADE': 'unmarked'}
    assert parse_entry(parse_entry(raw).to_dict()).semantic_degree == {'GRADE': 'unmarked'}


@pytest.mark.parametrize('bad', [None, [], True, {'GRADE': 'unknown'}, {'GRADE': True}, {'OTHER': 'mild'}])
def test_bad_entry_calibration_is_rejected(bad):
    with pytest.raises(SchemaError):
        parse_entry({'id': 'graded', 'form': 'graded', 'concept': ['GRADE'], 'frame': 'predicate_adj',
                     'semantic_degree': bad})


@pytest.mark.parametrize('degrees', [None, [], {'vp': {'mild@2': 'mild'}},
    {'predicate_adj': {'mild': 'mild'}}, {'predicate_adj': {'mild@2': 'unknown'}},
    {'predicate_adj': {'mild@2': True}}, {'predicate_adj': []}])
def test_trigger_calibration_requires_the_exact_existing_pattern_and_frame(degrees):
    with pytest.raises(SchemaError):
        parse_concept('GRADE', {'triggers': {'predicate_adj': ['mild@2']}, 'trigger_degrees': degrees})


def test_overlay_cannot_leave_dangling_trigger_calibration(tmp_path):
    path = tmp_path / 'bad.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
                                   'patch_concepts': {'DRUNK': {'triggers': {}}}}))
    with pytest.raises(SchemaError, match='trigger_degrees'):
        load_dictionary([path])


def test_round_append_finds_triggers_after_a_same_frame_calibration_map():
    raw = {'GRADE': {'description': 'A test.',
                     'trigger_degrees': {'predicate_adj': {'mild@2': 'mild'}},
                     'triggers': {'predicate_adj': ['mild@2']}}}
    text = yaml.safe_dump(raw, sort_keys=False, default_flow_style=None)
    plan = RoundPlan(SimpleNamespace(concept_fixes={}, trigger_fixes={}))
    plan.added_triggers = {'GRADE': {'predicate_adj': ['strong@5']}}
    fixed = yaml.safe_load(plan._concepts_text(text))['GRADE']
    assert fixed['triggers']['predicate_adj'] == ['mild@2', 'strong@5']
    assert fixed['trigger_degrees'] == raw['GRADE']['trigger_degrees']


def test_round_preserves_calibration_through_style_rewrites_and_guard_pruning(tmp_path, data_copy):
    directory = tmp_path / 'round'
    (directory / 'verify').mkdir(parents=True)
    (directory / 'round.yaml').write_text('name: degree\noutput: degree.yaml\n')
    verdict = {'decision': 'add_entry',
               'entry': {'id': 'zzdegree', 'form': 'zzmildterm', 'concept': ['ZZ_GRADE'],
                         'frame': 'predicate_adj', 'semantic_degree': {'ZZ_GRADE': 'mild'}},
               'new_concept': {'id': 'ZZ_GRADE', 'description': 'A synthetic graded state.',
                   'triggers': {'predicate_adj': ['zzstate@2', 'zzmildterm']},
                   'trigger_degrees': {'predicate_adj': {'zzstate@2': 'mild', 'zzmildterm': 'mild'}}}}
    (directory / 'verify' / 'verdicts-a.yaml').write_text(yaml.safe_dump([verdict]))
    config = RoundConfig.load(directory)
    config.trigger_fixes = {'intensity': {'zzstate': 4}}
    plan = plan_round(config, base_dictionary(config, data_copy))
    result = plan.write(data_copy)
    assert result.concepts['ZZ_GRADE'].trigger_degrees == {'predicate_adj': {'zzstate@4': 'mild'}}
    assert result.entries['zzdegree'].semantic_degree == {'ZZ_GRADE': 'mild'}
