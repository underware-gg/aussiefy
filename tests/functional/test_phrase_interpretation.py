"""Phrase-level interpretation: a phrase's context establishes the sense of its words before selection.

The context that establishes a reading (an object, a neighbouring noun) need not be part of the span it
replaces, so the context's own words keep their readings and swaps. Readings of the same words compete by
that evidence rather than pooling, so an incompatible sense never becomes a candidate.
"""
import pytest
import yaml

from aussiefy import Translator, harness, load_dictionary, translate, translate_changes
from aussiefy.detect import detect, resolve_overlaps
from aussiefy.explain import format_explain
from aussiefy.matcher import compile_pattern, match_at
from aussiefy.text import tokenize

EVERY_SWAP = {'document_type': 'custom', 'embellishment': 0,
              'document_config': {'profile': {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}}}
SEEDS = range(8)


def readings(source, dictionary):
    return resolve_overlaps(detect(tokenize(source), dictionary.index, concepts=dictionary.concepts,
                                   adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index,
                                   person_nouns=dictionary.person_nouns))


def concepts(source, dictionary):
    return {cid for d in readings(source, dictionary) for cid in d.concepts}


def outputs(translator, source, **options):
    options = {'level': 5, 'vulgarity': 3, **EVERY_SWAP, **options}
    return [translator.translate(source, seed=seed, **options).text for seed in SEEDS]


def overlay(tmp_path, entries):
    path = tmp_path / 'interpretation.yaml'
    path.write_text(yaml.safe_dump({'format': 'aussiefy-dictionary-overlay/v1', 'add_entries': entries}),
                    encoding='utf-8')
    return Translator(load_dictionary([path]), lookup_embedder=None)


# --- the shared mechanism ---------------------------------------------------------------------------------

def test_context_object_is_read_but_not_consumed():
    pattern = compile_pattern('believe ?={np}', 'vp', ('TEST',), 3)
    tokens = tokenize('You cannot believe a liar.')
    match = match_at(pattern, tokens, 2)
    assert (match.start, match.end) == (2, 3)
    assert match.object_start == 3 and match.context == (2, 4)   # detection reads the object's extent
    assert not match.captures
    assert not pattern.consuming[1:]


@pytest.mark.parametrize('text', ['believe ?<={np}', 'believe ?={np} ?={np}', '?={np} believe',
                                  'think ?={np} of', 'believe ?={np} ?=even'])
def test_context_object_placement_is_validated(text):
    with pytest.raises(ValueError):
        compile_pattern(text, 'vp', ('TEST',), 3)


@pytest.mark.parametrize('text', ['believe ?~{np}', 'believe ?<{np}', 'believe ={np}', 'believe ?={vp}',
                                  'believe !{np}', 'believe !={np}', 'believe ?={ing} ^end'])
def test_a_malformed_context_object_is_refused(text):
    with pytest.raises(ValueError, match='context object|cannot follow'):
        compile_pattern(text, 'vp', ('TEST',), 3)


@pytest.mark.parametrize('concept', ['UNRESOLVED_SENSE'])
def test_the_holding_reading_takes_no_entries(concept, tmp_path):
    with pytest.raises(Exception, match='takes no entries'):
        overlay(tmp_path, [{'id': 'test-hold', 'form': 'whatsit', 'concept': [concept], 'frame': 'vp'}])


@pytest.mark.parametrize('query,wrong', [('fantastic terrors', {'EXCELLENT', 'GOOD', 'GREAT_EXCLAIM'}),
                                         ('fantastic terrors and good food', {'EXCELLENT', 'GREAT_EXCLAIM'}),
                                         ('take heart', {'HEART_ORGAN'}),
                                         ("to your heart's content", {'HEART_ORGAN'})])
def test_lookup_offers_nothing_a_reading_ruled_out(query, wrong):
    assert not wrong & {cid for result in harness.lookup(query, level=5)['results'] for cid in result['concepts']}


@pytest.mark.parametrize('query,kept', [('believe a liar', 'a bullshitter'), ('believe my mate', 'mate'),
                                        ('believe the old man', 'old fella')])
def test_lookup_still_offers_the_context_objects_own_swaps(query, kept):
    assert kept in {result['form'] for result in harness.lookup(query, level=5)['results']}


@pytest.mark.parametrize('text', ['think nothing of ?={ing} again', 'think ?<={ing}'])
def test_a_gerund_object_must_end_the_pattern_too(text):
    with pytest.raises(ValueError, match='must end the pattern'):
        compile_pattern(text, 'vp', ('TEST',), 3)


