"""Reproduce the score comparison from the source facts at the recorded checkout."""

from dataclasses import asdict
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aussiefy import load_dictionary
from aussiefy.evidence import assess, parse_weights


def rows(dictionary, weights):
    terms = [(f'entry/{e.id}', e) for e in dictionary.entries.values()]
    terms += [(f'riff/{e.id}/{i}', r) for e in dictionary.entries.values() for i, r in enumerate(e.riffs)]
    terms += [(f'imagery/{image.id}', image) for image in dictionary.imagery]
    out = []
    for key, term in terms:
        a = assess(term, weights)
        out.append({'key': key, 'form': getattr(term, 'form', getattr(term, 'text', '')),
                    'score': a.attestation.score, 'bars': a.attestation.bars, 'evidence': a.evidence,
                    'counts': dict(a.attestation.counts)})
    return sorted(out, key=lambda r: r['key'])


def compare():
    dictionary = load_dictionary()
    baseline = parse_weights(yaml.safe_load((Path(__file__).with_name('baseline-weights.yaml')).read_text()))
    current = dictionary.evidence_weights
    before, after = rows(dictionary, baseline), rows(dictionary, current)
    by_key = {row['key']: row for row in after}
    assert len(by_key) == len(after)
    changes = [{'key': r['key'], 'before': r['evidence'], 'after': by_key[r['key']]['evidence']}
               for r in before if r['evidence'] != by_key[r['key']]['evidence']]
    inputs = [ROOT / 'aussiefy/data/attestation.yaml',
              Path(__file__).with_name('searched-reconciliation.json'),
              Path(__file__).with_name('followthrough-integration.json')]
    return {'schema': 'aussiefy-source-weight-calibration-1', 'reviewed': '2026-11-14',
            'dictionary_id': dictionary.identity, 'terms': len(after),
            'method': 'Source-based curator sanity check; no independent gold labels or measured classification accuracy.',
            'input_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            'baseline_weights': asdict(baseline), 'weights': asdict(current),
            'baseline_labels': dict(Counter(r['evidence'] for r in before)),
            'labels': dict(Counter(r['evidence'] for r in after)),
            'label_changes': changes, 'before': before, 'after': after}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = compare()
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: report[key] for key in ('terms', 'baseline_labels', 'labels')}, indent=2))
