"""The trainer's public CLI accepts recipe options without changing the caller's argv."""

import sys
import types

import pytest

from scripts import train_embedder


@pytest.mark.parametrize('reversed_neighbours', [False, True])
def test_wordnet_neighbour_order_cannot_change_training_selection(monkeypatch, reversed_neighbours):
    class Synset:
        def __init__(self, name, words, neighbours=()):
            self.key, self.words, self.neighbours = name, words, neighbours

        def name(self):
            return self.key

        def lemmas(self):
            return [types.SimpleNamespace(name=lambda w=w: w) for w in self.words]

        def similar_tos(self):
            return self.neighbours

    neighbours = [Synset('a.a.01', ['neighbour_a']), Synset('b.a.01', ['neighbour_b'])]
    if reversed_neighbours:
        neighbours.reverse()
    primary = Synset('base.a.01', ['base', 'primary_z', 'primary_a'], neighbours)
    later_sense = Synset('later.a.01', ['wrong_sense'])
    corpus = types.ModuleType('nltk.corpus')
    corpus.wordnet = types.SimpleNamespace(synsets=lambda word, pos: [primary, later_sense])
    nltk = types.ModuleType('nltk')
    nltk.corpus = corpus
    monkeypatch.setitem(sys.modules, 'nltk', nltk)
    monkeypatch.setitem(sys.modules, 'nltk.corpus', corpus)
    assert train_embedder.wordnet_synonyms('base', 'a', 1) == [
        'primary z', 'primary a', 'neighbour a', 'neighbour b']


@pytest.mark.parametrize('pattern,expected', [
    ('quit !of ^end@4','quit'),
    ('hungry ^person','hungry'),
    ('little ^adj','little'),
    ('great !war|deal@4','great'),
    ('Ordinary words','ordinary words'),
    ('{subj} {have} had {poss} fill ^person@4','they have had their fill'),
])
def test_training_binds_recipe_slots_before_shared_annotation_cleanup(pattern, expected, monkeypatch):
    monkeypatch.setattr(train_embedder,'R',{'pairs':{'placeholders':{
        'subj':'they','have':'have','poss':'their'}}})
    assert train_embedder.clean(pattern) == expected


@pytest.mark.parametrize("before", [True, False])
def test_recipe_option_works_on_either_side_of_the_command(tmp_path, monkeypatch, before):
    recipe = tmp_path / "recipe.yaml"
    recipe.write_text("holdout: 0.25\n")
    option = ["--recipe", str(recipe)]
    argv = ["trainer", *(option + ["check"] if before else ["check"] + option)]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(train_embedder, "R", {})
    monkeypatch.setattr(train_embedder, "RECIPE_PATH", train_embedder.RECIPE_PATH)
    observed = []
    monkeypatch.setattr(train_embedder, "check", lambda model: observed.append(train_embedder.R["holdout"]) or 0)
    assert train_embedder.main() == 0
    assert observed == [0.25] and sys.argv == argv


def test_missing_recipe_argument_is_a_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["trainer", "check", "--recipe"])
    with pytest.raises(SystemExit) as exc:
        train_embedder.main()
    assert exc.value.code == 2
    assert "--recipe: expected one argument" in capsys.readouterr().err


@pytest.mark.parametrize("command", [[], ["check"]])
def test_recipe_option_is_discoverable_in_help(monkeypatch, capsys, command):
    monkeypatch.setattr(sys, "argv", ["trainer", *command, "--help"])
    monkeypatch.setattr(train_embedder, "R", {})
    monkeypatch.setattr(train_embedder, "RECIPE_PATH", train_embedder.RECIPE_PATH)
    with pytest.raises(SystemExit) as exc:
        train_embedder.main()
    assert exc.value.code == 0 and "--recipe" in capsys.readouterr().out
