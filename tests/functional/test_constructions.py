"""Bounded, evidence-honest composition and its public surfaces."""

import json
from dataclasses import replace

import pytest
import yaml

from aussiefy import Translator, bulldust, load_dictionary, translate_changes
from aussiefy.constructions import ConstructionCatalog, ConstructionFamily, Ingredient, compose, generate, template_fragments
from aussiefy.errors import SchemaError, UserError
from aussiefy.evidence import Source, TermMetadata
from aussiefy.genre import resolve_document
from aussiefy.schema import Entry


def setting(tr, **config):
    return resolve_document(None, config=tr.dictionary.genres, document_type="general",
                            document_config=config or None).setting(2)


def test_seeded_results_keep_part_evidence_and_credit_without_borrowing_whole_sources(translator):
    args = dict(family="sideways-call-title", vulgarity=2, translator=translator)
    result = bulldust(**args)
    assert result == bulldust(**args)
    assert len(result["results"]) == 2
    for item in result["results"]:
        assert item["entry_id"] is None and item["construction_id"].startswith("construction/")
        assert item["evidence"] == "bulldust" and item["coined_by"] == "constructor"
        assert not item["sources"] and item["attestation"]["score"] == 0
        stem, ending = item["parts"]
        assert stem["entry_id"] in {"bugger-me-sideways", "fuck-me-sideways"} and stem["sources"]
        assert ending["credit"] == "Rob" and ending["coined_by"] == "person"
        for part in item["parts"]:
            assert item["text"][slice(*part["out_span"])] == part["text"]


def test_hunger_families_are_clean_and_readable(translator):
    items = bulldust("hungry", vulgarity=0, translator=translator)["results"]
    assert {item["text"] for item in items} == {
        "hungry enough to eat the shadow off a sausage",
        "hungry enough to lick the grease out of a pie warmer",
        "hungry enough to eat a fence post with tomato sauce"}
    assert all(item["vulgarity"] == 0 and item["frame"] == "predicate_adj" for item in items)
    assert len({bulldust("hungry", vulgarity=0, seed=n, translator=translator)["results"][0]["text"]
                for n in range(12)}) > 1


@pytest.mark.parametrize("family,theme", [("sideways-with-implement", "sex"), ("sideways-call-title", "religion")])
def test_family_can_raise_theme_without_changing_swear_cap(translator, family, theme):
    assert not bulldust(family=family, vulgarity=1, translator=translator)["results"]
    bob = bulldust(family=family, vulgarity=2, translator=translator)["results"]
    assert bob and all(theme in item["themes"] and all(isinstance(tag, str) for tag in item["themes"]) for item in bob)
    dad = bulldust(family=family, vulgarity=1, document_config={"themes": {theme: True}}, translator=translator)["results"]
    assert dad and all(item["vulgarity"] == 1 for item in dad)
    assert not bulldust(family=family, vulgarity=0, document_config={"themes": {theme: True}}, translator=translator)["results"]
    assert not bulldust(family=family, vulgarity=3, document_config={"themes": {theme: False}}, translator=translator)["results"]


def test_pinned_parts_only_vary_compatible_slots(translator):
    result = bulldust(family="sideways-with-implement", parts={"stem": "bugger-sideways"}, vulgarity=2,
                      translator=translator)
    assert len(result["results"]) == 2
    assert all(item["parts"][0]["ingredient_id"] == "bugger-sideways" for item in result["results"])
    mismatch = bulldust(family="sideways-with-implement", parts={"stem": "hungry"}, vulgarity=2, translator=translator)
    assert mismatch["outcome"] == "no-compatible-construction"
    for args in ({"parts": {"nonesuch": "hungry"}}, {"parts": {"state": "nonesuch"}}, {"family": "nonesuch"},
                 {"concept": "nonesuch"}, {"parts": []}, {"limit": True}, {"limit": 21}):
        with pytest.raises(UserError):
            bulldust(translator=translator, **args)


def _toy(dictionary, *, count=1, metadata=TermMetadata(), family_metadata=TermMetadata()):
    parts = tuple(Ingredient(f"left-{n}", "left", f"left{n}", metadata=metadata) for n in range(count))
    parts += tuple(Ingredient(f"right-{n}", "right", f"right{n}") for n in range(count))
    slots = (("left", "left"), ("right", "right"))
    family = ConstructionFamily("fixture", "{left} then {right}", slots,
                                template_fragments("{left} then {right}", slots), "HUNGRY", "predicate_adj",
                                metadata=family_metadata, preferred_words=(3, 3))
    catalog = ConstructionCatalog(parts, (family,), search_budget=32)
    return Translator(replace(dictionary, construction_catalog=catalog))


