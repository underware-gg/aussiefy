"""Meaning and argument ownership distinguish annoyance from fatigue or illness."""
import pytest

from aussiefy import Translator, harness, lookup, translate_changes

PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1},
           'stack': 0, 'swearing': {'infix': 0, 'exclaim': 0, 'closer': 0}}
OPTIONS = {'level': 5, 'vulgarity': 3, 'embellishment': 0,
           'document_type': 'custom', 'document_config': {'profile': PROFILE}}


@pytest.mark.parametrize('query', ['sick of work', 'tired of life', 'sick and tired of work', 'sick to death of work'])
@pytest.mark.parametrize('backend', [None, 'bundled'])
def test_contextual_discovery_returns_annoyance_not_literal_state(dictionary, query, backend):
    tr = Translator(dictionary, lookup_embedder=backend)
    found = lookup(query, translator=tr, vulgarity=3)['results']
    assert found and all('FED_UP' in dictionary.entries[e['id']].concept for e in found)
    # Direct vocabulary explanation remains broader than an inferred contextual replacement.
    direct = lookup('knackered', translator=tr, vulgarity=3)['results']
    assert any(e['id'] == 'knackered' for e in direct)


@pytest.mark.parametrize('source', ['She is sick of work.', 'She is tired of life.',
    'She is sick and tired of work.', 'She is sick to death of work.'])
@pytest.mark.parametrize('backend', ['none', 'ngram', 'bundled'])
def test_automatic_predicate_cannot_discard_the_object(translator, source, backend):
    result = translator.translate(source, embedder=backend, **OPTIONS)
    assert result.text == source
    assert len(result.records) == 1 and result.records[0].det.concepts == ('FED_UP',)
    record = result.records[0]
    assert record.det.captures['np'].text in {'work', 'life'}
    assert not record.eligible
    assert any('discard {np}' in reason for _, reason in record.rejected)
    changes = translate_changes(source, translator=translator, embedder=backend, **OPTIONS)
    assert changes.text == source
    assert not any(c['kind'] == 'substitution' for c in changes.changes)


@pytest.mark.parametrize('source,cid', [('She is tired from work.', 'TIRED'), ('She is sick with flu.', 'SICK')])
def test_literal_state_controls_keep_their_real_meanings(translator, source, cid):
    result = translator.translate(source, embedder='none', **OPTIONS)
    assert any(cid in r.det.concepts and r.eligible for r in result.records)
    assert result.text != source


def test_planning_preserves_arguments_too(translator):
    source = 'She is tired of life.'
    plan = harness.plan(source, translator=translator, **OPTIONS)
    assert plan['draft'] == source
