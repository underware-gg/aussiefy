"""Advanced settings inherit defaults and independently control observable engine behaviour."""

from dataclasses import asdict, replace
import json
import re

import pytest

from aussiefy import Translator, harness, translate
from aussiefy.errors import UserError
from aussiefy.model import PhoneticRule
from aussiefy.policy import Policy
from aussiefy.profile import ProfileOverrides
from aussiefy.schema import Entry
from aussiefy.yarn import brief, dispatch_tool


def config(**profile):
    return {"garnish": ["opener"], "profile": profile}


def selected(result, placement="opener"):
    return [g for g in result.garnish if g.entry_id and g.placement == placement]


PROSE = " ".join(["The river is flowing through the valley."] * 7)


@pytest.mark.parametrize("kind", ["general", "custom", "technical", "auto"])
def test_omitted_profile_settings_inherit_the_same_dial_defaults(kind, translator):
    base = translator.effective(level=4, vulgarity=1)
    eff = translator.effective(level=4, vulgarity=1, document_type=kind,
                               document_config={"profile": {"garnish": {"opener": 1}}})
    assert eff.profile.garnish["opener"] == 1
    assert eff.profile.garnish["tag"] == base.profile.garnish["tag"]
    assert eff.profile.rewrite == base.profile.rewrite and eff.swearing == base.swearing
    assert eff.profile.frames == base.profile.frames


def test_general_and_custom_inherit_different_document_defaults(translator):
    options = {"level": 5, "vulgarity": 0, "document_config": {"profile": {"garnish": {"opener": 1}}}}
    general = translator.translate(PROSE, **options)
    custom = translator.translate(PROSE, document_type="custom", **options)
    assert selected(general) and not selected(custom)
    assert general.profile_config == custom.profile_config
    enabled = translator.translate(PROSE, document_type="custom", **{
        **options, "document_config": config(garnish={"opener": 1})})
    assert selected(enabled)


@pytest.mark.parametrize("probability,limit,expected", [(0, 3, 0), (1, 0, 0), (1, 1, 1), (1, 2, 2)])
def test_opener_probability_and_text_limit(probability, limit, expected, translator):
    r = translator.translate(PROSE, vulgarity=0, document_type="custom",
                             document_config=config(garnish={"opener": probability}, max_garnish={"opener": limit}))
    assert len(selected(r)) == expected


@pytest.mark.parametrize("gap", [0, 1, 2])
def test_garnish_gap_controls_source_sentence_spacing(gap, translator):
    r = translator.translate(PROSE, vulgarity=0, document_type="custom",
                             document_config=config(garnish={"opener": 1}, max_garnish={"opener": 3}, garnish_gap=gap))
    positions = [g.sentence for g in selected(r)]
    assert positions == [0, gap + 1, 2 * (gap + 1)]


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_sentence_budget_controls_distinct_placements(budget, translator):
    r = translator.translate("You are walking to the river.", vulgarity=0, document_type="custom",
                             document_config={"garnish": ["opener", "tag"], "profile": {
                                 "garnish": {"opener": 1, "tag": 1}, "garnish_per_sentence": budget}})
    assert len([g for g in r.garnish if g.entry_id]) == budget


def test_zero_closer_limit_disables_both_channels(translator):
    for cap in (0, 2):
        r = translator.translate("That is my opinion.", vulgarity=cap, document_type="custom",
                                 document_config={"garnish": ["closer"], "profile": {
                                     "garnish": {"closer": 1}, "swearing": {"closer": 1},
                                     "max_garnish": {"closer": 0}}})
        assert not selected(r, "closer")


@pytest.mark.parametrize("profile", [{"substitution": {"lexical": 0, "phrase": 0, "idiom": 0}}, {"frames": []}])
def test_substitution_and_frame_controls_disable_swaps(profile, translator):
    source = "She was very tired. My friend had breakfast."
    base = translator.translate(source, document_type="custom")
    assert any(r.substituted for r in base.records)
    r = translator.translate(source, document_type="custom", document_config={"profile": profile})
    assert not any(r.substituted for r in r.records)


