"""Gate 4 additions preserve meanings, grammar, dials and source qualifications."""
from dataclasses import replace

import pytest

from aussiefy import Translator
from aussiefy.masks import masks

PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}
OPTIONS = dict(level=5, vulgarity=2, embellishment=0, english='none',
               document_config={'profile': PROFILE})


def only(dictionary, eid):
    return Translator(replace(dictionary, entries={eid: dictionary.entries[eid]}), lookup_embedder=None)


@pytest.mark.parametrize('eid,source,expected', [
    ('flat-strap-busy', 'I am swamped.', 'I am flat strap.'),
    ('flat-strap-busy', 'She was run off her feet.', 'She was flat strap.'),
    ('flat-strap-fast', 'She ran at top speed.', 'She ran flat strap.'),
    ('flat-strap-fast', 'He drove very quickly.', 'He drove flat strap.'),
    ('coldie', 'We had a few beers.', 'We had a few coldies.'),
    ('coldie', 'We had two warm beers.', 'We had two warm coldies.'),
    ('coldie', 'I drank a beer.', 'I drank a coldie.'),
    ('coldie', 'I drank one beer.', 'I drank one coldie.'),
    ('coldie', 'I drank another warm beer.', 'I drank another warm coldie.'),
    ('legendary-excellent', 'It was excellent.', 'It was legendary.'),
    ('legendary-excellent', 'An excellent show.', 'A legendary show.'),
    ('dickheads-address', 'Hello everyone.', 'Hello dickheads.'),
])
def test_new_choices_render_in_their_actual_slot(dictionary, eid, source, expected):
    # Keep other vocabulary out so the fixture proves the new candidate itself can render.
    tr = only(dictionary, eid)
    for seed in range(4):
        result = tr.translate(source, seed=seed, **OPTIONS)
        assert result.text.replace('flat-strap', 'flat strap') == expected
        assert any(r.chosen and r.chosen.entry.id == eid for r in result.records)


@pytest.mark.parametrize('source,forbidden', [
    ('The flat strap held the load.', {'flat-strap-busy', 'flat-strap-fast'}),
    ('The strap lay flat.', {'flat-strap-busy', 'flat-strap-fast'}),
    ('Everyone is ready.', {'dickheads-address'}),
    ('I invited everyone.', {'dickheads-address'}),
    ('The legendary monster appeared.', {'legendary-excellent'}),
    ('A legendary ruler is famous.', {'legendary-excellent'}),
])
def test_additions_do_not_establish_a_different_sense(dictionary, source, forbidden):
    result = Translator(dictionary, lookup_embedder=None).translate(source, **OPTIONS)
    assert not forbidden & {c.entry.id for r in result.records for c in r.eligible}


@pytest.mark.parametrize('eid,source,level,cap,expected', [
    ('flat-strap-busy', 'I am swamped.', 1, 0, False),
    ('flat-strap-busy', 'I am swamped.', 2, 0, True),
    ('flat-strap-fast', 'She ran at top speed.', 2, 0, False),
    ('flat-strap-fast', 'She ran at top speed.', 3, 0, True),
    ('legendary-excellent', 'It was excellent.', 1, 0, True),
    ('dickheads-address', 'Hello everyone.', 2, 1, False),
    ('dickheads-address', 'Hello everyone.', 2, 2, True),
])
def test_additions_obey_their_dials(dictionary, eid, source, level, cap, expected):
    result = only(dictionary, eid).translate(source, **(OPTIONS | {'level': level, 'vulgarity': cap}))
    assert any(r.chosen and r.chosen.entry.id == eid for r in result.records) == expected


def test_friendly_address_still_obeys_the_genres_person_swear_policy(dictionary):
    result = only(dictionary, 'dickheads-address').translate('Hello everyone.',
        **(OPTIONS | {'document_type': 'custom'}))
    assert result.text == 'Hello everyone.'
    assert not any(r.chosen for r in result.records)


def test_friendly_plural_mask_keeps_the_plural_ending(dictionary):
    entry = dictionary.entries['dickheads-address']
    assert masks('dickheads', dictionary.swears, dictionary.swear_compounds,
                 {word: entry.vulgarity for word in entry.mask}) == [
        {'span': [0, 9], 'ending_start': 8, 'vulgarity': 2}]


def test_approved_recommendations_do_not_fabricate_testimony_or_change_spellings(dictionary):
    for eid in ('coldie', 'dickheads-address', 'legendary-excellent'):
        entry = dictionary.entries[eid]
        assert 'Approved by Rob under R80' in entry.notes and 'PROVISIONAL' not in entry.notes
        assert entry.testimony is None
        assert not any(s.kind == 'testimony' for s in entry.sources)
    assert dictionary.entries['coldie'].form == 'a coldie'
    assert dictionary.entries['legendary-excellent'].reads_as == 'general'
    assert dictionary.entries['cunts-address'].vulgarity == 3


@pytest.mark.parametrize('source', ['I drank beer.', 'I drank some beer.', 'I drank much beer.',
    'I drank a pint of beer.', 'I drank either beer or wine.', 'The beer can was empty.'])
def test_coldie_does_not_invent_a_serving_or_modify_a_container(dictionary, source):
    result = only(dictionary, 'coldie').translate(source, **OPTIONS)
    assert result.text == source
    assert not any(r.chosen for r in result.records)
