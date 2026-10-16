"""Meaning and agreement boundaries reproduced from the inherited research backlog."""
import pytest


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
    assert not detect(tokenize('She felt terribl about it.'), PatternIndex([]), scorer, [p])
    got = detect(tokenize('She felt terribl yesterday.'), PatternIndex([]), scorer, [p])
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
