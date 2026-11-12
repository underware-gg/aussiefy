"""Per-call selection tuning; it changes weights, never meanings or permissions."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from .adjustments import Adjustments
from .errors import UserError, WarningMessage
from .match_keys import SourceMatch, known_match, parse_match_key


@dataclass(frozen=True)
class Preference:
    position: int
    match: str
    root: str
    term: str
    weight: float


@dataclass(frozen=True)
class TuningReport:
    popularity: bool = False
    used: frozenset[int] = frozenset()

    def to_dict(self) -> dict:
        return {"popularity": self.popularity, "preferences": len(self.used)}


@dataclass(frozen=True)
class Tuning:
    adjustments: Adjustments = field(default_factory=Adjustments)
    popularity: bool = False
    exact: dict[str, Preference] = field(default_factory=dict)
    roots: dict[str, Preference] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    @classmethod
    def prepare(cls, raw, dictionary) -> Tuning:
        if raw is None:
            raw = {}
        if not isinstance(raw, dict) or set(raw) - {"popularity", "preferences"}:
            raise UserError("tuning must be an object containing popularity and preferences")
        popularity = raw.get("popularity", False)
        if type(popularity) is not bool:
            raise UserError("popularity must be true or false")
        preferences = raw.get("preferences")
        if preferences is None:
            preferences = []
        if not isinstance(preferences, (list, tuple)):
            raise UserError("preferences must be a latest-first list of match, term and weight objects")
        exact, roots, warnings = {}, {}, []
        for i, row in enumerate(preferences):
            owner = f"preferences[{i}]"
            if not isinstance(row, dict) or set(row) != {"match", "term", "weight"}:
                raise UserError(f"{owner} must contain match, term and weight")
            weight = row["weight"]
            try:
                valid_weight = type(weight) in (int, float) and weight >= 1 and math.isfinite(weight)
            except OverflowError:
                valid_weight = False
            if not valid_weight:
                raise UserError(f"{owner}.weight must be a finite number at least 1")
            if any(not isinstance(row[k], str) or not row[k] for k in ("match", "term")):
                raise UserError(f"{owner}.match and term must be non-empty text")
            try:
                known = known_match(row["match"], dictionary)
            except UserError:
                known = False
            if not known:
                warnings.append(WarningMessage(f"{owner}: unknown source match {row['match']!r}; preference ignored",
                                               code="unknown_preference_match"))
            if row["term"] not in dictionary.entries:
                warnings.append(WarningMessage(f"{owner}: unknown term {row['term']!r}; preference ignored",
                                               code="unknown_preference_term"))
            if not known or row["term"] not in dictionary.entries:
                continue
            root = parse_match_key(row["match"]).root
            preference = Preference(i, row["match"], root, row["term"], weight)
            exact.setdefault(preference.match, preference)
            roots.setdefault(root, preference)
        return cls(dictionary.adjustments, popularity, exact, roots, tuple(warnings))

    def preference(self, match: SourceMatch | None) -> Preference | None:
        if match is None:
            return None
        return self.exact.get(match.key) or self.roots.get(match.root)

    def apply(self, candidates, match: SourceMatch | None, *, level: int, vulgarity: int,
              embellishment: int) -> Preference | None:
        if not candidates or match is None:
            return None
        preference = self.preference(match)
        applied = preference if preference and any(c.entry.id == preference.term for c in candidates) else None
        community = [self.adjustments.factor(match.key, c.entry.id, level=level, vulgarity=vulgarity,
                     embellishment=embellishment, popularity=self.popularity) for c in candidates]
        personal = [applied.weight if applied and c.entry.id == applied.term else 1 for c in candidates]
        if any(factor != 1 for factor in community + personal):
            weights = [math.log(c.weight) + math.log(a) + math.log(p) if c.weight else -math.inf
                       for c, a, p in zip(candidates, community, personal, strict=True)]
            peak = max(weights)
            if peak == -math.inf:
                # A finite multiplier must not resurrect exhausted repeat weights.
                peak = 0.0
            band = "popularity" if self.popularity else "normal"
            for c, a, p, weight in zip(candidates, community, personal, weights, strict=True):
                c.weight = math.exp(weight - peak)
                c.why += f"; community adjustment x {a:g} ({band} band)"
                if applied and c.entry.id == applied.term:
                    c.why += f"; personal preference x {p:g} (from {applied.match})"
                c.why += f", normalised w={c.weight:.3g}"
        return applied