def test_template_order_opaque_text_unicode_and_identity(dictionary):
    tr = _toy(dictionary)
    slots = (("left", "left"), ("right", "right"))
    family = replace(tr.dictionary.construction_catalog.families[0], template="{right} — {left}",
                     fragments=template_fragments("{right} — {left}", slots))
    chosen = {"left": Ingredient("one", "left", "🦘 {right}"), "right": Ingredient("two", "right", "é")}
    eff = tr.effective(vulgarity=0)
    item = compose(family, chosen, tr.dictionary, eff)
    assert item.text == "é — 🦘 {right}"
    assert [p.role for p in item.parts] == ["right", "left"]
    assert all(item.text[slice(*part.span)] == part.ingredient.text for part in item.parts)
    citation = Source("media", "fixture", ("term",), url="https://example.org/term")
    amended = {**chosen, "left": replace(chosen["left"], metadata=TermMetadata(sources=(citation,)))}
    assert compose(family, amended, tr.dictionary, eff).id == item.id
    other = replace(family, template="{right}: {left}", fragments=template_fragments("{right}: {left}", slots))
    assert compose(other, chosen, tr.dictionary, eff).id != item.id
    with pytest.raises(SchemaError, match="incompatible"):
        compose(family, {**chosen, "left": chosen["right"]}, tr.dictionary, eff)


@pytest.mark.parametrize("template", ["{left} {left}", "{left}", "{left!r} {right}", "{left:>4} {right}", "{left.x} {right}", "{left"])
def test_templates_reject_ambiguous_or_executable_formatting(template):
    with pytest.raises(SchemaError):
        template_fragments(template, (("left", "left"), ("right", "right")))


def test_sampling_is_bounded_and_collisions_cover_dictionary_forms(dictionary):
    tr = _toy(dictionary, count=200)
    generated = generate(tr.dictionary, tr.effective(vulgarity=0), setting(tr), limit=20)
    assert generated.attempts == 32 and len(generated.candidates) == 20
    assert generated == generate(tr.dictionary, tr.effective(vulgarity=0), setting(tr), limit=20)
    exact = _toy(dictionary)
    entry = Entry("existing", "left0 then right0", ("HUNGRY",), "predicate_adj")
    blocked = Translator(replace(exact.dictionary, entries={**dictionary.entries, entry.id: entry}))
    assert not generate(blocked.dictionary, blocked.effective(vulgarity=0), setting(blocked)).candidates


@pytest.mark.parametrize("metadata", [TermMetadata(reads_as="american"), TermMetadata(australian_use="uncommon"),
                                       TermMetadata(doubtful_definition=True), TermMetadata(register="dated")])
def test_all_parts_obey_usage_meaning_and_register_gates(dictionary, metadata):
    tr = _toy(dictionary, metadata=metadata)
    assert not generate(tr.dictionary, tr.effective(vulgarity=0, registers=["current"]), setting(tr)).candidates


def test_part_tiers_survive_weaker_family_and_exact_override(dictionary):
    tr = _toy(dictionary, metadata=TermMetadata(themes=("sex",), theme_tiers=(("sex", 3),)),
              family_metadata=TermMetadata(themes=("sex",), theme_tiers=(("sex", 1),)))
    assert not generate(tr.dictionary, tr.effective(vulgarity=2), setting(tr)).candidates
    eff = tr.effective(vulgarity=0, document_config={"themes": {"sex": True}})
    item = generate(tr.dictionary, eff, setting(tr)).candidates[0]
    assert dict(item.metadata.theme_tiers)["sex"] == 3


@pytest.mark.parametrize("change,match", [
    (lambda r: r["ingredients"][0].update(entry_id="missing"), "unknown ingredient entry"),
    (lambda r: r["ingredients"][0].update(text="extra"), "inherits all"),
    (lambda r: r["families"][0].update(template="{stem} {stem}"), "every declared slot"),
    (lambda r: r["families"][0]["slots"].update(ending="missing"), "unknown ingredient kind"),
    (lambda r: r["settings"].update(search_budget=True), "integer"),
    (lambda r: r["families"][0].update(placement=[]), "only opener"),
    (lambda r: r["families"][0].update(converted_parts={"stem": "bugger-sideways"}), "pin every slot"),
    (lambda r: r["families"][0].update(converted_parts={"stem": "bugger-sideways", "ending": "hungry"}), "incompatible ingredient"),
    (lambda r: r["ingredients"].append(r["ingredients"][0]), "duplicate ingredient"),
])
def test_catalogue_validation_at_load(data_copy, change, match):
    path = data_copy / "constructions.yaml"
    raw = yaml.safe_load(path.read_text())
    change(raw)
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match=match):
        load_dictionary(data_dir=data_copy)


