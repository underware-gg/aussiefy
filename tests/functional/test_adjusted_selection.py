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


def personal(dictionary, term='zz-choice-a', weight=20, *, degree=None):
    from aussiefy.match_keys import make_match_key, parse_match_key

    key = next(iter(dictionary.adjustments.by_context))[0]
    return {'match': make_match_key(parse_match_key(key).root, degree=degree), 'term': term, 'weight': weight}


def relative_odds(tuned, original, numerator='zz-choice-a', denominator='zz-choice-b'):
    a, b = weights(tuned), weights(original)
    return (a[numerator] / a[denominator]) / (b[numerator] / b[denominator])


def test_popularity_uses_its_wider_band_without_changing_evidence_or_rolls(adjusted_dictionary):
    plain = replace(adjusted_dictionary, adjustments=Adjustments())
    popular = run(adjusted_dictionary, _tuning={'popularity': True})
    original = run(plain)
    assert relative_odds(popular, original, 'zz-choice-b', 'zz-choice-a') == pytest.approx(3)
    a, b = spot(popular), spot(original)
    assert a.det == b.det and a.roll == b.roll and a.p == b.p and a.rejected == b.rejected
    assert set(weights(popular)) == set(weights(original))
    assert popular._tuning == {'popularity': True, 'preferences': 0}
    assert adjusted_dictionary.identity == plain.identity
    assert adjusted_dictionary.entries == plain.entries
    assert any('(popularity band)' in c.why for c in a.eligible)


@pytest.mark.parametrize('source', ['She is zzstate.', 'She is really zzstate.'])
def test_personal_weight_applies_exactly_or_at_same_root_before_variety(adjusted_dictionary, source):
    pref = personal(adjusted_dictionary)
    original = run(adjusted_dictionary, source)
    tuned = run(adjusted_dictionary, source, _tuning={'preferences': [pref]})
    assert relative_odds(tuned, original) == pytest.approx(20)
    assert tuned._tuning['preferences'] == 1
    assert spot(run(adjusted_dictionary, source, variety=1,
                    _tuning={'preferences': [pref]})).chosen.entry.id == 'zz-choice-a'


def test_exact_key_beats_a_more_recent_preference_at_another_degree(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary, 'zz-choice-b', 100),
                   personal(adjusted_dictionary, weight=8, degree='strong')]
    source = 'She is really zzstate.'
    tuned = run(adjusted_dictionary, source, _tuning={'preferences': preferences})
    assert relative_odds(tuned, run(adjusted_dictionary, source)) == pytest.approx(8)
    assert tuned._tuning['preferences'] == 1


def test_latest_same_root_preference_is_the_only_fallback(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary, weight=8, degree='mild'),
                   personal(adjusted_dictionary, 'zz-choice-b', 100, degree='strong')]
    tuned = run(adjusted_dictionary, _tuning={'preferences': preferences})
    assert relative_odds(tuned, run(adjusted_dictionary)) == pytest.approx(8)
    assert tuned._tuning['preferences'] == 1


def test_only_latest_preference_at_an_exact_key_counts(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary, weight=8), personal(adjusted_dictionary, 'zz-choice-b', 100)]
    tuned = run(adjusted_dictionary, _tuning={'preferences': preferences})
    assert relative_odds(tuned, run(adjusted_dictionary)) == pytest.approx(8)
    assert tuned._tuning['preferences'] == 1


def test_neutral_exact_preference_blocks_older_root_fallback(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary, 'zz-choice-b', 100),
                   personal(adjusted_dictionary, weight=1, degree='strong')]
    source = 'She is really zzstate.'
    tuned = run(adjusted_dictionary, source, _tuning={'preferences': preferences})
    assert relative_odds(tuned, run(adjusted_dictionary, source)) == pytest.approx(1)
    assert tuned._tuning['preferences'] == 1


@pytest.mark.parametrize('term', ['zz-crude', 'zz-theme', 'stoked'])
def test_known_but_ineligible_preference_neither_grants_access_nor_falls_back(adjusted_dictionary, term):
    source = 'She is really zzstate.'
    preferences = [personal(adjusted_dictionary, weight=100),
                   personal(adjusted_dictionary, term, 1e308, degree='strong')]
    tuned = run(adjusted_dictionary, source, _tuning={'preferences': preferences})
    original = run(adjusted_dictionary, source)
    assert weights(tuned) == weights(original)
    assert tuned.text == original.text and tuned._tuning['preferences'] == 0
    assert spot(tuned).rejected == spot(original).rejected
    assert tuned.warnings == original.warnings


