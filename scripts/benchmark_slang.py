"""Measure reproduction of independently reviewed target expressions, not general translation quality.

Run from an installed development checkout: python scripts/benchmark_slang.py --output report.json
Labels and inputs are fixed; the script does not derive labels from the current dictionary or outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml

from aussiefy.engine import Translator
from aussiefy.static import dictionary_fingerprint
from aussiefy.terms import fold, restore_g
from aussiefy.text import sentences, tokenize

ROOT = Path(__file__).resolve().parents[1]
LABELS = Path('tests/fixtures/curated-slang-labels.yaml')


def words(text: str) -> tuple[str, ...]:
    """Fixed case, drawl-g and punctuation normalisation; no learned vocabulary or stemming."""
    return tuple(re.findall(r'[a-z0-9]+', restore_g(fold(text))))


def occurrences(text: str, forms: list[str]) -> int:
    """Literal normalised expression occurrences, never spanning a sentence boundary."""
    phrases = {words(form) for form in forms}
    count = 0
    for sentence in sentences(tokenize(text)):
        tokens = words(text[sentence[0].start:sentence[-1].end])
        for phrase in phrases:
            width = len(phrase)
            count += sum(tokens[i:i+width] == phrase for i in range(len(tokens)-width+1))
    return count


def load_labels(root: Path) -> dict:
    """Refuse drift in paired inputs before measuring an established label set."""
    fixture = yaml.safe_load((root / LABELS).read_text(encoding='utf-8'))
    for doc in fixture['documents']:
        for kind in ('source', 'target'):
            path = root / doc[kind]
            if hashlib.sha256(path.read_bytes()).hexdigest() != doc[kind+'_sha256']:
                raise ValueError(f"{doc['id']}: {kind} changed; review a new benchmark version")
    return fixture


def measure(root: Path = ROOT, translator: Translator | None = None) -> dict:
    fixture = load_labels(root)
    contract = fixture['contract']
    policy = {k:v for k,v in contract.items() if k != 'seeds'}
    translator = translator or Translator(lookup_embedder=None)
    docs = []
    for doc in fixture['documents']:
        source = (root / doc['source']).read_text(encoding='utf-8')
        outputs = [translator.translate(source, seed=seed, **policy).text for seed in contract['seeds']]
        rows = []
        for label in doc['labels']:
            counts = [occurrences(output, label['forms']) for output in outputs]
            rows.append({'id':label['id'], 'forms':label['forms'],
                         'hit_seeds':[s for s,n in zip(contract['seeds'], counts) if n],
                         'output_occurrences':counts})
        hits = sum(bool(row['hit_seeds']) for row in rows)
        docs.append({'id':doc['id'], 'unique_expressions':len(rows), 'unique_hits':hits,
                     'share':hits/len(rows), 'labels':rows,
                     'output_sha256':[hashlib.sha256(x.encode()).hexdigest() for x in outputs]})
    return {'schema_version':1, 'measure':fixture['measure'], 'contract':contract,
            'labels_sha256':hashlib.sha256((root / LABELS).read_bytes()).hexdigest(),
            'dictionary_sha256':dictionary_fingerprint(root/'aussiefy/data'),
            'scorer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'documents':docs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='save the complete measurement report')
    args = parser.parse_args()
    result = measure()
    result['git_base'] = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    result['working_tree_dirty'] = bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True))
    if args.output:
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for doc in result['documents']:
        print(f"{doc['id']}: {doc['unique_hits']}/{doc['unique_expressions']} reviewed target expressions ({doc['share']:.1%})")
    print('Wording reproduction only; output occurrence counts are unaligned, not source-event fidelity scores.')


if __name__ == '__main__':
    main()
