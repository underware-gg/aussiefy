"""Scrape-and-flag pipeline: fetch -> parse -> normalise/merge -> LLM tag -> human review.

Only phrases are extracted. Source meanings are kept in staging files so the
tagger has context, but they never reach the dictionary: the `gloss` there is
always written fresh.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..errors import UserError
from ..model import Dictionary


class ReferenceOnly(Exception):
    """A source data/source_policy.yaml lists as reference-only: verify entries against it by hand, but don't
    extract from it without permission."""


def scrape(sources: list[str], dictionary: Dictionary, existing: list | None = None, *, source_url: str | None = None,
           permitted: bool = False, refresh: bool = False, log: Callable[[str], None] = print) -> list:
    """Extract phrases from URLs or saved HTML files and merge them into the staged phrases (`existing`), checked
    against the dictionary. A saved file needs source_url, the page it was saved from: it is what the source
    policy is checked against and what the phrases record. Raises ReferenceOnly for a reference-only source
    unless permitted."""
    from .fetch import fetch, reference_only
    from .normalise import merge
    from .parse import extract_phrases

    raw = []
    for src in sources:
        local = "://" not in src
        if local and not Path(src).is_file():
            raise UserError(f"no such file: {src}")
        if local and not source_url:
            raise UserError(f"{src} is a saved page: give the URL it was saved from (source URL), so the source "
                            "policy can be checked")
        page = source_url or src
        for url in dict.fromkeys([page] if local else [src, page]):
            reason = reference_only(url)
            if reason and not permitted:
                raise ReferenceOnly(f"refusing {src}: reference-only source ({reason})")
        html = Path(src).read_text(encoding="utf-8") if local else fetch(src, refresh=refresh)
        found = extract_phrases(html, page)
        log(f"{src}: {len(found)} phrases")
        raw.extend(found)
    return merge(raw, dictionary, existing)