def test_context_establishes_a_sense_while_a_neighbouring_edit_stays_available(dictionary):
    found = readings('You cannot believe a liar even when he tells the truth.', dictionary)
    verb = next(d for d in found if 'ACCEPT_AS_TRUE' in d.concepts)
    assert (verb.start, verb.end, verb.evidence_extent) == (2, 3, (2, 5))   # "even" is not part of the object
    assert verb.supersedes == ('THINK',)
    assert any('LIAR' in d.concepts and (d.start, d.end) == (3, 5) for d in found)
    assert not any('THINK' in d.concepts for d in found)


def test_same_span_senses_compete_by_evidence_instead_of_merging(dictionary):
    found = readings('Fantastic terrors never felt before.', dictionary)
    assert [(d.start, d.end, d.concepts, d.supersedes) for d in found] == [(0, 1, ('FANCIFUL',), ('EXCELLENT',))]
    assert concepts('That was a fantastic game.', dictionary) == {'EXCELLENT'}


@pytest.mark.parametrize('source', ['I believe he is lying.', 'She believed the rumours were true.',
                                    'I believe so.', 'I believed him to be honest.',
                                    'They believed the earth to be flat.', 'I believe the man in the car is lying.',
                                    'I believe the people here are lying.', 'I believe the man who called was lying.',
                                    'I believe everyone here knows.', 'I believe the story that he told was true.',
                                    'I believe the story he told was true.', 'I believe the man who has called was lying.',
                                    'I believe John Smith lied.'])
def test_clause_and_non_nominal_complements_are_not_objects(source, dictionary):
    assert concepts(source, dictionary) & {'ACCEPT_AS_TRUE', 'THINK'} == {'THINK'}


@pytest.mark.parametrize('source', ['I believe in you.', 'I believe that it works.',
                                    'I believe you and he were friends.'])
def test_prepositional_and_clausal_believe_take_no_object_reading(source, dictionary):
    assert 'ACCEPT_AS_TRUE' not in concepts(source, dictionary)


@pytest.mark.parametrize('source,sense', [('She thought highly of him.', 'REGARD_HIGHLY'),
                                          ('She thought a lot of him.', 'REGARD_HIGHLY'),
                                          ('He thinks very highly of her.', 'REGARD_HIGHLY'),
                                          ('He thought highly of the stories people tell.', 'REGARD_HIGHLY'),
                                          ('He thought so highly of her that he wrote.', 'REGARD_HIGHLY'),
                                          ('He thinks too highly of himself.', 'CONCEITED'),
                                          ("I don't think too highly of him.", 'REGARD_HIGHLY'),
                                          ("He doesn't think too much of the plan.", 'REGARD_HIGHLY'),
                                          ('They thought ill of him.', 'REGARD_POORLY'),
                                          ('He thinks too much of himself.', 'CONCEITED'),
                                          ('He thinks too much of the plan.', 'OVERVALUE'),
                                          ('She thinks nothing of walking ten miles.', 'NO_HARDSHIP')])
def test_evaluative_think_of_keeps_its_polarity(source, sense, dictionary):
    found = concepts(source, dictionary)
    assert sense in found and not found & {'THINK', 'A_LOT', 'ZERO_AMOUNT', 'NOTHING'}


def test_explanation_reports_the_superseded_reading(translator):
    result = translator.translate('You cannot believe a liar even when he tells the truth.', level=5, vulgarity=3,
                                  **EVERY_SWAP)
    explained = next(r for r in result.to_dict()['explain'] if r['concepts'] == ['ACCEPT_AS_TRUE'])
    assert explained['supersedes'] == ['THINK']
    assert explained['decision'] == 'kept original: no eligible entry'
    assert 'concept ACCEPT_AS_TRUE' in format_explain(result) and 'supersedes THINK' in format_explain(result)


# --- the agreed examples ----------------------------------------------------------------------------------

def test_valuing_is_not_reckoning_and_its_object_keeps_its_swaps(translator):
    source = 'The emperor thought so much of new clothes that he spent all his money.'
    texts = outputs(translator, source)
    assert not any('reckon' in text for text in texts)
    assert all(text.startswith('The emperor thought so much of ') for text in texts)
    assert any('clobber' in text for text in texts)


