"""Record and validate the content-addressed files of the pinned Hugging Face snapshot."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path


def snapshot_manifest(snapshot: Path) -> dict:
    files = {}
    for path in sorted(snapshot.rglob('*')):
        if not path.is_file():
            continue
        data = path.read_bytes()
        address = path.readlink().name if path.is_symlink() else path.name
        sha256 = hashlib.sha256(data).hexdigest()
        if len(address) == 64:
            actual = sha256
        elif len(address) == 40:
            actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        else:
            raise ValueError(f'{path.name}: expected a content-addressed snapshot symlink')
        if actual != address:
            raise ValueError(f'{path.name}: bytes differ from the pinned snapshot blob address')
        files[path.relative_to(snapshot).as_posix()] = {'sha256': sha256, 'blob_address': address,
                                                       'bytes': len(data)}
    if not files:
        raise ValueError('Snapshot contains no files')
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--against', type=Path)
    args = parser.parse_args()
    files = snapshot_manifest(args.snapshot)
    same = files == json.loads(args.against.read_text())['files'] if args.against else None
    result = {'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
              'revision': args.snapshot.name, 'files': files, 'matches_previous': same}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(files)} pinned blob addresses validated; matches previous: {same}')
    if same is False:
        raise SystemExit('Snapshot inputs changed; do not adopt the model')


if __name__ == '__main__':
    main()