@pytest.mark.parametrize('weight', [0, -1, .99, float('inf'), -float('inf'), float('nan'),
                                    True, '2', None, 10 ** 400])
def test_invalid_preference_weights_fail_even_for_unknown_records(adjusted_dictionary, weight):
    from aussiefy.errors import UserError

    pref = {'match': 'unknown', 'term': 'unknown', 'weight': weight}
    with pytest.raises(UserError, match=r'preferences\[0\].weight.*finite.*at least 1'):
        run(adjusted_dictionary, _tuning={'preferences': [pref]})


@pytest.mark.parametrize('raw', [[], {'popularity': 1}, {'popularity': 'yes'}, {'extra': True},
                               {'preferences': {}}, {'preferences': ['bad']},
                               {'preferences': [{'match': 'x', 'term': 'y'}]},
                               {'preferences': [{'match': 3, 'term': 'y', 'weight': 2}]}])
def test_invalid_tuning_shapes_are_user_errors(adjusted_dictionary, raw):
    from aussiefy.errors import UserError

    with pytest.raises(UserError):
        run(adjusted_dictionary, _tuning=raw)


def test_unknown_matches_and_terms_warn_without_hiding_valid_preferences(adjusted_dictionary):
    from aussiefy.match_keys import make_match_root

    unknown_match = {**personal(adjusted_dictionary),
                     'match': make_match_root(['ZZ_UNKNOWN'], 'adj', 'zzunknown')}
    preferences = [unknown_match, personal(adjusted_dictionary, 'zz-unknown'),
                   {**personal(adjusted_dictionary), 'match': 'old-format-key'}, personal(adjusted_dictionary)]
    tuned = run(adjusted_dictionary, _tuning={'preferences': preferences})
    original = run(adjusted_dictionary)
    warnings = [w for w in tuned.warnings if w not in original.warnings]
    assert len(warnings) == 3
    assert 'preferences[0]: unknown source match' in warnings[0]
    assert 'preferences[1]: unknown term' in warnings[1]
    assert 'preferences[2]: unknown source match' in warnings[2]
    assert all('preference ignored' in w for w in warnings)
    assert relative_odds(tuned, original) == pytest.approx(20)
    assert tuned._tuning['preferences'] == 1


def test_preferences_and_popularity_multiply_without_a_personal_band(adjusted_dictionary):
    pref = personal(adjusted_dictionary, 'zz-choice-b', 100)
    tuned = run(adjusted_dictionary, _tuning={'popularity': True, 'preferences': [pref]})
    original = run(replace(adjusted_dictionary, adjustments=Adjustments()))
    assert relative_odds(tuned, original, 'zz-choice-b', 'zz-choice-a') == pytest.approx(300)
    assert tuned._tuning == {'popularity': True, 'preferences': 1}


def test_a_strong_preference_can_outweigh_general_english_penalty(adjusted_dictionary):
    entries = dict(adjusted_dictionary.entries)
    entries['zz-choice-a'] = replace(entries['zz-choice-a'], reads_as='general')
    dictionary = replace(adjusted_dictionary, entries=entries)
    original = run(dictionary)
    assert weights(original)['zz-choice-a'] < weights(original)['zz-choice-b']
    tuned = run(dictionary, variety=1, _tuning={'preferences': [personal(dictionary)]})
    assert spot(tuned).chosen.entry.id == 'zz-choice-a'
    assert entries['zz-choice-a'].reads_as == 'general'


def test_repetition_still_reduces_a_personally_preferred_weight(adjusted_dictionary):
    config = {**OPTIONS['document_config'],
              'profile': {**OPTIONS['document_config']['profile'], 'stack': 0}}
    tuned = run(adjusted_dictionary, 'She is zzstate. He is zzstate.', variety=0, document_config=config,
                _tuning={'preferences': [personal(adjusted_dictionary, weight=100)]})
    records = [r for r in tuned.records if 'ZZ_TUNING' in r.det.concepts]
    assert records[0].chosen.entry.id == 'zz-choice-a'
    odds = [{c.entry.id: c.weight for c in r.eligible} for r in records]
    assert ((odds[1]['zz-choice-a'] / odds[1]['zz-choice-b']) /
            (odds[0]['zz-choice-a'] / odds[0]['zz-choice-b'])) == pytest.approx(.2)
    assert tuned._tuning['preferences'] == 1  # One input preference, used at two spots.


