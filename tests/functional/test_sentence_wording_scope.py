"""Sentence wording uses actual source scope; no dictionary phrase is a code branch."""
import pytest

from aussiefy import Translator
from aussiefy.detect import Detection, read_meanings
from aussiefy.plain_wording import plain_entry
from aussiefy.matcher import phrase_token
from aussiefy.changes import Watch
from aussiefy.engine import Spot, SubstitutionRecord
from aussiefy.select import Candidate
from aussiefy.schema import parse_concept
from aussiefy.text import tokenize


def rendered(dictionary, source, form, *, start=1, frame='np'):
    tokens = tokenize(source)
    be = next((t for t in tokens if t.norm in {'is', 'was', 'were'}), None)
    detection = Detection(start, len(tokens)-1, ('TEST',), frame, 3, 'test', '',
                          captures={'be': be} if be else {})
    concept = parse_concept('TEST', {'plain': 'a separate display name', 'plain_forms': {frame: form}})
    result = plain_entry(concept, detection, dictionary, tokens=tokens)
    if result is None:
        return None
    entry, reading = result
    tr = Translator(dictionary, lookup_embedder=None)
    watch = Watch()
    tr.translate(source, level=1, vulgarity=0, embellishment=0, _observer=watch)
    sent = watch.sentences[0].sent
    rec = SubstitutionRecord((tokens[start].start, tokens[detection.end-1].end), source, detection)
    spot = Spot(sent, rec, [], watch.run.state.copy(), set(), {}, set(), 0)
    result = tr.render_at_spot(Candidate(entry, 0, 'English', kind='plain', reading=reading), spot, watch.run)
    return source[:tokens[result.start].start] + result.text + source[tokens[result.end-1].end:], reading


@pytest.mark.parametrize('source,form,expected', [
    ('Her vase was sound.', '{np} {be} intact', 'Her vase was intact.'),
    ('Their vases were not sound.', '{poss} {np} {be} intact', 'Their vases were not intact.'),
    ("Their vases weren't sound.", '{poss} {np} {be} intact', 'Their vases were not intact.'),
    ('Her vase was not sound.', '{np} {be} not intact', 'Her vase was not intact.'),
    ('His vase was never sound.', '{np} {be} intact', 'His vase was never intact.'),
    ("Rob's vase was sound.", '{poss} {np} {be} intact', "Rob's vase was intact."),
    ("They saw Rob's vase was sound.", '{poss} {np} {be} intact', "They saw Rob's vase was intact."),
])
def test_source_possessor_auxiliary_number_and_negation_survive(dictionary, source, form, expected):
    start = next(i for i,t in enumerate(tokenize(source)) if t.norm in {'vase','vases'})
    result = rendered(dictionary, source, form, start=start)
    assert result and result[0] == expected


@pytest.mark.parametrize('source,form,start', [
    ('Her vase was sound.', 'soundness', 1),
    ('Her vase broke.', 'breakage', 1),
    ('Her vase cracked.', 'cracked vase', 1),
    ('Her vase was not sound.', 'vase was intact', 1),
    ('Her vase was sound.', 'vase was not intact', 1),
    ('Her vase was never sound.', 'vase was not intact', 1),
    ("The old boss's vase was sound.", '{poss} {np} {be} intact', 4),
    ("Jo and Sam's vase was sound.", '{poss} {np} {be} intact', 4),
])
def test_unrepresented_scope_or_ambiguous_owner_keeps_source(dictionary, source, form, start):
    assert rendered(dictionary, source, form, start=start) is None


@pytest.mark.parametrize('modal', ['can', 'could', 'would'])
def test_actual_modal_not_pattern_alternatives_decides_fidelity(dictionary, modal):
    source = f'I reckon it {modal} work.'
    tokens = tokenize(source)
    detection = Detection(1, len(tokens)-1, ('TEST',), 'vp', 3, 'test', '', captures={'np': tokens[2]})
    for candidate in ('can', 'could', 'would'):
        concept = parse_concept('TEST', {'plain': 'a separate name', 'plain_forms': {'vp': f'reckon {{np}} {candidate} work'}})
        result = plain_entry(concept, detection, dictionary, tokens=tokens)
        assert bool(result) == (candidate == modal)


def test_negation_cannot_move_over_a_bound_argument(dictionary):
    source = 'I cannot reckon the story.'
    tokens = tokenize(source)
    # The scoped phrase includes can/not and a captured nominal; not cannot move after it.
    detection = Detection(1, len(tokens)-1, ('TEST',), 'vp', 3, 'test', '', captures={'np': phrase_token(tokens[4:6])})
    concept = parse_concept('TEST', {'plain': 'a name', 'plain_forms': {'vp': 'can reckon {np} not'}})
    assert plain_entry(concept, detection, dictionary, tokens=tokens) is None


@pytest.mark.parametrize('cid,source', [
    ('HEARTBREAK', 'Her heart was broken.'),
    ('HEART_EFFORT', "Her heart wasn't in it."),
    ('HEART_EFFORT', "Her heart's in it."),
    ('DOUBT_IT', 'I doubt it could be done.'),
    ('DOUBT_IT', 'I doubt it would work.'),
])
def test_named_cases_preserve_source_without_faithful_authored_wording(dictionary, cid, source):
    tokens = tokenize(source)
    detection = next(d for d in read_meanings(tokens, dictionary).detections if cid in d.concepts)
    assert plain_entry(dictionary.concepts[cid], detection, dictionary, tokens=tokens) is None
    result = Translator(dictionary, lookup_embedder=None).translate(source, level=1, vulgarity=0, embellishment=0)
    assert source in result.text


@pytest.mark.parametrize('source,supported', [('Were they content?', True), ("Weren't they content?", False)])
def test_inverted_negative_scope_abstains_until_it_has_a_supported_form(dictionary, source, supported):
    tokens = tokenize(source)
    subject = next(t for t in tokens if t.norm == 'they')
    detection = Detection(0, len(tokens)-1, ('TEST',), 'clause', 3, 'test', '', question=True,
                          captures={'be': tokens[0], 'subj': subject})
    concept = parse_concept('TEST', {'plain': 'content', 'plain_forms': {'clause': '{subj} {be} happy'}})
    assert bool(plain_entry(concept, detection, dictionary, tokens=tokens)) is supported



def test_auxiliary_outside_replacement_is_not_duplicated(dictionary):
    tokens = tokenize('They were tired.')
    detection = Detection(2, 3, ('TEST',), 'predicate_adj', 3, 'test', '', captures={'be': tokens[1]})
    concept = parse_concept('TEST', {'plain': 'exhausted', 'plain_forms': {'predicate_adj': '{be} exhausted'}})
    assert plain_entry(concept, detection, dictionary, tokens=tokens) is None
