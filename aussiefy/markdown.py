"""Translate Markdown source spans; never render a parsed document back to source."""

from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
import re
import unicodedata

from .engine import Result, Translator
from .genre import Genre, Embellishment
from .policy import Effective, Policy, envelope


@dataclass(frozen=True)
class ProseSpan:
    start: int
    end: int


@dataclass(frozen=True)
class ProseUnit:
    source_span: tuple[int, int]
    output_span: tuple[int, int]
    text: str
    result: Result

    def to_dict(self) -> dict:
        return {"source_span": list(self.source_span), "output_span": list(self.output_span),
                "text": self.text, "result": self.result.to_dict()}


@dataclass(frozen=True)
class ProtectedSpan:
    source_span: tuple[int, int]
    output_span: tuple[int, int]

    def to_dict(self) -> dict:
        return {"source_span": list(self.source_span), "output_span": list(self.output_span)}


@dataclass
class DocumentResult:
    text: str
    source: str
    level: int
    seed: int
    vulgarity: int
    variety: int
    warnings: list[str]
    units: list[ProseUnit]
    protected: list[ProtectedSpan]
    genre: Genre
    english: str | None
    embellishment: Embellishment

    def envelope(self) -> dict:
        return envelope(self.level, self.vulgarity, self.warnings)

    def to_dict(self) -> dict:
        return {"format": "markdown", "text": self.text, "source": self.source, **self.envelope(),
                "seed": self.seed, "variety": self.variety, "units": [u.to_dict() for u in self.units],
                "protected": [p.to_dict() for p in self.protected],
                "genre": self.genre.name, "genre_scores": self.genre.scores, "english": self.english,
                "embellishment": self.embellishment.step, "embellishment_name": self.embellishment.name}


