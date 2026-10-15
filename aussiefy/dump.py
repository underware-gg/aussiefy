"""Canonical YAML writer for machine-managed dictionary files."""

from __future__ import annotations

from typing import Any, Iterable

import yaml

from .schema import Entry


class _Dumper(yaml.SafeDumper):
    pass


def _represent_list(dumper: yaml.SafeDumper, data: list):
    flow = all(isinstance(x, (str, int, float)) for x in data) and sum(len(str(x)) for x in data) < 80
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)


def _represent_dict(dumper: yaml.SafeDumper, data: dict):
    flow = bool(data) and all(isinstance(v, (str, int, float)) for v in data.values()) and len(str(data)) < 60
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items(), flow_style=flow)


_Dumper.add_representer(list, _represent_list)
_Dumper.add_representer(dict, _represent_dict)


def dump_yaml(data: Any) -> str:
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=110)


def dump_entries(entries: Iterable[Entry | dict], header: str = "") -> str:
    chunks = [header.rstrip() + "\n"] if header else []
    for e in entries:
        d = e.to_dict() if isinstance(e, Entry) else e
        chunks.append(dump_yaml([d]))
    return "\n".join(chunks)
