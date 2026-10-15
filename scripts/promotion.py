"""Release rules, pinned candidate validation and the rooted local Git boundary."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


BASE = "main"
REMOTE = "origin"
CHECKS = ([sys.executable, "scripts/publish_docs.py", "check"], [sys.executable, "-m", "ruff", "check", "."], [sys.executable, "-m", "pytest", "-q", "-rs"],
          [sys.executable, "scripts/notices.py", "check", "--wheel"])
# Tests that may skip in a release: they run on copyrighted texts kept only on a maintainer's machine.
ALLOWED_SKIPS = ("tests/functional/test_local_reference.py",)
SKIP_RE = re.compile(r"(?m)^SKIPPED \[\d+\] ([^:\s]+):.*$")
VERSION_FILE = "aussiefy/__init__.py"
VERSION_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
INIT_VERSION_RE = re.compile(r'(?m)^__version__\s*=\s*"([^"]*)"')
TRAILER = "Promoted-From"


class PromotionError(Exception):
    """A check failed; the message says which and how to fix it."""


# --- pure rules ------------------------------------------------------------------------------------------------

def parse_version(text: str) -> tuple[int, int, int]:
    m = VERSION_RE.fullmatch(text.strip())
    if not m:
        raise PromotionError(f"version {text!r} is not MAJOR.MINOR.PATCH")
    return int(m[1]), int(m[2]), int(m[3])


def bumped(version: str, part: str) -> str:
    major, minor, patch = parse_version(version)
    return {"major": f"{major + 1}.0.0", "minor": f"{major}.{minor + 1}.0", "patch": f"{major}.{minor}.{patch + 1}"}[part]


def check_increment(previous: str | None, new: str) -> None:
    """new must be exactly one semver step past previous (any valid version when there is no previous release)."""
    parse_version(new)
    if previous is None:
        return
    allowed = {bumped(previous, part) for part in ("major", "minor", "patch")}
    if new not in allowed:
        raise PromotionError(f"version {new} is not one step past {BASE}'s {previous}; "
                             f"expected one of {', '.join(sorted(allowed, key=parse_version))}")


def changelog_section(changelog: str, version: str) -> str:
    """The body of `## [version] - YYYY-MM-DD`, up to the next `## ` heading."""
    m = re.search(rf"(?m)^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}[ \t]*\n(.*?)(?=^## |\Z)", changelog, re.S)
    if not m or not m[1].strip():
        raise PromotionError(f"CHANGELOG.md has no dated section for {version} (`## [{version}] - YYYY-MM-DD`, "
                             "with the changes under it); `promote.py prepare` makes one from [Unreleased]")
    return m[1].strip()


def date_unreleased(changelog: str, version: str, today: dt.date) -> str:
    """Turn `## [Unreleased]` into `## [version] - today`, leaving a fresh empty [Unreleased] above it."""
    if not re.search(r"(?m)^## \[Unreleased\][ \t]*$", changelog):
        raise PromotionError("CHANGELOG.md has no `## [Unreleased]` section to release")
    return re.sub(r"(?m)^## \[Unreleased\][ \t]*$", f"## [Unreleased]\n\n## [{version}] - {today.isoformat()}",
                  changelog, count=1)


def unexpected_skips(pytest_output: str) -> list[str]:
    """The `-rs` skip lines in pytest's output for tests outside ALLOWED_SKIPS."""
    return [m[0] for m in SKIP_RE.finditer(pytest_output) if m[1] not in ALLOWED_SKIPS]


def release_message(version: str, notes: str, source: str) -> str:
    return f"Release v{version}\n\n{notes}\n\n{TRAILER}: {source}\n"


def promoted_from(message: str) -> str | None:
    m = re.search(rf"(?m)^{TRAILER}: ([0-9a-f]{{40}})$", message)
    return m[1] if m else None


# --- the git shell ---------------------------------------------------------------------------------------------

@dataclass
class Git:
    root: Path

    def invoke(self, *args: str):
        try:
            return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        except OSError as exc:
            raise PromotionError(f"git {' '.join(args)} in {self.root}: {exc}") from exc

    def run(self, *args: str, check: bool = True) -> str:
        p = self.invoke(*args)
        if check and p.returncode:
            raise PromotionError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
        return p.stdout.strip()

    def ok(self, *args: str) -> bool:
        return self.invoke(*args).returncode == 0

    def show(self, rev: str, path: str) -> str | None:
        return self.run("show", f"{rev}:{path}") if self.ok("cat-file", "-e", f"{rev}:{path}") else None


@dataclass
class Release:
    version: str
    previous: str | None
    source: str          # the commit being released
    base: str            # main's head, the new commit's parent
    notes: str


def version_in(text_init: str | None) -> str | None:
    m = INIT_VERSION_RE.search(text_init or "")
    return m[1] if m else None


def plan(git: Git, head: str, base: str, branch: str) -> Release:
    """Validate a pinned release/base pair without relying on the invoking checkout."""
    source = git.run("rev-parse", f"{head}^{{commit}}")
    base = git.run("rev-parse", f"{base}^{{commit}}")
    version = version_in(git.show(source, VERSION_FILE))
    if version is None:
        raise PromotionError(f"{VERSION_FILE} has no __version__")
    if branch != f"release/v{version}":
        raise PromotionError(f"release branch must be release/v{version}, got {branch}")
    previous = version_in(git.show(base, VERSION_FILE))
    check_increment(previous, version)
    if not git.ok("merge-base", "--is-ancestor", base, source):
        raise PromotionError("release does not contain the current main; update from dev and check again")
    origin = promoted_from(git.run("log", "-1", "--format=%B", base))
    if previous is not None:
        if origin is None or not git.ok("merge-base", "--is-ancestor", origin, source):
            raise PromotionError("main has missing or unrelated Promoted-From provenance")
        if git.run("rev-parse", f"{base}^{{tree}}") != git.run("rev-parse", f"{origin}^{{tree}}"):
            raise PromotionError("main's tree differs from its promoted source")
    tree = git.run("merge-tree", "--write-tree", base, source).splitlines()[0]
    if tree != git.run("rev-parse", f"{source}^{{tree}}"):
        raise PromotionError("proposed squash tree differs from the checked release head")
    notes = changelog_section(git.show(source, "CHANGELOG.md") or "", version)
    return Release(version, previous, source, base, notes)


def run_checks(git: Git, source: str, commands=CHECKS) -> None:
    """The required checks on a clean checkout of exactly the commit being released. A command fails if it
    exits non-zero or reports a skip outside ALLOWED_SKIPS."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "release"
        git.run("worktree", "add", "--detach", str(work), source)
        try:
            for cmd in commands:
                print(f"$ {' '.join(cmd)}", flush=True)
                returncode, output = run_echoed(cmd, work)
                if returncode:
                    raise PromotionError(f"`{' '.join(cmd)}` failed on {source[:12]}; nothing was released")
                skipped = unexpected_skips(output)
                if skipped:
                    raise PromotionError(f"`{' '.join(cmd)}` skipped tests on {source[:12]} (install the dev extra: "
                                         "pip install -e '.[dev]'); nothing was released:\n  " + "\n  ".join(skipped))
        finally:
            git.run("worktree", "remove", "--force", str(work))


def run_echoed(cmd: list[str], cwd: Path) -> tuple[int, str]:
    """Run cmd, echoing its output as it comes, and return its exit code and output."""
    lines = []
    with subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        for line in proc.stdout:
            print(line, end="", flush=True)
            lines.append(line)
    return proc.returncode, "".join(lines)
