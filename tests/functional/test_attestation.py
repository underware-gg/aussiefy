"""Evidence is a derived judgement, independent of selection policy and the live store."""

from dataclasses import replace

import pytest
import yaml

from aussiefy import load_dictionary
from aussiefy.evidence import (CuratorRecord, Source, TermMetadata, Testimony as EvidenceTestimony, assess, parse_metadata,
                              parse_weights)
from aussiefy.schema import SchemaError, parse_entry


def source(kind="scholarly_dictionary", publisher="Dictionary A", **kwargs):
    return Source(kind, publisher, ("term", "meaning"), url="https://example.org/term", **kwargs)


def summary(people=1, independent=None, places=1):
    return EvidenceTestimony(people, people if independent is None else independent, places,
                     "2026-10-19", "2026-10-19", "2026-10-20")


def test_hand_checked_score_goldens(dictionary):
    w = dictionary.evidence_weights
    a = source()
    b = source(publisher="Dictionary B")
    crowd = source("crowd_dictionary", "Wiktionary")
    for sources, score, bars, label in [
        ((), 0, 0, "unverified"), ((a,), 8, 4, "attested"),
        ((a, b), 10, 5, "attested"), ((a, crowd), 10, 5, "attested"),
        ((crowd,), 2, 1, "unverified"),
    ]:
        got = assess(TermMetadata(sources=sources), w)
        assert (got.attestation.score, got.attestation.bars, got.evidence) == (score, bars, label)


def test_copies_and_publisher_aliases_do_not_multiply_evidence(dictionary):
    a = source(publisher="  Dictionary A ")
    copy = replace(a, publisher="dictionary a", url="https://example.org/copy")
    one = assess(TermMetadata(sources=(a,)), dictionary.evidence_weights)
    many = assess(TermMetadata(sources=(a, copy, a)), dictionary.evidence_weights)
    assert one == many


def test_each_further_source_of_one_kind_adds_less(dictionary):
    values = [assess(TermMetadata(sources=tuple(source("crowd_dictionary", str(i)) for i in range(n))),
                     dictionary.evidence_weights).attestation.score for n in range(4)]
    assert [round(values[i + 1] - values[i], 4) for i in range(3)] == [2, 1.3, .845]


def test_component_citations_do_not_attest_the_whole_expression(dictionary):
    component = replace(source(), supports=(), note="Supports a component only.")
    assert assess(TermMetadata(sources=(component,)), dictionary.evidence_weights).attestation.score == 0


def test_testimony_cap_spoken_use_and_geographic_spread(dictionary):
    w = dictionary.evidence_weights
    broad = summary(10000, places=1000)
    term = TermMetadata(testimony=broad)
    capped = assess(term, w)
    assert (capped.attestation.score, capped.attestation.bars, capped.evidence) == (6, 3, "unverified")
    spoken = replace(term, spoken_use=CuratorRecord("2026-10-20", "Reviewed broad spoken use."))
    assert assess(spoken, w).evidence == "attested"
    near = assess(TermMetadata(testimony=summary(10, places=1)), w)
    spread = assess(TermMetadata(testimony=summary(10, places=5)), w)
    assert spread.attestation.score > near.attestation.score


def test_live_summary_replaces_export_and_changes_agent_label(dictionary):
    from aussiefy.evidence import Search
    term = TermMetadata(produced_by="agent", searched=Search("2026-10-20", "nothing_found"),
                        testimony=summary(1, independent=0))
    original = assess(term, dictionary.evidence_weights)
    live = assess(term, dictionary.evidence_weights, testimony=summary(2, independent=1))
    assert original.evidence == "bulldust" and live.evidence == "unverified"
    assert live.attestation.score > original.attestation.score
    assert live.attestation.people == 2
    assert term.testimony.people == 1
    empty = parse_metadata({"testimony": {"people": 0, "independent": 0, "places": 0,
                                         "summary_date": "2026-10-20"}}, "live")["testimony"]
    assert assess(term, dictionary.evidence_weights, testimony=empty).attestation.people == 0


def test_deliberate_coinage_needs_recorded_caught_on_even_with_sources(dictionary):
    term = TermMetadata(coined_by="person", sources=(source(), source(publisher="Another work")))
    assert assess(term, dictionary.evidence_weights).evidence == "bulldust"
    adopted = replace(term, caught_on=CuratorRecord("2026-10-20", "Independent published use."))
    assert assess(adopted, dictionary.evidence_weights).evidence == "attested"


def test_community_attribution_cannot_lift_testimony_cap(dictionary):
    testimony = Source("community", "Community export", ("term",), basis="testimony")
    term = TermMetadata(sources=(testimony,), testimony=summary(1000, places=20))
    got = assess(term, dictionary.evidence_weights)
    assert (got.evidence, got.attestation.bars) == ("unverified", 3)


