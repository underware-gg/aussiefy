"""aussiefy dev round: a research round's verdicts planned against the dictionary, then written only once valid."""

import pytest
import yaml

from aussiefy import rounds
from aussiefy.schema import SchemaError

VERDICTS = [
    {"candidate": "zzbonzer", "decision": "add_entry", "confidence": "high",
     "entry": {"id": "zzbonzer", "form": "zzbonzer", "concept": ["NEW:ZZ_GREAT"], "frame": "predicate_adj",
               "gloss": "Excellent (a test word).", "replaces": ["knackered", "very good"]},
     "new_concept": {"id": "ZZ_GREAT", "description": "Excellent.",
                     "triggers": {"predicate_adj": ["zzsuperb", "knackered"]}}},
    {"candidate": "zzmaybe", "decision": "add_entry", "confidence": "low",
     "entry": {"id": "zzmaybe", "form": "zzmaybe", "concept": ["TIRED"], "frame": "predicate_adj", "gloss": "Tired?"}},
    {"candidate": "knackered", "decision": "add_entry", "confidence": "high",
     "entry": {"id": "knackered-again", "form": "knackered", "concept": ["TIRED"], "frame": "predicate_adj"}},
    {"candidate": "zzworn", "decision": "trigger", "triggers_to_add": {"TIRED": {"predicate_adj": ["zzworn"]}}},
    {"candidate": "a habit", "decision": "style_guide", "guidance": "Say it plain."},
]


@pytest.fixture
def setup(tmp_path, data_copy):
    data = data_copy
    rd = tmp_path / "research" / "zz-round"
    (rd / "verify").mkdir(parents=True)
    (rd / "round.yaml").write_text(yaml.safe_dump({"name": "zz round", "output": "zz.yaml", "id_suffix": "-zz",
                                                   "header": "# zz round\n\n"}))
    (rd / "verify" / "verdicts-a.yaml").write_text(yaml.safe_dump(VERDICTS))
    return rounds.RoundConfig.load(rd), data


def _plan(config, data):
    return rounds.plan_round(config, rounds.base_dictionary(config, data))


def test_plan_applies_the_guards(setup):
    config, data = setup
    plan = _plan(config, data)
    assert [e["id"] for e in plan.entries] == ["zzbonzer", "zzmaybe"]
    assert plan.entries[1]["status"] == "gate"                        # a low-confidence accept ships gated
    assert plan.new_concepts["ZZ_GREAT"]["triggers"] == {"predicate_adj": ["zzsuperb"]}
    assert plan.added_triggers == {"TIRED": {"predicate_adj": ["zzworn"]}}
    reasons = {(kind, why) for kind, _, why, _ in plan.dropped}
    assert ("entry", "form already in the dictionary") in reasons
    assert ("trigger", "is an Aussie form") in reasons
    assert ("replaces", "is an Aussie form") in reasons and plan.entries[0]["replaces"] == ["very good"]
    assert plan.style_guide == [("a habit", "Say it plain.")]
    assert list(plan.entries[0])[:3] == ["id", "form", "concept"]    # written in the schema's key order


def test_invalid_candidate_cannot_reserve_a_form_or_leave_a_concept(setup):
    config, data = setup
    config.verdicts = [
        ("invalid", {"decision": "add_entry",
                     "entry": {"id": "zzinvalid", "form": "zzcandidate", "concept": ["ZZNEW"],
                               "frame": "np", "variants": [123]},
                     "new_concept": {"id": "ZZNEW", "description": "z",
                                     "triggers": {"np": ["the special place"]}}}),
        ("valid", {"decision": "add_entry",
                   "entry": {"id": "zzvalid", "form": "zzcandidate", "concept": ["TIRED"], "frame": "np"}}),
    ]
    plan = _plan(config, data)
    assert [e["id"] for e in plan.entries] == ["zzvalid"]
    assert not plan.new_concepts
    assert any(kind == "entry" and name == "zzinvalid" and "variants" in why
               for kind, name, why, _ in plan.dropped)
    assert "zzvalid" in plan.write(data).entries


def test_write_then_reapply_is_a_no_op(setup):
    config, data = setup
    d = _plan(config, data).write(data)
    assert "zzbonzer" in d.entries and "ZZ_GREAT" in d.concepts
    assert "zzworn" in d.concepts["TIRED"].triggers["predicate_adj"]
    written = {p: (data / p).read_text() for p in ("entries/zz.yaml", "concepts.yaml")}
    assert written["entries/zz.yaml"].startswith("# zz round\n\n- id: zzbonzer")
    _plan(config, data).write(data)
    assert {p: (data / p).read_text() for p in written} == written


