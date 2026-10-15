"""Prepare, check and finish releases through checked GitHub squash pull requests."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import re
import sys

from promotion import (Git, PromotionError, VERSION_FILE, INIT_VERSION_RE, bumped, changelog_section,
                       date_unreleased, plan, promoted_from, run_checks, run_echoed, version_in)
from promotion_github import GitHub
from publish_docs import PublicationError, generate as generate_docs, load as load_publication


def clean(git: Git) -> None:
    if git.run("status", "--porcelain"):
        raise PromotionError("working tree is not clean; review and commit or stash your changes")


def fetch(git: Git) -> None:
    git.run("fetch", "--prune", "--tags", "origin")


def sha(git: Git, ref: str) -> str:
    return git.run("rev-parse", f"{ref}^{{commit}}")


def branch_version(branch: str) -> str:
    match = re.fullmatch(r"release/v(\d+\.\d+\.\d+)", branch)
    if not match:
        raise PromotionError("expected a release/vX.Y.Z branch")
    return match[1]


def bump(root: Path, part: str, today: dt.date | None = None) -> str:
    try:
        init = root / VERSION_FILE
        changelog = root / load_publication(root).sources["CHANGELOG.md"]
        text = init.read_text(encoding="utf-8")
        current = version_in(text)
        if current is None:
            raise PromotionError(f"{VERSION_FILE} has no __version__")
        new = bumped(current, part)
        dated = date_unreleased(changelog.read_text(encoding="utf-8"), new, today or dt.date.today())
        init.write_text(INIT_VERSION_RE.sub(f'__version__ = "{new}"', text, 1), encoding="utf-8")
        changelog.write_text(dated, encoding="utf-8")
        generate_docs(root)
        return new
    except (PublicationError, KeyError, OSError) as exc:
        raise PromotionError(f"could not prepare version/changelog/publication: {exc}") from exc


def validate_pull(github: GitHub, pull: dict, head: str, base: str, branch: str, *, merged: bool = False) -> None:
    if (pull.get("draft") or pull["head"]["sha"] != head or pull["head"]["ref"] != branch
            or (pull["head"].get("repo") or {}).get("full_name") != github.repository
            or pull["base"]["ref"] != "main" or pull["base"]["repo"]["full_name"] != github.repository
            or (not merged and (pull["base"]["sha"] != base or pull["state"] != "open"))):
        raise PromotionError("PR repository/branch/head/base differs from the checked candidate")


def check(git: Git, head: str, base: str, branch: str, checks=run_checks):
    clean(git)
    rel = plan(git, head, base, branch)
    checks(git, rel.source)
    print(f"Checked release/v{rel.version}: head {rel.source}, base {rel.base}", flush=True)
    return rel


def prepare(git: Git, github: GitHub, part: str, checks=run_checks) -> dict:
    fetch(git)
    branch = git.run("branch", "--show-current")
    source = sha(git, "dev")
    if source != sha(git, "origin/dev"):
        raise PromotionError("dev differs from origin/dev; reconcile it without discarding commits")
    if branch == "dev":
        clean(git)
        version = version_in(git.show(source, VERSION_FILE))
        if version is None:
            raise PromotionError(f"{VERSION_FILE} has no __version__")
        new = bumped(version, part)
        branch = f"release/v{new}"
        if git.ok("show-ref", "--verify", f"refs/heads/{branch}") or git.ok("show-ref", "--verify", f"refs/remotes/origin/{branch}"):
            raise PromotionError(f"{branch} exists; inspect it and checkout that branch to resume prepare")
        if git.ok("rev-parse", "--verify", f"refs/tags/v{new}") or github.release(f"v{new}"):
            raise PromotionError(f"v{new} already exists; do not rebuild a different release")
        git.run("checkout", "-b", branch, source)
    else:
        new = branch_version(branch)
        if not git.ok("merge-base", "--is-ancestor", source, "HEAD"):
            raise PromotionError("dev advanced beyond this preparation; reconcile the release work explicitly")
    try:
        if sha(git, "HEAD") == source:
            working_version = version_in((git.root / VERSION_FILE).read_text(encoding="utf-8"))
            if working_version != new:
                if git.run("status", "--porcelain"):
                    raise PromotionError("partial preparation needs review before bumping; fix version/changelog then resume")
                if bump(git.root, part) != new:
                    raise PromotionError("resume part does not match the existing release branch")
            else:
                generate_docs(git.root)
            code, _ = run_echoed([sys.executable, "scripts/notices.py", "generate"], git.root)
            if code:
                raise PromotionError("notice generation failed")
            git.run("add", "--", VERSION_FILE, "docs/plain", "docs", "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md")
            tree = git.run("write-tree")
            provisional = git.run("commit-tree", tree, "-p", source, "-m", f"Verify release v{new}")
            rel = plan(git, provisional, "origin/main", branch)
            checks(git, provisional)
            git.run("commit", "-m", f"Prepare release v{new}")
        else:
            # A manually committed recovery still receives both isolated verification cycles.
            rel = plan(git, "HEAD", "origin/main", branch)
            checks(git, rel.source)
        clean(git)
        rel = check(git, "HEAD", "origin/main", branch, checks)
        if github.release(f"v{rel.version}"):
            raise PromotionError("version is already published")
        existing = github.pulls(branch)
        if len(existing) > 1 or (existing and existing[0]["state"] != "open"):
            raise PromotionError("release branch has conflicting historical PRs")
        if existing:
            validate_pull(github, existing[0], rel.source, rel.base, branch)
        git.run("push", "origin", f"HEAD:refs/heads/{branch}")
        pull = existing[0] if existing else github.open_pull(branch, rel.version, source, rel.source)
        print(f"Release PR: {pull['html_url']}; check with python scripts/promote.py check --pr {pull['number']}")
        return pull
    except (PromotionError, PublicationError) as exc:
        raise PromotionError(f"preparation retained on {branch}: {exc}\n"
                             f"Review/fix its work, then resume: python scripts/promote.py prepare {part}") from exc


def check_pull(git: Git, github: GitHub, number: int, checks=run_checks):
    clean(git)
    fetch(git)
    pull = github.pull(number)
    head, base, branch = pull["head"]["sha"], pull["base"]["sha"], pull["head"]["ref"]
    if sha(git, "origin/main") != base:
        raise PromotionError("PR base moved; recheck its current head/base")
    git.run("fetch", "origin", f"refs/pull/{number}/head")
    validate_pull(github, pull, head, base, branch)
    github.protection()
    github.checks(head)
    rel = check(git, head, base, branch, checks)
    print(f"Ready: python scripts/promote.py finish --pr {number} --head {head} --base {base}")
    return rel


def verify_merge(git: Git, rel, commit: str) -> None:
    if (git.run("rev-list", "--parents", "-n", "1", commit).split() != [commit, rel.base]
            or git.run("rev-parse", f"{commit}^{{tree}}") != git.run("rev-parse", f"{rel.source}^{{tree}}")
            or promoted_from(git.run("log", "-1", "--format=%B", commit)) != rel.source
            or changelog_section(git.show(commit, "CHANGELOG.md") or "", rel.version) != rel.notes):
        raise PromotionError("merged commit has wrong parent/tree/Promoted-From/changelog; nothing further will publish")


def verify_tag(git: Git, tag: str, commit: str) -> bool:
    if not git.ok("rev-parse", "--verify", f"refs/tags/{tag}"):
        return False
    if sha(git, f"refs/tags/{tag}") != commit:
        raise PromotionError(f"immutable {tag} points to a different commit")
    return True


def dev_ready(git: Git, tip: str, head: str, merged: str | None = None) -> bool:
    """Allow preparation ancestry or a completed reconciliation that retains later development."""
    if git.ok("merge-base", "--is-ancestor", tip, head):
        return True
    if not git.ok("merge-base", "--is-ancestor", head, tip):
        return False
    return git.run("rev-parse", f"{tip}^{{tree}}") == git.run("rev-parse", f"{head}^{{tree}}") or (
        merged is not None and git.ok("merge-base", "--is-ancestor", merged, tip))


def finish(git: Git, github: GitHub, number: int, head: str, base: str) -> str:
    clean(git)
    if git.run("branch", "--show-current") not in ("dev", f"release/v{version_in(git.show(head, VERSION_FILE))}"):
        raise PromotionError("finish from a clean dev or matching release branch")
    fetch(git)
    pull = github.pull(number)
    branch = pull["head"]["ref"]
    validate_pull(github, pull, head, base, branch, merged=bool(pull.get("merged")))
    rel = plan(git, head, base, branch)
    dev = sha(git, "dev")
    remote_dev = sha(git, "origin/dev")
    merged = pull.get("merge_commit_sha") if pull.get("merged") else None
    if merged is not None:
        verify_merge(git, rel, merged)
    if any(not dev_ready(git, tip, head, merged) for tip in (dev, remote_dev)):
        raise PromotionError(f"dev advanced after preparation; preserve its work by reconciling dev with {branch} "
                             "and verified main, then resume finish")
    if not git.ok("merge-base", "--is-ancestor", remote_dev, dev):
        raise PromotionError("local dev differs from origin/dev; reconcile before finishing")
    github.protection()
    tag = f"v{rel.version}"
    published = github.release(tag)
    if not pull.get("merged"):
        if published or git.ok("rev-parse", "--verify", f"refs/tags/{tag}"):
            raise PromotionError("tag/release already exists before this PR merge")
        if sha(git, "origin/main") != base:
            raise PromotionError("checked main base moved; prepare/check an updated candidate")
        github.protection()
        github.checks(head)
        # The server's strict checks close the base-move race; sha closes the head-move race.
        commit = github.merge(number, rel)
    else:
        commit = pull["merge_commit_sha"]
    fetch(git)
    if sha(git, "origin/main") != commit:
        raise PromotionError("main moved beyond the release; inspect before publishing/resuming")
    verify_merge(git, rel, commit)
    if not verify_tag(git, tag, commit):
        git.run("tag", "-a", tag, commit, "-m", f"aussiefy {rel.version}")
    git.run("push", "origin", f"refs/tags/{tag}")
    if published is None:
        published = github.publish(tag, commit, rel.notes)
    if (published.get("tag_name") != tag or published.get("name") != tag or published.get("body") != rel.notes
            or published.get("draft") is not False or published.get("prerelease") is not False):
        raise PromotionError("existing GitHub release differs from the verified version/notes; inspect it")
    fetch(git)
    remote_dev = sha(git, "origin/dev")
    local_dev = sha(git, "dev")
    if not git.ok("merge-base", "--is-ancestor", remote_dev, local_dev) or not dev_ready(git, local_dev, head, commit):
        raise PromotionError(f"release is published but dev advanced; preserve its work: checkout dev, merge {branch}, "
                             "resolve conflicts, merge -s ours origin/main, then push dev and resume finish")
    git.run("checkout", "dev")
    if git.ok("merge-base", "--is-ancestor", local_dev, head):
        git.run("merge", "--ff-only", head)
    if not git.ok("merge-base", "--is-ancestor", commit, "dev"):
        git.run("merge", "--no-ff", "-s", "ours", commit, "-m", f"Reconcile release {tag} from main")
    git.run("push", "origin", "dev:refs/heads/dev")
    if not git.ok("merge-base", "--is-ancestor", head, "dev") or not git.ok("merge-base", "--is-ancestor", commit, "dev"):
        raise PromotionError("dev reconciliation did not retain release source and main")
    remote = git.run("ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if remote:
        if remote.split()[0] != head:
            raise PromotionError("release branch advanced; retain it for review")
        # The lease constrains deletion only; never replace a branch tip or force-update dev/main.
        git.run("push", "origin", f"--force-with-lease=refs/heads/{branch}:{head}", f":refs/heads/{branch}")
    if git.ok("show-ref", "--verify", f"refs/heads/{branch}"):
        if sha(git, branch) != head:
            raise PromotionError("local release branch advanced; retain it for review")
        git.run("branch", "-d", branch)
    print(f"Published {tag} at {commit}; dev reconciled and release branch removed")
    return commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("part", choices=("major", "minor", "patch"))
    sub.add_parser("configure", help="apply and verify strict main protection when available")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--pr", type=int)
    check_parser.add_argument("--head", default="HEAD")
    check_parser.add_argument("--base", default="origin/main")
    check_parser.add_argument("--branch", help="release branch identity for detached CI checkout")
    finish_parser = sub.add_parser("finish")
    finish_parser.add_argument("--pr", type=int, required=True)
    finish_parser.add_argument("--head", required=True)
    finish_parser.add_argument("--base", required=True)
    args = parser.parse_args(argv)
    git = Git(args.root.resolve())
    try:
        if args.command == "check" and args.pr is None:
            check(git, args.head, args.base, args.branch or git.run("branch", "--show-current"))
            return 0
        repository = git.run("config", "--get", "remote.origin.url")
        match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?", repository)
        if not match:
            raise PromotionError("origin must identify the GitHub repository")
        github = GitHub(git.root, match[1])
        if args.command == "prepare":
            prepare(git, github, args.part)
        elif args.command == "configure":
            github.configure()
        elif args.command == "check":
            check_pull(git, github, args.pr)
        else:
            finish(git, github, args.pr, args.head, args.base)
        return 0
    except (PromotionError, PublicationError) as exc:
        print(f"promote: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
