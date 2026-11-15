"""Direct named witnesses from the Gate 4 acceptance audit."""
from dataclasses import replace

import pytest

from aussiefy import Translator, suggest_selection, translate_changes

BASE = {'vulgarity': 0, 'embellishment': 0, 'embedder': 'none'}


@pytest.mark.parametrize('level', range(1, 6))
def test_arvo_and_esky_are_kept_at_every_level_without_a_substitution_roll(translator, level):
    source = 'We put the esky outside this arvo.'
    cs = translate_changes(source, translator=translator, level=level, **BASE)
    own = {c['original']: c for c in cs.changes if c['kind'] == 'kept'}
    assert {'arvo', 'esky'} <= set(own)
    for term in ('arvo', 'esky'):
        change = own[term]
        assert change['output'] == term and not change['masks']
        assert change['alternatives'][-1]['kind'] == 'plain'
        assert all(o['vulgarity'] == 0 for o in change['alternatives'])
    assert all(r.roll is None and r.p == 0 for r in cs.result.records if r.kind == 'kept')


def test_general_omitted_and_literal_root_are_not_source_markers(dictionary):
    for text in ('The root of the problem remains.', 'She drove a car.'):
        cs = translate_changes(text, translator=Translator(dictionary, lookup_embedder=None), level=5, **BASE)
        assert not any(c['kind'] == 'kept' for c in cs.changes)
    esky = dictionary.entries['esky']
    for patch in ({'status': 'omit'}, {'reads_as': 'general'}):
        d = replace(dictionary, entries={esky.id: replace(esky, **patch)})
        cs = translate_changes('We took an esky.', translator=Translator(d, lookup_embedder=None), level=5, **BASE)
        assert not any(c['kind'] == 'kept' for c in cs.changes)


def test_unknown_unchanged_selection_has_the_no_dictionary_code(translator):
    source = 'Quantum entanglement.'
    body = suggest_selection(source, span=[0, len(source)-1], translator=translator, level=1, **BASE)
    assert body['text'] == source and body['outcome'] == 'not_in_dictionary'
    assert body['reading'] is None and not any(g['options'] for g in body['suggestions'])


def test_fantastic_dreams_is_held_and_cites_the_excluded_praise_reading(translator):
    cs = translate_changes('She had fantastic dreams.', translator=translator, level=5, **BASE)
    held = next(c for c in cs.changes if c['kind'] == 'held')
    assert held['original'] == held['output'] == 'fantastic'
    assert held['reading']['concept'] == 'FANCIFUL'
    praise = next(r for r in held['ruled_out'] if r['concept'] == 'EXCELLENT')
    assert praise['words'] and all(word['entry_id'] in cs.entries for word in praise['words'])


@pytest.mark.parametrize('seed', range(12))
@pytest.mark.parametrize('source', ['She wept. He was exhausted.', 'He believes a liar. She is hungry.',
                                   'She had fantastic dreams. His car is broken.'])
def test_observing_held_markers_preserves_unrelated_translation_choices(translator, source, seed):
    plain = translator.translate(source, level=5, seed=seed, **BASE)
    changes = translate_changes(source, translator=translator, level=5, seed=seed, **BASE)
    assert any(c['kind'] == 'held' for c in changes.changes)
    def choices(result):
        return [(r.span, r.roll, r.p, r.chosen.entry.id if r.chosen else None, r.output)
                for r in result.records if r.kind != 'held']
    assert changes.text == plain.text and choices(changes.result) == choices(plain)


