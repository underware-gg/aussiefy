"""Meaning and agreement boundaries reproduced from the inherited research backlog."""
import pytest

from aussiefy import harness, translate, translate_changes
from aussiefy.detect import detect, resolve_overlaps
from aussiefy.text import tokenize


@pytest.mark.parametrize('opening,closing', [('"', '"'), ('“', '”'), ("'", "'"), ('‘', '’')])
def test_agreement_detection_is_independent_of_dialogue_quotes(dictionary, opening, closing):
    from aussiefy.detect import detect, resolve_overlaps
    from aussiefy.text import tokenize
    tokens = tokenize(f'He said {opening}Very well,{closing} and left.')
    found = resolve_overlaps(detect(tokens, dictionary.index, concepts=dictionary.concepts, person_nouns=dictionary.person_nouns))
    assert any('OK_THEN' in d.concepts for d in found)
    assert not any('VERY' in d.concepts for d in found)


def test_quoted_agreement_fix_preserves_real_intensifiers_and_possessives(dictionary):
    from aussiefy.detect import at_clause_start, detect, resolve_overlaps
    from aussiefy.text import tokenize
    found = resolve_overlaps(detect(tokenize('She sang very well.'), dictionary.index,
                                    concepts=dictionary.concepts, person_nouns=dictionary.person_nouns))
    assert any('VERY' in d.concepts for d in found)
    assert not any('OK_THEN' in d.concepts for d in found)
    tokens = tokenize("The walkers' very tired guide stopped.")
    assert not at_clause_start(tokens, next(i for i, t in enumerate(tokens) if t.norm == 'very'))


@pytest.mark.parametrize('opening,closing', [('"', '"'), ('“', '”'), ("'", "'"), ('‘', '’')])
def test_quoted_word_object_does_not_turn_manner_into_agreement(dictionary, opening, closing):
    from aussiefy.detect import detect, resolve_overlaps
    from aussiefy.text import tokenize
    found = resolve_overlaps(detect(tokenize(f'He said {opening}go{closing} very well.'), dictionary.index,
                                    concepts=dictionary.concepts, person_nouns=dictionary.person_nouns))
    assert any('VERY' in d.concepts for d in found)
    assert not any('OK_THEN' in d.concepts for d in found)


@pytest.mark.parametrize('text', ['She was the best of the party.', 'A party of five arrived.',
                                 'The party won the election.', 'A function returns a number.'])
def test_ambiguous_groups_and_functions_do_not_establish_a_social_event(translator, text):
    for seed in range(8):
        r = translator.translate(text, level=5, seed=seed, vulgarity=0, embellishment='deadset')
        assert not any('PARTY' in record.det.concepts for record in r.records)


def test_explicit_social_events_keep_the_imported_general_option(translator):
    out = {translator.translate('We held a social gathering.', level=4, seed=s, vulgarity=0,
                                embellishment='deadset').text for s in range(8)}
    assert any('a do' in text for text in out)


def outputs(translator, text, **kwargs):
    return {translator.translate(text, level=5, vulgarity=0, embellishment='deadset', seed=s, **kwargs).text
            for s in range(12)}


@pytest.mark.parametrize('text', ['These are great disappointments.', 'It was a great dearth.',
                                 'Those were great losses.'])
def test_attributive_great_cannot_escape_noun_sense_guard(translator, text):
    assert outputs(translator, text) == {text}


def test_predicate_and_approved_attributive_praise_still_translate(translator):
    assert any('great' not in out for out in outputs(translator, 'It was great.'))
    assert any('great' not in out for out in outputs(translator, 'We had great fun.'))


@pytest.mark.parametrize('text', ['The dog is loyal.', 'The horse was loyal.', 'The animals are loyal.'])
def test_animal_subjects_are_not_person_roles(translator, text):
    assert all('true blue' not in out for out in outputs(translator, text))


def test_person_vocabulary_is_editable_dictionary_data(translator):
    assert 'apprentice' in translator.dictionary.person_nouns
    assert any('true blue' in out for out in outputs(translator, 'The apprentice was loyal.'))


@pytest.mark.parametrize('article', ['An', 'an', 'The', 'the'])
def test_capitalised_determiner_does_not_hide_a_guard(translator, article):
    assert all('American football coach' in out for out in outputs(translator, f'{article} American football coach arrived.'))
    assert any('footy' in out for out in outputs(translator, 'The football coach arrived.'))


@pytest.mark.parametrize('text', ['Where is my swimsuit?', 'Where was the swimsuit?', 'My swimsuit is wet.'])
def test_plural_only_clothes_do_not_break_singular_agreement(translator, text):
    outs = outputs(translator, text)
    assert all(not any(word in out for word in ['togs', 'bathers', 'swimmers']) for out in outs)
    assert any('cossie' in out or 'cozzie' in out for out in outs)


def test_plural_only_clothes_remain_available_without_singular_agreement(translator):
    assert any('togs' in out or 'bathers' in out or 'swimmers' in out
               for out in outputs(translator, 'I packed my swimsuit.'))


def test_similarity_fallback_enforces_zero_width_exclusions():
    from aussiefy.detect import detect
    from aussiefy.matcher import PatternIndex, compile_pattern
    from aussiefy.text import tokenize
    p = compile_pattern('terrible !about', 'predicate_adj', ('BAD',), 3)
    scorer = lambda text: {0: .99}
    assert not detect(tokenize('She felt terribl about it.'), PatternIndex([]), scorer, [p], person_nouns=None)
    got = detect(tokenize('She felt terribl yesterday.'), PatternIndex([]), scorer, [p], person_nouns=None)
    assert got and got[0].method == 'embedding'


