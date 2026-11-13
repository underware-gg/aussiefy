"""R64 foundation: display, sentence forms and exact search remain separate."""

from dataclasses import replace

import pytest
import yaml

from aussiefy import Translator, load_dictionary, lookup
from aussiefy.detect import read_meanings
from aussiefy.schema import SchemaError, parse_concept, parse_entry
from aussiefy.text import tokenize


def test_concept_wording_defaults_and_owned_input():
    assert parse_concept('TEST', {}).search_words == ()
    assert parse_concept('TEST', {}).plain_forms == {}
    raw = {'plain': "believe what you're told", 'search_words': ['take as true'],
           'plain_forms': {'vp': 'believe'}}
    concept = parse_concept('TEST', raw)
    raw['plain_forms']['vp'] = 'change'
    raw['search_words'].append('change')
    assert concept.plain_forms == {'vp': 'believe'}
    assert concept.search_words == ('take as true',)


@pytest.mark.parametrize('patch', [
    {'search_words': 'remorse'}, {'search_words': [1]}, {'search_words': ['']},
    {'search_words': [' remorse']}, {'search_words': ['one\ntwo']},
    {'search_words': ['remorse', 'REMORSE']},
    {'plain_forms': []}, {'plain_forms': {'unknown': 'word'}},
    {'plain_forms': {'vp': ''}}, {'plain_forms': {'vp': 1}},
    {'plain_forms': {'vp': '<b>believe</b>'}}, {'plain_forms': {'vp': '{unknown}'}},
    {'plain_forms': {'vp': '{obj'}}, {'plain_forms': {'vp': 'do; act'}},
    {'plain_forms': {'vp': 'one\ntwo'}}, {'plain_forms': {'vp': '{subj} believe'}},
])
def test_concept_wording_rejects_malformed_fields(patch):
    with pytest.raises(SchemaError):
        parse_concept('TEST', patch)


def test_overlay_search_words_find_the_meaning_without_becoming_source_triggers(tmp_path):
    path = tmp_path / 'wording.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1', 'patch_concepts': {
        'FANCIFUL': {'search_words': ['reviewed wonder words'], 'plain_forms': {'adj': 'imaginary'}}}}))
    d = load_dictionary([path])
    tr = Translator(d, lookup_embedder=None)
    result = lookup('REVIEWED WONDER WORDS', translator=tr)
    assert result['outcome'] == 'no_word_yet'
    assert {m['concept'] for m in result['meanings']} == {'FANCIFUL'}
    assert d.concepts['FANCIFUL'].plain_forms == {'adj': 'imaginary'}
    assert 'FANCIFUL' not in {c for r in read_meanings(tokenize('Reviewed wonder words.'), d).detections
                             for c in r.concepts}
    assert 'imaginary' not in d.named_meanings
    assert 'wonder words' not in d.named_meanings


def test_exact_display_name_reaches_its_word_without_a_component_reading_defeating_it(dictionary):
    concepts = {**dictionary.concepts, 'FOREST': replace(dictionary.concepts['FOREST'], plain='wooded country')}
    tr = Translator(replace(dictionary, concepts=concepts), lookup_embedder=None)
    result = lookup('wooded country', translator=tr, level=5, vulgarity=0)
    assert result['outcome'] == 'matched'
    assert 'the-bush' in {r['id'] for r in result['results']}
    assert all('FOREST' in r['concepts'] for r in result['results'])


@pytest.mark.parametrize('cid,frame,form,source,expected', [
    ('ACCEPT_AS_TRUE', 'vp', 'believe', 'I believe the story.', 'I believe the story.'),
    ('FEEL_SORRY', 'vp', 'feel bad', 'She felt awful about lying.', 'She felt bad about lying.'),
    ('ERRATIC_THINKING', 'clause', '{subj} {be} going round in circles',
     'I am thinking in circles.', 'I am going round in circles.'),
])
def test_sentence_forms_use_the_shared_renderer_without_changing_display_or_search(dictionary, cid, frame, form, source, expected):
    concept = parse_concept(cid, {'plain': 'a separate display name', 'plain_forms': {frame: form}})
    entry = parse_entry({'id': 'plain-test', 'form': concept.plain_forms[frame], 'frame': frame,
                         'concept': [cid], 'reads_as': 'general', 'incoherence': 1})
    d = replace(dictionary, entries={entry.id: entry})
    tr = Translator(d, lookup_embedder=None)
    result = tr.translate(source, level=5, vulgarity=0, embellishment=0, english='none',
        document_config={'garnish': [], 'profile': {'phonetic': 0,
        'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    assert result.text == expected
    assert any(r.chosen and r.chosen.entry.id == entry.id for r in result.records)
    assert concept.plain == 'a separate display name' and not concept.search_words


@pytest.mark.parametrize('query', ['think in circles','I am thinking in circles.'])
@pytest.mark.parametrize('level,step', [(1,0),(5,0),(5,2)])
def test_imagery_does_not_hide_a_wordless_meaning_but_remains_discoverable(dictionary,query,level,step):
    tr=Translator(dictionary,lookup_embedder=None)
    result=lookup(query,translator=tr,level=level,vulgarity=0,embellishment=step)
    assert result['outcome']=='no_word_yet'
    assert {m['concept'] for m in result['meanings']}=={'ERRATIC_THINKING'}
    if level==5 and step==2:
        assert 'country-racetrack-mind' in {image['id'] for image in result['imagery']}
    else:
        assert not result.get('imagery')
