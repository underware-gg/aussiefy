"""Reviewed degree belongs to the realised meaning, independently of style and profanity."""

import pytest

from aussiefy import Translator, load_dictionary, translate_changes


PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'garnish': {'riff': 0}, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}


def render(translator, text, opinion=False):
    return translator.translate(text, level=5, vulgarity=3, embedder='none', embellishment=0,
                                document_config={'narrator_opinion': opinion, 'profile': PROFILE})


def alcohol_record(result):
    return next(r for r in result.records if 'DRUNK' in r.det.concepts)


@pytest.mark.parametrize('opinion', [False, True])
@pytest.mark.parametrize('source,band', [('She is tipsy.', 'mild'), ('She is tiddly.', 'mild'),
                                       ('She is legless.', 'strong'), ('She is smashed.', 'strong')])
def test_reviewed_lexical_degree_is_preserved_in_both_directions(translator, source, band, opinion):
    record = alcohol_record(render(translator, source, opinion))
    assert record.eligible
    assert all(c.entry.semantic_degree.get('DRUNK') == band for c in record.eligible)


def test_unknown_degree_does_not_change_unspecified_source_availability(translator):
    record = alcohol_record(render(translator, 'She is drunk.'))
    assert 'half-cut' in {c.entry.id for c in record.eligible}


def test_retained_modifier_preserves_degree_without_adding_a_second_prefix(translator):
    result = render(translator, 'She is very drunk.')
    record = alcohol_record(result)
    assert 'pissed' in {c.entry.id for c in record.eligible}
    assert 'a-bit-full' not in {c.entry.id for c in record.eligible}
    assert 'very ' in result.text
    assert 'very full as ' not in result.text


def test_modifier_owner_survives_negation(translator):
    assert render(translator, 'She is not very drunk.').text == 'She is not very drunk.'


@pytest.mark.parametrize('source', ['She is very sozzled.', 'She is very pissed.',
    'She is very half-cut.', 'She is very half cut.', 'She is very maggoted.',
    'She is not very half-cut.', 'She is not very half cut.',
    'She is very full as a boot.'])
def test_reviewed_source_form_owns_its_modifier_without_becoming_a_replacement_trigger(translator, source):
    assert render(translator, source).text == source


def test_qualifier_survives_the_real_post_substitution_phonetic_phase(dictionary):
    from dataclasses import replace
    rule = next(r for r in dictionary.phonetic if r.id == 'as-fuck-intensifier')
    local = replace(dictionary, phonetic=[replace(rule, prob=1)])
    tr = Translator(local, lookup_embedder=None)
    profile = {**PROFILE, 'phonetic': 1, 'swearing': {'infix': 1}}
    result = tr.translate('She is not very drunk.', level=5, vulgarity=3, embellishment=2,
                          document_type='custom', document_config={'garnish': ['infix'], 'profile': profile})
    assert 'not very drunk' in result.text
    assert not any(p.rule == 'as-fuck-intensifier' for p in result.phonetic)


def test_external_qualifier_is_not_silently_lost_by_a_stacked_extra(translator):
    result = translator.translate('She is very drunk.', level=5, vulgarity=3, embellishment=0,
                                  document_config={'profile': {**PROFILE, 'stack': 1}})
    assert alcohol_record(result).stacked is None


@pytest.mark.parametrize('source', ['She is very tipsy.', 'She is slightly legless.',
                                  'She is very slightly drunk.', 'She is barely drunk.',
                                  'She is almost drunk.', 'She is only slightly drunk.'])
def test_unsupported_degree_compositions_remain_as_written(translator, source):
    assert render(translator, source).text == source


@pytest.mark.parametrize('source', ['She is slightly drunk.', 'She is mildly drunk.', 'She is a bit drunk.'])
def test_mild_qualifier_is_retained_with_a_known_unmarked_predicate(translator, source):
    result = render(translator, source)
    record = alcohol_record(result)
    assert record.eligible
    assert all(c.entry.semantic_degree.get('DRUNK') == 'unmarked' for c in record.eligible)
    qualifier = source.removeprefix('She is ').removesuffix('drunk.')
    assert result.text.startswith('She is ' + qualifier)


def test_entry_replaces_does_not_inherit_its_target_degree(tmp_path):
    path = tmp_path / 'entry.yaml'
    path.write_text('- {id: test-strong-direct, form: drunker, concept: [DRUNK], frame: predicate_adj, '
                    'semantic_degree: {DRUNK: strong}, replaces: [tipsy, very drunk]}\n')
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    assert 'test-strong-direct' not in {c.entry.id for c in alcohol_record(render(tr, 'She is tipsy.')).eligible}
    result = render(tr, 'She is very drunk.')
    assert result.text.startswith('She is very ')
    assert 'test-strong-direct' not in {c.entry.id for c in alcohol_record(result).eligible}


