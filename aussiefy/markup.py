"""Markdown and MDX protection: translate the prose, leave everything else exactly as it was.

mask() finds what isn't prose (code fences and inline code, front matter, imports, JSX and HTML tags with
their props, maths, link targets, URLs, file paths and identifiers, table pipes, list and quote markers,
headings) and overwrites each span with a run of one private-use character, the same length as the span. The
engine translates the masked text as usual: its offsets still match the source, a run is one opaque token
that nothing matches, and a block run ends a sentence. Masked.restore() puts every span back, and refuses an
output that lost or duplicated one.

Two kinds of run: a block (a fence, a tag on its own line, a list marker) is never inside a sentence, so
garnish can't land inside or across it; an inline span (`code`, a link target) sits in its sentence like a
word nobody will swap. Headings are kept as they are, so links to their anchors still work.
"""

from __future__ import annotations

import re
from collections import Counter

from .errors import UserError

MARKUPS = ("text", "markdown", "mdx", "auto")

from .protected import INLINE_CHARS, _ANY_RUN, Masked, MarkupError as MarkupError, protected_runs as protected_runs

# a link's text in masked prose: "[" and the words before its masked "](target)"
LINK_TEXT = re.compile(rf"\[[^\[\]\n]*(?=[{INLINE_CHARS}])")

VERBATIM_TAGS = {"pre", "code", "script", "style", "svg", "math", "kbd", "samp", "var"}


def detect_markup(text: str) -> str:
    """'mdx', 'markdown' or 'text', from what the text holds (for markup="auto")."""
    if re.search(r"^(?:import|export)\s.+\bfrom\s+['\"]|^<[A-Z][\w.]*[\s/>]", text, re.M):
        return "mdx"
    signals = (r"^\s*(?:```|~~~)", r"^#{1,6}\s+\S", r"\[[^\]\n]+\]\([^)\s]+\)", r"`[^`\n]+`",
               r"^\s*[-*+]\s+\S.*\n\s*[-*+]\s+\S", r"^\s*\|.*\|\s*$")
    return "markdown" if sum(bool(re.search(s, text, re.M)) for s in signals) >= 2 else "text"


def mask(text: str, markup: str = "text") -> Masked:
    """Protect everything in text that isn't prose. markup: text (nothing), markdown, mdx, or auto."""
    if markup not in MARKUPS:
        raise UserError(f"markup must be one of {', '.join(MARKUPS)}, not {markup!r}")
    if markup == "auto":
        markup = detect_markup(text)
    if markup == "text":
        return Masked(text, text)
    scanner = _Scanner(text, mdx=markup == "mdx")
    spans = scanner.scan()
    # Existing private-use glyphs are opaque source too; allocated placeholders must never collide with them.
    glyphs, previous = [], 0
    for start, end, _ in [*spans, (len(text), len(text), "inline")]:
        glyphs.extend((m.start(), m.end(), "inline") for m in _ANY_RUN.finditer(text, previous, start))
        previous = end
    spans = sorted([*spans, *glyphs])
    masked = Masked(text, text, spans, scanner.quiet)
    chars = list(text)
    for ch, (start, end, _) in zip(masked.placeholders, spans):
        chars[start:end] = ch * (end - start)
    masked.text = "".join(chars)
    masked.no_phonetic = lambda current: [m.span() for m in LINK_TEXT.finditer(current)]
    return masked


# --- the scanner ----------------------------------------------------------------------------------------

_FENCE = re.compile(r"[ \t]*(`{3,}|~{3,})")
_HEADING = re.compile(r"[ ]{0,3}#{1,6}(?:[ \t]|$)")
_SETEXT = re.compile(r"[ ]{0,3}(?:=+|-+)[ \t]*$")
_RULE = re.compile(r"[ ]{0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_LINK_DEF = re.compile(r"[ ]{0,3}\[[^\]\n]+\]:[ \t]*\S")
_TABLE_SEP = re.compile(r"[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)+\|?[ \t]*$")
_QUOTE = re.compile(r"[ \t]*(?:>[ \t]?)+")
_ITEM = re.compile(r"[ \t]*(?:[-*+]|\d{1,9}[.)])(?:[ \t]+|$)(?:\[[ xX]\][ \t]+)?")
_IMPORT = re.compile(r"(?:import|export)\s")

