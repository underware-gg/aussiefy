"""Approved slice 7 vocabulary, meaning identities and contextual grammar."""
from dataclasses import replace

import pytest

from aussiefy import Translator, lookup
from aussiefy.detect import read_meanings
from aussiefy.text import tokenize

OPTIONS = {'level':5, 'vulgarity':0, 'embellishment':0, 'english':'none', 'invention':False,
           'document_config':{'garnish':[], 'profile':{'phonetic':0,
              'substitution':{'lexical':1,'phrase':1,'idiom':1}}}}


def only(dictionary, eid):
    return Translator(replace(dictionary, entries={eid:dictionary.entries[eid]}), lookup_embedder=None)


def concepts(dictionary, source):
    return {c for r in read_meanings(tokenize(source), dictionary).detections for c in r.concepts}


@pytest.mark.parametrize('eid,source,expected', [
 ('puffed','I was out of breath after the stairs.','I was puffed after the stairs.'),
 ('wrecked-tired','I am exhausted.','I am wrecked.'),
 ('kerry-packered','I am exhausted.','I am Kerry-Packered.'),
 ('dead-on-poss-feet','She was exhausted.','She was dead on her feet.'),
 ('ready-to-drop','We were exhausted.','We were ready to drop.'),
 ('running-on-smell-oily-rag','He was exhausted.','He was running on the smell of an oily rag.'),
 ('run-on-smell-oily-rag','She lived on very little.','She ran on the smell of an oily rag.'),
 ('fall-off-perch','He died.','He fell off the perch.'),
 ('fall-off-perch','He has died.','He has fallen off the perch.'),
 ('rate-highly','I think highly of it.','I rate it.'),
 ('rate-highly','She thinks highly of the film.','She rates the film.'),
 ('dont-rate','I think poorly of it.',"I don't rate it."),
 ('dont-rate','She thinks poorly of the film.',"She doesn't rate the film."),
 ('dont-rate','He thought poorly of it.',"He didn't rate it."),
 ('dont-rate','I will think poorly of it.','I will not rate it.'),
 ('dont-rate','I want to think poorly of it.','I want to not rate it.'),
 ('dont-rate','Does she think poorly of it?','Does she not rate it?'),
 ('dont-rate','He has thought poorly of it.','He has not rated it.'),
 ('dont-rate','She is thinking poorly of it.','She is not rating it.'),
 ('dont-rate','I had my staff think poorly of it.','I had my staff not rate it.'),
 ('dont-rate','Does the critic think poorly of it?','Does the critic not rate it?'),
])
def test_approved_entries_render_at_the_actual_source_slot(dictionary,eid,source,expected):
    result=only(dictionary,eid).translate(source,**OPTIONS)
    assert result.text == expected
    assert any(r.chosen and r.chosen.entry.id == eid for r in result.records)


def test_puffed_is_actually_available_at_level_one_and_is_shared_english(dictionary):
    entry=dictionary.entries['puffed']
    assert (entry.incoherence,entry.vulgarity,entry.reads_as)==(1,0,'general')
    assert entry.concept==('BREATHLESS',)
    result=only(dictionary,'puffed').translate('I was out of breath.',**(OPTIONS|{'level':1}))
    assert result.text=='I was puffed.'
    assert lookup('out of breath',translator=Translator(dictionary,lookup_embedder=None),level=1,vulgarity=0)['outcome']=='matched'


@pytest.mark.parametrize('source', ['The rice was puffed.', 'His face was puffed up.',
 'He was puffed up with pride.','The puffed sleeves were fashionable.'])
def test_puffed_literal_senses_do_not_establish_breathlessness(dictionary,source):
    assert 'BREATHLESS' not in concepts(dictionary,source)


@pytest.mark.parametrize('source,cid', [
 ('Have a heart.','HEART_COMPASSION'),('Take heart.','HEART_SPIRIT'),
 ('Put your heart into it.','HEART_EFFORT'),("Her heart wasn't in it.",'HEART_EFFORT')])
def test_approved_heart_split_has_distinct_readings(dictionary,source,cid):
    found=concepts(dictionary,source)
    assert found & {'HEART_COMPASSION','HEART_SPIRIT','HEART_EFFORT'} == {cid}
    result=lookup(source,translator=Translator(dictionary,lookup_embedder=None))
    assert cid in {r['concept'] for r in result['meanings']}


def test_heart_split_keeps_medication_and_the_organ_out(dictionary):
    assert not {'HEART_SPIRIT','HEART_COMPASSION','HEART_EFFORT'} & concepts(dictionary,'Take heart medication daily.')
    assert 'HEART_ORGAN' in concepts(dictionary,'She has a healthy heart.')
    assert dictionary.concepts['HEART_EFFORT'].plain_forms['vp']=='try hard at {obj}'


@pytest.mark.parametrize('source,cid', [('I really rate it.','REGARD_HIGHLY'),
 ('I rate it highly.','REGARD_HIGHLY'),("I don't rate it.",'REGARD_POORLY'),
 ('I rate the new film.','REGARD_HIGHLY')])
def test_testimony_rate_forms_establish_the_right_regard(dictionary,source,cid):
    assert concepts(dictionary,source) & {'REGARD_HIGHLY','REGARD_POORLY'} == {cid}


@pytest.mark.parametrize('source', ['I rate it four stars.','She rated the hotel five stars.',
 "I don't rate it four stars.", 'Please rate your stay.','I rate it out of ten.','I rate it on a scale of one to ten.',
 'The rate of inflation rose.','At this rate we will be late.'])
def test_scoring_requests_and_rates_do_not_become_regard(dictionary,source):
    assert not {'REGARD_HIGHLY','REGARD_POORLY'} & concepts(dictionary,source)
    result=Translator(dictionary,lookup_embedder=None).translate(source,**OPTIONS)
    assert not any(r.chosen and r.chosen.entry.id in {'rate-highly','dont-rate'} for r in result.records)


def test_wrecked_person_and_vehicle_do_not_share_the_tired_reading(dictionary):
    assert 'TIRED' in concepts(dictionary,'I am wrecked after work.')
    assert 'TIRED' not in concepts(dictionary,'The car was wrecked in the crash.')
    assert 'BROKEN' in concepts(dictionary,'The car was wrecked in the crash.')


def test_testimony_is_not_invented_documentary_attestation(dictionary):
    ids={'wrecked-tired','kerry-packered','dead-on-poss-feet','ready-to-drop',
         'running-on-smell-oily-rag','run-on-smell-oily-rag','fall-off-perch','rate-highly','dont-rate'}
    for eid in ids:
        e=dictionary.entries[eid]
        assert e.testimony.people == e.testimony.independent == 1
        assert all(s.kind == 'testimony' and not s.url for s in e.sources)
    assert not any('prize pig' in e.form for e in dictionary.entries.values())


def test_oily_rag_forms_cover_both_approved_senses(dictionary):
    tr=Translator(dictionary,lookup_embedder=None)
    result=lookup('running on the smell of an oily rag',translator=tr,level=5,vulgarity=0)
    words={r['id']:r for r in result['results']}
    assert {'run-on-smell-oily-rag','running-on-smell-oily-rag'} <= set(words)
    assert dictionary.entries['run-on-smell-oily-rag'].concept==('FRUGAL_LIVING',)
    assert dictionary.entries['running-on-smell-oily-rag'].concept==('TIRED',)
