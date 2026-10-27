"""Community data composes without rewriting core meanings or manufacturing evidence."""

import shutil

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.detect import detect, resolve_overlaps
from aussiefy.engine import Translator
from aussiefy.evidence import Credit, assess, metadata_dict
from aussiefy.errors import SchemaError
from aussiefy.match_keys import detection_match, known_match
from aussiefy.schema import parse_entry
from aussiefy.text import tokenize


def extension(tmp_path, filename="community.yaml", namespace="community", **records):
    path = tmp_path / filename
    path.write_text(yaml.safe_dump({"format": "aussiefy-dictionary-extension/v1", "namespace": namespace,
                                    **records}), encoding="utf-8")
    return path


def citation(publisher="Synthetic dictionary", **changes):
    return {"kind": "scholarly_dictionary", "publisher": publisher, "supports": ["term", "meaning"],
            "url": "https://example.org/citation", **changes}


def snapshot(people=3, **changes):
    return {"people": people, "independent": people, "places": 1, "first_date": "2026-10-01",
            "last_date": "2026-10-25", "summary_date": "2026-10-26", **changes}


def term(eid="community:zz-test", **changes):
    return {"id": eid, "form": "zz-test-form", "concept": ["HUNGRY"], "frame": "predicate_adj", **changes}


def hungry_key(dictionary):
    found = resolve_overlaps(detect(tokenize("I am hungry."), dictionary.index, concepts=dictionary.concepts,
        adjective_nouns=dictionary.adjective_nouns, degree_index=dictionary.degree_index,
        person_nouns=dictionary.person_nouns))
    return detection_match(next(d for d in found if "HUNGRY" in d.concepts)).key


def adjustment(key, factor=2.0, term_id="stoked"):
    return {"normal": [.5, 1.5], "popularity": [.25, 3.0], "records": [
        {"match": key, "term": term_id, "level": 5, "vulgarity": 1, "embellishment": 2, "factor": factor}]}


def test_namespaced_entries_and_entryless_context_meanings_load(tmp_path):
    p = extension(tmp_path, entries=[term()], concepts={"community:ZZ_TRUST": {
        "description": "A synthetic context-reading test.", "plain": "accept a claim",
        "credit": [{"name": "a contributor", "scope": "definition"}],
        "triggers": {"vp": ["trust ?={np}"]}}})
    d = load_dictionary([p])
    assert d.entries["community:zz-test"].id != "zz-test"
    assert d.extensions == ("community",)
    assert "community:ZZ_TRUST" in d.wordless_meanings
    assert d.concepts["community:ZZ_TRUST"].credit == (Credit("a contributor", "definition"),)
    readings = resolve_overlaps(detect(tokenize("She trusts the story."), d.index, concepts=d.concepts,
                                        adjective_nouns=d.adjective_nouns, degree_index=d.degree_index,
                                        person_nouns=d.person_nouns))
    found = next(r for r in readings if "community:ZZ_TRUST" in r.concepts)
    key = detection_match(found)
    assert key and known_match(key.key, d) and key.root.startswith("community:ZZ_TRUST/")
    # Existing interfaces consume qualified ids without another translation path.
    from aussiefy import get_entry, list_entries
    tr = Translator(d, lookup_embedder=None)
    assert get_entry("community:zz-test", translator=tr)["entry"]["id"] == "community:zz-test"
    assert any(r["id"] == "community:zz-test" for r in list_entries(concept="HUNGRY", translator=tr)["results"])


@pytest.mark.parametrize("marker", [True, False])
def test_extension_guard_is_refused_with_extension_concept_and_reason(tmp_path, marker):
    path = extension(tmp_path, concepts={"community:ZZ_GUARD": {
        "description": "Synthetic rejection fixture.", "no_entries": marker,
        "triggers": {"vp": ["trust ?={np}"]}}})
    with pytest.raises(SchemaError) as error:
        load_dictionary([path])
    message = str(error.value)
    assert str(path) in message and "community:ZZ_GUARD" in message
    assert "no_entries is retired; concepts are meanings" in message


@pytest.mark.parametrize("options", [{}])
def test_entryless_extension_concept_is_listed_as_waiting_not_a_guard(tmp_path, options):
    from aussiefy import list_wordless_meanings
    path = extension(tmp_path, concepts={"community:ZZ_WAITING": {
        "description": "Synthetic meaning awaiting a word.", "plain": "accept a claim",
        "examples": ["She trusts the story."], "triggers": {"vp": ["trust ?={np}"]}, **options}})
    d = load_dictionary([path])
    result = list_wordless_meanings(limit=100, translator=Translator(d, lookup_embedder=None))
    assert any(row["concept"] == "community:ZZ_WAITING" for row in result["results"])


