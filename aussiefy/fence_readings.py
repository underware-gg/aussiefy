"""Counterfactual evidence for phrase protections, independent of explanation copy."""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import islice, product
from typing import TYPE_CHECKING

from .dialect import DialectTable
from .matcher import PatternIndex
from .schema import HOLDING_CONCEPT
from .text import tokenize

if TYPE_CHECKING:
    from .fences import Fence
    from .model import Dictionary


@dataclass(frozen=True)
class RuledOutMeaning:
    concept: str
    entries: tuple[str, ...]


@dataclass(frozen=True)
class RuledOutDialect:
    english: str
    before: str
    after: str


@dataclass(frozen=True)
class FenceTrial:
    text: str
    effect: str


@dataclass(frozen=True)
class FenceVariant:
    signature: tuple[str, ...]
    meanings: tuple[RuledOutMeaning, ...]
    dialect: tuple[RuledOutDialect, ...]


@dataclass(frozen=True)
class FenceReadings:
    fence: Fence
    meanings: tuple[RuledOutMeaning, ...]
    dialect: tuple[RuledOutDialect, ...]
    trials: tuple[FenceTrial, ...]
    generated_examples_truncated: bool = False
    variants: tuple[FenceVariant, ...] = ()

    @property
    def needs_audit(self) -> bool:
        return not self.meanings and not self.dialect

    def for_span(self, text: str, span: list[int]) -> FenceReadings:
        tokens = tokenize(text)
        for match in PatternIndex([self.fence.pattern]).find(tokens):
            if [tokens[match.start].start, tokens[match.end - 1].end] != span:
                continue
            signature = _variant_signature(match, tokens)
            for variant in self.variants:
                if variant.signature == signature:
                    return replace(self, meanings=variant.meanings, dialect=variant.dialect)
        return replace(self, meanings=(), dialect=())


def _variant_signature(match, tokens):
    start, end = match.context or (match.start, match.end)
    if match.object_start is not None:
        # Match marks only the object's first token. Keep its remaining context
        # conservatively rather than treating all "the ..." objects as one witness.
        end = len(tokens)
        while end > match.end and tokens[end - 1].is_punct:
            end -= 1
    slots = match.pattern.slots
    # A lexical modifier can change the reading (British pounds versus Australian pounds).
    captures = [(name, token.start, token.end) for name, token in match.captures.items()
                if name in slots and name != 'modifier']
    out = []
    for token in tokens[start:end]:
        slot = next(((name, first) for name, first, last in captures if first <= token.start < last), None)
        if slot is None:
            out.append(token.norm)
        elif token.start == slot[1]:
            out.append('{' + slot[0] + '}')
    return tuple(out)


class _WithoutFences:
    def __init__(self, index, excluded):
        self.index, self.excluded = index, excluded

    def find(self, tokens):
        return [m for m in self.index.find(tokens) if m.pattern.fence not in self.excluded]


# Grammar scaffolds, never source-reading claims. Every generated witness must still
# match the protection, and the normal reader and candidate checks assess its effect.
_SLOTS = {'subj': 'they', 'be': 'are', 'have': 'have', 'do': 'do', 'poss': 'their',
          'obj': 'them', 'objposs': 'their', 'np': 'the task', 'modifier': 'Australian', 'ing': 'working', 'will': 'will'}
_GENERATED_LIMIT = 128


def _examples(fence):
    choices = []
    for element in fence.pattern.elements:
        if element.kind == 'not':
            continue
        if element.kind == 'behind':
            # Assertions behind an earlier boundary need an authored sentence.
            return fence.examples, False
        values = ([_SLOTS[element.slot]] if element.slot else
                  sorted(element.values, key=lambda v: (len(v), v)))
        choices.append(([''] if element.optional else []) + values)
    generated = list(islice(product(*choices), _GENERATED_LIMIT + 1))
    texts = []
    for parts in generated[:_GENERATED_LIMIT]:
        phrase = ' '.join(p for p in parts if p).replace(" 's", "'s").replace(" n't", "n't")
        texts.append(phrase)
        if fence.frame == 'np':
            texts.append(f'They discussed {phrase}.')
        elif fence.frame == 'vp':
            texts.append(f'They {phrase}.')
        elif fence.frame in {'adj', 'predicate_adj'}:
            texts.append(f'They are {phrase}.')
    return tuple(dict.fromkeys((*fence.examples, *texts))), len(generated) > _GENERATED_LIMIT


def _facts(result, span):
    meanings, words = set(), set()
    for record in result.records:
        if record.span[0] >= span[1] or record.span[1] <= span[0]:
            continue
        for cid in set(record.det.concepts) - {HOLDING_CONCEPT}:
            key = (*record.span, cid)
            meanings.add(key)
            words.update((*key, candidate.entry.id) for candidate in record.eligible
                         if cid in candidate.entry.concept)
    return meanings, words


def _difference(before, after):
    meanings = {key[-1] for key in after[0] - before[0]}
    words = {(key[-2], key[-1]) for key in after[1] - before[1]}
    return meanings | {cid for cid, _ in words}, words


