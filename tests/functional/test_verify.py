"""verify: a translation checked against its original, as a log of problems with severity."""

from aussiefy import harness
from aussiefy.verify import SEVERITIES, counterparts

STORY = ("Goldilocks went for a walk in the forest. She found a house that belonged to three bears. "
         "She was very tired and hungry after walking for 3 hours. The porridge on the kitchen table was "
         "too hot to eat. She tried the second bowl, which was far too cold for her liking.")


def _kinds(report, severity=None):
    return [p["kind"] for p in report["problems"] if severity in (None, p["severity"])]


def test_the_engines_own_translation_verifies(translator):
    out = harness.translate(STORY, level=4, seed=1, translator=translator)["text"]
    report = harness.verify(out, original=STORY, level=4, translator=translator)
    assert report["ok"], report["problems"]
    assert set(report) >= {"ok", "counts", "problems", "metrics", "scope", "level", "vulgarity_name"}


def test_lost_facts_and_sentences_are_found(translator):
    bad = ("Goldilocks went for a walk in the bush. She was knackered and starvin' after walkin' for hours. "
           "The porridge on the kitchen table was too hot to eat. She tried the second bowl, which was far too "
           "cold for her liking.")
    report = harness.verify(bad, original=STORY, translator=translator)
    assert "number_dropped" in _kinds(report, "critical")
    assert any(p["kind"] == "unmatched" and "three bears" in p["phrase"] for p in report["problems"])
    assert not report["ok"]


def test_policy_breaches_are_major(translator):
    vulgar = STORY.replace("very tired", "fuckin' tired").replace("forest", "woods, y'all")
    report = harness.verify(vulgar, original=STORY, level=2, translator=translator)
    assert {"too_vulgar", "dialect"} <= set(_kinds(report, "major"))


def test_problems_come_worst_first_and_the_report_is_deterministic(translator):
    bad = STORY.replace("3 hours", "hours").replace("forest", "woods, y'all")
    first = harness.verify(bad, original=STORY, translator=translator)
    ranks = [SEVERITIES.index(p["severity"]) for p in first["problems"]]
    assert ranks == sorted(ranks)
    assert harness.verify(bad, original=STORY, translator=translator) == first


def test_untouched_sentences_are_coverage_not_faults(translator):
    report = harness.verify(STORY, original=STORY, level=5, translator=translator)
    assert report["metrics"]["untouched_share"] == 1.0 and report["ok"]
    assert set(_kinds(report, "info")) == {"untouched"}


def test_an_empty_translation_is_critical(translator):
    assert "empty" in _kinds(harness.verify("", original=STORY, translator=translator), "critical")


def test_markup_that_changed_is_critical(translator):
    original = "Run `make build` when you are very tired.\n\n```sh\nmake build\n```\n"
    broken = "Run `make it` when yer knackered.\n\n```sh\nmake build\n```\n"
    report = harness.verify(broken, original=original, markup="markdown", translator=translator)
    assert "markup_changed" in _kinds(report, "critical")


def test_counterparts_follow_split_and_merged_sentences():
    original = ["The wolf came to the door and knocked three times.", "The pig would not open it."]
    retold = ["Wolf rocks up.", "Knocks on the door three times, he does.", "Pig won't open it."]
    found = counterparts(original, retold)
    assert (found[0].start, found[0].end) == (0, 2) and found[0].retained > 0.5
    assert found[1].start == 2


def test_cli_verify_exits_1_on_a_major_problem(tmp_path, capsys):
    from aussiefy.cli import main

    (tmp_path / "o.txt").write_text(STORY)
    (tmp_path / "t.txt").write_text(STORY.replace("forest", "woods, y'all"))
    assert main(["verify", str(tmp_path / "t.txt"), "--original", str(tmp_path / "o.txt")]) == 1
    assert "dialect" in capsys.readouterr().out


def test_every_kind_lint_reports_has_a_severity():
    """verify's `ok` rests on the severity of each lint kind, so a new kind must be placed, not guessed."""
    import re
    from pathlib import Path

    from aussiefy.verify import SEVERITY

    pkg = Path(__file__).resolve().parents[2] / "aussiefy"
    kinds = {k for f in ("lint.py", "markup.py") for k in re.findall(r'"kind": "([a-z_]+)"', (pkg / f).read_text())}
    assert kinds and kinds <= set(SEVERITY), sorted(kinds - set(SEVERITY))
