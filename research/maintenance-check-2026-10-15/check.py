"""Repeat the offline maintenance measurements without training or calling a model API."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aussiefy import Translator, harness  # noqa: E402
from aussiefy.static import MODEL_DIR, dictionary_fingerprint  # noqa: E402

QUERIES = [
    'give them a bell', 'give Bob a bell', 'give them a bell.', 'shouted', 'harmless', 'probably',
    'very cold', 'raining heavily', 'worked very hard', 'not out of the question', 'officials',
    'stuff up', 'retire', 'very tired', 'a top bloke',
]


def measure() -> dict:
    spec = importlib.util.spec_from_file_location('train_embedder', ROOT / 'scripts/train_embedder.py')
    training = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(training)
    training.R = training.load_recipe()
    translator = Translator(lookup_embedder='bundled')
    encoder = training.Bundled(None)
    reference = training.reference(translator.dictionary, encoder, encoder.m.lookup_threshold)
    lookups = []
    for query in QUERIES:
        result = harness.lookup(query, level=5, vulgarity=3, translator=translator)
        lookups.append({'query': query, 'results': [
            {key: row[key] for key in ('form', 'concepts', 'match')} for row in result['results']]})
    return {
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'model': encoder.m.name,
        'git_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dictionary_sha256': dictionary_fingerprint(),
        'reference_sha256': training.sha256(ROOT / 'training/reference.yaml'),
        'lookup_sha256': training.sha256(ROOT / 'aussiefy/lookup.py'),
        'evaluator_sha256': training.sha256(Path(__file__)),
        'model_files': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sorted(MODEL_DIR.iterdir()) if path.is_file()},
        'reference': reference,
        'gaps': training.gap_benchmark(translator.dictionary, encoder),
        'toolkit_policy': {'level': 5, 'vulgarity': 3, 'lookup_embedder': 'bundled'},
        'toolkit_lookups': lookups,
        'new_weights_exported': False,
        'live_retellings_run': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = measure()
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    reference = report['reference']
    print(f"{reference['passed']}/{reference['required']} required references; report: {args.output}")
    return 0 if reference['passed'] == reference['required'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
