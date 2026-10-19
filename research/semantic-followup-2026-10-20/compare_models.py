"""Compare actual package readers under the same final dictionary and scoped-lookup runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aussiefy import Translator, load_dictionary
from aussiefy.harness import lookup
from aussiefy.static import MODEL_DIR, StaticEmbedder, dictionary_fingerprint


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--old-model', type=Path, default=MODEL_DIR)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    query_path = Path(__file__).with_name('lookup-queries.json')
    selection = json.loads(query_path.read_text())
    queries = list(dict.fromkeys(q for group in ('historical', 'source_audit', 'semantic_followup')
                                for q in selection[group]))
    settings = {'level': 5, 'vulgarity': 'uncle-bob', 'limit': 8, 'embellishment': 'dinkum',
                'document_type': 'general'}
    dictionary = load_dictionary()
    models = []
    for label, folder in [('previous', args.old_model), ('candidate', args.candidate)]:
        model = StaticEmbedder(folder)
        tr = Translator(dictionary, lookup_embedder=model)
        rows = []
        for query in queries:
            answer = lookup(query, translator=tr, **settings)
            rows.append({'query': query, 'results': [{key: row[key] for key in ('id', 'concepts', 'match', 'score')}
                                                    for row in answer['results']],
                         'note': answer.get('note')})
        models.append({'label': label, 'version': model.version,
                       'asset_sha256': {name: digest(folder/name) for name in ('meta.json', 'vocab.txt', 'vectors.f16')},
                       'lookups': rows})
    result = {'scope': __doc__, 'query_selection': selection, 'settings': settings,
              'dictionary_sha256': dictionary_fingerprint(), 'query_sha256': digest(query_path),
              'driver_sha256': digest(Path(__file__)),
              'runtime_sha256': {name: digest(ROOT/'aussiefy'/name)
                                 for name in ('lookup.py', 'detect.py', 'static.py', 'degree.py')},
              'git_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
              'models': models}
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(queries)} diagnostic queries; actual previous and candidate package readers compared')


if __name__ == '__main__':
    main()
