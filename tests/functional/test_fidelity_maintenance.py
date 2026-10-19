"""Regressions for independently observed grammar and sense failures."""
from dataclasses import replace

import pytest

from aussiefy.detect import check_frame
from aussiefy.matcher import compile_pattern, match_at
from aussiefy.realise import question_form
from aussiefy.select import usable_forms
from aussiefy.terms import form_key, strip_markup
from aussiefy.text import tokenize


@pytest.mark.parametrize('source', ['Can I be stupid?', 'Could he be completely confused?',
    'Would she be crazy?', 'Might they be very tired?', 'Should I be hungry?',
    'Had he been confused?', 'Does she seem angry?'])
def test_outer_auxiliary_is_preserved_without_a_second_finite_clause(source, translator):
    for seed in range(12):
        r = translator.translate(source, seed=seed, vulgarity=2, document_type='custom')
        assert r.text.split()[0].lower() == source.split()[0].lower()
        assert not any(s.substituted and s.chosen.entry.frame == 'clause' for s in r.records), r.text


@pytest.mark.parametrize('source', ['Is he stupid?', 'Was she confused?', 'Are you lazy?', 'Is he broke?'])
def test_fixed_finite_or_negative_clauses_are_not_used_as_question_answers(source, translator):
    for seed in range(15):
        r = translator.translate(source, seed=seed, vulgarity=3, document_type='custom')
        for s in r.records:
            if s.substituted and s.chosen.entry.frame == 'clause':
                assert question_form(s.chosen.entry.form) is not None, r.text
        assert "does he wouldn't" not in r.text.lower()
        assert "do you couldn't" not in r.text.lower()


@pytest.mark.parametrize('id', ['wouldnt-know-arse-from-elbow', 'shit-or-go-blind', 'arthur-or-martha',
    'couldnt-organise-a-chook-raffle'])
def test_question_rejection_does_not_remove_the_declarative_idiom(id, dictionary):
    from aussiefy.detect import Detection
    entry = dictionary.entries[id]
    toks = tokenize('he is stupid')
    det = Detection(2, 3, entry.concept, 'predicate_adj', 3, 'trigger', 'test',
                    captures={'subj':toks[0], 'be':toks[1]}, clause_start=0)
    assert usable_forms(entry, det)
    assert not usable_forms(entry, replace(det, question=True))


@pytest.mark.parametrize('source', ['What shall I do?', 'Shall we go?', 'Shall I not go?',
    'I wonder whether I shall go.', 'She asked what she shall do.', 'You shall not delete the files.',
    'We shall meet tomorrow.'])
def test_shall_keeps_its_modal_force_in_questions_embedding_and_declarations(source, translator):
    for level in (4, 5):
        for seed in range(5):
            r = translator.translate(source, level=level, seed=seed, vulgarity=0, document_type='custom',
                                     document_config={'profile':{'frames':[]}})
            assert 'shall' in r.text.lower(), r.text
            assert not any(p.rule in {'shall-will', 'shall-will-ll', 'will-not-wont'} for p in r.phonetic)


def test_will_still_contracts(translator):
    r = translator.translate('I will go. He will not go.', level=5, vulgarity=0, document_type='custom')
    assert "I'll" in r.text and "won't" in r.text


@pytest.mark.parametrize('source', ['I quit smoking.', 'He gave up smoking.', 'She quit her job.',
    'They gave up the work.', 'Quit smoking.', 'Give up the plan.', 'I gave up on it.',
    'She quit trying to win.', 'I quit NewCo.', 'He gave up quietly on the job.'])
def test_quit_with_a_complement_is_not_treated_as_a_complete_intransitive_phrase(source, translator):
    for seed in range(4):
        r = translator.translate(source, seed=seed, document_type='custom', vulgarity=0)
        assert not any(s.substituted and 'QUIT' in s.det.concepts for s in r.records), r.text


@pytest.mark.parametrize('source', ['I quit.', 'I quit now.', 'I give up.', 'He resigned.',
    'I give up completely.', 'Quit.', 'Give up.'])
def test_standalone_quit_keeps_its_useful_options(source, translator):
    r = translator.translate(source, document_type='custom', vulgarity=0, variety=1,
                             document_config={'profile':{'substitution':{'idiom':1, 'phrase':1}}})
    assert any(s.substituted and set(s.det.concepts) & {'QUIT', 'QUIT_COMMAND'} for s in r.records), r.text


@pytest.mark.parametrize('source', ['He was turning and tossing in bed.', 'She tossed and turned.',
    'He tossed restlessly.', 'She tosses about in bed.', 'They were tossing and turning.',
    'He turned and tossed in bed.', 'She was tossing and turning in bed.'])
