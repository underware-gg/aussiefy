"""Training labels must not simultaneously attract and repel the same normalised pair."""
import copy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts import train_embedder as trainer


@pytest.fixture
def recipe(monkeypatch):
    recipe = copy.deepcopy(trainer.load_recipe())
    recipe['sources']['wordnet']['enabled'] = False
    monkeypatch.setattr(trainer, 'R', recipe)
    return recipe


def test_complete_positive_trigger_is_not_its_own_wrong_sense(recipe):
    concept = SimpleNamespace(description='A synthetic meaning.', triggers={
        'predicate_adj': ['zzbase !continuation|wrong', 'zzbase continuation !wrong']})
    d = SimpleNamespace(concepts={'ZZ': concept})
    entry = SimpleNamespace(form='zzform', concept=['ZZ'], gloss='Synthetic meaning.')
    negatives = trainer.sense_negatives(d, [entry])
    assert negatives
    assert all(anchor != 'zzbase continuation' for anchor, _ in negatives)
    assert ('zzbase wrong', 'zzform') in negatives
    assert ('zzbase continuation wrong', 'zzform') in negatives
    assert ('zzbase continuation wrong', 'A synthetic meaning.') in negatives


def test_rain_exclusions_retain_invalid_continuations_but_not_the_longer_rain_trigger(recipe):
    d = trainer.load_dictionary()
    negatives = trainer.sense_negatives(d, trainer.entries(d))
    rain_forms = {trainer.clean(e.form) for e in trainer.entries(d) if 'RAINING_HARD' in e.concept}
    assert not any(a == 'it pouring down' and b in rain_forms for a, b in negatives)
    assert any(a == 'it pouring down onto' and b in rain_forms for a, b in negatives)


def test_conflicts_are_undirected_and_normalised_without_hiding_negative_sets():
    rows = ([('Alpha word', 'Beta word')], [('beta WORD', '  ALPHA   word ')], [('Alpha word', 'Beta word')])
    assert trainer.pair_conflicts(rows) == {
        'wrong_sense': [['alpha word', 'beta word']], 'opposite': [['alpha word', 'beta word']], 'negative_self': []}
    assert trainer.pair_conflicts(([('a', 'b')], [('a', 'c')], [])) == {'wrong_sense': [], 'opposite': [], 'negative_self': []}


def test_generated_extra_conflicts_fail_instead_of_silently_dropping_labels(monkeypatch):
    monkeypatch.setattr(trainer, 'pair_sets', lambda *_: ([('a', 'b')], [('b', 'a')], []))
    with pytest.raises(ValueError, match='Contradictory training labels'):
        trainer.checked_pairs(None, [])


@pytest.mark.parametrize('command', ['train', 'distil'])
def test_label_conflicts_stop_before_loading_any_model(monkeypatch, tmp_path, recipe, command):
    def forbidden(*args, **kwargs):
        raise AssertionError('Model loading/distillation was reached')
    monkeypatch.setitem(sys.modules, 'sentence_transformers', SimpleNamespace(SentenceTransformer=forbidden))
    monkeypatch.setitem(sys.modules, 'sentence_transformers.models', SimpleNamespace(StaticEmbedding=forbidden))
    monkeypatch.setitem(sys.modules, 'model2vec', SimpleNamespace(StaticModel=forbidden))
    monkeypatch.setitem(sys.modules, 'model2vec.distill', SimpleNamespace(distill=forbidden))
    monkeypatch.setitem(sys.modules, 'huggingface_hub', SimpleNamespace(snapshot_download=forbidden))
    monkeypatch.setattr(trainer, 'load_dictionary', lambda: None)
    monkeypatch.setattr(trainer, 'split', lambda *_: ([], []))
    monkeypatch.setattr(trainer, 'pair_sets', lambda *_: ([('a', 'b')], [('b', 'a')], []))
    with pytest.raises(ValueError, match='Contradictory training labels'):
        if command == 'train':
            trainer.train(tmp_path, 0)
        else:
            trainer.distil(tmp_path, 0, True)


@pytest.mark.parametrize('conflicting', [True, False])
def test_audit_cli_reports_and_exits_for_actual_label_state(monkeypatch, tmp_path, capsys, conflicting):
    report = tmp_path / 'audit.json'
    monkeypatch.setattr(trainer, 'load_dictionary', lambda: None)
    monkeypatch.setattr(trainer, 'split', lambda *_: ([SimpleNamespace(id='e', concept=['A', 'B'])], []))
    monkeypatch.setattr(trainer, 'pair_sets', lambda *_: ([('a', 'b')], [('b', 'a')] if conflicting else [], []))
    monkeypatch.setattr(sys, 'argv', ['trainer', 'audit', '--holdout', '0', '--report', str(report)])
    assert trainer.main() == int(conflicting)
    data = json.loads(report.read_text())
    assert data['counts']['positive'] == 1
    assert bool(data['conflicts']['wrong_sense']) == conflicting
    assert data['multi_concept_entries'] == [{'id': 'e', 'concepts': ['A', 'B']}]
    assert data['holdout'] == 0
    assert len(data['dictionary_sha256']) == 64
    assert not capsys.readouterr().out


@pytest.mark.parametrize('operator', ['!', '!='])
def test_exclusion_operators_use_the_matchers_own_plain_tokens(recipe, operator):
    d = SimpleNamespace(concepts={'ZZ': SimpleNamespace(description='Synthetic.',
        triggers={'predicate_adj': [f'zzbase {operator}with|other']})})
    entry = SimpleNamespace(form='zzform', concept=['ZZ'], gloss='Test.')
    negatives = trainer.sense_negatives(d, [entry])
    assert ('zzbase with', 'zzform') in negatives
    assert ('zzbase other', 'zzform') in negatives
    assert not any('=' in a or '!' in a for a, _ in negatives)


def test_other_concepts_positive_trigger_does_not_hide_a_wrong_sense(recipe):
    d = SimpleNamespace(concepts={
        'ZZ': SimpleNamespace(description='First.', triggers={'predicate_adj': ['zzbase !other']}),
        'YY': SimpleNamespace(description='Second.', triggers={'predicate_adj': ['zzbase other']})})
    entry = SimpleNamespace(form='zzform', concept=['ZZ'], gloss='First.')
    assert ('zzbase other', 'zzform') in trainer.sense_negatives(d, [entry])


@pytest.mark.parametrize('has_target', [True, False])
def test_nonterminal_exclusion_refusal_applies_only_when_generating_rows(recipe, has_target):
    d = SimpleNamespace(concepts={'ZZ': SimpleNamespace(description='Synthetic.',
        triggers={'predicate_adj': ['zzbase !other zzsuffix']})})
    entry = SimpleNamespace(form='zzform', concept=['ZZ'], gloss='Test.')
    if has_target:
        with pytest.raises(ValueError, match='nonterminal exclusion'):
            trainer.sense_negatives(d, [entry])
    else:
        assert trainer.sense_negatives(d, []) == []


def test_negative_self_pairs_are_impossible_even_without_a_positive_pair():
    assert trainer.pair_conflicts(([], [(' SAME word ', 'same  WORD')], []))['negative_self'] == [
        ['same word', 'same word']]
