"""R75's dollar word is countable currency, independent of loose money or sterling."""

import pytest

from aussiefy import Translator, lookup
from aussiefy.explore import get_entry


@pytest.mark.parametrize('query', ['dollar', 'dollars', 'a dollar', 'buck', 'bucks', 'five dollars', 'five bucks'])
def test_dollar_has_a_real_dictionary_word(dictionary, query):
    result = lookup(query, translator=Translator(dictionary, lookup_embedder=None), level=1, vulgarity=0)
    assert result['outcome'] == 'matched'
    assert any(word['id'] == 'buck' for word in result['results'])
    assert not any(word['id'] == 'quid' for word in result['results'])
    assert 'DOLLAR' not in dictionary.wordless_meanings


@pytest.mark.parametrize('source,expected', [
    ('It cost a dollar.', 'It cost a buck.'),
    ('It cost one dollar.', 'It cost one buck.'),
    ('It cost five dollars.', 'It cost five bucks.'),
    ('It cost 12.50 dollars.', 'It cost 12.50 bucks.'),
    ('It cost 35 dollars.', 'It cost 35 bucks.'),
])
def test_dollar_word_preserves_count_and_currency(dictionary, source, expected):
    tr = Translator(dictionary, lookup_embedder=None)
    result = tr.translate(source, level=1, vulgarity=0, embellishment=0, embedder='none', english='none',
                          document_config={'profile': {'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    assert result.text == expected
    assert any(r.chosen and r.chosen.entry.id == 'buck' for r in result.records)


@pytest.mark.parametrize('source', ['The buck stops here.', 'They passed the buck.',
                                   'They bucked the trend.', 'She will buck up.'])
def test_responsibility_and_verb_senses_are_not_dollars(dictionary, source):
    result = Translator(dictionary, lookup_embedder=None).translate(source, level=5, vulgarity=0,
              embellishment=0, embedder='none', english='none')
    assert not any(c.entry.id == 'buck' for r in result.records for c in r.eligible)


def test_dollar_word_retains_actual_testimony_alongside_documented_dollar_sense(dictionary):
    card = get_entry('buck', translator=Translator(dictionary, lookup_embedder=None))['entry']
    assert dictionary.entries['buck'].plural == 'bucks' and card['concepts'] == ['DOLLAR']
    assert card['evidence'] == 'attested'
    assert any(s['publisher'] == 'American Heritage Dictionary' and 'meaning' in s['supports']
               for s in card['sources'])
    assert card['attestation']['people'] == 1
    assert any(s['kind'] == 'testimony' and s['publisher'] == 'Rob (project owner)'
               for s in card['sources'])


@pytest.mark.parametrize('query,concept', [('two biscuits', 'BISCUIT'), ('5 dollars', 'DOLLAR'),
                                         ('my dollars', 'DOLLAR')])
def test_nominal_determiners_and_counts_scope_the_recognised_meaning(dictionary, query, concept):
    result = lookup(query, translator=Translator(dictionary, lookup_embedder=None), vulgarity=0)
    assert result['outcome'] == 'matched'
    assert result['results'] and all(concept in word['concepts'] for word in result['results'])


def test_a_count_does_not_hide_an_independent_meaning(dictionary):
    result = lookup('two biscuits and hungry', translator=Translator(dictionary, lookup_embedder=None))
    assert result['outcome'] == 'matched'
    assert {'BISCUIT', 'HUNGRY'} <= {cid for word in result['results'] for cid in word['concepts']}
    assert all(set(word['concepts']) & {'BISCUIT', 'HUNGRY'} for word in result['results'])


def test_a_count_cannot_adopt_uninterpreted_prefix_words(dictionary):
    from aussiefy.detect import read_meanings
    from aussiefy.lookup import _scoped_query
    from aussiefy.pos import tag
    from aussiefy.text import tokenize

    tokens = tokenize('two stray words biscuits')
    tags = tag([t.text for t in tokens])
    readings = read_meanings(tokens, dictionary, tags=tags, fragment=True).detections
    assert _scoped_query(tokens, readings, tags) is None


QUALIFIED_CURRENCIES = [
    '50 US dollars', '50 Australian dollars', '50 Canadian dollars',
    '50 New Zealand dollars', '50 East Caribbean dollars', '50 Hong Kong dollars',
    '50 Trinidad and Tobago dollars', '50 U.S. dollars', '50 U.S.A. dollars',
    '50 australian dollars', 'one Australian dollar', 'fifty British pounds',
    '50 UK pounds', '50 Kenyan shillings',
]
FORCE_WORDS = {'level': 5, 'vulgarity': 0, 'embellishment': 0, 'english': 'none', 'embedder': 'none',
               'document_config': {'profile': {'phonetic': 0,
                    'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}}


@pytest.mark.parametrize('amount', QUALIFIED_CURRENCIES)
def test_qualified_currency_names_are_preserved_across_translation_and_changes(dictionary, amount):
    from aussiefy import plan, translate_changes

    tr = Translator(dictionary, lookup_embedder=None)
    source = f'It cost {amount}.'
    result = tr.translate(source, **FORCE_WORDS)
    assert result.text == source
    assert not any(candidate.entry.id in {'buck', 'quid', 'a-deener'}
                   for record in result.records for candidate in record.eligible)
    changes = translate_changes(source, translator=tr, **FORCE_WORDS)
    assert changes.text == source and changes.to_dict()['changes'] == []
    prepared = plan(source, translator=tr, **{k: v for k, v in FORCE_WORDS.items() if k != 'embedder'})
    assert prepared['draft'] == source


@pytest.mark.parametrize('amount', QUALIFIED_CURRENCIES)
def test_qualified_currency_lookup_explains_preservation(dictionary, amount):
    result = lookup(amount, translator=Translator(dictionary, lookup_embedder=None), vulgarity=0)
    assert result['outcome'] == 'left_as_written' and not result['results']
    assert result['protections']
    assert all(p['reason'] == 'A qualified currency name stays as written.' for p in result['protections'])
    for protection in result['protections']:
        assert amount[slice(*protection['span'])] == protection['original']


@pytest.mark.parametrize('source,expected', [
    ('Give us dollars.', 'Give us bucks.'),
    ('Give them dollars.', 'Give them bucks.'),
    ('It cost ten dollars.', 'It cost ten bucks.'),
    ('It cost fifty dollars.', 'It cost fifty bucks.'),
    ('It cost FIFTY dollars.', 'It cost FIFTY bucks.'),
    ('It cost twenty-one dollars.', 'It cost twenty-one bucks.'),
    ('It cost a hundred dollars.', 'It cost a hundred bucks.'),
    ('It cost 50 dollars.', 'It cost 50 bucks.'),
    ('They are my dollars.', 'They are my bucks.'),
])
def test_counts_determiners_and_recipient_pronouns_do_not_qualify_currency(dictionary, source, expected):
    result = Translator(dictionary, lookup_embedder=None).translate(source, **FORCE_WORDS)
    assert result.text == expected
    assert any(r.chosen and r.chosen.entry.id == 'buck' for r in result.records)


def test_one_qualified_currency_does_not_protect_a_nearby_bare_amount(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    source = 'I paid 50 Australian dollars and she paid 20 dollars.'
    result = tr.translate(source, **FORCE_WORDS)
    assert result.text == 'I paid 50 Australian dollars and she paid 20 bucks.'


def test_currency_protection_is_dictionary_authored_and_holds_whole_readings(dictionary):
    from dataclasses import replace
    from aussiefy.fences import Fence
    from aussiefy.matcher import PatternIndex, compile_pattern

    fence = Fence('{modifier} credit|credits', 'np', 'grammar', 'Keep the qualified unit.',
                  True, frozenset(), exclusive=True)
    patterns = [compile_pattern('credit', 'np', ('DOLLAR',), 3),
                compile_pattern('Galactic credit', 'np', ('DOLLAR',), 3), fence.pattern]
    custom = replace(dictionary, index=PatternIndex(patterns), fences=(fence,))
    tr = Translator(custom, lookup_embedder=None)
    assert tr.translate('It cost five credits.', **FORCE_WORDS).text == 'It cost five bucks.'
    assert tr.translate('It cost five Galactic credits.', **FORCE_WORDS).text == 'It cost five Galactic credits.'
    assert lookup('Galactic credit', translator=tr)['outcome'] == 'left_as_written'


@pytest.mark.parametrize('exclusive', [None, 1, 'true'])
def test_exclusive_fence_flag_is_strict(exclusive):
    from aussiefy.errors import SchemaError
    from aussiefy.fences import parse_fences

    with pytest.raises(SchemaError, match='exclusive must be a boolean'):
        parse_fences([{'phrase': 'named unit', 'frame': 'np', 'kind': 'grammar', 'reason': 'Keep it.',
                       'scope': {'meanings': True, 'dialect': [], 'not_in': []}, 'exclusive': exclusive}])


def test_qualified_currency_explanations_do_not_share_country_specific_readings(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    british = lookup('British pounds', translator=tr, vulgarity=0)
    australian = lookup('Australian pounds', translator=tr, vulgarity=0)
    assert british['outcome'] == australian['outcome'] == 'left_as_written'
    assert 'STERLING_MONEY' in {item.get('concept') for p in british['protections'] for item in p['ruled_out']}
    assert 'STERLING_MONEY' not in {item.get('concept') for p in australian['protections'] for item in p['ruled_out']}


@pytest.mark.parametrize('count', ['ten', 'thirteen', 'nineteen', 'twenty', 'twenty-one', 'a hundred'])
@pytest.mark.parametrize('word,concept', [('bucks', 'DOLLAR'), ('biscuits', 'BISCUIT')])
def test_written_counts_scope_nominal_lookup_without_a_currency_bypass(dictionary, count, word, concept):
    result = lookup(f'{count} {word}', translator=Translator(dictionary, lookup_embedder=None), vulgarity=0)
    assert result['outcome'] == 'matched' and result['results']
    assert all(concept in card['concepts'] for card in result['results'])


def test_dollars_and_cents_is_a_whole_expression_with_nearby_bare_amount_controls(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    source = 'We discussed the dollars and cents, then paid fifty dollars.'
    assert tr.translate(source, **FORCE_WORDS).text == 'We discussed the dollars and cents, then paid fifty bucks.'
    result = lookup('dollars and cents', translator=tr, vulgarity=0)
    assert result['outcome'] == 'left_as_written' and result['protections']
    assert tr.translate('We counted one dollar and fifty cents.', **FORCE_WORDS).text == 'We counted one buck and fifty cents.'


@pytest.mark.parametrize('english', ['us', 'uk', 'none'])
def test_qualified_currency_protection_survives_the_dialect_stage(dictionary, english):
    source = 'It cost 50 US dollars.'
    tr = Translator(dictionary, lookup_embedder=None)
    assert tr.translate(source, **(FORCE_WORDS | {'english': english})).text == source
