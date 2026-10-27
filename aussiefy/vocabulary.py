"""Compose raw vocabulary records before schema validation and index construction."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from .schema import CONCEPT_KEYS, ENTRY_KEYS, SchemaError, parse_concept, parse_entry, validate_entry_id
from .evidence import parse_sources
from .extensions import FORMAT, parse_extension


@dataclass
class Vocabulary:
    concepts: dict[str, dict]
    entries: dict[str, dict] = field(default_factory=dict)
    origins: dict[str, str] = field(default_factory=dict)
    changes: list[dict[str, Any]] = field(default_factory=list)
    sources: dict[str, list[dict]] = field(default_factory=dict)
    extensions: list = field(default_factory=list)

    def add_entries(self, records: list, origin: str, errors: list[str], *, validate: bool = False) -> None:
        for raw in records:
            try:
                eid = validate_entry_id(raw, origin)
                if eid in self.entries:
                    raise SchemaError(f"duplicate id {eid!r} (first in {self.origins[eid]})")
                if validate:
                    parse_entry(raw, origin)
                record = deepcopy(raw)
                if eid in self.sources:
                    inline = parse_sources(record.get("sources"), eid)
                    inherited = parse_sources(self.sources[eid], f"sources.yaml {eid}")
                    record["sources"] = [s.to_dict() for s in dict.fromkeys(inline + inherited)]
                self.entries[eid] = record
                self.origins[eid] = origin
            except SchemaError as exc:
                errors.append(f"{origin}: {exc}")

    def apply(self, raw: dict | list, origin: str, errors: list[str]) -> None:
        if isinstance(raw, list):
            self.add_entries(raw, origin, errors, validate=True)
            return
        if raw.get("format") == FORMAT:
            try:
                extension = parse_extension(raw, origin)
            except SchemaError as exc:
                errors.append(str(exc))
                return
            self._additions(extension.concepts, extension.entries, origin, errors)
            self.extensions.append((origin, extension))
            return
        allowed = {"format", "add_concepts", "add_entries", "patch_concepts", "patch_entries"}
        if set(raw) - allowed:
            errors.append(f"{origin}: unknown overlay fields {sorted(set(raw) - allowed, key=str)}")
            return
        if raw.get("format") != "aussiefy-dictionary-overlay/v1":
            errors.append(f"{origin}: format must be aussiefy-dictionary-overlay/v1")
            return
        self._additions(raw.get("add_concepts", {}), raw.get("add_entries", []), origin, errors)
        self._patch(raw.get("patch_concepts", {}), self.concepts, CONCEPT_KEYS, "concept", origin, errors)
        self._patch(raw.get("patch_entries", {}), self.entries, set(ENTRY_KEYS) - {"id"}, "entry", origin, errors)

    def _additions(self, additions, entries, origin, errors):
        if not isinstance(additions, dict):
            errors.append(f"{origin}: add_concepts must be a mapping")
        else:
            for cid, record in additions.items():
                if cid in self.concepts:
                    errors.append(f"{origin}: duplicate concept {cid!r}; use patch_concepts")
                else:
                    try:
                        parse_concept(cid, record)
                    except SchemaError as exc:
                        errors.append(f"{origin}: add_concepts: {exc}")
                        continue
                    self.concepts[cid] = deepcopy(record)
                    self.changes.append(dict(origin=origin, kind="concept", id=cid, operation="add"))
        if not isinstance(entries, list):
            errors.append(f"{origin}: add_entries must be a list")
        else:
            existing = set(self.entries)
            self.add_entries(entries, origin, errors, validate=True)
            self.changes.extend(dict(origin=origin, kind="entry", id=eid, operation="add")
                                for eid in self.entries if eid not in existing)

    def _patch(self, patches, records, allowed, kind, origin, errors) -> None:
        section = "patch_entries" if kind == "entry" else "patch_concepts"
        if not isinstance(patches, dict):
            errors.append(f"{origin}: {section} must be a mapping")
            return
        for key, patch in patches.items():
            if key not in records:
                errors.append(f"{origin}: {section}: cannot patch unknown {kind} {key!r}")
                continue
            if not isinstance(patch, dict):
                errors.append(f"{origin}: {section} {key!r}: expected a mapping")
                continue
            if set(patch) - allowed:
                errors.append(f"{origin}: {section} {key!r}: unknown fields {sorted(set(patch) - allowed, key=str)}")
                continue
            if not isinstance(records[key], dict):
                errors.append(f"{origin}: {kind} {key!r}: cannot patch a malformed base record")
                continue
            merged = {**records[key], **deepcopy(patch)}
            try:
                parse_entry(merged, origin) if kind == "entry" else parse_concept(key, merged)
            except SchemaError as exc:
                errors.append(f"{origin}: {section} {key!r}: {exc}")
                continue
            records[key] = merged
            self.changes.append(dict(origin=origin, kind=kind, id=key, operation="patch", fields=sorted(patch)))
            if kind == "entry":
                self.origins[key] = origin
