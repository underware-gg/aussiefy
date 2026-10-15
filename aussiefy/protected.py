"""Format-independent opaque source spans and restoration invariants for text operations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable
from functools import cached_property

from .errors import UserError

BLOCK_BASE, INLINE_BASE = 0xF0000, 0x100000     # supplementary private use areas A and B
_ROOM = 0xFFFE                                   # placeholders available in each
BLOCK_RUN = "[\U000F0000-\U000FFFFD]+"
INLINE_CHARS = "\U00100000-\U0010FFFD"         # where inline placeholders live
INLINE_RUN = f"[{INLINE_CHARS}]+"
_ANY_RUN = re.compile(f"{BLOCK_RUN}|{INLINE_RUN}")




class MarkupError(RuntimeError):
    """The engine's output lost or duplicated a protected span (a bug: nothing should touch them)."""


@dataclass
class Masked:
    source: str
    text: str                                            # the source with every protected span masked
    spans: list[tuple[int, int, str]] = field(default_factory=list)   # (start, end, "block" | "inline")
    quiet: list[tuple[int, int]] = field(default_factory=list)        # table rows, list items: no garnish

    no_phonetic: Callable[[str], list[tuple[int, int]]] | None = None

    def quiet_at(self, pos: int) -> bool:
        return any(a <= pos < b for a, b in self.quiet)

    @cached_property
    def placeholders(self) -> dict[str, str]:
        used = set(self.source)
        available = {kind: (chr(n) for n in range(base, base + _ROOM) if chr(n) not in used)
                     for kind, base in (("block", BLOCK_BASE), ("inline", INLINE_BASE))}
        out = {}
        for start, end, kind in self.spans:
            ch = next(available[kind], None)
            if ch is None:
                raise UserError("too much markup to protect in one text; translate it in parts")
            out[ch] = self.source[start:end]
        return out

    def prose(self) -> str:
        """The source with every protected span blanked to spaces (newlines kept): what a lint should read."""
        chars = list(self.source)
        for start, end, _ in self.spans:
            chars[start:end] = [c if c == "\n" else " " for c in self.source[start:end]]
        return "".join(chars)

    def restore(self, text: str, *, whole: bool = True) -> str:
        """text with each placeholder run put back as its source span. whole: text is the full output, so
        every span must be there exactly once and intact (a sentence or a draft holds only some)."""
        if not self.spans:
            return text
        original = self.placeholders
        seen: dict[str, int] = {}

        def put_back(m: re.Match) -> str:
            pieces, run = [], m.group()
            while run:                       # adjacent spans make one run: split it per placeholder
                ch = run[0]
                n = len(run) - len(run.lstrip(ch))
                want = original.get(ch)
                if want is None or n != len(want):
                    raise MarkupError(f"protected span {ch!r} came back as {n} characters, not "
                                      f"{len(want) if want else '?'}")
                seen[ch] = seen.get(ch, 0) + 1
                pieces.append(want)
                run = run[n:]
            return "".join(pieces)

        out = _ANY_RUN.sub(put_back, text)
        if whole:
            lost = [s for ch, s in original.items() if seen.get(ch) != 1]
            if lost:
                raise MarkupError(f"{len(lost)} protected span(s) lost or repeated, e.g. {lost[0][:40]!r}")
        return out



def protected_runs(text: str) -> list[str]:
    """Opaque placeholder runs retained by a text operation."""
    return sorted(_ANY_RUN.findall(text))
