"""Appetite phrases fit feeling, tense and questions; elaborate images remain optional writer material."""

import pytest

from aussiefy import harness


APPETITE = {'feel-like-a-decent-feed', 'feel-like-some-tucker'}
HUNGER_IMAGES = {'could-go-a-decent-feed', 'hanging-out-for-a-feed', 'stomach-throat-cut', 'hungry-butter-beer-coaster',
                 'hungry-tomato-sauce-thong', 'hungry-guts-protest', 'could-do-with-a-feed',
                 'wouldnt-say-no-to-some-tucker'}


def translate(translator, text, seed):
    return translator.translate(text, level=5, seed=seed, vulgarity=0, embellishment=0,
        document_type='custom', document_config={'profile': {'phonetic': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


@pytest.mark.parametrize('source,expected', [
    ('feeling pretty hungry', {'feeling like a decent feed', 'feeling like some tucker'}),
    ('I am feeling pretty hungry.', {'I am feeling like a decent feed.', 'I am feeling like some tucker.'}),
    ('She feels pretty hungry.', {'She feels like a decent feed.', 'She feels like some tucker.'}),
    ('She felt pretty hungry.', {'She felt like a decent feed.', 'She felt like some tucker.'}),
    ('Are you feeling pretty hungry?', {'Are you feeling like a decent feed?', 'Are you feeling like some tucker?'}),
    ('They might feel hungry.', {'They might feel like a decent feed.', 'They might feel like some tucker.'}),
])
def test_appetite_phrases_fit_the_whole_verb_phrase(translator, source, expected):
    outputs = {translate(translator, source, seed).text for seed in range(16)}
    assert outputs == expected


@pytest.mark.parametrize('source', [
    'She feels hungry for success.', 'Feeling pretty hungry for power.',
    'I feel pretty hungry to win.', 'They feel pretty hungry children need help.',
])
def test_appetite_phrases_do_not_consume_other_complements(translator, source):
    result = translate(translator, source, 0)
    assert not APPETITE & {r.chosen.entry.id for r in result.records if r.substituted}


def plan(translator, text, exaggeration=2, vulgarity=1):
    return harness.plan(text, translator=translator, level=5, vulgarity=vulgarity, document_type='custom',
        document_config={'garnish': ['riff'], 'contextual_riffs': True, 'entry_riffs': False,
            'riff_exaggeration': exaggeration, 'profile': {'frames': [], 'phonetic': 0,
                'garnish': {'riff': 1}, 'max_garnish': {'riff': 0}}})


def images(result):
    return {i['id']: i for group in result['riffs'] for i in group['riffs'] if 'id' in i}


def test_elaborate_hunger_images_remain_rewrites_with_honest_origins(translator):
    result = plan(translator, 'She is hungry.')
    offered = images(result)
    assert HUNGER_IMAGES <= offered.keys()
    assert all(not offered[i]['automatic'] and offered[i]['form'] == 'rewrite' for i in HUNGER_IMAGES)
    assert offered['stomach-throat-cut']['text'] == "her stomach thinks her throat's been cut"
    assert offered['stomach-throat-cut']['origin'] == 'familiar'
    assert offered['could-go-a-decent-feed']['exaggeration'] == 0
    assert all(offered[i]['origin'] == 'original' for i in HUNGER_IMAGES if i.startswith('hungry-'))
    assert result['draft'] == 'She is hungry.'


def test_hunger_images_respect_exaggeration_and_vulgarity(translator):
    assert HUNGER_IMAGES & images(plan(translator, 'She is hungry.', exaggeration=0)).keys() == {
        'could-go-a-decent-feed', 'hanging-out-for-a-feed', 'could-do-with-a-feed',
        'wouldnt-say-no-to-some-tucker'}
    assert 'hungry-guts-protest' not in images(plan(translator, 'She is hungry.', vulgarity=0))


def test_all_new_templates_are_discoverable_for_a_writer(translator):
    result = harness.lookup('hungry', translator=translator, level=5, vulgarity=1, embellishment='troppo', limit=20)
    offered = {i['id']: i for i in result['imagery']}
    assert HUNGER_IMAGES <= offered.keys()
    assert all(offered[i]['template'] and not offered[i]['automatic'] for i in HUNGER_IMAGES)


@pytest.mark.parametrize('source', ['She is not hungry.', "She isn't hungry.", 'She is hungry for success.'])
def test_images_do_not_invent_appetite_or_turn_metaphors_into_food(translator, source):
    assert not HUNGER_IMAGES & images(plan(translator, source)).keys()
