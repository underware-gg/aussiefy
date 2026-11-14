"""Declared output requirements, distinct from recognising the source's meaning."""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import morph
from .context import following_shape
from .errors import SchemaError


@dataclass(frozen=True)
class GrammarRequirements:
    following: tuple[str, ...] | None = None
    not_following: tuple[str, ...] = ()
    nominal_roles: tuple[str, ...] = ()
    aspect: str = 'unknown'
    voice: str = 'unknown'
    position: str = 'source'

    def to_dict(self):
        out = {}
        if self.following is not None:
            out['following'] = list(self.following)
        if self.not_following:
            out['not_following'] = list(self.not_following)
        if self.nominal_roles:
            out['nominal_roles'] = list(self.nominal_roles)
        if self.aspect != 'unknown':
            out['aspect'] = self.aspect
        if self.voice != 'unknown':
            out['voice'] = self.voice
        if self.position != 'source':
            out['position'] = self.position
        return out


@dataclass(frozen=True)
class GrammarEvidence:
    following: str | None = None
    aspect: str | None = None
    voice: str | None = None
    nominal_role: str = 'unknown'


def grammar_evidence(requirements, det, tokens, tags, *, complete: bool = True) -> GrammarEvidence:
    requirements = tuple(requirements)
    boundary = (following_shape(tokens, det.end, tags, complete=complete)
                if any(r.following is not None or r.not_following for r in requirements) else None)
    if any(r.aspect not in {'unknown', 'either'} or r.voice not in {'unknown', 'either'} for r in requirements):
        aspect, voice = source_verb_shape(det, tokens, tags)
    else:
        aspect, voice = None, None
    return GrammarEvidence(boundary, aspect, voice, det.nominal_role)


def parse_requirements(raw, owner: str) -> GrammarRequirements:
    if raw is None:
        return GrammarRequirements()
    if not isinstance(raw, dict) or set(raw) - {'following', 'not_following', 'nominal_roles', 'aspect', 'voice', 'position'}:
        raise SchemaError(f'{owner}: grammar has invalid fields')
    following = raw.get('following')
    shapes = {'none', 'adverb', 'np', 'content', 'infinitive', 'verb_base'}
    if following is not None and (not isinstance(following, list) or not following
            or any(not isinstance(s, str) or not (s in shapes or re.fullmatch(r'prep:[a-z]+', s))
                   for s in following)):
        raise SchemaError(f'{owner}: grammar.following must list boundary shapes or prep:<word>')
    forbidden = raw.get('not_following', [])
    if not isinstance(forbidden, list) or any(not isinstance(s, str) or not (
            s in shapes or re.fullmatch(r'prep:[a-z]+', s)) for s in forbidden):
        raise SchemaError(f'{owner}: grammar.not_following must list boundary shapes or prep:<word>')
    roles = raw.get('nominal_roles', [])
    if not isinstance(roles, list) or any(not isinstance(s, str) or s not in {'head', 'modifier', 'possessor'} for s in roles):
        raise SchemaError(f'{owner}: grammar.nominal_roles must list head, modifier or possessor')
    aspect, voice = raw.get('aspect', 'unknown'), raw.get('voice', 'unknown')
    if not isinstance(aspect, str) or aspect not in {'unknown', 'state', 'event', 'either'}:
        raise SchemaError(f'{owner}: grammar.aspect must be unknown, state, event or either')
    if not isinstance(voice, str) or voice not in {'unknown', 'active', 'passive', 'either'}:
        raise SchemaError(f'{owner}: grammar.voice must be unknown, active, passive or either')
    position = raw.get('position', 'source')
    if not isinstance(position, str) or position not in {'source', 'before_verb'}:
        raise SchemaError(f'{owner}: grammar.position must be source or before_verb')
    return GrammarRequirements(position=position, following=tuple(dict.fromkeys(following)) if following is not None else None,
        not_following=tuple(dict.fromkeys(forbidden)), nominal_roles=tuple(dict.fromkeys(roles)), aspect=aspect, voice=voice)


