"""Source links are checked once without fetching, resolving or altering citation identity."""

import pytest

from aussiefy.errors import UserError
from aussiefy.source_urls import MAX_SOURCE_URL_LENGTH, validate_source_url


@pytest.mark.parametrize("url", [
    "https://example.com/a?word=bugger&kind=idiom#meaning", "http://example.org:80/path",
    "https://example.org:443/path", "https://example.com./a", "https://bücher.de/word",
    "https://xn--bcher-kva.de/path%20with%20spaces", "https://words.example.com/",
])
def test_public_shapes_are_preserved_without_any_io(url, monkeypatch):
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: pytest.fail("no DNS is needed for shape validation"))
    assert validate_source_url(url) == url


@pytest.mark.parametrize("url", [
    None, "", 1, "example.com", "ftp://example.com/a", "https:///missing", "https://localhost/a",
    "https://printer/a", "https://printer.local/a", "https://host.internal/a", "https://host.invalid/a",
    "http://127.0.0.1/a", "https://8.8.8.8/a", "https://[::1]/", "https://[2001:4860:4860::8888]/",
    "https://person@example.com/a", "https://:secret@example.com/a", "https://@example.com/a",
    "http://example.com:443/a", "https://example.com:444/a", "https://example.com:99999/a",
    "https://example.com:words/a", "https://example.com/a b", "https://example.com/a\nb",
    "https://example.com/\x00", "https://example.com/\u200b", "https://example..com/a", "https://example.com../a",
    "https://-bad.example.com/a", "https://example.com\\bad/a", "https://%65xample.com/a",
    "https://2130706433/", "https://0x7f.0.0.1/", "https://example.123/a",
    "https://" + "a" * 64 + ".com/", "https://example.com/" + "a" * MAX_SOURCE_URL_LENGTH,
])
def test_invalid_source_shapes_raise_a_user_error(url):
    with pytest.raises(UserError):
        validate_source_url(url)
