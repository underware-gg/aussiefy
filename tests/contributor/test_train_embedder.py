"""The trainer's public CLI accepts recipe options without changing the caller's argv."""

import sys

import pytest

from scripts import train_embedder


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
