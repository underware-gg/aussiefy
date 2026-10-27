"""Validated, bounded community pick weights; eligibility and evidence live elsewhere."""

from dataclasses import dataclass, field
import math

from .errors import SchemaError, UserError
from .match_keys import known_match


@dataclass(frozen=True)
class Band:
    lower: float
    upper: float


@dataclass(frozen=True)
class Adjustment:
    match: str
    term: str
    level: int
    vulgarity: int
    embellishment: int
    factor: float
    normal: Band
    popularity: Band

    @property
    def context(self):
        return self.match, self.term, self.level, self.vulgarity, self.embellishment


@dataclass(frozen=True)
class Adjustments:
    by_context: dict[tuple, tuple[Adjustment, ...]] = field(default_factory=dict)

    def factor(self, match: str, term: str, *, level: int, vulgarity: int, embellishment: int,
               popularity: bool = False) -> float:
        records = self.by_context.get((match, term, level, vulgarity, embellishment), ())
        if not records:
            return 1.0
        bands = [r.popularity if popularity else r.normal for r in records]
        common = Band(max(b.lower for b in bands), min(b.upper for b in bands))
        # Logs avoid overflow without losing a later countervailing factor.
        total = math.fsum(math.log(r.factor) for r in records)
        return math.exp(min(math.log(common.upper), max(math.log(common.lower), total)))


def _object(raw, fields, owner):
    if not isinstance(raw, dict) or set(raw) != set(fields):
        raise SchemaError(f"{owner}: expected fields {', '.join(fields)}")
    return raw


def _band(raw, owner):
    if (not isinstance(raw, list) or len(raw) != 2
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in raw)
            or not 0 < raw[0] <= 1 <= raw[1]):
        raise SchemaError(f"{owner}: band must be two finite positive bounds containing 1")
    return Band(*raw)


def load_adjustments(bundles, dictionary) -> Adjustments:
    out = {}
    for origin, raw in bundles:
        r = _object(raw, ("normal", "popularity", "records"), f"{origin}.adjustments")
        normal, popularity = (_band(r[k], f"{origin}.{k}") for k in ("normal", "popularity"))
        if not popularity.lower <= normal.lower <= normal.upper <= popularity.upper:
            raise SchemaError(f"{origin}: popularity band must contain the normal band")
        if not isinstance(r["records"], list):
            raise SchemaError(f"{origin}: adjustment records must be a list")
        seen = set()
        for raw_record in r["records"]:
            row = _object(raw_record, ("match", "term", "level", "vulgarity", "embellishment", "factor"), origin)
            for dial, low, high in (("level", 1, 5), ("vulgarity", 0, 3), ("embellishment", 0, 2)):
                if type(row[dial]) is not int or not low <= row[dial] <= high:
                    raise SchemaError(f"{origin}: adjustment {dial} must be an integer {low}–{high}")
            factor = row["factor"]
            if (type(factor) not in (int, float) or not math.isfinite(factor)
                    or not popularity.lower <= factor <= popularity.upper):
                raise SchemaError(f"{origin}: adjustment factor must fit the popularity band")
            if not isinstance(row["term"], str) or row["term"] not in dictionary.entries:
                raise SchemaError(f"{origin}: unknown adjustment term {row['term']!r}")
            try:
                known = known_match(row["match"], dictionary)
            except UserError as exc:
                raise SchemaError(f"{origin}: {exc}") from exc
            if not known:
                raise SchemaError(f"{origin}: unknown source match {row['match']!r}")
            record = Adjustment(**row, normal=normal, popularity=popularity)
            if record.context in seen:
                raise SchemaError(f"{origin}: duplicate adjustment for the same match, term and dials")
            seen.add(record.context)
            out.setdefault(record.context, []).append(record)
    return Adjustments({k: tuple(v) for k, v in out.items()})
