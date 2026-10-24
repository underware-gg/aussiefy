"""Stable explicit discovery does not certify a term as a contextual replacement."""

from dataclasses import replace

import pytest

from aussiefy import Translator
from aussiefy.errors import UserError
from aussiefy.explore import get_entry, list_entries, random_entry, suggest_name
from aussiefy.schema import Entry
from aussiefy.names import SLUG, SHAPES
from aussiefy import load_dictionary
from aussiefy.errors import SchemaError
import yaml


def test_pages_are_stable_complete_and_distinguish_exhaustion(dictionary):
    entries = {f"term-{n:03}": Entry(f"term-{n:03}", f"thing {n}", ("HUNGRY",), "np") for n in range(125)}
    tr = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    reverse = Translator(replace(dictionary, entries=dict(reversed(list(entries.items())))), lookup_embedder=None)
    seen, offset = [], 0
    while offset is not None:
        page = list_entries(limit=30, offset=offset, concept="hungry", translator=tr)
        assert page == list_entries(limit=30, offset=offset, concept="HUNGRY", translator=reverse)
        assert page["total"] == 125
        seen.extend(entry["id"] for entry in page["results"])
        offset = page["next_offset"]
    assert seen == sorted(entries)
    end = list_entries(offset=125, translator=tr)
    assert end["outcome"] == "page_exhausted" and not end["results"] and end["next_offset"] is None
    picked = {random_entry(seed=n, translator=tr)["entry"]["id"] for n in range(100)}
    assert any(key > "term-099" for key in picked)
    assert random_entry(seed=9, translator=tr) == random_entry(seed=9, translator=reverse)


def test_discovery_marks_holds_and_never_returns_omitted_entries(dictionary):
    entries = {
        "ordinary": Entry("ordinary", "ordinary", ("HUNGRY",), "np"),
        "foreign": Entry("foreign", "foreign", ("HUNGRY",), "np", reads_as="british"),
        "manual": Entry("manual", "manual", ("HUNGRY",), "np", status="gate"),
        "omitted": Entry("omitted", "omitted", ("HUNGRY",), "np", status="omit"),
    }
    tr = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    assert [row["id"] for row in list_entries(translator=tr)["results"]] == ["ordinary"]
    shown = {row["id"]: row for row in list_entries(include_gated=True, translator=tr)["results"]}
    assert set(shown) == {"ordinary", "foreign", "manual"}
    assert shown["foreign"]["held_back"] == ["reads_as"]
    assert shown["manual"]["held_back"] == ["status"]
    assert get_entry("foreign", translator=tr)["outcome"] == "nothing_fits"
    assert get_entry("missing", translator=tr)["outcome"] == "not_in_dictionary"
    assert get_entry("foreign", include_gated=True, translator=tr)["entry"] == shown["foreign"]
    assert get_entry("omitted", include_gated=True, translator=tr)["entry"] is None


def test_filters_and_exact_permissions_share_the_existing_policy(translator):
    opts = {"translator": translator, "vulgarity": 1, "concept": "THIRSTY", "theme": "sex"}
    rows = list_entries(**opts)["results"]
    assert "dry-as-a-dead-dingo" in {row["id"] for row in rows}
    assert all("THIRSTY" in row["concepts"] and "sex" in row["themes"] for row in rows)
    disabled = {**opts, "document_config": {"themes": {"sex": False}}}
    assert list_entries(**disabled)["outcome"] == "nothing_fits"
    assert random_entry(**disabled)["entry"] is None
    assert get_entry("dry-as-a-dead-dingo", vulgarity=0, document_config={"themes": {"sex": True}},
                     translator=translator)["entry"] is None


@pytest.mark.parametrize("options", [{"limit": True}, {"limit": 0}, {"limit": 101}, {"offset": True},
                                     {"offset": -1}, {"theme": "unknown"}, {"concept": "unknown"}])
def test_invalid_discovery_requests_raise(options, translator):
    with pytest.raises(UserError):
        list_entries(translator=translator, **options)


def test_random_seed_and_entry_id_are_checked(translator):
    with pytest.raises(UserError):
        random_entry(seed=True, translator=translator)
    with pytest.raises(UserError):
        get_entry([], translator=translator)


def test_names_are_seeded_clean_and_cover_the_three_reviewed_shapes(translator):
    names = set()
    for shape in SHAPES:
        for seed in range(40):
            result = suggest_name(seed=seed, shape=shape, translator=translator)
            assert result == suggest_name(seed=seed, shape=shape, translator=translator)
            assert result["outcome"] == "matched" and result["shape"] == shape
            assert result["vulgarity"] == 0 and result["themes"] == []
            assert SLUG.fullmatch(result["name"])
            names.add(result["name"])
    assert {"stoked-goanna", "fair-dinkum-legend"} <= names
    assert any("-from-" in name for name in names)
    assert len(names) > 40
    assert {suggest_name(seed=n, translator=translator)["shape"] for n in range(30)} == set(SHAPES)


