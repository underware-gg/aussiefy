from copy import deepcopy

import pytest
import yaml

from aussiefy import rounds
from aussiefy.schema import SchemaError


@pytest.fixture
def prepared(tmp_path, data_copy):
    rd = tmp_path / "zz-meta"
    (rd / "verify").mkdir(parents=True)
    (rd / "round.yaml").write_text("name: zz meta\noutput: zz-meta.yaml\n")
    verdict = {
        "decision": "add_entry",
        "entry": {"id": "zzmeta", "form": "zzmeta", "concept": ["ZZ_META"], "frame": "np"},
        "new_concept": {
            "id": "ZZ_META",
            "description": "A person test.",
            "triggers": {"np": ["zztestperson"]},
            "not_in": ["technical"],
            "person": True,
            "neutral_person": True,
        },
    }
    (rd / "verify" / "verdicts-a.yaml").write_text(yaml.safe_dump([verdict]))
    return rounds.RoundConfig.load(rd), data_copy


def plan(config, data):
    return rounds.plan_round(config, rounds.base_dictionary(config, data))


def test_full_metadata_and_explicit_entryless_guard(prepared):
    config, data = prepared
    path = config.directory / "concept_fixes.yaml"
    path.write_text("ZZ_GUARD:\n  description: Guard only.\n  triggers: {np: [zzguard]}\n  not_in: [technical]\n")
    config = rounds.RoundConfig.load(config.directory)
    p = plan(config, data)
    d = p.write(data)
    assert d.concepts["ZZ_META"].person and d.concepts["ZZ_META"].neutral_person
    assert d.concepts["ZZ_META"].not_in == {"technical"}
    assert "ZZ_GUARD" in d.concepts and not d.idioms_for(("ZZ_GUARD",))
    assert p.new_concepts["ZZ_META"]["not_in"] == ["technical"]


def test_reapplication_preserves_hand_metadata_comments_and_next_section(prepared):
    config, data = prepared
    plan(config, data).write(data)
    path = data / "concepts.yaml"
    text = path.read_text().replace("description: A person test.", "description: Hand reviewed. # keep this comment")
    text += "\n# --- later owner ----------------\nZZ_LATER:\n  description: Later.\n  triggers: {np: [zzlater]}\n"
    path.write_text(text)
    plan(config, data).write(data)
    assert path.read_text() == text
    assert yaml.safe_load(path.read_text())["ZZ_META"]["description"] == "Hand reviewed."


def test_explicit_fix_updates_one_record_and_preserves_neighbours(prepared):
    config, data = prepared
    plan(config, data).write(data)
    path = data / "concepts.yaml"
    text = (
        path.read_text()
        + "\n# --- later owner ----------------\nZZ_LATER:\n  description: Later. # keep\n  triggers: {np: [zzlater]}\n"
    )
    path.write_text(text)
    config.concept_fixes = {"ZZ_META": {"not_in": ["official"], "person": False}}
    d = plan(config, data).write(data)
    assert d.concepts["ZZ_META"].not_in == {"official"} and not d.concepts["ZZ_META"].person
    assert "# --- later owner ----------------\nZZ_LATER:\n  description: Later. # keep" in path.read_text()
    after = path.read_text()
    plan(config, data).write(data)
    assert path.read_text() == after


def test_fix_for_existing_concept_can_replace_triggers(prepared):
    config, data = prepared
    config.concept_fixes = {"TIRED": {"not_in": ["technical"], "triggers": {"predicate_adj": ["zzexhausted"]}}}
    d = plan(config, data).write(data)
    assert d.concepts["TIRED"].not_in == {"technical"}
    assert d.concepts["TIRED"].triggers == {"predicate_adj": ("zzexhausted",)}


def test_second_sense_requires_explicit_permission_and_a_new_concept(prepared):
    config, data = prepared
    original = {
        "decision": "add_entry",
        "entry": {"id": "zz-knackered", "form": "knackered", "concept": ["ZZ_META"], "frame": "np"},
    }
    config.verdicts.append(("second", deepcopy(original)))
    assert "zz-knackered" not in [e["id"] for e in plan(config, data).entries]
    config.verdicts[-1][1]["allow_existing_form"] = True
    p = plan(config, data)
    assert "zz-knackered" in [e["id"] for e in p.entries]
    p.write(data)
    config.verdicts[-1][1]["entry"]["concept"] = ["TIRED"]
    assert "zz-knackered" not in [e["id"] for e in plan(config, data).entries]


def test_invalid_concept_fix_keeps_files_untouched(prepared):
    config, data = prepared
    before = (data / "concepts.yaml").read_text()
    config.concept_fixes = {"TIRED": {"person": "yes"}}
    with pytest.raises(SchemaError):
        plan(config, data).write(data)
    assert (data / "concepts.yaml").read_text() == before
    assert not (data / "entries" / "zz-meta.yaml").exists()