class _MeaningProbe:
    def __init__(self, dictionary):
        from .engine import Translator

        self.dictionary = dictionary
        self.translator = Translator(dictionary, lookup_embedder=None)
        self.fence_index = PatternIndex([f.pattern for f in dictionary.fences if f.meanings])
        self.settings = dict(level=5, vulgarity=3, seed=0, registers=['current', 'dated', 'archaic'],
            embellishment=0, embedder='none', english='none', document_type='custom',
            document_config={'themes': dict.fromkeys(sorted(set().union(*dictionary.theme_defaults.values())), True),
                             'profile': {'phonetic': 0, 'stack': 0,
                                         'substitution': dict.fromkeys(('lexical', 'phrase', 'idiom'), 1)}})

    def without(self, text, fences):
        from .engine import Translator

        dictionary = replace(self.dictionary, index=_WithoutFences(self.dictionary.index, fences))
        return Translator(dictionary, lookup_embedder=None).translate(text, **self.settings)

    def compare(self, text, tokens, hit):
        span = tokens[hit.start].start, tokens[hit.end - 1].end
        before = _facts(self.translator.translate(text, **self.settings), span)
        after = _facts(self.without(text, {hit.pattern.fence}), span)
        meanings, words = _difference(before, after)
        if meanings:
            return meanings, words, 'direct'
        overlaps = {m.pattern.fence for m in self.fence_index.find(tokens)
                    if m.start < hit.end and hit.start < m.end}
        meanings, words = _difference(before, _facts(self.without(text, overlaps), span))
        if meanings:
            return meanings, words, 'overlap'
        raw = any(m.pattern.concepts and m.start < hit.end and hit.start < m.end
                  for m in self.dictionary.index.find(tokens))
        return set(), set(), 'other_checks' if raw else 'no_source_pattern'


def _dialect_readings(table, unfenced, fence, text, tokens, hit):
    out = set()
    for english in sorted(fence.dialect):
        source = None if english == 'unknown' else english
        if not fence.applies(source, 'general'):
            continue
        existing = {(m.start, m.end, m.text) for m in table.find(tokens, source, 'general')}
        for swap in unfenced.find(tokens, source, 'general'):
            if (swap.start < hit.end and hit.start < swap.end
                    and (swap.start, swap.end, swap.text) not in existing):
                before = text[tokens[swap.start].start:tokens[swap.end - 1].end]
                out.add(RuledOutDialect(swap.swap.english, before, swap.text))
    return out


def _derive_fence(fence, probe, table, unfenced):
    index = PatternIndex([fence.pattern])
    meanings, words, dialect, trials = set(), set(), set(), []
    variants = {}
    examples, truncated = _examples(fence)
    for text in examples:
        tokens = tokenize(text)
        for hit in index.find(tokens):
            new_meanings, new_words, effect = (probe.compare(text, tokens, hit) if fence.meanings
                                               else (set(), set(), 'no_dialect_swap'))
            blocked_dialect = _dialect_readings(table, unfenced, fence, text, tokens, hit)
            meanings.update(new_meanings)
            words.update(new_words)
            dialect.update(blocked_dialect)
            signature = _variant_signature(hit, tokens)
            variant_meanings, variant_words, variant_dialect = variants.setdefault(signature, (set(), set(), set()))
            variant_meanings.update(new_meanings)
            variant_words.update(new_words)
            variant_dialect.update(blocked_dialect)
            if blocked_dialect:
                effect = f'{effect}+dialect' if fence.meanings else 'dialect'
            trials.append(FenceTrial(text, effect))
    return FenceReadings(fence, _meaning_records(meanings, words), _dialect_records(dialect),
        tuple(dict.fromkeys(trials)), truncated,
        tuple(FenceVariant(signature, _meaning_records(cids, entries), _dialect_records(swaps))
              for signature, (cids, entries, swaps) in sorted(variants.items())))


def _meaning_records(meanings, words):
    return tuple(RuledOutMeaning(cid, tuple(sorted(eid for meaning, eid in words if meaning == cid)))
                 for cid in sorted(meanings))


def _dialect_records(dialect):
    return tuple(sorted(dialect, key=lambda row: (row.english, row.before, row.after)))


class FenceReadingIndex:
    """Bounded, dictionary-local evidence builds, shared by lookup and the batch audit."""

    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary
        self._fences = frozenset(dictionary.fences)
        self._probe = _MeaningProbe(dictionary)
        self._unfenced = DialectTable(list(dictionary.dialect.swaps), dictionary.dialect.lint_only)
        self._built: dict[Fence, FenceReadings] = {}

    def __getitem__(self, fence: Fence) -> FenceReadings:
        if fence not in self._fences:
            raise KeyError(fence)
        if fence not in self._built:
            self._built[fence] = _derive_fence(fence, self._probe, self.dictionary.dialect, self._unfenced)
        return self._built[fence]


def derive_fence_readings(dictionary: Dictionary) -> tuple[FenceReadings, ...]:
    """Build the full evidence/audit using the same lazy index as reader-facing lookup.

    Missing evidence is diagnostic (R71), never grounds to remove a protection.
    """
    return tuple(dictionary.fence_readings[fence] for fence in dictionary.fences)
