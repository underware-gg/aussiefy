"""Reviewed subject placement and the immutable policy shared by every consumer."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from .evidence import TermMetadata

from .errors import SchemaError


THEME_NAME = re.compile(r"[a-z]+(?:_[a-z]+)*")


def parse_tags(raw: object, owner: str) -> tuple[tuple[str, ...], tuple[tuple[str, int], ...]]:
    if not isinstance(raw, list):
        raise SchemaError(f"{owner}: themes must be a list")
    names, tiers = [], []
    for tag in raw:
        name = tag.get("name") if isinstance(tag, dict) else tag
        if not isinstance(name, str) or not THEME_NAME.fullmatch(name):
            raise SchemaError(f"{owner}: themes need canonical names")
        if name in names:
            raise SchemaError(f"{owner}: duplicate theme {name!r}")
        names.append(name)
        if isinstance(tag, dict):
            if set(tag) != {"name", "tier"} or type(tag["tier"]) is not int or tag["tier"] not in range(4):
                raise SchemaError(f"{owner}: a theme tag needs name and an integer tier 0–3")
            tiers.append((name, tag["tier"]))
    return tuple(names), tuple(tiers)


@dataclass(frozen=True)
class ThemePolicy:
    tier: int
    starts: tuple[tuple[str, int], ...]
    overrides: tuple[tuple[str, bool], ...] = ()

    @cached_property
    def limits(self) -> Mapping[str, int]:
        overrides = dict(self.overrides)
        return MappingProxyType({name: (3 if overrides[name] else -1) if name in overrides else self.tier
                                 for name, _ in self.starts})

    @cached_property
    def defaults(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self.starts))

    @cached_property
    def enabled(self) -> frozenset[str]:
        return frozenset(name for name, tier in self.starts if self.limits[name] >= tier)

    def blocked(self, term: TermMetadata) -> tuple[str, ...]:
        tiers = dict(term.theme_tiers)
        return tuple(name for name in term.themes if self.limits[name] < tiers.get(name, self.defaults[name]))

    def to_dict(self) -> dict[str, bool]:
        return {name: name in self.enabled for name, _ in self.starts}

    def rules(self) -> dict[str, dict[str, int]]:
        return {name: {"default_tier": tier, "allowed_through": self.limits[name]} for name, tier in self.starts}


ThemePermissions = ThemePolicy | frozenset[str]


def blocked_themes(term: TermMetadata, permitted: ThemePermissions) -> tuple[str, ...]:
    # Older caller-supplied binary permissions mean exact all-or-none overrides.
    return permitted.blocked(term) if isinstance(permitted, ThemePolicy) else tuple(name for name in term.themes if name not in permitted)
