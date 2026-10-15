import json

import pytest

from aussiefy import harness, models
from aussiefy.embed import make_embedder
from aussiefy.errors import UserError


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path))
    monkeypatch.setattr(models, "_cached", None)
    return tmp_path


def test_bundled_by_default_and_never_imports_torch(home, translator, monkeypatch):
    import builtins

    real, attempted = builtins.__import__, set()

    def recording(name, *a, **k):   # records the attempt even where torch isn't installed, or is already loaded
        attempted.add(name.split(".")[0])
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", recording)
    st = models.status()
    assert not st["enabled"] and not st["usable"]   # no sentence-transformers model unless installed
    assert st["active"].startswith("bundled:") and st["bundled"]["enabled"]
    assert models.local_embedder().name == st["active"] == make_embedder("configured").name
    with pytest.raises(UserError, match="embedder install"):   # asked for by name, no quiet stand-in
        make_embedder("local")
    harness.lookup("very busy", translator=translator)
    assert attempted, "the hook saw no imports at all"   # it does see the lazy ones made along the way
    assert not {"torch", "sentence_transformers"} & attempted, attempted


def test_bundled_can_be_switched_off(home, dictionary):
    from aussiefy import Translator

    assert models.set_bundled(False)["active"] == "ngram" and models.local_embedder() is None
    # a translator resolves the machine's setting once, on first use: a new one sees the change
    fresh = Translator(dictionary)
    assert fresh.lookup_embedder is None
    assert all(r["match"] != "meaning (local model)"
               for r in harness.lookup("knackered beyond belief", translator=fresh)["results"])
    injected = Translator(dictionary, lookup_embedder=None)
    assert harness.lookup("very tired", translator=injected)["results"]
    with pytest.raises(UserError, match="embedder install"):
        make_embedder("local")
    assert models.set_bundled(True)["active"].startswith("bundled:")


def test_enable_needs_an_install(home):
    with pytest.raises(UserError, match="embedder install"):
        models.set_enabled(True)


@pytest.mark.parametrize("field,value", [("enabled", "false"), ("path", 3), ("model", [])])
def test_nested_config_fields_fail_before_use(home, field, value, capsys):
    from aussiefy.cli import main

    path = home / "config.json"
    path.write_text(json.dumps({"embedder": {field: value}}))
    assert main(["embedder", "status"]) == 2
    assert str(path) in capsys.readouterr().err


def test_incomplete_saved_model_is_refused_before_status(home, monkeypatch):
    (home / "config.json").write_text(json.dumps({"embedder": {"enabled": True, "path": str(home)}}))
    monkeypatch.setattr(models, "packages_available", lambda: True)
    with pytest.raises(UserError, match="needs a non-empty model and path"):
        models.status()


@pytest.mark.parametrize("config", [{}, {"embedder": {}}])
def test_no_saved_model_is_a_valid_config(home, config):
    (home / "config.json").write_text(json.dumps(config))
    assert not models.status()["usable"]


def test_dry_run_install_is_explicit_and_changes_nothing(home):
    steps = []
    out = models.install(dry_run=True, log=steps.append)
    assert out["dry_run"] and any("download.pytorch.org/whl/cpu" in s for s in steps)
    assert not (home / "config.json").exists()
    steps.clear()
    models.install(torch="skip", dry_run=True, log=steps.append)
    assert not any("pip install torch" in s for s in steps)


def test_installed_but_disabled_is_not_used(home, monkeypatch):
    model_dir = home / "models" / "tiny"
    model_dir.mkdir(parents=True)
    (home / "config.json").write_text(json.dumps({"embedder": {"model": "tiny", "path": str(model_dir),
                                                               "enabled": False}}))
    monkeypatch.setattr(models, "packages_available", lambda: True)
    assert not models.usable() and models.local_embedder().name.startswith("bundled:")   # falls back, no torch
    assert models.set_enabled(True)["usable"]
    assert not models.set_enabled(False)["usable"]
    assert models.remove()["model"] is None and not model_dir.exists()


@pytest.mark.parametrize("config", ["[]", '{"embedder": "tiny"}', '{"bundled": "no"}'])
def test_a_config_of_the_wrong_shape_is_refused(home, config):
    (home / "config.json").write_text(config)
    with pytest.raises(UserError, match="config.json should be a JSON object"):
        models.status()