@pytest.mark.parametrize("change", [
    lambda raw: raw["descriptors"].append("missing"),
    lambda raw: raw["places"].append("Upper_Case"),
    lambda raw: raw["places"].append(raw["places"][0]),
    lambda raw: raw["phrases"].append([]),
])
def test_names_catalogue_rejects_invalid_or_known_disallowed_parts(data_copy, change):
    path = data_copy / "names.yaml"
    raw = yaml.safe_load(path.read_text())
    change(raw)
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match="names.yaml"):
        load_dictionary(data_dir=data_copy)


def test_names_allow_missing_catalogue_and_check_request_options(data_copy, translator):
    (data_copy / "names.yaml").unlink()
    tr = Translator(load_dictionary(data_dir=data_copy), lookup_embedder=None)
    assert suggest_name(translator=tr)["outcome"] == "nothing_fits"
    for options in ({"seed": True}, {"shape": []}, {"shape": "unknown"}):
        with pytest.raises(UserError):
            suggest_name(translator=translator, **options)


def test_no_match_codes_preserve_meaning_and_direct_term_recognition(dictionary):
    from aussiefy import lookup
    tr = Translator(replace(dictionary, entries={
        "held": Entry("held", "testnoun", ("HUNGRY",), "predicate_adj", status="gate", gloss="xylophone"),
    }, imagery=()), lookup_embedder=None)
    assert lookup("hungry", translator=tr)["outcome"] == "nothing_fits"
    assert lookup("testnoun", translator=tr)["outcome"] == "nothing_fits"
    assert lookup("testnoun", include_gated=True, translator=tr)["outcome"] == "matched"
    assert lookup("xylophone", translator=tr)["outcome"] == "nothing_fits"
    assert lookup("xylophone", include_gated=True, translator=tr)["outcome"] == "matched"
    assert lookup("harpsichord", translator=tr)["outcome"] == "not_in_dictionary"
    for query, limit in (("", 8), (None, 8), ("hungry", True)):
        with pytest.raises(UserError):
            lookup(query, limit=limit, translator=tr)
    omitted = replace(tr.dictionary.entries["held"], status="omit")
    tr = Translator(replace(tr.dictionary, entries={omitted.id: omitted}), lookup_embedder=None)
    assert lookup("testnoun", include_gated=True, translator=tr)["outcome"] == "not_in_dictionary"


def test_variations_validate_whole_expressions_and_keep_other_parts_fixed(translator):
    from aussiefy import variations
    options = dict(family="sideways-with-implement", parts={"stem": "bugger-sideways", "ending": "rusty-spanner"},
                   vulgarity=2, translator=translator)
    out = variations(**options)
    assert out == variations(**options)
    assert out["outcome"] == "matched"
    for group in out["variations"]:
        assert len(group["options"]) == 2
        for candidate in group["options"]:
            assert candidate["evidence"] == "bulldust" and candidate["construction_id"]
            for part in candidate["parts"]:
                if part["role"] != group["role"]:
                    assert part["ingredient_id"] == options["parts"][part["role"]]
                assert candidate["text"][slice(*part["out_span"])] == part["text"]
    denied = variations(**{**options, "document_config": {"themes": {"sex": False}}})
    assert denied["outcome"] == "nothing_fits" and all(not group["options"] for group in denied["variations"])
    for overrides in ({"family": None}, {"parts": None}, {"parts": {}}, {"parts": {"stem": "hungry"}},
                      {"parts": {"stem": "hungry", "ending": "rusty-spanner"}}, {"seed": True}):
        with pytest.raises(UserError):
            variations(**{**options, **overrides})


@pytest.mark.parametrize("command,function,args,kwargs", [
    ("entries", "list_entries", ["--concept", "HUNGRY", "--theme", "sex", "--limit", "3", "--offset", "1"],
     {"concept": "HUNGRY", "theme": "sex", "limit": 3, "offset": 1}),
    ("entry", "get_entry", ["stoked"], {"entry_id": "stoked"}),
    ("random-entry", "random_entry", ["--seed", "7", "--concept", "HUNGRY"], {"seed": 7, "concept": "HUNGRY"}),
    ("suggest-name", "suggest_name", ["--seed", "9", "--shape", "place"], {"seed": 9, "shape": "place"}),
    ("variations", "variations", ["hungry-enough-to", "--parts", '{"state":"hungry","act":"sausage-shadow"}'],
     {"family": "hungry-enough-to", "parts": {"state": "hungry", "act": "sausage-shadow"}}),
])
def test_exploration_cli_returns_the_python_result(command, function, args, kwargs, capsys):
    import json
    import aussiefy
    from aussiefy.cli import main
    expected = getattr(aussiefy, function)(**kwargs)
    status = main([command, "--json", *args])
    assert json.loads(capsys.readouterr().out) == expected
    assert status == (0 if expected["outcome"] == "matched" else 1)


