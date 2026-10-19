"""Reviewed vocabulary keeps the input's role, reference and lexical sense."""

import pytest

from aussiefy import harness


def render(translator, source, seed=0):
    return translator.translate(source, level=5, vulgarity=1, registers=['current', 'dated'], seed=seed,
        embellishment=0, document_type='custom', document_config={'profile': {'phonetic': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


def selected(result):
    return {r.chosen.entry.id for r in result.records if r.substituted}


@pytest.mark.parametrize('source,expected', [
    ('We began.', 'We kicked off.'),
    ('They cobbled together a chair.', 'They knocked together a chair.'),
    ('She wanted comradeship.', 'She wanted mateship.'),
    ('Tell him to dream on.', "Tell him he's dreamin'."),
    ('Tell them to dream on.', "Tell them they're dreamin'."),
    ('I could do with a meal.', 'I could do with a feed.'),
    ('We could do with something to eat.', 'We could do with a feed.'),
    ("I wouldn't say no to some food.", "I wouldn't say no to some tucker."),
    ('They needed another chance at success.', 'They needed another crack at success.'),
])
def test_supported_senses_are_available(translator, source, expected):
    assert render(translator, source).text == expected


@pytest.mark.parametrize('source,excluded', [
    ('They put together a chair.', {'kick-off', 'knock-together'}),
    ('They brought forth a child.', {'kick-off', 'knock-together'}),
    ('They brought forth a nation.', {'kick-off', 'knock-together'}),
    ('She valued devotion to God.', {'mateship'}),
    ('She valued brand loyalty.', {'mateship'}),
    ('Ask the authorities.', {'pollie', 'the-pollies'}),
    ('The government announced a plan.', {'pollie', 'the-pollies'}),
    ('They wanted a new lease of life.', {'another-crack-at'}),
    ('She left for no reason.', {'for-nothin', 'for-sweet-bugger-all'}),
    ('They ate on the enclosed porch.', {'a-sleep-out'}),
    ('They waited in the school lunchroom.', {'the-tuckshop'}),
    ('She is a reckless driver.', {'a-yobbo', 'a-peb'}),
    ('He was an itinerant worker.', {'sundowner'}),
    ('Could you do with a meal?', {'could-do-with-a-feed'}),
    ('I could have done with a meal.', {'could-do-with-a-feed'}),
    ('She was hungry.', {'could-do-with-a-feed', 'wouldnt-say-no-to-some-tucker'}),
    ('A known source sentence start.', {'kick-off'}),
    ('The race start.', {'kick-off'}),
    ('They looked for a tramp steamer.', {'swagman', 'sundowner'}),
    ('They saw a tramp stamp.', {'swagman', 'sundowner'}),
    ('They removed tramp iron.', {'swagman', 'sundowner'}),
    ('I could do with a meal allowance.', {'could-do-with-a-feed'}),
    ('I could do with some food colouring.', {'could-do-with-a-feed'}),
    ('I could do with some food security.', {'could-do-with-a-feed'}),
    ("I wouldn't say no to some food poisoning training.", {'wouldnt-say-no-to-some-tucker'}),
])
def test_distinct_meanings_are_not_collapsed(translator, source, excluded):
    for seed in range(8):
        assert not selected(render(translator, source, seed)) & excluded


def test_lout_and_driver_senses_share_only_supported_options(translator):
    driver = {e for seed in range(8) for e in selected(render(translator, 'He is a reckless driver.', seed))}
    lout = {e for seed in range(16) for e in selected(render(translator, 'He is a lout.', seed))}
    assert driver == {'a-hoon'}
    assert 'a-yobbo' in lout
    assert 'a-hoon' in lout


def test_a_finite_start_after_a_noun_subject_still_has_its_verb_reading(translator):
    assert render(translator, 'The race got started.').text == 'The race kicked off.'


def test_named_cultural_terms_are_discoverable_without_inventing_their_context(translator):
    for query, entry in [('Goon of Fortune', 'goon-of-fortune'), ('Hills Hoist', 'hills-hoist')]:
        cards = harness.lookup(query, translator=translator, level=5, vulgarity=0, limit=20)['results']
        assert entry in {c['id'] for c in cards}
    for source in ['We played a drinking game.', 'They held a party.', 'She bought a rotary clothesline.']:
        assert not selected(render(translator, source)) & {'goon-of-fortune', 'hills-hoist'}


def test_non_monetary_wasted_effort_is_preserved(translator):
    result = translator.translate('They waited in vain.', level=5, vulgarity=1, embellishment='dinkum')
    choices = {c.entry.id for r in result.records for c in r.eligible}
    assert 'for-sweet-bugger-all' in choices
