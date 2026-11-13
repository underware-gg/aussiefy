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
    entries = {f"term-{n:03}": Entry(f"term-{n:03}", f"thing {n:03}", ("HUNGRY",), "np") for n in range(125)}
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
    hidden = get_entry("omitted", include_gated=True, translator=tr)
    assert hidden["entry"] is None and hidden["outcome"] == "not_in_dictionary" and "reason" not in hidden


def test_filters_and_exact_permissions_share_the_existing_policy(translator):
    opts = {"translator": translator, "vulgarity": 1, "concept": "THIRSTY", "theme": "sex"}
    rows = list_entries(**opts)["results"]
    assert "dry-as-a-dead-dingo" in {row["id"] for row in rows}
    assert all("THIRSTY" in row["concepts"] and "sex" in {tag['name'] for tag in row["themes"]} for row in rows)
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
    assert "no compatible suggestion" in lookup("hungry", translator=tr)["note"]
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
    ("wordless-meanings", "list_wordless_meanings", ["--limit", "5", "--offset", "3"], {"limit": 5, "offset": 3}),
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
    for tool in ("aussie_entries", "aussie_wordless_meanings"):
        response = asyncio.run(server.call_tool(tool, {})).structured_content
        assert response["limit"] == 3 and len(response["results"]) <= 3
        with pytest.raises(ToolError):
            asyncio.run(server.call_tool(tool, {"limit": 4}))


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


def _readings(source, dictionary):
    from aussiefy.detect import detect, resolve_overlaps
    from aussiefy.text import tokenize
    found = resolve_overlaps(detect(tokenize(source), dictionary.index, concepts=dictionary.concepts,
                                    adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index,
                                    person_nouns=dictionary.person_nouns))
    return {cid for reading in found for cid in reading.concepts}


def test_wordless_meanings_page_only_genuine_meanings_with_plain_wording(translator):
    from aussiefy.explore import list_wordless_meanings
    from aussiefy.schema import HOLDING_CONCEPT
    d = translator.dictionary
    seen, offset = [], 0
    while offset is not None:
        page = list_wordless_meanings(offset=offset, limit=7, translator=translator)
        assert page["total"] == len(d.wordless_meanings) and page["outcome"] == "matched"
        seen.extend(page["results"])
        offset = page["next_offset"]
    ids = [row["concept"] for row in seen]
    assert ids == sorted(ids) and {"ACCEPT_AS_TRUE", "HEART_SPIRIT", "FANCIFUL"} <= set(ids)
    assert not {HOLDING_CONCEPT, "BROKEN_OTHER_SENSE"} & set(ids)
    assert "BIN" not in ids   # the dialect table already swaps "trash can" for the Australian "bin"
    assert all(row["plain"] and row["examples"] for row in seen)
    assert not {cid for e in d.entries.values() if e.status != "omit" for cid in e.concept} & set(ids)
    end = list_wordless_meanings(offset=len(ids), translator=translator)
    assert end["outcome"] == "page_exhausted" and end["next_offset"] is None


@pytest.mark.parametrize("options", [{"limit": True}, {"limit": 0}, {"limit": 101}, {"offset": True}, {"offset": -1}])
def test_invalid_wordless_meaning_pages_raise(options, translator):
    from aussiefy.explore import list_wordless_meanings
    with pytest.raises(UserError):
        list_wordless_meanings(translator=translator, **options)


def test_every_concept_example_reads_as_its_meaning(dictionary):
    for cid, concept in dictionary.concepts.items():
        for example in concept.examples:
            assert cid in _readings(example, dictionary), (cid, example)


def test_a_word_for_a_meaning_takes_it_off_the_waiting_list(dictionary):
    from aussiefy import lookup
    from aussiefy.explore import list_wordless_meanings
    word = Entry("test-heart", "testheart", ("HEART_SPIRIT",), "vp")
    tr = Translator(replace(dictionary, entries={**dictionary.entries, word.id: word}), lookup_embedder=None)
    assert "HEART_SPIRIT" not in tr.dictionary.wordless_meanings
    assert "HEART_SPIRIT" not in {row["concept"] for row in list_wordless_meanings(limit=100, translator=tr)["results"]}
    assert lookup("take heart", translator=tr)["outcome"] == "matched"


