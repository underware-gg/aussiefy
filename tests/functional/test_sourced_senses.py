"""Source-reviewed meanings retain the source's event, number, effort and benefit-receipt claims."""

import pytest

from aussiefy import Translator
from aussiefy.lookup import lookup


def render(translator, text, seed=0):
    return translator.translate(text, level=5, seed=seed, vulgarity=0, registers=['current', 'dated'],
        document_type='custom', document_config={'profile': {'phonetic': 0, 'substitution': {
            'lexical': 1, 'phrase': 1, 'idiom': 1}}})


def picks(result):
    return {r.chosen.entry.id for r in result.records if r.substituted}


@pytest.mark.parametrize('text,expected', [
    ('It was a lively party.', 'It was a party going off like a frog in a sock.'),
    ('Those lively parties were noisy.', 'Those parties going off like a frog in a sock were noisy.'),
    ('They partied wildly.', 'They went off like a frog in a sock.'),
    ('She went wild with excitement.', 'She went off like a frog in a sock.'),
])
def test_frog_has_explicit_lively_party_and_excited_reaction_senses(translator, text, expected):
    assert render(translator, text).text == expected


@pytest.mark.parametrize('text', [
    'The party started.', 'It was a political party.', 'She was excited.',
    'The pendulum was in full swing.', 'The party was not lively.',
    'It was a lively party conference.', 'The wild party leader spoke.',
    'Those energetic party members voted.', 'He is a lively party planner.',
])
def test_frog_does_not_invent_a_wild_party_or_reaction(translator, text):
    assert not picks(render(translator, text)) & {'frog-in-a-sock-party', 'go-off-like-a-frog-in-a-sock'}


@pytest.mark.parametrize('text', [
    'She is unemployed.', 'They were jobless.', 'He is out of work.', 'She is on welfare.',
])
def test_joblessness_does_not_assert_benefit_receipt_or_avoidance(translator, text):
    result = render(translator, text)
    assert not picks(result) & {'dole-bludger', 'on-the-dole', 'the-dole'}


def test_explicit_unemployment_payments_remain_distinct_from_work_avoidance(translator):
    result = render(translator, 'She is receiving unemployment benefits.')
    assert result.text == 'She is on the dole.'
    assert picks(result) == {'on-the-dole'}
    accusation = render(translator, 'He is a work-shy unemployment benefits claimant.')
    assert accusation.text == 'He is a dole bludger.'
    assert picks(accusation) == {'dole-bludger'}


def test_lookup_does_not_equate_unemployed_with_work_avoidance(dictionary):
    result = lookup('unemployed', translator=Translator(dictionary, lookup_embedder=None))
    assert not {'dole-bludger', 'on-the-dole'} & {e['id'] for e in result['results']}


def test_earnest_attempt_does_not_claim_hardship(translator):
    assert render(translator, 'They gave it everything.').text == 'They had a proper crack.'
    assert 'have-a-proper-crack' not in picks(render(translator, 'They suffered hardship.'))
    assert not picks(render(translator, 'They fought hard with knives.')) & {'have-a-proper-crack', 'do-it-tough'}
    assert 'have-a-proper-crack' not in picks(render(translator, 'They tried hard to lift it.'))
    assert 'have-a-proper-crack' not in picks(render(translator, 'They gave it everything they had.'))


@pytest.mark.parametrize('text', [
    'God willing, we will return.', 'By the grace of God, she survived.',
    'Everything is true, so help me God.', 'This nation, under God, shall endure.',
    'By God, I will finish this.',
])
def test_religious_contexts_do_not_become_surprise_or_wrong_contingency(translator, text):
    for seed in range(8):
        result = render(translator, text, seed)
        assert 'by-crikey' not in picks(result)
        if not text.startswith('God willing'):
            assert 'god-bloody-willing' not in picks(result)


def test_by_crikey_remains_available_as_a_surprise_exclamation(translator):
    assert any('by-crikey' in picks(render(translator, 'Wow!', seed)) for seed in range(64))


def test_fair_go_does_not_replace_every_kind_of_freedom(translator):
    assert picks(render(translator, 'They wanted fair treatment.')) & {'a-fair-go', 'a-fair-shake'}
    for text in ['They wanted freedom.', 'They fought for liberty.', 'Freedom of speech matters.']:
        assert not picks(render(translator, text)) & {'a-fair-go', 'a-fair-shake'}


def test_loose_consecration_paraphrases_need_explicit_unlock(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    loose = {'make-true-blue', 'make-true-blue-bare', 'make-fair-dinkum'}
    for query in ['true blue', 'make fair dinkum']:
        plain = lookup(query, translator=tr, limit=100)
        assert not loose & {e['id'] for e in plain['results']}
        unlocked = lookup(query, translator=tr, limit=100, include_gated=True)
        held = [e for e in unlocked['results'] if e['id'] in loose]
        assert held and all(e['gated'] == ['dubious_meaning'] for e in held)
    for seed in range(8):
        assert not loose & picks(render(tr, 'We consecrated it.', seed))


@pytest.mark.parametrize('text,expected', [
    ('We used the barbecue for the first time.', 'We christened the barbecue.'),
    ('She uses it for the first time.', 'She christens it.'),
    ('We consecrated it.', 'We consecrated it.'),
    ('They sanctified the ground.', 'They sanctified the ground.'),
])
def test_first_use_keeps_its_object_and_does_not_replace_consecration(translator, text, expected):
    assert render(translator, text).text == expected
