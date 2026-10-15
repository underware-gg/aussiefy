"""Release rules and complete resumable PR releases with real local Git and a simulated GitHub server."""

import datetime as dt
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import promotion as p  # noqa: E402
import promote as flow  # noqa: E402
from promotion_github import ACTIONS_APP_ID, REQUIRED_CHECK, require_checks, require_protection  # noqa: E402
from publish_docs import generate, check as check_docs  # noqa: E402


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def write(root, name, text):
    file = root / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)


def commit(root, message):
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', message)
    return git(root, 'rev-parse', 'HEAD')


def test_increment_is_one_semver_step():
    p.check_increment(None, '0.1.0')
    for new in ('0.1.1', '0.2.0', '1.0.0'):
        p.check_increment('0.1.0', new)
    for bad in ('0.1.0', '0.1.2', '0.3.0', '0.2.1', '2.0.0', '0.0.9'):
        with pytest.raises(p.PromotionError):
            p.check_increment('0.1.0', bad)
    with pytest.raises(p.PromotionError):
        p.parse_version('1.2')
    assert p.bumped('1.4.2', 'minor') == '1.5.0' and p.bumped('1.4.2', 'major') == '2.0.0'


def test_changelog_rules():
    text = '# Changelog\n\n## [Unreleased]\n\n- New thing.\n\n## [0.1.0] - 2026-10-01\n\n- Old.\n'
    dated = p.date_unreleased(text, '0.2.0', dt.date(2026, 10, 12))
    assert '## [Unreleased]\n\n## [0.2.0] - 2026-10-12' in dated
    assert p.changelog_section(dated, '0.2.0') == '- New thing.'
    with pytest.raises(p.PromotionError):
        p.changelog_section('# Changelog\n\n## [0.2.0] - 2026-10-12\n', '0.2.0')


class Server:
    """Only the network boundary is simulated; strict server enforcement uses actual remote Git."""
    repository = 'owner/aussiefy'

    def __init__(self, root, remote):
        self.root, self.remote = root, remote
        self.prs, self.releases, self.events = [], {}, []
        self.enforced, self.success, self.move_base, self.fail_at = True, True, False, None
        self.bad_merge = False

    def boundary(self, name):
        self.events.append(name)
        if self.fail_at == name:
            self.fail_at = None
            raise p.PromotionError(f'interrupted at {name}')

    def protection(self):
        self.boundary('protection')
        if not self.enforced:
            raise p.PromotionError('no strict protection')

    def checks(self, head):
        self.boundary('checks')
        if not self.success:
            raise p.PromotionError('required head check failed')

    def release(self, tag):
        return self.releases.get(tag)

    def pulls(self, branch):
        return [pr for pr in self.prs if pr['head']['ref'] == branch]

    def open_pull(self, branch, version, source, head):
        self.boundary('open')
        pr = {'number': len(self.prs)+1, 'state': 'open', 'draft': False, 'merged': False,
              'head': {'ref': branch, 'sha': head, 'repo': {'full_name': self.repository}},
              'base': {'ref': 'main', 'sha': git(self.remote, 'rev-parse', 'main'),
                       'repo': {'full_name': self.repository}}, 'html_url': 'https://example.org/pr'}
        self.prs.append(pr)
        git(self.remote, "update-ref", f"refs/pull/{pr['number']}/head", head)
        return pr

    def pull(self, number):
        return self.prs[number-1]

    def merge(self, number, rel):
        self.boundary('merge')
        current = git(self.remote, 'rev-parse', 'main')
        if self.move_base:
            current = git(self.remote, 'commit-tree', f'{current}^{{tree}}', '-p', current, '-m', 'main advanced')
            git(self.remote, 'update-ref', 'refs/heads/main', current)
        pr = self.pull(number)
        if current != rel.base or pr['head']['sha'] != rel.source or not self.enforced or not self.success:
            raise p.PromotionError('server refused stale head/base or failed enforcement')
        message = p.release_message(rel.version, rel.notes, rel.source)
        if self.bad_merge:
            message = 'wrong provenance'
        merged = git(self.remote, 'commit-tree', f'{rel.source}^{{tree}}', '-p', current, '-m', message)
        git(self.remote, 'update-ref', 'refs/heads/main', merged, current)
        pr.update(merged=True, state='closed', merge_commit_sha=merged)
        self.boundary('after-merge')
        return merged

    def publish(self, tag, commit, notes):
        self.boundary('publish')
        self.releases[tag] = {'tag_name': tag, 'name': tag, 'body': notes, 'draft': False, 'prerelease': False}
        self.boundary('after-publish')
        return self.releases[tag]


