"""Pinned Interfold ingestion uses the shared cache and atomic ordinary-file persistence."""

import importlib
from pathlib import Path

import pytest
import requests
import yaml

from aussiefy.scrape.ingest import Manifest, ingest
from aussiefy.errors import UserError

fetcher = importlib.import_module('aussiefy.scrape.fetch')
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def manifest(tmp_path):
    data = yaml.safe_load((ROOT / 'tests/corpus/everyday/interfold.yaml').read_text())
    data['items'] = data['items'][:2]
    data['out'] = 'out'
    path = tmp_path / 'manifest.yaml'
    path.write_text(yaml.safe_dump(data))
    return Manifest.load(path)


def test_pinned_pages_are_verbatim_cached_and_skipped_when_present(manifest, tmp_path, monkeypatch):
    text = '# Example\r\n\r\nimport X from "x"\r\n<Callout>Words.</Callout>\r\n`code`'
    calls = []

    class Response:
        def raise_for_status(self):
            return None

    def get(url, **kwargs):
        calls.append((url, kwargs))
        response = Response()
        response.text = text
        return response

    monkeypatch.setattr(requests, 'get', get)
    fetch = lambda url: fetcher.fetch(url, cache_dir=tmp_path / 'cache', delay=0)
    outcomes = ingest(manifest, fetch)
    assert [o.status for o in outcomes] == ['saved', 'saved']
    assert [url for url, _ in calls] == [s.url for s in manifest.sources]
    assert all(k['headers']['User-Agent'] == fetcher.USER_AGENT for _, k in calls)
    assert all(o.path.read_bytes() == text.encode() for o in outcomes)
    assert all(o.status == 'present' for o in ingest(manifest, fetch))
    for o in outcomes:
        o.path.unlink()
    assert all(o.status == 'saved' for o in ingest(manifest, fetch))
    assert len(calls) == 2


def test_page_failure_does_not_block_other_pages(manifest):
    def fetch(url):
        if url == manifest.sources[0].url:
            raise fetcher.FetchError('offline')
        return 'Complete page.\n'

    outcomes = ingest(manifest, fetch)
    assert [o.status for o in outcomes] == ['failed', 'saved']
    assert not outcomes[0].path.exists()
    assert outcomes[1].path.read_text() == 'Complete page.\n'


@pytest.mark.parametrize('source_path', ['../outside.mdx', '/outside.mdx', 'docs/../../outside.mdx'])
def test_invalid_repository_paths_fail_before_fetch(manifest, source_path):
    data = yaml.safe_load(manifest.path.read_text())
    data['items'][0]['path'] = source_path
    manifest.path.write_text(yaml.safe_dump(data))
    with pytest.raises(UserError, match='repository-relative'):
        Manifest.load(manifest.path)


@pytest.mark.parametrize('existing', ['symlink', 'directory'])
def test_nonordinary_page_is_failed_before_fetch(manifest, tmp_path, existing):
    manifest.out.mkdir()
    page = manifest.out / manifest.sources[0].filename
    outside = tmp_path / 'outside'
    outside.write_text('Untouched.\n')
    page.symlink_to(outside) if existing == 'symlink' else page.mkdir()
    calls = []
    outcomes = ingest(manifest, lambda url: calls.append(url) or 'Complete page.\n')
    assert [o.status for o in outcomes] == ['failed', 'saved']
    assert calls == [manifest.sources[1].url] and outside.read_text() == 'Untouched.\n'


@pytest.mark.parametrize('refresh', [False, True])
def test_interrupted_page_save_is_atomic_and_a_repeat_recovers(manifest, monkeypatch, refresh):
    manifest.out.mkdir()
    page = manifest.out / manifest.sources[0].filename
    if refresh:
        page.write_text('Previous complete page.\n')
    real = fetcher.tempfile.NamedTemporaryFile

    class FailingWrite:
        def __init__(self, **kwargs):
            self.saved = real(**kwargs)
            self.name = self.saved.name

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.saved.close()

        def write(self, data):
            self.saved.write(data[:4])
            raise OSError('disk full during save')

    monkeypatch.setattr(fetcher.tempfile, 'NamedTemporaryFile', FailingWrite)
    failed = ingest(manifest, lambda url: 'Complete new page.\n', force=refresh)
    assert all(o.status == 'failed' and 'disk full' in o.error for o in failed)
    assert not list(manifest.out.glob('.*'))
    assert page.read_text() == 'Previous complete page.\n' if refresh else not page.exists()
    monkeypatch.setattr(fetcher.tempfile, 'NamedTemporaryFile', real)
    outcomes = ingest(manifest, lambda url: 'Complete new page.\n', force=refresh)
    assert all(o.status == 'saved' for o in outcomes)
    assert all(o.path.read_text() == 'Complete new page.\n' for o in outcomes)


@pytest.mark.parametrize('refresh', [False, True])
def test_interrupted_fetch_cache_save_never_creates_a_completed_page(manifest, tmp_path, monkeypatch, refresh):
    import hashlib

    cache = tmp_path / 'cache'
    cache.mkdir()
    cached = cache / (hashlib.sha1(manifest.sources[0].url.encode()).hexdigest() + '.html')
    if refresh:
        cached.write_text('Previous complete page.\n')
    calls = []

    class Response:
        text = 'Complete new page.\n'

        def raise_for_status(self):
            return None

    def get(url, **kwargs):
        calls.append(url)
        return Response()

    real = fetcher.tempfile.NamedTemporaryFile

    class FailingWrite:
        def __init__(self, **kwargs):
            self.saved = real(**kwargs)
            self.name = self.saved.name

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.saved.close()

        def write(self, data):
            self.saved.write(data[:4])
            raise OSError('disk full during cache save')

    monkeypatch.setattr(requests, 'get', get)
    monkeypatch.setattr(fetcher.tempfile, 'NamedTemporaryFile', FailingWrite)
    fetch = lambda url: fetcher.fetch(url, cache_dir=cache, delay=0, refresh=refresh)
    failed = ingest(manifest, fetch)
    assert all(o.status == 'failed' and 'fetch cache' in o.error for o in failed)
    assert not list(cache.glob('.*')) and not list(manifest.out.iterdir())
    assert cached.read_text() == 'Previous complete page.\n' if refresh else not cached.exists()
    monkeypatch.setattr(fetcher.tempfile, 'NamedTemporaryFile', real)
    recovered = ingest(manifest, fetch)
    assert all(o.status == 'saved' for o in recovered)
    assert all(o.path.read_text() == Response.text for o in recovered)
    assert len(calls) == 4
