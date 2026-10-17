"""The changes cost benchmark (scripts/benchmark_changes.py) measures what it says; timings themselves are left to
runs on a quiet machine, not the suite."""

from scripts.benchmark_changes import BUDGET, GATED, HOSTED_TYPES, REPORTED, measure, summary, texts


def test_the_benchmark_texts_are_cut_at_a_sentence():
    cut = texts(800)
    assert len(cut) == 6 and all(0 < len(t) <= 800 and t.rstrip()[-1] in ".?!" for _, t in cut)


def test_the_gate_covers_every_setting_the_hosted_service_allows():
    types = {o.get("document_type", "general") for o in GATED.values()}
    assert types == set(HOSTED_TYPES) and not set(REPORTED) & set(GATED)


def test_the_benchmark_times_changes_against_translate():
    rows = measure(repeats=1, size=400, larger=(600,))
    assert {r["setting"] for r in rows} >= set(GATED) | set(REPORTED)
    assert all(r["translate_ms"] > 0 and r["changes_ms"] > 0 and r["ratio"] > 0 for r in rows)
    assert any(r["renderings"] for r in rows) and any("Markdown" in r["setting"] for r in rows)
    totals = summary(rows)
    assert all(s["gated"] == (k in GATED) for k, s in totals.items()) and BUDGET == 1.5