def candidate_checks(repo, head):
    """Actual isolated checkout and freshness check; full project gates run separately in rehearsal."""
    script = str(Path(__file__).resolve().parents[2] / 'scripts/publish_docs.py')
    p.run_checks(repo, head, ([sys.executable, script, 'check', '--root', '.'],))


@pytest.fixture
def repo(tmp_path):
    root, remote = tmp_path / 'repo', tmp_path / 'origin.git'
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    for path in (root,):
        git(path, 'config', 'user.email', 'test@example.com')
        git(path, 'config', 'user.name', 'Release test')
    write(root, 'LICENSE', 'Fixture licence.\n')
    commit(root, 'initial')
    git(root, 'checkout', '-qb', 'dev')
    write(root, p.VERSION_FILE, '__version__ = "0.1.0"\n')
    write(root, 'docs/plain/root/CHANGELOG.md', '# Changelog\n\n## [Unreleased]\n\n- I am very busy.\n')
    write(root, 'docs/publication.yaml', yaml.safe_dump({'translation': {'level': 5, 'vulgarity': 'dad', 'seed': 0},
        'documents': [{'source': 'docs/plain/root/CHANGELOG.md', 'output': 'CHANGELOG.md'}]}))
    write(root, 'README.md', '# Fixture\n')
    write(root, 'CONTRIBUTING.md', '# Fixture\n')
    write(root, 'THIRD_PARTY_NOTICES.md', 'Own fixture notice.\n')
    write(root, 'scripts/notices.py', 'print("Own fixture notice remains unchanged.")\n')
    generate(root)
    commit(root, 'development')
    git(tmp_path, 'clone', '--bare', str(root), str(remote))
    git(remote, 'config', 'user.email', 'test@example.com')
    git(remote, 'config', 'user.name', 'Release server')
    git(root, 'remote', 'add', 'origin', str(remote))
    git(root, 'fetch', '-q', 'origin')
    return p.Git(root), Server(root, remote)


def prepared(repo):
    local, server = repo
    pr = flow.prepare(local, server, 'minor', candidate_checks)
    return local, server, pr, pr['head']['sha'], pr['base']['sha']


def test_two_complete_cycles_have_only_subsequent_changes_in_next_pr(repo):
    local, server, pr, head, base = prepared(repo)
    merge = flow.finish(local, server, pr['number'], head, base)
    assert git(local.root, 'rev-parse', 'v0.2.0^{commit}') == merge
    assert git(local.root, 'rev-parse', 'dev^{tree}') == git(local.root, 'rev-parse', f'{head}^{{tree}}')
    assert git(server.remote, 'rev-list', '--count', 'main') == '2'
    assert not git(server.remote, 'branch', '--list', 'release/*')
    assert git(local.root, 'merge-base', '--is-ancestor', merge, 'dev') == ''
    assert flow.finish(local, server, pr['number'], head, base) == merge
    source = local.root / 'docs/plain/root/CHANGELOG.md'
    source.write_text(source.read_text().replace('## [Unreleased]\n', '## [Unreleased]\n\n- Second change.\n'))
    write(local.root, 'new.txt', 'Only subsequent work.\n')
    generate(local.root)
    commit(local.root, 'new work')
    git(local.root, 'push', '-q', 'origin', 'dev')
    second = flow.prepare(local, server, 'patch', candidate_checks)
    diff = set(git(local.root, 'diff', '--name-only', f"{second['base']['sha']}...{second['head']['sha']}").splitlines())
    assert diff == {p.VERSION_FILE, 'CHANGELOG.md', 'docs/plain/root/CHANGELOG.md', 'new.txt'}
    flow.finish(local, server, second['number'], second['head']['sha'], second['base']['sha'])
    assert git(server.remote, 'rev-list', '--count', 'main') == '3'
    check_docs(local.root)


@pytest.mark.parametrize('boundary', ['after-merge', 'publish', 'after-publish'])
def test_finish_resumes_after_network_boundaries(repo, boundary):
    local, server, pr, head, base = prepared(repo)
    server.fail_at = boundary
    with pytest.raises(p.PromotionError, match='interrupted'):
        flow.finish(local, server, pr['number'], head, base)
    merged = flow.finish(local, server, pr['number'], head, base)
    assert len(server.releases) == 1 and git(local.root, 'rev-parse', 'v0.2.0^{commit}') == merged
    assert git(server.remote, 'rev-list', '--count', 'main') == '2'


