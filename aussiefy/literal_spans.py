"""Keep caller-owned words exact while surrounding text is edited."""

from .offsets import map_position
from .protected import Masked


def retain_literals(before, after, edit, spans):
    """An ordinary edit plus exact-case restoration; reject any edit through owned words."""
    a, b, length = edit
    if any((a < end and start < b) or (a == b and start < a < end) for start, end in spans):
        return None
    moved = tuple((map_position([edit], start, 'right'), map_position([edit], end, 'left'))
                  for start, end in spans)
    pieces = after
    for (start, end), (left, right) in zip(spans, moved, strict=True):
        pieces = pieces[:left] + before[start:end] + pieces[right:]
    return pieces, moved


def mask_literals(text, spans):
    """Opaque runs of equal length, distinct from any existing markup placeholders."""
    masked = Masked(text, text, spans=[(a, b, 'inline') for a, b in spans])
    for (a, b, _), key in zip(masked.spans, masked.placeholders, strict=True):
        masked.text = masked.text[:a] + key * (b - a) + masked.text[b:]
    return masked


def restore_literals(masked, text):
    """Restore only these owned runs; surrounding markup belongs to its own masker."""
    moved = []
    for key, words in masked.placeholders.items():
        start = text.index(key)
        moved.append((start, start + len(words)))
        text = text.replace(key * len(words), words)
    return text, tuple(sorted(moved))
