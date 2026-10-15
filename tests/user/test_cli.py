"""The CLI through main(): every subcommand's exit code and one observable fact about its output."""

import json

import pytest

from aussiefy.cli import FELL_BACK, main

EXTRA = "- {id: zzqwop, form: zzqwop, concept: [TIRED], frame: predicate_adj, gloss: Utterly tired (a test word).}\n"


@pytest.fixture
def extra(tmp_path):
    path = tmp_path / "extra.yaml"
    path.write_text(EXTRA)
    return str(path)


def test_default_command_is_translate(capsys):
    assert main(["I'm extremely busy.", "-l", "5", "-s", "1", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["level"] == 5 and data["decisions"]["substitutions"]


def test_explain_goes_to_stderr(capsys):
    main(["translate", "Are you crazy?", "-l", "4", "--explain"])
    out, err = capsys.readouterr()
    assert out.strip() and "substitutions:" in err and "rejected:" in err


def test_random_seed_is_printed_and_accepted_wherever_seeds_are(capsys):
    assert main(["translate", "I'm tired.", "-s", "random"]) == 0
    assert capsys.readouterr().err.startswith("seed: ")
    assert main(["plan", "I'm tired.", "-s", "random"]) == 0


def test_text_can_be_a_file(tmp_path, capsys):
    f = tmp_path / "t.txt"
    f.write_text("I'm extremely busy.")
    assert main(["plan", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["draft"]


def test_lookup(capsys):
    assert main(["lookup", "very", "tired"]) == 0
    assert "knackered" in capsys.readouterr().out
    assert main(["lookup", "zzqqxx"]) == 1


def test_lookup_shows_riffs(capsys):
    assert main(["lookup", "wheelie", "bin"]) == 0
    assert "riff (" in capsys.readouterr().out


def test_lint_exit_codes(capsys):
    assert main(["lint", "G'day mate, she's flat out like a lizard drinking."]) == 0
    assert main(["lint", "Y'all know the color is wrong."]) == 1
    assert "dialect" in capsys.readouterr().out


def test_dials_by_name(capsys):
    assert main(["guide", "-l", "swaggie", "--vulgarity", "Uncle Bob", "--json"]) == 0
    g = json.loads(capsys.readouterr().out)
    assert (g["level"], g["level_name"], g["vulgarity"], g["vulgarity_name"]) == (5, "swaggie", 2, "uncle-bob")
    with pytest.raises(SystemExit) as exc:
        main(["guide", "-l", "drongo"])
    assert exc.value.code == 2 and "1 (tourist), 2 (blow-in)" in capsys.readouterr().err


def test_guide(capsys):
    assert main(["guide", "-l", "2"]) == 0
    assert capsys.readouterr().out.startswith("Level 2 (blow-in):")


def test_plan_is_json(capsys):
    assert main(["plan", "She was tired and very hungry."]) == 0
    assert {"draft", "planned", "openings"} <= set(json.loads(capsys.readouterr().out))


def test_every_toolkit_command_reads_extra_dictionaries(extra, capsys):
    """--dict reaches the dictionary every command reads (lookup, lint, guide, plan and gaps used to ignore it)."""
    assert main(["lookup", "zzqwop", "--dict", extra]) == 0
    assert main(["show", "zzqwop", "--dict", extra]) == 0
    assert main(["lookup", "zzqwop"]) == 1
    capsys.readouterr()
    assert main(["validate", "--dict", extra]) == 0
    assert "ok: " in capsys.readouterr().out


def test_validate_and_show(capsys):
    assert main(["validate"]) == 0
    assert capsys.readouterr().out.startswith("ok: ")
    assert main(["show", "lizard"]) == 0
    assert "flat out like a lizard drinking" in capsys.readouterr().out
    assert main(["show", "zzqqxx"]) == 1


def test_bad_dictionary_reports_error(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- {id: oops, form: x, concept: [NOPE], frame: np}\n")
    assert main(["validate", "--dict", str(bad)]) == 2
    assert "unknown concept 'NOPE'" in capsys.readouterr().err


def test_compare(capsys):
    assert main(["compare", "tests/corpus/reference/goldilocks.txt", "tests/corpus/targets/goldilocks_level5.txt",
                 "--seeds", "2"]) == 0
    assert "vocabulary overlap:" in capsys.readouterr().out


def test_gaps(tmp_path, capsys):
    text = tmp_path / "t.txt"
    text.write_text("The serene lake glistened under the moon. The serene lake was calm.")
    assert main(["gaps", str(text), "--embedder", "ngram", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["gaps"]
    assert main(["gaps", str(text), "--draft", "nope=x"]) == 2


def test_embedder_status(capsys):
    assert main(["embedder", "status"]) == 0
    assert "bundled" in json.dumps(json.loads(capsys.readouterr().out))


def test_llm_modes_signal_a_fallback(capsys, monkeypatch):
    """Without the SDK (or a key) yarn keeps the draft, says so on stderr, and exits FELL_BACK, not 0."""
    import builtins

    real = builtins.__import__

    def no_anthropic(name, *a, **k):
        if name == "anthropic":
            raise ModuleNotFoundError("No module named 'anthropic'")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_anthropic)
    assert main(["yarn", "She was tired.", "--json"]) == FELL_BACK
    assert json.loads(capsys.readouterr().out)["status"].startswith("kept draft")
    assert main(["translate", "Our ancestors conceived this proposition with considerable deliberation.",
                 "--rewrite", "hard"]) == FELL_BACK
    assert "[rewrite]" in capsys.readouterr().err


def test_dev_fragments(tmp_path, capsys):
    out = tmp_path / "f.yaml"
    assert main(["dev", "fragments", "-o", str(out)]) == 0
    assert out.exists()


def test_dev_scrape_refuses_reference_only_sources(capsys, tmp_path):
    rc = main(["dev", "scrape", "https://www.macquariedictionary.com.au/australian-word-map/",
               "-o", str(tmp_path / "s.yaml")])
    assert rc == 3
    assert "reference-only source" in capsys.readouterr().err
    assert not (tmp_path / "s.yaml").exists()


def test_dev_round_dry_run_reproduces_the_classics_round(capsys):
    """Re-planning a shipped round adds nothing new: its entries are all there and its triggers are in place.
    The counts are the classics round's (210 verdict entries + the-good-oil, 30 gated, 139 concepts): they change
    only if the round's own files do."""
    assert main(["dev", "round", "research/classics-2026-10-11"]) == 0
    assert capsys.readouterr().out.startswith("211 entries (30 gated), 139 new concepts, 0 triggers")


def test_every_command_the_package_names_exists():
    """Messages and docstrings that say `aussiefy <command>` name a real one (a stale name gets translated)."""
    import re
    from pathlib import Path

    from aussiefy.cli import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction").choices
    named = set()
    for path in Path("aussiefy").rglob("*.py"):
        named |= set(re.findall(r"(?:`|run: |^ +)aussiefy ([a-z]+)\b", path.read_text(encoding="utf-8"), re.M))
    named |= set(re.findall(r"`aussiefy ([a-z]+)\b", Path("README.md").read_text(encoding="utf-8")))
    stale = named - set(sub)
    assert not stale, stale


def test_yarn_tools_runs_the_loop_by_hand(tmp_path, capsys):
    from aussiefy.cli import main

    src = tmp_path / "story.txt"
    src.write_text("She was very tired. She went to the shop.")
    assert main(["yarn-tools", "brief", str(src), "-l", "3"]) == 0
    assert "STYLE GUIDE" in capsys.readouterr().out
    assert main(["yarn-tools", "lookup", str(src), "very tired"]) == 0
    capsys.readouterr()
    bad = tmp_path / "bad.txt"
    bad.write_text("Y'all, she was tired.")
    assert main(["yarn-tools", "submit", str(src), str(bad), "-l", "3"]) == 1
    capsys.readouterr()
    from aussiefy.yarn import brief

    good = tmp_path / "good.txt"
    good.write_text(brief(src.read_text(), level=3).plan["draft"])
    log, out = tmp_path / "log.jsonl", tmp_path / "yarn.txt"
    assert main(["yarn-tools", "submit", str(src), str(good), "-l", "3", "-o", str(out), "--log", str(log)]) == 0
    assert out.read_text().strip() == good.read_text().strip() and len(log.read_text().splitlines()) == 1
