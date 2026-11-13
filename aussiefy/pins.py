"""Explicit replay choices, scoped to an exact source and dictionary; no host or account state."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .constructions import generate, rendering_entry
from .errors import UserError
from .match_keys import known_match


def source_identity(source):
    return 'sha256:' + hashlib.sha256(source.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Target:
    entry_id: str | None
    construction_id: str | None
    family: str | None
    parts: tuple[tuple[str, str], ...]
    form: str

    @classmethod
    def parse(cls, raw, dictionary):
        if not isinstance(raw, dict) or set(raw) != {'entry_id', 'construction_id', 'family', 'parts', 'form'}:
            raise UserError('pin target needs entry_id, construction_id, family, parts and form')
        if not isinstance(raw['form'], str) or not raw['form']:
            raise UserError('pin target form must be non-empty text')
        eid, cid, family, parts = (raw[k] for k in ('entry_id', 'construction_id', 'family', 'parts'))
        if eid is not None:
            if not isinstance(eid, str) or eid not in dictionary.entries:
                raise UserError('pin target names an unknown entry')
            if cid is not None or family is not None or parts != {}:
                raise UserError('entry pins cannot carry a construction recipe')
        else:
            if not isinstance(cid, str) or not isinstance(family, str):
                raise UserError('construction pins need a construction_id and family')
            catalog = dictionary.construction_catalog
            pattern = next((f for f in catalog.families if f.id == family), None) if catalog else None
            if pattern is None or not isinstance(parts, dict) or set(parts) != {r for r, _ in pattern.slots}:
                raise UserError('construction pin needs a known family and every slot')
            ingredients = {p.id: p for p in catalog.ingredients}
            if any(not isinstance(v, str) or v not in ingredients or ingredients[v].kind != kind
                   for role, kind in pattern.slots for v in (parts[role],)):
                raise UserError('construction pin has an unknown or incompatible ingredient')
        return cls(eid, cid, family, tuple(sorted(parts.items())), raw['form'])

    def to_dict(self):
        return {'entry_id': self.entry_id, 'construction_id': self.construction_id,
                'family': self.family, 'parts': dict(self.parts), 'form': self.form}

    def resolve(self, dictionary, eff, setting, *, seed, mood):
        if self.entry_id is not None:
            return dictionary.entries[self.entry_id], None
        if not setting.invention:
            raise UserError('construction pin requires invention')
        candidates = generate(dictionary, eff, setting, seed=seed, family=self.family,
                              parts=dict(self.parts), limit=1, mood=mood).candidates
        if not candidates or candidates[0].id != self.construction_id or candidates[0].text != self.form:
            raise UserError('construction pin is unavailable or differs from its recipe')
        c = candidates[0]
        return rendering_entry(c, dictionary), c


def target(entry, form, construction=None):
    if construction:
        return Target(None, construction.id, construction.family.id,
                      tuple((p.role, p.ingredient.id) for p in construction.parts), form)
    return Target(entry.id, None, None, (), form)


@dataclass(frozen=True)
class Pin:
    index: int
    kind: str
    span: tuple[int, int]
    match: str | None = None
    placement: str | None = None
    target: Target | None = None
    stack: Target | None = None
    riff: str | None = None
    image_id: str | None = None

    @property
    def key(self):
        return self.kind, self.span, self.placement

    def to_dict(self):
        row = {'kind': self.kind, 'span': list(self.span)}
        if self.kind == 'substitution':
            row.update(match=self.match, target=self.target.to_dict() if self.target else None,
                       stack=self.stack.to_dict() if self.stack else None, riff=self.riff)
        elif self.kind == 'garnish':
            row.update(placement=self.placement, target=self.target.to_dict() if self.target else None)
        else:
            row.update(match=self.match, image_id=self.image_id)
        return row


@dataclass(frozen=True)
class Pins:
    dictionary_id: str
    source_id: str
    seed: int
    complete: bool
    picks: tuple[Pin, ...]

    @classmethod
    def prepare(cls, raw, source, dictionary, seed):
        if raw is None:
            return None
        if not isinstance(raw, dict) or set(raw) != {'version', 'dictionary_id', 'source_id', 'seed', 'complete', 'picks'}:
            raise UserError('pins needs version, dictionary_id, source_id, seed, complete and picks')
        if type(raw['version']) is not int or raw['version'] != 1 or type(raw['complete']) is not bool:
            raise UserError('pins needs version 1 and a boolean complete')
        if raw['dictionary_id'] != dictionary.identity or raw['source_id'] != source_identity(source):
            raise UserError('pins belong to a different dictionary or source')
        if type(raw['seed']) is not int or raw['seed'] != seed:
            raise UserError('pins require their original seed')
        if not isinstance(raw['picks'], list):
            raise UserError('pins.picks must be a list')
        pins, keys = [], set()
        for i, row in enumerate(raw['picks']):
            if not isinstance(row, dict) or row.get('kind') not in {'substitution', 'garnish', 'imagery'}:
                raise UserError('unknown pin kind')
            kind = row['kind']
            fields = {'kind', 'span'} | ({'match', 'target', 'stack', 'riff'} if kind == 'substitution' else
                        {'placement', 'target'} if kind == 'garnish' else {'match', 'image_id'})
            if set(row) != fields:
                raise UserError('pin has missing or unknown fields')
            span = row['span']
            if (not isinstance(span, list) or len(span) != 2 or any(type(x) is not int for x in span)
                    or not 0 <= span[0] < span[1] <= len(source)):
                raise UserError('pin span must address source code points')
            match, placement = row.get('match'), row.get('placement')
            if kind != 'garnish' and (not isinstance(match, str) or not known_match(match, dictionary)):
                raise UserError('pin needs a known source match')
            if kind == 'garnish' and placement not in {'opener', 'connective', 'aside', 'tag', 'tail', 'closer'}:
                raise UserError('unknown pinned garnish placement')
            selected = Target.parse(row['target'], dictionary) if row.get('target') is not None else None
            stack = Target.parse(row['stack'], dictionary) if row.get('stack') is not None else None
            if stack and stack.construction_id:
                raise UserError('a stacked pin must name an entry')
            riff, image_id = row.get('riff'), row.get('image_id')
            if riff is not None and (not isinstance(riff, str) or not riff):
                raise UserError('pin riff must be non-empty text or null')
            if kind == 'substitution' and selected is None and (stack or riff):
                raise UserError('an unchanged pin cannot carry a stack or riff')
            if image_id is not None and (not isinstance(image_id, str) or image_id not in {x.id for x in dictionary.imagery}):
                raise UserError('unknown pinned image')
            pin = Pin(i, kind, tuple(span), match, placement, selected, stack, riff, image_id)
            if pin.key in keys:
                raise UserError('duplicate pin at one source spot')
            keys.add(pin.key)
            pins.append(pin)
        return cls(dictionary.identity, source_identity(source), seed, raw['complete'], tuple(pins))

    def at(self, kind, span, *, placement=None, match=None):
        pin = next((p for p in self.picks if p.key == (kind, tuple(span), placement)), None)
        if pin is not None and pin.match != match:
            raise UserError('pin source match differs from the current reading')
        return pin

    def check_used(self, used):
        missing = {p.index for p in self.picks} - set(used)
        if missing:
            raise UserError('pins could not be applied: ' + ', '.join(map(str, sorted(missing))))

    def to_dict(self):
        return {'version': 1, 'dictionary_id': self.dictionary_id, 'source_id': self.source_id,
                'seed': self.seed, 'complete': self.complete, 'picks': [p.to_dict() for p in self.picks]}


def capture(result, *, offset=0):
    from .match_keys import detection_match
    rows = []
    for rec in result.records:
        if not rec.substituted and not rec.image_id:
            continue
        span = tuple(x + offset for x in rec.span)
        identified = detection_match(rec.det)
        if identified is None:
            raise UserError('this source reading has no replay match identity')
        match = identified.key
        if rec.substituted:
            rows.append(Pin(0, 'substitution', span, match=match,
                target=target(rec.chosen.entry, rec.form, rec.chosen.construction),
                stack=target(rec.stacked.entry, rec.stacked_form) if rec.stacked else None, riff=rec.riff))
        if rec.image_id:
            rows.append(Pin(0, 'imagery', span, match=match, image_id=rec.image_id))
    for g in result.garnish:
        if not g.text or g.image_id:
            continue
        span = tuple(x + offset for x in result.sentences[g.sentence])
        entry = g.construction or g.entry_id
        selected = target(entry, g.text, g.construction) if g.construction else Target(g.entry_id, None, None, (), g.text)
        rows.append(Pin(0, 'garnish', span, placement=g.placement, target=selected))
    return rows


def packet(result, rows):
    return Pins(result.dictionary_id, source_identity(result.source), result.seed, True, tuple(rows)).to_dict()
