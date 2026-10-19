"""Reviewed lexical distinctions preserve quantity, reference, purpose, polarity and grammatical roles."""

from pathlib import Path

import pytest
import yaml

from aussiefy import Translator


@pytest.fixture
def reviewed(dictionary):
    return Translator(dictionary, lookup_embedder=None)


def render(translator, text, *, document_config=None, **kwargs):
    return translator.translate(text, level=5, vulgarity=3, registers=['current', 'dated', 'archaic'],
        unlock=['all'], embedder='none', embellishment=0,
        document_config={'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}},
                         **(document_config or {})}, **kwargs)


def eligible(result):
    return {c.entry.id for r in result.records for c in r.eligible}


@pytest.mark.parametrize('source,wanted', [
    ('He carries his swag.', 'hump-the-swag'),
    ('He walked carrying a swag.', 'go-waltzing-matilda'),
    ('He is showily dressed.', 'pox-doctors-clerk'),
    ('The dishonest scheme failed.', 'slanter'),
    ('They exposed a sham.', 'kid-stakes'),
    ('She wandered around aimlessly.', 'mooch-around'),
    ('They scolded him.', 'rouse-on'),
    ('There is nothing left.', 'not-a-sausage'),
    ('She is alone.', 'on-your-pat-predicate'),
    ('She is lonely.', 'lonely-as-a-shag-on-a-rock'),
    ('The low spirits passed.', 'the-joes'),
    ('I bought a 24-pack of beer.', 'slab'),
    ('I bought a freezer block.', 'ice-brick'),
    ('I know a guy who knows a guy.', 'know-a-bloke'),
    ('They girdled the trees.', 'ringbark'),
    ('The river ran high to its banks.', 'run-a-banker'),
    ('I saw a Eucalyptus coolabah.', 'coolibah-tree'),
    ('I saw a timber slab hut.', 'slab-hut'),
    ('I saw a dingo.', 'dingo'),
    ('I saw a monitor lizard.', 'goanna'),
    ('The mounted police.', 'troopers'),
    ('I drank strong drink.', 'snake-juice'),
    ('I bought fresh produce.', 'fruit-and-veg'),
])
def test_reviewed_senses_remain_eligible(reviewed, source, wanted):
    assert wanted in eligible(render(reviewed, source))


@pytest.mark.parametrize('source,excluded', [
    ('He tramps the roads.', 'hump-the-swag'),
    ('He tramps the roads.', 'go-waltzing-matilda'),
    ('He carries his swag.', 'go-waltzing-matilda'),
    ('The building is showy.', 'pox-doctors-clerk'),
    ('The cheap and nasty bag broke.', 'slanter'),
    ("That task seems like child's play.", 'kid-stakes'),
    ('She trudged home.', 'mooch-around'),
    ('She plodded home.', 'mooch-around'),
    ('They yelled at him for help.', 'rouse-on'),
    ('They shouted at him for help.', 'rouse-on'),
    ('They got angry at him.', 'rouse-on'),
    ('There is very little left.', 'not-a-sausage'),
    ('Nothing much happened.', 'not-a-sausage'),
    ('There is not much left.', 'not-a-sausage'),
    ('There is nothing but food.', 'not-a-sausage'),
    ('It is nothing like the original.', 'not-a-sausage'),
    ('She is lonely.', 'on-pat-malone'),
    ('She is alone.', 'lonely-as-a-shag-on-a-rock'),
    ('I bought a gel pack for my knee.', 'ice-brick'),
    ('I know a guy.', 'know-a-bloke'),
    ('They girdled the town.', 'ringbark'),
    ('The river overflowed its banks.', 'run-a-banker'),
    ('The river burst its banks.', 'run-a-banker'),
    ('I saw a gum tree by the waterhole.', 'coolibah-tree'),
    ('I saw a rough timber cabin.', 'slab-hut'),
    ('I saw a wild dog.', 'dingo'),
    ('The alcohol evaporated.', 'snake-juice'),
    ('The colonial police.', 'troopers'),
    ('He set him on his own animal.', 'on-your-pat'),
    ('He set him on his own animal.', 'on-your-pat-predicate'),
])
def test_distinct_meanings_do_not_become_reviewed_slang(reviewed, source, excluded):
    assert excluded not in eligible(render(reviewed, source))


