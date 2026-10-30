"""Reviewed source-meaning conditions; these are independent of an output entry's grammar."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from typing import NamedTuple

from . import morph
from .context import context_object
from .errors import SchemaError
from .matcher import compile_pattern, is_name, match_at


@dataclass(frozen=True)
class MeaningContext:
    preposition: str
    argument: str
    heads: tuple[str, ...] = ()
    not_heads: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    control: str | None = None
    person: bool | None = None

    def to_dict(self) -> dict:
        out = {'preposition': self.preposition, 'argument': self.argument}
        for key in ('heads', 'not_heads', 'actions'):
            if value := getattr(self, key):
                out[key] = list(value)
        if self.control is not None:
            out['control'] = self.control
        if self.person is not None:
            out['person'] = self.person
        return out

    @cached_property
    def action_patterns(self):
        return tuple(compile_pattern(text, 'vp', (), 3) for text in self.actions)


def parse_meaning_context(raw, owner: str) -> MeaningContext | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) - {'preposition', 'argument', 'heads', 'not_heads', 'actions', 'control', 'person'}:
        raise SchemaError(f'{owner}: invalid source_context fields')
    prep, argument = raw.get('preposition'), raw.get('argument')
    if not isinstance(prep, str) or not re.fullmatch('[a-z]+', prep) or argument not in ('np', 'ing', 'nominal'):
        raise SchemaError(f'{owner}: source_context needs a preposition and np, ing or nominal argument')
    values = {}
    for key in ('heads', 'not_heads', 'actions'):
        value = raw.get(key, [])
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise SchemaError(f'{owner}: source_context.{key} must list text')
        values[key] = tuple(dict.fromkeys(value))
    for key in ('heads', 'not_heads'):
        if any(not re.fullmatch('[a-z]+', h) for h in values[key]):
            raise SchemaError(f'{owner}: source_context.{key} must list lowercase words')
    if set(values['heads']) & set(values['not_heads']):
        raise SchemaError(f'{owner}: source_context heads and not_heads must not overlap')
    control, person = raw.get('control'), raw.get('person')
    if control not in (None, 'subject') or control is not None and argument != 'ing':
        raise SchemaError(f'{owner}: subject control requires an ing argument')
    if person is not None and type(person) is not bool:
        raise SchemaError(f'{owner}: source_context.person must be a boolean')
    if values['actions'] and argument != 'ing':
        raise SchemaError(f'{owner}: source_context.actions requires an ing argument')
    context = MeaningContext(prep, argument, **values, control=control, person=person)
    try:
        for pattern in context.action_patterns:
            if (pattern.clause_start or pattern.clause_end or pattern.person_only or pattern.object_argument
                    or pattern.before_modifier or any(e.kind not in {'lit', 'slot'} for e in pattern.elements)):
                raise ValueError('actions use bounded literal/slot patterns without frame directives')
    except ValueError as exc:
        raise SchemaError(f'{owner}: source_context.actions: {exc}') from None
    return context


class ContextEvidence(NamedTuple):
    supported: bool | None
    end: int


def meaning_context(context: MeaningContext, tokens, end: int, tags, person_nouns, *, subject=None) -> ContextEvidence:
    if end >= len(tokens) or tokens[end].norm != context.preposition:
        return ContextEvidence(None, end)
    start = end + 1
    if start >= len(tokens):
        return ContextEvidence(None, start)
    if context.control == 'subject' and subject is None:
        return ContextEvidence(None, start)
    kinds = ('np', 'ing') if context.argument == 'nominal' else (context.argument,)
    obj, kind = None, ''
    for candidate in kinds:
        obj = context_object(tokens, start, tags, kind=candidate)
        if obj is not None:
            kind = candidate
            break
    if obj is None or not obj.settled:
        return ContextEvidence(None, obj.end if obj is not None else start)
    head = tokens[start] if kind == 'ing' else tokens[obj.end - 1]
    if head.norm in context.not_heads or morph.singular_of(head.norm) in context.not_heads:
        return ContextEvidence(False, obj.end)
    if context.heads and is_name(head) and head.norm in context.heads:
        return ContextEvidence(None, obj.end)
    if context.person is False and (head.norm in person_nouns or is_name(head)):
        return ContextEvidence(False, obj.end)
    if context.person is True and head.norm not in person_nouns and not is_name(head):
        return ContextEvidence(None, obj.end)
    if context.heads and head.norm not in context.heads and morph.singular_of(head.norm) not in context.heads:
        return ContextEvidence(None, obj.end)
    if context.actions:
        for pattern in context.action_patterns:
            match = match_at(pattern, tokens, start)
            if match is not None and match.end <= obj.end \
                    and all(tags[i].startswith('RB') for i in range(match.end, obj.end)):
                return ContextEvidence(True, obj.end)
        return ContextEvidence(None, obj.end)
    return ContextEvidence(True, obj.end)
