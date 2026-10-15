"""Source ingestion: a manifest of sources in, local text files the corpus and tests read out.

A manifest is YAML:

    out: ../local/everyday/news          # where the files go, relative to the manifest
    defaults: {repo: owner/name, ref: <commit>}   # optional, merged into every item
    items:
      - name: some_page                  # the file's name, without extension
        url: https://example.org/page    # an HTML page: its readable text, cut between start and end
        start: "First words"             # optional, inclusive
        end: "last words."
      - name: getting_started
        path: docs/pages/start.mdx       # a file in a GitHub repo (repo and ref from defaults or the item)

Any other keys (title, licence, genre ...) are the corpus's metadata and pass through untouched.

An HTML page becomes plain text, paragraphs separated by blank lines (`.txt`). A raw file (a repo path, or a
URL ending .md, .mdx or .txt) is kept verbatim, including line endings; its extension says what it is, so a
`.mdx` page is translated with markup="mdx". The conversion is pure (convert); the network is one injected
function (ingest's fetch), so both are tested without it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import urlsplit

import yaml

from ..errors import UserError
from .fetch import FetchError, save_text

RAW_GITHUB = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
RAW_SUFFIXES = (".md", ".mdx", ".markdown", ".txt")
BREAK = "\x00"   # stands in for <br> while whitespace is collapsed


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    raw: bool                       # a file kept verbatim, not an HTML page
    suffix: str                     # the saved file's extension
    start: str | None = None
    end: str | None = None

    @classmethod
    def from_item(cls, item: dict, defaults: dict) -> "Source":
        item = {**defaults, **item}
        if "name" not in item:
            raise UserError(f"a manifest item has no name: {item}")
        name = item["name"]
        if not isinstance(name, str) or not name.strip() or name in (".", "..") or any(c in name for c in ("/", "\\", "\0", "\r", "\n")):
            raise UserError(f"source name must be a non-empty filename stem, got {name!r}")
        if "path" in item:
            if not item.get("repo") or not item.get("ref"):
                raise UserError(f"{item['name']}: a repo path needs repo and ref (in the item or defaults)")
            path = item["path"]
            if not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path:
                raise UserError(f"{name}: expected a normalised repository-relative source path")
            url = RAW_GITHUB.format(repo=item["repo"], ref=item["ref"], path=item["path"])
        elif "url" in item:
            url = item["url"]
        else:
            raise UserError(f"{item['name']}: give a url or a repo path")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
        except ValueError as exc:
            raise UserError(f"{name}: invalid source URL: {exc}") from exc
        if parsed is None or parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise UserError(f"{name}: expected an HTTP(S) source URL")
        for key in ("start", "end"):
            if key in item and (not isinstance(item[key], str) or not item[key].strip()):
                raise UserError(f"{name}: {key} must be a non-empty text marker")
        if ("start" in item) != ("end" in item):
            raise UserError(f"{item['name']}: give both start and end markers, or neither")
        suffix = Path(url.split("?")[0]).suffix.lower()
        raw = suffix in RAW_SUFFIXES or "path" in item
        return cls(item["name"], url, raw, suffix if raw and suffix else ".txt", item.get("start"), item.get("end"))

    @property
    def filename(self) -> str:
        return self.name + self.suffix


@dataclass(frozen=True)
class Manifest:
    path: Path
    out: Path
    sources: list[Source]

    @classmethod
    def load(cls, path: str | Path, *, ref: str | None = None) -> "Manifest":
        """ref overrides the manifest's pinned git ref (e.g. "main" for the current docs)."""
        path = Path(path)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise UserError(f"{path}: could not read ingest manifest: {exc}") from exc
        if not isinstance(data, dict) or "items" not in data or "out" not in data:
            raise UserError(f"{path}: a manifest needs `out` and `items` (see aussiefy.scrape.ingest)")
        if not isinstance(data["items"], list) or not data["items"] or any(not isinstance(item, dict) for item in data["items"]):
            raise UserError(f"{path}: items must be a non-empty list of mappings")
        if not isinstance(data["out"], str) or not data["out"].strip() or not isinstance(data.get("defaults", {}), dict):
            raise UserError(f"{path}: out must be a directory name and defaults a mapping")
        defaults = {**(data.get("defaults") or {}), **({"ref": ref} if ref else {})}
        sources = [Source.from_item({**item, **({"ref": ref} if ref else {})}, defaults)
                   for item in data["items"]]
        if len({source.filename for source in sources}) != len(sources):
            raise UserError(f"{path}: duplicate output filenames")
        return cls(path, (path.parent / data["out"]).resolve(), sources)