def test_distinct_preferences_used_at_different_keys_are_counted_once_each(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary), personal(adjusted_dictionary, degree='strong')]
    tuned = run(adjusted_dictionary, 'She is zzstate. He is really zzstate. They are zzstate.',
                _tuning={'preferences': preferences})
    assert tuned._tuning['preferences'] == 2


def test_changes_locked_option_probes_do_not_count_ineligible_preferences(adjusted_dictionary):
    from aussiefy.changes import Watch, collect, finish

    tr = Translator(adjusted_dictionary, lookup_embedder=None)
    watch = Watch()
    result, drafts = collect(tr, 'She is zzstate.', **OPTIONS, _observer=watch,
                             _tuning={'preferences': [personal(adjusted_dictionary, 'zz-crude', 100)]})
    assert watch.run.preferences_used == set()  # Check the live state after the probes, not just its earlier summary.
    changed = finish(result, drafts, adjusted_dictionary)
    assert changed.result._tuning['preferences'] == 0
    assert any(o['entry_id'] == 'zz-crude' for c in changed.changes for o in c['locked'])


def test_changes_share_tuned_picks_and_preserve_current_public_contract(adjusted_dictionary):
    from aussiefy.changes import build

    tuning = {'popularity': True, 'preferences': [personal(adjusted_dictionary)]}
    tr = Translator(adjusted_dictionary, lookup_embedder=None)
    result = run(adjusted_dictionary, _tuning=tuning, variety=1)
    changed = build(tr, 'She is zzstate.', **{**OPTIONS, 'variety': 1}, _tuning=tuning)
    assert changed.text == result.text
    assert changed.result._tuning == result._tuning
    assert next(c for c in changed.changes if c['kind'] == 'substitution')['entry_id'] == 'zz-choice-a'
    assert changed.to_dict()['version'] == 4
    assert changed.to_dict()['tuning'] == result.to_dict()['tuning'] == result.tuning


def test_large_finite_personal_and_community_factors_do_not_overflow(adjusted_dictionary):
    from aussiefy.adjustments import Band

    huge = {key: tuple(replace(r, factor=1e308, normal=Band(.5, 1e308), popularity=Band(.25, 1e308))
                       for r in records) for key, records in adjusted_dictionary.adjustments.by_context.items()}
    dictionary = replace(adjusted_dictionary, adjustments=Adjustments(huge))
    tuned = run(dictionary, _tuning={'preferences': [personal(dictionary, 'zz-choice-b', 1e308)]})
    assert all(math.isfinite(c.weight) for c in spot(tuned).eligible)
    assert spot(tuned).chosen.entry.id == 'zz-choice-b'


def test_tuning_neither_rescues_failed_rolls_nor_changes_detection(adjusted_dictionary):
    tuning = {'popularity': True, 'preferences': [personal(adjusted_dictionary)]}
    quiet = {'garnish': [], 'profile': {'phonetic': 0, 'substitution': {'lexical': .01, 'phrase': .01, 'idiom': .01}}}
    original = run(adjusted_dictionary, document_config=quiet)
    tuned = run(adjusted_dictionary, document_config=quiet, _tuning=tuning)
    assert spot(tuned).det == spot(original).det
    assert spot(tuned).roll == spot(original).roll
    assert spot(tuned).decision == spot(original).decision
    assert spot(tuned).chosen is None and tuned.text == original.text


def test_tuning_is_deterministic_and_never_leaks_to_later_calls(adjusted_dictionary):
    tuning = {'popularity': True, 'preferences': [personal(adjusted_dictionary, weight=3)]}
    tr = Translator(adjusted_dictionary, lookup_embedder=None)
    original = tr.translate('She is zzstate.', **OPTIONS).to_dict()
    picks = set()
    for seed in range(24):
        a = tr.translate('She is zzstate.', **{**OPTIONS, 'seed': seed}, _tuning=tuning)
        b = tr.translate('She is zzstate.', **{**OPTIONS, 'seed': seed}, _tuning=tuning)
        assert a.to_dict() == b.to_dict() and a._tuning == b._tuning
        picks.add(spot(a).chosen.entry.id)
    assert picks == {'zz-choice-a', 'zz-choice-b'}
    assert tr.translate('She is zzstate.', **OPTIONS).to_dict() == original


