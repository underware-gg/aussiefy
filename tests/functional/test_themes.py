"""Subject permissions filter new language consistently, independently of profanity."""

from dataclasses import replace

import pytest
import yaml

from aussiefy import Translator, harness, load_dictionary, translate, translate_changes
from aussiefy.cards import entry_card
from aussiefy.errors import UserError
from aussiefy.matcher import PatternIndex, compile_pattern
from aussiefy.policy import Policy, resolve
from aussiefy.schema import Entry, Imagery, Riff, SchemaError
from aussiefy.yarn import brief


@pytest.mark.parametrize("cap, allowed", [
    (0, {"drinking", "gambling", "religion", "death"}),
    (1, {"drinking", "gambling", "religion", "death", "drinking_games", "bodily_functions", "tobacco"}),
    (2, None), (3, None),
])
def test_tier_defaults_come_from_data(cap, allowed, dictionary):
    assert resolve(Policy(vulgarity=cap), dictionary).permitted_themes == (set(dictionary.theme_defaults[3]) if allowed is None else allowed)


@pytest.mark.parametrize("themes", [{"drugs": 1}, {"drugs": "false"}, {"drugs": None},
                                    {"unknown": True}, {1: True}, [], None])
def test_overrides_require_exact_known_boolean_settings(themes, dictionary):
    with pytest.raises(UserError, match="document_config.themes"):
        resolve(Policy(document_config={"themes": themes}), dictionary)


def test_override_order_and_caller_mutation_cannot_change_policy(dictionary):
    raw = {"drugs": True, "drinking": False}
    policy = Policy(vulgarity=0, document_config={"themes": raw})
    expected = resolve(policy, dictionary)
    raw["drugs"] = False
    assert resolve(policy, dictionary) == expected
    assert "drugs" in expected.permitted_themes and "drinking" not in expected.permitted_themes
    assert policy.document_config == Policy(document_config={"themes": {
        "drinking": False, "drugs": True}}).document_config
    assert policy.document_config.values()["themes"] == {"drinking": False, "drugs": True}


@pytest.mark.parametrize("fault", ["missing-tier", "unknown-theme", "missing-theme", "not-boolean"])
def test_invalid_theme_data_cannot_load(data_copy, fault):
    path = data_copy / "themes.yaml"
    raw = yaml.safe_load(path.read_text())
    if fault == "missing-tier":
        del raw[0]
    elif fault == "unknown-theme":
        raw[0]["unknown"] = True
    elif fault == "missing-theme":
        del raw[0]["drinking"]
    else:
        raw[0]["drugs"] = 1
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match="themes.yaml"):
        load_dictionary(data_dir=data_copy)


@pytest.fixture
def themed(dictionary):
    def term(eid, **settings):
        return Entry(eid, eid, ("TIRED",), "predicate_adj", **settings)
    entries = [term("zzplain"), term("zzdrug", themes=("drugs",)),
               term("zzboth", themes=("drugs", "religion")),
               term("zzlocked", themes=("violence",), vulgarity=2)]
    forms = PatternIndex([compile_pattern(e.form, e.frame, e.concept, e.intensity, entry_id=e.id) for e in entries])
    return Translator(replace(dictionary, entries={e.id: e for e in entries}, imagery=(), form_index=forms), lookup_embedder=None)


def eligible(result):
    return {candidate.entry.id for record in result.records for candidate in record.eligible}


@pytest.mark.parametrize("kind", ["general", "custom", "technical", "auto"])
def test_overrides_are_independent_of_cap_and_document_type(themed, kind):
    quiet = themed.translate("I am tired.", vulgarity=0, document_type=kind)
    assert eligible(quiet) == {"zzplain"}
    enabled = themed.translate("I am tired.", vulgarity=0, document_type=kind,
                              document_config={"themes": {"drugs": True, "religion": False}})
    assert eligible(enabled) == {"zzplain", "zzdrug"}  # every theme must be permitted
    loud = themed.translate("I am tired.", vulgarity=3, document_type=kind,
                           document_config={"themes": {"violence": False}})
    assert "zzlocked" not in eligible(loud)


