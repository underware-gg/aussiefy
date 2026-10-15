"""GitHub REST boundary for checked release pull requests; authentication belongs to gh."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlencode

from promotion import PromotionError, release_message

REQUIRED_CHECK = "aussiefy-release-head"
ACTIONS_APP_ID = 15368


class GitHubError(PromotionError):
    def __init__(self, message: str, status: int | None):
        super().__init__(message)
        self.status = status


def require_protection(data: dict) -> None:
    checks = data.get("required_status_checks") or {}
    identities = checks.get("checks") or []
    reviews = data.get("required_pull_request_reviews")
    bypass = (reviews or {}).get("bypass_pull_request_allowances") or {}
    if (checks.get("strict") is not True
            or {"context": REQUIRED_CHECK, "app_id": ACTIONS_APP_ID} not in identities
            or (data.get("enforce_admins") or {}).get("enabled") is not True
            or reviews is None or any(bypass.values())
            or (data.get("allow_force_pushes") or {}).get("enabled") is not False
            or (data.get("allow_deletions") or {}).get("enabled") is not False):
        raise PromotionError("main requires strict release-head checks pinned to GitHub Actions, required PRs, "
                             "administrator enforcement, and no review/force-push/deletion bypass")


def require_checks(runs: list[dict], head: str) -> None:
    matching = [r for r in runs if r.get("name") == REQUIRED_CHECK
                and (r.get("app") or {}).get("id") == ACTIONS_APP_ID and r.get("head_sha") == head]
    latest = max(matching, key=lambda r: r["id"], default=None)
    if not latest or latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise PromotionError(f"{REQUIRED_CHECK} has not succeeded on exact head {head}")


@dataclass
class GitHub:
    root: Path
    repository: str

    def api(self, endpoint: str, method: str = "GET", body: dict | None = None, *, optional: bool = False,
            pages: bool = False):
        cmd = ["gh", "api", endpoint, "--method", method]
        if body is not None:
            cmd += ["--input", "-"]
        if pages:
            cmd += ["--paginate", "--slurp"]
        try:
            result = subprocess.run(cmd, cwd=self.root, input=json.dumps(body) if body is not None else None,
                                    capture_output=True, text=True)
        except OSError as exc:
            raise PromotionError(f"could not invoke gh: {exc}") from exc
        if result.returncode:
            match = re.search(r"HTTP (\d+)", result.stderr)
            status = int(match[1]) if match else None
            if optional and status == 404:
                return None
            raise GitHubError(f"GitHub {method} {endpoint}: {result.stderr.strip()}", status)
        if not result.stdout.strip():
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise PromotionError(f"GitHub {endpoint}: invalid JSON response") from exc

    def repo(self, suffix: str = "", **kwargs):
        return self.api(f"repos/{self.repository}{suffix}", **kwargs)

    def protection(self) -> None:
        try:
            require_protection(self.repo("/branches/main/protection"))
        except GitHubError as exc:
            raise PromotionError(f"cannot verify enforceable main protection; automated finish is disabled: {exc}") from exc

    def configure(self) -> None:
        # Availability is checked before changing any settings. Never weaken an existing rule.
        current = self.repo("/branches/main/protection", optional=True)
        if current is not None:
            require_protection(current)
            return
        self.repo("/branches/main/protection", method="PUT", body={
            "required_status_checks": {"strict": True, "checks": [{"context": REQUIRED_CHECK, "app_id": ACTIONS_APP_ID}]},
            "enforce_admins": True, "required_pull_request_reviews": {"required_approving_review_count": 0,
                "bypass_pull_request_allowances": {"users": [], "teams": [], "apps": []}},
            "restrictions": None, "allow_force_pushes": False, "allow_deletions": False})
        self.protection()

    def pull(self, number: int) -> dict:
        return self.repo(f"/pulls/{number}")

    def pulls(self, branch: str) -> list[dict]:
        query = urlencode({"state": "all", "head": f"{self.repository.split('/')[0]}:{branch}", "base": "main", "per_page": 100})
        return [item for page in self.repo(f"/pulls?{query}", pages=True) for item in page]

    def checks(self, head: str) -> None:
        query = urlencode({"check_name": REQUIRED_CHECK, "filter": "latest", "per_page": 100})
        pages = self.repo(f"/commits/{head}/check-runs?{query}", pages=True)
        require_checks([r for page in pages for r in page["check_runs"]], head)

    def open_pull(self, branch: str, version: str, source: str, head: str) -> dict:
        return self.repo("/pulls", method="POST", body={"title": f"Release v{version}", "head": branch,
            "base": "main", "body": f"Prepared from dev `{source}`. Release head: `{head}`.\n\n"
            "Publication, Ruff, full tests and wheel/provenance checks passed twice locally on the candidate.\n"
            "Required CI checks this exact release head. Finish requires the checked head/base and strict main protection."})

    def merge(self, number: int, rel) -> str:
        message = release_message(rel.version, rel.notes, rel.source)
        result = self.repo(f"/pulls/{number}/merge", method="PUT", body={"merge_method": "squash", "sha": rel.source,
            "commit_title": f"Release v{rel.version}", "commit_message": message.split("\n", 1)[1].strip()})
        if not result.get("merged"):
            raise PromotionError(f"GitHub refused the checked squash merge: {result.get('message')}")
        return result["sha"]

    def release(self, tag: str):
        return self.repo(f"/releases/tags/{tag}", optional=True)

    def publish(self, tag: str, commit: str, notes: str) -> dict:
        return self.repo("/releases", method="POST", body={"tag_name": tag, "target_commitish": commit,
            "name": tag, "body": notes, "draft": False, "prerelease": False})
