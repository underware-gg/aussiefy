"""Rob's R78–R80 rulings keep sense, source wording and permissions independent."""
from dataclasses import replace

import pytest

from aussiefy import Translator, get_entry, translate_changes
from aussiefy.changes import Watch
from aussiefy.detect import read_meanings
from aussiefy.masks import masks
from aussiefy.plain_wording import plain_entry
from aussiefy.select import Candidate
from aussiefy.text import tokenize

BASE = dict(level=5, vulgarity=3, embellishment=0, english='none', embedder=None,
            document_config={'garnish': [], 'profile': {'phonetic':0,
                'substitution': {'lexical':1, 'phrase':1, 'idiom':1}}})
SPLITS = [('a-blue','a-blue-argument','FIGHT','ARGUE'),
          ('cark-it','cark-it-machine','DIE','BROKEN'),
          ('carked-it','carked-it-dead','BROKEN','DIE'),
          ('give-a-hiding','give-a-hiding-defeat','BEAT_UP','DEFEAT_SOUNDLY'),
          ('kick-arse','kick-arse-defeat','BEAT_UP','DEFEAT_SOUNDLY'),
          ('perv-on','perv-on-admire','OGLE','ADMIRING_LOOK'),
          ('put-the-boot-in','put-the-boot-in-criticise','KICK_WHEN_DOWN','PILE_ON_CRITICISM')]


@pytest.mark.parametrize('old,new,old_meaning,new_meaning', SPLITS)
def test_approved_senses_keep_public_ids_and_written_forms(dictionary,old,new,old_meaning,new_meaning):
    a,b=dictionary.entries[old],dictionary.entries[new]
    assert a.form == b.form and a.concept == (old_meaning,) and b.concept == (new_meaning,)
    assert old in dictionary.entry_ids and new in dictionary.entry_ids
    assert 'R80' in a.notes and 'R80' in b.notes
    assert a.testimony is None and b.testimony is None
    assert get_entry(old,translator=Translator(dictionary,lookup_embedder=None))['outcome']=='matched'
    if new not in {'carked-it-dead'}:
        assert not b.themes
    else:
        assert b.themes == ('death',)
    assert '{' not in b.gloss and '}' not in b.gloss


@pytest.mark.parametrize('source,meaning,wrong', [
    ('They had an argument about the bill.','ARGUE','FIGHT'),
    ('A physical fight outside the pub.','FIGHT','ARGUE'),
    ('The van died.','BROKEN','DIE'),
    ('The old dog died.','DIE','BROKEN'),
    ('He has died.','DIE','BROKEN'),
    ('The van has carked it.','BROKEN','DIE'),
    ('The old tree carked it.','DIE','BROKEN'),
    ('They beat him up.','BEAT_UP','DEFEAT_SOUNDLY'),
    ('They trounced us at chess.','DEFEAT_SOUNDLY','BEAT_UP'),
    ('She admired the cars at the car show.','ADMIRING_LOOK','OGLE'),
    ('They piled on more criticism after her setback.','PILE_ON_CRITICISM','KICK_WHEN_DOWN'),
])
def test_scoped_source_readings_do_not_randomly_choose_the_opposite_sense(dictionary,source,meaning,wrong):
    meanings={c for r in read_meanings(tokenize(source),dictionary).detections for c in r.concepts}
    assert meaning in meanings and wrong not in meanings


@pytest.mark.parametrize('source', ['They thrashed us.','They walloped us.','A fight.'])
def test_unqualified_mixed_senses_remain_held(dictionary,source):
    tr=Translator(dictionary,lookup_embedder=None)
    changes=translate_changes(source,translator=tr,**BASE)
    assert changes.text == source
    assert any('UNRESOLVED_SENSE' in r.concepts for r in read_meanings(tokenize(source),dictionary).detections)
    assert not any(r.chosen for r in changes.result.records)


@pytest.mark.parametrize('source,forbidden', [
    ('They beat the eggs.',{'BEAT_UP','DEFEAT_SOUNDLY'}),
    ('She looked at the timetable.',{'ADMIRING_LOOK','OGLE'}),
    ('They perved on the photos.',{'ADMIRING_LOOK'}),
    ('They criticised a first draft.',{'PILE_ON_CRITICISM'}),
    ('They kicked the winning goal.',{'KICK_WHEN_DOWN','PILE_ON_CRITICISM'}),
    ('She wore a blue shirt.',{'FIGHT','ARGUE'}),
    ('He is dead serious.',{'DIE'}),
    ('He was dead inside.',{'DIE'}),
])
def test_split_controls_do_not_invent_the_slang_reading(dictionary,source,forbidden):
    meanings={c for r in read_meanings(tokenize(source),dictionary).detections for c in r.concepts}
    assert not meanings & forbidden


