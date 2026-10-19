"""Corrections compose into the shared dictionary, rather than rewriting engine output."""

import asyncio
import json

import pytest
import yaml

import aussiefy
from aussiefy import Translator, load_dictionary
from aussiefy.schema import SchemaError
from aussiefy.vocabulary import Vocabulary

FORMAT = "aussiefy-dictionary-overlay/v1"


def overlay(tmp_path, name="correction.yaml", **operations):
    path = tmp_path / name
    path.write_text(yaml.safe_dump({"format": FORMAT, **operations}), encoding="utf-8")
    return path


@pytest.fixture
def correction(tmp_path):
    bad = overlay(tmp_path, "01-base.yaml",
                  add_concepts={"TEST_PERSON": {"description": "A person's role.",
                                               "triggers": {"np": ["a courageous volunteer"]}}},
                  add_entries=[{"id": "test-person", "form": "a digger", "concept": ["TEST_PERSON"],
                                "frame": "np", "replaces": ["a fearless helper"]}])
    fixed = overlay(tmp_path, "02-correction.yaml",
                    add_concepts={"TEST_BRAVE": {"description": "An explicitly courageous person.",
                                                "triggers": {"np": ["a courageous volunteer"]}}},
                    patch_concepts={"TEST_PERSON": {"triggers": {}}},
                    patch_entries={"test-person": {"form": "a brave bastard", "concept": ["TEST_BRAVE"],
                                                   "replaces": [], "vulgarity": 1}})
    return bad, fixed


def test_correction_removes_bad_routes_and_preserves_engine_guards(correction):
    original = Translator(load_dictionary(correction[:1]), lookup_embedder=None)
    fixed = Translator(load_dictionary(correction), lookup_embedder=None)
    text = "I met a courageous volunteer."
    assert "a digger" in original.translate(text, level=5).text
    result = fixed.translate(text, level=5, embellishment="deadset")
    assert "a brave bastard" in result.text
    record = next(r for r in result.records if r.chosen and r.chosen.entry.id == "test-person")
    assert record.det.concepts == ("TEST_BRAVE",)
    assert not any(p.entry_id == "test-person" for p in fixed.dictionary.patterns)
    assert not fixed.dictionary.concepts["TEST_PERSON"].triggers
    assert "bastard" not in fixed.translate(text, level=5, vulgarity="nan").text
    assert "a digger" in original.translate(text, level=5).text
    assert fixed.dictionary.entries["test-person"].origin_file == str(correction[1])


def test_all_consumers_use_the_same_compiled_correction(correction):
    tr = Translator(load_dictionary(correction), lookup_embedder=None)
    text = "I met a courageous volunteer."
    options = dict(level=5, vulgarity=1, embellishment="deadset", translator=tr)
    assert aussiefy.lookup("a courageous volunteer", **options)["results"][0]["id"] == "test-person"
    assert aussiefy.plan(text, **options)["draft"] == "I met a brave bastard."
    changes = aussiefy.translate_changes(text, **options)
    swap = next(c for c in changes.changes if c["kind"] == "substitution")
    assert swap["entry_id"] == "test-person"
    assert not any(o["rendered"] == "a digger" for o in swap["alternatives"])
    issues = aussiefy.lint("A brave bastard.", level=5, vulgarity=0, suggest=False, translator=tr)["issues"]
    assert any(i["kind"] == "too_vulgar" and "brave bastard" in i["phrase"] for i in issues)
    from aussiefy.mcp_server import build_server
    server = build_server(translator=tr)
    result = asyncio.run(server.call_tool("aussie_translate", {"text": text, "level": 5,
                                                            "vulgarity": 1, "embellishment": "deadset"}))
    assert "a brave bastard" in str(result)


