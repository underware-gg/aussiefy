"""The fixed pilot's working examples and reviewed lexical units remain executable."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from aussiefy import Translator
from aussiefy.text import tokenize

RESEARCH = Path(__file__).parents[2] / 'research' / 'ed16-grammar-2026-10-30'
PILOT = json.loads((RESEARCH / 'pilot.json').read_text())
MIGRATION = json.loads((RESEARCH / 'exclusion-migration.json').read_text())


@pytest.mark.parametrize('row', PILOT['entries'], ids=lambda row: row['id'])
def test_fixed_pilot_examples(dictionary, row):
    engine = Translator(replace(dictionary, entries={row['id']: dictionary.entries[row['id']]}), lookup_embedder=None)
    settings = PILOT['settings'] | row.get('settings_override', {})
    positive = engine.translate(row['positive'], **settings)
    eligible = {c.entry.id for r in positive.records for c in r.eligible}
    assert row['id'] in eligible
    assert positive.text == row['trials']['positive']['text']
    contrast = engine.translate(row['contrast'], **settings)
    assert row['id'] not in {c.entry.id for r in contrast.records for c in r.eligible}


@pytest.mark.parametrize('source,expected', [('My father is here.', 'My old pot is here.'),
    ('His dad is here.', 'His old pot is here.'), ('Our fathers are here.', 'Our old pots are here.')])
def test_possessive_noun_patterns_preserve_the_owner_and_number(dictionary, source, expected):
    engine = Translator(replace(dictionary, entries={'old-pot': dictionary.entries['old-pot']}), lookup_embedder=None)
    assert engine.translate(source, registers=['current', 'dated', 'archaic'], **PILOT['settings']).text == expected
    assert not any(r.eligible for r in engine.translate(source, **PILOT['settings']).records)


@pytest.mark.parametrize('source', ['His father spoke quietly.', 'Our fathers brought the tools.'])
def test_a_known_noun_head_does_not_look_like_an_unfinished_adjective_phrase(dictionary, source):
    entries = {id: dictionary.entries[id] for id in ['old-fella', 'old-man']}
    engine = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    result = engine.translate(source, **PILOT['settings'])
    assert any(r.chosen for r in result.records)
    assert result.text.lower().startswith(source.split()[0].lower() + ' old ')


@pytest.mark.parametrize('row', MIGRATION['expanded_new_fences'], ids=lambda row: row['phrase'])
def test_migrated_units_match_as_whole_phrases(dictionary, row):
    tokens = tokenize(row['phrase'])
    assert any(m.start == 0 and m.end == len(tokens) and m.pattern.fence is not None
               for m in dictionary.index.find(tokens))


@pytest.mark.parametrize('source,expected', [
    ("I'm eager to see it.", "I'm hanging out to see it."),
    ('She was eager for the weekend.', 'She was hanging out for the weekend.'),
])
def test_hanging_out_keeps_verb_tense_and_one_complement(dictionary, source, expected):
    entries = {id: dictionary.entries[id] for id in ['hang-out-for', 'hang-out-to']}
    engine = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    assert engine.translate(source, **PILOT['settings']).text == expected


@pytest.mark.parametrize('source', ['He is eager.', 'She is eager for', 'They are hanging out with mates.',
                                  "She wasn't eager for the weekend."])
def test_hanging_out_requires_anticipation_and_an_established_complement(dictionary, source):
    entries = {id: dictionary.entries[id] for id in ['hang-out-for', 'hang-out-to']}
    engine = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    result = engine.translate(source, **PILOT['settings'])
    assert not any(r.eligible for r in result.records)


def test_emotional_heart_expression_keeps_the_body_part_word(dictionary):
    engine = Translator(dictionary, lookup_embedder=None)
    source = 'It had gone to his heart to leave them alone.'
    result = engine.translate(source, **PILOT['settings'])
    assert 'heart' in result.text and 'ticker' not in result.text
    assert not any(c.entry.id == 'ticker' for r in result.records for c in r.eligible)


@pytest.mark.parametrize('id,source,protected', [
    ('a-public-servant', 'She is a civil servant.', 'public servant'),
    ('the-public-service', 'She joined the civil service.', 'public service'),
])
@pytest.mark.parametrize('enabled', [True, False])
def test_public_service_fences_protect_components_without_blocking_whole_outputs(dictionary, id, source, protected, enabled):
    entry = dictionary.entries[id]
    entries = {**dictionary.entries, id: replace(entry, status='active' if enabled else 'omit')}
    engine = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    result = engine.translate(source, **PILOT['settings'])
    assert any(r.chosen and r.chosen.entry.id == id for r in result.records) is enabled
    literal = engine.translate(f'They discussed the {protected}.', **PILOT['settings'])
    assert protected in literal.text
    assert not any('PEOPLE' in r.det.concepts for r in literal.records)
