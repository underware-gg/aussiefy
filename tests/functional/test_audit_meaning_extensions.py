"""Source-audited forms preserve packaging, activity, time, currency and grammatical roles."""

import pytest


def render(translator, source, seed=0, cap=0):
    return translator.translate(source, level=5, vulgarity=cap, seed=seed, embedder='none',
        registers=['current', 'dated'], document_type='custom', document_config={
            'garnish': ['infix'], 'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


def offered(result):
    return {c.entry.id for r in result.records for c in r.eligible}


@pytest.mark.parametrize('source,expected', [
    ('I bought a can of beer.', 'I bought a tinnie.'),
    ('I bought a small bottle of beer.', 'I bought a stubby.'),
    ('I bought a bottle of beer.', 'I bought a bottle of beer.'),
    ('The embryo is viable.', 'The embryo is viable.'),
    ('The plan is feasible.', 'The plan is a goer.'),
    ('I heard the latest gossip.', 'I heard the goss.'),
    ('They had a gossip.', 'They had a goss.'),
    ('We booked a pub dinner for eight.', 'We booked a counter meal for eight.'),
])
def test_supported_constructions_are_grammatical(translator, source, expected):
    assert render(translator, source).text == expected


@pytest.mark.parametrize('source,excluded', [
    ('I bought a can of beer.', {'stubby'}),
    ('I bought a bottle of beer.', {'stubby', 'tinnie'}),
    ('I bought a small bottle of beer.', {'tinnie'}),
    ('They drank beer.', {'stubby', 'tinnie'}),
    ('They needed a school sports field.', {'the-footy-oval'}),
    ('This costs ten dollars.', {'quid'}),
    ('They carried a pound of flour.', {'quid'}),
    ('The embryo is viable.', {'a-goer'}),
    ('We bred a crossbreed of two cattle.', {'a-bitzer'}),
    ('They were testing the latest.', {'a-goss', 'have-a-goss', 'a-goss-session'}),
    ('They installed the latest software.', {'a-goss', 'have-a-goss', 'a-goss-session'}),
    ('It was an argument, with no aggression.', {'biffo'}),
    ('It was a verbal fight.', {'biffo'}),
    ('We booked a pub dinner for eight.', {'a-counter-lunch'}),
    ('We attended a dance party inside a hotel ballroom.', {'a-bush-doof'}),
    ('It was a binge of science documentaries.', {'piss-up'}),
    ('A cold front crossed the American plains.', {'southerly-buster'}),
])
def test_distinct_references_are_not_inferred(translator, source, excluded):
    assert not offered(render(translator, source, cap=3)) & excluded


def test_morning_is_not_inferred_from_generic_early(translator):
    assert 'sparrows-fart' in offered(render(translator, 'They swam at dawn.', cap=1))
    for source in ['He finished very early in the evening.', 'She spoke first thing after lunch.']:
        assert 'sparrows-fart' not in offered(render(translator, source, cap=1))


@pytest.mark.parametrize('source,entry', [
    ('They played on the football oval.', 'the-footy-oval'),
    ('They wanted cash.', 'quid'),
    ('He is a mixed-breed dog.', 'a-bitzer'),
    ('It was a brawl.', 'biffo'),
    ('We booked a pub lunch.', 'a-counter-lunch'),
    ('We attended an outdoor rave.', 'a-bush-doof'),
    ('It was a drinking party.', 'piss-up'),
    ('A gusty southerly change arrived.', 'southerly-buster'),
])
def test_precise_positive_contexts_remain_available(translator, source, entry):
    assert entry in offered(render(translator, source, cap=3))


@pytest.mark.parametrize("source,expected", [
    ("They drank beer.", "They drank amber fluid."),
    ("They drank a cold beer.", "They drank a coldie."),
    ("It was a pretence.", "It was kid stakes."),
    ("The rumours were false.", "The rumours were false."),
])
def test_mass_and_count_noun_grammar(translator, source, expected):
    assert render(translator, source).text == expected


def test_beer_package_qualifiers_do_not_become_count_nouns(translator):
    result = render(translator, "I bought a case of beer holding 12 bottles.")
    assert result.text == "I bought a case of amber fluid holding 12 bottles."


@pytest.mark.parametrize('source', [
    'I bought one beer.', 'I bought 1 beer.', 'I bought another beer.',
    'I bought every beer.', 'I bought each beer.', 'I bought one warm beer.',
    'I bought another very warm beer.', 'I bought many beers.',
])
def test_mass_beer_wording_preserves_count_constructions(translator, source):
    result = render(translator, source)
    assert 'amber-fluid' not in offered(result)
    assert 'beer' in result.text


@pytest.mark.parametrize('source', [
    'I drank beer.', 'I drank some beer.', 'I drank much beer.', 'I drank no beer.',
    'I drank some warm beer.', 'I drank a pint of beer.', 'I drank either beer or wine.',
])
def test_mass_beer_wording_accepts_mass_quantifiers_and_containers(translator, source):
    result = render(translator, source)
    assert 'amber-fluid' in offered(result)
    assert 'amber fluid' in result.text


@pytest.mark.parametrize('beverage', ['root beer', 'ginger beer'])
def test_named_beer_compounds_retain_their_identity(translator, beverage):
    source = f'They drank {beverage}.'
    result = render(translator, source)
    assert result.text == source
    assert 'amber-fluid' not in offered(result)
    assert not any('BEER' in record.det.concepts for record in result.records)


@pytest.mark.parametrize('source', ['I heard each rumour.', 'I heard another rumour.'])
def test_mass_number_compatibility_applies_to_information_nouns(translator, source):
    assert 'a-goss' not in offered(render(translator, source))


@pytest.mark.parametrize('source,available', [('I drank beer.', True), ('I bought one warm beer.', False)])
def test_change_options_share_mass_number_eligibility(translator, source, available):
    from aussiefy import translate_changes
    changes = translate_changes(source, translator=translator, level=5, vulgarity=0,
        embellishment=0, embedder='none', document_type='custom', document_config={
            'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    ids = {option['entry_id'] for change in changes.changes for option in change['alternatives']}
    assert ('amber-fluid' in ids) == available
