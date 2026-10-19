"""Offline, standalone epoch-zero sampler diagnostic, not a captured training schedule or a fit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import train_embedder as trainer  # noqa: E402


def run():
    import torch
    from datasets import Dataset
    from sentence_transformers.base.sampler import NoDuplicatesBatchSampler

    trainer.R = trainer.load_recipe()
    dictionary = trainer.load_dictionary()
    pairs = trainer.pairs(dictionary, trainer.entries(dictionary))
    data = Dataset.from_dict({'anchor': [a for a, _ in pairs], 'positive': [b for _, b in pairs]})
    known = {(a.casefold(), b.casefold()) for a, b in pairs}
    rows = []
    for size in (trainer.R['finetune']['batch'], trainer.R['static_tune']['batch']):
        sampler = NoDuplicatesBatchSampler(data, batch_size=size, drop_last=False,
                                           generator=torch.Generator(), seed=trainer.R['seed'])
        batches = samples = conflicts = affected = 0
        examples = []
        for indices in sampler:
            batches += 1
            samples += len(indices)
            hits = [(i, j) for i in indices for j in indices if i != j
                    and (pairs[i][0].casefold(), pairs[j][1].casefold()) in known]
            conflicts += len(hits)
            affected += bool(hits)
            for i, j in hits[:max(0, 6 - len(examples))]:
                examples.append({'anchor': pairs[i][0], 'positive': pairs[i][1],
                                 'in_batch_negative': pairs[j][1]})
        rows.append({'batch_size': size, 'batches': batches, 'rows': samples,
                     'known_positive_negative_logits': conflicts, 'affected_batches': affected, 'examples': examples})
    return {'scope': __doc__, 'seed': trainer.R['seed'],
            'driver_sha256': trainer.sha256(Path(__file__)),
            'sampler_sha256': trainer.sha256(Path(inspect.getfile(NoDuplicatesBatchSampler))),
            'trainer_sha256': trainer.sha256(Path(trainer.__file__)),
            'dictionary_sha256': trainer.dictionary_fingerprint(), 'recipe_sha256': trainer.sha256(trainer.RECIPE_PATH),
            'pairs_sha256': hashlib.sha256(json.dumps(pairs).encode()).hexdigest(),
            'versions': {name: importlib.metadata.version(name) for name in ('torch', 'sentence-transformers', 'datasets')},
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(run(), indent=2) + '\n')