@pytest.mark.parametrize("backend", ["none", "bundled"])
@pytest.mark.parametrize("level,vulgarity,embellishment", [(1, 0, 0), (5, 3, 2)])
def test_qualified_waiting_meaning_shares_core_lookup_readings(tmp_path, backend, level, vulgarity, embellishment):
    from aussiefy import lookup
    from aussiefy.detect import read_meanings
    cid = "community:ZZ_REPORTED_CLAIM"
    path = extension(tmp_path, concepts={cid: {
        "description": "Synthetic meaning whose object supplies context.", "plain": "accept a synthetic claim",
        "examples": ["She trusts the story.", "I trust what he says."],
        "triggers": {"vp": ["trust ?={np}"]}}})
    d = load_dictionary([path])
    tr = Translator(d, lookup_embedder=backend)
    for meaning in ("ACCEPT_AS_TRUE", cid):
        concept = d.concepts[meaning]
        for query in (concept.plain, *concept.examples):
            result = lookup(query, translator=tr, level=level, vulgarity=vulgarity,
                            embellishment=embellishment)
            assert result["outcome"] == "no_word_yet", (meaning, query, result)
            assert meaning in {row["concept"] for row in result["meanings"]}
    for query in d.concepts[cid].examples:
        reading = next(r for r in read_meanings(tokenize(query), d, fragment=True).detections if cid in r.concepts)
        match = detection_match(reading)
        assert match and known_match(match.key, d) and match.root.startswith(cid + "/")


def test_qualified_entry_uses_the_existing_translation_and_changes_pipeline(tmp_path):
    import json
    import jsonschema
    from aussiefy import translate_changes
    from aussiefy.loader import DATA_DIR
    p = extension(tmp_path, concepts={"community:ZZ_EXAMPLE": {"description": "Synthetic test meaning.",
        "triggers": {"predicate_adj": ["zzsynthetic"]}}},
        entries=[term(concept=["community:ZZ_EXAMPLE"])])
    tr = Translator(load_dictionary([p]), lookup_embedder=None)
    result = translate_changes("I am zzsynthetic.", level=5, embellishment=0, translator=tr)
    assert any(c["entry_id"] == "community:zz-test" for c in result.changes)
    assert "zz-test-form" in result.result.text
    jsonschema.validate(result.to_dict(), json.loads((DATA_DIR / "changes.schema.json").read_text()))


@pytest.mark.parametrize("records", [
    {"namespace": "Not-a-namespace"}, {"entries": [term("zz-unqualified")]},
    {"entries": [term("other:zz-test")]}, {"concepts": {"ZZ_UNQUALIFIED": {}}},
    {"concepts": {"other:ZZ_TEST": {}}}, {"patch_entries": {"stoked": {"form": "bad"}}},
    {"evidence": [{"evidence_for": "stoked", "themes": []}]},
    {"evidence": [{"evidence_for": "nonexistent"}]},
    {"entries": [term(promoted_from="community:old")]},
    {"concepts": {"community:ZZ_UNKNOWN": {"triggers": {"vp": ["trust ?={unknown}"]}}}},
])
def test_extension_boundaries_fail_with_schema_errors(tmp_path, records):
    with pytest.raises(SchemaError):
        load_dictionary([extension(tmp_path, **records)])


def test_same_form_same_meaning_requires_evidence_but_another_sense_is_separate(tmp_path, dictionary):
    original = dictionary.entries["stoked"]
    p = extension(tmp_path, entries=[term(form=original.form, concept=list(original.concept), frame=original.frame)])
    with pytest.raises(SchemaError, match="use evidence_for"):
        load_dictionary([p])
    p = extension(tmp_path, entries=[term(form=original.form, concept=["HUNGRY"], frame=original.frame)])
    d = load_dictionary([p])
    assert d.entries["stoked"] == original
    assert d.entries["community:zz-test"].concept == ("HUNGRY",)


def test_evidence_adds_sources_and_scoped_credit_without_patching_the_term(tmp_path, dictionary):
    original = dictionary.entries["stoked"]
    records = [{"evidence_for": "stoked", "sources": [citation()], "credit": [
        {"name": "term contributor", "scope": "term"}, {"name": "definition contributor", "scope": "definition"}]}]
    p = extension(tmp_path, evidence=records)
    d = load_dictionary([p])
    entry = d.entries["stoked"]
    assert entry.form == original.form and entry.concept == original.concept and entry.themes == original.themes
    added = next(s for s in entry.sources if s.publisher == "Synthetic dictionary")
    assert added.kind == "community" and added.evidence_kind == "scholarly_dictionary"
    assert entry.attestation.score >= original.attestation.score
    assert metadata_dict(entry)["credit"] == records[0]["credit"]
    assert entry.to_dict()["credit"] == records[0]["credit"]
    assert parse_entry(entry.to_dict()).credit == entry.credit
    assert dictionary.entries["stoked"] == original