def test_field_replacement_order_and_sidecar_source_clearing(tmp_path, dictionary, data_copy):
    sidecar = yaml.safe_load((data_copy / "sources.yaml").read_text())
    eid = next(eid for eid, urls in sidecar.items() if urls and eid in dictionary.entries)
    first = overlay(tmp_path, "first.yaml", patch_entries={eid: {"sources": [], "notes": "first", "intensity": 3}},
                    patch_concepts={"BUSY": {"triggers": {"predicate_adj": ["extremely busy@4"]}}})
    second = overlay(tmp_path, "second.yaml", patch_entries={eid: {"notes": "second"}})
    d = load_dictionary([first, second])
    assert d.entries[eid].sources == ()
    assert d.entries[eid].notes == "second" and d.entries[eid].intensity == 3
    assert d.concepts["BUSY"].triggers == {"predicate_adj": ("extremely busy@4",)}
    assert dictionary.entries[eid].sources
    assert [c["origin"] for c in d.overlay_changes][-1] == str(second)


def test_directory_order_matches_legacy_yaml_then_yml_order(tmp_path):
    overlay(tmp_path, "z.yaml", patch_entries={"mate": {"notes": "yaml"}})
    overlay(tmp_path, "a.yml", patch_entries={"mate": {"notes": "yml"}})
    (tmp_path / "nested").mkdir()
    overlay(tmp_path / "nested", patch_entries={"mate": {"notes": "nested"}})
    assert load_dictionary([tmp_path]).entries["mate"].notes == "yml"


@pytest.mark.parametrize("operations, message", [
    ({"format": "unknown"}, "format must be"),
    ({"typo": {}}, "unknown overlay fields"),
    ({"add_concepts": []}, "add_concepts must be a mapping"),
    ({"add_entries": {}}, "add_entries must be a list"),
    ({"patch_entries": []}, "patch_entries must be a mapping"),
    ({"patch_entries": {"absent": {"notes": "x"}}}, "unknown entry 'absent'"),
    ({"patch_concepts": {"ABSENT": {"triggers": {}}}}, "unknown concept 'ABSENT'"),
    ({"add_concepts": {"BUSY": {}}}, "duplicate concept 'BUSY'"),
    ({"add_entries": [{"id": "mate"}]}, "duplicate id 'mate'"),
    ({"patch_entries": {"mate": {"id": "new-mate"}}}, "unknown fields"),
    ({"patch_entries": {"mate": {"unknown": True}}}, "unknown fields"),
    ({"patch_entries": {"mate": {"vulgarity": 99}}}, "vulgarity"),
    ({"patch_entries": {"mate": {"insult": "no"}}}, "must be true or false"),
    ({"patch_entries": {"mate": {"gloss": ["wrong"]}}}, "must be text"),
    ({"patch_entries": {"mate": {"plural": ["mates"]}}}, "plural"),
    ({"patch_entries": {"mate": {"weight": float("nan")}}}, "positive finite"),
    ({"patch_entries": {"mate": {"weight": float("inf")}}}, "positive finite"),
    ({"patch_entries": {"mate": {"slots": False}}}, "must be a mapping"),
    ({"patch_concepts": {"BUSY": {"description": []}}}, "description must be text"),
    ({"patch_concepts": {"BUSY": {"person": "yes"}}}, "must be true or false"),
    ({"patch_concepts": {"BUSY": {"unknown": True}}}, "unknown fields"),
    ({"patch_concepts": {"BUSY": {"triggers": False}}}, "must be a mapping"),
    ({"patch_concepts": {"BUSY": {"triggers": []}}}, "must be a mapping"),
    ({"add_concepts": {"NEW": {"unknown": True}}}, "unknown field"),
    ({"add_concepts": {"NEW": []}}, "expected a mapping"),
])
def test_invalid_overlay_operations_fail_with_origin(tmp_path, operations, message):
    path = overlay(tmp_path, **operations)
    with pytest.raises(SchemaError) as exc:
        load_dictionary([path])
    assert message in str(exc.value) and str(path) in str(exc.value)


