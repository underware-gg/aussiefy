"""The CLI's edges: a file, setting or argument the user got wrong is exit 2 with a message that names it, never a
traceback (exit 1 means a negative answer); and the notices that keep a slip from passing silently."""

import json
import subprocess

import pytest

from aussiefy.cli import main

ORIGINAL = "tests/corpus/reference/goldilocks.txt"
TARGET = "tests/corpus/targets/goldilocks_level5.txt"


@pytest.mark.parametrize("argv, named", [
    (["lint", "drfat.txt"], "drfat.txt"),                        # a mistyped file isn't linted as the text "drfat.txt"
    (["translate", "drafts/story"], "drafts/story"),
    (["lint", "G'day.", "--original", "nope.txt"], "--original: no such file: nope.txt"),
    (["G'day.", "--dict", "nope.yaml"], "--dict: no such file or directory: nope.yaml"),
    (["compare", "nope.txt", TARGET], "nope.txt"),
    (["gaps", "nope.txt"], "nope.txt"),
    (["gaps", ORIGINAL, "--draft", "goldilocks=nope.txt"], "--draft goldilocks: no such file: nope.txt"),
    (["dev", "round", "research/no-such-round"], "no round.yaml in research/no-such-round"),
    (["dev", "tag", "nope.yaml"], "no such staging file: nope.yaml"),
    (["dev", "review", "nope.yaml"], "nope.yaml"),
    (["dev", "review", "tests/corpus/golden.yaml", "--data-dir", "nope"], "--data-dir: no such directory: nope"),
    (["dev", "harvest", "nope.txt", ORIGINAL], "nope.txt"),
    (["dev", "scrape", "listcle.html", "--source-url", "https://example.com/x"], "no such file: listcle.html"),
    (["embedder", "install", "--dry-run", "--from", "nope"], "--from: no such model folder: nope"),
])
def test_a_path_that_names_nothing_is_a_usage_error(argv, named, capsys):
    assert main(argv) == 2
    assert named in capsys.readouterr().err


def test_text_with_a_slash_or_a_suffix_is_still_text_when_it_has_spaces(capsys):
    assert main(["lint", "it's 50/50 whether she'll be right"]) == 0
    assert main(["plan", "notes.txt"]) == 2      # one word that looks like a file and isn't one


def test_a_policy_value_outside_its_closed_set_is_a_usage_error(capsys):
    assert main(["translate", "G'day.", "--registers", "bogus"]) == 2
    assert "unknown register(s) 'bogus'" in capsys.readouterr().err


