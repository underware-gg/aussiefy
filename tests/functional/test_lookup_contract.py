"""Discovery explains protected wording without turning rejected guesses into readings."""

from dataclasses import replace

import pytest

from aussiefy import Translator, lookup
from aussiefy import discovery_outcomes as outcomes
from aussiefy.explore import get_entry, list_entries, list_wordless_meanings, random_entry, suggest_name
from aussiefy.bulldust import variations
from aussiefy.fences import parse_fences
from aussiefy.matcher import PatternIndex


class NoModel:
    lookup_threshold = .5

    def similarity(self, *args):
        raise AssertionError('A protected or wordless reading does not need model guesses')


def test_protected_phrase_returns_its_current_reason_and_actual_reading(dictionary):
    tr = Translator(dictionary, lookup_embedder=NoModel())
    out = lookup('national forest', translator=tr)
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN and out['results'] == []
    assert out['dictionary_id'] == dictionary.identity
    protection, = out['protections']
    fence = next(f for f in dictionary.fences if f.phrase == 'national forest')
    assert protection['reason'] == fence.reason
    assert protection['reason'] == out['note'] == ''
    assert protection['span'] == [0, 15] and protection['original'] == 'national forest'
    assert out['ruled_out'] == protection['ruled_out']
    reading, = out['ruled_out']
    assert reading['kind'] == 'meaning' and reading['concept'] == 'FOREST'
    assert any(word['id'] == 'the-bush' for word in reading['words'])
    assert all('sources' in word and 'attestation' in word for word in reading['words'])


def test_intentionally_kept_protection_has_no_invented_reading(dictionary):
    out = lookup('a people', translator=Translator(dictionary, lookup_embedder=NoModel()))
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert not out['ruled_out'] and not out['protections'][0]['ruled_out']
    assert out['note'] == out['protections'][0]['reason']
    assert not out['results'] and 'meanings' not in out


@pytest.mark.parametrize('query,unrelated', [('gift shop', 'HORSE'), ('field notes', 'DAY'),
                                          ('field guide', 'HOSPITAL')])
def test_pattern_alternatives_cannot_lend_readings_to_other_phrases(query, unrelated, translator):
    out = lookup(query, translator=translator)
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert unrelated not in {row.get('concept') for row in out['ruled_out']}