def source_verb_shape(det, tokens, tags) -> tuple[str | None, str | None]:
    if det.frame in {'adj', 'predicate_adj'}:
        return 'state', None
    if det.frame == 'clause' and 'be' in det.captures:
        copula = det.captures['be']
        i = next((i + 1 for i, token in enumerate(tokens) if token.start == copula.start), len(tokens))
        while i < det.end and tags[i].startswith('RB'):
            i += 1
        if i < det.end and tags[i].startswith('JJ'):
            return 'state', None
    if det.frame != 'vp':
        return None, None
    i = det.start
    before = i - 1
    while before >= 0 and tags[before].startswith('RB'):
        before -= 1
    previous = tokens[before].norm if before >= 0 else None
    word = tokens[i].norm
    participle = bool(morph.is_participle(word))
    if previous in morph.BE_FORMS and participle:
        if det.end < len(tokens) and tokens[det.end].norm == 'by' \
                and following_shape(tokens, det.end, tags) == 'prep:by':
            return 'event', 'passive'
        # A be+participle can be a result state or a passive event, never proof of an active event.
        return None, None
    if tags[i].startswith('JJ'):
        return 'state', None
    if previous in morph.BE_FORMS and det.inflection == 'ing':
        return 'event', 'active'
    if previous in morph.HAVE_FORMS | morph.DO_FORMS | {'will', 'would', 'may', 'might', 'can', 'could',
                                                       'shall', 'should', 'must', 'to'}:
        return 'event', 'active'
    if tags[i] in {'VBD', 'VBP', 'VBZ'} and (det.captures.get('agent') or det.subject_noun):
        return 'event', 'active'
    if tags[i] == 'VB' and (i == 0 or tokens[i - 1].is_punct):
        return 'event', 'active'
    return None, None


def grammar_problem(entry, det, tokens, tags, *, complete: bool = True,
                    evidence: GrammarEvidence | None = None) -> str | None:
    requirement = entry.grammar
    if requirement.position == 'before_verb' and det.moved_prefix is None:
        index = det.end
        while index < len(tokens) and tags[index].startswith('RB'):
            index += 1
        from .pos import VERBS
        if index >= len(tokens) or tags[index] not in VERBS:
            return 'cannot establish a before-verb adverb position'
    if evidence is None:
        evidence = grammar_evidence((requirement,), det, tokens, tags, complete=complete)
    if requirement.nominal_roles and evidence.nominal_role not in requirement.nominal_roles:
        return 'cannot establish a supported nominal role'
    if requirement.not_following:
        if evidence.following is None:
            return 'cannot establish the required following grammar'
        if evidence.following in requirement.not_following:
            return f'following {evidence.following} conflicts with the declared grammar'
    if requirement.following is not None:
        shape = evidence.following
        if shape is None:
            return 'cannot establish the required following grammar'
        allowed = requirement.following
        if shape not in allowed and not (shape == 'np' and 'content' in allowed):
            return f'following {shape} does not fit the declared grammar'
    if requirement.aspect not in {'unknown', 'either'} or requirement.voice not in {'unknown', 'either'}:
        aspect, voice = evidence.aspect, evidence.voice
        if requirement.aspect not in {'unknown', 'either'} and aspect != requirement.aspect:
            return f'cannot establish required {requirement.aspect} aspect'
        if requirement.voice not in {'unknown', 'either'} and voice != requirement.voice:
            return f'cannot establish required {requirement.voice} voice'
    return None


def grammar_coverage(entries) -> dict[str, int]:
    entries = tuple(entries)
    return {'entries': len(entries),
            'following': sum(e.grammar.following is not None or bool(e.grammar.not_following) for e in entries),
            'aspect': sum(e.grammar.aspect != 'unknown' for e in entries),
            'voice': sum(e.grammar.voice != 'unknown' for e in entries),
            'nominal_roles': sum(bool(e.grammar.nominal_roles) for e in entries),
            'number': sum(e.number != 'any' for e in entries)}
