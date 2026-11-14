"""Validated request-owned wording; never dictionary metadata or tuning evidence."""

from dataclasses import dataclass
import hashlib
import json
import re

from .errors import UserError
from .masks import profanity_rating
from .schema import Entry, SchemaError, parse_entry
from .terms import fold

MAX_PERSONAL_TERMS = 50
MAX_PHRASE_LENGTH = 120
MAX_PHRASE_WORDS = 12
_WORD = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*['’]?")


@dataclass(frozen=True)
class PersonalTerm:
    phrase: str
    term: str
    vulgarity: int
    key: str

    def rendering_entry(self, frame: str) -> Entry:
        return parse_entry({'id': self.key.replace(':', '-'), 'form': self.term,
                            'concept': ['PERSONAL'], 'frame': frame, 'vulgarity': self.vulgarity,
                            'class': 'lexical' if len(self.term.split()) == 1 else 'phrase'})


@dataclass(frozen=True)
class PersonalTerms:
    provided: int = 0
    items: tuple[PersonalTerm, ...] = ()


def _phrase(value, field):
    if (not isinstance(value, str) or not value or value != value.strip()
            or len(value) > MAX_PHRASE_LENGTH or len(value.split()) > MAX_PHRASE_WORDS
            or any(not _WORD.fullmatch(word) for word in value.split())
            or '\n' in value or '\r' in value):
        raise UserError(f'personal_terms {field} must contain 1–12 whole words, at most 120 characters, without markup or slots')
    return ' '.join(value.split())


def prepare(raw, dictionary, *, hook=None, dials=None) -> PersonalTerms:
    if hook is not None:
        if raw is not None:
            raise UserError('personal_terms come from the host for this call')
        raw = hook(**dials)
    if raw is None:
        return PersonalTerms()
    if not isinstance(raw, list) or len(raw) > MAX_PERSONAL_TERMS:
        raise UserError(f'personal_terms must be a list of at most {MAX_PERSONAL_TERMS} items')
    items = {}
    for item in raw:
        if not isinstance(item, dict) or not {'phrase', 'term'} <= set(item) or set(item) - {'phrase', 'term', 'vulgarity'}:
            raise UserError('personal_terms items need phrase, term and optional vulgarity')
        phrase, term = (_phrase(item[name], name) for name in ('phrase', 'term'))
        tier = item.get('vulgarity', profanity_rating(term, dictionary))
        if type(tier) is not int or not 0 <= tier <= 3:
            raise UserError('personal_terms vulgarity must be an integer from 0 to 3')
        digest = hashlib.sha256(json.dumps([fold(phrase), term, tier], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        parsed = PersonalTerm(fold(phrase), term, tier, 'personal:' + digest)
        try:
            parsed.rendering_entry('np')
        except SchemaError as exc:
            raise UserError(f'personal_terms: {exc}') from exc
        key = fold(phrase)
        if key in items and items[key] != parsed:
            raise UserError('personal_terms has conflicting terms for the same source phrase')
        items.setdefault(key, parsed)
    return PersonalTerms(len(raw), tuple(items.values()))


@dataclass(frozen=True)
class PersonalMatch:
    term: PersonalTerm
    detection: object


def find(tokens, prepared, readings, dictionary, tags, *, complete=True):
    from . import pos
    from .detect import Detection, check_frame
    from .matcher import compile_pattern, match_at
    from .text import tokenize
    from dataclasses import replace

    matches = []
    for term in prepared.items:
        phrase_tokens = tokenize(term.phrase)
        plain = tuple(token.norm for token in phrase_tokens)
        for start, token in enumerate(tokens):
            if not token.is_word:
                continue
            exact_end = start + len(plain)
            exact = tuple(t.norm for t in tokens[start:exact_end]) == plain
            tag = tags[start]
            frames = (('np',) if tag in pos.NAMES | pos.NOUNS | {'DT', 'PRP$', 'PRP'} else
                      ('vp',) if tag in pos.VERBS else
                      ('predicate_adj', 'adj') if tag.startswith('JJ') else
                      ('adv',) if tag.startswith('RB') else ('np', 'vp', 'adj', 'adv', 'interjection'))
            detection = None
            for frame in frames:
                pattern = compile_pattern(term.phrase, frame, (), 3)
                matched = match_at(pattern, tokens, start, tags=tags)
                if matched is None:
                    continue
                detection = check_frame(matched, tokens, dictionary.adjective_nouns, tags, complete=complete)
                if detection is not None:
                    break
            if detection is None and exact:
                detection = Detection(start, exact_end, (), frames[0], 3, 'personal', term.phrase)
            if detection is None:
                continue
            inferred = [reading for reading in readings
                        if reading.start == detection.start and reading.end == detection.end
                        and (reading.source_pattern is None or reading.source_pattern.fence is None)]
            if len(inferred) == 1:
                detection = replace(inferred[0])
            else:
                detection = replace(detection, concepts=(), source_pattern=None, direct=set())
            matches.append(PersonalMatch(term, detection))
    # Longer explicit phrases own their whole span; request order breaks identical-length ties.
    occupied = set()
    selected = []
    for matched in sorted(matches, key=lambda m: (-(m.detection.end - m.detection.start), m.detection.start)):
        span = set(range(matched.detection.start, matched.detection.end))
        if not span & occupied:
            selected.append(matched)
            occupied.update(span)
    return sorted(selected, key=lambda m: m.detection.start)