def test_first_attested_uses_supported_citation_date_not_publication_timestamp(dictionary):
    dated = replace(source(), cited_date="1890s", supports=("term", "date"))
    later = replace(source(publisher="Other"), cited_date="1914–1918", supports=("term", "date"))
    irrelevant = replace(source(), cited_date="1738", supports=("term",))
    term = TermMetadata(sources=(later, irrelevant, dated), dated_by_curator="1800")
    assert assess(term, dictionary.evidence_weights).first_attested == "1890s"
    assert assess(replace(term, sources=(irrelevant,)), dictionary.evidence_weights).first_attested == "1800"


@pytest.mark.parametrize("raw, message", [
    ({"sources": ["https://example.test"]}, "structured|object"),
    ({"sources": [{"kind": "crowd_dictionary", "publisher": "X", "supports": ["date"], "url": "https://example.org"}]}, "cited_date"),
    ({"coined_by": "constructor", "sources": [source().to_dict()]}, "constructor"),
    ({"spoken_use": {"date": "2026-10-20", "note": "Confirmed"}}, "testimony"),
    ({"caught_on": {"date": "2026-10-20", "note": "Confirmed"}}, "independent testimony"),
    ({"sources": [Source("testimony", "Community", ("term",)).to_dict()]}, "testimony summary"),
    ({"origin": "familiar"}, "origin"),
    ({"reads_as": "imported"}, "reads_as"),
    ({"australian_use": False}, "australian_use"),
    ({"themes": [{"name": "drinking", "tier": True}]}, "tier"),
    ({"doubtful_definition": 1}, "true or false"),
    ({"misreadable": "yes"}, "true or false"),
    ({"searched": {"date": "2026-02-30", "outcome": "found"}}, "ISO date"),
    ({"searched": {"date": "2026-10-20", "outcome": []}}, "outcome"),
    ({"searched": {"date": "2026-10-20", "outcome": {}}}, "outcome"),
    ({"testimony": {"people": 1, "independent": 2, "places": 1}}, "exceed"),
    ({"sources": [replace(source(), url="https://[broken").to_dict()]}, "malformed source URL"),
])
def test_metadata_boundary_invariants(raw, message):
    with pytest.raises(SchemaError, match=message):
        parse_metadata(raw, "test")


def test_loader_rejects_forged_derived_label_and_retired_imagery_origin(data_copy):
    path = data_copy / "imagery.yaml"
    raw = yaml.safe_load(path.read_text())
    raw[0]["evidence"] = "attested"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match="unknown fields"):
        load_dictionary(data_dir=data_copy)
    raw[0].pop("evidence")
    raw[0]["origin"] = "original"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match="origin"):
        load_dictionary(data_dir=data_copy)


def test_stored_fields_roundtrip_but_derived_fields_are_not_written(dictionary):
    for entry in dictionary.entries.values():
        raw = entry.to_dict()
        assert not {"evidence", "attestation", "first_attested"}.intersection(raw)
        assert parse_entry(raw).sources == entry.sources


def test_bad_weights_fail_instead_of_poisoning_selection(dictionary):
    from dataclasses import asdict
    raw = asdict(dictionary.evidence_weights)
    raw["source_weights"] = dict(raw["source_weights"])
    for key, value in (("bar_width", 0), ("diminishing", 1), ("general_pick_factor", float("nan"))):
        with pytest.raises(SchemaError):
            parse_weights({**raw, key: value})


def test_general_is_a_weight_not_an_eligibility_gate(translator):
    from aussiefy.detect import Detection
    from aussiefy.schema import Entry
    from aussiefy.select import candidates, weighted_pick
    det = Detection(start=0, end=1, concepts=("GOOD",), frame="adj", intensity=3, method="trigger", pattern="good")
    entries = [Entry("aussie-test", "ripper", ("GOOD",), "adj"),
               Entry("general-test", "excellent", ("GOOD",), "adj", reads_as="general")]
    cands, rejected = candidates(det, entries, translator.effective(level=5, vulgarity=0), {}, set(), frozenset())
    assert not rejected and len(cands) == 2
    selected = [weighted_pick(cands, i / 1000).entry.id for i in range(1000)]
    assert 0 < selected.count("general-test") < selected.count("aussie-test")


def test_score_increase_within_a_bar_increases_weight(translator):
    from aussiefy.detect import Detection
    from aussiefy.evidence import Attestation
    from aussiefy.schema import Entry
    from aussiefy.select import candidates
    det = Detection(start=0, end=1, concepts=("GOOD",), frame="adj", intensity=3, method="trigger", pattern="good")
    low = Entry("low-score", "ripper", ("GOOD",), "adj", attestation=Attestation(score=2.1, bars=1))
    high = replace(low, id="high-score", attestation=Attestation(score=3.9, bars=1))
    cands, _ = candidates(det, [low, high], translator.effective(level=5, vulgarity=0), {}, set(), frozenset())
    weights = {c.entry.id: c.weight for c in cands}
    assert weights["high-score"] > weights["low-score"]


def test_riff_register_is_parsed_and_validated(data_copy):
    path = data_copy / "riffs.yaml"
    path.write_text("wheelie-bin:\n- text: tipped over in the gutter\n  register: dated\n")
    assert load_dictionary(data_dir=data_copy).entries["wheelie-bin"].riffs[0].register == "dated"
    path.write_text(path.read_text().replace("dated", "antique"))
    with pytest.raises(SchemaError, match="register"):
        load_dictionary(data_dir=data_copy)


