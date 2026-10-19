"""Quantity approximation is a reviewed mapping permission, not a property of slang wording."""

from dataclasses import replace
import json
import pytest
import yaml
import jsonschema

from aussiefy import Translator, harness, load_dictionary, translate_changes
from aussiefy.changes import SCHEMA
from aussiefy.genre import resolve_document
from aussiefy.policy import DocumentOverrides
from aussiefy.schema import SchemaError, parse_concept
from aussiefy.errors import UserError
from aussiefy.select import mapping_effects

SOURCE = "It happened four score and seven years ago."
PROFILE = {
    "phonetic": 0,
    "substitution": {"lexical": 1, "phrase": 1, "idiom": 1},
    "garnish": {"riff": 0},
    "swearing": {"infix": 0, "exclaim": 0, "closer": 0},
}


def options(enabled):
    return dict(
        level=5,
        vulgarity=0,
        embellishment=0,
        embedder="none",
        document_config={"profile": PROFILE, "quantity_approximation": enabled},
    )


@pytest.mark.parametrize(
    "kind", ["general", "custom", "story", "personal", "news", "instructions", "technical", "official"]
)
@pytest.mark.parametrize("step", [0, 1, 2])
def test_defaults_are_resolved_then_exact_override_wins(dictionary, kind, step):
    genre = resolve_document("", config=dictionary.genres, document_type=kind)
    assert genre.setting(step).quantity_approximation is (step > 0 and kind in {"general", "story", "personal"})
    for explicit in (True, False):
        genre = resolve_document(
            "", config=dictionary.genres, document_type=kind, document_config={"quantity_approximation": explicit}
        )
        assert genre.setting(step).quantity_approximation is explicit


@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_permission_requires_real_boolean(bad):
    with pytest.raises(UserError, match="quantity_approximation"):
        DocumentOverrides.parse({"quantity_approximation": bad})


def test_indefinite_and_exact_sources_have_different_effects(translator):
    for enabled in (False, True):
        ordinary = translator.translate("It happened ages ago.", **options(enabled))
        assert any(r.eligible for r in ordinary.records if "LONG_AGO" in r.det.concepts)
        result = translator.translate(SOURCE, **options(enabled))
        record = next(r for r in result.records if "LONG_AGO" in r.det.concepts)
        assert bool(record.eligible) is enabled
        assert record.det.mapping_effects == {"LONG_AGO": ("quantity_approximation",)}
        if enabled:
            assert record.chosen.semantic_effects == ("quantity_approximation",)
        else:
            assert result.text == SOURCE
            assert any("quantity_approximation is false" in why for _, why in record.rejected)


def test_plan_changes_lookup_share_permission_and_report_applied_mapping(translator):
    for enabled in (False, True):
        args = options(enabled)
        plan = harness.plan(SOURCE, translator=translator, **{k: v for k, v in args.items() if k != "embedder"})
        assert bool(plan["planned"]) is enabled
        if enabled:
            assert plan["planned"][0]["semantic_effects"] == ["quantity_approximation"]
        changes = translate_changes(SOURCE, translator=translator, **args)
        jsonschema.validate(changes.to_dict(), json.loads(SCHEMA.read_text()))
        swaps = [c for c in changes.changes if c["kind"] == "substitution"]
        assert bool(swaps) is enabled
        if enabled:
            assert all(o["semantic_effects"] == ["quantity_approximation"] for c in swaps for o in c["alternatives"])
        found = harness.lookup(
            "four score and seven years ago",
            translator=translator,
            level=5,
            vulgarity=0,
            embellishment=0,
            document_config={"quantity_approximation": enabled},
        )
        assert bool({"yonks-ago", "donkeys-years-ago"} & {c["id"] for c in found["results"]}) is enabled
    found = harness.lookup("yonks ago", translator=translator, embellishment=0)
    assert "yonks-ago" in {c["id"] for c in found["results"]}


def test_target_only_ordinary_slang_is_not_intrinsically_lossy(translator):
    assert not [
        i
        for i in harness.lint("It happened yonks ago.", translator=translator, suggest=False)["issues"]
        if i["kind"] == "semantic_effect"
    ]


def test_original_allows_checking_a_reviewed_approximation(translator):
    for enabled in (False, True):
        result = harness.lint(
            "It happened yonks ago.",
            original=SOURCE,
            translator=translator,
            embellishment=0,
            document_config={"quantity_approximation": enabled},
            suggest=False,
        )
        assert bool([i for i in result["issues"] if i["kind"] == "semantic_effect"]) is (not enabled)


def test_exact_replaces_cannot_bypass_source_certificate(tmp_path):
    path = tmp_path / "direct.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "format": "aussiefy-dictionary-overlay/v1",
                "patch_entries": {"yonks-ago": {"replaces": ["four score and seven years ago"]}},
            }
        )
    )
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    assert tr.translate(SOURCE, **options(False)).text == SOURCE


def test_an_independent_precise_reading_does_not_inherit_another_concepts_loss(translator):
    result = translator.translate(SOURCE, **options(False))
    det = next(r.det for r in result.records if "LONG_AGO" in r.det.concepts)
    precise = replace(translator.dictionary.entries["yonks-ago"], concept=("PRECISE_DURATION",))
    det = replace(det, concepts=det.concepts + ("PRECISE_DURATION",))
    assert mapping_effects(precise, det, narrator_opinion=False, quantity_approximation=False) == ()


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {"vp": {}},
        {"adv": {"missing": ["quantity_approximation"]}},
        {"adv": {"ages ago": ["unknown"]}},
        {"adv": {"ages ago": []}},
    ],
)
def test_annotation_requires_existing_frame_pattern_and_known_effects(bad):
    with pytest.raises(SchemaError):
        parse_concept("AGO", {"triggers": {"adv": ["ages ago"]}, "trigger_effects": bad})