@pytest.mark.parametrize('boundary', ['tag', 'tag-push', 'dev-ff', 'dev-merge', 'dev-push', 'remote-delete', 'local-delete'])
def test_finish_resumes_at_local_git_boundaries(repo, monkeypatch, boundary):
    local, server, pr, head, base = prepared(repo)
    original = local.run
    failed = False

    def interrupted(*args, **kwargs):
        nonlocal failed
        kind = ('tag' if args[0] == 'tag' else 'tag-push' if args[:2] == ('push', 'origin') and 'refs/tags/' in args[-1]
                else 'dev-ff' if args[:2] == ('merge', '--ff-only') else 'dev-merge' if args[:2] == ('merge', '--no-ff')
                else 'dev-push' if args[:3] == ('push', 'origin', 'dev:refs/heads/dev')
                else 'remote-delete' if args[:2] == ('push', 'origin') and args[-1].startswith(':refs/heads/')
                else 'local-delete' if args[:2] == ('branch', '-d') else None)
        if kind == boundary and not failed:
            failed = True
            raise p.PromotionError(f'interrupted at {kind}')
        return original(*args, **kwargs)

    monkeypatch.setattr(local, 'run', interrupted)
    with pytest.raises(p.PromotionError, match='interrupted'):
        flow.finish(local, server, pr['number'], head, base)
    assert failed
    flow.finish(local, server, pr['number'], head, base)
    assert git(server.remote, 'rev-list', '--count', 'main') == '2'


def test_server_rejects_main_moving_between_preflight_and_merge(repo):
    local, server, pr, head, base = prepared(repo)
    server.move_base = True
    with pytest.raises(p.PromotionError, match='server refused stale'):
        flow.finish(local, server, pr['number'], head, base)
    assert not server.releases and not git(local.root, 'tag') and not pr['merged']


@pytest.mark.parametrize('problem', ['protection', 'checks', 'head', 'dev', 'main', 'tag', 'provenance'])
def test_finish_refuses_unreviewed_or_inconsistent_state(repo, problem):
    local, server, pr, head, base = prepared(repo)
    if problem == 'protection':
        server.enforced = False
    elif problem == 'checks':
        server.success = False
    elif problem == 'head':
        pr['head']['sha'] = 'f'*40
    elif problem == 'dev':
        git(local.root, 'checkout', 'dev')
        write(local.root, 'later.txt', 'Later development must survive.\n')
        commit(local.root, 'later development')
        git(local.root, 'push', 'origin', 'dev')
    elif problem == 'main':
        advanced = git(server.remote, 'commit-tree', f'{base}^{{tree}}', '-p', base, '-m', 'advanced')
        git(server.remote, 'update-ref', 'refs/heads/main', advanced)
    elif problem == 'tag':
        git(local.root, 'tag', 'v0.2.0', base)
    else:
        server.bad_merge = True
    with pytest.raises(p.PromotionError):
        flow.finish(local, server, pr['number'], head, base)
    assert not server.releases
    if problem in ("checks", "protection"):
        assert "merge" not in server.events and not pr["merged"]


def test_failed_prepare_keeps_reviewable_work_and_resumes(repo):
    local, server = repo
    def failed(*args):
        raise p.PromotionError('gate failed')
    with pytest.raises(p.PromotionError, match='preparation retained.*gate failed'):
        flow.prepare(local, server, 'minor', failed)
    assert git(local.root, 'branch', '--show-current') == 'release/v0.2.0'
    assert not server.prs and not git(server.remote, 'branch', '--list', 'release/*')
    assert version_in_file(local.root) == '0.2.0'
    flow.prepare(local, server, 'minor', candidate_checks)
    assert len(server.prs) == 1


def version_in_file(root):
    return p.version_in((root / p.VERSION_FILE).read_text())


def test_a_skipped_test_fails_checks_unless_explicitly_allowed(repo):
    local, _ = repo
    head = git(local.root, 'rev-parse', 'HEAD')
    allowed = 'SKIPPED [2] tests/functional/test_local_reference.py:16: no local reference texts'
    missing = "SKIPPED [1] tests/contributor/test_scrape.py:21: missing dependency"
    def report(line):
        return ([sys.executable, '-c', 'import sys; print(sys.argv[1])', line],)
    p.run_checks(local, head, report(allowed))
    with pytest.raises(p.PromotionError, match='install the dev extra'):
        p.run_checks(local, head, report(missing))
    assert len(git(local.root, 'worktree', 'list').splitlines()) == 1