def test_restless_tossing_does_not_become_throwing(source, translator):
    r = translator.translate(source, document_type='custom', vulgarity=0, variety=1,
                             document_config={'profile':{'substitution':{'idiom':1}}})
    assert not any(s.substituted and 'THROW' in s.det.concepts for s in r.records), r.text
    assert any('RESTLESS_SLEEP' in s.det.concepts for s in r.records)


def test_throwing_a_ball_is_still_recognised(translator):
    r = translator.translate('He tossed a ball.', document_type='custom', vulgarity=0, variety=1,
                             document_config={'profile':{'substitution':{'idiom':1}}})
    assert any(s.substituted and 'THROW' in s.det.concepts for s in r.records)


@pytest.mark.parametrize('source', ['He turned and tossed a ball.',
    'She turned and tossed the rubbish into the bin.', 'He is tossing and turning the pancakes.'])
def test_compound_literal_throwing_does_not_offer_sleep_imagery(source, translator):
    r = translator.translate(source, document_type='custom', vulgarity=0, variety=1)
    assert not any('RESTLESS_SLEEP' in s.det.concepts for s in r.records)
    assert any('THROW' in s.det.concepts for s in r.records)
    assert not any(i.concept == 'RESTLESS_SLEEP' for i in r.imagery)


@pytest.mark.parametrize('source', ['We must establish the facts.', 'The tests establish semantic fidelity.',
    'She established whether it was true.', 'We established a company.'])
def test_bare_establish_is_preserved_without_guessing_its_sense(source, translator):
    r = translator.translate(source, document_type='custom', vulgarity=0, variety=1)
    assert not any(s.substituted and s.text.lower().startswith('establish') for s in r.records)
    assert 'establish' in r.text.lower()


def test_founding_is_distinct_from_starting_or_rough_assembly(translator):
    r = translator.translate('They brought forth a nation.', document_type='custom', vulgarity=0,
                             document_config={'profile':{'substitution':{'idiom':1}}})
    assert r.text == 'They brought forth a nation.'
    assert not any(s.substituted and s.chosen.entry.id in {'kick-off', 'knock-together'} for s in r.records)


@pytest.mark.parametrize('source', ['Love God with all your heart.', 'I support her wholeheartedly.',
    'She sincerely loves her family.', 'He walked solemnly.'])
def test_devotion_and_manner_do_not_become_truth_assurances(source, translator):
    for seed in range(4):
        r = translator.translate(source, document_type='custom', vulgarity=0, seed=seed)
        assert not any(s.substituted and s.chosen.entry.id == 'hand-on-heart' for s in r.records), r.text


def test_truth_assurance_still_has_hand_on_heart(translator):
    r = translator.translate('I say in all honesty that it is true.', document_type='custom', vulgarity=0,
                             document_config={'profile':{'substitution':{'phrase':1}}})
    assert 'hand on heart' in r.text


def test_clause_end_marker_is_data_owned_and_has_no_language_model_tokens(dictionary):
    p = compile_pattern('zzwalk ^end', 'vp', ('QUIT',), 3)
    assert p.clause_end and '^end' not in p.text
    toks = tokenize('zzwalk an object')
    assert check_frame(match_at(p, toks, 0), toks) is None
    assert strip_markup('quit !of ^end@4') == 'quit'
    assert form_key('quit ^end') == form_key('quit')
    assert compile_pattern('{subj} {be} tossing and turning ^end', 'clause',
                           ('RESTLESS_SLEEP',), 3).clause_end
    with pytest.raises(ValueError, match='verb-phrase'):
        compile_pattern('x ^end', 'np', ('QUIT',), 3)


@pytest.mark.parametrize('form,expected', [
    ('{subj} {have} had a gutful', '{have} {subj} had a gutful'),
    ('{subj} {have} carked it', '{have} {subj} carked it'),
    ('{subj} {have} done {poss} dash', '{have} {subj} done {poss} dash'),
    ('{subj} {have} a face like a wet week', '{do} {subj} have a face like a wet week'),
    ('{subj} {have} short arms and deep pockets', '{do} {subj} have short arms and deep pockets'),
])
def test_question_have_distinguishes_perfect_auxiliary_from_lexical_possession(form, expected):
    assert question_form(form) == expected


def test_misspelled_pattern_directive_cannot_silently_change_matching():
    with pytest.raises(ValueError, match='unknown pattern directives'):
        compile_pattern('quit ^endish', 'vp', ('QUIT',), 3)