def test_an_allowed_mapping_does_not_excuse_another_dropped_number(tmp_path):
    path = tmp_path / "numeric.yaml"
    pattern = "87 years ago"
    path.write_text(
        yaml.safe_dump(
            {
                "format": "aussiefy-dictionary-overlay/v1",
                "patch_concepts": {
                    "LONG_AGO": {
                        "triggers": {"adv": [pattern]},
                        "trigger_effects": {"adv": {pattern: ["quantity_approximation"]}},
                    }
                },
            }
        )
    )
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    report = harness.lint(
        "It happened yonks ago. People came.",
        original="It happened 87 years ago. 12 people came.",
        translator=tr,
        suggest=False,
        document_config={"quantity_approximation": True},
    )
    assert [w["phrase"] for w in report["warnings"] if w["kind"] == "number_dropped"] == ["12"]


@pytest.mark.parametrize(
    "query", ["It happened four score and seven years ago.", "four score and seven years ago, before the war"]
)
def test_context_cannot_bypass_lookup_mapping_permission(translator, query):
    for enabled in (False, True):
        result = harness.lookup(
            query,
            translator=translator,
            embellishment=0,
            limit=100,
            document_config={"quantity_approximation": enabled},
        )
        terms = [c for c in result["results"] if c["id"] in {"yonks-ago", "donkeys-years-ago"}]
        assert bool(terms) is enabled
        assert all(c["semantic_effects"] == ["quantity_approximation"] for c in terms)


def test_round_unrelated_fix_preserves_source_effects(tmp_path, data_copy):
    from aussiefy.rounds import RoundConfig, base_dictionary, plan_round

    directory = tmp_path / "round"
    directory.mkdir()
    (directory / "round.yaml").write_text("name: quantity\noutput: quantity.yaml\n")
    config = RoundConfig.load(directory)
    config.concept_fixes = {"LONG_AGO": {"description": "An event in the distant past."}}
    result = plan_round(config, base_dictionary(config, data_copy)).write(data_copy)
    assert result.concepts["LONG_AGO"].trigger_effects == {
        "adv": {"four score and seven years ago@5": ("quantity_approximation",)}
    }


def test_new_round_style_rewrite_preserves_source_effects(tmp_path, data_copy):
    from aussiefy.rounds import RoundConfig, base_dictionary, plan_round

    directory = tmp_path / "round"
    (directory / "verify").mkdir(parents=True)
    (directory / "round.yaml").write_text("name: quantity\noutput: quantity.yaml\n")
    verdict = {
        "decision": "add_entry",
        "entry": {"id": "zzquantity", "form": "zzages", "concept": ["ZZ_QUANTITY"], "frame": "adv"},
        "new_concept": {
            "id": "ZZ_QUANTITY",
            "description": "A synthetic reviewed duration.",
            "triggers": {"adv": ["zzduration@5"]},
            "trigger_effects": {"adv": {"zzduration@5": "quantity_approximation"}},
        },
    }
    (directory / "verify" / "verdicts-a.yaml").write_text(yaml.safe_dump([verdict]))
    config = RoundConfig.load(directory)
    config.trigger_fixes = {"intensity": {"zzduration": 4}}
    result = plan_round(config, base_dictionary(config, data_copy)).write(data_copy)
    assert result.concepts["ZZ_QUANTITY"].trigger_effects == {"adv": {"zzduration@4": ("quantity_approximation",)}}


@pytest.mark.parametrize("source_frame,expected", [("predicate_adj", False), ("interjection", True)])
def test_direct_frame_cannot_strip_a_valid_source_effect(tmp_path, source_frame, expected):
    path = tmp_path / "frames.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "format": "aussiefy-dictionary-overlay/v1",
                "add_concepts": {
                    "ZZ_APPROX": {
                        "triggers": {source_frame: ["quantified"]},
                        "trigger_effects": {source_frame: {"quantified": ["quantity_approximation"]}},
                    }
                },
                "add_entries": [
                    {
                        "id": "zz-ancient",
                        "form": "ancient",
                        "concept": ["ZZ_APPROX"],
                        "frame": "adj",
                        "replaces": ["quantified"],
                    }
                ],
            }
        )
    )
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = tr.translate("She is quantified.", **options(False))
    assert any(c.entry.id == "zz-ancient" for r in result.records for c in r.eligible) is expected
    assert ("ancient" in result.text) is expected


def test_ordinary_writer_checks_do_not_pay_for_a_full_conditional_source_parse(translator, monkeypatch):
    def unexpected_parse(*args, **kwargs):
        raise AssertionError("ordinary text requires no conditional source parse")

    monkeypatch.setattr("aussiefy.detect.detect", unexpected_parse)
    report = harness.lint(
        "People arrived.",
        original="12 people arrived.",
        translator=translator,
        english="none",
        suggest=False,
        document_config={"quantity_approximation": True},
    )
    assert [w["phrase"] for w in report["warnings"] if w["kind"] == "number_dropped"] == ["12"]