def test_policy_warnings_go_to_stderr_and_into_the_json(capsys):
    assert main(["translate", "She was tired.", "--region", "atlantis"]) == 0
    assert "warning: no entry is tagged with region 'atlantis'" in capsys.readouterr().err
    assert main(["translate", "She was tired.", "--region", "atlantis", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["policy_warnings"] and {"level_name", "vulgarity_name", "variety", "difficult_sentences"} <= set(data)


def test_compare_and_gaps_take_the_level_by_name(tmp_path, capsys):
    assert main(["compare", ORIGINAL, TARGET, "--seeds", "1", "-l", "local"]) == 0
    assert "at level 3" in capsys.readouterr().out
    text = tmp_path / "t.txt"
    text.write_text("The serene lake glistened under the moon.")
    assert main(["gaps", str(text), "-l", "blow-in", "--embedder", "ngram", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["level"] == 2


def test_plan_accepts_json(capsys):
    assert main(["plan", "She was tired.", "--json"]) == 0
    assert "draft" in json.loads(capsys.readouterr().out)


def test_a_bad_seed_says_what_a_seed_is(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["translate", "G'day.", "-s", "abc"])
    assert exc.value.code == 2 and "seed must be a whole number or 'random', not 'abc'" in capsys.readouterr().err


def test_show_says_when_nothing_matches(capsys):
    assert main(["show", "zzqqxx"]) == 1
    assert "no entry matches 'zzqqxx'" in capsys.readouterr().err


def test_lint_counts_warnings_when_there_are_no_issues(capsys):
    assert main(["lint", "G'day mate, bloody bloody bloody bloody hell."]) == 0
    assert capsys.readouterr().out.rstrip().endswith("ok (2 warning(s))")


def test_lint_does_not_suggest_what_an_issue_already_fixes(capsys):
    assert main(["lint", "He walked down the sidewalk.", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert [i["phrase"] for i in out["issues"]] == ["sidewalk"]
    assert not [s for s in out["suggestions"] if s["text"] == "sidewalk"]


def test_a_mistyped_command_is_translated_with_a_notice(capsys):
    assert main(["lnit", "G'day."]) == 0
    out, err = capsys.readouterr()
    assert out.strip() and "did you mean 'lint'?" in err


def test_reading_stdin_from_a_terminal_says_so(monkeypatch, capsys):
    import io

    class Terminal(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", Terminal("She was tired.\n"))
    assert main([]) == 0
    out, err = capsys.readouterr()
    assert out.strip() and "reading text from stdin" in err


def test_a_config_of_the_wrong_shape_is_exit_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text('{"embedder": "tiny"}')
    assert main(["embedder", "status"]) == 2
    assert "config.json should be a JSON object" in capsys.readouterr().err
    (tmp_path / "config.json").write_text("{not json")
    assert main(["embedder", "status"]) == 2
    assert "is not valid JSON" in capsys.readouterr().err


def test_a_failed_embedder_install_is_exit_2(monkeypatch, capsys):
    from aussiefy import models

    def fail(**kwargs):
        raise subprocess.CalledProcessError(1, ["pip", "install", "torch"])

    monkeypatch.setattr(models, "install", fail)
    assert main(["embedder", "install"]) == 2
    assert "install step failed (pip install torch)" in capsys.readouterr().err


def test_dev_tag_without_the_sdk_is_exit_2(monkeypatch, tmp_path, capsys):
    import builtins

    staged = tmp_path / "s.yaml"
    staged.write_text("- {id: zzword, form: zzword}\n")
    real = builtins.__import__

    def no_anthropic(name, *a, **k):
        if name == "anthropic":
            raise ModuleNotFoundError("No module named 'anthropic'")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_anthropic)
    assert main(["dev", "tag", str(staged), "-o", str(tmp_path / "t.yaml")]) == 2
    assert "anthropic SDK isn't installed" in capsys.readouterr().err
    assert not (tmp_path / "t.yaml").exists()


def test_yarn_no_cache_reaches_yarn(monkeypatch, capsys):
    import importlib

    yarn = importlib.import_module("aussiefy.yarn")
    seen = {}
    real = yarn.yarn

    def spy(text, **kwargs):
        seen.update(kwargs)
        return real(text, **kwargs)

    monkeypatch.setattr(yarn, "yarn", spy)
    main(["yarn", "She was tired.", "--no-cache", "--json"])
    assert seen["cache"] is False


def test_yarn_caches_under_the_aussiefy_home(monkeypatch, tmp_path):
    from aussiefy import claude

    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path))
    assert claude.default_cache_dir("yarn") == tmp_path / "cache" / "yarn"


def test_scraping_a_saved_page_needs_its_source_url(tmp_path, capsys):
    page = "tests/fixtures/listicle_a.html"
    assert main(["dev", "scrape", page, "-o", str(tmp_path / "s.yaml")]) == 2
    assert "give the URL it was saved from" in capsys.readouterr().err
    # a saved copy of a reference-only page is refused like the page itself
    assert main(["dev", "scrape", page, "--source-url", "https://www.macquariedictionary.com.au/x",
                 "-o", str(tmp_path / "s.yaml")]) == 3
    assert "reference-only source" in capsys.readouterr().err and not (tmp_path / "s.yaml").exists()
    pytest.importorskip("bs4")
    assert main(["dev", "scrape", page, "--source-url", "https://example.com/slang", "-o", str(tmp_path / "s.yaml")]) == 0
    assert "https://example.com/slang" in (tmp_path / "s.yaml").read_text()


def test_dev_tag_makes_its_output_folder_before_tagging(monkeypatch, tmp_path):
    from aussiefy.scrape import tag

    staged = tmp_path / "s.yaml"
    staged.write_text("- {id: zzword, form: zzword}\n")
    out = tmp_path / "new" / "folder" / "t.yaml"
    seen = []
    monkeypatch.setattr(tag, "tag_all", lambda items, *a, **k: seen.append(out.parent.is_dir()) or [])
    assert main(["dev", "tag", str(staged), "-o", str(out)]) == 0
    assert seen == [True] and out.exists()


@pytest.mark.parametrize("text,notice", [
    ("shwo lizard", True), ("plain", True), ("plain words please", False),
    ("plain English words", False), ("how are you", False),
])
def test_near_command_notice_only_for_a_word_or_two(text, notice, capsys):
    assert main(text.split()) == 0
    assert ("did you mean" in capsys.readouterr().err) is notice


@pytest.mark.parametrize("argv", [
    ["yarn-tools", "brief", "missing.txt"],
    ["judge", "brief", "G'day.", "--candidate", "a=missing.txt"],
    ["judge", "read", "missing.json", "report.json"],
    ["judge", "tally", "missing.json"],
])
def test_new_file_consumers_use_contextual_read_errors(argv, capsys):
    assert main(argv) == 2
    assert "no such file" in capsys.readouterr().err


def test_missing_declined_file_is_a_contextual_usage_error(tmp_path, capsys):
    source = tmp_path / "source.txt"
    source.write_text("She was tired.")
    missing = tmp_path / "declined.yaml"
    assert main(["yarn-tools", "lint", str(source), "--declined", str(missing)]) == 2
    assert "--declined: no such file" in capsys.readouterr().err
