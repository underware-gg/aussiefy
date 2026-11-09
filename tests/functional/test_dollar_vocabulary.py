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
    ('It cost 12.50 US dollars.', 'It cost 12.50 US bucks.'),
    ('It cost 35 Australian dollars.', 'It cost 35 Australian bucks.'),
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


def test_dollar_word_retains_the_actual_testimony_without_invented_attestation(dictionary):
    card = get_entry('buck', translator=Translator(dictionary, lookup_embedder=None))['entry']
    assert dictionary.entries['buck'].plural == 'bucks' and card['concepts'] == ['DOLLAR']
    assert card['evidence'] == 'unverified'
    assert card['attestation']['people'] == 1
    assert card['sources'][0]['kind'] == 'testimony'
    assert card['sources'][0]['publisher'] == 'Rob (project owner)'


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
