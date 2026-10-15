"""Current documentation uses real CLI syntax and reproduces its displayed output."""

import argparse
import io
from pathlib import Path
import re
import shlex
import sys

import pytest

from aussiefy.cli import build_parser, main

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from publish_docs import authoritative_docs, load  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]


def current_docs():
    return [ROOT / name for name in authoritative_docs(ROOT, load(ROOT))]


def command_args(line):
    """Read argv only: shell pipes, redirections and comments never execute."""
    if not re.search(r"(?:^|[|;]\s*|&&\s*)(?:\$ )?aussiefy(?:\s|$)", line):
        return None
    line = line.replace("<command>", "translate").replace("<round>", "example-round")
    lexer = shlex.shlex(line.removeprefix("$ "), posix=True, punctuation_chars="|<>;&")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    tokens = list(lexer)
    for i, token in enumerate(tokens):
        if token == "aussiefy" and (i == 0 or tokens[i - 1] in ("|", ";", "&&")):
            args = tokens[i + 1:]
            stop = next((j for j, arg in enumerate(args) if arg in ("<", ">", ">>", "|", ";", "&&")), len(args))
            return args[:stop]
    return None


def documented_commands():
    for path in current_docs():
        fence = None
        for number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                fence = None if fence is not None else stripped[3:]
                continue
            fragments = [stripped] if fence in ("", "sh", "bash", "console") or line.startswith("    ") else []
            if fence is None:
                fragments += re.findall(r"`([^`\n]+)`", line)
            for fragment in fragments:
                args = command_args(fragment)
                if args is not None:
                    yield path.relative_to(ROOT).as_posix(), number, args


COMMANDS = list(documented_commands())


def parser_args(parser, args):
    """Apply implicit translate syntax; complete bare command references, not runnable examples."""
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
    args = list(args)
    if not args or args[0] not in (*sub, "-h", "--help"):
        args.insert(0, "translate")
    references = {("lookup",): ["query"], ("show",): ["query"], ("compare",): ["original", "target"],
                  ("gaps",): ["file"], ("verify",): ["draft", "--original", "original"],
                  ("judge",): ["tally", "verdict"], ("yarn-tools",): ["brief", "source"], ("yarn-tools", "brief"): ["source"],
                  ("embedder",): ["status"], ("dev",): ["fragments"],
                  ("dev", "scrape"): ["url"], ("dev", "tag"): ["staging"],
                  ("dev", "harvest"): ["original", "rewrite"],
                  ("dev", "review"): ["tagged"], ("dev", "round"): ["directory"]}
    return args + references.get(tuple(args), [])


@pytest.mark.parametrize("path,line,args", COMMANDS, ids=[f"{p}:{n}" for p, n, _ in COMMANDS])
def test_documented_commands_parse(path, line, args, capsys):
    parser = build_parser()
    try:
        parser.parse_args(parser_args(parser, args))
    except SystemExit as exc:
        assert exc.code == 0, f"{path}:{line}: {args}\n{capsys.readouterr().err}"


def test_command_scan_covers_the_current_surfaces():
    paths = {p for p, _, _ in COMMANDS}
    assert {"docs/plain/root/README.md", "docs/plain/user/getting-started.md", "docs/plain/user/agents.md",
            "docs/plain/contributor/data-acquisition.md", "skills/aussiefy/SKILL.md"} <= paths
    commands = {args[0] for _, _, args in COMMANDS if args}
    assert {"translate", "guide", "plan", "lookup", "lint", "show", "yarn", "dev", "embedder"} <= commands


def displayed_examples():
    for path in current_docs():
        for block in re.findall(r"(?m)^```[^\n]*\n(.*?)^```", path.read_text(), re.S):
            lines = block.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("$ aussiefy "):
                    end = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("$ ")), len(lines))
                    yield path.relative_to(ROOT).as_posix(), command_args(line), "\n".join(lines[i + 1:end]).strip()


EXAMPLES = list(displayed_examples())


@pytest.mark.parametrize("path,args,expected", EXAMPLES, ids=[p for p, _, _ in EXAMPLES])
def test_displayed_cli_output(path, args, expected, capsys, monkeypatch):
    assert expected, f"{path}: a prompt example must display its result"
    assert not {"--surface", "--rewrite", "yarn", "dev", "embedder"} & set(args)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert main(args) == 0
    out, err = capsys.readouterr()
    actual = out.rstrip() + ("\n\n" + err.strip() if err else "")
    assert actual == expected, path


def test_displayed_output_scan_is_not_empty():
    assert {"docs/plain/root/README.md", "docs/plain/user/getting-started.md", "docs/plain/functional/explain.md"} <= {p for p, _, _ in EXAMPLES}


@pytest.mark.parametrize("line,expected", [
    ('echo "aussiefy fake" | aussiefy -l 4 < input.txt # --fake', ["-l", "4"]),
    ('aussiefy "# is text" --json', ["# is text", "--json"]),
    ('claude mcp add aussiefy -- aussiefy-mcp', None),
    ('aussiefy show lizard > output.yaml', ["show", "lizard"]),
])
def test_shell_syntax_is_removed_without_losing_quoted_text(line, expected):
    assert command_args(line) == expected


def test_bad_documented_flags_and_subcommands_fail(capsys):
    for line in ("aussiefy lint draft.txt --not-a-flag", "aussiefy dev nope", "aussiefy show lizard --wrong"):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(parser_args(parser, command_args(line)))
        assert exc.value.code == 2