def test_imagery_is_not_a_word_but_a_construction_can_express_the_meaning(dictionary):
    from aussiefy.schema import Imagery
    image = Imagery("test-heart-image", "like a lion", ("HEART_SPIRIT",), "comparison")
    assert "HEART_SPIRIT" in replace(dictionary, imagery=(*dictionary.imagery, image)).wordless_meanings
    catalog = dictionary.construction_catalog
    family = replace(catalog.families[0], concept="HEART_SPIRIT")
    with_family = replace(dictionary, construction_catalog=replace(catalog, families=(*catalog.families, family)))
    assert "HEART_SPIRIT" not in with_family.wordless_meanings


def _overlay(tmp_path, document):
    path = tmp_path / "overlay.yaml"
    path.write_text(yaml.safe_dump({"format": "aussiefy-dictionary-overlay/v1", **document}), encoding="utf-8")
    return path


def test_the_holding_concept_cannot_be_unmarked_to_take_entries(tmp_path):
    path = _overlay(tmp_path, {"patch_concepts": {"UNRESOLVED_SENSE": {"no_entries": True}}})
    with pytest.raises(SchemaError, match="unknown fields.*no_entries"):
        load_dictionary([path])


def test_an_extension_meaning_without_plain_wording_is_flagged(tmp_path):
    path = _overlay(tmp_path, {"add_concepts": {"TEST_WAITING": {
        "description": "A test meaning.", "triggers": {"vp": ["zorbulate"]}}}})
    d = load_dictionary([path])
    assert "TEST_WAITING" in d.wordless_meanings
    assert any("TEST_WAITING" in warning and "plain wording" in warning for warning in d.warnings)


def test_images_and_constructions_cannot_target_abstention(data_copy):
    path = data_copy / "imagery.yaml"
    raw = yaml.safe_load(path.read_text())
    raw[0]["concepts"] = ["UNRESOLVED_SENSE"]
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match="takes no images or constructions"):
        load_dictionary(data_dir=data_copy)


def test_a_blank_names_catalogue_fails_to_load(data_copy):
    (data_copy / "names.yaml").write_text("")
    with pytest.raises(SchemaError, match="names.yaml"):
        load_dictionary(data_dir=data_copy)


def test_lookup_says_when_a_recognised_meaning_has_no_word_yet(translator):
    from aussiefy import lookup
    waiting = lookup("take heart", translator=translator)
    assert waiting["outcome"] == "no_word_yet" and not waiting["results"]
    assert waiting["meanings"] == [{"concept": "HEART_SPIRIT",
                                    "plain": translator.dictionary.concepts["HEART_SPIRIT"].plain}]
    assert lookup("fantastic terrors", translator=translator)["outcome"] == "no_word_yet"
    # a waiting meaning's trigger negated or embedded in more than it explains is not claimed, nor is a guard
    for query in ("not the fallen", "I never bring into being", "not loyalty", "harpsichord"):
        assert lookup(query, translator=translator)["outcome"] != "no_word_yet", query
    assert lookup("very busy", translator=translator)["outcome"] == "matched"


def test_cli_lookup_names_the_meaning_with_no_word_yet(capsys, dictionary):
    from aussiefy.cli import main
    assert main(["lookup", "take", "heart"]) == 1
    assert f"meaning HEART_SPIRIT: {dictionary.concepts['HEART_SPIRIT'].plain}" in capsys.readouterr().out


@pytest.mark.parametrize("backend", ["none", "bundled"])
@pytest.mark.parametrize("level,vulgarity,embellishment", [(1, 0, 0), (5, 3, 2)])
def test_every_waiting_meaning_round_trips_through_lookup(dictionary, backend, level, vulgarity, embellishment):
    from aussiefy import lookup
    tr = Translator(dictionary, lookup_embedder=backend)
    for cid in dictionary.wordless_meanings:
        concept = dictionary.concepts[cid]
        for wording in (concept.plain, *concept.examples):
            result = lookup(wording, translator=tr, level=level, vulgarity=vulgarity,
                            embellishment=embellishment)
            assert result["outcome"] == "no_word_yet", (cid, wording, result)
            assert cid in {row["concept"] for row in result["meanings"]}, (cid, wording, result)
            assert all(row.get("match") != "meaning (local model)" for row in result["results"])


