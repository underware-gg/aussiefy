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


def prepare(raw, dictionary) -> PersonalTerms:
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
