"""Rebuild aussiefy/data/pos/tagger.json.gz from NLTK's averaged-perceptron tagger (MIT).

    python scripts/build_pos.py path/to/averaged_perceptron_tagger_eng.zip

The zip is nltk_data's (see aussiefy/data/pos/README.md for the URL and checksum). Weights are rounded to three
decimals, which changes no tag on the corpus, and the three JSON files are packed into one gzipped JSON.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path

SHA256 = "6025f530624335c67d6547d44757b357b4e79bae030a0383e9887a92c1718f0b"
OUT = Path(__file__).resolve().parent.parent / "aussiefy" / "data" / "pos" / "tagger.json.gz"


def main(zip_path: str) -> None:
    raw = Path(zip_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        sys.exit(f"{zip_path}: unexpected checksum (want {SHA256})")
    with zipfile.ZipFile(zip_path) as z:
        part = {name.rsplit(".", 2)[-2]: json.loads(z.read(name)) for name in z.namelist() if name.endswith(".json")}
    weights = {f: {label: round(w, 3) for label, w in labels.items() if round(w, 3)}
               for f, labels in part["weights"].items()}
    blob = {"classes": part["classes"], "tagdict": part["tagdict"], "weights": {f: ls for f, ls in weights.items() if ls}}
    OUT.write_bytes(gzip.compress(json.dumps(blob, separators=(",", ":")).encode(), 9, mtime=0))
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1])