def test_exact_plain_wording_is_authored_evidence_not_a_fuzzy_guess(tmp_path):
    from aussiefy import lookup
    path = _overlay(tmp_path, {"add_concepts": {"TEST_WAITING": {
        "description": "A synthetic meaning.", "plain": "an inexplicably adequate situation", "triggers": {}}}})
    tr = Translator(load_dictionary([path]), lookup_embedder=None)
    result = lookup("  AN  inexplicably adequate situation  ", translator=tr)
    assert result["outcome"] == "no_word_yet"
    assert result["meanings"] == [{"concept": "TEST_WAITING", "plain": "an inexplicably adequate situation"}]
    assert lookup("not an inexplicably adequate situation", translator=tr)["outcome"] != "no_word_yet"


def test_a_wordless_reading_needs_no_model_and_cannot_be_rescued_by_unrelated_dial_rejections(dictionary):
    from aussiefy import lookup

    class UnusedModel:
        lookup_threshold = .5

        def similarity(self, query, text):
            raise AssertionError("A settled wordless reading must not fall back to the model")

    tr = Translator(dictionary, lookup_embedder=UnusedModel())
    for query in ("fantastic terrors", "loyal devotion", "It will probably rain.", "take heart"):
        result = lookup(query, translator=tr, level=1, vulgarity=0)
        assert result["outcome"] == "no_word_yet" and not result["results"]


def test_a_wordless_verb_preserves_its_objects_independent_meaning():
    from aussiefy import lookup
    result = lookup("believe a liar", level=5, vulgarity=3)
    assert result["outcome"] == "no_word_yet"
    assert {row["concept"] for row in result["meanings"]} == {"ACCEPT_AS_TRUE"}
    assert any(row["form"] == "a bullshitter" for row in result["results"])


@pytest.mark.parametrize("query,cid", [("accept as true", "ACCEPT_AS_TRUE"), ("fanciful", "FANCIFUL"),
                                      ("ACCEPT_AS_TRUE", "ACCEPT_AS_TRUE")])
def test_an_explicit_meaning_name_is_discovery_evidence(query, cid, translator):
    from aussiefy import lookup
    result = lookup(query, translator=translator)
    assert result["outcome"] == "no_word_yet"
    assert cid in {row["concept"] for row in result["meanings"]}
    assert not result["results"]


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_preserves_wordless_outcome_with_independent_object_offers(capsys, json_output):
    import json
    from aussiefy.cli import main
    options = ["--json"] if json_output else []
    assert main(["lookup", "believe a liar", "--level", "5", *options]) == 1
    output = capsys.readouterr().out
    if json_output:
        result = json.loads(output)
        assert result["outcome"] == "no_word_yet" and result["results"] and result["meanings"]
    else:
        assert "a bullshitter" in output and "meaning ACCEPT_AS_TRUE" in output


