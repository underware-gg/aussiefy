"""Raw reference-ranking probes for the three rejected-fit failures; no runtime lookup filters."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aussiefy.lookup import meaning_texts  # noqa: E402
from aussiefy.static import MODEL_DIR, dictionary_fingerprint  # noqa: E402
from scripts import train_embedder as trainer  # noqa: E402


def run(candidate):
    dictionary = trainer.load_dictionary()
    entries = trainer.entries(dictionary)
    items = [(e.id, e.concept, text) for e in entries for text in meaning_texts(e, dictionary)]
    queries = ['girl', 'feeling really down', 'a good mate of mine']
    rows, assets = [], {}
    for name, path in [('bundled', MODEL_DIR), ('rejected', candidate)]:
        encoder = trainer.Bundled(path)
        assets[name] = {p: trainer.sha256(path / p) for p in ('meta.json', 'vocab.txt', 'vectors.f16')}
        similarities = encoder.sims(queries, [x[2] for x in items])
        for query, scores in zip(queries, similarities):
            ordered = sorted(range(len(items)), key=lambda i: -float(scores[i]))
            seen, top = set(), []
            for i in ordered:
                entry_id, concepts, text = items[i]
                if entry_id in seen:
                    continue
                seen.add(entry_id)
                top.append({'entry': entry_id, 'concepts': list(concepts), 'winning_text': text,
                            'score': round(float(scores[i]), 6)})
                if len(top) == 6:
                    break
            rows.append({'reader': name, 'query': query, 'top_entries': top})
    return {'scope': __doc__, 'assets': assets, 'dictionary_sha256': dictionary_fingerprint(),
            'driver_sha256': trainer.sha256(Path(__file__)),
            'trainer_sha256': trainer.sha256(Path(trainer.__file__)), 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(run(args.candidate), indent=2) + '\n')