_INLINE = re.compile("|".join([
    r"(?P<code>`+)",
    r"(?P<math>\$\$|\$(?=[^\s$\d]))",
    r"(?P<image>!\[)",
    r"(?P<dest>\]\((?:[^()\s]|\([^()\s]*\))*(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\))",
    r"(?P<ref>\]\[[^\]\n]*\])",
    r"(?P<footnote>\[\^[^\]\n]+\])",
    r"(?P<autolink><(?:https?|mailto|ftp):[^>\s]+>)",
    r"(?P<url>(?:https?://|www\.)[^\s<>()\[\]{}\"'`]+)",
    r"(?P<email>[\w.+-]+@[\w-]+(?:\.[\w-]+)+)",
    r"(?P<tag></?[A-Za-z][\w.:-]*|<>|</>)",
    r"(?P<brace>\{)",
    r"(?P<entity>&(?:#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);)",
    r"(?P<escape>\\[\\`*_{}\[\]()#+\-.!|<>~$])",
    r"(?P<chunk>[^\s`<>\[\]()\"{}|]+(?:\(\))?)",
]))
_TEMPLATE = re.compile(r"\{\{[^\n]*?\}\}|\{%[^\n]*?%\}")   # one line: a stray "{{" doesn't swallow the text
_ATTRS = re.compile(r"\{[#.][\w-]+(?:\s+[#.][\w-]+)*\}")
# a chunk (no spaces) that is code-ish: an identifier, a path, a flag, a file name, a variable
_CODEISH = re.compile(r"""
    \w_\w | [A-Za-z0-9]/[A-Za-z0-9~.] | ^[~/.]+/ | \\\w | :: | -> | => | == | \w=\S | ^\$[A-Za-z_{(]
    | ^--?[A-Za-z][\w-]*$ | ^@[\w-]+/ | [a-z][A-Z] | \w\.[a-z]{2,}\w*\(? | \(\)$
""", re.X)
_TRIM = ".,;:!?*_'\"’”)"