def test_bad_frame_vocabulary_is_a_dictionary_error(data_copy):
    from aussiefy.loader import load_dictionary
    from aussiefy.schema import SchemaError
    (data_copy / 'grammar.yaml').write_text('person_nouns: [Dog]\n')
    with pytest.raises(SchemaError, match='grammar.yaml'):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize('text', ['Which swimsuit does she want?', 'Which swimsuit is she wearing?',
                                 'Which swimsuit is Bob wearing?'])
def test_object_question_auxiliary_does_not_agree_with_clothing(translator, text):
    assert any(any(word in out for word in ['togs', 'bathers', 'swimmers']) for out in outputs(translator, text))


@pytest.mark.parametrize('possessive', ['my', 'your', 'his', 'her', 'its', 'our', 'their', "one's"])
@pytest.mark.parametrize('apostrophe', ["'", '’'])
def test_heart_content_is_one_meaning_unit(possessive, apostrophe, translator):
    source = f'Use it to {possessive} heart{apostrophe}s content.'
    found = resolve_overlaps(detect(tokenize(source), translator.dictionary.index,
                                   concepts=translator.dictionary.concepts, person_nouns=translator.dictionary.person_nouns))
    assert any('AS_MUCH_AS_DESIRED' in d.concepts for d in found)
    assert not any('HEART_ORGAN' in d.concepts for d in found)
    for seed in range(4):
        result = translator.translate(source, level=5, vulgarity=1, seed=seed,
            document_type='custom', document_config={'profile': {'phonetic': 0,
                'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}, embellishment=0)
        assert source == result.text


@pytest.mark.parametrize('source', ["We ate to our hearts' content.", 'They danced to their hearts’ content.'])
def test_plural_possessive_heart_content_keeps_its_whole_meaning(source, translator):
    result = translator.translate(source, level=5, vulgarity=1, embellishment=0,
                                  document_type='custom', document_config={'profile': {'phonetic': 0}})
    assert source == result.text


def test_idiom_unit_is_shared_by_translation_tools(translator):
    source = "Use it to your heart's content."
    options = {'translator': translator, 'level': 5, 'vulgarity': 1, 'embellishment': 0,
               'document_type': 'custom', 'document_config': {'profile': {'phonetic': 0}}}
    assert translate(source, **options).text == source
    changes = translate_changes(source, **options)
    assert changes.text == source
    assert not changes.changes
    assert harness.plan(source, **options)['draft'] == source
    assert 'ticker' not in {e['id'] for e in harness.lookup(source, **options)['results']}
    markdown = "Use it *to your heart's content*."
    assert translate(markdown, markdown=True, **options).text == markdown


def test_literal_heart_is_still_available(translator):
    result = translator.translate('The doctor listened to my heart.', level=5, vulgarity=1,
        embellishment=0, document_type='custom', document_config={'profile': {'phonetic': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    assert any(r.substituted and r.chosen.entry.id == 'ticker' for r in result.records)
    assert 'ticker' in result.text


def test_idiom_ownership_does_not_hide_a_literal_heart_in_the_same_sentence(translator):
    source = "Use it to your heart's content while the doctor listens to my heart."
    result = translator.translate(source, level=5, vulgarity=1, embellishment=0,
        document_type='custom', document_config={'profile': {'phonetic': 0,
            'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})
    assert "to your heart's content" in result.text
    assert 'my ticker' in result.text


def _readings(source, dictionary):
    return resolve_overlaps(detect(tokenize(source), dictionary.index, concepts=dictionary.concepts,
                                   adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index,
                                   person_nouns=dictionary.person_nouns))


@pytest.mark.parametrize('source', ['Much of the time is wasted.', 'It was wasted.', 'The money was wasted.',
                                    'Money was wasted.', '"Money was wasted," he said.', 'Time was wasted.',
                                    'Nothing was wasted.', 'The fees were wasted.', 'The trees were smashed.',
                                    'The wine was drunk.', 'The glass was smashed.', 'The tank is full.'])
def test_a_person_only_sense_is_not_read_of_a_thing(source, dictionary):
    """Drunk (or full) is said only of people: of time, money or a glass the word keeps its other meanings,
    so the sense is never established, explained or looked up."""
    assert not {'DRUNK', 'FULL'} & {cid for d in _readings(source, dictionary) for cid in d.concepts}
    assert not any({'DRUNK', 'FULL'} & set(r['concepts']) for r in harness.lookup(source, level=5)['results'])


@pytest.mark.parametrize('source', ['I was wasted last night.', 'They were wasted.', 'We got smashed.',
                                    'He was drunk.', 'The man was plastered.', 'My mate was drunk.',
                                    'The boss was wasted.', 'John was hammered.', 'The students were drunk.',
                                    'The tourists were plastered.'])
def test_a_person_only_sense_still_reads_of_a_person(source, dictionary):
    assert 'DRUNK' in {cid for d in _readings(source, dictionary) for cid in d.concepts}


@pytest.mark.parametrize('source,inflected', [('He tells lies.', 'tellings'), ('He fools around.', 'muckings')])
def test_verb_idiom_heads_are_inflected_once(source, inflected, translator):
    for seed in range(8):
        assert inflected not in translator.translate(source, level=5, vulgarity=3, embellishment=0, seed=seed).text
