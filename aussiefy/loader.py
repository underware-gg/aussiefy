"""Load and validate the dictionary, concept vocabulary, level profiles and phonetic rules from YAML.

The I/O side of the dictionary: what it loads into lives in model.py."""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

import yaml

from .errors import UserError
from .terms import fold
from . import pos
from .dialect import parse_dialect
from .genre import GenreConfig
from .matcher import Pattern, PatternIndex, compile_pattern
from .model import Dictionary, LevelProfile, PhoneticRule, RewriteThresholds, SwearProfile, swear_strength
from .schema import (CLASSES, FRAMES, GARNISH_KEYS, RIFF_TONES, Concept, Entry, Riff, SchemaError, parse_concept,
                     parse_entry)

DATA_DIR = Path(__file__).parent / "data"


# libyaml's parser (bundled with PyYAML's wheels) loads the dictionary about ten times faster
_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _read_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_YAML_LOADER)


def _read(path: Path, errors: list[str], empty: list | dict) -> Any:
    """A data file's YAML, of the same type as `empty`; a missing file, invalid YAML or the wrong top level is
    collected as an error and reads as `empty`, so one load reports every problem."""
    try:
        data = _read_yaml(path)
    except FileNotFoundError:
        errors.append(f"{path}: missing")
        return empty
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: could not read: {exc}")
        return empty
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return empty
    if data is None:
        return empty
    if not isinstance(data, type(empty)):
        errors.append(f"{path}: top level must be a {'list' if isinstance(empty, list) else 'mapping'}")
        return empty
    return data


def _read_optional(path: Path, errors: list[str], empty: list | dict) -> Any:
    return _read(path, errors, empty) if path.exists() else empty


def _entry_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.glob("*.yaml")) + sorted(p.glob("*.yml")))
        elif p.exists():
            files.append(p)
        else:
            raise UserError(f"no such dictionary file or directory: {p}")
    return files


def entry_files(data_dir: str | Path = DATA_DIR) -> list[Path]:
    """The entry files a data directory's dictionary is built from (entries/*.yaml and *.yml)."""
    return _entry_files([Path(data_dir) / "entries"])


def _thresholds(level: int, raw: dict) -> RewriteThresholds:
    unknown = set(raw) - set(RewriteThresholds.__dataclass_fields__)
    if unknown:
        raise SchemaError(f"level {level}: unknown rewrite threshold(s) {sorted(unknown)}")
    return RewriteThresholds(**raw)


def _profile(level: int, raw: dict, base: dict) -> LevelProfile:
    merged = {**base, **raw}
    sub = merged.get("substitution", {})
    for key in sub:
        if key not in CLASSES:
            raise SchemaError(f"level {level}: unknown substitution class {key!r}")
    for name in ("garnish", "max_garnish"):
        unknown = set(merged.get(name) or {}) - set(GARNISH_KEYS)
        if unknown:
            raise SchemaError(f"level {level}: unknown {name} key(s) {sorted(unknown)} (use {', '.join(GARNISH_KEYS)})")
    frames = tuple(merged.get("frames", FRAMES))
    for f in frames:
        if f not in FRAMES:
            raise SchemaError(f"level {level}: unknown frame {f!r}")
    stretch = merged.get("stretch", [3, 5])
    return LevelProfile(
        level=level,
        substitution={k: float(sub.get(k, 0.0)) for k in CLASSES},
        frames=frames,
        vulgarity=int(merged.get("vulgarity", 0)),
        registers=tuple(merged.get("registers", ["current"])),
        garnish={k: float(v) for k, v in (merged.get("garnish") or {}).items()},
        max_garnish={k: int(v) for k, v in (merged.get("max_garnish") or {}).items()},
        garnish_gap=int(merged.get("garnish_gap", 1)),
        garnish_per_sentence=int(merged.get("garnish_per_sentence", 1)),
        rewrite=_thresholds(level, merged.get("rewrite") or {}),
        stack=float(merged.get("stack", 0.0)),
        phonetic=float(merged.get("phonetic", 0.0)),
        stretch=(int(stretch[0]), int(stretch[1])),
    )


