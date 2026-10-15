"""The bundled Aussie embedding model: static word vectors, read with the standard library alone.

A Model2Vec-style static model (scripts/train_embedder.py: MiniLM fine-tuned on the dictionary, distilled, then
tuned). A text's vector is the mean of its tokens' vectors, so there is no network to run: no torch, no numpy,
and the same text always gets the same vector. It ships in aussiefy/data/model:

    vectors.f16   one little-endian float16 row per token
    vocab.txt     the WordPiece vocabulary, one token per line, in row order
    meta.json     dimensions, added tokens, the cut-offs it was calibrated to, and the dictionary it was trained on

The tokenizer reproduces the `tokenizers` BERT pipeline the model was trained with (normaliser, added tokens,
pre-tokeniser, WordPiece); tests/architecture/test_static.py checks it against the real one when that's installed.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import string
import struct
import unicodedata
from functools import lru_cache
from pathlib import Path

from .errors import UserError
from .loader import DATA_DIR, entry_files

MODEL_DIR = DATA_DIR / "model"


def available() -> bool:
    return (MODEL_DIR / "meta.json").is_file()


def dictionary_fingerprint(data_dir: Path = DATA_DIR) -> str:
    """sha256 of the dictionary files the model learns from, to tell when it's out of date."""
    h = hashlib.sha256()
    for p in [data_dir / "concepts.yaml", data_dir / "riffs.yaml", *entry_files(data_dir)]:
        if p.is_file():
            h.update(p.name.encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def _is_punct(ch: str) -> bool:
    return ch in string.punctuation or unicodedata.category(ch).startswith("P")


def _is_cjk(cp: int) -> bool:
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF or 0x2A700 <= cp <= 0x2B73F
            or 0x2B740 <= cp <= 0x2B81F or 0x2B820 <= cp <= 0x2CEAF or 0xF900 <= cp <= 0xFAFF
            or 0x2F800 <= cp <= 0x2FA1F)


def normalize(text: str) -> str:
    """BertNormalizer: drop control characters, space out CJK, strip accents, lowercase."""
    out = []
    for ch in text:
        cp = ord(ch)
        if cp in (0, 0xFFFD) or (unicodedata.category(ch).startswith("C") and ch not in "\t\n\r"):
            continue
        if ch.isspace():
            out.append(" ")
        elif _is_cjk(cp):
            out.append(f" {ch} ")
        else:
            out.append(ch)
    text = unicodedata.normalize("NFD", "".join(out))
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()


class StaticEmbedder:
    """Embedder protocol (name, similarity) over the bundled static vectors."""

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.meta = json.loads((model_dir / "meta.json").read_text(encoding="utf-8"))
        self.version = self.meta.get("version")
        self.name = "bundled:" + self.meta["name"] + (f"-{self.version}" if self.version else "")
        self.dims = self.meta["dims"]
        self.lookup_threshold = self.meta["lookup_threshold"]
        self.gaps_confident = self.meta["gaps_confident"]
        tokens = (model_dir / "vocab.txt").read_text(encoding="utf-8").split("\n")
        self.vocab = {t: i for i, t in enumerate(tokens) if t}
        self.unk = self.vocab[self.meta["unk_token"]]
        added = sorted(self.meta["added_tokens"], key=len, reverse=True)
        self._added = re.compile("|".join(re.escape(t) for t in added)) if added else None
        self._rows = (model_dir / "vectors.f16").read_bytes()
        self._fmt = struct.Struct(f"<{self.dims}e")
        if len(self._rows) != len(tokens) * self._fmt.size:
            raise UserError(f"{model_dir}: vectors.f16 doesn't match vocab.txt; reinstall aussiefy")
        # bounded, and owned by the instance: the dictionary's own texts (about 1,600 glosses and descriptions)
        # stay warm, while a long-lived MCP server's endless distinct queries can't grow the cache without limit
        # (a cached vector is about 8 KB as Python floats)
        self._row = lru_cache(maxsize=4096)(self._unpack_row)
        self.encode = lru_cache(maxsize=4096)(self._encode)

    # --- tokenizer ---

    def _wordpiece(self, word: str) -> list[int]:
        if len(word) > 100:
            return [self.unk]
        ids, start = [], 0
        while start < len(word):
            end = len(word)
            while end > start:
                piece = word[start:end] if start == 0 else "##" + word[start:end]
                if piece in self.vocab:
                    ids.append(self.vocab[piece])
                    break
                end -= 1
            else:
                return [self.unk]
            start = end
        return ids

    def _pretokenize(self, text: str) -> list[str]:
        words, cur = [], []
        for ch in text:
            if ch.isspace() or _is_punct(ch):
                if cur:
                    words.append("".join(cur))
                    cur = []
                if not ch.isspace():
                    words.append(ch)
            else:
                cur.append(ch)
        if cur:
            words.append("".join(cur))
        return words

    def tokenize(self, text: str) -> list[int]:
        """Token ids as `tokenizers` gives them (no special tokens), unknown pieces dropped as Model2Vec does."""
        text = normalize(text)
        ids, pos = [], 0
        for m in (self._added.finditer(text) if self._added else ()):
            ids += [i for w in self._pretokenize(text[pos:m.start()]) for i in self._wordpiece(w)]
            ids.append(self.vocab[m.group()])
            pos = m.end()
        ids += [i for w in self._pretokenize(text[pos:]) for i in self._wordpiece(w)]
        return [i for i in ids if i != self.unk]

    # --- vectors ---

    def _unpack_row(self, i: int) -> tuple[float, ...]:
        return self._fmt.unpack_from(self._rows, i * self._fmt.size)

    def _encode(self, text: str) -> tuple[float, ...]:
        """Mean of the token vectors, scaled to unit length (all zeros when no token is known)."""
        ids = self.tokenize(text)
        if not ids:
            return (0.0,) * self.dims
        sums = [0.0] * self.dims
        for i in ids:
            for k, v in enumerate(self._row(i)):
                sums[k] += v
        norm = math.sqrt(sum(v * v for v in sums)) or 1.0
        return tuple(v / norm for v in sums)

    def similarity(self, a: str, b: str) -> float:
        return sum(x * y for x, y in zip(self.encode(a), self.encode(b)))

    def stale(self) -> bool:
        """True when the dictionary has changed since the model was trained (retrain with the script)."""
        return self.meta.get("dictionary_sha256") != dictionary_fingerprint()


_cached: StaticEmbedder | None = None


def bundled() -> StaticEmbedder | None:
    """The bundled model, loaded once; None if this install doesn't carry it."""
    global _cached
    if _cached is None and available():
        _cached = StaticEmbedder()
    return _cached
