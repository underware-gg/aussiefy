"""The changes cost benchmark (scripts/benchmark_changes.py) measures what it says; timings themselves are left to
runs on a quiet machine, not the suite."""

from scripts.benchmark_changes import SETTINGS, measure, texts


def test_the_benchmark_texts_are_cut_at_a_sentence():
    cut = texts(800)
    assert len(cut) == 6 and all(0 < len(t) <= 800 and t.rstrip()[-1] in ".?!" for _, t in cut)


def test_the_benchmark_times_changes_against_translate():
    rows = measure(repeats=1, size=400)
    assert {r["setting"] for r in rows} == set(SETTINGS) and len(rows) == 3 * 6
    assert all(r["translate_ms"] > 0 and r["changes_ms"] > 0 and r["ratio"] > 0 for r in rows)
    assert any(r["renderings"] for r in rows)