def html_to_text(html: str) -> str:
    """Visible text with paragraph breaks kept as blank lines (and <br> line breaks, for verse)."""
    from bs4 import BeautifulSoup  # optional dependency: pip install aussiefy[scrape]

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with(BREAK)
    blocks = []
    for el in soup.find_all(["p", "blockquote", "li", "h1", "h2", "h3", "pre"]):
        if el.find(["p", "blockquote", "li"]):
            continue  # only leaf blocks, so text isn't duplicated
        if el.name == "pre":
            text = el.get_text().replace(BREAK, "\n").strip()
        else:
            # a newline in the HTML source is just a space; only <br> breaks a line (verse), and the
            # non-breaking spaces poems are indented with are dropped
            text = re.sub(r"\s+", " ", el.get_text())
            text = "\n".join(line.strip() for line in text.split(BREAK)).strip()
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def excerpt(text: str, start: str, end: str) -> str:
    """The text from start through end (curly apostrophes straightened first, so markers can be typed)."""
    norm = text.replace("’", "'").replace("​", "")
    i = norm.find(start)
    if i < 0:
        raise ValueError(f"start marker {start!r} not found")
    j = norm.find(end, i)
    if j < 0:
        raise ValueError(f"end marker {end!r} not found after the start")
    return norm[i:j + len(end)].strip() + "\n"


def convert(source: Source, body: str) -> str:
    """What gets saved for a fetched body: a raw file verbatim (including line endings), a page's readable text;
    either cut between the markers when it has them."""
    text = body if source.raw else html_to_text(body)
    if source.start:   # Source.from_item makes sure there's an end too
        return excerpt(text, source.start, source.end)
    return text if source.raw or text.endswith("\n") else text + "\n"


@dataclass(frozen=True)
class Outcome:
    source: Source
    path: Path
    status: str                     # "saved", "present" or "failed"
    words: int = 0
    error: str = ""


def ingest(manifest: Manifest, fetch: Callable[[str], str], *, force: bool = False) -> list[Outcome]:
    """Fetch and convert every source in the manifest into manifest.out. A file already there is kept unless
    force. One source failing (network, markers moved) doesn't stop the rest; its Outcome says why."""
    manifest.out.mkdir(parents=True, exist_ok=True)
    outcomes = []
    for source in manifest.sources:
        path = manifest.out / source.filename
        if path.is_symlink() or path.is_dir():
            outcomes.append(Outcome(source, path, "failed", error="output must be an ordinary file"))
            continue
        if path.exists() and not force:
            outcomes.append(Outcome(source, path, "present"))
            continue
        try:
            text = convert(source, fetch(source.url))
        except (FetchError, ValueError) as exc:   # the network, or markers the page no longer has: carry on
            outcomes.append(Outcome(source, path, "failed", error=f"{type(exc).__name__}: {exc}"))
            continue
        if path.is_symlink():
            raise UserError(f"{path}: output must be an ordinary file")
        try:
            save_text(path, text)
        except (UserError, OSError) as exc:
            outcomes.append(Outcome(source, path, "failed", error=str(exc)))
            continue
        outcomes.append(Outcome(source, path, "saved", len(text.split())))
    return outcomes
