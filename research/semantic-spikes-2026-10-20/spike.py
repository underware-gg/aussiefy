"""Bounded, offline pair/degree diagnostics; run with the pinned training environment and WordNet."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aussiefy import Translator, lookup  # noqa: E402
from aussiefy.degree import realised_degree  # noqa: E402
from scripts import train_embedder as trainer  # noqa: E402

PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'garnish': {'riff': 0}, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}
SOURCES = [
    'I am absolutely starving.', 'I am really starving.', 'I am very hungry.',
    'I am hungry enough to eat anything.', 'I am so hungry that I could cry.',
    'I am too hungry to sleep.', 'She is slightly drunk.', 'She is very tipsy.',
    'She is drunk enough to fall over.', 'She is legless enough to fall over.',
]


def run():
    trainer.R = trainer.load_recipe()
    dictionary = trainer.load_dictionary()
    entries = trainer.entries(dictionary)
    positives = trainer.pairs(dictionary, entries)
    senses = trainer.sense_negatives(dictionary, entries)
    opposites = trainer.opposite_negatives(dictionary, entries)
    key = lambda pair: tuple(sorted(text.casefold() for text in pair))
    conflicts = sorted({key(p) for p in positives} & {key(p) for p in senses + opposites})
    bridges = [{'entry': e.id, 'concepts': list(e.concept)} for e in entries if len(e.concept) > 1]
    tr = Translator(dictionary, lookup_embedder=None)
    rows = []
    for source in SOURCES:
        result = tr.translate(source, level=5, vulgarity=3, embellishment=0, embedder='none',
                              document_config={'profile': PROFILE})
        rows.append({'source': source, 'output': result.text,
                     'predicates': [{'concepts': list(r.det.concepts), 'lexical': r.det.semantic_degree,
                                     'qualifier': list(r.det.degree_qualifier), 'relational': r.det.result_clause,
                                     'realised': {c: realised_degree(b, r.det.degree_qualifier)
                                                  for c, b in r.det.semantic_degree.items()},
                                     'eligible': sorted(c.entry.id for c in r.eligible)}
                                    for r in result.records if r.det.degree_concepts]})
    paths = [ROOT / 'scripts/train_embedder.py', ROOT / 'training/recipe.yaml',
             *sorted((ROOT / 'aussiefy').glob('*.py')), *sorted((ROOT / 'aussiefy/data').rglob('*.yaml'))]
    return {'inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'counts': {'positive': len(positives), 'wrong_sense': len(senses), 'opposite': len(opposites),
                       'concept_counts_per_entry': dict(Counter(len(e.concept) for e in entries))},
            'unordered_label_conflicts': conflicts, 'multi_concept_bridges': bridges, 'degree': rows,
            'lookup': {q: [e['id'] for e in lookup(q, translator=tr, vulgarity=3)['results']]
                       for q in ('absolutely starving', 'hungry enough to eat anything', 'sick of work', 'tired of life')}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(run(), indent=2) + '\n')