def test_bump_edits_plain_changelog_and_regenerates(repo):
    local, _ = repo
    assert flow.bump(local.root, 'minor', dt.date(2026, 10, 12)) == '0.2.0'
    assert '## [0.2.0] - 2026-10-12' in (local.root / 'docs/plain/root/CHANGELOG.md').read_text()
    assert p.changelog_section((local.root / 'CHANGELOG.md').read_text(), '0.2.0')
    assert [sys.executable, 'scripts/publish_docs.py', 'check'] in p.CHECKS


@pytest.mark.parametrize('problem', ['strict', 'admins', 'bypass', 'check', 'app', 'force', 'delete', 'pr'])
def test_missing_strict_enforcement_or_bypass_is_refused(problem):
    rule = {'required_status_checks': {'strict': True, 'checks': [{'context': REQUIRED_CHECK, 'app_id': ACTIONS_APP_ID}]},
            'enforce_admins': {'enabled': True}, 'required_pull_request_reviews': {'bypass_pull_request_allowances': {}},
            'allow_force_pushes': {'enabled': False}, 'allow_deletions': {'enabled': False}}
    require_protection(rule)
    if problem == 'strict':
        rule['required_status_checks']['strict'] = False
    elif problem == 'admins':
        rule['enforce_admins']['enabled'] = False
    elif problem == 'bypass':
        rule['required_pull_request_reviews']['bypass_pull_request_allowances'] = {'apps': [{}]}
    elif problem == 'check':
        rule['required_status_checks']['checks'] = []
    elif problem == 'app':
        rule['required_status_checks']['checks'][0]['app_id'] = -1
    elif problem in ('force', 'delete'):
        rule['allow_force_pushes' if problem == 'force' else 'allow_deletions']['enabled'] = True
    else:
        rule['required_pull_request_reviews'] = None
    with pytest.raises(p.PromotionError):
        require_protection(rule)


def test_old_or_wrong_app_check_does_not_excuse_latest_failure():
    run = {'id': 1, 'name': REQUIRED_CHECK, 'app': {'id': ACTIONS_APP_ID}, 'head_sha': 'a'*40,
           'status': 'completed', 'conclusion': 'success'}
    require_checks([run], 'a'*40)
    with pytest.raises(p.PromotionError):
        require_checks([run], 'b'*40)
    with pytest.raises(p.PromotionError):
        require_checks([run, {**run, 'id': 2, 'conclusion': 'failure'}], 'a'*40)


def test_published_release_recovery_retains_later_dev_work(repo):
    local, server, pr, head, base = prepared(repo)
    server.fail_at = 'after-publish'
    with pytest.raises(p.PromotionError, match='interrupted'):
        flow.finish(local, server, pr['number'], head, base)
    git(local.root, 'checkout', 'dev')
    write(local.root, 'later.txt', 'Preserved later development.\n')
    later = commit(local.root, 'later work')
    git(local.root, 'merge', '--no-edit', head)
    git(local.root, 'fetch', 'origin')
    git(local.root, 'merge', '-s', 'ours', '--no-edit', 'origin/main')
    git(local.root, 'push', 'origin', 'dev')
    flow.finish(local, server, pr['number'], head, base)
    assert (local.root / 'later.txt').read_text() == 'Preserved later development.\n'
    assert git(local.root, 'merge-base', '--is-ancestor', later, 'dev') == ''
    assert not git(server.remote, 'branch', '--list', 'release/*')


def test_invalid_cli_root_is_diagnosed(tmp_path, capsys):
    assert flow.main(['--root', str(tmp_path / 'missing'), 'check']) == 1
    assert 'git branch --show-current' in capsys.readouterr().err


def test_manually_committed_failed_preparation_receives_both_checks(repo):
    local, server = repo
    def fail(*args):
        raise p.PromotionError('failed before preparation commit')
    with pytest.raises(p.PromotionError):
        flow.prepare(local, server, 'minor', fail)
    commit(local.root, 'reviewed manual recovery')
    checked = []
    def observe(git_repo, head):
        checked.append(head)
    flow.prepare(local, server, 'minor', observe)
    assert len(checked) == 2 and len(set(checked)) == 1


@pytest.mark.parametrize('prerequisite', ['protection', 'checks'])
def test_pr_readiness_refuses_before_expensive_gate(repo, prerequisite):
    local, server, pr, _, _ = prepared(repo)
    if prerequisite == 'protection':
        server.enforced = False
    else:
        server.success = False
    observed = []
    with pytest.raises(p.PromotionError):
        flow.check_pull(local, server, pr['number'], lambda *args: observed.append(args))
    assert observed == []
