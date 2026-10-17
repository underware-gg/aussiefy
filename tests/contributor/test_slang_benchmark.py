"""Validate independently curated labels and the fixed wording scorer, without tuning output scores."""
import hashlib
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.benchmark_slang import LABELS, load_labels, measure, occurrences, words

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('text,forms,expected', [
    ('She was knackered. Knackered, she was.', ['knackered'], 2),
    ('Blokesmanship.', ['blokes'], 0),
    ('Proper. Crack!', ['proper crack'], 0),
    ("Brand-spankin'-new.", ['brand-spanking-new'], 1),
    ("Carked it.", ['carked it','CARKED IT'], 1),
    ("Shootin’ through like a Bondi tram.", ["shooting through like a Bondi tram"], 1),
])
def test_fixed_normalisation_and_sentence_boundaries(text, forms, expected):
    assert occurrences(text, forms) == expected


def test_reviewed_fixture_is_fixed_to_its_actual_sources_and_targets():
    fixture = load_labels(ROOT)
    assert fixture['schema_version'] == 1
    assert len({d['id'] for d in fixture['documents']}) == 2
    for doc in fixture['documents']:
        source = (ROOT / doc['source']).read_text()
        target = (ROOT / doc['target']).read_text()
        assert len({label['id'] for label in doc['labels']}) == len(doc['labels'])
        for label in doc['labels']:
            assert label['meaning'] and label['source_anchors']
            assert all(words(form) and occurrences(target,[form]) for form in label['forms'])
            assert all(anchor.lower() in source.lower() for anchor in label['source_anchors'])
        assert all(row['span'].lower() in target.lower() and row['reason'] for row in doc['exclusions'])
    assert fixture['documents'][1]['source'].endswith('goldilocks_full.txt')
    assert [len(d['labels']) for d in fixture['documents']] == [10,22]


def test_changed_paired_source_requires_a_new_review(tmp_path):
    fixture = load_labels(ROOT)
    paths = [LABELS] + [Path(doc[k]) for doc in fixture['documents'] for k in ('source','target')]
    for path in paths:
        (tmp_path/path).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/path,tmp_path/path)
    changed = tmp_path/fixture['documents'][0]['source']
    changed.write_text(changed.read_text()+'New sentence.\n')
    with pytest.raises(ValueError, match='source changed'):
        load_labels(tmp_path)


def test_repetition_does_not_inflate_unique_expression_coverage():
    class Probe:
        def translate(self, text, *, seed, **policy):
            assert policy == dict(level=5,vulgarity=2,embellishment='troppo',
                                  document_type='general',embedder='none')
            return SimpleNamespace(text='Blokes, blokes.' if seed == 0 else '')

    report = measure(ROOT,Probe())
    getty,goldilocks = report['documents']
    assert getty['unique_hits'] == 1 and goldilocks['unique_hits'] == 0
    label = next(row for row in getty['labels'] if row['id'] == 'blokes')
    assert label['hit_seeds'] == [0] and label['output_occurrences'] == [2]+[0]*9


def test_frozen_baseline_identifies_the_label_set_and_scorer():
    import json

    report = json.loads((ROOT/'research/maintenance-2026-10-17/slang-baseline.json').read_text())
    assert report['labels_sha256'] == hashlib.sha256((ROOT/LABELS).read_bytes()).hexdigest()
    assert re.fullmatch('[a-f0-9]{64}',report['scorer_sha256'])
    assert re.fullmatch('[a-f0-9]{64}',report['dictionary_sha256'])
    for doc in report['documents']:
        assert doc['unique_hits'] == sum(bool(row['hit_seeds']) for row in doc['labels'])
        assert len(doc['output_sha256']) == 10
        assert all(len(row['output_occurrences']) == 10 for row in doc['labels'])
