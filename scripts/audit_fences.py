"""Derive protected phrases' alternative readings and report missing evidence for review.

Run with the development package installed: python scripts/audit_fences.py [--output audit.json]
Never changes dictionary data or removes protections.
"""

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from aussiefy import load_dictionary
from aussiefy.fence_readings import derive_fence_readings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    dictionary = load_dictionary()
    rows = derive_fence_readings(dictionary)
    report = {
        'dictionary': dictionary.identity,
        'method': 'Forced substitution, no model, drawl, garnish or dialect pass; normal source and candidate checks. '
                  'Dialect evidence comes from guarded swaps. Generated examples are bounded, not exhaustive.',
        'fences': len(rows),
        'needs_audit': sum(row.needs_audit for row in rows),
        'variants_needing_audit': sum(not variant.meanings and not variant.dialect
                                     for row in rows for variant in row.variants),
        'diagnostics': dict(sorted(Counter(trial.effect for row in rows for trial in row.trials).items())),
        'results': [{'phrase': row.fence.phrase, 'frame': row.fence.frame, 'reason': row.fence.reason,
                     'ruled_out': [asdict(meaning) for meaning in row.meanings],
                     'dialect': [asdict(swap) for swap in row.dialect],
                     'needs_audit': row.needs_audit,
                     'generated_examples_truncated': row.generated_examples_truncated,
                     'variants': [{**asdict(variant), 'needs_audit': not variant.meanings and not variant.dialect}
                                  for variant in row.variants],
                     'trials': [asdict(trial) for trial in row.trials]} for row in rows],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
