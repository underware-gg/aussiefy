"""Model trials verify complete pinned cache inputs, including a blob's extra storage symlink."""
import hashlib
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def cache(tmp_path):
    snapshot = tmp_path / 'snapshot'
    blobs = tmp_path / 'blobs'
    storage = tmp_path / 'storage'
    for folder in (snapshot, blobs, storage):
        folder.mkdir()
    data = {'config.json': b'{"tokenizer":"original"}', 'model.safetensors': b'abc'}
    for name, value in data.items():
        address = (hashlib.sha256(value).hexdigest() if name.endswith('.safetensors') else
                   hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest())
        target = storage / name
        target.write_bytes(value)
        (blobs / address).symlink_to(target)
        (snapshot / name).symlink_to(blobs / address)
    return snapshot


@pytest.fixture
def manifest():
    return runpy.run_path(str(ROOT / 'research/semantic-followup-2026-10-20/base_integrity.py'))['snapshot_manifest']


def test_a_complete_cache_manifest_validates_the_snapshot_address_before_the_storage_symlink(cache, manifest):
    found = manifest(cache)
    assert set(found) == {'config.json', 'model.safetensors'}
    assert found['model.safetensors']['sha256'] == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'


@pytest.mark.parametrize('name', ['config.json', 'model.safetensors'])
def test_changed_configuration_or_weights_cannot_keep_a_valid_pinned_manifest(cache, manifest, name):
    manifest(cache)
    (cache / name).write_bytes(b'changed')
    with pytest.raises(ValueError, match='bytes differ'):
        manifest(cache)
