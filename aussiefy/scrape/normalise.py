"""Normalise scraped phrases, merge variants across sources and check them against the dictionary."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..dump import dump_yaml
from ..errors import UserError
from ..model import Dictionary
from ..schema import PLACEHOLDER_RE
from ..terms import fold
from .parse import RawPhrase

_ELISIONS = [
    (r"in'(?=\W|$)", "ing"), (r"\bya\b", "you"), (r"\byer\b", "your"), (r"'n\b", " and"), (r"\bn'\b", "and"),
    (r"\bo'\b", "of"), (r"\bfella\b", "fellow"),
]


def merge_key(phrase: str) -> str:
    """The key that recognises one scraped idiom across sources and spellings: deliberately looser than
    terms.form_key, which decides "same term?" for the dictionary. Scraped phrases arrive with a subject, a copula
    and a possessive ("he's got kangaroos loose in the top paddock"), so this drops copulas and subject
    pronouns and spells elisions out. Omitted entries are stored by the hash of this key (flagged.yaml
    key_sha256), so changing it means re-hashing them."""
    s = fold(phrase).replace("“", "").replace("”", "")
    s = PLACEHOLDER_RE.sub(" ", s)
    s = re.sub(r"\(.*?\)", " ", s)              # drop parenthetical asides
    for pat, rep in _ELISIONS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"^(to|a|an|the|you|you're|he's|she's|it's|i'm|they're)\s+", "", s.strip())
    s = re.sub(r"\b(your|his|her|their|my|our|its|me|one's)\b", "POSS", s)
    s = re.sub(r"\b(is|are|am|was|were|be|has|have|had|got|a|an|the)\b", "", s)
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" '")


def key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def slug(phrase: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", phrase.lower().replace("'", "")).strip("-")
    return "-".join(s.split("-")[:6]) or "phrase"


def unique_id(phrase: str, taken: set[str]) -> str:
    """A new id for a phrase: its slug, numbered past every id already taken. The id joins `taken`."""
    base = slug(phrase)
    sid, n = base, 2
    while sid in taken:
        sid, n = f"{base}-{n}", n + 1
    taken.add(sid)
    return sid


@dataclass
class Staged:
    id: str
    form: str
    variants: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    source_meanings: list[str] = field(default_factory=list)   # tagger context only, never published
    usage: list[str] = field(default_factory=list)
    known_as: str | None = None        # existing entry id with the same key
    known_status: str | None = None

    def to_dict(self) -> dict:
        d = {"id": self.id, "form": self.form, "variants": self.variants, "sources": self.sources,
             "source_meanings": self.source_meanings, "usage": self.usage}
        if self.known_as:
            d["known_as"] = self.known_as
            d["known_status"] = self.known_status
        return d


def dictionary_keys(dictionary: Dictionary) -> tuple[dict[str, str], dict[str, str]]:
    """(key -> entry id, key_sha256 -> entry id) over every entry, omitted ones included."""
    keys: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for e in dictionary.entries.values():
        for form in e.all_forms:
            k = merge_key(form)
            keys.setdefault(k, e.id)
            hashes.setdefault(key_hash(k), e.id)
        if e.key_sha256:
            hashes[e.key_sha256] = e.id
    return keys, hashes


def merge(raw: list[RawPhrase], dictionary: Dictionary | None = None,
          existing: list[Staged] | None = None) -> list[Staged]:
    staged: dict[str, Staged] = {merge_key(s.form): s for s in existing or []}
    keys, hashes = dictionary_keys(dictionary) if dictionary else ({}, {})
    used_ids = set(dictionary.entries) if dictionary else set()
    used_ids |= {s.id for s in staged.values()}
    for r in raw:
        form = re.sub(r"\s+", " ", r.phrase).strip().rstrip(".!")
        if not form or len(form) > 100:
            continue
        key = merge_key(form)
        if not key:
            continue
        item = staged.get(key)
        if item is None:
            item = Staged(unique_id(form, used_ids), form)
            known = keys.get(key) or hashes.get(key_hash(key))
            if known and dictionary:
                item.known_as = known
                item.known_status = dictionary.entries[known].status
            staged[key] = item
        elif form.lower() != item.form.lower() and form.lower() not in (v.lower() for v in item.variants):
            item.variants.append(form)
        if r.url not in item.sources:
            item.sources.append(r.url)
        if r.meaning and r.meaning not in item.source_meanings:
            item.source_meanings.append(r.meaning)
        if r.usage and r.usage not in item.usage:
            item.usage.append(r.usage)
    return list(staged.values())


def load_staged(path: str | Path) -> list[Staged]:
    """A staging file's phrases (what scrape, fragments and harvest write and tag reads)."""
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise UserError(f"no such staging file: {path}") from None
    except yaml.YAMLError as exc:
        raise UserError(f"{path}: invalid YAML: {exc}") from exc
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise UserError(f"{path}: not a staging file (a list of phrases, each with an id and a form)")
    for i, r in enumerate(raw, 1):
        if not (isinstance(r, dict) and "id" in r and "form" in r):
            raise UserError(f"{path}: phrase {i} needs an id and a form, got {r!r}")
        for key in ("id", "form"):
            if not isinstance(r[key], str) or not r[key].strip():
                raise UserError(f"{path}: phrase {i}: {key} must be non-empty text")
        for key in ("variants", "sources", "source_meanings", "usage"):
            if key in r and (not isinstance(r[key], list) or any(not isinstance(v, str) for v in r[key])):
                raise UserError(f"{path}: phrase {i}: {key} must be a list of text")
    return [Staged(**{k: v for k, v in r.items() if k in Staged.__dataclass_fields__}) for r in raw]


def save_staged(path: str | Path, items: list[Staged]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml([s.to_dict() for s in items]), encoding="utf-8")