def test_a_later_layer_cannot_hide_an_invalid_operation(tmp_path):
    bad = overlay(tmp_path, "bad.yaml", patch_entries={"mate": {"vulgarity": 99}})
    good = overlay(tmp_path, "good.yaml", patch_entries={"mate": {"vulgarity": 0}})
    with pytest.raises(SchemaError, match="vulgarity"):
        load_dictionary([bad, good])


@pytest.mark.parametrize("pure_python", [False, True])
@pytest.mark.parametrize("text", [
    "format: aussiefy-dictionary-overlay/v1\npatch_entries:\n  mate: {notes: first}\n  mate: {notes: second}\n",
    "format: aussiefy-dictionary-overlay/v1\npatch_entries:\n  mate: {notes: first, notes: second}\n",
    "format: aussiefy-dictionary-overlay/v1\npatch_entries:\n  mate: {<<: {notes: first, notes: second}}\n",
    "format: aussiefy-dictionary-overlay/v1\npatch_entries:\n  mate: {<<: {notes: first}, <<: {notes: second}}\n",
])
def test_duplicate_yaml_keys_are_errors(tmp_path, monkeypatch, pure_python, text):
    from aussiefy import loader
    if pure_python:
        monkeypatch.setattr(loader, "_YAML_LOADER", yaml.SafeLoader)
    path = tmp_path / "duplicate.yaml"
    path.write_text(text)
    with pytest.raises(SchemaError, match="duplicate mapping key"):
        load_dictionary([path])


@pytest.mark.parametrize("pure_python", [False, True])
def test_legacy_yaml_anchors_and_merge_keys_remain_supported(tmp_path, monkeypatch, pure_python):
    from aussiefy import loader
    if pure_python:
        monkeypatch.setattr(loader, "_YAML_LOADER", yaml.SafeLoader)
    path = tmp_path / "anchors.yaml"
    path.write_text("- &base {id: overlay-one, form: first form, concept: [BUSY], frame: predicate_adj}\n"
                    "- &second {<<: *base, id: overlay-two, form: second form}\n"
                    "- {<<: [*second, *base], id: overlay-three}\n")
    d = load_dictionary([path])
    assert d.entries["overlay-one"].form == "first form"
    assert d.entries["overlay-two"].form == "second form"
    assert d.entries["overlay-three"].form == "second form"


def test_extra_entry_directory_can_replace_builtin_inventory_without_losing_sources(dictionary):
    from aussiefy.loader import DATA_DIR
    d = load_dictionary([DATA_DIR / "entries"], include_builtin=False)
    assert d.entries.keys() == dictionary.entries.keys()
    for eid, entry in dictionary.entries.items():
        assert d.entries[eid].sources == entry.sources


def test_raw_composition_keeps_explicit_defaults_and_does_not_mutate_inputs():
    original = {"id": "x", "form": "thing", "frame": "np", "concept": ["TEST"], "intensity": 3}
    patch = {"format": FORMAT, "patch_entries": {"x": {"variants": [], "plain_sense": False}}}
    vocabulary = Vocabulary({"TEST": {"triggers": {}}})
    errors = []
    vocabulary.add_entries([original], "base", errors)
    vocabulary.apply(patch, "patch", errors)
    assert not errors
    assert vocabulary.entries["x"]["intensity"] == 3
    assert vocabulary.entries["x"]["variants"] == [] and vocabulary.entries["x"]["plain_sense"] is False
    assert "variants" not in original
    assert patch["patch_entries"]["x"] == {"variants": [], "plain_sense": False}


def test_cli_reports_correction_and_uses_it(correction, capsys):
    from aussiefy.cli import main
    args = [item for path in correction for item in ["--dict", str(path)]]
    assert main(["validate", *args]) == 0
    assert f"overlay {correction[1]}: patch entry test-person" in capsys.readouterr().out
    assert main(["show", "test-person", *args]) == 0
    assert "# overlay" in capsys.readouterr().out
    assert main(["translate", "I met a courageous volunteer.", "-l", "5", "-e", "deadset", "--json", *args]) == 0
    assert json.loads(capsys.readouterr().out)["text"] == "I met a brave bastard."