def test_drawl_multiplier_controls_phonetics_without_disabling_spelling(translator):
    rules = [PhoneticRule("drawl", re.compile(r"walking"), "walkin'", 1, 1),
             PhoneticRule("spelling", re.compile(r"color"), "colour", 1, 1, kind="spelling")]
    tr = Translator(replace(translator.dictionary, phonetic=rules))
    source = "I am walking past the color chart."
    quiet = tr.translate(source, document_type="custom", document_config={"profile": {"phonetic": 0}})
    loud = tr.translate(source, document_type="custom", document_config={"profile": {"phonetic": 2}})
    assert "walking" in quiet.text and "walkin'" in loud.text
    assert "colour" in quiet.text and "colour" in loud.text


def test_swear_rates_and_stretch_respect_the_vulgarity_cap(translator):
    entry = Entry("test-swear", "far out", (), "interjection", type="garnish", placement="opener",
                  vulgarity=1, stretch=True, when=("any",))
    tr = Translator(replace(translator.dictionary, entries={
        **{e.id: e for e in translator.dictionary.entries.values() if e.type != "garnish"},
        "test-swear": entry}))
    for rate, cap, expected in [(0, 1, False), (1, 0, False), (1, 1, True)]:
        r = tr.translate("The river is flowing through the valley.", vulgarity=cap, document_type="custom",
                         document_config=config(garnish={"opener": 0}, swearing={"exclaim": rate}, stretch=[4, 4]))
        assert bool(selected(r)) == expected
        if expected:
            assert r.text.startswith("Faaaar out,")


def test_infix_multiplier_is_independent_of_clean_drawl_and_respects_cap(translator):
    rule = PhoneticRule("test-infix", re.compile(r"great"), "bloody great", 1, 1, vulgarity=1)
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    for multiplier, cap, expected in [(0, 1, False), (2, 0, False), (2, 1, True)]:
        r = tr.translate("That is great.", vulgarity=cap, document_type="custom", document_config={
            "garnish": ["infix"], "profile": {"frames": [], "phonetic": 0, "swearing": {"infix": multiplier}}})
        assert ("bloody" in r.text) == expected


def test_swear_lean_changes_candidate_weight_without_bypassing_cap(translator):
    def weights(lean, cap):
        r = translator.translate("You are very tired.", vulgarity=cap, document_type="custom",
                                 document_config={"profile": {"swearing": {"lean": lean}}})
        return {c.entry.id: (c.entry.vulgarity, c.weight) for x in r.records for c in x.eligible}
    normal, strong = weights(1, 2), weights(2, 2)
    vulgar = [k for k, (cap, _) in normal.items() if cap]
    clean = [k for k, (cap, _) in normal.items() if not cap]
    assert vulgar and clean
    assert all(strong[k][1] == normal[k][1] * 2 for k in vulgar)
    assert all(strong[k][1] == normal[k][1] for k in clean)
    assert all(cap == 0 for cap, _ in weights(2, 0).values())


@pytest.mark.parametrize("probability", [0, 1])
def test_stack_probability_changes_second_idiom_selection(probability, translator):
    r = translator.translate("She is crazy.", vulgarity=0, document_type="custom",
                             document_config={"profile": {"stack": probability}})
    assert any(x.substituted for x in r.records)
    assert any(x.stacked for x in r.records) == bool(probability)


@pytest.mark.parametrize("probability,limit,expected", [(0, 1, False), (1, 0, False), (1, 1, True)])
def test_riff_probability_and_limit_control_optional_colour(probability, limit, expected, translator):
    r = translator.translate("We put out the ashcans.", vulgarity=0, document_type="custom", document_config={
        "garnish": ["riff"], "profile": {"garnish": {"riff": probability}, "max_garnish": {"riff": limit}}})
    assert any(x.riff for x in r.records) == expected


