"""Phrases whose component words must not take an unrelated reading or dialect swap."""

from dataclasses import dataclass, replace
from functools import cached_property

from .matcher import Pattern, PatternIndex, compile_pattern
from .schema import FRAMES, SchemaError, parse_not_in
from .text import tokenize

KINDS = frozenset({'set_phrase', 'other_sense', 'grammar'})
ENGLISHES = frozenset({'unknown', 'us', 'uk'})


@dataclass(frozen=True)
class Fence:
    phrase: str
    frame: str
    kind: str
    reason: str
    meanings: bool
    dialect: frozenset[str]
    not_in: frozenset[str] = frozenset()
    examples: tuple[str, ...] = ()
    inflect_head: bool = True

    @cached_property
    def pattern(self) -> Pattern:
        return replace(compile_pattern(self.phrase, self.frame, (), 3, inflect_head=self.inflect_head),
                       guard=True, fence=self)

    def applies(self, english: str | None, genre: str | tuple[str, ...]) -> bool:
        domains = (genre,) if isinstance(genre, str) else genre
        return (english or 'unknown') in self.dialect and not self.not_in.intersection(domains)


def pattern_key(pattern: Pattern) -> tuple:
    """Equivalent patterns share a fence even if one writes an inflected alternative explicitly."""
    return (pattern.frame, pattern.elements, pattern.person_only, pattern.before_modifier,
            pattern.clause_end, pattern.clause_start, pattern.object_argument)


def parse_fences(raw) -> tuple[Fence, ...]:
    if not isinstance(raw, list):
        raise SchemaError('fences.yaml: expected a list')
    fences, seen = [], set()
    for i, row in enumerate(raw):
        where = f'fences.yaml: item {i + 1}'
        required = {'phrase', 'frame', 'kind', 'scope', 'reason'}
        if (not isinstance(row, dict) or not required <= row.keys()
                or row.keys() - required - {'examples', 'inflect_head'}):
            raise SchemaError(f'{where}: needs phrase, frame, kind, scope and reason')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ('phrase', 'frame', 'kind')):
            raise SchemaError(f'{where}: phrase, frame and kind must be non-empty text')
        if not isinstance(row['reason'], str) or row['reason'] and not row['reason'].strip():
            raise SchemaError(f'{where}: reason must be text, or empty when derived evidence explains every form')
        inflect_head = row.get('inflect_head', True)
        if type(inflect_head) is not bool:
            raise SchemaError(f'{where}: inflect_head must be a boolean')
        if row['kind'] not in KINDS or row['frame'] not in FRAMES:
            raise SchemaError(f'{where}: unknown kind or frame')
        scope = row['scope']
        if not isinstance(scope, dict) or set(scope) != {'meanings', 'dialect', 'not_in'}:
            raise SchemaError(f'{where}: scope needs meanings, dialect and not_in')
        dialect = scope['dialect']
        if (not isinstance(scope['meanings'], bool) or not isinstance(dialect, list)
                or any(not isinstance(v, str) or v not in ENGLISHES for v in dialect)
                or len(set(dialect)) != len(dialect) or not (scope['meanings'] or dialect)):
            raise SchemaError(f'{where}: scope needs a boolean meanings and distinct dialects from {sorted(ENGLISHES)}')
        if not isinstance(scope['not_in'], list) or any(not isinstance(v, str) for v in scope['not_in']):
            raise SchemaError(f'{where}: not_in must be a list of document domains')
        examples = row.get('examples', [])
        if (not isinstance(examples, list) or any(not isinstance(v, str) or not v.strip() for v in examples)
                or len(set(examples)) != len(examples)):
            raise SchemaError(f'{where}: examples must be distinct non-empty strings')
        fence = Fence(row['phrase'], row['frame'], row['kind'], row['reason'], scope['meanings'],
                      frozenset(dialect), parse_not_in(where, scope['not_in']), tuple(examples), inflect_head)
        try:
            key = pattern_key(fence.pattern)
            index = PatternIndex([fence.pattern])
            for example in fence.examples:
                if not index.find(tokenize(example)):
                    raise SchemaError(f'{where}: example {example!r} does not match the fence')
        except ValueError as exc:
            raise SchemaError(f'{where}: {exc}') from exc
        if key in seen:
            raise SchemaError(f'{where}: duplicate fence {fence.phrase!r}; combine its scopes')
        seen.add(key)
        fences.append(fence)
    return tuple(fences)
