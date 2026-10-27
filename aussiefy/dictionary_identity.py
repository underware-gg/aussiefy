"""Content identity for reproducible dictionary loads; filenames outside the core are not identities."""

import hashlib
from pathlib import Path

from .errors import SchemaError


def dictionary_identity(data: Path, extra_files: list[Path], *, include_builtin: bool) -> str:
    digest = hashlib.sha256(b"aussiefy-dictionary/v1\0" + bytes([include_builtin]))
    inputs = [(p.relative_to(data).as_posix(), p) for p in sorted(data.rglob("*")) if p.is_file()
              and p.suffix in {".yaml", ".yml", ".json", ".txt", ".f16", ".gz"}
              and (include_builtin or not (p.parent.name == "entries" or p.name == "constructions.yaml"))]
    inputs += [(f"extension/{i}", p) for i, p in enumerate(extra_files)]
    for name, path in inputs:
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise SchemaError(f"cannot fingerprint dictionary input {path}: {exc}") from exc
        key = name.encode("utf-8")
        digest.update(len(key).to_bytes(4, "big") + key + hashlib.sha256(content).digest())
    return "sha256:" + digest.hexdigest()