def test_believing_a_speaker_is_not_reckoning_and_the_speaker_keeps_its_swap(translator):
    texts = outputs(translator, 'You cannot believe a liar even when he tells the truth.')
    assert not any('reckon' in text for text in texts)
    assert any('believe a bullshitter' in text for text in texts)


def test_fanciful_fantastic_is_not_praise(translator):
    texts = outputs(translator, 'Thrilled me, filled me with fantastic terrors never felt before.')
    assert all('fantastic terrors' in text for text in texts)


def test_heart_content_reading_supersedes_the_organ(dictionary):
    found = readings("Use it to your heart's content.", dictionary)
    assert [(d.concepts, d.supersedes) for d in found] == [(('AS_MUCH_AS_DESIRED',), ('HEART_ORGAN',))]


@pytest.mark.parametrize('source', ['I believe he is lying.', 'I think it will rain.', 'I believe so.'])
def test_genuine_thinking_still_reckons(source, translator):
    assert all('reckon' in text for text in outputs(translator, source))


def test_genuine_praise_still_takes_aussie_praise(translator):
    texts = outputs(translator, 'That was a fantastic game.')
    assert any(word in text for text in texts for word in ('ripper', 'beaut', 'grouse'))


def test_literal_heart_still_takes_ticker(translator):
    assert all('ticker' in text for text in outputs(translator, 'The doctor listened to my heart.'))


CONTROLS = {'reckon': 'I think it will rain.', 'ripper': 'That was a fantastic game.',
            'beaut': 'That was a fantastic game.', 'ticker': 'The doctor listened to my heart.'}


@pytest.mark.parametrize('options', [{'vulgarity': 0},
                                     {'level': 4, 'document_config': {'profile': {'phonetic': 0}}}])
@pytest.mark.parametrize('source,wrong', [
    ('The emperor thought so much of new clothes that he spent all his money.', 'reckon'),
    ('You cannot believe a liar even when he tells the truth.', 'reckon'),
    ('Fantastic terrors never felt before.', 'ripper'),
    ('Fantastic terrors never felt before.', 'beaut'),
    ("Use it to your heart's content.", 'ticker'),
])
def test_protection_holds_while_the_component_sense_stays_available(source, wrong, options, translator):
    """The component's own swap still fires under the same dials and rolls; inside the phrase it never does,
    although the phrase's reading has no candidate of its own."""
    assert any(wrong in text.lower() for text in outputs(translator, CONTROLS[wrong], **options))
    assert not any(wrong in text.lower() for text in outputs(translator, source, **options))


def test_seeded_interpretation_is_repeatable(dictionary):
    source = 'You cannot believe a liar even when he tells the truth. The emperor thought so much of new clothes.'
    first = [Translator(dictionary).translate(source, level=5, vulgarity=3, seed=seed).text for seed in SEEDS]
    again = [Translator(dictionary).translate(source, level=5, vulgarity=3, seed=seed).text for seed in SEEDS]
    assert first == again


@pytest.mark.parametrize('source,wrong,sense', [
    ('You cannot believe a liar even when he tells the truth.', 'reckon', 'THINK'),
    ('The emperor thought so much of new clothes.', 'reckon', 'THINK'),
    ('Fantastic terrors never felt before.', 'ripper', 'EXCELLENT'),
])
def test_alternatives_and_explanations_share_the_interpretation(source, wrong, sense, translator):
    options = {'translator': translator, 'level': 5, 'vulgarity': 3, **EVERY_SWAP}
    changes = translate_changes(source, **options)
    offered = {alt['entry_id'] for change in changes.to_dict()['changes'] for alt in change['alternatives']}
    assert wrong not in offered
    assert harness.plan(source, **options)['draft'] == translate(source, **options).text
    assert wrong not in {result['id'] for result in harness.lookup(source, **options)['results']}
    explain = translate(source, **options).to_dict()['explain']
    assert not any(sense in record['concepts'] for record in explain)
    assert any(sense in record.get('supersedes', ()) for record in explain)


# --- whole-phrase replacement and grammatical controls -----------------------------------------------------

def test_a_dictionary_entry_can_carry_the_interpreted_sense(tmp_path):
    tr = overlay(tmp_path, [{'id': 'test-trust', 'form': 'trust', 'concept': ['ACCEPT_AS_TRUE'], 'frame': 'vp'}])
    texts = outputs(tr, 'You cannot believe a liar even when he tells the truth.')
    assert any('trust a bullshitter' in text for text in texts)
    assert not any('reckon' in text for text in texts)
    assert 'I trusted him.' in outputs(tr, 'I believed him.')