def test_testimony_snapshots_replace_counts_and_curator_records_use_shared_invariants(tmp_path, dictionary):
    p = extension(tmp_path, evidence=[{"evidence_for": "stoked", "testimony": snapshot(),
                                      "spoken_use": {"date": "2026-10-26", "note": "Synthetic review."}}])
    d = load_dictionary([p])
    e = d.entries["stoked"]
    assert e.testimony.people == 3 and e.attestation.people == 3
    assert assess(e, d.evidence_weights, testimony=e.testimony).attestation == e.attestation
    q = extension(tmp_path, "other.yaml", namespace="other", evidence=[
        {"evidence_for": "stoked", "testimony": snapshot(4)}])
    with pytest.raises(SchemaError, match="consolidated"):
        load_dictionary([p, q])
    q = extension(tmp_path, "other.yaml", namespace="other", evidence=[
        {"evidence_for": "stoked", "testimony": snapshot()}])
    assert load_dictionary([p, q]).entries["stoked"].testimony.people == 3


@pytest.mark.parametrize("record", [
    {"spoken_use": {"date": "2026-10-26", "note": "No testimony."}},
    {"testimony": snapshot(people=1, independent=2)},
    {"credit": [{"name": "someone", "scope": "account"}]},
    {"sources": [citation(url="http://localhost/ref")]},
])
def test_evidence_cannot_bypass_metadata_invariants(tmp_path, record):
    with pytest.raises(SchemaError):
        load_dictionary([extension(tmp_path, entries=[term()],
            evidence=[{"evidence_for": "community:zz-test", **record}])])


def test_evidence_may_target_a_later_loaded_extension(tmp_path):
    a = extension(tmp_path, evidence=[{"evidence_for": "other:zz-test", "sources": [citation()]}])
    b = extension(tmp_path, "other.yaml", namespace="other", entries=[term("other:zz-test")])
    assert load_dictionary([a, b]).entries["other:zz-test"].sources[0].kind == "community"


def test_evidence_cannot_give_constructor_output_sources_or_add_stale_testimony(tmp_path):
    p = extension(tmp_path, entries=[term(coined_by="constructor")], evidence=[
        {"evidence_for": "community:zz-test", "sources": [citation()]}])
    with pytest.raises(SchemaError, match="constructor output"):
        load_dictionary([p])
    p = extension(tmp_path, entries=[term(testimony=snapshot())], evidence=[
        {"evidence_for": "community:zz-test", "testimony": snapshot(summary_date="2026-10-25")}])
    with pytest.raises(SchemaError, match="older"):
        load_dictionary([p])


def test_promoted_aliases_keep_credit_and_refuse_stale_exports(tmp_path):
    promoted = term("zz-promoted", promoted_from="community:zz-test", credit=[{"name": "snapshot name", "scope": "term"}],
                    sources=[citation(kind="community", basis="scholarly_dictionary")])
    core_patch = tmp_path / "promoted.yaml"
    core_patch.write_text(yaml.safe_dump([promoted]))
    d = load_dictionary([core_patch])
    assert d.promoted_entries == {"community:zz-test": "zz-promoted"}
    assert d.entries["zz-promoted"].credit[0].name == "snapshot name"
    with pytest.raises(SchemaError, match="already promoted"):
        load_dictionary([core_patch, extension(tmp_path, entries=[term()])])


@pytest.mark.parametrize("former", [True, ["community:zz-test"], {"id": "community:zz-test"}, "unqualified"])
def test_malformed_promotion_is_a_schema_error_not_an_indexing_error(tmp_path, former):
    path = tmp_path / "invalid-promotion.yaml"
    path.write_text(yaml.safe_dump([term("zz-core", promoted_from=former, credit="snapshot name")]))
    with pytest.raises(SchemaError, match="promoted_from"):
        load_dictionary([path])


@pytest.mark.parametrize("credit", [None, [], [{"name": "definition writer", "scope": "definition"}]])
def test_promotion_requires_term_contributor_credit(tmp_path, credit):
    path = tmp_path / "missing-credit.yaml"
    raw = term("zz-core", promoted_from="community:zz-test")
    if credit is not None:
        raw["credit"] = credit
    path.write_text(yaml.safe_dump([raw]))
    with pytest.raises(SchemaError, match="contributor credit"):
        load_dictionary([path])


