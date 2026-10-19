"""Lookup inference respects established meaning paths while direct dictionary discovery stays broad."""

import pytest

from aussiefy import Translator, harness, load_dictionary
from aussiefy.lookup import _scoped_query
from aussiefy.detect import detect, resolve_overlaps
from aussiefy import pos
from aussiefy.text import tokenize


@pytest.fixture(params=['none', 'bundled'])
def translator(dictionary, request):
    return Translator(dictionary, lookup_embedder=request.param)


def results(tr, query, **options):
    return harness.lookup(query, translator=tr, level=5, vulgarity=3, limit=100, **options)['results']


def concepts(found):
    return {c for row in found for c in row['concepts']}


@pytest.mark.parametrize('query', ['probably', 'wake up', 'hard to finish', 'not out of the question'])
def test_recognised_meanings_without_a_certified_equivalent_abstain(translator, query):
    assert not results(translator, query)


def test_hard_work_does_not_retrieve_agitation_or_other_work_senses(translator):
    found = results(translator, 'worked hard')
    assert found
    assert all('WORK_HARD' in r['concepts'] for r in found)
    assert not any(r['id'] == 'het-up' for r in found)


@pytest.mark.parametrize('query,entry', [('a can of beer', 'tinnie'),
    ('a small bottle of beer', 'stubby'), ('a cold one at the pub', 'coldie')])
def test_container_and_drink_senses_remain_distinct(translator, query, entry):
    assert {r['id'] for r in results(translator, query)} == {entry}


@pytest.mark.parametrize('query,band', [('very hungry', 'strong'), ('slightly hungry', 'mild'),
    ('a very hungry man', 'strong')])
def test_inferred_appetite_choices_obey_reviewed_degree(translator, query, band):
    found = [r for r in results(translator, query) if 'HUNGRY' in r['concepts']]
    assert found
    assert all(translator.dictionary.entries[r['id']].semantic_degree.get('HUNGRY') == band for r in found)


@pytest.mark.parametrize('query', ['not drunk', 'not tired'])
def test_a_second_concept_cannot_rescue_an_unsupported_negated_sense(translator, query):
    denied = 'DRUNK' if query == 'not drunk' else 'TIRED'
    assert all(denied not in r['concepts'] for r in results(translator, query))


@pytest.mark.parametrize('query', ['not drunk but tired', 'not tired yesterday but tired today'])
def test_an_independent_positive_occurrence_supplies_its_own_meaning_path(translator, query):
    found = results(translator, query)
    assert any(r['id'] == 'stonkered' for r in found)
    assert 'TIRED' in concepts(found)


@pytest.mark.parametrize('query,wanted', [('a tired man', {'TIRED'}), ('a very busy man', {'BUSY'}),
    ('hungry and thirsty', {'HUNGRY', 'THIRSTY'})])
def test_modifiers_and_coordinated_fragments_keep_their_meanings(translator, query, wanted):
    assert wanted <= concepts(results(translator, query))


@pytest.mark.parametrize('query', ['crook', 'rooted', 'do the hard yards', 'coves', 'playing up', 'kip'])
def test_explicit_inflected_and_partial_term_discovery_remains_available(translator, query):
    assert any(not r['match'].startswith('meaning') for r in results(translator, query))


@pytest.mark.parametrize('query,expected', [
    ('probably', {'PROBABLE'}), ('wake up', {'WAKE_UP'}),
    ('hard to finish', {'DIFFICULT'}), ('a cold one at the pub', {'COLD_BEER_SERVING'}),
    ('a melancholy man', None), ('very beautiful', None), ('very large', None),
    ('hungry and inexplicably melancholy', None), ('want some food', None),
])
def test_query_scope_does_not_treat_an_incidental_reading_as_the_whole_query(dictionary, query, expected):
    ts = tokenize(query)
    tags = pos.tag([t.text for t in ts])
    readings = resolve_overlaps(detect(ts, dictionary.index, concepts=dictionary.concepts,
        adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index, fragment=True))
    assert _scoped_query(ts, readings, tags) == expected


def test_unknown_modifier_retains_model_fallback_instead_of_a_man_only_veto(dictionary):
    class Model:
        lookup_threshold = .5

        def similarity(self, query, text):
            return .99 if 'sad' in text.lower() else 0

    found = results(Translator(dictionary, lookup_embedder=Model()), 'a melancholy man')
    assert 'SAD' in concepts(found)