def test_lookup_and_locked_probes_cannot_unlock_forbidden_subjects(themed):
    opts = {"translator": themed, "vulgarity": 0, "document_type": "custom"}
    found = harness.lookup("tired", include_gated=True, limit=30, **opts)
    assert {e["id"] for e in found["results"]} == {"zzplain"}
    changes = translate_changes("I am tired.", **opts)
    assert not any(c["locked"] for c in changes.changes)
    assert not {"zzdrug", "zzboth", "zzlocked"}.intersection(changes.entries)
    allowed = translate_changes("I am tired.", document_config={"themes": {"violence": True}}, **opts)
    assert any(o["entry_id"] == "zzlocked" for c in allowed.changes for o in c["locked"])


def test_riffs_cards_and_agent_plan_reuse_the_same_permissions(themed):
    entries = {"zzplain": replace(themed.dictionary.entries["zzplain"], riffs=(
        Riff("a plain image"), Riff("a forbidden image", themes=("violence",))))}
    tr = Translator(replace(themed.dictionary, entries=entries), lookup_embedder=None)
    config = {"garnish": ["riff"], "entry_riffs": True, "contextual_riffs": False,
              "profile": {"garnish": {"riff": 1}, "phonetic": 0}}
    opts = {"translator": tr, "vulgarity": 0, "document_type": "custom", "document_config": config}
    result = translate("I am tired.", **opts)
    assert "forbidden image" not in result.text
    plan = harness.plan("I am tired.", **opts)
    assert [r["text"] for group in plan["riffs"] for r in group["riffs"]] == ["a plain image"]
    changes = translate_changes("I am tired.", **opts)
    assert [r["text"] for r in changes.entries["zzplain"]["riffs"]] == ["a plain image"]
    card = entry_card(entries["zzplain"], permitted_themes=result.permitted_themes)
    assert [r["text"] for r in card["riffs"]] == ["a plain image"]
    session = brief("I am tired.", **opts)
    assert session.payload["THEME_PERMISSIONS"] == result.envelope()["theme_permissions"]


def test_imagery_uses_the_same_permission_for_insertion_lookup_and_plans(themed):
    image = Imagery("zzimage", "a forbidden image", ("TIRED",), "Test fixture.", themes=("violence",))
    tr = Translator(replace(themed.dictionary, imagery=(image,)), lookup_embedder=None)
    config = {"garnish": ["riff"], "entry_riffs": False, "contextual_riffs": True, "riff_exaggeration": 1,
              "profile": {"garnish": {"riff": 1}, "phonetic": 0}}
    opts = {"translator": tr, "vulgarity": 0, "document_type": "custom", "document_config": config}
    assert "forbidden image" not in translate("I am tired.", **opts).text
    assert not harness.plan("I am tired.", **opts)["riffs"]
    assert not harness.lookup("tired", **opts).get("imagery")
    config = {**config, "themes": {"violence": True}}
    assert harness.lookup("tired", **{**opts, "document_config": config})["imagery"][0]["id"] == "zzimage"


@pytest.mark.parametrize("mode", [{}, {"markdown": True}, {"markup": "mdx"}])
def test_permissions_survive_document_routing_and_do_not_delete_source_subjects(themed, mode):
    source = "I am tired.\n\nBeer and cannabis are mentioned here."
    result = translate(source, translator=themed, vulgarity=3, document_type="custom",
                       document_config={"themes": {"drugs": False, "violence": False, "drinking": False}}, **mode)
    assert "Beer" in result.text and "cannabis" in result.text
    assert "zzdrug" not in result.text and "zzboth" not in result.text and "zzlocked" not in result.text
    assert result.envelope()["theme_permissions"]["drugs"] is False


