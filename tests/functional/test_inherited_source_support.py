"""Real source records retain their sense limits and count works, rather than mirrors."""

from aussiefy.evidence import assess


def test_same_dennis_work_on_two_hosts_is_one_witness(dictionary):
    entry = dictionary.entries["know-a-bloke"]
    supported = [source for source in entry.sources if "meaning" in source.supports]
    assert len({source.url for source in supported}) >= 2
    assert len({source.publisher for source in supported}) == 1
    assert (entry.attestation.score, dict(entry.attestation.counts)) == (4, {"literature": 1})


def test_lexicographic_article_and_dictionary_have_separate_source_kinds(dictionary):
    entry = dictionary.entries["a-goss"]
    macquarie = next(source for source in entry.sources
                     if source.publisher == "Macquarie Dictionary" and "meaning" in source.supports)
    collins = next(source for source in entry.sources if source.publisher == "Collins Dictionary")
    assert macquarie.kind == "media" and collins.kind == "scholarly_dictionary"
    assert "meaning" in macquarie.supports and "meaning" in collins.supports
    assert entry.attestation.score == 9


def test_partial_constructions_remain_references_without_score(dictionary):
    for eid in ("fruit-and-veg-section", "fruit-and-veg-aisle", "fruit-and-veg-department", "a-brass-razoo"):
        entry = dictionary.entries[eid]
        assert entry.sources
        assert all(not source.supports for source in entry.sources)
        assert assess(entry, dictionary.evidence_weights).attestation.score == 0


def test_broad_reported_period_does_not_become_an_invented_exact_date(dictionary):
    entry = dictionary.entries["sheila"]
    source = next(source for source in entry.sources if source.publisher == "Australian National Dictionary Centre")
    assert "late 19th century" in source.note
    assert "date" not in source.supports and source.cited_date is None
    assert entry.first_attested is None


def test_source_research_does_not_lift_existing_usage_holds(dictionary):
    entry = dictionary.entries["cruisin-for-a-bruisin"]
    assert entry.australian_use == "uncommon"
    assert entry.evidence == "unverified"