def _merged(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if start == end:
            continue
        if result and start <= result[-1][1]:
            result[-1] = result[-1][0], max(end, result[-1][1])
        else:
            result.append((start, end))
    return result


def _without(start: int, end: int, protected: list[tuple[int, int]], first: int):
    for i in range(first, len(protected)):
        left, right = protected[i]
        if right <= start:
            continue
        if left >= end:
            break
        if left > start:
            yield start, left
        start = max(start, right)
        if start >= end:
            return
    if start < end:
        yield start, end


def _closing(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == opening:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def html_tag_pattern():
    """Match parser-recognised HTML tags and comments at source positions."""
    from markdown_it.common.html_re import HTML_TAG_RE

    # The parser matches a sliced suffix. Remove only its start anchor to match at source positions.
    return re.compile(HTML_TAG_RE.pattern.removeprefix("^"), HTML_TAG_RE.flags)


def _inline_protected(text: str, parser) -> list[tuple[int, int]]:
    """Retain complete links/code and ambiguous unclosed syntax, including across lines."""
    spans = []
    special_pattern = re.compile(r"(?:https?://[^\s<>]+|&(?:#[xX][0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);)")
    from markdown_it.helpers import parseLinkLabel
    from markdown_it.rules_inline.state_inline import StateInline
    from markdown_it.rules_inline.autolink import AUTOLINK_RE, EMAIL_RE
    tags = html_tag_pattern()
    state = StateInline(text, parser, {}, [])
    ticks = re.compile(r"`+")
    i = 0
    while i < len(text):
        start = i
        char = text[i]
        if char == "\\":
            i = min(i + 2, len(text))
        elif char == "`":
            run = ticks.match(text, i)[0]
            close = re.compile(r"(?<!`)" + re.escape(run) + r"(?!`)").search(text, i + len(run))
            i = close.end() if close else len(text)
        elif char == "[" or (char == "!" and text[i:i + 2] == "!["):
            label = i + (char == "!")
            close = parseLinkLabel(state, label)
            if close < 0:
                i = len(text)
            else:
                end = close + 1
                after = end
                while after < len(text) and text[after].isspace():
                    after += 1
                if after < len(text) and text[after] in "([":
                    end = inline_link_end(text, after) if text[after] == "(" else _closing(text, after, "[", "]")
                    i = end if end is not None else len(text)
                else:
                    i = end
        elif char == "<":
            match = tags.match(text, i)
            if match:
                i = _html_region_end(text, i, match.end())
            else:
                angle_end = text.find(">", i + 1)
                content = text[i + 1:angle_end] if angle_end >= 0 else ""
                if angle_end >= 0 and (AUTOLINK_RE.fullmatch(content) or EMAIL_RE.fullmatch(content)):
                    i = angle_end + 1
                else:
                    i = len(text)
        elif char == "{":
            end = _closing(text, i, "{", "}")
            i = end if end is not None else len(text)
        elif char in "*_~":
            i += 1
        else:
            special = special_pattern.match(text, i)
            if special:
                i += len(special[0])
            else:
                i += 1
                continue
        spans.append((start, i))
    return _merged(spans)


def inline_link_end(text: str, opening: int) -> int | None:
    """Use the parser's destination/title boundaries, including quotes and escaped parentheses."""
    from markdown_it.helpers import parseLinkDestination, parseLinkTitle

    pos = opening + 1
    while pos < len(text) and text[pos].isspace():
        pos += 1
    destination = parseLinkDestination(text, pos, len(text))
    if destination.ok:
        pos = destination.pos
        space_start = pos
        while pos < len(text) and text[pos].isspace():
            pos += 1
        title = parseLinkTitle(text, pos, len(text))
        if pos != space_start and title.ok:
            pos = title.pos
            while pos < len(text) and text[pos].isspace():
                pos += 1
    return pos + 1 if pos < len(text) and text[pos] == ")" else None


def _prefix(body: str) -> int:
    """Retain indentation and list/quote container markers on each physical source line."""
    i = 0
    while True:
        while i < len(body) and body[i] in " \t":
            i += 1
        marker = re.match(r"(?:>[ \t]?|(?:[-+*]|\d{1,9}[.)])[ \t]+)", body[i:])
        if not marker:
            return i
        i += len(marker[0])


def _word_adjacent_delimiters(text: str) -> bool:
    for marker in re.finditer(r"[*_~]+", text):
        before = text[marker.start() - 1] if marker.start() else " "
        after = text[marker.end()] if marker.end() < len(text) else " "
        if all(not c.isspace() and unicodedata.category(c)[0] not in ("P", "S") for c in (before, after)):
            return True
    return False


def _frontmatter(lines: list[str], offsets: list[int]) -> tuple[int, int] | None:
    if not lines or lines[0].rstrip("\r\n \t").lstrip("\ufeff") not in ("---", "+++"):
        return None
    delimiter = lines[0].strip("\ufeff\r\n \t")
    for i in range(1, len(lines)):
        if lines[i].strip("\r\n \t") in (delimiter, "..." if delimiter == "---" else delimiter):
            return 0, offsets[i + 1]
    return 0, offsets[-1]


def _html_region_end(source: str, start: int, default: int) -> int:
    """Balance lexical tags only, skipping whole comments/declarations and raw-text payloads."""
    tags = html_tag_pattern()
    opening = tags.match(source, start)
    head_pattern = re.compile(r"<(/?)([A-Za-z][\w:.-]*)")
    head = head_pattern.match(opening[0]) if opening else None
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    raw_text = {"script", "style", "textarea", "title", "pre", "xmp", "iframe", "noembed", "noframes"}
    if not head or head[1] or head[2].lower() in void or opening[0].endswith("/>"):
        return default
    name = head[2].lower()
    depth = 0
    pos = start
    while pos < len(source):
        left = source.find("<", pos)
        if left < 0:
            break
        token = tags.match(source, left)
        if token is None:
            if source.startswith(("<!--", "<![CDATA[", "<?", "<!"), left):
                return len(source)
            pos = left + 1
            continue
        tag = head_pattern.match(token[0])
        pos = token.end()
        if tag is None:
            continue
        tag_name = tag[2].lower()
        closes = bool(tag[1])
        self_closes = token[0].endswith("/>")
        if tag_name == name:
            depth += -1 if closes else (0 if self_closes else 1)
            if depth == 0:
                return max(default, pos)
        if not closes and not self_closes and tag_name in raw_text:
            closing = re.compile(r"</" + re.escape(tag_name) + r"[ \t\r\n]*>", re.I).search(source, pos)
            if closing is None:
                return len(source)
            pos = closing.end()
            if tag_name == name:
                depth -= 1
                if depth == 0:
                    return max(default, pos)
    return len(source)


def prose_spans(source: str) -> list[ProseSpan]:
    """Use block line maps and raw inline spans; everything else stays protected.

    Normalised parser content never reconstructs source. Physical lines bound engine units, preserving hard
    wraps and line endings even when a substitution phrase might otherwise span two lines.
    """
    from markdown_it import MarkdownIt

    lines = [line for line in re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", source) if line]
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    parser = MarkdownIt("commonmark").enable("table")
    tokens = parser.parse(source)
    protected = []
    frontmatter = _frontmatter(lines, offsets)
    if frontmatter:
        protected.append(frontmatter)
    paragraphs = []
    for i, token in enumerate(tokens):
        if token.map is None:
            continue
        start, end = (offsets[n] for n in token.map)
        if token.type in ("heading_open", "fence", "code_block", "table_open", "html_block"):
            html_start = start + _prefix(lines[token.map[0]].rstrip("\r\n"))
            protected.append((start, _html_region_end(source, html_start, end) if token.type == "html_block" else end))
        if token.type == "inline" and i and tokens[i - 1].type == "paragraph_open":
            paragraphs.append(token.map)
            if _word_adjacent_delimiters(source[start:end]):
                protected.append((start, end))  # Word-adjacent delimiters depend on flanking text, not just marker bytes.
            protected += [(start + a, start + b) for a, b in _inline_protected(source[start:end], parser)]
    protected = _merged(protected)
    protected_ends = [end for _, end in protected]
    prose = []
    for begin, finish in paragraphs:
        for i in range(begin, finish):
            body = lines[i].rstrip("\r\n")
            start = offsets[i] + _prefix(body)
            end = offsets[i] + len(body.rstrip(" \t"))
            if re.match(r"(?:import|export)\b", source[start:end]):
                continue  # MDX/JavaScript declarations are outside this Markdown dialect.
            for left, right in _without(start, end, protected, bisect_right(protected_ends, start)):
                part = source[left:right]
                leading = len(part) - len(part.lstrip(" \t"))
                trailing = len(part.rstrip(" \t"))
                while leading < trailing and not part[leading].isalnum():
                    leading += 1  # Prefix punctuation fixes delimiter flanking and must precede any inserted garnish.
                if any(c.isalpha() for c in part[leading:trailing]):
                    prose.append(ProseSpan(left + leading, left + trailing))
    return sorted(prose, key=lambda p: p.start)


def _escape(text: str) -> str:
    # Source units have no newlines; custom slang must not inject a block or hard break.
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").strip(" \t")
    text = re.sub(r"([\\`*_{}\[\]<>()!#|~>+\-=&])", r"\\\1", text)
    return re.sub(r"^(\d{1,9})\.([ \t])", r"\1\\.\2", text)


def translate_document(source: str, translator: Translator, policy: Policy, effective: Effective) -> DocumentResult:
    pieces = []
    units = []
    protected = []
    source_at = output_at = 0
    from .dialect import text_english
    from .genre import text_genre

    spans = prose_spans(source)
    prose = "\n".join(source[span.start:span.end] for span in spans)
    genre = text_genre(prose, source, config=translator.dictionary.genres)
    context = (genre, text_english(policy.english, prose, translator.dictionary.us_spellings))
    for span in spans:
        if span.start > source_at:
            piece = source[source_at:span.start]
            pieces.append(piece)
            protected.append(ProtectedSpan((source_at, span.start), (output_at, output_at + len(piece))))
            output_at += len(piece)
        r = translator.translate(source[span.start:span.end], level=policy.level, seed=policy.seed,
                                 vulgarity=policy.vulgarity, variety=policy.variety, registers=policy.registers,
                                 regions=policy.regions, unlock=policy.unlock, embedder=policy.embedder,
                                 english=policy.english, embellishment=policy.embellishment, _context=context)
        rendered = _escape(r.text)
        pieces.append(rendered)
        units.append(ProseUnit((span.start, span.end), (output_at, output_at + len(rendered)), rendered, r))
        source_at = span.end
        output_at += len(rendered)
    if source_at < len(source):
        piece = source[source_at:]
        pieces.append(piece)
        protected.append(ProtectedSpan((source_at, len(source)), (output_at, output_at + len(piece))))
    warnings = list(dict.fromkeys([*effective.warnings, *(w for u in units for w in u.result.warnings)]))
    return DocumentResult("".join(pieces), source, effective.level, policy.seed, effective.vulgarity,
                          policy.variety, warnings, units, protected, genre, context[1], genre.setting(policy.embellishment))