def test_initial_pages_use_headwords_and_counts_respect_the_eligible_set(dictionary):
    entries={
        'kick-in-guts':Entry('kick-in-guts','a kick in the guts',('HUNGRY',),'np'),
        'kiwi':Entry('kiwi','kiwi',('HUNGRY',),'np'),
        'the-bush':Entry('the-bush','bush',('HUNGRY',),'np'),
        '3d-term':Entry('3d-term','3D term',('HUNGRY',),'np'),
        'keeper':Entry('keeper','kept back',('HUNGRY',),'np',status='gate'),
        'k-omitted':Entry('k-omitted','omitted',('HUNGRY',),'np',status='omit'),
        'k-other':Entry('k-other','kooky',('THIRSTY',),'np')}
    tr=Translator(replace(dictionary,entries=entries),lookup_embedder=None)
    page=list_entries(initial='k',concept='HUNGRY',limit=1,translator=tr)
    assert page['initial']=='k' and page['total']==2 and page['next_offset']==1
    assert [r['id'] for r in page['results']]==['kick-in-guts']
    assert page['initial_counts']['k']==2 and page['initial_counts']['b']==1 and page['initial_counts']['#']==1
    assert page['initial_counts']['z']==0 and len(page['initial_counts'])==27
    assert sum(page['initial_counts'].values())==4
    end=list_entries(initial='k',concept='HUNGRY',offset=2,translator=tr)
    assert end['outcome']=='page_exhausted' and end['total']==2 and end['initial_counts']==page['initial_counts']
    empty=list_entries(initial='z',concept='HUNGRY',translator=tr)
    assert empty['outcome']=='nothing_fits' and empty['total']==0 and empty['initial_counts']==page['initial_counts']
    assert [r['id'] for r in list_entries(initial='#',concept='HUNGRY',translator=tr)['results']]==['3d-term']
    assert list_entries(initial='k',concept='HUNGRY',include_gated=True,translator=tr)['total']==3
    assert list_entries(initial='k',translator=tr)['total']==3


def test_initial_counts_follow_theme_permissions_and_filters(translator):
    options={'translator':translator,'concept':'THIRSTY','theme':'sex','vulgarity':1}
    result=list_entries(**options)
    assert sum(result['initial_counts'].values())==result['total']
    assert result['initial_counts']['d'] >= 1
    disabled=list_entries(**options,themes={'sex':False})
    assert disabled['total']==0 and sum(disabled['initial_counts'].values())==0


@pytest.mark.parametrize('initial',['', 'K', 'ab', '1', '*', 3, True, []])
def test_initial_filter_rejects_invalid_values(translator,initial):
    with pytest.raises(UserError,match='initial'):
        list_entries(initial=initial,translator=translator)


def test_headword_collation_strips_whole_articles_and_uses_id_only_for_ties(dictionary):
    entries = {
        'z-counter': Entry('z-counter', 'a counter meal', ('HUNGRY',), 'np'),
        'a-hanrahan': Entry('a-hanrahan', 'a Hanrahan', ('HUNGRY',), 'np'),
        'z-earbashing': Entry('z-earbashing', 'AN earbashing', ('HUNGRY',), 'np'),
        'the-bush': Entry('the-bush', 'The bush', ('HUNGRY',), 'np'),
        'a-numeric': Entry('a-numeric', 'a 3D term', ('HUNGRY',), 'np'),
        'z-first': Entry('z-first', 'a kangaroo', ('HUNGRY',), 'np'),
        'a-last': Entry('a-last', 'the kiwi', ('HUNGRY',), 'np'),
        'a-tie': Entry('a-tie', 'an apple', ('HUNGRY',), 'np'),
        'z-tie': Entry('z-tie', 'the apple', ('HUNGRY',), 'np'),
        'z-article-prefix': Entry('z-article-prefix', 'another thing', ('HUNGRY',), 'np'),
    }
    tr = Translator(replace(dictionary, entries=entries), lookup_embedder=None)
    reverse = Translator(replace(dictionary, entries=dict(reversed(list(entries.items())))), lookup_embedder=None)
    page = list_entries(translator=tr)
    assert page == list_entries(translator=reverse)
    assert [x['id'] for x in page['results']] == [
        'a-numeric', 'z-article-prefix', 'a-tie', 'z-tie', 'the-bush', 'z-counter',
        'z-earbashing', 'a-hanrahan', 'z-first', 'a-last']
    assert page['initial_counts']['a'] == 3
    assert page['initial_counts']['h'] == page['initial_counts']['c'] == page['initial_counts']['#'] == 1
    assert [x['id'] for x in list_entries(initial='k', translator=tr)['results']] == ['z-first', 'a-last']
    assert list_entries(initial='k', limit=1, offset=1, translator=tr)['results'][0]['id'] == 'a-last'
    assert get_entry('a-hanrahan', translator=tr)['entry']['id'] == 'a-hanrahan'
