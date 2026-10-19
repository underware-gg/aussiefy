"""Report frozen Gettysburg wording anchors under precise and narrative policies; never retune anchors."""
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aussiefy import Translator  # noqa: E402
from aussiefy.terms import fold, restore_g  # noqa: E402

source = ROOT / 'tests/corpus/reference/gettysburg.txt'
anchors_path = ROOT / 'tests/fixtures/gettysburg-wording-anchors.yaml'
frozen = yaml.safe_load(anchors_path.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest() == frozen['source_sha256']
tr = Translator(lookup_embedder=None)
rows = []
for kind, step in [('auto', 'deadset'), ('auto', 'dinkum'), ('auto', 'troppo'), ('technical', 'troppo')]:
    results = [tr.translate(source.read_text(), level=5, seed=seed, document_type=kind,
                            embellishment=step) for seed in range(10)]
    outputs = [restore_g(fold(r.text)).replace('-', ' ') for r in results]
    hits = [any(all(restore_g(word) in output for word in anchor['content']) for output in outputs)
            for anchor in frozen['anchors']]
    rows.append({'document_type': kind, 'detected_genre': results[0].genre.name, 'embellishment': step,
                 'quantity_approximation': results[0].embellishment.quantity_approximation,
                 'hits': sum(hits), 'denominator': len(hits), 'coverage': sum(hits)/len(hits),
                 'anchor_hits': hits,
                 'duration_substitutions': sum(any('LONG_AGO' in r.det.concepts and r.substituted
                                                   for r in result.records) for result in results),
                 'opening_samples': [r.text[:80] for r in results],
                 'output_sha256': [hashlib.sha256(r.text.encode()).hexdigest() for r in results]})
print(json.dumps({'source_sha256': frozen['source_sha256'],
                  'anchors_sha256': hashlib.sha256(anchors_path.read_bytes()).hexdigest(),
                  'level': 5, 'seeds': list(range(10)),
                  'measure': 'Frozen historical wording overlap, not a semantic quality score.', 'runs': rows}, indent=2))