def test_every_concept_example_has_an_explicit_rendering_audit_and_known_gaps_are_not_called_complete(dictionary):
    from pathlib import Path
    import runpy
    root = Path(__file__).resolve().parents[2]
    audit = runpy.run_path(str(root / 'research/gate4-self-review-2026-11-15/audit_plain_forms.py'))['audit']
    report = audit(Translator(dictionary, lookup_embedder=None))
    assert report['examples'] == sum(len(concept.examples) for concept in dictionary.concepts.values())
    assert report['all_examples_meet_R64'] is False  # Acceptance remains open, even though gap detection passes.
    assert {(row['concept'], row['example']) for row in report['unresolved']} == {
        ('HEARTBREAK', 'Her heart was broken.'), ('HEART_EFFORT', "Her heart wasn't in it."),
        ('DOUBT_IT', 'I doubt it could be done.')}
    assert all(not row.get('issues') for row in report['rows'] if row['status'] == 'rendered')
    restless = next(row for row in report['rows'] if row['concept'] == 'RESTLESS_SLEEP')
    assert restless['whole'] == 'I was tossing and turning.' and restless['status'] == 'rendered'
    assert all(row['source_preserved'] and 'rendered' not in row for row in report['unresolved'])


def test_elu_construction_stem_sources_keep_their_crowd_kind(dictionary):
    sources = [source for entry in dictionary.entries.values() for source in entry.sources
               if source.url and 'english.stackexchange.com' in source.url]
    assert sources and all(source.kind == 'crowd_dictionary' for source in sources)


def test_ew9_current_active_levels_have_individual_review_coverage(dictionary):
    import hashlib
    import json
    from pathlib import Path
    import yaml
    root = Path(__file__).resolve().parents[2]
    receipt = json.loads((root / 'research/gate4-self-review-2026-11-15/level-reconciliation.json').read_text())
    baseline_path = root / receipt['baseline']['path']
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == receipt['baseline']['sha256']
    reviewed = {row['id']: row['new'] for row in yaml.safe_load(baseline_path.read_text())}
    later = receipt['later_entries']
    assert len({row['rationale'] for row in later}) == len(later)
    assert all(row['authority_and_limits'] and row['status'] in
               {'approved as recorded', 'provisional retention recommendation'} for row in later)
    assert not set(reviewed) & {row['id'] for row in later}
    reviewed.update({row['id']: row['level'] for row in later})
    active = {entry.id: entry for entry in dictionary.entries.values() if entry.status == 'active'}
    assert set(active) <= set(reviewed)
    assert all(entry.incoherence == reviewed[entry.id] for entry in active.values())
    assert receipt['active_entries'] == len(active)
    assert not receipt['unreviewed_active_ids'] and not receipt['baseline']['current_level_mismatches']


def test_current_calibration_and_ew4_records_reproduce_the_source_hunt_receipt():
    import json
    from pathlib import Path
    import runpy
    root = Path(__file__).resolve().parents[2] / 'research/gate4-self-review-2026-11-15'
    fresh = runpy.run_path(str(root / 'recheck_calibration.py'))['recheck']()
    assert fresh == json.loads((root / 'calibration-recheck.json').read_text())
    assert fresh['terms'] == 1409 and fresh['all_terms_have_searched']
    assert fresh['all_score_rows_equal_archive'] and fresh['weight_only_label_changes'] == 333


@pytest.mark.parametrize('source,form,expected', [
    ('I doubt it could be done.', 'doubt it can be done', None),
    ('I doubt it could be done.', 'doubt {np} could be done', 'doubt it could be done'),
    ('I doubt it would work.', 'doubt {np} could be done', None),
    ('I doubt it would work.', 'doubt {np} would work', 'doubt it would work'),
])
def test_sentence_wording_preserves_a_required_modal_or_declines(dictionary, source, form, expected):
    from aussiefy.detect import read_meanings
    from aussiefy.plain_wording import plain_entry
    from aussiefy.realise import realise
    from aussiefy.text import tokenize
    detection = next(d for d in read_meanings(tokenize(source), dictionary).detections if 'DOUBT_IT' in d.concepts)
    concept = replace(dictionary.concepts['DOUBT_IT'], plain_forms={'vp': form})
    result = plain_entry(concept, detection, dictionary, tokens=tokenize(source))
    assert (realise(result[0], form, result[1]) if result else None) == expected
