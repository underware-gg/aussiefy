"""Observe gh REST request contracts while substituting only process/network responses."""

import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import promotion_github as api  # noqa: E402
from promotion import Release, PromotionError  # noqa: E402
import promote  # noqa: E402


def test_merge_uses_expected_head_squash_and_exact_provenance(monkeypatch, tmp_path):
    requests = []
    def execute(cmd, **kwargs):
        requests.append((cmd, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({'merged': True, 'sha': 'm'*40}), stderr='')
    monkeypatch.setattr(api.subprocess, 'run', execute)
    gh = api.GitHub(tmp_path, 'owner/repo')
    rel = Release('1.0.0', '0.1.0', 'a'*40, 'b'*40, '- Published prose.')
    assert gh.merge(7, rel) == 'm'*40
    cmd, kwargs = requests[0]
    assert cmd[:3] == ['gh', 'api', 'repos/owner/repo/pulls/7/merge']
    assert cmd[3:] == ['--method', 'PUT', '--input', '-']
    assert kwargs['cwd'] == tmp_path
    body = json.loads(kwargs['input'])
    assert body['sha'] == rel.source and body['merge_method'] == 'squash'
    assert body['commit_title'] == 'Release v1.0.0'
    assert body['commit_message'] == '- Published prose.\n\nPromoted-From: ' + rel.source


@pytest.mark.parametrize('status', [403, 404, 422])
def test_only_explicit_404_is_optional_absence(monkeypatch, tmp_path, status):
    monkeypatch.setattr(api.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1, stdout='{}', stderr=f'gh: refused (HTTP {status})'))
    gh = api.GitHub(tmp_path, 'owner/repo')
    if status == 404:
        assert gh.release('v1.0.0') is None
    else:
        with pytest.raises(api.GitHubError) as caught:
            gh.release('v1.0.0')
        assert caught.value.status == status


def test_pagination_retains_all_check_pages(monkeypatch, tmp_path):
    calls = []
    run = {'id': 1, 'name': api.REQUIRED_CHECK, 'head_sha': 'a'*40, 'app': {'id': api.ACTIONS_APP_ID},
           'status': 'completed', 'conclusion': 'success'}
    def execute(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout=json.dumps([{'check_runs': []}, {'check_runs': [run]}]), stderr='')
    monkeypatch.setattr(api.subprocess, 'run', execute)
    api.GitHub(tmp_path, 'owner/repo').checks('a'*40)
    assert calls[0][-2:] == ['--paginate', '--slurp']


def test_configure_checks_availability_before_settings_and_verifies_readback(monkeypatch, tmp_path):
    calls = []
    rule = {'required_status_checks': {'strict': True, 'checks': [{'context': api.REQUIRED_CHECK, 'app_id': api.ACTIONS_APP_ID}]},
            'enforce_admins': {'enabled': True}, 'required_pull_request_reviews': {'bypass_pull_request_allowances': {}},
            'allow_force_pushes': {'enabled': False}, 'allow_deletions': {'enabled': False}}
    def execute(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if len(calls) == 1:
            return SimpleNamespace(returncode=1, stdout='{}', stderr='HTTP 404')
        return SimpleNamespace(returncode=0, stdout=json.dumps(rule), stderr='')
    monkeypatch.setattr(api.subprocess, 'run', execute)
    api.GitHub(tmp_path, 'owner/repo').configure()
    assert len(calls) == 3
    body = json.loads(calls[1][1]['input'])
    assert body['required_status_checks']['strict'] and body['enforce_admins']
    assert body['required_pull_request_reviews']['bypass_pull_request_allowances'] == {'users': [], 'teams': [], 'apps': []}
    assert calls[2][0][-1] == 'GET'


def test_configure_does_not_overwrite_incompatible_existing_protection(monkeypatch, tmp_path):
    calls = []
    def execute(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout='{}', stderr='')
    monkeypatch.setattr(api.subprocess, 'run', execute)
    with pytest.raises(PromotionError):
        api.GitHub(tmp_path, 'owner/repo').configure()
    assert len(calls) == 1 and '--input' not in calls[0]


def test_rooted_cli_removes_direct_main_release_command(tmp_path):
    with pytest.raises(SystemExit) as caught:
        promote.main(['--root', str(tmp_path), 'release'])
    assert caught.value.code == 2


def test_ci_check_is_associated_with_actual_release_push_head():
    path = Path(__file__).resolve().parents[2] / '.github/workflows/release.yml'
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert workflow['on'] == {'push': {'branches': ['release/v*']}}
    assert workflow['permissions'] == {'contents': 'read'}
    job = workflow['jobs']['release-head']
    assert job['name'] == api.REQUIRED_CHECK
    checkout = job['steps'][0]['with']
    assert checkout['ref'] == '${{ github.sha }}' and checkout['fetch-depth'] == '0'
    assert checkout['persist-credentials'] == 'false'
    verification = job['steps'][-1]
    assert verification['env']['RELEASE_HEAD'] == '${{ github.sha }}'
    assert '--head "$RELEASE_HEAD" --base origin/main --branch "$RELEASE_BRANCH"' in verification['run']