def test_conflicting_source_certificates_do_not_collapse_to_unknown(tmp_path):
    import yaml
    path = tmp_path / 'conflict.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1', 'patch_concepts': {'DRUNK': {
        'triggers': {'predicate_adj': ['tipsy@2', 'tipsy@3']},
        'trigger_degrees': {'predicate_adj': {'tipsy@2': 'mild', 'tipsy@3': 'strong'}}}}}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = render(tr, 'She is tipsy.')
    assert result.text == 'She is tipsy.'
    assert not alcohol_record(result).eligible


def test_repeated_translations_cannot_mutate_compiled_evidence(translator):
    before = [dict(p.semantic_degree) for p in translator.dictionary.patterns]
    render(translator, 'She is tipsy.')
    render(translator, 'She is very drunk.')
    assert before == [p.semantic_degree for p in translator.dictionary.patterns]


def test_inapplicable_frame_does_not_poison_applicable_degree_evidence(tmp_path):
    import yaml
    path = tmp_path / 'frames.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'TEST_FRAME_GRADE': {'description': 'A graded state.',
            'triggers': {'predicate_adj': ['gradedstate'], 'interjection': ['gradedstate']},
            'trigger_degrees': {'predicate_adj': {'gradedstate': 'mild'},
                                'interjection': {'gradedstate': 'strong'}}}},
        'add_entries': [{'id': 'test-frame-mild', 'form': 'wearied', 'concept': ['TEST_FRAME_GRADE'],
                         'frame': 'predicate_adj', 'semantic_degree': {'TEST_FRAME_GRADE': 'mild'}}]}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = render(tr, 'She is gradedstate.')
    record = next(r for r in result.records if 'TEST_FRAME_GRADE' in r.det.concepts)
    assert not record.det.degree_conflicts
    assert {c.entry.id for c in record.eligible} == {'test-frame-mild'}


def test_unknown_source_degree_keeps_unspecified_availability_but_preserves_explicit_qualifiers(tmp_path, dictionary):
    import yaml
    triggers = {f: list(ps) for f, ps in dictionary.concepts['DRUNK'].triggers.items()}
    triggers['predicate_adj'].append('woozy')
    path = tmp_path / 'unknown-source.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1',
        'patch_concepts': {'DRUNK': {'triggers': triggers}}}))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    assert 'half-cut' in {c.entry.id for c in alcohol_record(render(tr, 'She is woozy.')).eligible}
    result = render(tr, 'She is very woozy.')
    assert result.text == 'She is very woozy.'
    assert not alcohol_record(result).eligible


def test_result_clause_operator_survives(translator):
    result = render(translator, 'She was so drunk that she fell asleep.')
    assert ' so ' in result.text and ' that ' in result.text
    record = alcohol_record(result)
    assert all(c.entry.substitution_class == 'lexical' for c in record.eligible)


def test_semantic_degree_is_shared_by_automatic_change_alternatives(translator):
    result = translate_changes('She is tipsy.', translator=translator, level=5, vulgarity=0,
                               embellishment=0, embedder='none', document_config={'profile': PROFILE})
    offered = [o for c in result.changes if c['kind'] == 'substitution'
               for o in c['alternatives'] + c['locked']]
    assert all(translator.dictionary.entries[o['entry_id']].semantic_degree.get('DRUNK') == 'mild'
               for o in offered)


def test_degree_policy_uses_dictionary_meanings_without_named_concept_branches(tmp_path):
    import yaml
    path = tmp_path / 'new-sense.yaml'
    path.write_text(yaml.safe_dump({
        'format': 'aussiefy-dictionary-overlay/v1',
        'add_concepts': {'TEST_GRADED': {
            'description': 'A synthetic gradable state.',
            'triggers': {'predicate_adj': ['testingly weary']},
            'trigger_degrees': {'predicate_adj': {'testingly weary': 'mild'}}}},
        'add_entries': [
            {'id': 'test-mild', 'form': 'wearied', 'concept': ['TEST_GRADED'],
             'frame': 'predicate_adj', 'semantic_degree': {'TEST_GRADED': 'mild'}},
            {'id': 'test-strong', 'form': 'exhausted', 'concept': ['TEST_GRADED'],
             'frame': 'predicate_adj', 'semantic_degree': {'TEST_GRADED': 'strong'}}]
    }))
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = render(tr, 'She is testingly weary.')
    record = next(r for r in result.records if 'TEST_GRADED' in r.det.concepts)
    assert {c.entry.id for c in record.eligible} == {'test-mild'}