def test_an_invalid_result_leaves_the_dictionary_untouched(setup):
    config, data = setup
    plan = _plan(config, data)
    plan.entries.append({"id": "zzbad", "form": "zzbad", "concept": ["NOPE"], "frame": "np"})
    before = (data / "concepts.yaml").read_text()
    with pytest.raises(SchemaError):
        plan.write(data)
    assert not (data / "entries" / "zz.yaml").exists()
    assert (data / "concepts.yaml").read_text() == before


def test_an_unparsed_verdict_file_blocks_the_write(setup):
    config, data = setup
    (config.directory / "verify" / "verdicts-b.yaml").write_text("- {broken: [")
    config = rounds.RoundConfig.load(config.directory)   # a round's inputs are read when it's loaded
    plan = _plan(config, data)
    assert plan.unparsed == ["verdicts-b.yaml"] and "doesn't parse" in "\n".join(plan.summary())
    with pytest.raises(SchemaError):
        plan.write(data)


def test_a_configured_reference_must_exist(setup, capsys):
    """A user error (exit 2) naming the missing file, not a traceback."""
    from aussiefy.cli import main
    from aussiefy.errors import UserError

    config, _ = setup
    (config.directory / "round.yaml").write_text(yaml.safe_dump({"name": "zz", "output": "zz.yaml",
                                                                 "reference": "missing.yaml"}))
    with pytest.raises(UserError, match="missing.yaml"):
        rounds.RoundConfig.load(config.directory)
    assert main(["dev", "round", str(config.directory)]) == 2
    assert str(config.directory / "missing.yaml") in capsys.readouterr().err


def test_replanning_sets_aside_later_entries_that_use_the_rounds_concepts(setup):
    """A hand entry in another file may use a round's new concept; re-planning the round must still load."""
    config, data = setup
    _plan(config, data).write(data)
    (data / "entries" / "later.yaml").write_text(
        "- {id: zzlater, form: zzlater, concept: [ZZ_GREAT], frame: predicate_adj, gloss: Later.}\n")
    plan = _plan(config, data)
    assert [e["id"] for e in plan.entries] == ["zzbonzer", "zzmaybe"]
    assert "zzlater" in plan.write(data).entries


def test_replanning_sets_aside_only_riffs_for_removed_entries_and_preserves_the_real_data(setup):
    config, data = setup
    _plan(config, data).write(data)
    (data / "entries" / "later.yaml").write_text(
        "- {id: zzlater, form: zzlater, concept: [ZZ_GREAT], frame: predicate_adj, gloss: Later.}\n")
    path = data / "riffs.yaml"
    original = path.read_text()
    path.write_text(original + '\nzzbonzer: [{text: "a round image", tone: comic}]\n'
                    'zzlater: [{text: "a later image", tone: plain}]\n')
    before = path.read_bytes()
    base = rounds.base_dictionary(config, data)
    assert "zzbonzer" not in base.entries and "zzlater" not in base.entries
    assert base.entries["wheelie-bin"].riffs
    updated = rounds.plan_round(config, base).write(data)
    assert updated.entries["zzbonzer"].riffs[0].text == "a round image"
    assert updated.entries["zzlater"].riffs[0].text == "a later image"
    assert path.read_bytes() == before
    path.write_text(path.read_text() + 'zzunknown: [{text: "a genuine orphan", tone: comic}]\n')
    with pytest.raises(SchemaError, match="unknown entry 'zzunknown'"):
        rounds.base_dictionary(config, data)


def test_harvest_keeps_numbers_out_of_the_way():
    from aussiefy.loader import load_dictionary
    from aussiefy.scrape.harvest import harvest

    staged = harvest("The show is on Sunday, Oct. 11, at 10 a.m. and fans can capture photos.",
                     "The show's on Sunday the 11th of October, 10 in the mornin', and fans can snap some happy snaps.",
                     load_dictionary())
    forms = [s.form for s in staged]
    assert not any(f in ("the th", "th") for f in forms) and any("happy snaps" in f for f in forms), forms


@pytest.mark.parametrize("lines, want", [
    (['    vp: ["a", "b"]   # not "c" [x]'], ['    vp: ["a", "b", "z"]   # not "c" [x]']),
    (['    vp: ["a", "b",   # see [x]', '         "c"]'], ['    vp: ["a", "b",   # see [x]', '         "c", "z"]']),
    (['    vp: []'], ['    vp: ["z"]']),
    (['    vp: ["it\'s # not a comment"]'], ['    vp: ["it\'s # not a comment", "z"]']),
])
def test_new_triggers_go_at_the_end_of_the_flow_list(lines, want):
    from aussiefy.rounds import _append_to_flow_list
    _append_to_flow_list(lines, 0, len(lines), '"z"')
    assert lines == want