@pytest.mark.parametrize('eid,source,expected', [
    ('a-blue-argument','There was an argument about the bill.','There was a blue about the bill.'),
    ('cark-it-machine','The van died.','The van carked it.'),
    ('carked-it-dead','He is dead.','He has carked it.'),
    ('give-a-hiding','They beat him up.','They give him a hiding.'),
    ('give-a-hiding-defeat','They trounced us at chess.','They gave us a hiding at chess.'),
    ('kick-arse','They beat him up.',"They kick his arse."),
    ('kick-arse-defeat','They trounced us at chess.',"They kicked our arse at chess."),
    ('perv-on-admire','She admired the cars at the car show.','She perved on the cars at the car show.'),
    ('put-the-boot-in-criticise','They piled on more criticism after her setback.','They put the boot in after her setback.'),
])
def test_each_new_rendering_preserves_its_arguments_and_context(dictionary,eid,source,expected):
    tr=Translator(replace(dictionary,entries={eid:dictionary.entries[eid]}),lookup_embedder=None)
    for seed in (0,3):
        result=tr.translate(source,seed=seed,**BASE)
        assert result.text == expected
        assert any(r.chosen and r.chosen.entry.id==eid for r in result.records)


def test_figurative_readings_do_not_erase_word_vulgarity(dictionary):
    assert dictionary.entries['kick-arse-defeat'].vulgarity==2
    assert dictionary.entries['perv-on-admire'].vulgarity==1
    for eid,source in [('kick-arse-defeat','They trounced us at chess.'),
                       ('perv-on-admire','She admired the cars at the car show.')]:
        tr=Translator(replace(dictionary,entries={eid:dictionary.entries[eid]}),lookup_embedder=None)
        result=tr.translate(source,**(BASE|{'vulgarity':0}))
        assert result.text==source


@pytest.mark.parametrize('cap', [0,1,2,3])
def test_plural_cunts_requires_explicit_tradie_and_keeps_masking(dictionary,cap):
    entry=dictionary.entries['cunts-address']
    tr=Translator(replace(dictionary,entries={entry.id:entry}),lookup_embedder=None)
    cs=translate_changes('Hello everyone.',translator=tr,**(BASE|{'vulgarity':cap}))
    chosen=[c for c in cs.changes if c.get('entry_id')==entry.id]
    assert bool(chosen)==(cap==3)
    assert masks('cunts',dictionary.swears,dictionary.swear_compounds,{w:entry.vulgarity for w in entry.mask})==[
        {'span':[0,5],'ending_start':4,'vulgarity':3}]
    for source in ['Everyone is ready.','I invited everyone.']:
        assert tr.translate(source,**(BASE|{'vulgarity':cap})).text==source
    assert tr.translate('Hello everyone.',**(BASE|{'document_type':'custom','vulgarity':cap})).text=='Hello everyone.'


@pytest.mark.parametrize('eid,form', [('g-ya-mad-cunt','you wild one'),('g-ya-cunt','my friend'),
                                     ('g-ya-beautiful-cunt','you wonderful person')])
def test_approved_tradie_english_forms_are_available_without_masking_source(dictionary,eid,form):
    entry=dictionary.entries[eid]
    assert entry.plain_form==form and entry.vulgarity==3
    tr=Translator(dictionary,lookup_embedder=None)
    cs=translate_changes('Thanks, '+entry.form+'!',translator=tr,**(BASE|{'vulgarity':0}))
    kept=next(c for c in cs.changes if c['kind']=='kept' and entry.form in c['original'].lower())
    assert not kept['masks'] and kept['original']==kept['output']
    assert any(o['kind']=='plain' and o['rendered'].lower()==form for o in kept['alternatives'])


@pytest.mark.parametrize('source,cid,expected', [
    ('Her heart was broken.','HEARTBREAK','She was heartbroken.'),
    ('Your heart was broken.','HEARTBREAK','You were heartbroken.'),
    ('My heart is broken.','HEARTBREAK','I am heartbroken.'),
    ("Their heart wasn't in it.",'HEART_EFFORT','They were not engaged in it.'),
    ("Her heart wasn't in it.",'HEART_EFFORT','She was not engaged in it.'),
    ('I doubt it could be done.','DOUBT_IT','I doubt it could be done.'),
    ('I doubt it would work.','DOUBT_IT','I doubt it would work.'),
])
def test_faithful_forms_use_the_real_spot_renderer(dictionary,source,cid,expected):
    tr=Translator(dictionary,lookup_embedder=None);watch=Watch()
    tr.translate(source,**BASE,_observer=watch)
    spot=next(s for s in watch.spots if cid in s.rec.det.concepts)
    ent,reading=plain_entry(dictionary.concepts[cid],spot.rec.det,dictionary,tokens=spot.sent.tokens,tags=spot.sent.tags)
    rendered=tr.render_at_spot(Candidate(ent,0,'English',kind='plain',reading=reading),spot,replace(watch.run,state=spot.state.copy()))
    a,b=spot.sent.tokens[rendered.start].start,spot.sent.tokens[rendered.end-1].end
    assert source[:a]+rendered.text+source[b:]==expected


def test_prize_pig_remains_unadmitted(dictionary):
    assert not any('prize' in e.form and 'pig' in e.form for e in dictionary.entries.values())