def test_tuning_input_is_snapshotted_and_null_preferences_mean_none(adjusted_dictionary):
    from aussiefy.tuning import Tuning

    row = personal(adjusted_dictionary)
    raw = {'preferences': [row]}
    tuning = Tuning.prepare(raw, adjusted_dictionary)
    row['weight'] = 999
    raw['preferences'].clear()
    assert next(iter(tuning.exact.values())).weight == 20
    assert run(adjusted_dictionary, _tuning={'preferences': None}).to_dict() == run(adjusted_dictionary).to_dict()



@pytest.mark.parametrize('options', [{'level': 4}, {'vulgarity': 0}, {'vulgarity': 2},
                                    {'embellishment': 0}, {'embellishment': 1}])
def test_popularity_does_not_borrow_adjustments_from_other_dials(adjusted_dictionary, options):
    tuned = run(adjusted_dictionary, _tuning={'popularity': True}, **options)
    original = run(adjusted_dictionary, **options)
    assert weights(tuned) == weights(original)
    assert tuned.text == original.text


def test_personal_factor_does_not_restore_an_exhausted_repeat_weight(adjusted_dictionary):
    from aussiefy.engine import PassObserver

    class Exhausted(PassObserver):
        def begin(self, run):
            run.state.entry_uses['zz-choice-a'] = 1000

    tuned = run(adjusted_dictionary, _observer=Exhausted(),
                _tuning={'preferences': [personal(adjusted_dictionary, weight=1e308)]})
    assert weights(tuned)['zz-choice-a'] == 0
    assert tuned._tuning['preferences'] == 0


def test_markdown_units_share_the_runtime_and_public_tuning_report(adjusted_dictionary):
    from aussiefy.markdown import translate_document
    from aussiefy.policy import resolve

    tr = Translator(adjusted_dictionary, lookup_embedder=None)
    policy = tr.policy(**{**OPTIONS, 'variety': 1})
    tuning = {'popularity': True, 'preferences': [personal(adjusted_dictionary)]}
    result = translate_document('She is zzstate.\n\nHe is really zzstate.', tr, policy,
                                resolve(policy, adjusted_dictionary),
                                _tuning=tuning)
    assert len(result.units) == 2
    assert all(spot(unit.result).chosen.entry.id == 'zz-choice-a' for unit in result.units)
    assert all(unit.result._tuning['preferences'] == 1 for unit in result.units)
    assert result.to_dict()['tuning'] == {'popularity': True, 'preferences': 1}


def tuned_document(dictionary, source, tuning, *, changes=False, unit=None):
    from aussiefy.markdown import document_changes, translate_document
    from aussiefy.policy import resolve

    tr = Translator(dictionary, lookup_embedder=None)
    policy = tr.policy(**{**OPTIONS, 'variety': 1})
    effective = resolve(policy, dictionary)
    if changes:
        return document_changes(source, tr, policy, effective, _tuning=tuning)
    return translate_document(source, tr, policy, effective, unit=unit, _tuning=tuning)


@pytest.mark.parametrize('changes', [False, True])
def test_document_counts_one_preference_once_across_prose_units(adjusted_dictionary, changes):
    result = tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is really zzstate.',
                            {'popularity': True, 'preferences': [personal(adjusted_dictionary)]}, changes=changes)
    document = result.result if changes else result
    assert len(document.units) == 2
    assert [u.result._tuning['preferences'] for u in document.units] == [1, 1]
    assert document._tuning == {'popularity': True, 'preferences': 1}
    assert all(spot(u.result).chosen.entry.id == 'zz-choice-a' for u in document.units)
    assert result.to_dict()['tuning'] == {'popularity': True, 'preferences': 1}
    if changes:
        assert result.to_dict()['version'] == 4


def test_document_preserves_distinct_exact_and_root_preferences_without_double_counting(adjusted_dictionary):
    preferences = [personal(adjusted_dictionary), personal(adjusted_dictionary, 'zz-choice-b', 20, degree='strong')]
    doc = tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is really zzstate.\n\nThey are zzstate.',
                         {'preferences': preferences})
    assert [spot(u.result).chosen.entry.id for u in doc.units] == ['zz-choice-a', 'zz-choice-b', 'zz-choice-a']
    assert [u.result._tuning['preferences'] for u in doc.units] == [1, 1, 1]
    assert doc._tuning['preferences'] == 2


