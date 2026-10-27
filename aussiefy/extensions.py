"""Additive community manifests and evidence composition, before indexes are built."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import re

from .evidence import credit_records, parse_credit, parse_metadata, parse_sources
from .errors import SchemaError
from .identifiers import CONCEPT_ID, ENTRY_ID, NAMESPACE, in_namespace
from .terms import form_key
from .schema import parse_entry

FORMAT = "aussiefy-dictionary-extension/v1"
EVIDENCE_FIELDS = {"evidence_for", "sources", "testimony", "spoken_use", "caught_on", "credit"}


@dataclass(frozen=True)
class Extension:
    namespace: str
    concepts: dict
    entries: list
    evidence: list
    adjustments: dict | None


def _community_sources(raw, owner):
    return [dict(source.to_dict(), kind="community", basis=source.evidence_kind)
            for source in parse_sources(raw, owner)]


def parse_extension(raw, owner) -> Extension:
    allowed = {"format", "namespace", "concepts", "entries", "evidence", "adjustments"}
    if set(raw) - allowed:
        raise SchemaError(f"{owner}: unknown extension fields {sorted(set(raw) - allowed, key=str)}")
    ns = raw.get("namespace")
    if not isinstance(ns, str) or not re.fullmatch(NAMESPACE, ns):
        raise SchemaError(f"{owner}: extension namespace must be lower-case kebab-case")
    concepts, entries, evidence = (deepcopy(raw.get(k, default))
                                  for k, default in (("concepts", {}), ("entries", []), ("evidence", [])))
    if not isinstance(concepts, dict) or not isinstance(entries, list) or not isinstance(evidence, list):
        raise SchemaError(f"{owner}: concepts must be a mapping; entries and evidence must be lists")
    for cid in concepts:
        if not in_namespace(cid, ns) or not CONCEPT_ID.fullmatch(cid):
            raise SchemaError(f"{owner}: extension concept ids must be qualified with {ns}:")
        if isinstance(concepts[cid], dict) and concepts[cid].get("no_entries") is True:
            raise SchemaError(f"{owner}: concept {cid}: guards are core-only until ED16 settles")
    for entry in entries:
        if (not isinstance(entry, dict) or not in_namespace(entry.get("id"), ns)
                or not ENTRY_ID.fullmatch(entry["id"]) or "promoted_from" in entry):
            raise SchemaError(f"{owner}: extension entry ids must be qualified with {ns}:; promotion belongs in core")
        entry["sources"] = _community_sources(entry.get("sources"), owner)
    for record in evidence:
        if (not isinstance(record, dict) or set(record) - EVIDENCE_FIELDS
                or not isinstance(record.get("evidence_for"), str)
                or not ENTRY_ID.fullmatch(record["evidence_for"])):
            raise SchemaError(f"{owner}: evidence needs evidence_for and only additive evidence fields")
        if "sources" in record:
            record["sources"] = _community_sources(record["sources"], owner)
    return Extension(ns, concepts, entries, evidence, raw.get("adjustments"))


def compose_evidence(entries, extensions):
    """Merge citations and credit, replacing exported aggregates rather than summing anonymous people."""
    promoted = {}
    for eid, entry in entries.items():
        if entry.get("promoted_from") is not None:
            old = parse_entry(entry).promoted_from
            if old in promoted:
                raise SchemaError(f"{old}: promoted by more than one core entry")
            promoted[old] = eid
    for old, core in promoted.items():
        if old in entries:
            raise SchemaError(f"{old}: already promoted to {core}; regenerate the extension")

    summaries = {}
    for owner, extension in extensions:
        for record in extension.evidence:
            eid = record["evidence_for"]
            if eid in promoted:
                raise SchemaError(f"{eid}: promoted to {promoted[eid]}; evidence must name the core id")
            if eid not in entries:
                raise SchemaError(f"{owner}: evidence_for names unknown entry {eid!r}")
            target = deepcopy(entries[eid])
            previous_metadata = parse_metadata(target, eid)
            if "sources" in record:
                target["sources"] = [s.to_dict() for s in dict.fromkeys(
                    previous_metadata["sources"] + parse_sources(record["sources"], eid))]
            if "credit" in record:
                current = previous_metadata.get("credit")
                supplied = record["credit"]
                credits = credit_records(supplied) if isinstance(supplied, str) else parse_credit(supplied, eid)
                target["credit"] = [asdict(c) for c in dict.fromkeys(credit_records(current) + credits)]
            for key in ("testimony", "spoken_use", "caught_on"):
                if key in record:
                    target[key] = deepcopy(record[key])
            merged_metadata = parse_metadata(target, eid)
            if "testimony" in record:
                parsed = merged_metadata["testimony"]
                if eid in summaries and summaries[eid] != parsed:
                    raise SchemaError(f"{eid}: provide one consolidated testimony snapshot, not separate counts")
                previous = previous_metadata.get("testimony")
                if previous and parsed.summary_date < previous.summary_date:
                    raise SchemaError(f"{eid}: testimony snapshot is older than the loaded summary")
                summaries[eid] = parsed
            for key in ("spoken_use", "caught_on"):
                if key in record:
                    newer = merged_metadata[key]
                    previous = previous_metadata.get(key)
                    if previous and previous.date == newer.date and previous != newer:
                        raise SchemaError(f"{eid}: conflicting {key} records on the same date")
                    if previous and newer.date < previous.date:
                        target[key] = deepcopy(entries[eid][key])
            entries[eid] = target


def validate_extension_forms(entries, extensions):
    core_forms = {}
    for eid, entry in entries.items():
        if ":" not in eid:
            for form in entry.all_forms:
                core_forms.setdefault(form_key(form), []).append(entry)
    for _, extension in extensions:
        for raw in extension.entries:
            entry = entries[raw["id"]]
            for form in entry.all_forms:
                for core in core_forms.get(form_key(form), ()):
                    if entry.frame == core.frame and set(entry.concept) & set(core.concept):
                        raise SchemaError(f"{entry.id}: same form and meaning as core {core.id}; use evidence_for")
