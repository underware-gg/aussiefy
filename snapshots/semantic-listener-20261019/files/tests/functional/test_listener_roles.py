"""Participant possessives retain the listener rather than borrow the speaking agent."""

import pytest

from aussiefy import morph
from aussiefy.detect import Detection
from aussiefy.realise import noun_slots
from aussiefy.select import binding_problem, form_problem
from aussiefy.text import Token


def render(translator, text, seed=0):
    return translator.translate(text, level=5, vulgarity=0, seed=seed, embellishment=0,
        embedder='none', document_type='custom', document_config={'profile': {
            'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}})


@pytest.mark.parametrize('source,expected', [
    ('She talked his ear off.', 'She bent his ear.'),
    ('He talked her ear off.', 'He bent her ear.'),
    ('They talked my ear off.', 'They bent my ear.'),
    ('She talked their ear off.', 'She bent their ear.'),
    ('She talked at length to Mary.', "She bent Mary's ear."),
])
def test_explicit_listener_is_retained(translator, source, expected):
    result = render(translator, source)
    assert result.text == expected
    for record in result.records:
        assert {candidate.entry.id for candidate in record.eligible} <= {'bend-ear', 'earbash'}


@pytest.mark.parametrize('source', ['She rambled about the trip.', 'They talked at length.',
    'She rambles.', 'They went on and on.'])
def test_missing_listener_does_not_become_the_speaker(translator, source):
    result = render(translator, source)
    candidates = {c.entry.id for r in result.records for c in r.eligible}
    assert not candidates & {'bend-ear', 'earbash'}
    assert candidates & {'bang-on', 'rabbit-on', 'yabber-on'}


def test_direct_possessive_binding_does_not_invent_an_object():
    token = Token('his', 0, 3, 'his', 0, 0)
    detection = Detection(0, 1, ('TALK_ON',), 'vp', 3, 'concept', 'talk {objposs} ear off', captures={'objposs': token})
    assert binding_problem('bend {objposs} ear', detection) is None
    assert binding_problem('earbash {obj}', detection) is not None
    assert form_problem('bang on', detection) == 'would discard {objposs}: his'
    assert noun_slots(detection)['objposs'] == 'his'


@pytest.mark.parametrize('form,expected', [('base', 'bend'), ('3sg', 'bends'), ('past', 'bent'),
    ('pp', 'bent'), ('ing', 'bending')])
def test_shared_bend_morphology(form, expected):
    assert morph.inflect('bend', form) == expected


@pytest.mark.parametrize('source', [
    'She talked at length to Mary and Jane.', 'She talked at length to him and her.',
    'She talked at Mary and Jane.', 'She talked at him and her.',
    'She talked at length to Mary Smith.', 'She talked at length to her friend.',
    "She talked at length to Mary's mother.", 'She talked at length to Mary of Sydney.',
    'She talked at length to Mary, Jane and Bob.',
    'She talked at length to Mary (and Jane).',
])
def test_partial_or_coordinated_listener_arguments_remain_whole(translator, source):
    result = render(translator, source)
    assert result.text.startswith('She talked at')
    assert not {'bend-ear', 'earbash'} & {c.entry.id for r in result.records for c in r.eligible}


@pytest.mark.parametrize('source', ['They scolded him and left.', 'They scolded him and shouted.',
    'They scolded him and Mary left.', 'They scolded him and promptly left.'])
def test_terminal_argument_completion_preserves_coordinated_verbs_and_clauses(translator, source):
    result = render(translator, source)
    assert any('SCOLD' in r.det.concepts for r in result.records)
    assert ' and ' + source.split(' and ', 1)[1] in result.text


@pytest.mark.parametrize('source', ['They tried the tool and the cheese.',
    'They scolded him and her.', 'They scolded Mary Smith.', 'They scolded her friend.'])
def test_completion_boundary_is_shared_beyond_speech_slang(translator, source):
    result = render(translator, source)
    assert not any(r.det.concepts and {'SCOLD', 'TRY_OUT'} & set(r.det.concepts) for r in result.records)


@pytest.mark.parametrize('markup', ['markdown', 'mdx'])
def test_opaque_listener_continuations_are_not_assumed_complete(translator, markup):
    from aussiefy import translate
    source = 'She talked at length to Mary `and Jane`.'
    result = translate(source, translator=translator, level=5, vulgarity=0, embellishment=0,
                       markup=markup, document_type='custom',
                       document_config={'profile': {'phonetic': 0}})
    assert result.text == source


@pytest.mark.parametrize("source", ["We tried mediation and hiring a lawyer.",
    "We tried painting and hiring a decorator."])
def test_coordinated_gerund_objects_are_not_partially_replaced(translator, source):
    for seed in range(4):
        result = render(translator, source, seed)
        assert not any("TRY_OUT" in record.det.concepts for record in result.records)
        assert "a burl and hiring" not in result.text


@pytest.mark.parametrize('source', [
    'She talked at length to Mary as well as Jane.',
    'She talked at length to Mary, as well as Jane.',
    'They scolded him as well as her.',
    'We tried mediation as well as hiring a lawyer.',
])
def test_multiword_coordinators_do_not_split_terminal_arguments(translator, source):
    result = render(translator, source)
    assert not any({'TALK_ON', 'SCOLD', 'TRY_OUT'} & set(record.det.concepts) for record in result.records)


@pytest.mark.parametrize('source', [
    'They scolded him as well as Jane did.',
])
def test_multiword_coordinator_preserves_finite_clause_continuations(translator, source):
    result = render(translator, source)
    assert any('SCOLD' in record.det.concepts for record in result.records)
    assert ' as well as ' + source.split(' as well as ', 1)[1] in result.text
