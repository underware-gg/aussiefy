"""Verify the current dictionary against the immutable source-hunt calibration receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def recheck():
    from aussiefy import load_dictionary
    folder = ROOT / 'research/gate4-evidence-2026-11-14'
    archived = json.loads((folder / 'calibration.json').read_text())
    fresh = json.loads(json.dumps(runpy.run_path(str(folder / 'calibrate.py'))['compare']()))
    for key in ('before', 'after', 'weights', 'baseline_weights', 'baseline_labels', 'labels', 'label_changes'):
        if fresh[key] != archived[key]:
            raise AssertionError(f'calibration drift: {key}; review new evidence rather than rewriting the archive')
    dictionary = load_dictionary()
    terms = list(dictionary.entries.values()) + [r for entry in dictionary.entries.values() for r in entry.riffs] + list(dictionary.imagery)
    missing = [getattr(term, 'id', getattr(term, 'text', '')) for term in terms if not term.searched]
    if missing:
        raise AssertionError(f'EW4 searched records missing: {missing}')
    return {'reviewed': '2026-11-15', 'dictionary_id': dictionary.identity,
            'archive_dictionary_id': archived['dictionary_id'], 'terms': len(terms), 'all_terms_have_searched': True,
            'all_score_rows_equal_archive': True, 'weights': fresh['weights'],
            'baseline_labels': fresh['baseline_labels'], 'labels': fresh['labels'],
            'weight_only_label_changes': len(fresh['label_changes']),
            'archive_sha256': hashlib.sha256((folder / 'calibration.json').read_bytes()).hexdigest(),
            'score_rows_sha256': hashlib.sha256(json.dumps(fresh['after'], sort_keys=True).encode()).hexdigest(),
            'method_and_limits': fresh['method'],
            'acceptance': 'Calibration performed; not Rob acceptance and not independent measured accuracy.'}


if __name__ == '__main__':
    report = recheck()
    Path(__file__).with_name('calibration-recheck.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'weights'}, indent=2))