def load_dictionary(extra: Iterable[str | Path] = (), data_dir: str | Path | None = None,
                    include_builtin: bool = True) -> Dictionary:
    data = Path(data_dir) if data_dir else DATA_DIR
    errors: list[str] = []
    warnings: list[str] = []

    concepts: dict[str, Concept] = {}
    for cid, raw in _read(data / "concepts.yaml", errors, {}).items():
        try:
            concepts[cid] = parse_concept(cid, raw or {})
        except SchemaError as exc:
            errors.append(str(exc))

    prof_raw = _read(data / "profiles.yaml", errors, {})
    base = prof_raw.get("base", {})
    profiles = {}
    for lvl, raw in (prof_raw.get("levels") or {}).items():
        try:
            profiles[int(lvl)] = _profile(int(lvl), raw or {}, base)
        except SchemaError as exc:
            errors.append(str(exc))
    if sorted(profiles) != [1, 2, 3, 4, 5]:
        errors.append(f"profiles.yaml must define levels 1-5, found {sorted(profiles)}")

    grammar = _read_optional(data / "grammar.yaml", errors, {})
    person_roles, adjective_nouns, name_aliases = frozenset(), {}, {}
    if not isinstance(grammar, dict) or set(grammar) - {"person_nouns", "adjective_nouns", "name_aliases"}:
        errors.append("grammar.yaml: expected person_nouns, adjective_nouns and name_aliases")
    else:
        def words(raw, where):
            if not isinstance(raw, list) or any(not isinstance(w, str) or not re.fullmatch(r"[a-z]+", w) for w in raw):
                errors.append(f"grammar.yaml: {where} must list lower-case words")
                return frozenset()
            return frozenset(raw)
        person_roles = words(grammar.get("person_nouns", []), "person_nouns")
        adjectives = grammar.get("adjective_nouns", {})
        if not isinstance(adjectives, dict) or any(not isinstance(w, str) or not re.fullmatch(r"[a-z]+", w) for w in adjectives):
            errors.append("grammar.yaml: adjective_nouns must map lower-case adjectives to noun lists")
        else:
            adjective_nouns = {w: words(ns, f"adjective_nouns.{w}") for w, ns in adjectives.items()}

    aliases = grammar.get("name_aliases", {}) if isinstance(grammar, dict) else {}
    if not isinstance(aliases, dict):
        errors.append("grammar.yaml: name_aliases must map exact phrases to accepted wording lists")
    else:
        for phrase, variants in aliases.items():
            if (not isinstance(phrase, str) or not phrase.strip() or not isinstance(variants, list)
                    or not variants or any(not isinstance(v, str) or not v.strip() for v in variants)):
                errors.append("grammar.yaml: name_aliases requires non-empty phrases and wording lists")
            else:
                name_aliases[fold(phrase)] = tuple(fold(v) for v in variants)

    phonetic: list[PhoneticRule] = []
    readings = {}

    for raw in _read(data / "phonetic.yaml", errors, []):
        try:
            if not isinstance(raw, dict):
                raise TypeError("expected a mapping")
            reading = raw.get("reads_as")
            if reading is not None and (
                    not isinstance(reading, str) or not re.fullmatch(r"[a-z]+(?:[ '][a-z]+)*", reading)
                    or raw.get("kind", "drawl") != "drawl" or not isinstance(raw.get("replace"), str)
                    or not re.fullmatch(r"[A-Za-z' ]+", raw["replace"]) or not raw["replace"].strip()):
                raise ValueError("reads_as requires canonical lower-case words and a literal drawl replacement")
            if reading is not None:
                key = fold(raw["replace"])
                if key in readings and readings[key] != reading:
                    raise ValueError(f"reads_as conflicts for replacement {key!r}")
                readings[key] = reading
            unless_before = raw.get("unless_before")
            if unless_before is not None and (not isinstance(unless_before, str) or not unless_before.strip()):
                raise ValueError("unless_before must be a non-empty regular expression")
            phonetic.append(PhoneticRule(raw["id"], re.compile(raw["match"]), raw["replace"],
                                         float(raw.get("prob", 1.0)), int(raw.get("min_level", 5)),
                                         raw.get("notes", ""), int(raw.get("vulgarity", 0)),
                                         raw.get("kind", "drawl"),
                                         float(raw["dialogue_prob"]) if "dialogue_prob" in raw else None, reading,
                                         re.compile(unless_before) if unless_before is not None else None))
        except (KeyError, TypeError, ValueError, re.error) as exc:
            errors.append(f"phonetic rule {raw!r}: {exc}")

    builtin = [data / "entries"] if include_builtin else []
    for missing in (d for d in builtin if not d.is_dir()):
        errors.append(f"{missing}: missing")
    sources = [d for d in builtin if d.is_dir()] + [Path(p) for p in extra]
    entries: dict[str, Entry] = {}
    for path in _entry_files(sources):
        for raw in _read(path, errors, []):
            try:
                entry = parse_entry(raw, origin=path.name)
            except SchemaError as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            if entry.id in entries:
                errors.append(f"{path.name}: duplicate id {entry.id!r} (first in {entries[entry.id].origin_file})")
                continue
            for c in entry.concept:
                if c not in concepts:
                    errors.append(f"{entry.id}: unknown concept {c!r} (add it to concepts.yaml)")
            if entry.status == "active" and {"not_aussie", "fabricated", "dubious_meaning"} & set(entry.flags):
                warnings.append(f"{entry.id}: flagged {list(entry.flags)} but status is active")
            entries[entry.id] = entry

    # riffs.yaml: the images a term calls up (wheelie bin -> bin chickens fightin' over the scraps), rated for
    # swearing word by word from swears.yaml so the vulgarity cap applies to them too
    swears = {str(k).lower(): int(v) for k, v in _read(data / "swears.yaml", errors, {}).items()}
    try:
        dialect = parse_dialect(_read_optional(data / "dialect.yaml", errors, {}))
    except SchemaError as exc:
        errors.append(str(exc))
        dialect = parse_dialect(None)
    try:
        genres = GenreConfig.from_mapping(_read(data / "genres.yaml", errors, {}), pos.lower_words())
    except SchemaError as exc:
        errors.append(str(exc))
        genres = None


    for entry_id, riffs in _read(data / "riffs.yaml", errors, {}).items():
        if entry_id not in entries:
            errors.append(f"riffs.yaml: unknown entry {entry_id!r}")
            continue
        rated = []
        for riff in riffs or ():
            text, tone = (riff, "plain") if isinstance(riff, str) else \
                ((riff.get("text"), riff.get("tone", "plain")) if isinstance(riff, dict) else (None, None))
            if not isinstance(text, str) or not text.strip() or tone not in RIFF_TONES:
                errors.append(f"riffs.yaml: {entry_id}: each riff needs text and a tone in {RIFF_TONES}")
                continue
            words = re.findall(r"[a-z']+", text.lower())
            rated.append(Riff(text.strip(), max((swear_strength(swears, w) for w in words), default=0), tone))
        entries[entry_id] = replace(entries[entry_id], riffs=tuple(rated))

    # sources.yaml: extra source URLs per entry id, maintained by the scrape review tool
    # so hand-curated files are never rewritten.
    for entry_id, urls in _read_optional(data / "sources.yaml", errors, {}).items():
        if entry_id not in entries:
            warnings.append(f"sources.yaml: unknown entry {entry_id!r}")
            continue
        merged = tuple(dict.fromkeys(entries[entry_id].sources + tuple(urls or ())))
        entries[entry_id] = replace(entries[entry_id], sources=merged)

    patterns: list[Pattern] = []
    for c in concepts.values():
        for frame, texts in c.triggers.items():
            for t in texts:
                try:
                    patterns.append(compile_pattern(t, frame, (c.id,), 3))
                except ValueError as exc:
                    errors.append(f"concept {c.id}: {exc}")
    for e in entries.values():
        if e.type != "idiom" or e.status == "omit":
            continue
        for t in e.replaces:
            try:
                patterns.append(compile_pattern(t, e.frame, e.concept, e.intensity, entry_id=e.id))
            except ValueError as exc:
                errors.append(f"{e.id}: {exc}")

    forms: list[Pattern] = []
    for e in entries.values():
        if e.type != "idiom" or e.status == "omit":
            continue
        for f in e.all_forms:
            try:
                forms.append(compile_pattern(f.replace("{np}", "{obj}"), e.frame, e.concept, e.intensity, entry_id=e.id))
            except ValueError as exc:
                errors.append(f"{e.id}: form {f!r}: {exc}")

    detectable = {c for p in patterns for c in p.concepts}
    for c in concepts:
        if c not in detectable and any(c in e.concept for e in entries.values() if e.type == "idiom"):
            warnings.append(f"concept {c} has entries but no triggers or replaces; it can never be detected")

    swearing = {}
    for v, raw in (prof_raw.get("swearing") or {}).items():
        unknown = set(raw or {}) - set(SwearProfile.__dataclass_fields__)
        if unknown or int(v) not in range(4):
            errors.append(f"profiles.yaml: swearing {v}: {sorted(unknown) or 'vulgarity must be 0-3'}")
            continue
        swearing[int(v)] = SwearProfile(**{k: float(x) for k, x in (raw or {}).items()})
    if errors:
        raise SchemaError("dictionary failed validation:\n  " + "\n  ".join(errors))
    return Dictionary(entries, concepts, profiles, phonetic, prof_raw.get("policy", {}), patterns,
                      PatternIndex(patterns), PatternIndex(forms), swears, dialect, warnings, swearing, genres, pos.lower_words(), person_roles, adjective_nouns, name_aliases)


def write_validated(data_dir: str | Path, files: dict[str, str], extra: Iterable[str | Path] = ()) -> Dictionary:
    """Write files (text by path relative to data_dir) only if the dictionary they make loads: they are written
    into a scratch copy of data_dir first, and a SchemaError leaves data_dir untouched. Returns the new dictionary."""
    data = Path(data_dir)
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "data"
        shutil.copytree(data, scratch)
        for rel, text in files.items():
            (scratch / rel).write_text(text, encoding="utf-8")
        load_dictionary(extra, data_dir=scratch)
    for rel, text in files.items():
        (data / rel).write_text(text, encoding="utf-8")
    return load_dictionary(extra, data_dir=data)


def load_genres(data_dir: Path = DATA_DIR) -> GenreConfig:
    errors: list[str] = []
    raw = _read(Path(data_dir) / "genres.yaml", errors, {})
    if errors:
        raise SchemaError("\n  ".join(errors))
    return GenreConfig.from_mapping(raw, pos.lower_words())
