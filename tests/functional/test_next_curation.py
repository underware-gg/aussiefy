"""Applied next-round curation preserves sense, grammar, permissions and permanent IDs."""
from dataclasses import replace

import pytest

from aussiefy import Translator, get_entry, lookup
from aussiefy.detect import read_meanings
from aussiefy.text import tokenize

OPTIONS = dict(level=5, vulgarity=1, embellishment=0, english='none', embedder=None,
    document_config={'garnish': [], 'profile': {'phonetic': 0,
        'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
IDS = {'have-a-go', 'booze', 'a-cold-one', 'have-a-cry', 'buck'}


@pytest.fixture
def curated(dictionary):
    return Translator(replace(dictionary, entries={k: e for k, e in dictionary.entries.items() if k in IDS}),
                      lookup_embedder=None)


@pytest.mark.parametrize('source,expected', [
    ('I will try.', 'I will have a go.'),
    ('She made an attempt.', 'She had a go.'),
    ('Bring some liquor.', 'Bring some booze.'),
    ('She ordered a cold beer.', 'She ordered a cold one.'),
    ('She ordered two cold beers.', 'She ordered two cold ones.'),
    ('She wept.', 'She had a cry.'),
    ('She has wept.', 'She has had a cry.'),
    ('She did not weep.', 'She did not have a cry.'),
    ('It costs 50 dollars.', 'It costs 50 bucks.'),
])
def test_applied_forms_keep_number_auxiliaries_and_arguments(curated, source, expected):
    for seed in (0, 3):
        assert curated.translate(source, seed=seed, **OPTIONS).text == expected


@pytest.mark.parametrize('source', [
    'I will have a go at him.', 'I will have a go at swimming.',
    'She chose a cold one.', 'The alcohol evaporated.', 'Bring two alcoholic drinks.',
    'She ordered a warm beer.', 'She ordered a cold beer bottle.', 'Bring some cold beer.',
    'She cried for help.', 'They cried wolf.', 'The fox cried.',
    'It costs 50 US dollars.', 'It costs 50 Australian dollars.', 'It costs 50 Canadian dollars.',
])
def test_ambiguous_or_wrong_senses_keep_the_source(curated, source):
    assert curated.translate(source, seed=0, **OPTIONS).text == source


@pytest.mark.parametrize('eid', sorted(IDS - {'buck'}))
def test_entries_are_shared_english_and_have_independent_scoped_sources(dictionary, eid):
    e = dictionary.entries[eid]
    assert e.reads_as == 'general' and e.incoherence == 1 and e.vulgarity == 0
    assert e.searched and e.sources and e.testimony is None
    assert dictionary.entry_ids[eid] == eid
    assert get_entry(eid, translator=Translator(dictionary, lookup_embedder=None))['entry']['id'] == eid


@pytest.mark.parametrize('source', ['Bring some liquor.', 'She ordered a cold beer.'])
def test_drinking_permission_is_separate_from_word_vulgarity(curated, source):
    assert curated.translate(source, seed=0, **(OPTIONS | {'vulgarity': 0, 'themes': {'drinking': False}})).text == source


def test_exact_crying_prevents_near_even_when_the_exact_word_is_blocked(dictionary):
    assert 'CRY' not in dictionary.wordless_meanings
    tr = Translator(dictionary, lookup_embedder=None)
    # A higher-grade exact entry still makes the meaning non-wordless.
    blocked = replace(dictionary, entries={k: replace(e, incoherence=5) if 'CRY' in e.concept else e
                                           for k, e in dictionary.entries.items()})
    for runner in (tr, Translator(blocked, lookup_embedder=None)):
        result = runner.translate('She wept.', seed=0, **(OPTIONS | {'level': 1, 'embellishment': 2}))
        assert not any(r.chosen and r.chosen.near for r in result.records)
    found = lookup('cry', translator=tr)
    assert {e['id'] for e in found['results']} == {'have-a-cry'}


@pytest.mark.parametrize('source', ['I will have a go at him.', 'She chose a cold one.'])
def test_unresolved_guards_own_the_whole_ambiguous_unit(dictionary, source):
    readings = read_meanings(tokenize(source), dictionary).detections
    assert any('UNRESOLVED_SENSE' in r.concepts for r in readings)
    assert not any({'TRY', 'COLD_BEER_SERVING'} & set(r.concepts) for r in readings)
