"""Approved ED16 meanings, source-context grammar and evidence boundaries."""

from dataclasses import replace

import pytest
import yaml

from aussiefy import Translator, load_dictionary, lookup
from aussiefy.detect import read_meanings
from aussiefy.matcher import compile_pattern, match_at
from aussiefy.schema import Entry, SchemaError
from aussiefy.text import tokenize

WAITING = {'HEARTBREAK', 'FREEDOM', 'FEEL_SORRY', 'UNEMPLOYED', 'GET_EXCITED', 'GIFT_TALENT'}
EVERY_SWAP = {'level': 5, 'vulgarity': 0, 'embellishment': 0, 'embedder': 'none',
              'document_type': 'custom', 'document_config': {'profile': {'phonetic': 0,
              'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}}


@pytest.mark.parametrize('cid', sorted(WAITING))
def test_approved_meanings_wait_through_their_plain_wording_and_examples(dictionary, cid):
    tr = Translator(dictionary, lookup_embedder=None)
    concept = dictionary.concepts[cid]
    assert cid in dictionary.wordless_meanings and concept.plain and concept.examples
    for query in (concept.plain, *concept.examples):
        result = lookup(query, translator=tr)
        assert result['outcome'] == 'no_word_yet'
        assert cid in {m['concept'] for m in result['meanings']}
    for sentence in concept.examples:
        assert cid in {cid for d in read_meanings(tokenize(sentence), dictionary).detections for cid in d.concepts}


def test_a_real_word_can_now_express_heartbreak(dictionary):
    entry = Entry('test-heartache', 'heartache', ('HEARTBREAK',), 'np')
    assert 'HEARTBREAK' not in replace(dictionary, entries={**dictionary.entries, entry.id: entry}).wordless_meanings


@pytest.mark.parametrize('marker', [True, False])
def test_core_concepts_cannot_reintroduce_no_entries(tmp_path, marker):
    path = tmp_path / 'overlay.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'patch_concepts': {'HEARTBREAK': {'no_entries': marker}}}))
    with pytest.raises(SchemaError, match='unknown fields.*no_entries'):
        load_dictionary([path])


@pytest.mark.parametrize('source,expected', [
    ("I'm dying to see it.", "I'm keen to see it."),
    ('She is dying for a holiday.', 'She is keen for a holiday.'),
    ('They were dying to help.', 'They were keen to help.'),
])
def test_eagerness_keeps_its_complement_and_strong_reading(translator, source, expected):
    for seed in range(8):
        result = translator.translate(source, seed=seed, **EVERY_SWAP)
        assert result.text in {expected, expected.replace('keen', 'hanging out')}
        reading = next(r.det for r in result.records if 'EAGER' in r.det.concepts)
        assert reading.intensity == 4


def test_drink_reading_and_actual_death_remain_distinct(translator):
    thirst = translator.translate("I'm dying for a drink.", **EVERY_SWAP)
    assert any('THIRSTY' in r.det.concepts for r in thirst.records)
    assert not any('EAGER' in r.det.concepts for r in thirst.records)
    death = translator.translate('He is dying.', **EVERY_SWAP)
    assert any('DIE' in r.det.concepts for r in death.records)
    assert not any('EAGER' in r.det.concepts for r in death.records)


def test_gift_of_the_gab_is_a_fence_not_a_talent_or_present(dictionary):
    found = read_meanings(tokenize('He has the gift of the gab.'), dictionary).detections
    assert not {'GIFT', 'GIFT_TALENT'} & {c for d in found for c in d.concepts}
    assert any(d.source_pattern.fence is not None for d in found)


def test_hanging_out_terms_keep_their_grammar_and_publisher_weight(dictionary):
    for eid, score in [('hang-out-for', 7), ('hang-out-to', 3)]:
        entry = dictionary.entries[eid]
        assert entry.concept == ('EAGER',) and entry.frame == 'predicate_adj'
        assert entry.form == 'hanging out' and entry.status == 'active'
        assert entry.grammar.following == (('prep:for',) if eid.endswith('for') else ('infinitive',))
        assert entry.evidence == 'unverified' and entry.attestation.score == score
    tr = Translator(dictionary, lookup_embedder=None)
    result = tr.translate('He is eager.', **EVERY_SWAP)
    assert result.text == 'He is keen.'
    offers = lookup('eager', translator=tr, include_gated=True, limit=100)
    assert {'hang-out-for', 'hang-out-to'} <= {row['id'] for row in offers['results']}


def test_other_verb_forms_remain_known_eagerness_without_forcing_a_wrong_frame(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    result = tr.translate("I'd die to see it.", **EVERY_SWAP)
    assert result.text == "I'd die to see it."
    assert any('EAGER' in r.det.concepts for r in result.records)
    assert lookup('die to', translator=tr)['outcome'] == 'matched'


@pytest.mark.parametrize('pattern,source,start,end,context', [
    ('wish ?=for+a', 'wish for a break', 0, 1, (0, 3)),
    ('wish ?=to|for+a', 'wish to go', 0, 1, (0, 2)),
    ('wish ?=for|for+a', 'wish for a break', 0, 1, (0, 3)),
    ('?<=we+all wish', 'we all wish', 2, 3, (0, 3)),
])
def test_literal_context_sequences_read_without_consuming(pattern, source, start, end, context):
    match = match_at(compile_pattern(pattern, 'vp', ('TEST',), 3), tokenize(source), start)
    assert match is not None
    assert (match.start, match.end, match.context) == (start, end, context)


@pytest.mark.parametrize('source', ['wish for', 'wish for the break', 'wish for, a break'])
def test_literal_sequences_do_not_guess_missing_or_interrupted_context(source):
    assert match_at(compile_pattern('wish ?=for+a', 'vp', ('TEST',), 3), tokenize(source), 0) is None


@pytest.mark.parametrize('pattern', ['wish ?=for++a', 'wish ?=+for', 'wish ?<=we+'])
def test_malformed_literal_sequences_are_rejected(pattern):
    with pytest.raises(ValueError, match='nonempty words'):
        compile_pattern(pattern, 'vp', ('TEST',), 3)