def test_exploration_page_cap_is_enforced_by_hosted_mcp():
    import asyncio
    from aussiefy.mcp_server import build_server
    from mcp.server.mcpserver.exceptions import ToolError
    server = build_server(lookup_limit=3)
    response = asyncio.run(server.call_tool("aussie_entries", {})).structured_content
    assert response["limit"] == 3 and len(response["results"]) <= 3
    with pytest.raises(ToolError):
        asyncio.run(server.call_tool("aussie_entries", {"limit": 4}))


def test_names_never_use_known_garnish_insults_or_themed_literal_parts(data_copy):
    path = data_copy / "names.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["things"] = ["ya-galah", "ya-drongo", "goon-bag"]
    raw["nicknames"] = ["fuckwit"]
    raw["phrases"] = [["bugger-me-sideways"]]
    path.write_text(yaml.safe_dump(raw))
    tr = Translator(load_dictionary(data_dir=data_copy), lookup_embedder=None)
    assert all(suggest_name(shape=shape, translator=tr)["outcome"] == "nothing_fits" for shape in SHAPES)


def test_names_do_not_make_valid_translation_overlays_fail(tmp_path):
    overlay = tmp_path / "held-name-word.yaml"
    overlay.write_text(yaml.safe_dump({"format": "aussiefy-dictionary-overlay/v1",
                                      "patch_entries": {"stoked": {"status": "gate"}}}))
    tr = Translator(load_dictionary([overlay]), lookup_embedder=None)
    for seed in range(40):
        name = suggest_name(shape="descriptive", seed=seed, translator=tr)["name"]
        assert name and not name.startswith("stoked-")


def test_image_recognition_precedes_embellishment_permission(translator):
    from aussiefy import lookup
    assert lookup("starting gun", embellishment=0, translator=translator)["outcome"] == "nothing_fits"
    assert lookup("starting gun", embellishment=2, translator=translator)["outcome"] == "matched"


def test_every_known_fixed_hazard_survives_name_punctuation_normalisation(dictionary):
    from aussiefy.names import _safe
    from aussiefy.schema import PLACEHOLDER_RE
    from aussiefy.terms import name_slug
    for entry in dictionary.entries.values():
        if not (entry.vulgarity or entry.themes or entry.insult or entry.status == "omit"):
            continue
        for form in entry.all_forms:
            if not PLACEHOLDER_RE.search(form):
                assert not _safe(name_slug(form), dictionary), (entry.id, form)


def test_meaning_recognition_precedes_semantic_permission(dictionary):
    from aussiefy import lookup
    entry = Entry("judgment", "testnoun", ("HUNGRY",), "predicate_adj", gloss="xylophone",
                  semantic_effects=("opinion",))
    tr = Translator(replace(dictionary, entries={entry.id: entry}, imagery=()), lookup_embedder=None)
    assert lookup("xylophone", document_config={"narrator_opinion": False}, translator=tr)["outcome"] == "nothing_fits"
    assert lookup("xylophone", document_config={"narrator_opinion": True}, translator=tr)["outcome"] == "matched"
    direct = lookup("testnoun", document_config={"narrator_opinion": False}, translator=tr)
    assert direct["outcome"] == "matched" and not direct["results"][0]["effects_permitted"]


def test_attached_reflexive_hazards_use_the_existing_morphology(dictionary):
    from aussiefy.names import _safe
    for pronoun in ("oneself", "myself", "yourself", "himself", "herself", "itself", "ourselves", "themselves"):
        assert not _safe("top-" + pronoun, dictionary)


def test_name_safety_includes_known_themed_riffs_and_imagery(dictionary):
    from aussiefy.names import _safe
    from aussiefy.schema import Riff, Imagery
    holder = Entry("holder", "holder", ("HUNGRY",), "adj",
                   riffs=(Riff("fists in flight", themes=("violence",)),))
    image = Imagery("fixture", "with a glass of grog", ("HUNGRY",), "comparison", themes=("drinking",))
    d = replace(dictionary, entries={**dictionary.entries, holder.id: holder}, imagery=(*dictionary.imagery, image))
    assert not _safe("fists-in-flight", d)
    assert not _safe("with-a-glass-of-grog", d)


def test_slotted_imagery_keeps_its_hazard_after_handle_punctuation_changes(dictionary):
    from aussiefy.names import _safe
    assert not _safe("her-stomach-thinks-her-throat-s-been-cut", dictionary)