def test_new_guard_and_fixes_can_be_added_after_initial_write(prepared):
    config, data = prepared
    plan(config, data).write(data)
    config.concept_fixes = {"ZZ_GUARD": {"triggers": {"np": ["zzguard"]}}}
    path = data / "concepts.yaml"
    d = plan(config, data).write(data)
    assert "ZZ_GUARD" in d.concepts and path.read_text().count(config.marker) == 1
    after = path.read_text()
    plan(config, data).write(data)
    assert path.read_text() == after


def test_explicit_fix_preserves_later_section_without_eof_newline(prepared):
    config, data = prepared
    plan(config, data).write(data)
    path = data / "concepts.yaml"
    suffix = "\n# --- next section ----------------\nZZ_NEXT:\n  description: Next.\n  triggers: {np: [zznext]}"
    path.write_text(path.read_text() + suffix)
    config.concept_fixes = {"ZZ_META": {"person": False}}
    plan(config, data).write(data)
    assert path.read_text().endswith(suffix)


def test_a_nonmapping_concept_fix_is_rejected(prepared):
    config, data = prepared
    config.concept_fixes = {"TIRED": False}
    with pytest.raises(SchemaError, match="expected concept fields"):
        plan(config, data)


def test_new_concept_false_metadata_is_not_discarded(prepared):
    config, data = prepared
    config.verdicts[0][1]["new_concept"]["person"] = False
    p = plan(config, data)
    assert p.new_concepts["ZZ_META"]["person"] is False
    assert not p.write(data).concepts["ZZ_META"].person


def test_explicit_trigger_fixes_reapply_to_preserved_concepts(prepared):
    config, data = prepared
    plan(config, data).write(data)
    path = data / "concepts.yaml"
    path.write_text(path.read_text().replace("description: A person test.", "description: Hand reviewed."))
    config.trigger_fixes = {
        "add": {"ZZ_META": {"np": ["zzadded"]}},
        "remove": {"ZZ_META": {"np": ["zztestperson"]}},
        "intensity": {"zzadded": 4},
    }
    p = plan(config, data)
    d = p.write(data)
    assert d.concepts["ZZ_META"].triggers == {"np": ("zzadded@4",)}
    assert d.concepts["ZZ_META"].description == "Hand reviewed."
    after = path.read_text()
    plan(config, data).write(data)
    assert path.read_text() == after


def test_summary_shows_explicit_existing_concept_changes(prepared):
    config, data = prepared
    config.concept_fixes = {"TIRED": {"person": False, "not_in": ["official"]}}
    summary = "\n".join(plan(config, data).summary())
    assert "1 explicit concept fixes" in summary and "TIRED: not_in, person" in summary


@pytest.mark.parametrize("shape", ["[]", "false", "0", "word"])
def test_concept_fix_file_must_be_a_mapping(prepared, shape):
    config, data = prepared
    (config.directory / "concept_fixes.yaml").write_text(shape)
    config = rounds.RoundConfig.load(config.directory)
    with pytest.raises(SchemaError, match="expected a mapping"):
        plan(config, data)


def test_explicit_trigger_addition_preserves_distinct_exclusions(prepared):
    config, data = prepared
    config.verdicts[0][1]["new_concept"]["triggers"] = {"np": ["zzsource !first"]}
    plan(config, data).write(data)
    config.trigger_fixes = {"add": {"ZZ_META": {"np": ["zzsource !second"]}}}
    dictionary = plan(config, data).write(data)
    assert dictionary.concepts["ZZ_META"].triggers["np"] == ("zzsource !second", "zzsource !first")
    before = (data / "concepts.yaml").read_text()
    plan(config, data).write(data)
    assert (data / "concepts.yaml").read_text() == before


def test_contextual_images_follow_set_aside_concepts_only_in_scratch(prepared):
    config, data = prepared
    plan(config, data).write(data)
    path = data/'imagery.yaml'
    original = path.read_bytes()
    rows = yaml.safe_load(original)
    rows += [dict(id='own-context', text='like a mower', concepts=['ZZ_META'], usage='Test.'),
             dict(id='surviving-context', text='like a shovel', concepts=['BUSY'], related=['ZZ_META'], usage='Test.')]
    path.write_text(yaml.safe_dump(rows))
    before = path.read_bytes()
    scratch = rounds.base_dictionary(config, data)
    assert 'own-context' not in {i.id for i in scratch.imagery}
    assert next(i for i in scratch.imagery if i.id == 'surviving-context').related == ()
    assert path.read_bytes() == before
    rows.append(dict(id='genuine-orphan', text='like a boot', concepts=['MISSING_CONCEPT'], usage='Test.'))
    path.write_text(yaml.safe_dump(rows))
    with pytest.raises(SchemaError, match='known'):
        rounds.base_dictionary(config, data)
