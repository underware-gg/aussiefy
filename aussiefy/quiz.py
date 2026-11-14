"""Seeded meaning questions: dictionary evidence excludes answers; similarity only ranks distractors."""

from dataclasses import dataclass
import math
import re

from .policy import roll
from .schema import Entry, PLACEHOLDER_RE
from .terms import fold, form_key


STOP_WORDS = frozenset('''about also been being from into onto over rather someone something that their
them there these they this those than very where which with your'''.split())
WORD_CLASSES = {
    'imperative': 'exclamation', 'interjection': 'exclamation', 'np': 'noun',
    'adj': 'adjective', 'predicate_adj': 'adjective', 'vp': 'verb', 'clause': 'verb', 'adv': 'adverb', 'tag': 'tag',
}


def option_text(gloss):
    """The first gloss clause, without parenthetical asides or quoted examples."""
    out, depth = [], 0
    for character in gloss:
        if character in '([':
            depth += 1
        elif character in ')]':
            depth = max(0, depth - 1)
        elif not depth:
            out.append(character)
    text = re.sub(r'["“][^"”]*["”]', '', ''.join(out))
    text = re.sub(r"(?<!\w)['‘].*?['’](?!\w)", '', text)
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.split(r';|[.:]\s', text, maxsplit=1)[0]
    text = ' '.join(text.split()).strip(' ,;:')
    return text + ('' if not text or text.endswith(('.', '?', '!')) else '.')


def content_words(text):
    return frozenset(re.findall(r'[^\W\d_]{4,}', PLACEHOLDER_RE.sub('', text.lower()))) - STOP_WORDS


@dataclass(frozen=True)
class QuizTerm:
    entry: Entry
    text: str
    form_words: frozenset
    words: frozenset
    meaning: str
    person: bool
    form: str


def askable_pool(entries, concepts):
    pool = []
    for entry in sorted(entries, key=lambda item: item.id):
        if entry.type != 'idiom':
            continue
        text = option_text(entry.gloss)
        words = content_words(text)
        forms = frozenset().union(*(content_words(form) for form in entry.all_forms))
        if (not any(c.isalnum() for c in text) or words & forms
                or any(form_key(text) == form_key(form) for form in entry.all_forms)):
            continue
        meanings = [concepts[cid] for cid in entry.concept]
        meaning = ' '.join([text, *(word for c in meanings
            for word in (c.description, c.plain, *c.search_words) if word)])
        pool.append(QuizTerm(entry, text, forms, words, meaning, any(c.person for c in meanings), form_key(entry.form)))
    return tuple(pool)


def candidates(question, pool, excluded=()):
    def eligible(other):
        return (other.entry.id != question.entry.id and other.entry.id not in excluded
                and other.text != question.text
                and other.form != question.form
                and not set(other.entry.concept).intersection(question.entry.concept)
                and not other.form_words & question.form_words and not other.words & question.words)
    available = [other for other in pool if eligible(other)]
    same_frame = [other for other in available if other.entry.frame == question.entry.frame]
    if len(same_frame) >= 12:
        return same_frame
    return [other for other in available
            if WORD_CLASSES[other.entry.frame] == WORD_CLASSES[question.entry.frame]]


def bands(ranked, person):
    n = len(ranked)
    if not n:
        return (), (), ()
    close = [row for row in ranked if row.person == person][:5] or ranked[:5]
    middle = ranked[int(n * .4):max(int(n * .4) + 1, math.ceil(n * .6))]
    bottom = ranked[int(n * .85):]
    far = [row for row in bottom if row.person != person] + [row for row in bottom if row.person == person]
    return close, middle, far


@dataclass(frozen=True)
class Question:
    entry: Entry
    options: tuple[dict, ...]
    answer: int


def question_for(question, pool, embedder, offers, seed):
    possible = candidates(question, pool)
    if len(possible) < 3:
        return None
    offered = offers(question.text)
    possible = candidates(question, pool, offered)
    if len(possible) < 3:
        return None
    ranked = sorted(possible, key=lambda row: (-embedder.similarity(question.meaning, row.meaning), row.entry.id))
    chosen, texts, rejected = [], {fold(question.text)}, set()
    for name, preferred in zip(('close', 'middle', 'far'), bands(ranked, question.person)):
        order = sorted(preferred, key=lambda row: ((row.person == question.person) if name == 'far' else False,
                        roll(seed, 'meaning-quiz', question.entry.id, name, row.entry.id), row.entry.id))
        # A thin band or rejected true reading must not force an unsafe option.
        preferred_ids = {row.entry.id for row in preferred}
        remaining = [row for row in ranked if row.entry.id not in preferred_ids]
        for row in [*order, *remaining]:
            if row.entry.id in rejected or fold(row.text) in texts:
                continue
            if question.entry.id in offers(row.text):
                rejected.add(row.entry.id)
                continue
            chosen.append(row)
            texts.add(fold(row.text))
            break
        else:
            return None
    options = sorted([question, *chosen],
        key=lambda row: (roll(seed, 'meaning-quiz', question.entry.id, 'option', row.entry.id), row.entry.id))
    return Question(question.entry, tuple({'text': row.text, 'entry_id': row.entry.id} for row in options),
                    next(i for i, row in enumerate(options) if row.entry.id == question.entry.id))


def select_question(pool, embedder, offers, seed):
    for question in sorted(pool, key=lambda row: (roll(seed, 'meaning-quiz', row.entry.id, 'question'), row.entry.id)):
        if result := question_for(question, pool, embedder, offers, seed):
            return result
    return None