def test_garnish_requires_the_same_themes_as_substitutions(themed):
    opener = Entry("zzopener", "zzopener", (), "interjection", type="garnish", placement="opener",
                   when=("any",), themes=("violence",))
    tr = Translator(replace(themed.dictionary, entries={**themed.dictionary.entries, opener.id: opener}))
    config = {"garnish": ["opener"], "profile": {"garnish": {"opener": 1}}}
    blocked = tr.translate("I am tired.", vulgarity=0, document_type="custom", document_config=config)
    assert not any(g.entry_id == "zzopener" for g in blocked.garnish)
    allowed = tr.translate("I am tired.", vulgarity=0, document_type="custom",
                           document_config={**config, "themes": {"violence": True}})
    assert any(g.entry_id == "zzopener" for g in allowed.garnish)


def test_known_forbidden_terms_fail_lint_verify_and_agent_submission(themed):
    from aussiefy.retelling import validate

    opts = {"translator": themed, "vulgarity": 0, "document_type": "custom"}
    source, draft = "I am tired.", "I am zzdrug."
    checked = harness.lint(draft, original=source, suggest=False, **opts)
    assert any(i["kind"] == "theme" and i["themes"] == ["drugs"] for i in checked["issues"])
    assert any(p["kind"] == "theme" and p["severity"] == "major"
               for p in harness.verify(draft, original=source, **opts)["problems"])
    assert any(p.startswith("theme:") for p in validate(brief(source, **opts), draft))
    assert not any(i["kind"] == "theme" for i in harness.lint(
        draft, original=source, suggest=False, document_config={"themes": {"drugs": True}}, **opts)["issues"])
    assert not any(i["kind"] == "theme" for i in harness.lint(
        draft, original=draft, suggest=False, **opts)["issues"])
    repeated = harness.lint(draft + " " + draft, original=draft, suggest=False, **opts)
    assert len([i for i in repeated["issues"] if i["kind"] == "theme"]) == 1


def test_known_fixed_images_and_riffs_keep_source_use_allowances(themed):
    entry = replace(themed.dictionary.entries["zzplain"], riffs=(Riff("a forbidden riff", themes=("sex",)),))
    image = Imagery("zzimage", "a forbidden image", ("TIRED",), "Fixture.", themes=("violence",))
    tr = Translator(replace(themed.dictionary, entries={**themed.dictionary.entries, entry.id: entry}, imagery=(image,)))
    for text in ("A forbidden riff.", "A forbidden image."):
        assert any(i["kind"] == "theme" for i in harness.lint(
            text, original="A plain sentence.", vulgarity=0, translator=tr, suggest=False)["issues"])
        assert not any(i["kind"] == "theme" for i in harness.lint(
            text, original=text, vulgarity=0, translator=tr, suggest=False)["issues"])


def test_custom_rewriter_cannot_bypass_known_theme_permissions(themed):
    class Rewriter:
        model = "fixture"

        def rewrite(self, original, draft, planned, **options):
            assert "drugs" not in options["permitted_themes"]
            return "I am zzdrug.", "rewritten"

    result = themed.translate("I am tired.", vulgarity=0, document_type="custom", rewriter=Rewriter(), rewrite_mode="all")
    assert "zzdrug" not in result.text
    assert result.rewrites[0].output is None and "forbidden themes" in result.rewrites[0].status