def test_adjustments_are_exact_scoped_bounded_and_do_not_change_evidence(tmp_path, dictionary):
    key = hungry_key(dictionary)
    p = extension(tmp_path, adjustments=adjustment(key))
    d = load_dictionary([p])
    args = dict(level=5, vulgarity=1, embellishment=2)
    assert d.adjustments.factor(key, "stoked", **args) == pytest.approx(1.5)
    assert d.adjustments.factor(key, "stoked", popularity=True, **args) == pytest.approx(2)
    assert d.adjustments.factor(key + ";degree=strong", "stoked", **args) == 1
    assert d.adjustments.factor(key, "stoked", **{**args, "level": 4}) == 1
    assert d.adjustments.factor(key, "other:missing", **args) == 1
    assert d.entries == dictionary.entries
    # Loading the data does not turn tuning on ahead of slice 6's call contract.
    a, b = Translator(dictionary), Translator(d)
    assert a.translate("I am hungry.", seed=2).text == b.translate("I am hungry.", seed=2).text


@pytest.mark.parametrize("changes", [{"factor": 4}, {"factor": float("nan")}, {"factor": True},
    {"term": "missing"}, {"match": "unknown"}, {"level": True}, {"vulgarity": 4}, {"embellishment": 3}])
def test_invalid_adjustments_are_refused(tmp_path, dictionary, changes):
    raw = adjustment(hungry_key(dictionary))
    raw["records"][0].update(changes)
    with pytest.raises(SchemaError):
        load_dictionary([extension(tmp_path, adjustments=raw)])


@pytest.mark.parametrize("change", ["invalid-band", "inverted-bands", "duplicate", "unknown-root"])
def test_invalid_adjustment_bundles_are_refused(tmp_path, dictionary, change):
    raw = adjustment(hungry_key(dictionary))
    if change == "invalid-band":
        raw["normal"] = [0, 1.5]
    elif change == "inverted-bands":
        raw["popularity"] = [.75, 1.25]
    elif change == "duplicate":
        raw["records"] *= 2
    else:
        raw["records"][0]["match"] = "HUNGRY/np/" + "0" * 64
    with pytest.raises(SchemaError):
        load_dictionary([extension(tmp_path, adjustments=raw)])


def test_multiple_extensions_multiply_factors_then_apply_their_common_band(tmp_path, dictionary):
    key = hungry_key(dictionary)
    a = extension(tmp_path, adjustments=adjustment(key))
    b = extension(tmp_path, "other.yaml", namespace="other", adjustments=adjustment(key))
    for paths in ([a, b], [b, a]):
        d = load_dictionary(paths)
        assert d.adjustments.factor(key, "stoked", level=5, vulgarity=1, embellishment=2) == pytest.approx(1.5)
        assert d.adjustments.factor(key, "stoked", level=5, vulgarity=1, embellishment=2,
                                    popularity=True) == pytest.approx(3)


def test_only_matching_extensions_contribute_their_band(tmp_path, dictionary):
    key = hungry_key(dictionary)
    a = extension(tmp_path, adjustments=adjustment(key))
    restrictive = adjustment(key)
    restrictive.update(normal=[.75, 1.25], popularity=[.5, 2])
    b = extension(tmp_path, "other.yaml", namespace="other", adjustments=restrictive)
    d = load_dictionary([a, b])
    assert d.adjustments.factor(key, "stoked", level=5, vulgarity=1, embellishment=2) == pytest.approx(1.25)
    restrictive["records"][0]["level"] = 4
    b = extension(tmp_path, "other.yaml", namespace="other", adjustments=restrictive)
    d = load_dictionary([a, b])
    assert d.adjustments.factor(key, "stoked", level=5, vulgarity=1, embellishment=2) == pytest.approx(1.5)


def test_identity_follows_content_and_order_not_paths_or_modified_times(tmp_path, dictionary, data_copy):
    p = extension(tmp_path, entries=[term()])
    relocated = tmp_path / "relocated.yaml"
    shutil.copyfile(p, relocated)
    a, b = load_dictionary([p]), load_dictionary([relocated])
    assert a.identity == b.identity != dictionary.identity
    assert load_dictionary(data_dir=data_copy).identity == dictionary.identity
    identity = a.identity
    raw = yaml.safe_load(p.read_text())
    raw["entries"][0]["notes"] = "A data change, not a new version."
    p.write_text(yaml.safe_dump(raw))
    assert load_dictionary([p]).identity != identity
    other = extension(tmp_path, "other.yaml", namespace="other", entries=[term("other:zz-test")])
    assert load_dictionary([p, other]).identity != load_dictionary([other, p]).identity
    (data_copy / "profiles.yaml").write_text((data_copy / "profiles.yaml").read_text() + "\n# changed\n")
    assert load_dictionary(data_dir=data_copy).identity != dictionary.identity
    from aussiefy.loader import DATA_DIR
    assert load_dictionary([DATA_DIR / "entries"], include_builtin=False).identity != dictionary.identity