@pytest.mark.parametrize('source', ['', '```text\nShe is zzstate.\n```\n', 'She is zzstate.\n\nHe is zzstate.'])
def test_document_reports_unknown_preferences_once_even_without_prose(adjusted_dictionary, source):
    pref = personal(adjusted_dictionary, 'unknown-term')
    doc = tuned_document(adjusted_dictionary, source, {'popularity': True, 'preferences': [pref]})
    warnings = [w for w in doc.warnings if 'unknown term' in w]
    assert len(warnings) == 1
    assert doc._tuning == {'popularity': True, 'preferences': 0}
    if source.startswith('```') or not source:
        assert doc.units == [] and doc.text == source


@pytest.mark.parametrize('changes', [False, True])
def test_a_document_prepares_tuning_once_including_change_probes(adjusted_dictionary, monkeypatch, changes):
    from aussiefy.tuning import Tuning

    prepare = Tuning.prepare
    calls = []

    def counted(cls, raw, dictionary):
        calls.append(raw)
        return prepare(raw, dictionary)

    monkeypatch.setattr(Tuning, 'prepare', classmethod(counted))
    tuning = {'preferences': [personal(adjusted_dictionary)]}
    tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is zzstate.', tuning, changes=changes)
    assert calls == [tuning]


def test_invalid_document_tuning_fails_before_processing_any_unit(adjusted_dictionary):
    from aussiefy.errors import UserError

    called = []
    with pytest.raises(UserError, match='finite number'):
        tuned_document(adjusted_dictionary, 'She is zzstate.',
                        {'preferences': [personal(adjusted_dictionary, weight=float('inf'))]},
                        unit=lambda *args, **kwargs: called.append(args))
    assert not called


def test_document_tuning_snapshots_inputs_before_unit_callbacks(adjusted_dictionary):
    row = personal(adjusted_dictionary)
    raw = {'preferences': [row]}
    tr = Translator(adjusted_dictionary, lookup_embedder=None)

    def unit(text, **options):
        row['term'] = 'zz-choice-b'
        row['weight'] = 1e308
        raw['preferences'].clear()
        return tr.translate(text, **options)

    doc = tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is zzstate.', raw, unit=unit)
    assert all(spot(u.result).chosen.entry.id == 'zz-choice-a' for u in doc.units)
    assert doc._tuning['preferences'] == 1


def test_document_change_probes_cannot_inflate_aggregate_preference_counts(adjusted_dictionary):
    result = tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is zzstate.',
                            {'preferences': [personal(adjusted_dictionary, 'zz-crude', 100)]}, changes=True)
    assert result.result._tuning['preferences'] == 0
    assert all(u.result._tuning_report.used == frozenset() for u in result.result.units)
    assert any(o['entry_id'] == 'zz-crude' for c in result.changes for o in c['locked'])


def test_tuning_reports_are_immutable_and_summaries_are_detached(adjusted_dictionary):
    from dataclasses import FrozenInstanceError

    doc = tuned_document(adjusted_dictionary, 'She is zzstate.\n\nHe is zzstate.',
                         {'preferences': [personal(adjusted_dictionary)]})
    summary = doc._tuning
    summary['preferences'] = 999
    assert doc._tuning['preferences'] == 1
    unit_summary = doc.units[0].result._tuning
    unit_summary['preferences'] = 999
    assert doc.units[0].result._tuning['preferences'] == 1
    with pytest.raises(FrozenInstanceError):
        doc._tuning_report.popularity = True
    assert doc._tuning_report.used == frozenset({0})


def test_untuned_document_calls_stay_isolated_after_tuned_calls(adjusted_dictionary):
    source = 'She is zzstate.\n\nHe is zzstate.'
    original = tuned_document(adjusted_dictionary, source, None).to_dict()
    tuning = {'popularity': True, 'preferences': [personal(adjusted_dictionary)]}
    a = tuned_document(adjusted_dictionary, source, tuning, changes=True)
    b = tuned_document(adjusted_dictionary, source, tuning, changes=True)
    assert a.to_dict() == b.to_dict() and a.result._tuning == b.result._tuning
    assert tuned_document(adjusted_dictionary, source, None).to_dict() == original