def test_model_rewriter_checks_fresh_and_cached_output(themed, tmp_path):
    import json
    from conftest import FakeClaude, json_reply
    from aussiefy.llm import ClaudeRewriter

    bad = ClaudeRewriter(client=FakeClaude(json_reply({"text": "I am zzdrug."})), cache=False, translator=themed)
    assert bad.rewrite("I am tired.", "I am tired.", [], level=5, vulgarity=0)[0] is None
    good = ClaudeRewriter(client=FakeClaude(json_reply({"text": "I am zzplain."})), cache_dir=tmp_path, translator=themed)
    assert good.rewrite("I am tired.", "I am tired.", [], level=5, vulgarity=0)[0] == "I am zzplain."
    [path] = list(tmp_path.glob("*.json"))
    record = json.loads(path.read_text())
    assert record["payload"]["THEME_PERMISSIONS"]["drugs"] is False
    record["text"] = "I am zzdrug."
    path.write_text(json.dumps(record))
    client = FakeClaude(json_reply({"text": "I am zzplain."}))
    again = ClaudeRewriter(client=client, cache_dir=tmp_path, translator=themed)
    assert again.rewrite("I am tired.", "I am tired.", [], level=5, vulgarity=0)[0] == "I am zzplain."
    assert len(client.calls) == 1


def test_surface_model_cannot_add_known_forbidden_terms(themed):
    from conftest import FakeClaude, json_reply
    from aussiefy.llm import surface_rewrite

    result = themed.translate("I am tired.", vulgarity=0, document_type="custom")
    before = result.text
    client = FakeClaude(json_reply({"text": "I am zzplain and zzdrug."}))
    surface_rewrite(result, client=client, translator=themed)
    assert result.text == before and result.surface["outcome"] == "fell_back"
    assert "forbidden themes" in result.surface["status"]


def test_theme_lint_keeps_plain_sense_and_ambiguous_wording_unresolved(themed):
    from aussiefy.semantic_checks import theme_issues

    plain = replace(themed.dictionary.entries["zzdrug"], plain_sense=True)
    d = replace(themed.dictionary, entries={**themed.dictionary.entries, plain.id: plain})
    assert not theme_issues("I am zzdrug.", "I am tired.", d, frozenset())


def test_longer_expressions_own_theme_readings_and_source_allowances(themed):
    from aussiefy.semantic_checks import theme_issues

    entries = [Entry("crack", "crack", ("TIRED",), "np", themes=("drugs",)),
               Entry("have-a-crack", "have a crack", ("TIRED",), "np"),
               Entry("smoke-crack", "smoke crack", ("TIRED",), "np", themes=("drugs",))]
    forms = PatternIndex([compile_pattern(e.form, e.frame, e.concept, e.intensity, entry_id=e.id) for e in entries])
    d = replace(themed.dictionary, entries={e.id: e for e in entries}, form_index=forms)
    assert not theme_issues("Have a crack.", "Try it.", d, frozenset())
    assert theme_issues("Smoke crack.", "Have a crack.", d, frozenset())
    assert not theme_issues("Smoke crack.", "Smoke crack.", d, frozenset())
    allowed = replace(entries[0], themes=())
    d = replace(d, entries={**d.entries, allowed.id: allowed})
    assert theme_issues("Smoke crack.", "Try it.", d, frozenset())


@pytest.mark.parametrize("kind", ["riff", "imagery", "garnish"])
def test_allowed_fixed_colour_owns_its_nested_homonym(themed, kind):
    from aussiefy.semantic_checks import theme_issues

    entries = dict(themed.dictionary.entries)
    images = ()
    if kind == "riff":
        entries["zzplain"] = replace(entries["zzplain"], riffs=(Riff("give zzdrug a burl"),))
    elif kind == "imagery":
        images = (Imagery("zzimage", "give zzdrug a burl", ("TIRED",), "Fixture."),)
    else:
        entries["zzgarnish"] = Entry("zzgarnish", "give zzdrug a burl", (), "interjection", type="garnish")
    d = replace(themed.dictionary, entries=entries, imagery=images)
    assert not theme_issues("Give zzdrug a burl.", "Try it.", d, frozenset())
    assert theme_issues("I am zzdrug.", "Give zzdrug a burl.", d, frozenset())