def test_a_whole_phrase_entry_keeps_tense_negation_polarity_and_the_object(tmp_path):
    tr = overlay(tmp_path, [{'id': 'test-rate', 'form': 'rate', 'concept': ['REGARD_HIGHLY'], 'frame': 'vp'}])
    assert set(outputs(tr, 'He thought highly of her.')) == {'He rated her.'}
    assert set(outputs(tr, "I don't think much of it.")) == {"I don't rate it."}
    assert set(outputs(tr, 'He thought little of her.')) == {"He didn't rate her."}


def test_a_whole_phrase_entry_cannot_discard_a_result_degree(tmp_path):
    tr = overlay(tmp_path, [{'id': 'test-rate', 'form': 'rate', 'concept': ['REGARD_HIGHLY'], 'frame': 'vp'}])
    result = tr.translate('The emperor thought so much of new clothes that he spent all his money.', level=5,
                          **EVERY_SWAP)
    record = next(r for r in result.records if r.det.concepts == ('REGARD_HIGHLY',))
    assert not record.substituted
    assert ('test-rate', "no form fits: would discard 'so', which its result complement depends on") in record.rejected


@pytest.mark.parametrize('options', [
    {'vulgarity': 0},                                                                         # dial excludes it
    {'document_config': {'profile': {'phonetic': 0, 'substitution': {'lexical': 0.3, 'phrase': 0.3,
                                                                       'idiom': 0.3}}}},  # rolls keep it
])
def test_an_unused_phrase_entry_never_falls_back_to_the_component_sense(options, tmp_path):
    tr = overlay(tmp_path, [{'id': 'test-trust', 'form': 'trust', 'concept': ['ACCEPT_AS_TRUE'], 'frame': 'vp',
                             'vulgarity': 2}])
    texts = outputs(tr, 'You cannot believe a liar even when he tells the truth.', **options)
    assert not any('reckon' in text for text in texts)
    assert any('believe' in text for text in texts)


@pytest.mark.parametrize('source,kept', [("It's too hot to sleep.", 'too hot to sleep'),
                                         ('It was such a fuss that nobody came.', 'such a fuss that')])
def test_claimed_result_degree_keeps_its_complement_grammatical(source, kept, translator):
    assert all(kept in text for text in outputs(translator, source, vulgarity=1))


def test_a_later_clause_is_not_a_result_complement(translator):
    assert any(text.startswith('Ta') for text in outputs(translator, "Thank you so much, that's excellent."))
    assert any('armpit' in text for text in outputs(translator, 'It was too hot and we went to the beach.',
                                                    vulgarity=1))


# --- object extent, self-regard and the heart's other senses ------------------------------------------------

@pytest.mark.parametrize('source', ['I believe the old man next door completely.',
                                    "You can't believe a word the old man next door says.",
                                    "I believe the man's story.", 'I believe a very old man.',
                                    'You cannot believe a liar who tells lies.', 'I believe the man that I met.',
                                    'I believe the man who said he was lying.', 'I believe the people who say it is safe.'])
def test_a_context_object_is_read_by_its_tags_not_a_word_count(source, translator):
    assert 'ACCEPT_AS_TRUE' in concepts(source, translator.dictionary)
    assert not any('reckon' in text for text in outputs(translator, source))


@pytest.mark.parametrize('source,expected', [
    ('He thinks too much of himself.', 'He thinks the sun shines out of his own arse.'),
    ('She thought so highly of herself.', 'She thought the sun shone out of her own arse.'),
])
def test_self_regard_takes_the_sun_shining_out_of_ones_own_arse(source, expected, translator):
    assert expected in outputs(translator, source, vulgarity=2)


@pytest.mark.parametrize('source', ["He doesn't think much of himself.", 'He thinks too much of the plan.',
                                    'John thinks too much of himself.'])
def test_self_regard_needs_a_reflexive_affirmative_and_a_pronoun_to_agree_with(source, translator):
    assert not any('arse' in text for text in outputs(translator, source, vulgarity=2))


