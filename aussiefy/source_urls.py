"""One offline source-link shape check shared by dictionary loading and submission clients."""

from __future__ import annotations

import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit

from .errors import UserError

MAX_SOURCE_URL_LENGTH = 2048
INTERNAL_SUFFIXES = {"localhost", "local", "internal", "test", "invalid", "example", "home", "lan", "onion"}
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def validate_source_url(url: str) -> str:
    """Return the unchanged HTTP(S) citation, or raise UserError for an invalid link shape.

    This never fetches a URL, resolves DNS or certifies its content or eventual destination.
    """
    if not isinstance(url, str) or not url or len(url) > MAX_SOURCE_URL_LENGTH:
        raise UserError(f"source URL must be non-empty text of at most {MAX_SOURCE_URL_LENGTH} characters")
    if any(char.isspace() or unicodedata.category(char).startswith("C") for char in url):
        raise UserError("source URL must not contain spaces or control characters")
    try:
        parsed = urlsplit(url)
        host, port = parsed.hostname, parsed.port
    except ValueError as exc:
        raise UserError("malformed source URL") from exc
    if parsed.scheme not in {"http", "https"} or not host:
        raise UserError("source URL must be HTTP(S) with a public host name")
    if parsed.username is not None or parsed.password is not None:
        raise UserError("source URL must not contain a user name or password")
    if port is not None and port != {"http": 80, "https": 443}[parsed.scheme]:
        raise UserError("source URL must use its scheme's default port")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise UserError("source URL must name a public host, not an IP address")
    try:
        ascii_host = (host[:-1] if host.endswith(".") else host).encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise UserError("source URL has an invalid host name") from exc
    labels = ascii_host.split(".")
    if (len(ascii_host) > 253 or len(labels) < 2 or any(not LABEL.fullmatch(label) for label in labels)
            or not re.fullmatch(r"(?:[a-z]{2,63}|xn--[a-z0-9-]+)", labels[-1])
            or labels[-1] in INTERNAL_SUFFIXES):
        raise UserError("source URL must use a public host name, not a single-label or internal name")
    return url