def test_real_subject_tags_and_mixed_senses_use_normal_eligibility(translator):
    opts = {"translator": translator, "vulgarity": 0, "include_gated": True, "limit": 100,
            "document_config": {"themes": {"drinking": False}}}
    for query, kept, held in [("full after eating", "full-as-a-goog-food", "full-as-a-goog"),
                              ("tired", "stonkered-tired", "stonkered")]:
        ids = {e["id"] for e in harness.lookup(query, **opts)["results"]}
        assert kept in ids and held not in ids
    d = translator.dictionary
    assert d.entries["goon-of-fortune"].themes == ("drinking_games", "drinking")
    assert not d.entries["wanker"].themes
    assert not d.entries["flat-out-lizard"].themes


def test_real_child_riffs_carry_their_own_subjects(dictionary):
    allowed = dictionary.theme_defaults[3] - {"drinking", "gambling", "bodily_functions"}
    for eid, banned in [("esky", "tinnies"), ("drongo", "brewery"),
                        ("galah", "raffle"), ("bucketing-down", "pissin'")]:
        entry = dictionary.entries[eid]
        assert any(banned in riff.text for riff in entry.riffs)
        assert all(banned not in riff.text for riff in entry.riffs_within(3, allowed))
        card = entry_card(entry, permitted_themes=allowed)
        assert all(banned not in riff["text"] for riff in card.get("riffs", []))
    nan = resolve(Policy(vulgarity=0), dictionary).permitted_themes
    assert not dictionary.entries["bucketing-down"].riffs_within(0, nan)


@pytest.mark.parametrize("text", ["The box is full.", "The apples are rotten.", "The lizard is legless.",
                                  "Set it on a slab.", "The food is maggoted.", "The water sloshed around.",
                                  "Use a half-cut plank.", "She rode in a tinnie.", "Chrissie arrived."])
def test_real_ordinary_readings_are_not_treated_as_forbidden_subjects(text, translator):
    from aussiefy.semantic_checks import theme_issues
    from aussiefy.llm import ClaudeRewriter

    themes = frozenset()
    assert not theme_issues(text, "An ordinary statement.", translator.dictionary, themes)
    hook = ClaudeRewriter(cache=False, translator=translator)
    assert hook._problem(text, "An ordinary statement.", [], themes) is None


def test_split_senses_retain_all_existing_source_leads(dictionary):
    for old, new in [("stonkered", "stonkered-tired"), ("off-their-chops", "off-their-chops-high")]:
        assert {s.url for s in dictionary.entries[old].sources} == {s.url for s in dictionary.entries[new].sources}
        assert dictionary.entries[old].sources


@pytest.mark.parametrize("tier", range(4))
def test_guide_examples_obey_their_subject_tier(tier, translator):
    from aussiefy.semantic_checks import theme_issues
    guide = harness.guide(level=5, vulgarity=tier, translator=translator)
    prose = "\n".join(guide[key] for key in ("voice", "language", "craft"))
    eff = translator.effective(level=5, vulgarity=tier)
    assert not theme_issues(prose, None, translator.dictionary, eff.theme_policy)


@pytest.mark.parametrize("mode", ["plain", "changes", "markdown", "rewriter"])
def test_real_source_subjects_survive_restricted_translations(mode, translator):
    from aussiefy.terms import fold
    source = "We saw a dunny and a durry. They called it a bit of biffo. I might have a root."
    class Rewriter:
        model = "source-retention-fixture"
        def rewrite(self, original, draft, planned, **options):
            return draft, "retained draft"
    for seed in range(20):
        options = {"translator": translator, "vulgarity": 0, "seed": seed, "embellishment": 0}
        if mode == "rewriter":
            options.update(rewriter=Rewriter(), rewrite_mode="all")
        if mode == "markdown":
            options["markdown"] = True
        if mode == "rewriter":
            options.pop("translator")
            result = translator.translate(source, **options)
        else:
            result = (translate_changes if mode == "changes" else translate)(source, **options)
        for phrase in ("dunny", "durry", "biffo", "root"):
            assert phrase in fold(result.text)
        if mode == "rewriter":
            assert result.rewrites


