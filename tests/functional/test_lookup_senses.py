"""Lookup recognises grammar slots and inflection without borrowing an unrelated sense."""
import pytest

from aussiefy import lookup


@pytest.mark.parametrize('query', ['give them a bell', 'give him a bell', 'give her a bell', 'give Bob a bell', 'give them a bell.', '(give them a bell)'])
def test_filled_object_slot_finds_the_telephone_sense(query, translator):
    results = lookup(query, translator=translator)['results']
    assert results and any('bell' in f for f in results[0].get('variants', []))
    assert not any(any(word in r['form'] for word in ['hiding', 'arse', 'towel']) for r in results)


def test_shouted_does_not_inflect_a_drinks_noun(translator):
    results = lookup('shouted', translator=translator)['results']
    assert not any('shout' in r['form'] for r in results)


@pytest.mark.parametrize('query,form', [('coves', 'cove'), ('chucked a sickie', 'chuck a sickie'),
                                      ('playing up', 'play up')])
def test_real_noun_and_head_verb_inflections_still_work(query, form, translator):
    assert form in [r['form'] for r in lookup(query, translator=translator)['results']]


@pytest.mark.parametrize('query,form', [
    ('drink', 'flat out like a lizard drinking'), ('bushwalk', 'bushwalking'),
    ('pull', '{subj} {be} pulling a swifty'), ('kip', "been kippin' in"),
])
def test_partial_lookup_handles_standard_and_dropped_g(query, form, dictionary):
    from aussiefy import Translator

    results = lookup(query, translator=Translator(dictionary, lookup_embedder=None), limit=100)['results']
    assert any(r['form'] == form and r['match'] == 'part of a phrase' for r in results)


def test_negated_model_meaning_needs_a_shared_anchor(translator):
    bad = {'OUT_OF_LINE', 'DANGEROUS', 'SCOUNDREL'}
    assert all(not bad.intersection(r['concepts']) for r in lookup('harmless', translator=translator)['results'])


def test_slots_cannot_cross_trailing_words(translator):
    out = lookup('give them a bell then', translator=translator)['results']
    assert all(r['match'] != 'slang term' for r in out)


def test_slot_only_custom_form_is_rejected_at_dictionary_boundary(tmp_path):
    from aussiefy import load_dictionary
    from aussiefy.schema import SchemaError

    path = tmp_path / 'slot-only.yaml'
    path.write_text('- {id: zz-slot-only, form: "{obj}", concept: [TIRED], frame: vp}\n')
    with pytest.raises(SchemaError, match='needs at least one required literal word'):
        load_dictionary([path])


@pytest.mark.parametrize('query', ["Don't be a cunt", "Don’t be a cunt", 'Do not be a cunt', "Don't be a jerk",
                                  "Don't be cruel", "Don't be late"])
def test_a_negated_auxiliary_is_not_evidence_for_reassurance(query, dictionary):
    from aussiefy import Translator
    for backend in ('bundled', None):
        result = lookup(query, translator=Translator(dictionary, lookup_embedder=backend), vulgarity=3)
        assert not any('NO_PROBLEM' in e['concepts'] for e in result['results'])


@pytest.mark.parametrize('query', ["Don't worry", "Don’t worry", 'Do not worry'])
def test_real_reassurance_keeps_its_meaning(query, dictionary):
    from aussiefy import Translator
    result = lookup(query, translator=Translator(dictionary, lookup_embedder='bundled'))
    assert any('NO_PROBLEM' in e['concepts'] for e in result['results'])


@pytest.mark.parametrize('query', ['whisper', 'Whisper!', 'a whisper', 'whispers', 'whispering', 'whispered', 'murmur', 'speak softly'])
def test_soft_speech_is_neither_shouting_nor_silence(query, dictionary):
    from aussiefy import Translator
    result = lookup(query,translator=Translator(dictionary,lookup_embedder='bundled'),level=5,vulgarity=1,limit=50)
    assert result['outcome'] == 'not_in_dictionary'
    assert result['results'] == []


@pytest.mark.parametrize('query,forbidden', [('tiny',{'HUGE'}),('cheap',{'EXPENSIVE'}),('expensive',{'DIRT_CHEAP','CHEAP_WINE'})])
def test_known_antonyms_cannot_be_inferred_from_model_similarity(query, forbidden, dictionary):
    from dataclasses import replace
    from aussiefy import Translator
    from aussiefy.lookup import _LookupBatch
    class TopicOnly:
        lookup_threshold = .5
        def similarity(self, a, b):
            return 1.0
    for model in ('bundled', TopicOnly()):
        tr = Translator(dictionary,lookup_embedder=model)
        results = lookup(query,translator=tr,level=5,vulgarity=1,limit=100)['results']
        assert not any(forbidden.intersection(entry['concepts']) and entry['match_kind'] == 'model' for entry in results)
        # Force retrieval to inspect the contrary senses, beyond ordinary result truncation.
        entries = {eid:e for eid,e in dictionary.entries.items() if forbidden.intersection(e.concept)}
        small = Translator(replace(dictionary,entries=entries),lookup_embedder=model)
        assert not lookup(query,translator=small,level=5,vulgarity=1,limit=100)['results']
        batch = _LookupBatch(small,level=5,vulgarity=1,embellishment=None,document_type='general',
                             document_config=None,include_gated=False)
        assert batch.entry_ids(query) == set()