def test_zero_swear_weight_leaves_source_when_only_vulgar_candidates_exist(translator):
    only = {k: e for k, e in translator.dictionary.entries.items() if e.vulgarity > 0}
    tr = Translator(replace(translator.dictionary, entries=only))
    r = tr.translate("He is very tired.", document_type="custom", document_config={"profile": {"swearing": {"lean": 0}}})
    assert not any(x.substituted for x in r.records)


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_sentence_budget_combines_clean_and_sweary_channels(budget, translator):
    r = translator.translate("You are walking to the river.", vulgarity=1, document_type="custom", document_config={
        "garnish": ["opener", "tag"], "profile": {"garnish": {"opener": 1, "tag": 1},
        "swearing": {"exclaim": 1}, "garnish_per_sentence": budget}})
    assert len([g for g in r.garnish if g.entry_id]) == budget


def test_text_limit_combines_clean_and_sweary_channels(translator):
    r = translator.translate(PROSE, vulgarity=1, document_type="custom", document_config=config(
        garnish={"opener": 1}, swearing={"exclaim": 1}, max_garnish={"opener": 1}, garnish_gap=0))
    assert len(selected(r)) == 1


def test_rewrite_thresholds_control_actual_rewriter_dispatch(translator):
    class Rewriter:
        model = "test"
        def rewrite(self, original, draft, planned, **kwargs):
            return draft, "checked"
    source = "The proposition was conceived with considerable deliberation and dedicated to posterity."
    enabled = translator.translate(source, rewriter=Rewriter(), document_type="custom",
                                   document_config={"profile": {"rewrite": {"min_words": 1}}})
    disabled = translator.translate(source, rewriter=Rewriter(), document_type="custom",
                                    document_config={"profile": {"rewrite": {"min_words": 100}}})
    assert enabled.rewrites and not disabled.rewrites


def test_profile_objects_are_snapshots_and_never_mutate_dictionary(translator):
    before = asdict(translator.dictionary.profiles[5])
    raw = {"profile": {"garnish": {"opener": 1}, "frames": ["np"], "rewrite": {"min_words": 1}}}
    policy = Policy(document_config=raw)
    raw["profile"]["garnish"]["opener"] = 0
    raw["profile"]["frames"].clear()
    raw["profile"]["rewrite"]["min_words"] = 99
    assert policy.document_config.values()["profile"] == {"garnish": {"opener": 1}, "frames": ["np"], "rewrite": {"min_words": 1}}
    translator.translate(PROSE, document_config=policy.document_config)
    assert asdict(translator.dictionary.profiles[5]) == before
    with pytest.raises(TypeError):
        policy.document_config.profile._data["garnish"]["opener"] = 0


def test_effective_snapshot_is_complete_and_reusable(translator):
    first = translator.translate(PROSE, level=4, vulgarity=2, document_config=config(
        garnish={"opener": 1}, swearing={"infix": 2}, rewrite={"min_words": 8}, frames=["np"]))
    snapshot = first.to_dict()["profile_config"]
    assert snapshot["garnish"]["aside"] == 0
    assert snapshot["max_garnish"]["connective"] == 99
    again = translator.translate(PROSE, level=4, vulgarity=2,
                                 document_config={"garnish": ["opener"], "profile": snapshot})
    assert again.text == first.text and again.profile_config == snapshot
    snapshot["garnish"]["opener"] = 0
    assert translator.translate(PROSE, level=4, vulgarity=2).profile_config["garnish"]["opener"] == .2


