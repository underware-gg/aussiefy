"""Request-local tuning of the profiles selected by the level and vulgarity dials."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, replace
import math
from types import MappingProxyType

from .errors import UserError
from .model import LevelProfile, RewriteThresholds, SwearProfile
from .schema import CLASSES, FRAMES, GARNISH_KEYS


PROFILE_KEYS = ("substitution", "frames", "garnish", "max_garnish", "garnish_gap", "garnish_per_sentence",
                "rewrite", "stack", "phonetic", "stretch", "swearing")


def _object(raw, keys, path):
    if not isinstance(raw, dict) or any(not isinstance(k, str) for k in raw):
        raise UserError(f"{path} must be an object with setting names")
    unknown = set(raw) - set(keys)
    if unknown:
        raise UserError(f"unknown {path} settings: {', '.join(sorted(unknown))}")


def _number(value, path, *, integer=False, minimum=0, maximum=None):
    valid = type(value) is int if integer else type(value) in (int, float)
    if not valid or (type(value) is float and not math.isfinite(value)) or value < minimum or (maximum is not None and value > maximum):
        bounds = f"{minimum}–{maximum}" if maximum is not None else f"at least {minimum}"
        raise UserError(f"{path} must be a finite {'integer' if integer else 'number'} {bounds}")


def _thaw(value):
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class ProfileOverrides:
    """A validated immutable snapshot; omitted map keys inherit, lists replace."""
    _data: Mapping

    @classmethod
    def parse(cls, raw):
        if isinstance(raw, cls):
            raw = raw.values()
        path = "document_config.profile"
        _object(raw, PROFILE_KEYS, path)
        data = dict(raw)
        maps = {"substitution": CLASSES, "garnish": GARNISH_KEYS, "max_garnish": GARNISH_KEYS,
                "rewrite": tuple(f.name for f in fields(RewriteThresholds)),
                "swearing": tuple(f.name for f in fields(SwearProfile))}
        for key, value in data.items():
            where = f"{path}.{key}"
            if key in maps:
                _object(value, maps[key], where)
                for name, number in value.items():
                    integer = key == "max_garnish" or (key == "rewrite" and name != "max_coverage")
                    minimum = 1 if key == "rewrite" and name in ("min_level", "formal_length") else 0
                    maximum = None
                    if key in ("substitution", "garnish") or (key == "swearing" and name in ("exclaim", "closer")):
                        maximum = 1
                    elif key == "rewrite":
                        maximum = 5 if name == "min_level" else 1 if name == "max_coverage" else None
                    _number(number, f"{where}.{name}", integer=integer, minimum=minimum, maximum=maximum)
                data[key] = MappingProxyType(dict(value))
            elif key == "frames":
                if not isinstance(value, (list, tuple)) or any(not isinstance(v, str) or v not in FRAMES for v in value):
                    raise UserError(f"{where} must be a list from {', '.join(FRAMES)}")
                data[key] = tuple(dict.fromkeys(value))
            elif key == "stretch":
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    raise UserError(f"{where} must be [minimum, maximum] vowel repeats")
                for n in value:
                    _number(n, where, integer=True, minimum=1)
                if value[0] > value[1]:
                    raise UserError(f"{where} minimum must not exceed maximum")
                data[key] = tuple(value)
            else:
                _number(value, where, integer=key in ("garnish_gap", "garnish_per_sentence"),
                        maximum=1 if key == "stack" else None)
        return cls(MappingProxyType(data))

    def values(self) -> dict:
        return _thaw(self._data)

    def apply(self, profile: LevelProfile, swearing: SwearProfile) -> tuple[LevelProfile, SwearProfile]:
        values = dict(self._data)
        for key in ("substitution", "garnish", "max_garnish"):
            if key in values:
                values[key] = {**getattr(profile, key), **values[key]}
        if "rewrite" in values:
            values["rewrite"] = replace(profile.rewrite, **values["rewrite"])
        swearing = replace(swearing, **values.pop("swearing", {}))
        return replace(profile, **values), swearing


def profile_config(profile: LevelProfile, swearing: SwearProfile) -> dict:
    """Complete, reusable tuning settings, including implicit zero rates and fallback limits."""
    values = {k: v for k, v in asdict(profile).items() if k in PROFILE_KEYS}
    values["frames"] = list(profile.frames)
    values["stretch"] = list(profile.stretch)
    values["garnish"] = {k: profile.garnish.get(k, 0.0) for k in GARNISH_KEYS}
    values["max_garnish"] = {k: profile.limit(k) for k in GARNISH_KEYS}
    return {**values, "swearing": asdict(swearing)}
