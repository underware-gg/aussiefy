"""ED15 uses curated directed relations only at genuinely wordless source spots."""

from dataclasses import replace

import pytest

from aussiefy import Translator, lookup, translate_changes
from aussiefy.changes import Watch
from aussiefy.detect import read_meanings
from aussiefy.text import tokenize

OPTIONS = {'level': 5, 'vulgarity': 0, 'embedder': 'none',
           'document_config': {'garnish': [], 'profile': {'phonetic': 0, 'stack': 0,
               'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}}


@pytest.fixture
def wordless_translator(dictionary):
    """Exercise ED15's genuinely wordless condition after admitting an exact CRY word."""
    return Translator(replace(dictionary, entries={k: e for k, e in dictionary.entries.items()
                                                  if 'CRY' not in e.concept}), lookup_embedder=None)


@pytest.mark.parametrize('source,concept', [('She cried.', 'CRY'), ('She wept.', 'CRY'),
    ('She bawled.', 'NOISY_CRY'), ('She sobbed.', 'NOISY_CRY'), ('She cried loudly.', 'NOISY_CRY')])
def test_crying_source_distinguishes_the_narrower_noisy_meaning(dictionary, source, concept):
    readings = read_meanings(tokenize(source), dictionary).detections
    assert concept in {cid for reading in readings for cid in reading.concepts}
    if concept != 'CRY':
        assert 'CRY' not in {cid for reading in readings for cid in reading.concepts}


@pytest.mark.parametrize('source', ['The fox cried.', 'They cried wolf.', 'She cried for help.',
    "She cried, 'Stop!'", 'She cried, "Stop!"', "He bawled, 'Stop!'", 'She bawled him out.'])
def test_other_cries_and_reported_speech_do_not_create_crying(dictionary, source):
    readings = read_meanings(tokenize(source), dictionary).detections
    assert not {'CRY', 'NOISY_CRY'} & {cid for reading in readings for cid in reading.concepts}


@pytest.mark.parametrize('setting,probability', [(1, 0.5), (2, 0.75)])
def test_near_has_a_separate_probability_and_can_leave_a_held_spot(wordless_translator, setting, probability):
    applied = 0
    for seed in range(20):
        result = wordless_translator.translate('She wept.', **OPTIONS, seed=seed, embellishment=setting)
        rec = next(record for record in result.records if 'CRY' in record.det.concepts)
        assert rec.p == probability
        assert rec.roll is not None
        if rec.chosen:
            applied += 1
            assert rec.chosen.near.minimum <= setting
            assert rec.det.concepts == ('CRY',)
        else:
            assert rec.kind == 'held' and result.text == 'She wept.'
    assert 0 < applied < 20


@pytest.mark.parametrize('genre', ['news', 'instructions', 'technical', 'official', 'custom'])
def test_excluded_genres_do_not_use_near_even_at_troppo(wordless_translator, genre):
    for seed in range(3):
        result = wordless_translator.translate('She wept.', **OPTIONS, seed=seed, embellishment=2, document_type=genre)
        assert not any(record.chosen and record.chosen.near for record in result.records)
        assert any(record.kind == 'held' for record in result.records)


@pytest.mark.parametrize('source', ['She wept.', 'She wholeheartedly loved him.'])
def test_deadset_takes_no_near_word(wordless_translator, source):
    for seed in range(3):
        result = wordless_translator.translate(source, **OPTIONS, embellishment=0, seed=seed)
        assert result.text == source
        assert not any(record.chosen and record.chosen.near for record in result.records)


def test_exact_word_prevents_near_even_when_the_level_blocks_it(translator):
    source = 'I think highly of him.'
    for seed in range(3):
        result = translator.translate(source, **(OPTIONS | {'level': 1}), embellishment=2, seed=seed)
        assert not any(record.kind == 'held' or record.chosen and record.chosen.near for record in result.records)


@pytest.mark.parametrize('source,expected', [
    ('She loved him wholeheartedly.', 'She defo loved him.'),
    ('She wholeheartedly loved him.', 'She defo loved him.'),
    ('She has loved him wholeheartedly.', 'She has defo loved him.'),
    ('I agree wholeheartedly.', 'I defo agree.'),
])
def test_before_verb_grammar_keeps_the_existing_verb_and_object(translator, source, expected):
    result = translate_changes(source, translator=translator, **OPTIONS, embellishment=2, seed=0)
    assert result.text == expected
    changed = next(change for change in result.changes if change.get('near'))
    assert changed['reading']['concept'] == 'WHOLEHEARTED'
    assert changed['near']['concept'] == 'DEFINITELY'
    assert all(option.get('near', {}).get('concept') == 'DEFINITELY'
               for option in changed['alternatives'] if option['kind'] == 'entry')


def test_adoration_context_object_is_bound_and_not_replaced_by_self_regard(translator):
    watch = Watch()
    translator.translate('I think highly of him.', **(OPTIONS | {'vulgarity': 2}), embellishment=2, _observer=watch)
    spot = next(spot for spot in watch.spots if 'REGARD_HIGHLY' in spot.rec.det.concepts)
    reading = replace(spot.rec.det, concepts=('ADORE',), direct=set())
    eligible, _ = translator.eligible(reading, spot.sent, watch.run, watch.run.eff, spot.state, set(),
                                      translator.dictionary.idioms_for(('ADORE',)))
    assert eligible
    for candidate in eligible:
        assert candidate.reading.captures['obj'].norm == 'him'
        rendered = translator.render_at_spot(candidate, spot, watch.run)
        assert rendered.text == 'think the sun shines out of his arse'
        assert rendered.end == len(spot.sent.tokens) - 1


def test_waiting_lookup_shows_every_citation_at_deadset(wordless_translator):
    result = lookup('cry', translator=wordless_translator, level=5, vulgarity=0, embellishment=0)
    assert result['outcome'] == 'no_word_yet'
    crying = next(meaning for meaning in result['meanings'] if meaning['concept'] == 'CRY')
    assert {near['concept'] for near in crying['near']} == {'NOISY_CRY', 'INTENSE_NOISY_CRY', 'SULK'}
    for near in crying['near']:
        assert near['kind'] == 'near' and near['differs'] and near['setting'] in {'dinkum', 'troppo'}
        assert all(near['concept'] in entry['concepts'] for entry in near['words'])


def test_complete_replay_can_explicitly_keep_a_wordless_source(translator):
    initial = translator.translate('She wept.', **OPTIONS, embellishment=2, seed=0)
    packet = initial.replay_pins()
    packet['picks'] = []
    replay = translator.translate('She wept.', **OPTIONS, embellishment=2, seed=0, pins=packet)
    assert replay.text == 'She wept.'


def test_near_pick_replays_through_the_same_hard_gates(translator):
    initial = translator.translate('She loved him wholeheartedly.', **OPTIONS, embellishment=2, seed=0)
    packet = initial.replay_pins()
    replay = translator.translate(initial.source, **OPTIONS, embellishment=2, seed=0, pins=packet)
    assert replay.text == initial.text == 'She defo loved him.'
