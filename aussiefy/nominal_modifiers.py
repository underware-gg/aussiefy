"""Bounded lexical noun modifiers for source protections; quantities alone do not qualify a head."""

from . import morph, pos

# Written cardinal counts can be tagged as nouns or adjectives in short queries.
CARDINALS = frozenset("""zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen
fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred
hundreds thousand thousands million millions billion billions trillion trillions""".split())
COUNTS = CARDINALS | {'dozen', 'dozens', 'couple', 'score', 'few', 'several', 'many', 'more', 'most',
                     'less', 'least', 'fewer', 'enough'}
MODIFIERS = pos.NOUNS | pos.NAMES | {'JJ', 'JJR', 'JJS'}
DETERMINERS = {'DT', 'PDT', 'PRP$', 'CD'}


def is_cardinal(word):
    return all(part in CARDINALS for part in word.split('-'))


def cardinal_at(tokens, index):
    """A cardinal word or its internal hyphen, using the canonical tokenisation."""
    return is_cardinal(tokens[index].norm) or (
        tokens[index].text == '-' and 0 < index < len(tokens) - 1
        and is_cardinal(tokens[index - 1].norm) and is_cardinal(tokens[index + 1].norm))


def modifier_lengths(tokens, start, tags=None):
    """Lengths of contiguous nominal modifiers, including names and dotted initials.

    Read original case: US may name a modifier even when tagged as a pronoun or count; us cannot.
    A lexical qualifier is required, so articles, possessives and counts alone leave a bare head.
    Protect uncertain named/lexically modified heads conservatively, without guessing a geography.
    """
    tags = tags if tags is not None else pos.tag([token.text for token in tokens])
    lexical = False
    for i in range(start, min(len(tokens), start + 12)):
        token = tokens[i]
        acronym = (token.text.isalpha() and token.text.isupper() and len(token.text) > 1
                   and token.norm not in COUNTS | morph.POSSESSIVES | {'a', 'an', 'the'})
        if token.text == '.' and i > start and tokens[i - 1].text.isupper() \
                and len(tokens[i - 1].text) == 1 and tokens[i - 1].end == token.start:
            if lexical:
                yield i - start + 1
            continue
        if token.is_punct:
            return
        if token.norm in {'and', 'of'} and lexical:
            continue
        if token.norm in morph.OBJECT_PRONOUNS | morph.PRONOUNS.keys() and not acronym:
            return
        if tags[i] not in MODIFIERS | DETERMINERS and not acronym:
            return
        lexical |= acronym or tags[i] in MODIFIERS and token.norm not in COUNTS and not is_cardinal(token.norm)
        if (lexical and tags[i] in MODIFIERS) or acronym:
            yield i - start + 1