@pytest.mark.parametrize('package', ['case', 'carton', '24-pack', 'twenty-four pack'])
@pytest.mark.parametrize('tail', ['bottle', 'bottles', 'label', 'labels'])
def test_beer_packages_do_not_match_containers_or_packaging_text(reviewed, package, tail):
    result = render(reviewed, f'I bought a {package} of beer {tail}.')
    assert 'slab' not in eligible(result)
    assert not any('CASE_OF_BEER' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('source', ['I bought a 24-pack of water.', 'I bought a twenty-four pack.',
                                  'I bought a 12-pack of beer.',
                                  'I bought a case of beer containing 12 bottles.',
                                  'I bought a carton of beer with 12 bottles.'])
def test_slab_does_not_invent_beer_or_erase_a_different_explicit_count(reviewed, source):
    assert 'slab' not in eligible(render(reviewed, source))


@pytest.mark.parametrize('source,expected', [
    ('I could not care less about it.', "I couldn't give a stuff about it."),
    ("I couldn't care less about it.", "I couldn't give a stuff about it."),
    ('The produce section is closed.', 'The fruit and veg section is closed.'),
    ('The produce aisle is closed.', 'The fruit and veg aisle is closed.'),
    ('The produce department is closed.', 'The fruit and veg department is closed.'),
    ('She is alone.', 'She is on her Pat Malone.'),
    ('The river ran high to its banks.', 'The river ran a banker.'),
    ('They girdled the trees.', 'They ringbarked the trees.'),
])
def test_realised_forms_preserve_modals_places_possessives_and_objects(reviewed, source, expected):
    assert render(reviewed, source).text == expected


def test_comparative_care_is_not_complete_indifference(reviewed):
    result = render(reviewed, 'I care less about it.')
    assert result.text == 'I care less about it.'
    assert not {'give-a-stuff-about', 'couldnt-give-a-stuff-about'} & eligible(result)


@pytest.mark.parametrize('domain', ['technical', 'official', 'instructions'])
def test_clinical_precision_is_an_explicit_document_setting(reviewed, domain):
    source = 'The conjunctivitis is painful.'
    assert 'sandy-blight' in eligible(render(reviewed, source))
    protected = render(reviewed, source, document_config={'term_domains': [domain]})
    assert 'sandy-blight' not in eligible(protected)
    assert protected.text == source


def test_gated_historical_low_spirits_is_available_only_when_unlocked(reviewed):
    source = 'The low spirits passed.'
    blocked = reviewed.translate(source, level=5, vulgarity=0, registers=['current','dated','archaic'],
                                 embedder='none', embellishment=0)
    assert 'the-joes' not in eligible(blocked)
    assert 'the-joes' in eligible(render(reviewed, source))


def test_reviewed_sidecar_sources_reach_cards_without_becoming_whole_construction_claims(dictionary):
    assert 'https://downloads.bbc.co.uk/learningenglish/features/tews/170606_tews_not_a_sausage.pdf' in dictionary.entries['not-a-sausage'].sources
    for eid in ['fruit-and-veg-section', 'fruit-and-veg-aisle', 'fruit-and-veg-department']:
        entry = dictionary.entries[eid]
        assert entry.sources == ('https://dictionary.cambridge.org/dictionary/english/veg',)
        assert 'compositional' in entry.notes
    sidecar = yaml.safe_load((Path(__file__).resolve().parents[2] / 'aussiefy/data/sources.yaml').read_text())
    assert all(len(urls) == len(set(urls)) for urls in sidecar.values())


@pytest.mark.parametrize('source', [
    'I bought a case of beer.', 'I bought a carton of beer.',
    'I bought a case of beer holding 12 bottles.', 'I bought a case of beer (12 bottles).',
    'I bought a carton of beer, which contains 12 bottles.',
])
def test_unknown_beer_package_counts_are_not_automatically_twenty_four(reviewed, source):
    assert 'slab' not in eligible(render(reviewed, source))


@pytest.mark.parametrize('package', ['24-pack of beer', 'twenty-four pack of beer', 'case of 24 beers',
                                    'carton of 24 beers'])
def test_explicit_twenty_four_unit_beer_packages_remain_available(reviewed, package):
    assert 'slab' in eligible(render(reviewed, f'I bought a {package}.'))