class _Scanner:
    def __init__(self, text: str, mdx: bool):
        self.text, self.mdx = text, mdx
        self.spans: list[tuple[int, int, str]] = []
        self.reach = 0                 # the furthest any span reaches
        self.quiet: list[tuple[int, int]] = []
        self.lines = text.splitlines(keepends=True)
        self.starts = [0]
        for line in self.lines:
            self.starts.append(self.starts[-1] + len(line))

    def block(self, start: int, end: int) -> None:
        if end > start:
            self.spans.append((start, end, "block"))
            self.reach = max(self.reach, end)

    def span(self, start: int, end: int) -> None:
        """A protected span: inline when it sits on one line, a block when it runs over several."""
        (self.inline if self.line_of(end - 1) == self.line_of(start) else self.block)(start, end)

    def inline(self, start: int, end: int) -> None:
        if end > start:
            self.spans.append((start, end, "inline"))
            self.reach = max(self.reach, end)

    def line_end(self, li: int) -> int:
        """The end of line li, before its newline."""
        return self.starts[li] + len(self.lines[li].rstrip("\r\n"))

    def line_of(self, pos: int) -> int:
        lo, hi = 0, len(self.lines) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def scan(self) -> list[tuple[int, int, str]]:
        n = len(self.lines)
        li = self.front_matter()
        prev_blank, in_list = True, False
        while li < n:
            line = self.lines[li].rstrip("\r\n")
            start = self.starts[li]
            if start < self.reach:          # inside a span that ran on from an earlier line (already scanned)
                li += 1
                continue
            nxt = self.lines[li + 1].rstrip("\r\n") if li + 1 < n else ""
            if not line.strip():
                prev_blank = True
                li += 1
                continue
            stripped = line.strip()
            if (m := _FENCE.match(line)):
                fence = m.group(1)
                li = self.until(li, re.compile(rf"[ \t]*{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$"))
            elif stripped.startswith("$$"):
                single = len(stripped) > 2 and stripped.endswith("$$")
                li = li + 1 if single else self.until(li, re.compile(r".*\$\$[ \t]*$"))
            elif stripped.startswith("<!--"):
                li = self.through(li, "<!--", "-->")
            elif self.mdx and stripped.startswith("{/*"):
                li = self.through(li, "{/*", "*/}")
            elif self.mdx and _IMPORT.match(line):
                li = self.statement(li)
            elif _HEADING.match(line) or _RULE.match(line) or _LINK_DEF.match(line) or _TABLE_SEP.match(line):
                li += 1
            elif self.setext(line, nxt, in_list):
                li += 2
            elif not self.mdx and prev_blank and not in_list and re.match(r"(?: {4}|\t)", line):
                end = li + 1
                while end < n and (re.match(r"(?: {4}|\t)", self.lines[end]) or not self.lines[end].strip()):
                    end += 1
                while end > li + 1 and not self.lines[end - 1].strip():
                    end -= 1
                li = end
            elif (tag := self.tag_at(start + len(line) - len(line.lstrip()))):
                li = self.tag_line(li, *tag)
                prev_blank = False
                continue
            else:
                in_list = self.prose_line(li) or (in_list and line[:1] in " \t")
                prev_blank = False
                li += 1
                continue
            self.block(start, self.line_end(li - 1))
            prev_blank = False
        spans = sorted(self.spans)
        for (_, end, _), (start, _, _) in zip(spans, spans[1:]):
            if start < end:
                raise MarkupError(f"overlapping protected spans at {start}")
        return spans

    def setext(self, line: str, nxt: str, in_list: bool) -> bool:
        """A heading underlined with === or --- (a --- under a list item or a table row is something else)."""
        if not nxt or not _SETEXT.match(nxt) or in_list or _ITEM.match(line) or _QUOTE.match(line):
            return False
        return "=" in nxt or "|" not in line

    # -- block helpers --------------------------------------------------------------------------------

    def front_matter(self) -> int:
        if not self.lines or self.lines[0].rstrip() not in ("---", "+++"):
            return 0
        fence = self.lines[0].rstrip()
        for li in range(1, len(self.lines)):
            if self.lines[li].rstrip() == fence:
                self.block(0, self.line_end(li))
                return li + 1
        return 0

    def until(self, li: int, closing: re.Pattern) -> int:
        """The line after the one (after li) that matches closing, or the end of the text."""
        for j in range(li + 1, len(self.lines)):
            if closing.match(self.lines[j].rstrip("\r\n")):
                return j + 1
        return len(self.lines)

    def through(self, li: int, opening: str, closing: str) -> int:
        """The line after the one that closes a comment opened on line li (it may close on li itself)."""
        first = self.lines[li]
        if closing in first[first.find(opening) + len(opening):]:
            return li + 1
        for j in range(li + 1, len(self.lines)):
            if closing in self.lines[j]:
                return j + 1
        return len(self.lines)

    def statement(self, li: int) -> int:
        """An import/export: until its brackets close at a line end."""
        depth = 0
        for j in range(li, len(self.lines)):
            for ch in _code_only(self.lines[j]):
                depth += (ch in "{[(") - (ch in "}])")
            if depth <= 0:
                return j + 1
        return len(self.lines)

    def tag_at(self, pos: int) -> tuple[int, int] | None:
        """(start, end) of a JSX/HTML tag starting at pos, or None."""
        if not re.match(r"</?[A-Za-z]|<>|</>", self.text[pos:pos + 3]):
            return None
        end = _scan_tag(self.text, pos)
        return (pos, end) if end else None

    def tag_line(self, li: int, start: int, end: int) -> int:
        """A tag at a line's start: a block (it can't share a sentence with what came before). A verbatim
        element (<pre>, <code> ...) runs to its closing tag; prose after the tag on its last line is scanned."""
        end = self.verbatim_end(start, end)
        self.block(start, end)
        last = self.line_of(max(start, end - 1))
        rest_end = self.line_end(last)
        if end < rest_end and self.text[end:rest_end].strip():
            if (more := self.tag_at(end + len(self.text[end:rest_end]) - len(self.text[end:rest_end].lstrip()))):
                return self.tag_line(last, *more)
            self.inline_scan(end, rest_end)
        return last + 1

    def verbatim_end(self, start: int, end: int) -> int:
        """Where the element whose opening tag is text[start:end] ends, if its content is never prose (<pre>,
        <kbd> ...); otherwise the tag's own end."""
        tag = self.text[start:end]
        name = re.match(r"</?([\w.:-]*)", tag).group(1)
        if name.lower() not in VERBATIM_TAGS or tag.startswith("</") or tag.endswith("/>"):
            return end
        close = re.compile(rf"</{re.escape(name)}\s*>", re.I).search(self.text, end)
        return close.end() if close else len(self.text)

    # -- prose ---------------------------------------------------------------------------------------

    def prose_line(self, li: int) -> bool:
        """Markers at the line's start are blocks; the rest is scanned inline. True for a list item."""
        pos, end = self.starts[li], self.line_end(li)
        item = False
        while pos < end:
            m = _QUOTE.match(self.text, pos, end) or _ITEM.match(self.text, pos, end)
            if not m or m.end() == pos:
                break
            if m.re is _ITEM:
                item = True
            self.block(pos, m.end())
            pos = m.end()
        if item:
            self.quiet.append((self.starts[li], end))
        if "|" in self.text[pos:end] and self.table_row(li):
            self.quiet.append((self.starts[li], end))
            for m in re.finditer(r"(?<!\\)\|", self.text[pos:end]):
                self.block(pos + m.start(), pos + m.end())
        self.inline_scan(pos, end)
        return item

    def table_row(self, li: int) -> bool:
        near = [self.lines[j].rstrip("\r\n") for j in (li - 1, li + 1) if 0 <= j < len(self.lines)]
        line = self.lines[li]
        return bool(_TABLE_SEP.match(line)) or any(_TABLE_SEP.match(x) for x in near) or (
            line.lstrip().startswith("|") and line.rstrip().endswith("|"))

    def inline_scan(self, pos: int, end: int) -> None:
        text = self.text
        while pos < end:
            m = _INLINE.search(text, pos, end)
            if not m:
                return
            kind, a = m.lastgroup, m.start()
            b = m.end()
            if kind == "code":
                close = re.compile(rf"(?<!`){m.group()}(?!`)").search(text, b, self._para_end(a))
                if close:
                    b = close.end()
                    self.span(a, b)
            elif kind == "math":
                close = text.find(m.group(), b, self._para_end(a))
                if close > b and (m.group() == "$$" or (text[close - 1] != " " and not text[close + 1:close + 2].isdigit())):
                    b = close + len(m.group())
                    self.inline(a, b)
            elif kind == "image":
                b = self._image(a)
                if b > m.end():
                    self.inline(a, b)
            elif kind in ("dest", "ref", "footnote", "autolink", "email", "entity", "escape"):
                self.inline(a, b)
            elif kind == "url":
                url = m.group().rstrip(".,;:!?")
                b = a + len(url)
                self.inline(a, b)
            elif kind == "tag":
                tag_end = _scan_tag(text, a)
                if tag_end:
                    b = self.verbatim_end(a, tag_end)
                    self.span(a, b)
            elif kind == "brace":
                if self.mdx:
                    close = _scan_balanced(text, a)
                    if close:
                        b = close
                        self.span(a, b)
                elif (attr := _TEMPLATE.match(text, a) or _ATTRS.match(text, a)):
                    b = attr.end()   # a template's {{ macro }} or {% tag %}, or a heading's {#id .class}
                    self.inline(a, b)
            elif kind == "chunk":
                word = m.group()
                core = word if word.endswith("()") else word.rstrip(_TRIM)
                lead = len(core) - len(core.lstrip("*_'\"‘“("))
                core = core[lead:]
                codeish = (bool(core) and _CODEISH.search(core) is not None
                           and not re.fullmatch(r"(?:[A-Za-z]\.){2,}[A-Za-z]?", core)   # "U.S.", "e.g."
                           and not re.fullmatch(r"[A-Za-z]+/[A-Za-z]+", core))           # "and/or"
                if codeish or _path_like(core):
                    self.inline(a + lead, a + lead + len(core))
            if b > end:     # a span ran over this line (a multi-line code span or tag): skip what it took
                return self._resume(b)
            pos = max(b, a + 1)

    def _resume(self, pos: int) -> None:
        """Carry on scanning prose from pos, the middle of a later line."""
        li = self.line_of(pos)
        if pos < self.line_end(li):
            self.inline_scan(pos, self.line_end(li))

    def _para_end(self, pos: int) -> int:
        m = re.compile(r"\n[ \t]*\n").search(self.text, pos)
        return m.start() if m else len(self.text)

    def _image(self, a: int) -> int:
        depth, i, text = 0, a + 1, self.text
        while i < len(text) and text[i] != "\n":
            depth += (text[i] == "[") - (text[i] == "]")
            if depth == 0:
                break
            i += 1
        m = re.compile(r"\]\((?:[^()\s]|\([^()\s]*\))*(?:\s+\"[^\"\n]*\")?\)|\]\[[^\]\n]*\]").match(text, i)
        return m.end() if m else a + 2