def test_term_tiers_and_exact_theme_overrides_share_one_policy(translator):
    from aussiefy.evidence import theme_rejection
    d = translator.dictionary
    nan = translator.effective(vulgarity=0).theme_policy
    dad = translator.effective(vulgarity=1).theme_policy
    duck = next(x for x in d.imagery if x.id == "hungry-low-flying-duck")
    throat = next(x for x in d.imagery if x.id == "stomach-throat-cut")
    for term in (d.entries["dunny"], duck):
        assert not theme_rejection(term, nan)
    assert theme_rejection(throat, nan) and not theme_rejection(throat, dad)
    for eid in ("a-durry", "a-ciggie", "rollie", "dart-cigarette", "useful-as-an-ashtray"):
        assert theme_rejection(d.entries[eid], nan) and not theme_rejection(d.entries[eid], dad)
    disabled = translator.effective(vulgarity=3, document_config={"themes": {"bodily_functions": False}}).theme_policy
    assert theme_rejection(d.entries["dunny"], disabled)
    enabled = translator.effective(vulgarity=0, document_config={"themes": {"violence": True}}).theme_policy
    assert not theme_rejection(throat, enabled)
    # A term tier can also raise a theme which is otherwise enabled for Nan.
    assert theme_rejection(d.entries["g-bugger-me-sideways"], dad)
    assert not theme_rejection(d.entries["g-bugger-me-sideways"], translator.effective(vulgarity=2).theme_policy)


@pytest.mark.parametrize("eid,theme", [
    ("donger", "sex"), ("pash-obj", "sex"), ("off-like-a-brides-nightie", "sex"),
    ("colder-than-a-witchs-tit", "sex"), ("cold-enough-brass-monkey", "sex"),
    ("aggro", "violence"), ("towel-up", "violence"), ("cruisin-for-a-bruisin", "violence"),
    ("chunder", "bodily_functions"), ("enough-to-make-a-brown-dog-spew", "bodily_functions"),
])
def test_approved_mature_uses_start_at_dad_with_exact_overrides(eid, theme, translator):
    from aussiefy.evidence import theme_rejection
    term = translator.dictionary.entries[eid]
    assert theme_rejection(term, translator.effective(vulgarity=0).theme_policy)
    assert not theme_rejection(term, translator.effective(vulgarity=1).theme_policy)
    assert not theme_rejection(term, translator.effective(vulgarity=0,
        document_config={"themes": {theme: True}}).theme_policy)
    assert theme_rejection(term, translator.effective(vulgarity=3,
        document_config={"themes": {theme: False}}).theme_policy)


@pytest.mark.parametrize("eid", ["a-spunk", "a-spunkrat", "spunky", "have-a-barney",
    "get-your-gear-off", "pox-doctors-clerk", "budgie-smugglers", "spewin"])
def test_subject_tags_follow_the_curated_sense_not_word_associations(eid, dictionary):
    assert not dictionary.entries[eid].themes


@pytest.mark.parametrize("tags", [[{"name": "sex", "tier": True}], [{"name": "sex", "tier": -1}],
                                  [{"name": "sex", "tier": 4}], ["sex", "sex"],
                                  [{"name": "sex", "tier": 1, "extra": True}]])
def test_bad_tag_tiers_fail_at_the_data_boundary(tags):
    from aussiefy.evidence import parse_metadata
    with pytest.raises(SchemaError, match="tier|duplicate"):
        parse_metadata({"themes": tags}, "fixture")


