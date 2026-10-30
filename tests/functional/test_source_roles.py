"""Source-role evidence survives without word-class fences and is shared by discovery."""

from dataclasses import replace

import pytest

from aussiefy import Translator
from aussiefy.detect import read_meanings
from aussiefy.lookup import lookup
from aussiefy.matcher import PatternIndex
from aussiefy.text import tokenize


@pytest.fixture
def without_grammar_fences(dictionary):
    patterns = [p for p in dictionary.patterns if p.fence is None or p.fence.kind != 'grammar']
    return replace(dictionary, patterns=patterns, index=PatternIndex(patterns))


@pytest.mark.parametrize('text,cid,entry', [
    ('He thanked his fellow Texans.', 'FELLOW_MAN', 'bloke'),
    ('The room stays cooler.', 'COOLER', 'esky'),
    ('The room was much cooler.', 'COOLER', 'esky'),
    ('They expected cooler times.', 'COOLER', 'esky'),
    ('They expected cooler hours.', 'COOLER', 'esky'),
    ('The room keeps cooler.', 'COOLER', 'esky'),
    ('The room grew cooler.', 'COOLER', 'esky'),
    ('They expected cooler, drier weather.', 'COOLER', 'esky'),
    ('A cooler, drier day follows.', 'COOLER', 'esky'),
    ('He thanked his fellow respected members.', 'FELLOW_MAN', 'bloke'),
])
def test_adjective_evidence_rules_out_noun_senses(without_grammar_fences, text, cid, entry):
    dictionary = without_grammar_fences
    interpreted = read_meanings(tokenize(text), dictionary)
    assert cid in interpreted.ruled_out
    assert cid not in {c for det in interpreted.detections for c in det.concepts}
    tr = Translator(dictionary, lookup_embedder=None)
    assert entry not in {r['id'] for r in lookup(text, translator=tr)['results']}
    result = tr.translate(text, level=5, vulgarity=3, embellishment=0, embedder='none')
    assert not any(cid in rec.det.concepts for rec in result.records)


@pytest.mark.parametrize('text,word,role', [
    ('They carried a cooler.', 'cooler', 'head'),
    ('The football match starts soon.', 'football', 'modifier'),
    ('They ate chocolate biscuits.', 'chocolate', 'modifier'),
    ("She made her grandmother's bed.", 'grandmother', 'possessor'),
    ('She made her grandmother’s bed.', 'grandmother', 'possessor'),
])
def test_nominal_roles_do_not_impose_a_compound_ban(dictionary, text, word, role):
    tokens = tokenize(text)
    readings = read_meanings(tokens, dictionary).detections
    reading = next(d for d in readings if tokens[d.end - 1].norm == word)
    assert reading.nominal_role == role


def test_adjective_vocabulary_requires_words(data_copy):
    import yaml
    from aussiefy import load_dictionary
    from aussiefy.schema import SchemaError

    path = data_copy / 'grammar.yaml'
    raw = yaml.safe_load(path.read_text())
    raw['adjectives'] = ['cool', 1]
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match='adjectives must list lower-case words'):
        load_dictionary(data_dir=data_copy)


def test_a_rejected_sense_does_not_suppress_another_valid_occurrence(without_grammar_fences):
    tokens = tokenize('The room stays cooler but they brought a cooler.')
    readings = read_meanings(tokens, without_grammar_fences)
    matches = [d for d in readings.detections if 'COOLER' in d.concepts]
    assert len(matches) == 1
    assert tokens[matches[0].start - 1].norm == 'a'
    assert matches[0].nominal_role == 'head'


@pytest.mark.parametrize('description', ['shy', 'quiet', 'modest'])
def test_reserved_retiring_is_a_distinct_source_sense(dictionary, description):
    text = f'She is {description} and retiring.'
    assert 'RETIRE' not in {cid for d in read_meanings(tokenize(text), dictionary).detections for cid in d.concepts}
    assert 'pull-the-pin' not in {r['id'] for r in lookup(text, translator=Translator(dictionary, lookup_embedder=None))['results']}