@pytest.mark.parametrize("profile", [None, [], {"unknown": 1}, {"level": 5}, {"garnish": None},
    {"garnish": {"madeup": 0}}, {"garnish": {"opener": 1.1}}, {"substitution": {"lexical": True}},
    {"max_garnish": {"opener": 1.5}}, {"garnish_gap": -1}, {"garnish_per_sentence": False},
    {"phonetic": float("inf")}, {"stack": -1}, {"frames": "np"}, {"frames": ["unknown"]},
    {"stretch": [2]}, {"stretch": [3, 2]}, {"stretch": [0, 3]}, {"rewrite": {"unknown": 1}},
    {"rewrite": {"min_level": 6}}, {"rewrite": {"min_words": None}}, {"rewrite": {"max_coverage": 2}},
    {"swearing": {"exclaim": 2}}, {"swearing": {"infix": -1}}, {"swearing": {"lean": float("nan")}}])
def test_malformed_profiles_are_boundary_errors(profile):
    with pytest.raises(UserError, match="document_config.profile"):
        Policy(document_config={"profile": profile})


def test_explicitly_constructed_profile_is_revalidated():
    with pytest.raises(UserError, match="document_config.profile"):
        from aussiefy.policy import DocumentOverrides
        Policy(document_config=DocumentOverrides(profile=ProfileOverrides({"stack": 2})))


def test_all_document_operations_report_the_same_profile(translator):
    conf = config(garnish={"opener": 1}, max_garnish={"opener": 1}, phonetic=0, swearing={"infix": 2})
    opts = {"document_type": "custom", "document_config": conf, "level": 4, "vulgarity": 1, "translator": translator}
    source = "You are very tired."
    translated = harness.translate(source, **opts)
    results = [translated, harness.plan(source, **opts), harness.guide(**opts),
               harness.lint(translated["text"], original=source, **opts),
               harness.verify(translated["text"], original=source, **opts),
               harness.translate(source, markdown=True, **opts), harness.translate(source, markup="markdown", **opts)]
    assert all(r["profile_config"] == translated["profile_config"] for r in results)
    session = brief(source, **opts)
    assert session.payload["PROFILE_CONFIG"] == translated["profile_config"]
    conf["profile"]["phonetic"] = 2
    checked, _ = dispatch_tool(session, "lint", {"text": source})
    assert checked["profile_config"] == translated["profile_config"]


def test_lint_suggestions_respect_disabled_substitutions(translator):
    source = "She was very tired."
    assert harness.lint(source, translator=translator)["suggestions"]
    assert harness.lint(source, translator=translator, document_config={"profile": {"frames": []}})["suggestions"] == []


@pytest.mark.parametrize("mode", [{"markdown": True}, {"markup": "markdown"}])
def test_flavour_preserves_technical_terms_grammar_and_markup(mode, translator):
    source = "# Setup\n\nThe browser uses cookies. You are very tired.\n\nRun `pip install aussiefy`.\n"
    r = translate(source, translator=translator, vulgarity=0, document_type="custom", document_config={
        "term_domains": ["technical"], "garnish": ["opener"], "profile": {
            "garnish": {"opener": 1}, "max_garnish": {"opener": 1}, "phonetic": 0}}, **mode)
    assert "browser uses cookies" in r.text and "`pip install aussiefy`" in r.text
    assert r.text.startswith("# Setup\n") and "You are very tired" not in r.text
    records = [g for unit in r.units for g in unit.result.garnish] if mode.get("markdown") else r.garnish
    assert len([g for g in records if g.entry_id and g.placement == "opener"]) == 1
    assert "Run `pip install aussiefy`." in r.text


def test_advanced_limits_and_spacing_apply_across_markdown_units(translator):
    source = "\n\n".join(["The river is flowing through the valley."] * 7)
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=config(garnish={"opener": 1}, max_garnish={"opener": 2}, garnish_gap=2))
    positions = [i for i, unit in enumerate(r.units) if selected(unit.result)]
    assert positions == [0, 3]


def test_cli_accepts_nested_profile_overrides(capsys):
    from aussiefy.cli import main
    assert main(["translate", "--json", "--document-type", "custom", "--document-config",
                 json.dumps({"profile": {"frames": []}}), "She was very tired."]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["profile_config"]["frames"] == []
    assert not result.get("decisions", {}).get("substitutions")
