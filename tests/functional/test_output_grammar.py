"""Declared whole-output contracts distinguish unknown metadata from unknown source fit."""

from dataclasses import replace

import pytest

from aussiefy import pos
from aussiefy.detect import Detection
from aussiefy.grammar import GrammarRequirements, grammar_problem, parse_requirements
from aussiefy.schema import Entry, SchemaError, parse_entry
from aussiefy.text import tokenize


@pytest.mark.parametrize('raw', [[], {'following': []}, {'following': ['somewhere']},
    {'following': [False]}, {'aspect': []}, {'voice': 'middle'}, {'unknown': True}])
def test_invalid_grammar_is_a_named_loader_error(raw):
    with pytest.raises(SchemaError, match='example: grammar'):
        parse_requirements(raw, 'example')


def test_grammar_roundtrips_as_minimal_dictionary_data():
    raw = {'id': 'example', 'form': 'hanging out', 'concept': ['EAGER'], 'frame': 'predicate_adj',
           'grammar': {'following': ['infinitive', 'prep:for'], 'aspect': 'state'}}
    entry = parse_entry(raw)
    assert entry.to_dict()['grammar'] == raw['grammar']
    assert parse_entry(entry.to_dict()) == entry
    assert 'grammar' not in replace(entry, grammar=GrammarRequirements()).to_dict()


@pytest.mark.parametrize('text,allowed,problem', [
    ('eager to see it.', ['infinitive'], False),
    ('eager for the weekend.', ['prep:for'], False),
    ('eager for', ['prep:for'], True),
    ('eager.', ['infinitive', 'prep:for'], True),
    ('throw the ball.', ['np'], False),
    ('think the plan works.', ['content'], False),
    ('vomited all night.', ['adverb'], False),
    ('retired yesterday.', ['adverb'], False),
])
def test_contract_reads_the_boundary_after_the_whole_phrase(text, allowed, problem):
    tokens = tokenize(text)
    entry = Entry('example', 'example', ('EXAMPLE',), 'vp',
                  grammar=GrammarRequirements(following=tuple(allowed)))
    det = Detection(0, 1, ('EXAMPLE',), 'vp', 3, 'trigger', tokens[0].norm)
    result = grammar_problem(entry, det, tokens, pos.tag([t.text for t in tokens]))
    assert bool(result) is problem


def test_unknown_annotation_is_different_from_a_required_unknown_boundary():
    tokens = tokenize('eager')
    det = Detection(0, 1, ('EAGER',), 'predicate_adj', 3, 'trigger', 'eager')
    entry = Entry('example', 'hanging out', ('EAGER',), 'predicate_adj')
    tags = pos.tag([t.text for t in tokens])
    assert grammar_problem(entry, det, tokens, tags, complete=False) is None
    required = replace(entry, grammar=GrammarRequirements(following=('infinitive',)))
    assert 'cannot establish' in grammar_problem(required, det, tokens, tags, complete=False)


@pytest.mark.parametrize('text,end', [("retire, I'll go fishing.", 1), ("bundle up, it's cold.", 2)])
def test_a_settled_new_clause_is_not_an_argument(text, end):
    from aussiefy.context import following_shape
    tokens = tokenize(text)
    assert following_shape(tokens, end, pos.tag([t.text for t in tokens])) == 'none'