@pytest.mark.parametrize('query,expected', [('scream','SCREAM'),('keep quiet','KEEP_QUIET'),
                                          ('inexpensive','DIRT_CHEAP'),('expensive','EXPENSIVE'),('enormous','HUGE')])
def test_true_sides_and_explicit_terms_still_work(query, expected, dictionary):
    from aussiefy import Translator
    result = lookup(query,translator=Translator(dictionary,lookup_embedder='bundled'),vulgarity=1,limit=50)
    assert any(expected in entry['concepts'] for entry in result['results'])


def test_contrasts_are_sense_scoped_and_negation_does_not_assert_a_pole(dictionary):
    from aussiefy.lookup import _model_contrasts
    from aussiefy.text import tokenize
    assert _model_contrasts(tokenize('tiny'), dictionary) == {'HUGE'}
    assert not _model_contrasts(tokenize('not tiny'), dictionary)
    assert not _model_contrasts(tokenize('tiny and enormous'), dictionary)
    # A direct term containing an antonym still explains itself (the drinks sense of shout).
    assert any(entry['id'] == 'your-shout' for entry in lookup('your shout')['results'])


@pytest.mark.parametrize('bad', [
    {'speech':[{'words':['whisper'],'concepts':['MISSING']},{'words':['shout'],'concepts':[]}]},
    {'speech':[{'words':['whisper'],'concepts':[]},{'words':['whisper'],'concepts':[]}]},
    {'speech':[{'words':['whisper'],'concepts':[]}]},
])
def test_bad_contrasts_fail_at_the_dictionary_boundary(dictionary,bad):
    from aussiefy.loader import _lookup_contrasts
    from aussiefy.schema import SchemaError
    with pytest.raises(SchemaError,match='lookup-contrasts'):
        _lookup_contrasts(bad,dictionary.concepts)


@pytest.mark.parametrize('backend', [None, 'bundled'])
@pytest.mark.parametrize('query', ['tiny', 'small', 'Tiny!', '(small)'])
def test_a_quality_word_does_not_infer_a_small_entity(dictionary,backend,query):
    from aussiefy import Translator,harness
    out = harness.lookup(query=query,level=5,vulgarity=1,translator=Translator(dictionary,lookup_embedder=backend))
    assert out['outcome'] == 'not_in_dictionary' and out['results'] == []


@pytest.mark.parametrize('backend', [None, 'bundled'])
@pytest.mark.parametrize('query', ['loud', 'Loud!'])
def test_loud_does_not_infer_a_lout_or_a_driver_from_its_description(dictionary,backend,query):
    from aussiefy import Translator,harness
    out = harness.lookup(query=query,level=5,vulgarity=1,limit=50,translator=Translator(dictionary,lookup_embedder=backend))
    ids = {entry['id'] for entry in out['results']}
    assert ids <= {'lairy'}
    if query == 'loud':
        assert ids == {'lairy'}
    assert all(entry['concepts'] == ['SHOWY'] for entry in out['results'])


@pytest.mark.parametrize('query,wanted', [('huge','whopping'),('a small child','littlie'),('child','little-bugger'),
                                        ('little','little-tacker'),('sad','face-like-a-wet-week')])
def test_kind_checks_keep_quality_entity_and_direct_term_discovery(dictionary,query,wanted):
    from aussiefy import Translator,harness
    out = harness.lookup(query=query,level=5,vulgarity=1,limit=50,translator=Translator(dictionary,lookup_embedder='bundled'))
    assert wanted in {entry['id'] for entry in out['results']}


def test_model_kind_is_the_source_sense_not_the_idioms_surface_frame(dictionary):
    from dataclasses import replace
    from aussiefy import Translator
    class Similar:
        lookup_threshold=.5
        def similarity(self,a,b):return .99
    quality = replace(dictionary.entries['whopping'],frame='np',form='a mountain of a thing')
    child = dictionary.entries['little-bugger']
    d = replace(dictionary,adjectives=dictionary.adjectives|{'gargantuan'},entries={quality.id:quality,child.id:child})
    out = lookup('gargantuan',translator=Translator(d,lookup_embedder=Similar()),vulgarity=1)
    assert {entry['id'] for entry in out['results']} == {'whopping'}
    assert out['results'][0]['frame'] == 'np'


def test_a_wrong_kind_gloss_cannot_rescue_another_meaning_path(dictionary):
    from dataclasses import replace
    from aussiefy import Translator
    class DescribesAChild:
        lookup_threshold=.5
        def similarity(self,a,b):return .99 if 'child' in b.lower() else 0
    mixed = replace(dictionary.entries['little-bugger'],concept=('CHILD','HUGE'))
    d = replace(dictionary,adjectives=dictionary.adjectives|{'gargantuan'},entries={mixed.id:mixed})
    assert not lookup('gargantuan',translator=Translator(d,lookup_embedder=DescribesAChild()),vulgarity=1)['results']


def test_qualified_quality_fragments_do_not_become_entity_queries(dictionary):
    from dataclasses import replace
    from aussiefy import Translator
    class Similar:
        lookup_threshold=.5
        def similarity(self,a,b):return .99
    child = dictionary.entries['little-bugger']
    degree = dictionary.entries['dead-adv']
    tr = Translator(replace(dictionary,entries={child.id:child,degree.id:degree}),lookup_embedder=Similar())
    for query in ['tiny','very tiny','really very small','a bit small','loud','extremely loud']:
        assert not lookup(query,translator=tr,vulgarity=1)['results'],query
    assert lookup('a small child',translator=tr,vulgarity=1)['results']