def test_missing_catalogue_is_compatible_with_existing_custom_data(data_copy):
    (data_copy / "constructions.yaml").unlink()
    tr = Translator(load_dictionary(data_dir=data_copy))
    assert bulldust("HUNGRY", translator=tr)["outcome"] == "no-compatible-construction"


def test_constructed_garnish_is_removable_and_valid_under_existing_changes_contract(dictionary):
    import jsonschema
    from aussiefy.changes import SCHEMA
    # An ordinary Entry supplies the stem, but no prewritten garnish can win this controlled placement.
    tr = Translator(replace(dictionary, entries={k: e for k, e in dictionary.entries.items() if e.type != "garnish"}))
    config = {"garnish": ["opener"], "profile": {"garnish": {"opener": 1}, "max_garnish": {"opener": 1},
              "swearing": {"exclaim": 1}, "phonetic": 0}}
    cs = translate_changes("The river is flowing through the valley.", translator=tr, vulgarity=2, seed=2,
                           embellishment=2, document_config=config)
    assert any(record.construction for record in cs.result.garnish)
    jsonschema.validate(cs.to_dict(), json.loads(SCHEMA.read_text()))
    item = next(change for change in cs.changes if change.get("placement") == "opener")
    assert item["entry_id"] is None and item["alternatives"] == []
    assert "removed" in item and item["id"] not in {row["id"] for row in cs.withheld}
    a, b = item["removed"]["out_span"]
    removed = cs.text[:a] + item["removed"]["rendered"] + cs.text[b:]
    assert removed == "The river is flowing through the valley."
    assert item["masks"]


def test_constructor_has_no_source_text_for_auto_detection(translator):
    for concept in (None, "HUNGRY"):
        with pytest.raises(UserError, match="auto"):
            bulldust(concept, document_type="auto", translator=translator)


def test_known_riff_and_imagery_forms_are_collisions(dictionary):
    from aussiefy.schema import Imagery, Riff

    tr = _toy(dictionary)
    form = "left0 then right0"
    entry = Entry("fixture-holder", "holder", ("HUNGRY",), "adj", riffs=(Riff(form),))
    imagery = Imagery("fixture-image", form, ("HUNGRY",), "comparison")
    for overrides in ({"entries": {**dictionary.entries, entry.id: entry}}, {"imagery": (*dictionary.imagery, imagery)}):
        d = replace(tr.dictionary, **overrides)
        assert not generate(d, tr.effective(vulgarity=0), setting(tr)).candidates


def test_zero_weights_and_entry_manual_gates_are_respected(translator):
    d = translator.dictionary
    for override in ({"weight": 0}, {"status": "gate"}, {"status": "omit"}, {"region": ("qld",)}):
        entry = replace(d.entries["bugger-me-sideways"], **override)
        tr = Translator(replace(d, entries={**d.entries, entry.id: entry}))
        args = dict(family="sideways-with-implement", parts={"stem": "bugger-sideways"}, vulgarity=2,
                    regions=["vic"], translator=tr)
        assert not bulldust(**args)["results"]
    entry = replace(d.entries["bugger-me-sideways"], status="gate")
    tr = Translator(replace(d, entries={**d.entries, entry.id: entry}))
    assert bulldust(family="sideways-with-implement", parts={"stem": "bugger-sideways"}, vulgarity=2,
                    unlock=["all"], translator=tr)["results"]


def test_exaggeration_and_solemn_permissions_are_independent(translator):
    assert not bulldust("HUNGRY", embellishment=0, translator=translator)["results"]
    assert bulldust("HUNGRY", embellishment=0, document_config={"riff_exaggeration": 1},
                    translator=translator)["results"]
    eff = translator.effective(vulgarity=0)
    assert generate(translator.dictionary, eff, setting(translator), concept="HUNGRY", mood="solemn").candidates
    assert not generate(translator.dictionary, eff, setting(translator, solemn_comic_terms=False),
                        concept="HUNGRY", mood="solemn").candidates


def test_cadence_prefers_reviewed_length_band_before_weight(dictionary):
    tr = _toy(dictionary)
    catalog = tr.dictionary.construction_catalog
    parts = (*catalog.ingredients, Ingredient("long", "left", "one two three four five six", weight=1000))
    tr = Translator(replace(tr.dictionary, construction_catalog=replace(catalog, ingredients=parts)))
    generated = generate(tr.dictionary, tr.effective(vulgarity=0), setting(tr))
    assert generated.candidates[0].text == "left0 then right0"
    assert generated.candidates[0].cadence > generated.candidates[1].cadence