def test_shared_metadata_gates_riffs_and_imagery_without_gating_bulldust(dictionary):
    from aussiefy.evidence import metadata_rejections
    from aussiefy.schema import Entry, Riff
    for fields in ({"reads_as": "american"}, {"australian_use": "uncommon"}, {"doubtful_definition": True},
                   {"misreadable": True}):
        riff = Riff("a creative comparison", **fields)
        entry = Entry("riff-test", "ripper", ("GOOD",), "adj", riffs=(riff,))
        assert metadata_rejections(riff) and not entry.riffs_within(3, frozenset(dictionary.theme_defaults[3]), registers=("current",))
    assert not metadata_rejections(TermMetadata(coined_by="agent", evidence="bulldust"))
    assert next(i for i in dictionary.imagery if i.id == "chew-nails").reads_as == "american"


def test_real_reviewed_anchor_scores(dictionary):
    for eid, first in [("gday", "1880s"), ("arvo", "1920s"), ("bulldust", "1920s")]:
        entry = dictionary.entries[eid]
        assert (entry.attestation.score, entry.attestation.bars, entry.evidence) == (10, 5, "attested")
        assert entry.first_attested == first


def test_garnish_shares_metadata_weights_and_preserves_swear_tier(translator):
    from aussiefy.evidence import Attestation
    from aussiefy.garnish import garnish_weights, tier_match
    from aussiefy.schema import Entry
    australian = Entry("aussie-test", "crikey", (), "interjection", type="garnish", placement="opener")
    general = replace(australian, id="general-test", form="well", reads_as="general")
    sourced = replace(australian, id="sourced-test", attestation=Attestation(score=1.0))
    eff = translator.effective(level=5, vulgarity=2)
    weights = garnish_weights([australian, general, sourced], eff, False)
    assert weights[1] == weights[0] * eff.general_pick_factor
    assert weights[2] > weights[0]
    sweary = replace(sourced, vulgarity=1)
    assert garnish_weights([sweary], eff, True)[0] == eff.metadata_weight(sweary) * tier_match(1, 2)


@pytest.mark.parametrize("raw", [
    {"testimony": {"people": 1, "independent": 0, "places": 1, "first_date": "2026-10-20",
                   "last_date": "2026-10-20", "summary_date": "2026-10-20"}},
    {"sources": [{"kind": "media", "publisher": "Example", "url": "https://example.org/term",
                  "supports": ["australian_use"]}]},
])
def test_caught_on_requires_independent_use_of_the_term(raw):
    with pytest.raises(SchemaError, match="caught_on"):
        parse_metadata({**raw, "coined_by": "person", "caught_on": {"date": "2026-10-20", "note": "Review"}}, "fixture")


@pytest.mark.parametrize("kind", ["entry", "riff"])
@pytest.mark.parametrize("field", ["evidence", "attestation", "first_attested"])
def test_stored_evidence_labels_are_rejected_everywhere(data_copy, kind, field):
    path = data_copy / ("entries/lexical.yaml" if kind == "entry" else "riffs.yaml")
    raw = yaml.safe_load(path.read_text())
    if kind == "entry":
        raw[0][field] = "attested"
    else:
        raw["wheelie-bin"] = [{"text": "some image", field: "attested"}]
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(SchemaError, match=field if kind == "entry" else f"derived fields.*{field}"):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize("reading", ["unknown", "aboriginal"])
def test_reads_as_does_not_use_origin_or_uncertainty_categories(reading):
    with pytest.raises(SchemaError, match="reads_as"):
        parse_metadata({"reads_as": reading}, "fixture")


def test_general_word_remains_an_editor_alternative(translator):
    from aussiefy import translate_changes
    found = False
    for seed in range(20):
        result = translate_changes("The tickets were expensive.", translator=translator, seed=seed,
                                   vulgarity=0, embellishment=0)
        for change in result.changes:
            found |= any(option["entry_id"] == "dear-expensive" for option in change.get("alternatives", []))
    assert found


def test_colour_picker_applies_metadata_without_excluding_general(translator):
    from aussiefy.garnish import pick_riff
    from aussiefy.policy import roll
    from aussiefy.schema import Riff
    general = Riff("a familiar comparison", reads_as="general")
    aussie = Riff("an Aussie comparison")
    eff = translator.effective(level=5, vulgarity=0)
    # Put the general option first so the position preference cannot hide its metadata penalty.
    items = (general, aussie)
    rolls = [roll(seed, "metadata-picker") for seed in range(1000)]
    weighted = [pick_riff(items, "light", r, [eff.metadata_weight(x) for x in items]) for r in rolls]
    neutral = [pick_riff(items, "light", r, [1, 1]) for r in rolls]
    assert 0 < weighted.count(general) < neutral.count(general)
    assert weighted == [pick_riff(items, "light", r, [eff.metadata_weight(x) for x in items]) for r in rolls]