def test_new_work_source_trigger_keeps_automatic_complements_intact(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    config = {'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
                          'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}}
    for source in ('I worked hard.', 'I am working hard.', 'I have worked hard.', 'I worked hard and completed the job.'):
        result = tr.translate(source, level=5, vulgarity=3, embellishment=0, embedder='none', document_config=config)
        assert any(r.substituted and 'WORK_HARD' in r.det.concepts for r in result.records)
    for source in ('I worked hard enough to finish the job.', 'I worked hard to finish the job.',
                   'I worked hard after the meeting.'):
        result = tr.translate(source, level=5, vulgarity=3, embellishment=0, embedder='none', document_config=config)
        assert not any(r.substituted and 'WORK_HARD' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('query,denied', [('not a tired man', 'TIRED'), ('not a good man', 'GOOD_PERSON'),
    ('not excellent', 'GREAT_EXCLAIM'), ('not great', 'GREAT_EXCLAIM')])
def test_external_negation_applies_before_determiners_and_across_source_frames(translator, query, denied):
    assert all(denied not in r['concepts'] for r in results(translator, query))


@pytest.mark.parametrize('query', ['a sick man with a tired dog', 'happy although tired'])
def test_complements_cannot_swallow_other_recognised_predicates(dictionary, query):
    ts = tokenize(query)
    tags = pos.tag([t.text for t in ts])
    readings = resolve_overlaps(detect(ts, dictionary.index, concepts=dictionary.concepts,
        adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index, fragment=True))
    assert _scoped_query(ts, readings, tags) is None


def test_coordinated_head_scope_includes_owned_degree_qualifiers(dictionary):
    ts = tokenize('very drunk and slightly hungry')
    tags = pos.tag([t.text for t in ts])
    readings = resolve_overlaps(detect(ts, dictionary.index, concepts=dictionary.concepts,
        adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index, fragment=True))
    assert _scoped_query(ts, readings, tags) == {'DRUNK', 'HUNGRY'}


@pytest.mark.parametrize('query,wanted', [('not bad', 'NOT_BAD'), ('not working', 'BROKEN')])
def test_negation_inside_an_established_source_phrase_is_part_of_its_meaning(translator, query, wanted):
    assert wanted in concepts(results(translator, query))


def test_a_negative_spelling_can_establish_a_positive_meaning_with_new_dictionary_data(tmp_path):
    import yaml
    path = tmp_path / 'possible.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1', 'add_entries': [
        {'id': 'test-possible', 'form': 'testpossible', 'concept': ['POSSIBILITY'], 'frame': 'predicate_adj'}]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    assert any(r['id'] == 'test-possible' for r in results(tr, 'not impossible'))
    assert not any(r['id'] == 'test-possible' for r in results(tr, 'not not impossible'))


def test_known_meaning_without_an_equivalent_explains_abstention(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    known = harness.lookup('probably', translator=tr)
    unknown = harness.lookup('zzqqxx', translator=tr)
    assert 'no compatible suggestion' in known['note']
    assert 'unvetted' not in known['note']
    assert 'unvetted' in unknown['note']


def test_lookup_only_meanings_remain_discoverable_without_becoming_automatic(tmp_path):
    import yaml
    path = tmp_path / 'discovery.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'TEST_DISCOVERABLE': {'description': 'A lookstate for dictionary discovery only.',
            'lookup_only': True, 'unless_after': ['for'], 'triggers': {'predicate_adj': ['lookstate']}}},
        'add_entries': [{'id': 'test-discoverable', 'form': 'lookword', 'concept': ['TEST_DISCOVERABLE'],
                         'frame': 'predicate_adj'}]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    assert any(r['id'] == 'test-discoverable' for r in results(tr, 'lookstate'))
    translated = tr.translate('She is lookstate.', level=5, embedder='none')
    assert not any('TEST_DISCOVERABLE' in r.det.concepts for r in translated.records)


@pytest.mark.parametrize('query', ['hard at work', 'a hard drive', 'She is hard.'])
def test_ambiguous_hard_without_an_infinitive_does_not_establish_difficulty(dictionary, query):
    ts = tokenize(query)
    readings = detect(ts, dictionary.index, concepts=dictionary.concepts,
        adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index, fragment=True)
    assert not any('DIFFICULT' in r.concepts for r in readings)
