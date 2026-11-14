"""Paired offline quiz timing against the frozen dev checkpoint, with the same current dictionary/model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def baseline_module(name, ref):
    source = subprocess.check_output(['git', 'show', f'{ref}:aussiefy/{name}.py'], cwd=ROOT, text=True)
    if name == 'explore':
        source = source.replace('from .lookup import lookup', 'from ._quiz_baseline_lookup import lookup')
        source = source.replace('from .quiz import askable_pool, select_question',
                                'from ._quiz_baseline_quiz import askable_pool, select_question')
    module = types.ModuleType('aussiefy._quiz_baseline_' + name)
    module.__package__ = 'aussiefy'
    sys.modules[module.__name__] = module
    exec(compile(source, f'{ref}:aussiefy/{name}.py', 'exec'), module.__dict__)
    return module


def benchmark(ref):
    if not re.fullmatch('[0-9a-f]{40}', ref):
        raise ValueError('baseline-ref must be a full commit hash')
    from aussiefy import Translator, meaning_quiz
    baseline_module('lookup', ref)
    baseline_module('quiz', ref)
    old = baseline_module('explore', ref).meaning_quiz
    tr = Translator(lookup_embedder='bundled')
    # Warm the model and both algorithms. Timings exclude dictionary load and first model/index setup.
    for operation in (old, meaning_quiz):
        operation(seed=99, vulgarity=0, embellishment=0, translator=tr)
    rows = []
    for cap in range(4):
        for seed in range(10):
            responses, seconds = {}, {}
            order = [('before', old), ('after', meaning_quiz)]
            if seed % 2:
                order.reverse()
            for label, operation in order:
                started = time.perf_counter()
                responses[label] = operation(seed=seed, vulgarity=cap, embellishment=0, translator=tr)
                seconds[label] = time.perf_counter() - started
            if responses['before'] != responses['after']:
                raise AssertionError(f'seeded quiz changed at {seed=}, {cap=}')
            rows.append({'seed': seed, 'vulgarity': cap, **seconds,
                         'response_sha256': hashlib.sha256(json.dumps(responses['after'], sort_keys=True).encode()).hexdigest(),
                         'entry_id': responses['after']['entry']['id'], 'options': responses['after']['options'],
                         'answer': responses['after']['answer']})
    means = {key: statistics.mean(row[key] for row in rows) for key in ('before', 'after')}
    return {'baseline_commit': ref, 'dictionary_id': tr.dictionary.identity, 'python': platform.python_version(),
            'platform': platform.platform(), 'model': tr.lookup_embedder.name, 'questions': len(rows),
            'method': 'Warm, serial paired calls; alternating order; same current dictionary and model. No network.',
            'mean_seconds': means, 'median_seconds': {key: statistics.median(row[key] for row in rows)
                for key in means}, 'max_seconds': {key: max(row[key] for row in rows) for key in means},
            'mean_reduction_fraction': 1 - means['after'] / means['before'],
            'all_responses_identical': True,
            'runtime_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / 'aussiefy/lookup.py', ROOT / 'aussiefy/explore.py', ROOT / 'aussiefy/quiz.py')},
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = benchmark(args.baseline_ref)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}, indent=2))
