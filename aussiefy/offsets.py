"""Half-open positions mapped through actual ordered text edits, without rendering or I/O."""

from collections.abc import Sequence
from typing import Literal

Bias = Literal["left", "right"]
Side = Literal["start", "end"]

def _walk(edits: Sequence[tuple[int, int, int]], pos: int, past_insertion: bool) -> tuple[int, tuple[int, int] | None]:
    """A position through edits (start, end, new length), sorted, in the input's coordinates: where it lands, or,
    for a position inside a replaced span, None and that edit's new start and end. past_insertion: whether a
    position at an insertion goes after it."""
    delta = 0
    for a, b, n in edits:
        if pos < a or (pos == a and (b > a or not past_insertion)):
            break
        if pos >= b:
            delta += n - (b - a)
            continue
        return pos, (a + delta, a + delta + n)
    return pos + delta, None


class Straddle(Exception):
    """A position falls inside an edit: a match across a region's edge."""


def map_position(edits: Sequence[tuple[int, int, int]], pos: int, bias: Bias) -> int:
    """A position through edits. At an insertion, bias "left" stays before it and "right" goes after; a position
    inside a replaced span raises Straddle."""
    out, inside = _walk(edits, pos, bias == "right")
    if inside is not None:
        raise Straddle(pos, inside)
    return out


def map_outward(edits: Sequence[tuple[int, int, int]], pos: int, side: Side) -> int:
    """One end of a span through edits, taking in an edit it falls inside: a "start" goes to the edit's start, an
    "end" to its end (and at an insertion, a start stays before it and an end goes after)."""
    out, inside = _walk(edits, pos, side == "end")
    if inside is None:
        return out
    return inside[0] if side == "start" else inside[1]


def unmap_position(edits: Sequence[tuple[int, int, int]], pos: int, side: Side) -> int:
    """A position in edited text back in the input; inside an edit's new text, its input's "start" or end."""
    delta = 0
    for a, b, n in edits:
        new_start = a + delta
        if pos <= new_start:
            break
        if pos < new_start + n:
            return a if side == "start" else b
        delta += n - (b - a)
    return pos - delta



def map_spans(spans: list[list[int]], edits: Sequence[tuple[int, int, int]]) -> None:
    """Update local annotation spans through one pass; an overlapping edit belongs to the annotation."""
    for span in spans:
        span[:] = [map_outward(edits, span[0], "start"), map_outward(edits, span[1], "end")]