def test_dialect_citations_respect_the_document_domain(dictionary):
    from aussiefy.dialect import DialectTable

    original = next(f for f in dictionary.fences if f.phrase == 'real estate agent')
    fence = replace(original, meanings=True, not_in=frozenset({'technical'}))
    fences = tuple(fence if f == original else f for f in dictionary.fences)
    patterns = [*dictionary.patterns, fence.pattern]
    custom = replace(dictionary, fences=fences, patterns=patterns, index=PatternIndex(patterns),
                     dialect=DialectTable(list(dictionary.dialect.swaps), dictionary.dialect.lint_only, fences))
    tr = Translator(custom, lookup_embedder=NoModel())
    general = lookup('real estate agent', translator=tr)
    technical = lookup('real estate agent', translator=tr, document_type='technical')
    assert general['outcome'] == technical['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert any(row['kind'] == 'dialect' for row in general['ruled_out'])
    assert not any(row['kind'] == 'dialect' for row in technical['ruled_out'])


def test_dialect_only_protection_identifies_the_guarded_swap(dictionary):
    out = lookup('real estate agent', translator=Translator(dictionary, lookup_embedder=NoModel()))
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert {'kind': 'dialect', 'english': 'uk', 'original': 'estate agent',
            'output': 'real estate agent'} in out['ruled_out']
    assert all('concept' not in row for row in out['ruled_out'])
    assert all(row['original'] == 'estate agent' for row in out['ruled_out'])
    plural = lookup('real estate agents', translator=Translator(dictionary, lookup_embedder=NoModel()))
    assert all(row['original'] == 'estate agents' and row['output'] == 'real estate agents'
               for row in plural['ruled_out'])


@pytest.mark.parametrize('query', ['fortune cookie', 'first-party cookie', 'eye candy', 'arm candy',
                                 'rock candy', 'tough cookie', 'smart cookie'])
def test_complete_dialect_protection_outranks_unscoped_component_guesses(query, dictionary):
    out = lookup(query, translator=Translator(dictionary, lookup_embedder=NoModel()))
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN and not out['results']
    assert out['protections'] and all(row['kind'] == 'dialect' for row in out['ruled_out'])


def test_unclear_source_is_not_a_meaning_waiting_for_a_word(dictionary):
    out = lookup('a gift for kindness', translator=Translator(dictionary, lookup_embedder=NoModel()))
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN and not out['ruled_out']
    assert 'unclear' in out['note'] and 'adding words' in out['note']
    assert 'meanings' not in out and not out['results']


@pytest.mark.parametrize('query', ['  national forest  ', '(national forest)', '"national forest"'])
def test_protected_spans_refer_to_the_original_query(query, translator):
    out = lookup(query, translator=translator)
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
    for protection in out['protections']:
        assert query[slice(*protection['span'])] == protection['original'] == 'national forest'


def test_independent_protections_are_kept_separate_and_readings_are_merged(translator):
    out = lookup('national forest and bottle of beer', translator=translator)
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert [row['original'] for row in out['protections']] == ['national forest', 'bottle of beer']
    assert {reading['concept'] for reading in out['ruled_out']} == {'FOREST', 'BEER'}


def test_an_incidental_protection_cannot_turn_the_whole_query_into_an_abstention(translator):
    out = lookup('national forest and hungry', translator=translator)
    assert out['outcome'] == outcomes.MATCHED
    assert 'protections' not in out
    assert any('HUNGRY' in word['concepts'] for word in out['results'])


def test_a_curated_whole_expression_still_explains_itself(translator):
    out = lookup("dog's breakfast", translator=translator)
    assert out['outcome'] == outcomes.MATCHED
    assert any(word['match_kind'] == 'term' for word in out['results'])
    assert 'protections' not in out


def test_wordless_outcome_and_named_ranking_remain_unchanged(dictionary):
    tr = Translator(dictionary, lookup_embedder=NoModel())
    out = lookup('fantastic terrors', translator=tr)
    assert out['outcome'] == outcomes.NO_WORD_YET and not out['results']
    assert out['dictionary_id'] == dictionary.identity


def _fatigue_protection(dictionary):
    fence, = parse_fences([{'phrase': 'they are very tired', 'frame': 'clause', 'kind': 'set_phrase',
                           'scope': {'meanings': True, 'dialect': [], 'not_in': []},
                           'reason': 'This wording is deliberately kept.'}])
    patterns = [*dictionary.patterns, fence.pattern]
    return replace(dictionary, fences=(*dictionary.fences, fence), patterns=patterns, index=PatternIndex(patterns))


def test_cached_evidence_is_filtered_again_for_each_request(dictionary, monkeypatch):
    from aussiefy import fence_readings

    tr = Translator(_fatigue_protection(dictionary), lookup_embedder=NoModel())
    wide = lookup('they are very tired', translator=tr, vulgarity=3, limit=100)
    assert wide['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert any(word['vulgarity'] for row in wide['ruled_out'] for word in row['words'])
    fence = next(f for f in tr.dictionary.fences if f.phrase == 'they are very tired')
    assert all(row.signature[0] == 'they' for row in tr.dictionary.fence_readings[fence].variants)

    def no_rebuild(*args):
        raise AssertionError('The same dictionary protection must not be re-derived')

    monkeypatch.setattr(fence_readings, '_derive_fence', no_rebuild)
    mild = lookup('they are very tired', translator=tr, vulgarity=0, limit=1)
    assert all(len(row['words']) <= 1 and all(word['vulgarity'] == 0 for word in row['words'])
               for row in mild['ruled_out'])
    empty = lookup('they are very tired', translator=tr, level=1, vulgarity=0)
    assert empty['outcome'] == outcomes.LEFT_AS_WRITTEN
    assert any(row['concept'] == 'TIRED' for row in empty['ruled_out'])


def test_evidence_does_not_leak_between_dictionary_instances(dictionary):
    first = lookup('bottle of beer', translator=Translator(dictionary, lookup_embedder=None))
    without = replace(dictionary, entries={eid: entry for eid, entry in dictionary.entries.items() if eid != 'amber-fluid'})
    second = lookup('bottle of beer', translator=Translator(without, lookup_embedder=None))
    assert any(word['id'] == 'amber-fluid' for row in first['ruled_out'] for word in row.get('words', []))
    assert not any(word['id'] == 'amber-fluid' for row in second['ruled_out'] for word in row.get('words', []))


def test_variant_evidence_normalises_captured_slots_without_losing_the_literal_unit(dictionary):
    fence, = parse_fences([{'phrase': 'a gift for {poss} father', 'frame': 'np', 'kind': 'set_phrase',
                           'scope': {'meanings': True, 'dialect': [], 'not_in': []},
                           'reason': 'This wording is deliberately kept.'}])
    patterns = [*dictionary.patterns, fence.pattern]
    custom = replace(dictionary, fences=(*dictionary.fences, fence), patterns=patterns, index=PatternIndex(patterns))
    tr = Translator(custom, lookup_embedder=NoModel())
    for poss in ['his', 'my', 'their']:
        out = lookup(f'a gift for {poss} father', translator=tr)
        assert out['outcome'] == outcomes.LEFT_AS_WRITTEN
        assert 'FATHER' in {row.get('concept') for row in out['ruled_out']}
    contextual, = parse_fences([{'phrase': 'believe ?={np}', 'frame': 'vp', 'kind': 'set_phrase',
                                'scope': {'meanings': True, 'dialect': [], 'not_in': []},
                                'reason': 'This wording is deliberately kept.',
                                'examples': ['believe the story', 'believe the liar']}])
    patterns = [*dictionary.patterns, contextual.pattern]
    custom = replace(dictionary, fences=(contextual,), patterns=patterns, index=PatternIndex(patterns))
    evidence = custom.fence_readings[contextual]
    assert any('story' in row.signature for row in evidence.variants)
    assert any('liar' in row.signature for row in evidence.variants)


def test_response_mutation_cannot_poison_the_cached_evidence(translator):
    first = lookup('national forest', translator=translator)
    first['ruled_out'][0]['words'][0]['form'] = 'poisoned response'
    second = lookup('national forest', translator=translator)
    assert all(word['form'] != 'poisoned response' for row in second['ruled_out'] for word in row['words'])


def test_rich_lookup_cards_match_entry_detail_and_report_default_placement(translator):
    out = lookup('very tired', vulgarity=2, translator=translator)
    for word in out['results']:
        detail = get_entry(word['id'], vulgarity=2, translator=translator)['entry']
        assert {key: value for key, value in word.items() if key not in {'score', 'match', 'match_kind'}} == detail
        assert all(isinstance(source, dict) for source in word['sources'])
        assert {'evidence', 'attestation', 'reads_as', 'held_back', 'minimum_vulgarity'} <= word.keys()
        assert word['minimum_vulgarity'] == max([word['vulgarity'], *(tag['tier'] for tag in word['themes'])])
    default = get_entry('dry-as-a-dead-dingo', vulgarity=1, translator=translator)['entry']
    override = get_entry('dry-as-a-dead-dingo', vulgarity=1, document_config={'themes': {'sex': True}},
                         translator=translator)['entry']
    assert default['themes'] == override['themes']
    assert default['minimum_vulgarity'] == override['minimum_vulgarity']


def test_match_codes_do_not_depend_on_display_text(translator):
    assert any(row['match_kind'] == 'term' for row in lookup('coves', translator=translator)['results'])
    phrase = next(row for row in lookup('kip', translator=translator, limit=100)['results']
                  if row['form'] == "been kippin' in")
    assert phrase['match_kind'] == 'phrase'
    assert all(row['match_kind'] in outcomes.MATCH_KINDS
               for row in lookup('very tired', short=True, translator=translator)['results'])


def test_image_lookup_uses_the_same_match_codes(translator):
    out = lookup('hungry', embellishment=2, vulgarity=3, translator=translator)
    assert out['imagery']
    assert all(row['match_kind'] in outcomes.MATCH_KINDS for row in out['imagery'])


def test_model_only_match_is_distinct_from_a_model_boost_to_an_exact_meaning(dictionary):
    target = dictionary.entries['knackered'].gloss

    class Model:
        lookup_threshold = .1

        def similarity(self, query, text):
            return 1 if text == target else 0

    tr = Translator(dictionary, lookup_embedder=Model())
    unfamiliar = lookup('quuxzor', translator=tr, limit=100)
    assert next(row for row in unfamiliar['results'] if row['id'] == 'knackered')['match_kind'] == 'model'
    familiar = lookup('very tired', translator=tr, limit=100)
    assert next(row for row in familiar['results'] if row['id'] == 'knackered')['match_kind'] == 'meaning'


def test_discovery_outcomes_and_dictionary_identity_are_shared(translator):
    calls = [lookup('a people', translator=translator), lookup('zzqqxx', translator=translator),
             get_entry('missing', translator=translator), list_entries(translator=translator),
             list_wordless_meanings(translator=translator), random_entry(translator=translator),
             suggest_name(translator=translator), variations('sideways-call-title',
                 parts={'stem': 'bugger-sideways', 'ending': 'call-me-the-pope'}, translator=translator)]
    assert all(row['outcome'] in outcomes.OUTCOMES and row['dictionary_id'] == translator.dictionary.identity
               for row in calls)


@pytest.mark.parametrize('query,has_citation', [('a people', False), ('national forest', True)])
def test_plain_cli_reports_preservation_without_calling_it_no_match(query, has_citation, capsys):
    from aussiefy.cli import main

    assert main(['lookup', query]) == 1
    text = capsys.readouterr().out
    assert query in text and 'no match for' not in text
    assert ('Not read as:' in text) == has_citation
    if has_citation:
        assert f'{query}:' not in text


def test_json_cli_reports_the_protected_outcome(capsys):
    import json
    from aussiefy.cli import main

    assert main(['lookup', 'a people', '--json']) == 1
    out = json.loads(capsys.readouterr().out)
    assert out['outcome'] == outcomes.LEFT_AS_WRITTEN and out['ruled_out'] == []
    assert out['protections'][0]['reason'] and out['dictionary_id']
