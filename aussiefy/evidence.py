"""Stored evidence and a pure, shared assessment of a term's attestation."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from typing import Any
from urllib.parse import urlsplit

from .errors import SchemaError, UserError
from .source_urls import validate_source_url
from .themes import ThemePermissions, blocked_themes, parse_tags

SOURCE_KINDS = ("scholarly_dictionary", "slang_dictionary", "crowd_dictionary", "literature", "media",
                "testimony", "community")
DOCUMENTARY_KINDS = SOURCE_KINDS[:-2]
SUPPORTS = ("term", "meaning", "australian_use", "date")
VARIETIES = ("australian", "british", "irish", "american", "aboriginal", "other", "unknown")
REGISTERS = ("current", "dated", "archaic")
READINGS = ("australian", "general", "british", "irish", "american", "other")


@dataclass(frozen=True)
class Source:
    kind: str
    publisher: str
    supports: tuple[str, ...]
    url: str | None = None
    cited_date: str | None = None
    note: str = ""
    basis: str | None = None       # community attribution retains the underlying kind of evidence

    @property
    def evidence_kind(self) -> str:
        return self.basis if self.kind == "community" else self.kind

    def to_dict(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items() if v is not None and v != ""}


def unreviewed_source(url: str, *, owner: str, note: str) -> Source:
    """Turn an acquisition URL into a citation without claiming expression-level support."""
    if not isinstance(url, str):
        raise SchemaError(f"{owner}: source URL must be text")
    try:
        publisher = urlsplit(url).netloc.lower().removeprefix("www.")
    except ValueError as exc:
        raise SchemaError(f"{owner}: malformed source URL") from exc
    raw = Source("media", publisher, (), url=url, note=note).to_dict()
    return parse_sources([raw], owner)[0]


@dataclass(frozen=True)
class Testimony:
    people: int
    independent: int
    places: int
    first_date: str | None
    last_date: str | None
    summary_date: str


@dataclass(frozen=True)
class Search:
    date: str
    outcome: str
    note: str = ""


@dataclass(frozen=True)
class CuratorRecord:
    date: str
    note: str


@dataclass(frozen=True)
class Attestation:
    score: float = 0.0
    bars: int = 0
    counts: tuple[tuple[str, int], ...] = ()
    people: int = 0
    independent: int = 0
    places: int = 0
    weights_version: str = ""

    def to_dict(self) -> dict:
        return {**asdict(self), "counts": dict(self.counts)}


@dataclass(frozen=True)
class Assessment:
    attestation: Attestation
    evidence: str
    first_attested: str | None


@dataclass(frozen=True, kw_only=True)
class TermMetadata:
    sources: tuple[Source, ...] = ()
    searched: Search | None = None
    coined_by: str | None = None
    produced_by: str | None = None
    caught_on: CuratorRecord | None = None
    spoken_use: CuratorRecord | None = None
    testimony: Testimony | None = None
    credit: str | None = None
    origin: str = "unknown"
    register: str = "current"
    origin_language: str | None = None
    australian_use: str = "common"
    reads_as: str = "australian"
    dated_by_curator: str | None = None
    themes: tuple[str, ...] = ()
    theme_tiers: tuple[tuple[str, int], ...] = ()   # parsed from explicit tiers within themes; never a separate YAML field
    doubtful_definition: bool = False
    misreadable: bool = False
    attestation: Attestation = field(default_factory=Attestation)
    evidence: str = "unverified"
    first_attested: str | None = None


DERIVED_FIELDS = {"attestation", "evidence", "first_attested"}
INTERNAL_FIELDS = {"theme_tiers"}
METADATA_KEYS = tuple(f.name for f in fields(TermMetadata) if f.name not in DERIVED_FIELDS | INTERNAL_FIELDS)


@dataclass(frozen=True)
class EvidenceWeights:
    version: str
    provisional: bool
    source_weights: tuple[tuple[str, float], ...]
    diminishing: float
    bar_width: float
    attested_bars: int
    testimony_scale: float
    testimony_saturation: float
    place_bonus: float
    general_pick_factor: float
    attestation_pick_bonus: float


def _object(raw, allowed, owner):
    if not isinstance(raw, dict) or any(not isinstance(k, str) for k in raw) or set(raw) - set(allowed):
        raise SchemaError(f"{owner}: expected an object with fields {', '.join(allowed)}")
    return raw


def _text(value, owner):
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{owner}: expected non-empty text")
    return value


def _date(value, owner):
    value = value.isoformat() if isinstance(value, date) else value
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("non-canonical date")
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{owner}: expected an ISO date") from exc
    return value


def _period(value, owner):
    if isinstance(value, date):
        value = value.isoformat()
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}(?:-\d{2}-\d{2}|s|[–-]\d{4})?", value):
        raise SchemaError(f"{owner}: expected a year, decade, year range or ISO date")
    if len(value) == 10:
        _date(value, owner)
    if re.fullmatch(r"\d{4}[–-]\d{4}", value) and value[:4] > value[-4:]:
        raise SchemaError(f"{owner}: year range is reversed")
    return value


def parse_sources(raw, owner: str) -> tuple[Source, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise SchemaError(f"{owner}: sources must be a list of structured records")
    out = []
    for record in raw:
        r = dict(_object(record, tuple(f.name for f in fields(Source)), f"{owner}.sources"))
        if r.get("kind") not in SOURCE_KINDS:
            raise SchemaError(f"{owner}: source kind must be one of {SOURCE_KINDS}")
        _text(r.get("publisher"), f"{owner}.source.publisher")
        support = r.get("supports")
        if not isinstance(support, list) or any(not isinstance(v, str) or v not in SUPPORTS for v in support):
            raise SchemaError(f"{owner}: source supports must list {SUPPORTS}")
        r["supports"] = tuple(dict.fromkeys(support))
        if r["kind"] == "community":
            if r.get("basis") not in SOURCE_KINDS[:-1]:
                raise SchemaError(f"{owner}: a community source needs an underlying basis kind")
        elif r.get("basis") is not None:
            raise SchemaError(f"{owner}: basis is only valid for community sources")
        if r.get("basis", r["kind"]) != "testimony" or r.get("url") is not None:
            try:
                validate_source_url(r.get("url"))
            except UserError as exc:
                raise SchemaError(f"{owner}: {exc}") from exc
        if r.get("cited_date") is not None:
            r["cited_date"] = _period(r["cited_date"], f"{owner}.source.cited_date")
        if "date" in r["supports"] and not r.get("cited_date"):
            raise SchemaError(f"{owner}: date support requires cited_date")
        if not isinstance(r.get("note", ""), str):
            raise SchemaError(f"{owner}: source note must be text")
        out.append(Source(**r))
    return tuple(dict.fromkeys(out))


def parse_metadata(raw: dict, owner: str) -> dict:
    out = {k: raw[k] for k in METADATA_KEYS if k in raw}
    out["sources"] = parse_sources(raw.get("sources"), owner)
    for key, choices in (("coined_by", ("person", "agent", "constructor")), ("produced_by", ("agent",)),
                         ("origin", VARIETIES), ("reads_as", READINGS),
                         ("register", REGISTERS),
                         ("australian_use", ("common", "uncommon"))):
        if key in out and out[key] not in choices:
            raise SchemaError(f"{owner}: {key} must be one of {choices}")
    for key in ("doubtful_definition", "misreadable"):
        if key in out and type(out[key]) is not bool:
            raise SchemaError(f"{owner}: {key} must be true or false")
    for key in ("credit", "origin_language"):
        if key in out:
            _text(out[key], f"{owner}.{key}")
    if "dated_by_curator" in out:
        out["dated_by_curator"] = _period(out["dated_by_curator"], f"{owner}.dated_by_curator")
    if "themes" in out:
        out["themes"], out["theme_tiers"] = parse_tags(out["themes"], owner)
    if "searched" in out:
        r = dict(_object(out["searched"], ("date", "outcome", "note"), f"{owner}.searched"))
        r["date"] = _date(r.get("date"), f"{owner}.searched.date")
        if (not isinstance(r.get("outcome"), str) or r["outcome"] not in {"found", "nothing_found", "inconclusive"}
                or not isinstance(r.get("note", ""), str)):
            raise SchemaError(f"{owner}: searched needs a valid outcome and text note")
        out["searched"] = Search(**r)
    if "testimony" in out:
        r = dict(_object(out["testimony"], tuple(f.name for f in fields(Testimony)), f"{owner}.testimony"))
        for key in ("people", "independent", "places"):
            if type(r.get(key)) is not int or r[key] < 0:
                raise SchemaError(f"{owner}: testimony {key} must be a non-negative integer")
        if r["independent"] > r["people"] or r["places"] > r["people"]:
            raise SchemaError(f"{owner}: independent people and places cannot exceed people")
        r["summary_date"] = _date(r.get("summary_date"), f"{owner}.testimony.summary_date")
        for key in ("first_date", "last_date"):
            r[key] = _date(r.get(key), f"{owner}.testimony.{key}") if r["people"] or r.get(key) is not None else None
        if (r["first_date"] is None) != (r["last_date"] is None) or (r["first_date"] is not None and
                not r["first_date"] <= r["last_date"] <= r["summary_date"]):
            raise SchemaError(f"{owner}: testimony dates must be ordered")
        out["testimony"] = Testimony(**r)
    for key in ("caught_on", "spoken_use"):
        if key in out:
            r = _object(out[key], ("date", "note"), f"{owner}.{key}")
            out[key] = CuratorRecord(_date(r.get("date"), f"{owner}.{key}.date"), _text(r.get("note"), f"{owner}.{key}.note"))
    if out.get("coined_by") == "constructor" and out["sources"]:
        raise SchemaError(f"{owner}: constructor output cannot carry sources")
    testimony = out.get("testimony")
    if any(s.evidence_kind == "testimony" for s in out["sources"]) and not testimony:
        raise SchemaError(f"{owner}: testimony sources require a testimony summary")
    if out.get("spoken_use") and (not testimony or not testimony.people):
        raise SchemaError(f"{owner}: spoken_use requires a testimony summary")
    documentary = any(s.evidence_kind != "testimony" and set(s.supports) & {"term", "meaning"} for s in out["sources"])
    if out.get("caught_on") and not (documentary or testimony and testimony.independent):
        raise SchemaError(f"{owner}: caught_on needs a non-testimony source or independent testimony")
    return out


def parse_weights(raw) -> EvidenceWeights:
    names = tuple(f.name for f in fields(EvidenceWeights))
    r = dict(_object(raw, names, "attestation weights"))
    if set(r) != set(names):
        raise SchemaError("attestation weights: all settings are required")
    _text(r["version"], "weights.version")
    if type(r["provisional"]) is not bool or type(r["attested_bars"]) is not int or not 2 <= r["attested_bars"] <= 5:
        raise SchemaError("weights: provisional must be boolean; attested_bars must be 2–5")
    sw = _object(r["source_weights"], DOCUMENTARY_KINDS, "weights.source_weights")
    if set(sw) != set(DOCUMENTARY_KINDS):
        raise SchemaError("weights: every documentary source kind needs a weight")
    numbers = {**sw, **{k: r[k] for k in names if k not in {"version", "provisional", "source_weights", "attested_bars"}}}
    if any(type(v) not in (float, int) or not math.isfinite(v) or v < 0 for v in numbers.values()):
        raise SchemaError("weights: all numeric settings must be finite and non-negative")
    if not (0 < r["diminishing"] < 1 and 0 < r["general_pick_factor"] < 1 and r["bar_width"] > 0
            and r["testimony_saturation"] > 0):
        raise SchemaError("weights: diminishing/general factors must be between zero and one; scales must be positive")
    r["source_weights"] = tuple(sw.items())
    return EvidenceWeights(**r)


def assess(term: TermMetadata, weights: EvidenceWeights, *, testimony: Testimony | None = None) -> Assessment:
    """Live testimony replaces the exported summary. No storage, clock or random state is consulted."""
    summary = testimony if testimony is not None else term.testimony
    # One publisher/work has one vote, even across kinds or copied URLs. Retain its strongest citation.
    independent: dict[str, Source] = {}
    source_weights = dict(weights.source_weights)
    for source in term.sources:
        if not set(source.supports) & {"term", "meaning"}:
            continue
        publisher = source.publisher.strip().casefold()
        previous = independent.get(publisher)
        if previous is None or (source_weights.get(source.evidence_kind, 0), source.evidence_kind, source.url or "") > (
                source_weights.get(previous.evidence_kind, 0), previous.evidence_kind, previous.url or ""):
            independent[publisher] = source
    counts = Counter(s.evidence_kind for s in independent.values())
    score = sum(source_weights[kind] * sum(weights.diminishing ** i for i in range(count))
                for kind, count in counts.items() if kind != "testimony")
    documentary = any(kind != "testimony" for kind in counts)
    people, places, outsiders = (summary.people, summary.places, summary.independent) if summary else (0, 0, 0)
    testimony_score = weights.testimony_scale * (1 - math.exp(-people / weights.testimony_saturation))
    testimony_score += weights.place_bonus * math.log1p(places)
    threshold = weights.attested_bars * weights.bar_width
    if not documentary and not term.spoken_use:
        testimony_score = min(testimony_score, threshold - weights.bar_width)
    score = min(5 * weights.bar_width, score + testimony_score)
    bars = min(5, int(score / weights.bar_width))
    label = "attested" if bars >= weights.attested_bars else "unverified"
    if term.coined_by and not term.caught_on:
        label = "bulldust"
    elif label != "attested" and term.produced_by == "agent" and term.searched and term.searched.outcome == "nothing_found" and not outsiders:
        label = "bulldust"
    dated = [s.cited_date for s in term.sources if s.cited_date and "date" in s.supports]
    first = min(dated, key=lambda v: (int(v[:4]), v)) if dated else term.dated_by_curator
    return Assessment(Attestation(round(score, 6), bars, tuple(sorted(counts.items())), people, outsiders, places,
                                   weights.version), label, first)


def metadata_dict(term: TermMetadata, *, derived: bool = False) -> dict[str, Any]:
    names = (*METADATA_KEYS, *sorted(DERIVED_FIELDS)) if derived else METADATA_KEYS
    out = {k: asdict(v) if hasattr(v, "__dataclass_fields__") else list(v) if isinstance(v, tuple) else v
           for k in names if (v := getattr(term, k)) is not None}
    if not derived:
        tiers = dict(term.theme_tiers)
        out["themes"] = [{"name": name, "tier": tiers[name]} if name in tiers else name for name in term.themes]
    out["sources"] = [s.to_dict() for s in term.sources]
    if derived:
        out["attestation"] = term.attestation.to_dict()
    return out


def metadata_rejections(term: TermMetadata, *, allow_misreadable: bool = False) -> tuple[str, ...]:
    reasons = []
    if term.reads_as not in {"australian", "general"}:
        reasons.append("reads_as")
    if term.australian_use == "uncommon":
        reasons.append("australian_use")
    if term.doubtful_definition:
        reasons.append("doubtful_definition")
    if term.misreadable and not allow_misreadable:
        reasons.append("misreadable")
    return tuple(reasons)


def register_rejection(term: TermMetadata, registers) -> str | None:
    if term.register not in registers:
        return f"register '{term.register}' not allowed (allowed: {', '.join(registers)})"
    return None


def theme_rejection(term: TermMetadata, permitted: ThemePermissions) -> str | None:
    if blocked := blocked_themes(term, permitted):
        return "themes not permitted: " + ", ".join(sorted(blocked))
    return None
