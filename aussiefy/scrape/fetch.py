"""Polite, cached page fetching."""

from __future__ import annotations

import hashlib
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from .. import claude
from ..errors import UserError
from ..loader import DATA_DIR


def reference_only(url: str, data_dir: Path | None = None) -> str | None:
    """The reason a URL may not be bulk-scraped (see data/source_policy.yaml), or None. A rule matches when its
    domain is a whole run of labels in the URL's host, in any case: the domain and its subdomains, and for a bare
    label such as "australiannationaldictionary", any host with that label."""
    import yaml

    host = urlsplit(url).hostname or urlsplit(f"//{url}").hostname or ""   # with a scheme, or without one
    path = (data_dir or DATA_DIR) / "source_policy.yaml"
    try:
        policy = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise UserError(f"{path}: could not read source policy: {exc}") from exc
    if not isinstance(policy, dict) or not isinstance(policy.get("reference_only"), list):
        raise UserError(f"{path}: source policy must contain a reference_only list")
    for rule in policy["reference_only"]:
        if not isinstance(rule, dict) or not isinstance(rule.get("domain"), str) or not re.fullmatch(
                r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*", rule["domain"].strip(".")):
            raise UserError(f"{path}: each reference_only rule needs a non-empty domain")
        if not isinstance(rule.get("reason"), str) or not rule["reason"].strip():
            raise UserError(f"{path}: each reference_only rule needs a non-empty reason")
        if f".{rule['domain'].lower().strip('.')}." in f".{host}.":
            return " ".join(str(rule.get("reason", "")).split())
    return None


class FetchError(Exception):
    """A page that couldn't be fetched: the network, or the server's answer."""


USER_AGENT = "aussiefy-scraper/0.1 (+https://github.com/underware-gg/aussiefy; phrase research)"
_last_fetch = 0.0


def save_text(path: Path, text: str) -> None:
    """Atomically save verbatim fetched text, so failed writes never become completed inputs."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as saved:
            temporary = Path(saved.name)
            saved.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fetch(url: str, cache_dir: str | Path | None = None, delay: float = 2.0, refresh: bool = False) -> str:
    """The page at url, from the cache (cache_dir, default cache/scrape under the aussiefy home) unless refresh."""
    cache = Path(cache_dir) if cache_dir else claude.default_cache_dir("scrape")
    path = cache / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    try:
        cache.mkdir(parents=True, exist_ok=True)
        if path.exists() and not refresh:
            with path.open(encoding="utf-8", newline="") as saved:
                return saved.read()
    except (OSError, UnicodeError) as exc:
        raise FetchError(f"{path}: could not read fetch cache: {exc}") from exc

    import requests  # optional dependency: pip install aussiefy[scrape]

    global _last_fetch
    wait = delay - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"{url}: {exc}") from exc
    finally:
        _last_fetch = time.monotonic()
    content_type = resp.headers.get("Content-Type", "")
    if (content_type.split(";", 1)[0].strip().lower() in {"text/html", "application/xhtml+xml"}
            and not re.search(r";\s*charset\s*=", content_type, re.I)):
        from bs4 import UnicodeDammit

        # requests defaults text/html to Latin-1 even when the page declares UTF-8 in a meta tag.
        # An explicit HTTP charset remains authoritative; non-HTML responses keep requests' decoding.
        resp.encoding = UnicodeDammit(resp.content, is_html=True).original_encoding
    try:
        save_text(path, resp.text)
    except OSError as exc:
        raise FetchError(f"{path}: could not save fetch cache: {exc}") from exc
    return resp.text
