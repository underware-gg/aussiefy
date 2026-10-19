"""Isolated dry release with cached-only base resolution and retained failure evidence."""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import huggingface_hub
from aussiefy.static import dictionary_fingerprint
from scripts import train_embedder as t
from base_integrity import snapshot_manifest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True, help='fresh directory for work, candidate and evidence')
parser.add_argument('--cache', type=Path, required=True, help='local Hugging Face cache containing the exact pinned base')
parser.add_argument('--nltk-data', type=Path, required=True, help='local NLTK data containing corpora/wordnet.zip')
options = parser.parse_args()
import nltk
nltk.data.path.insert(0, str(options.nltk_data))
options.out.mkdir(parents=True, exist_ok=False)
t.R = t.load_recipe()
work = options.out / 'work'
dest = options.out / 'candidate'
evidence_path = options.out / 'evidence.json'
if work.exists() or dest.exists() or evidence_path.exists():
    raise RuntimeError('Fresh work, destination and evidence paths must not exist')
git = t.git_state()
# Record exact inputs, train fresh evaluation and full models, and reject input drift.
input_roots = [Path(t.ROOT) / name for name in ('aussiefy', 'training', 'scripts')]
def input_manifest():
    return {str(p.relative_to(t.ROOT)): t.sha256(p) for root in input_roots
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
frozen_inputs = input_manifest()
BASE_FILES = ['model.safetensors', 'config.json', 'tokenizer.json', 'tokenizer_config.json',
              'special_tokens_map.json', 'vocab.txt', 'modules.json', 'sentence_bert_config.json',
              'config_sentence_transformers.json', '1_Pooling/config.json', '2_Normalize/config.json',
              'README.md', '.gitattributes']
original_snapshot = huggingface_hub.snapshot_download
cached = Path(original_snapshot(t.R['base']['model'], revision=t.R['base']['revision'], local_files_only=True, cache_dir=options.cache, allow_patterns=BASE_FILES))
if cached.name != t.R['base']['revision']:
    raise RuntimeError('Cached base revision does not match pinned recipe')
evidence = {
    'purpose': 'Fresh evaluation and full fit after predicate, hunger and contextual-lookup corrections; unchanged pinned recipe and frozen historical references, no reused checkpoint or weakened gate.',
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'git': git, 'dictionary_sha256': dictionary_fingerprint(),
    'recipe_sha256': t.sha256(t.RECIPE_PATH), 'trainer_sha256': t.sha256(Path(t.__file__)),
    'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'toolchain': t.toolchain(), 'wordnet': t.wordnet_version(),
    'wordnet_zip_sha256': t.sha256(options.nltk_data / 'corpora/wordnet.zip'),
    'base': t.R['base'], 'cached_base_weights_sha256': t.sha256(cached / 'model.safetensors'),
    'cached_only_snapshot_resolution': True, 'base_file_allowlist': BASE_FILES,
    'base_snapshot_manifest': snapshot_manifest(cached),
    'integrity_helper_sha256': t.sha256(Path(__file__).with_name('base_integrity.py')),
    'pair_digest_serialization': 'SHA-256 of UTF-8 json.dumps(rows, ensure_ascii=False, separators=(comma, colon)); ordered pairs retained',
    'recipe': t.R, 'input_manifest': frozen_inputs, 'fits': [], 'reference_calls': [],
}

def save():
    evidence_path.write_text(json.dumps(evidence, indent=2) + '\n')

def cached_snapshot(*args, **kwargs):
    kwargs['local_files_only'] = True
    kwargs['cache_dir'] = options.cache
    kwargs['allow_patterns'] = BASE_FILES
    return original_snapshot(*args, **kwargs)

original_train = t.train
def fresh_train(path, holdout):
    d = t.load_dictionary()
    tr, held = t.split(d, holdout)
    row = {'holdout': holdout, 'entries': len(tr), 'held_entries': len(held), 'pairs': {}}
    for name, build in [('positive', t.pairs), ('wrong_sense', t.sense_negatives), ('opposite', t.opposite_negatives)]:
        pairs = build(d, tr)
        row['pairs'][name] = {'count': len(pairs), 'ordered_sha256': hashlib.sha256(
            json.dumps(pairs, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()}
    evidence['fits'].append(row)
    save()
    original_train(path, holdout)
    row['weights_sha256'] = t.sha256(path / 'aussie-minilm' / 'model.safetensors')
    row['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    save()

original_evaluate = t.evaluate
def evaluate(*args, **kwargs):
    result = original_evaluate(*args, **kwargs)
    evidence['evaluation'] = result
    save()
    return result

original_calibrate = t.calibrate
def calibrate(*args, **kwargs):
    result = original_calibrate(*args, **kwargs)
    evidence['calibration'] = result
    save()
    return result

original_reference = t.reference
def reference(*args, **kwargs):
    result = original_reference(*args, **kwargs)
    evidence['reference_calls'].append(result)
    save()
    return result

huggingface_hub.snapshot_download = cached_snapshot
t.train = fresh_train
t.evaluate = evaluate
t.calibrate = calibrate
t.reference = reference
save()
args = argparse.Namespace(version='1.4.0', dest=str(dest), force=False, allow_failures=False, out=work)
try:
    result = t.release(args)
    evidence['exit_code'] = result
    evidence['exported'] = (dest / 'meta.json').exists()
finally:
    evidence['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    evidence['final_git'] = t.git_state()
    evidence['external_inputs_unchanged'] = (snapshot_manifest(cached) == evidence['base_snapshot_manifest']
        and t.sha256(options.nltk_data / 'corpora/wordnet.zip') == evidence['wordnet_zip_sha256'])
    evidence['inputs_unchanged'] = input_manifest() == frozen_inputs and evidence['external_inputs_unchanged']
    if not evidence['inputs_unchanged']:
        evidence['invalidated_reason'] = 'Runtime, data or training inputs changed during fit; do not adopt this trial.'
    save()
if not evidence['inputs_unchanged']:
    raise SystemExit('Training inputs changed during the fit; candidate invalidated')
raise SystemExit(result)
