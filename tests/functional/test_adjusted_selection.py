"""Loaded community adjustments affect picks, never the interpretation or permissions."""

from dataclasses import replace
import math

import pytest
import yaml

from aussiefy import Translator, load_dictionary, translate, translate_changes
from aussiefy.adjustments import Adjustments
from aussiefy.detect import read_meanings
from aussiefy.match_keys import detection_match
from aussiefy.text import tokenize


OPTIONS = dict(level=5, vulgarity=1, embellishment=2, english='none', embedder='none',
               document_type='custom', document_config={'garnish': [], 'profile': {'phonetic': 0,
               'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


@pytest.fixture(scope='module')
def adjusted_dictionary(tmp_path_factory):
    root = tmp_path_factory.mktemp('adjusted-selection')
    overlay = root / 'synthetic.yaml'
    overlay.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'ZZ_TUNING': {'description': 'Synthetic test state.',
            'triggers': {'predicate_adj': ['zzstate']},
            'trigger_degrees': {'predicate_adj': {'zzstate': 'unmarked'}}}},
        'add_entries': [dict(id=eid, form=eid.replace('-', ''), concept=['ZZ_TUNING'],
            frame='adj', semantic_degree={'ZZ_TUNING': 'unmarked'}, **extra)
            for eid, extra in [('zz-choice-a', {}), ('zz-choice-b', {}),
                               ('zz-crude', {'vulgarity': 2}),
                               ('zz-theme', {'themes': [{'name': 'sex', 'tier': 2}]})]]}))
    base = load_dictionary([overlay])
    det = next(d for d in read_meanings(tokenize('She is zzstate.'), base).detections if 'ZZ_TUNING' in d.concepts)
    key = detection_match(det).key
    manifests = []
    for ns in ['first', 'second']:
        path = root / f'{ns}.yaml'
        path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-extension/v1', 'namespace': ns,
            'adjustments': {'normal': [.5, 1.5], 'popularity': [.25, 3], 'records': [
                dict(match=key, term=eid, level=5, vulgarity=1, embellishment=2, factor=factor)
                for eid, factor in [('zz-choice-b', 2), ('zz-crude', 3), ('zz-theme', 3)]]}}))
        manifests.append(path)
    return load_dictionary([overlay, *manifests])


def run(dictionary, source='She is zzstate.', **options):
    return Translator(dictionary, lookup_embedder=None).translate(source, **{**OPTIONS, **options})


def spot(result):
    return next(r for r in result.records if 'ZZ_TUNING' in r.det.concepts)


def weights(result):
    return {c.entry.id: c.weight for c in spot(result).eligible}


def test_loaded_adjustments_change_actual_candidate_odds_within_normal_band(adjusted_dictionary):
    tuned = weights(run(adjusted_dictionary))
    plain = weights(run(replace(adjusted_dictionary, adjustments=Adjustments())))
    assert set(tuned) == set(plain) == {'zz-choice-a', 'zz-choice-b'}
    assert (tuned['zz-choice-b'] / tuned['zz-choice-a']) / (plain['zz-choice-b'] / plain['zz-choice-a']) == pytest.approx(1.5)
    assert any('community adjustment x 1.5 (normal band)' in c.why for c in spot(run(adjusted_dictionary)).eligible)


@pytest.mark.parametrize('options', [{'level': 4}, {'vulgarity': 0}, {'vulgarity': 2},
                                    {'embellishment': 0}, {'embellishment': 1}])
def test_adjustments_do_not_leak_across_resolved_dials(adjusted_dictionary, options):
    plain = replace(adjusted_dictionary, adjustments=Adjustments())
    assert weights(run(adjusted_dictionary, **options)) == weights(run(plain, **options))


def test_a_root_adjustment_does_not_apply_to_a_qualified_key(adjusted_dictionary):
    plain = replace(adjusted_dictionary, adjustments=Adjustments())
    tuned = run(adjusted_dictionary, 'She is really zzstate.')
    assert detection_match(spot(tuned).det).degree == 'strong'
    assert weights(tuned) == weights(run(plain, 'She is really zzstate.'))
    assert weights(tuned)


def test_adjustments_are_applied_before_variety_prunes_the_candidates(adjusted_dictionary):
    assert spot(run(adjusted_dictionary, variety=1)).chosen.entry.id == 'zz-choice-b'


def test_adjustments_change_seeded_picks_without_changing_rolls_or_eligibility(adjusted_dictionary):
    plain = replace(adjusted_dictionary, adjustments=Adjustments())
    changed = 0
    for seed in range(32):
        tuned, original = (run(d, seed=seed) for d in (adjusted_dictionary, plain))
        a, b = spot(tuned), spot(original)
        assert a.det == b.det and a.p == b.p and a.roll == b.roll
        assert {c.entry.id for c in a.eligible} == {c.entry.id for c in b.eligible}
        assert a.rejected == b.rejected
        changed += a.chosen.entry.id != b.chosen.entry.id
        assert tuned.to_dict() == run(adjusted_dictionary, seed=seed).to_dict()
    assert changed > 0
    assert adjusted_dictionary.entries == plain.entries


def test_a_failed_roll_is_not_rescued_by_an_adjustment(adjusted_dictionary):
    quiet = {'garnish': [], 'profile': {'phonetic': 0, 'substitution': {'lexical': .01, 'phrase': .01, 'idiom': .01}}}
    tuned = run(adjusted_dictionary, document_config=quiet)
    original = run(replace(adjusted_dictionary, adjustments=Adjustments()), document_config=quiet)
    assert spot(tuned).decision == spot(original).decision
    assert spot(tuned).chosen is None and tuned.text == original.text


def test_changes_and_markdown_use_the_same_adjusted_selection(adjusted_dictionary):
    tr = Translator(adjusted_dictionary, lookup_embedder=None)
    options = {k: v for k, v in OPTIONS.items() if k != 'embedder'}
    for markdown in [False, True]:
        source = 'She is zzstate.' + ('\n' if markdown else '')
        output = translate(source, translator=tr, markdown=markdown, variety=1, **options)
        changes = translate_changes(source, translator=tr, markdown=markdown, variety=1, embedder='none', **options)
        assert output.text == changes.text
        substitution = next(c for c in changes.changes if c['kind'] == 'substitution')
        assert substitution['entry_id'] == 'zz-choice-b'


def test_large_finite_adjustments_preserve_finite_odds(adjusted_dictionary):
    from aussiefy.adjustments import Band

    huge = {key: tuple(replace(r, factor=1e308, normal=Band(.5, 1e308), popularity=Band(.25, 1e308))
                       for r in records) for key, records in adjusted_dictionary.adjustments.by_context.items()}
    dictionary = replace(adjusted_dictionary, adjustments=Adjustments(huge))
    record = spot(run(dictionary))
    assert all(math.isfinite(c.weight) for c in record.eligible)
    assert record.chosen.entry.id == 'zz-choice-b'


@pytest.mark.parametrize('all_exhausted', [False, True])
def test_repeat_penalty_underflow_is_not_rescued_or_made_nan(adjusted_dictionary, all_exhausted):
    from aussiefy.engine import PassObserver

    class LongText(PassObserver):
        def begin(self, run):
            run.state.entry_uses['zz-choice-b'] = 1000
            if all_exhausted:
                run.state.entry_uses['zz-choice-a'] = 1000

    result = run(adjusted_dictionary, _observer=LongText())
    values = weights(result)
    assert all(math.isfinite(w) for w in values.values())
    assert values['zz-choice-b'] == 0
    assert (values['zz-choice-a'] == 0) is all_exhausted
