"""Extract (phrase, meaning, usage) rows from listicle-style slang pages.

Handles the common layouts:
  * tables with a header row (Saying | Meaning | Usage, in any order or naming)
  * list items of the form "Phrase - meaning" / "Phrase: meaning"
  * numbered headings ("12. Flat out like a lizard drinking") followed by a paragraph
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PHRASE_HEADERS = ("saying", "phrase", "slang", "expression", "idiom", "term", "word")
MEANING_HEADERS = ("meaning", "definition", "translation", "means", "explanation")
USAGE_HEADERS = ("usage", "example", "use", "in a sentence", "context")
SEPARATOR_RE = re.compile(r"^\s*[\"“]?(.{2,80}?)[\"”]?\s*(?:\s[-–—]\s|:\s)\s*(.+)$")
NUMBERED_RE = re.compile(r"^\s*\d{1,3}[.)]\s+[\"“]?(.+?)[\"”]?\s*$")


@dataclass
class RawPhrase:
    phrase: str
    meaning: str
    usage: str
    url: str
    section: str = ""


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().strip("“”\"")


def _column(headers: list[str], keys: tuple[str, ...]) -> int | None:
    for i, h in enumerate(headers):
        if any(k in h for k in keys):
            return i
    return None


def _section_of(node) -> str:
    heading = node.find_previous(["h2", "h3"])
    return _clean(heading.get_text()) if heading else ""


def extract_phrases(html: str, url: str) -> list[RawPhrase]:
    from bs4 import BeautifulSoup  # optional dependency: pip install aussiefy[scrape]

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    out: list[RawPhrase] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [_clean(c.get_text()).lower() for c in rows[0].find_all(["th", "td"])]
        p_col = _column(header_cells, PHRASE_HEADERS)
        m_col = _column(header_cells, MEANING_HEADERS)
        u_col = _column(header_cells, USAGE_HEADERS)
        body = rows[1:] if p_col is not None or m_col is not None else rows
        p_col = 0 if p_col is None else p_col
        m_col = 1 if m_col is None else m_col
        section = _section_of(table)
        for row in body:
            cells = [_clean(c.get_text()) for c in row.find_all(["td", "th"])]
            if len(cells) <= max(p_col, m_col):
                continue
            usage = cells[u_col] if u_col is not None and u_col < len(cells) else ""
            if cells[p_col]:
                out.append(RawPhrase(cells[p_col], cells[m_col], usage, url, section))

    if not out:
        for li in soup.find_all("li"):
            m = SEPARATOR_RE.match(_clean(li.get_text()))
            if m:
                out.append(RawPhrase(_clean(m.group(1)), _clean(m.group(2)), "", url, _section_of(li)))
        for h in soup.find_all(["h2", "h3", "h4"]):
            m = NUMBERED_RE.match(_clean(h.get_text()))
            if m:
                para = h.find_next_sibling("p")
                out.append(RawPhrase(_clean(m.group(1)), _clean(para.get_text()) if para else "", "", url))
    return out