@pytest.mark.parametrize('subject,reflexive', [('She', 'herself'), ('He', 'himself'), ('They', 'themselves')])
@pytest.mark.parametrize('evaluation', ['the world', 'a lot', 'too much', 'too highly'])
def test_negated_self_regard_does_not_claim_conceit(subject, reflexive, evaluation, translator):
    auxiliary = 'do' if subject == 'They' else 'does'
    source = f'{subject} {auxiliary} not think {evaluation} of {reflexive}.'
    found = concepts(source, translator.dictionary)
    assert 'REGARD_HIGHLY' in found and not found & {'CONCEITED', 'OVERVALUE'}
    assert not any('arse' in text for text in outputs(translator, source, vulgarity=2))


@pytest.mark.parametrize('source', ["She doesn't think the world of herself.", 'He never thinks the world of himself.'])
def test_contracted_or_never_negated_self_regard_is_not_conceit(source, dictionary):
    found = concepts(source, dictionary)
    assert 'REGARD_HIGHLY' in found and 'CONCEITED' not in found


def test_adoring_someone_else_keeps_their_arse(translator):
    assert 'She thinks the sun shines out of his arse.' in outputs(translator, 'She adores him.', vulgarity=2)


@pytest.mark.parametrize('source', ['Have heart, the team is still in it.', 'He has a lot of heart.',
                                    'Take heart, it will pass.', 'She showed real heart in the final.',
                                    'Have a heart, mate.', 'Put your heart into it.', "Her heart wasn't in it.",
                                    "My heart's not in it.", 'His heart was never in it.',
                                    'I cannot find in my heart to leave them.',
                                    'I cannot find it in my heart to forgive him.'])
def test_heart_as_spirit_or_courage_is_never_ticker(source, translator):
    assert not any('ticker' in text for text in outputs(translator, source))


@pytest.mark.parametrize('source', ['She broke my heart.', 'It breaks my heart to see it.',
                                    'You have broken his heart.', 'Breaking her heart was cruel.',
                                    'She broke all our hearts.', 'My heart breaks for them.',
                                    'My heart is breaking.', 'His heart has been broken.', "My heart's broken.",
                                    'My heart will break.', 'She will break a heart or two.'])
def test_a_broken_heart_is_grief_not_ticker(source, translator):
    assert 'HEARTBREAK' in concepts(source, translator.dictionary)
    assert not any('ticker' in text for text in outputs(translator, source))


@pytest.mark.parametrize('source', ['The doctor listened to my heart.', 'From the bottom of my heart, thanks.',
                                    'Ah, distinctly I remember, the beating of my heart.', 'He has a weak heart.',
                                    'He has a heart murmur.'])
def test_a_determined_heart_still_takes_ticker(source, translator):
    assert all('ticker' in text for text in outputs(translator, source))


@pytest.mark.parametrize('source', ['I believe the stories people tell.', 'I believe the bus driver lied.'])
def test_an_object_or_clause_the_tags_cannot_settle_stays_as_written(source, translator):
    found = readings(source, translator.dictionary)
    held = next(d for d in found if d.concepts == ('UNRESOLVED_SENSE',))
    assert held.supersedes == ('THINK',)
    assert all(text.startswith('I believe the') for text in outputs(translator, source))


@pytest.mark.parametrize('source', ['I believe what he says.', 'I believe what you told me.',
                                    'I believe what happened.', 'I believe whatever she told me.',
                                    'They believe what the report says.'])
def test_believing_what_was_said_is_taking_it_as_true(source, translator):
    assert 'ACCEPT_AS_TRUE' in concepts(source, translator.dictionary)
    assert not any('reckon' in text for text in outputs(translator, source))


def test_a_free_relative_subject_keeps_supposition(translator):
    assert all('I reckon what he says is true.' == text for text in outputs(translator, 'I believe what he says is true.'))


def test_a_free_relative_subject_of_a_past_clause_keeps_supposition(dictionary):
    found = concepts('I believe whatever she told me was false.', dictionary)
    assert found & {'ACCEPT_AS_TRUE', 'THINK'} == {'THINK'}


@pytest.mark.parametrize('source', ['I believe what she told me was true.', 'I believe what they told us was a lie.',
                                    'I believe the man who told us was honest.',
                                    'I believe the man who told you was lying.',
                                    'I believe the woman who said the man was lying is honest.',
                                    'I believe the man who was sick is right.',
                                    'I believe the man who seemed nice was lying.'])
def test_a_relative_clause_object_leaves_the_next_verb_to_the_main_clause(source, dictionary):
    """An object pronoun, or one that disagrees with the verb, cannot be a complement clause's subject."""
    assert concepts(source, dictionary) & {'ACCEPT_AS_TRUE', 'THINK', 'UNRESOLVED_SENSE'} == {'THINK'}