def test_theme_registry_grows_from_data_and_rejects_unknown_tags(data_copy):
    from aussiefy.evidence import theme_rejection
    path = data_copy / "themes.yaml"
    raw = yaml.safe_load(path.read_text())
    for tier in raw:
        raw[tier]["new_subject"] = tier >= 1
    path.write_text(yaml.safe_dump(raw))
    d = load_dictionary(data_dir=data_copy)
    term = Entry("fixture", "fixture", ("TIRED",), "adj", themes=("new_subject",))
    assert theme_rejection(term, resolve(Policy(vulgarity=0), d).theme_policy)
    assert not theme_rejection(term, resolve(Policy(vulgarity=1), d).theme_policy)
    p = data_copy / "entries/lexical.yaml"
    entries = yaml.safe_load(p.read_text())
    entries[0]["themes"] = ["not_registered"]
    p.write_text(yaml.safe_dump(entries))
    with pytest.raises(SchemaError, match="unknown themes"):
        load_dictionary(data_dir=data_copy)


def test_tag_tiers_round_trip_without_a_second_stored_field(dictionary):
    from aussiefy.schema import parse_entry
    entry = dictionary.entries["dunny"]
    raw = entry.to_dict()
    assert raw["themes"] == [{"name": "bodily_functions", "tier": 0}]
    assert "theme_tiers" not in raw
    assert parse_entry(raw).theme_tiers == entry.theme_tiers



def test_canonical_expression_rating_owns_nested_swear_words(translator):
    def rude(text, original=None):
        return [i for i in harness.lint(text, original=original, vulgarity=0, translator=translator,
                                      suggest=False)["issues"] if i["kind"] == "too_vulgar"]
    assert not rude("Bloody hell.")
    assert rude("Bloody hell, that is bloody hard.")
    assert rude("That is bloody hard.", "Bloody hell.")
    # The same general mechanism respects new curator-rated phrases, without naming them in Python.
    entry = Entry("fixture", "bloody nonsense", ("TIRED",), "np", vulgarity=0)
    d = replace(translator.dictionary, entries={**translator.dictionary.entries, entry.id: entry})
    assert any(tier == 0 and pattern.search("bloody nonsense") for pattern, tier in d.phrase_swear_ratings)



def test_graded_theme_policy_reaches_agent_briefs(translator):
    session = brief("I am hungry.", translator=translator, vulgarity=0, embellishment=2)
    rules = session.payload["THEME_RULES"]
    assert session.payload["THEME_PERMISSIONS"]["sex"] is False
    assert rules["sex"] == {"default_tier": 2, "allowed_through": 0}
    blocked = brief("I am hungry.", translator=translator, vulgarity=0,
                    document_config={"themes": {"sex": False}})
    assert blocked.payload["THEME_RULES"]["sex"]["allowed_through"] == -1


def test_model_acceptance_and_cache_use_the_graded_policy(translator, tmp_path):
    from aussiefy.llm import ClaudeRewriter
    from conftest import FakeClaude, json_reply
    output = "I am hungry enough to eat the crotch out of a low-flying duck."
    hook = ClaudeRewriter(client=FakeClaude(json_reply({"text": output})), cache_dir=tmp_path, translator=translator)
    nan = translator.effective(vulgarity=0).theme_policy
    for _ in range(2):
        assert hook.rewrite("I am hungry.", "I am hungry.", [], level=5, vulgarity=0, theme_policy=nan)[0] == output
    assert len(hook.client.calls) == 1
    banned = translator.effective(vulgarity=0, document_config={"themes": {"sex": False}}).theme_policy
    rejected = ClaudeRewriter(client=FakeClaude(json_reply({"text": output})), cache_dir=tmp_path, translator=translator)
    assert rejected.rewrite("I am hungry.", "I am hungry.", [], level=5, vulgarity=0, theme_policy=banned)[0] is None
    assert len(rejected.client.calls) == 1


def test_builtin_sentence_guide_does_not_teach_forbidden_dad_terms(translator):
    from aussiefy.llm import REWRITE_SYSTEM
    from aussiefy.semantic_checks import theme_issues
    dad = translator.effective(vulgarity=1).theme_policy
    assert not theme_issues(REWRITE_SYSTEM, None, translator.dictionary, dad)
