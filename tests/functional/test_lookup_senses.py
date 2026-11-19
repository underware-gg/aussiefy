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