@pytest.mark.parametrize('source', ['I believe the woman who said he was lying.',
                                    'I believe the man who said she was right.',
                                    'I believe the men who said the boss was lying.'])
def test_a_subject_or_disagreement_opens_the_relative_clauses_own_complement(source, dictionary):
    """"he was lying" has a subject pronoun; "the men ... was" cannot be the main clause."""
    assert 'ACCEPT_AS_TRUE' in concepts(source, dictionary)


@pytest.mark.parametrize('source', ['I believe the man who told the police was lying.',
                                    'I believe the woman who saw the doctor was ill.',
                                    'I believe the woman who said the man was lying.',
                                    'I believe the people who told you were lying.',
                                    'I believe what he told the police was true.',
                                    'I believe the man who told her story was lying.',
                                    'I believe the police who told the man were lying.'])
def test_a_relative_clause_complement_the_tags_cannot_settle_stays_as_written(source, translator):
    """"who told the police [was lying]" and "who said the man [was lying]" differ only in the verb's own
    grammar, which the tags do not carry."""
    found = concepts(source, translator.dictionary)
    assert 'UNRESOLVED_SENSE' in found and 'ACCEPT_AS_TRUE' not in found
    assert all(text.startswith('I believe') for text in outputs(translator, source))


# --- imagining, and what "think nothing of" leaves open ------------------------------------------------------

@pytest.mark.parametrize('source', ['Only think what a use it would be to our kingdom!',
                                    'Think what we could do with the money.', 'Just think how lucky we are.'])
def test_an_invitation_to_picture_is_not_reckoning(source, translator):
    assert 'IMAGINE' in concepts(source, translator.dictionary)
    assert not any('reckon' in text.lower() for text in outputs(translator, source))


@pytest.mark.parametrize('source,kept', [('I think what he did was wrong.', 'reckon what he did'),
                                         ('They only think what they are told.', 'only reckon what')])
def test_a_subject_keeps_think_what_a_supposition(source, kept, translator):
    assert all(kept in text for text in outputs(translator, source))


@pytest.mark.parametrize('source', ["Think what you like, I'm off.", 'Think how to fix it.', 'Think what to do next.',
                                    'Think what you will.'])
def test_believing_or_working_out_is_not_picturing(source, translator):
    assert 'IMAGINE' not in concepts(source, translator.dictionary)
    assert all(text.startswith('Think') for text in outputs(translator, source))


@pytest.mark.parametrize('source', ['He thought nothing of her.', 'She thinks nothing of it.',
                                    'He thought nothing of the cold.'])
def test_think_nothing_of_a_nominal_is_left_open(source, tmp_path):
    """Low regard ("of her") or no bother ("of the cold"): only a gerund settles it as no hardship."""
    tr = overlay(tmp_path, [{'id': 'test-no-trouble', 'form': 'have no trouble with', 'concept': ['NO_HARDSHIP'],
                             'frame': 'vp'}])
    found = concepts(source, tr.dictionary)
    assert 'UNRESOLVED_SENSE' in found and 'NO_HARDSHIP' not in found
    assert not any('trouble' in text for text in outputs(tr, source))


@pytest.mark.parametrize('source', ['He thought nothing of walking ten miles.',
                                    'He thought nothing of driving all night.',
                                    'He thought nothing of walking to the shops every day.'])
def test_think_nothing_of_doing_is_no_hardship(source, dictionary):
    assert 'NO_HARDSHIP' in concepts(source, dictionary)
    assert 'UNRESOLVED_SENSE' not in concepts(source, dictionary)


@pytest.mark.parametrize('source,sense', [('She thinks a lot of working mums.', 'REGARD_HIGHLY'),
                                          ('She thinks highly of working mothers.', 'REGARD_HIGHLY'),
                                          ('You cannot believe running commentary.', 'ACCEPT_AS_TRUE')])
def test_a_participle_modifying_a_noun_is_still_a_nominal_object(source, sense, translator):
    assert sense in concepts(source, translator.dictionary)
    assert not any('reckon' in text for text in outputs(translator, source))


def test_heart_medication_is_not_courage(dictionary):
    assert 'HEART_SPIRIT' not in concepts('Take heart medication daily.', dictionary)
    assert 'HEART_SPIRIT' in concepts('Take heart, it will pass.', dictionary)
