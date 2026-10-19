"""Isolated dry release with cached-only base resolution and retained failure evidence."""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, '/Users/robmorris/Development/Underware/aussiefy')
import huggingface_hub
from aussiefy.static import dictionary_fingerprint
from scripts import train_embedder as t

t.R = t.load_recipe()
work = Path('/private/tmp/aussiefy-semantic-model-20261019/work')
dest = Path('/private/tmp/aussiefy-semantic-model-20261019/candidate')
evidence_path = Path('/private/tmp/aussiefy-semantic-model-20261019/evidence.json')
if work.exists() or dest.exists() or evidence_path.exists():
    raise RuntimeError('Fresh work, destination and evidence paths must not exist')
git = t.git_state()
# The required model gate blocks committing the corrected dictionary.
# Record exact dirty inputs, train afresh, and require unchanged inputs at completion.
input_roots = [Path(t.ROOT) / name for name in ('aussiefy', 'training', 'scripts')]
def input_manifest():
    return {str(p.relative_to(t.ROOT)): t.sha256(p) for root in input_roots
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
frozen_inputs = input_manifest()
original_snapshot = huggingface_hub.snapshot_download
cached = Path(original_snapshot(t.R['base']['model'], revision=t.R['base']['revision'], local_files_only=True))
if cached.name != t.R['base']['revision']:
    raise RuntimeError('Cached base revision does not match pinned recipe')
evidence = {
    'purpose': 'Fresh evaluation and full fit against reviewed semantic dictionary corrections and migrated reference labels; unchanged pinned recipe, no reused checkpoint or weakened gate.',
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'git': git, 'dictionary_sha256': dictionary_fingerprint(),
    'recipe_sha256': t.sha256(t.RECIPE_PATH), 'trainer_sha256': t.sha256(Path(t.__file__)),
    'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'toolchain': t.toolchain(), 'wordnet': t.wordnet_version(),
    'base': t.R['base'], 'cached_base_weights_sha256': t.sha256(cached / 'model.safetensors'),
    'cached_only_snapshot_resolution': True,
    'pair_digest_serialization': 'SHA-256 of UTF-8 json.dumps(rows, ensure_ascii=False, separators=(comma, colon)); ordered pairs retained',
    'recipe': t.R, 'input_manifest': frozen_inputs, 'fits': [], 'reference_calls': [],
}

def save():
    evidence_path.write_text(json.dumps(evidence, indent=2) + '\n')

def cached_snapshot(*args, **kwargs):
    kwargs['local_files_only'] = True
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
args = argparse.Namespace(version='1.3.0', dest=str(dest), force=False, allow_failures=False, out=work)
try:
    result = t.release(args)
    evidence['exit_code'] = result
    evidence['exported'] = (dest / 'meta.json').exists()
finally:
    evidence['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    evidence['final_git'] = t.git_state()
    evidence['inputs_unchanged'] = input_manifest() == frozen_inputs
    if not evidence['inputs_unchanged']:
        evidence['invalidated_reason'] = 'Runtime, data or training inputs changed during fit; do not adopt this trial.'
    save()
raise SystemExit(result)
