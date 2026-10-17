"""Declared page encodings and the reviewed seed intake's semantic boundaries."""
import hashlib
import importlib
from pathlib import Path

import pytest
import requests
import yaml

from aussiefy.loader import load_dictionary

fetcher = importlib.import_module('aussiefy.scrape.fetch')
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('content_type,body,expected', [
    ('text/html', '<meta charset="UTF-8"><p>She’ll be right.</p>'.encode(),
     '<meta charset="UTF-8"><p>She’ll be right.</p>'),
    ('text/html', b'<meta charset="windows-1252"><p>caf\xe9</p>',
     '<meta charset="windows-1252"><p>café</p>'),
    ('text/html; CHARSET=windows-1252', b'<meta charset="UTF-8"><p>caf\xe9</p>',
     '<meta charset="UTF-8"><p>café</p>'),
    ('text/plain; charset=utf-8', '# Café\r\n`code`\r\n'.encode(), '# Café\r\n`code`\r\n'),
    ('text/html', b'', ''),
])
def test_fetch_respects_http_or_declared_html_encoding_and_caches_the_decoded_text(
        content_type, body, expected, tmp_path, monkeypatch):
    response = requests.Response()
    response.status_code = 200
    response.headers['Content-Type'] = content_type
    response._content = body
    response.encoding = requests.utils.get_encoding_from_headers(response.headers)
    calls = []
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: calls.append(a) or response)
    url = 'https://example.test/seed'
    assert fetcher.fetch(url, cache_dir=tmp_path, delay=0) == expected
    assert fetcher.fetch(url, cache_dir=tmp_path, delay=0) == expected
    assert len(calls) == 1
    assert (tmp_path / (hashlib.sha1(url.encode()).hexdigest()+'.html')).read_bytes() == expected.encode()


def test_seed_ledger_is_complete_and_promoted_entries_are_real():
    ledger = yaml.safe_load((ROOT/'research/maintenance-2026-10-17/seed-decisions.yaml').read_text())
    rows = ledger['decisions']
    assert len(rows) == ledger['normalised_candidates'] == 212
    assert [row['row'] for row in rows] == list(range(212))
    assert all(row['reason'] for row in rows)
    dictionary = load_dictionary()
    for row in rows:
        if 'target' in row:
            assert row['target'] in dictionary.entries
        if row['decision'] == 'entry':
            assert dictionary.entries[row['target']].status == 'active'
    assert rows[32]['target'] == 'g-ya-galah'  # Component/tag coverage, not a noun replacement.
    assert rows[99]['decision'] == rows[173]['decision'] == 'retain_craft'


@pytest.mark.parametrize('source,concept', [
    ('He rushed around frantically.', 'FRANTIC_ACTIVITY'),
    ('They lived on very little.', 'FRUGAL_LIVING'),
    ('He was brazen.', 'BRAZEN'),
])
def test_precise_new_seed_senses_have_usable_forms(source, concept, translator):
    result = translator.translate(source, level=5, vulgarity=2, variety=1,
        document_type='custom', document_config={'profile':{'substitution':{'idiom':1}}})
    assert any(s.substituted and concept in s.det.concepts for s in result.records), result.text


@pytest.mark.parametrize('source', ['He was busy.', 'They were poor.', 'He was arrogant.',
    'The server was brazen.', 'It runs on very little fuel.', 'They lived on very little money.'])
def test_seed_precision_does_not_infer_new_specific_senses(source, translator):
    result = translator.translate(source, document_type='custom')
    assert not any(s.substituted and set(s.det.concepts) & {'FRANTIC_ACTIVITY','FRUGAL_LIVING','BRAZEN'}
                   for s in result.records)