def _path_like(core: str) -> bool:
    """A file name: name.ext with a known-looking extension (main.rs, README.md), not an abbreviation."""
    return bool(re.fullmatch(r"[\w-]+(?:\.[\w-]+)*\.(?:[a-z]{1,5}\d?)", core)) and not re.fullmatch(
        r"(?:[A-Za-z]{1,3}\.)+[A-Za-z]{0,3}", core) and len(core.split(".")[0]) > 1


def _code_only(line: str) -> str:
    """line without its string literals (so brackets in strings don't count)."""
    return re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`(?:[^`\\]|\\.)*`", "", line)


def _skip_string(text: str, i: int) -> int:
    """The index after the string literal that starts at text[i]."""
    quote, i = text[i], i + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if quote == "`" and text.startswith("${", i):
            close = _scan_balanced(text, i + 1)
            i = close if close else i + 2
            continue
        if text[i] == quote:
            return i + 1
        if quote != "`" and text[i] == "\n":
            return i + 1       # an unclosed quote ends at the line (an apostrophe in prose, not a string)
        i += 1
    return len(text)


def _scan_balanced(text: str, i: int, limit: int = 50_000) -> int | None:
    """From an opening brace at text[i], the index after its match (strings skipped), or None."""
    depth, j, stop = 0, i, min(len(text), i + limit)
    while j < stop:
        ch = text[j]
        if ch in "'\"`" and depth:
            j = _skip_string(text, j)
            continue
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def _scan_tag(text: str, i: int, limit: int = 50_000) -> int | None:
    """From '<' at text[i], the index after the tag's closing '>' (quoted and braced props skipped), or None."""
    j, stop = i + 1, min(len(text), i + limit)
    if not re.match(r"/?[A-Za-z>]|/>", text[j:j + 2]):
        return None
    while j < stop:
        ch = text[j]
        if ch in "'\"":
            j = _skip_string(text, j)
            continue
        if ch == "{":
            close = _scan_balanced(text, j)
            if close is None:
                return None
            j = close
            continue
        if ch == ">":
            return j + 1
        if ch == "<" or (ch == "\n" and text[j:j + 3].startswith("\n\n") and not text[i + 1:i + 2].isupper()):
            return None        # a stray '<' in prose ("a < b"), not a tag
        j += 1
    return None


def markup_changed(text: str, original: str, markup: str) -> list[dict]:
    """Lint issues for code or markup in original that text doesn't carry unchanged (as often as it had it)."""
    if markup == "auto":
        markup = detect_markup(original)
    m = mask(original, markup)
    want = Counter(original[a:b] for a, b, _ in m.spans if original[a:b].strip())
    out = []
    for piece, n in want.items():
        if text.count(piece) < n:
            out.append({"kind": "markup_changed", "phrase": piece[:80],
                        "why": "code or markup from the original is missing or changed; keep it exactly as it was"})
    return out
