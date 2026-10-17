"""The `changes` builder: every change a translation made, placed in its output, with each spot's alternatives
rendered where they stand.

It runs in the same pass as translate, watching it (engine.PassObserver), and renders each alternative the way the
engine would at that spot with the rest of the output held fixed: through render_at_spot (form, article,
replacement span, stack, riff, a/an and capitals), the sentence's garnish put back as decided, and each phonetic
rule's pass over the spot's region only, its count starting from the matches in the unchanged text before it and
its context read from the whole text. A swap is therefore local: it can differ from a whole re-render with that
pick, where later rolls and picks shift. The contract is VERSION, its shape aussiefy/data/changes.schema.json
(docs/architecture/decisions/dd-029-changes-builder.md).
"""

from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property, lru_cache
from pathlib import Path
from string import Formatter
from typing import Any, Literal

from .cards import entry_card, shows_riffs
from .engine import (PassObserver, Result, SentenceTrace, Spot, SpotRendering, Translator,
                     first_replaced)
from .garnish import (Edit, GarnishOffer, PhoneticPass, PhoneticTrace, in_dialogue, phonetic_admits,
                      phonetic_replacement, place_garnish)
from .masks import masks
from .model import Dictionary
from .policy import resolve
from .schema import Entry
from .select import Candidate
from .text import FIRST_WORD_RE

VERSION = 1          # the changes contract; a change to its shape or to how ids are made bumps it
SCHEMA = Path(__file__).resolve().parent / "data" / "changes.schema.json"   # its JSON Schema
ID_FORMAT = "{kind}:{start}-{end}[:{placement or rule}][#{n}]"   # how a change's id is made ([...]: where it has one)
CONTEXT = 64         # characters of whole-text context read either side of a region, for the rules' lookaround
MARGIN = 16          # ... the outer part of which is read, never compared (a match there may be cut short)
WIDEN = 4            # the most words a region widens by, each side, for a phonetic match across its edge
_FIELDS = ("id", "kind", "src_span", "out_span", "original", "output", "entry_id", "vulgarity", "masks", "placement",
           "image_id", "removed", "rule", "pair", "alternatives", "locked", "covers")   # a change's, in order
KINDS = ("substitution", "dialect", "garnish", "swear_infix", "phonetic")   # also their order at one output span
# why a swap or a garnish offers its pick alone (ChangeSet.withheld)
PICK_DIFFERS = "pick-differs"            # the pick, rendered over its region, isn't the output there
REGION_UNSETTLED = "region-unsettled"    # a phonetic match still reads across the region's edge after widening

Bias = Literal["left", "right"]
Side = Literal["start", "end"]


@dataclass
class ChangeSet:
    """A translation and its changes under the contract VERSION: `changes` in output order, the card of every
    entry they name (each sent once), and the swaps and garnish whose alternatives are withheld (their pick alone
    offered, and a garnish's removal left out), with why."""
    result: Any                       # engine.Result, or markdown.DocumentResult for a Markdown document
    changes: list[dict[str, Any]]
    entries: dict[str, dict[str, Any]]
    withheld: list[dict[str, str]] = field(default_factory=list)
    version: int = VERSION

    @property
    def text(self) -> str:
        return self.result.text

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "text": self.result.text, "changes": self.changes, "entries": self.entries,
                "withheld": self.withheld}


@dataclass
class Draft:
    """A change as the builder makes it, before finish(): its contract fields so far (no id, masks or covers yet),
    the placement or rule its id adds to its kind and source span, the entries its own rendering and each
    alternative's and locked option's rendering came from (whose mask words each carries), and why its
    alternatives are withheld, if they are."""
    change: dict[str, Any]
    key: str = ""
    entries: list[str] = field(default_factory=list)
    rendering_entries: list[list[str]] = field(default_factory=list)   # alternatives', then locked options'
    withheld: str | None = None

    def renderings(self) -> Iterator[dict[str, Any]]:
        """Each rendering a page can swap in: the alternatives, the locked options and a removal."""
        yield from self.change["alternatives"]
        yield from self.change["locked"]
        if self.change.get("removed"):
            yield self.change["removed"]

    def relocate(self, source: int, position: Callable[[int], int],
                 rendering: Callable[[list[int], str], str], text: str) -> None:
        """Move the change into a larger text (a Markdown document): source offsets shifted by source, output
        positions mapped through position, each rendering through rendering (its span here, its text), and its
        output read again from text."""
        c = self.change
        c["src_span"] = [c["src_span"][0] + source, c["src_span"][1] + source]
        for r in self.renderings():
            r["rendered"] = rendering(r["out_span"], r["rendered"])
            r["out_span"] = [position(r["out_span"][0]), position(r["out_span"][1])]
        c["out_span"] = [position(c["out_span"][0]), position(c["out_span"][1])]
        c["output"] = text[c["out_span"][0]:c["out_span"][1]]


def build(translator: Translator, text: str, **options) -> ChangeSet:
    """Translate text (Translator.translate's options, without a rewriter) and build its changes in the same pass."""
    result, drafts = collect(translator, text, **options)
    return finish(result, drafts, translator.dictionary)


def collect(translator: Translator, text: str, _observer: Watch | None = None,
            **options) -> tuple[Result, list[Draft]]:
    """The translation and its changes before finish(), in its own output's and source's coordinates. A document
    adapter relocates each unit's drafts, then finishes them together."""
    if options.get("rewriter") is not None:
        raise ValueError("a sentence rewritten whole has no changes to swap; build changes without a rewriter")
    watch = _observer if _observer is not None else Watch()
    result = translator.translate(text, **options, _observer=watch)
    return result, _Builder(translator, watch, result).drafts()


def finish(result: Any, drafts: list[Draft], dictionary: Dictionary) -> ChangeSet:
    """The contract: ids made (kind, source span, placement or rule, and a running number for the rare repeat),
    changes in output order, what each one's swap or removal reaches into (covers), each rendering's maskable
    words, the cards of the entries they name (built as lookup builds them, under the result's vulgarity and
    embellishment), and the swaps whose alternatives are withheld."""
    for d in drafts:
        d.change["id"] = _change_id(d)
    drafts = sorted(drafts, key=lambda d: (d.change["out_span"][0], d.change["out_span"][1],
                                           KINDS.index(d.change["kind"]), d.change["id"]))
    seen: dict[str, int] = {}
    for d in drafts:
        n = seen[d.change["id"]] = seen.get(d.change["id"], 0) + 1
        if n > 1:
            d.change["id"] = _change_id(d, n)
    _cover(drafts)
    names: set[str] = set()
    for d in drafts:
        c = d.change
        c["masks"] = _masked(dictionary, c["output"], d.entries)
        for o, entries in zip(c["alternatives"] + c["locked"], d.rendering_entries, strict=True):
            o["masks"] = _masked(dictionary, o["rendered"], entries)
        names.update(i for es in [d.entries, *d.rendering_entries] for i in es)
    riffs = shows_riffs(result.embellishment)
    entries = {i: entry_card(dictionary.entries[i], result.vulgarity, riffs) for i in sorted(names)}
    withheld = [{"id": d.change["id"], "reason": d.withheld} for d in drafts if d.withheld]
    changes = [{k: d.change[k] for k in _FIELDS if k in d.change} for d in drafts]
    return ChangeSet(result, changes, entries, withheld)


_ID_PART = re.compile(r"\[([^\]]*)\]|[^\[]+")   # ID_FORMAT's parts: [an optional one], or a fixed one


def _change_id(d: Draft, n: int = 1) -> str:
    """A change's id, as ID_FORMAT makes it: its kind and source span, then its placement or rule and the number
    of a repeat (from the second), each only where it has one."""
    a, b = d.change["src_span"]
    fields = {"kind": d.change["kind"], "start": a, "end": b, "placement or rule": d.key, "n": n if n > 1 else ""}
    out = []
    for m in _ID_PART.finditer(ID_FORMAT):
        optional = m.group(1) is not None
        part = m.group(1) if optional else m.group(0)
        if optional and not all(fields[name] for _, name, _, _ in Formatter().parse(part) if name):
            continue
        out.append(part.format_map(fields))
    return "".join(out)


def _masked(dictionary: Dictionary, text: str, entry_ids: list[str]) -> list[dict[str, Any]]:
    """A rendering's maskable words: listed swears, compounds, and the mask words of the entries it came from."""
    words: dict[str, int] = {}
    for e in (dictionary.entries[i] for i in entry_ids):
        for w in e.mask:
            words[w] = max(words.get(w, 0), e.vulgarity)
    return masks(text, dictionary.swears, dictionary.swear_compounds, words)


# -- offsets ------------------------------------------------------------------------------------------------------

def _walk(edits: Sequence[Edit], pos: int, past_insertion: bool) -> tuple[int, tuple[int, int] | None]:
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


def map_position(edits: Sequence[Edit], pos: int, bias: Bias) -> int:
    """A position through edits. At an insertion, bias "left" stays before it and "right" goes after; a position
    inside a replaced span raises Straddle."""
    out, inside = _walk(edits, pos, bias == "right")
    if inside is not None:
        raise Straddle(pos, inside)
    return out


def map_outward(edits: Sequence[Edit], pos: int, side: Side) -> int:
    """One end of a span through edits, taking in an edit it falls inside: a "start" goes to the edit's start, an
    "end" to its end (and at an insertion, a start stays before it and an end goes after)."""
    out, inside = _walk(edits, pos, side == "end")
    if inside is None:
        return out
    return inside[0] if side == "start" else inside[1]


def unmap_position(edits: Sequence[Edit], pos: int, side: Side) -> int:
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


# -- what the pass reports ----------------------------------------------------------------------------------------

@dataclass
class _Op:
    """A garnish the engine placed: its entry and words, where they went in the text before them, and what the
    engine picked it from."""
    entry: Entry
    form: str
    edit: Edit
    offer: GarnishOffer

    @property
    def placement(self) -> str:
        return self.offer.placement


class Watch(PassObserver):
    """Keeps what the builder needs from the pass: a snapshot of the state at each pick, each sentence's splices and
    garnish (with what each garnish was picked from), contextual imagery, the closer and the phonetic passes. It
    only watches: it steers nothing (choose and placing stay the engine's own)."""

    def __init__(self):
        self.run: Any = None
        self.spots: list[Spot] = []
        self.sentences: list[SentenceTrace] = []
        self.ops: dict[int, list[_Op]] = defaultdict(list)
        self.images: dict[tuple[int, int], tuple[str, str]] = {}   # (sentence, splice) -> (image id, words)
        self.closer: _Op | None = None
        self.joined = self.final = ""
        self.trace: PhoneticTrace | None = None

    def begin(self, run):
        self.run = run

    def spot(self, spot):
        self.spots.append(spot)

    def imagery(self, sentence, image_id, splice, suffix):
        self.images[(sentence, splice)] = (image_id, suffix)

    def garnish(self, sentence, entry, form, edit, offer):
        op = _Op(entry, form, edit, offer)
        if offer.placement == "closer":
            self.closer = op
        else:
            self.ops[sentence].append(op)

    def sentence(self, trace):
        self.sentences.append(trace)

    def phonetic(self, joined, trace, final):
        self.joined, self.trace, self.final = joined, trace, final


# -- sentences, tellings and regions ---------------------------------------------------------------------------

@dataclass
class _Splice:
    """A splice in a sentence, in source coordinates, and what put it there."""
    start: int
    end: int
    text: str
    kind: str                 # substitution | imagery | dialect
    owner: Any = None         # the Spot, the image id, or the DialectRecord


@dataclass
class _Layout:
    """A sentence as one telling has it: the source sentence's splice edits, then each garnish's edit in turn (None
    where it isn't placed), and the garnished text."""
    splices: list[Edit]
    garnish: list[Edit | None]
    text: str

    def forward(self, pos: int, bias: Bias) -> int:
        return self.after_garnish(map_position(self.splices, pos, bias), bias, 0)

    def after_garnish(self, pos: int, bias: Bias, first: int) -> int:
        for e in self.garnish[first:]:
            if e is not None:
                pos = map_position([e], pos, bias)
        return pos

    def back(self, pos: int, side: Side) -> int:
        for e in reversed(self.garnish):
            if e is not None:
                pos = unmap_position([e], pos, side)
        return unmap_position(self.splices, pos, side)


@dataclass
class _Sentence:
    trace: SentenceTrace
    splices: list[_Splice]
    ops: list[_Op]
    first_replaced: bool
    layout: _Layout
    before: list[str] | None = None     # its text before each garnish went in (read on demand)

    @property
    def offset(self) -> int:
        return self.trace.sent.tokens[0].start


@dataclass
class _Option:
    candidate: Candidate
    rendering: SpotRendering
    locked_at: int | None = None
    text: str = ""
    infix: int = 0

    @property
    def entry(self) -> Entry:
        return self.candidate.entry

    @property
    def entries(self) -> list[str]:
        """The entries its rendering came from: its own, and the one stacked after it."""
        stacked = self.rendering.stacked
        return [self.entry.id] + ([stacked.entry.id] if stacked else [])


@dataclass
class _Region:
    """Where a spot's options go: a source token span, its bounds in each phonetic pass's input (the base text),
    and in the final text."""
    start: int
    end: int
    bounds: list[tuple[int, int]] = field(default_factory=list)
    final: tuple[int, int] = (0, 0)
    flags: set[str] = field(default_factory=set)


class _PassView:
    """One phonetic pass as a region [a, b) of its input reads it: the context either side, the matches before it
    (where its count starts), and the neighbours' matches to compare an option's with."""

    def __init__(self, p: PhoneticPass, a: int, b: int):
        self.pass_, self.a, self.b = p, a, b
        starts, ends = p.starts, p.ends
        self.left, self.right = p.before[max(0, a - CONTEXT):a], p.before[b:b + CONTEXT]
        self.count = bisect_left(starts, a)
        self.straddle = bool(self.count and ends[self.count - 1] > a)
        self._left = range(bisect_left(starts, a - CONTEXT + MARGIN), self.count)
        self._right = range(bisect_left(starts, b), bisect_left(starts, b + CONTEXT - MARGIN))
        self.triggers = _triggers(p.rule.pattern)
        self.quiet = self.triggers is not None and not self.straddle and not self._left and not self._right

    @cached_property
    def base_left(self) -> list[tuple[int, str]]:
        p = self.pass_
        return [(p.starts[j] - self.a, p.before[p.starts[j]:p.ends[j]]) for j in self._left if p.ends[j] <= self.a]

    @cached_property
    def base_right(self) -> list[tuple[int, str]]:
        p = self.pass_
        return [(p.starts[j] - self.b, p.before[p.starts[j]:p.ends[j]]) for j in self._right]

    def position(self, offset: int) -> int:
        """Where a match offset into the region sits in the base text, for the spans the rule reads (clamped to
        the region, which an option's text may outrun)."""
        return self.a + min(offset, max(0, self.b - self.a - 1))


class _Builder:
    def __init__(self, translator: Translator, watch: Watch, result: Result):
        self.translator, self.watch, self.result = translator, watch, result
        self.run = watch.run                # what render_at_spot and garnish replay read (engine.render_at_spot)
        self.passes: list[PhoneticPass] = watch.trace.passes
        self.restore = self.run.masked.restore
        self.final = result.text            # the final text, protected spans restored (the same length)
        self.source = result.source
        self.closer = watch.closer
        self.starts = [st.start for st in watch.sentences]
        self.sentences = [self._sentence(st) for st in watch.sentences]
        self._raised: dict[int, Any] = {}
        self._plans: dict[tuple, list[_PassView]] = {}

    def drafts(self) -> list[Draft]:
        out = [self._substitution(spot) for spot in self.watch.spots if spot.rec.substituted]
        for sentence in self.sentences:
            for s in sentence.splices:
                if s.kind == "dialect":
                    out.append(self._dialect(sentence, s))
                elif s.kind == "imagery":
                    out.append(self._imagery(sentence, s))
            out += [self._garnish(sentence, k) for k in range(len(sentence.ops))]
        if self.closer is not None:
            out.append(self._closer())
        return out + self._phonetic()

    def _change(self, kind: str, src: tuple[int, int], out: tuple[int, int], entry: Entry | None, vulgarity: int,
                original: str | None = None, alternatives: list[dict] | None = None, locked: list[dict] | None = None,
                **extra) -> dict[str, Any]:
        """A change's contract fields, but its id, masks and covers, which finish() adds."""
        return {"kind": kind, "src_span": list(src), "out_span": list(out),
                "original": self.source[src[0]:src[1]] if original is None else original,
                "output": self.final[out[0]:out[1]], "entry_id": entry.id if entry else None,
                "vulgarity": vulgarity, **extra, "alternatives": alternatives or [], "locked": locked or []}

    # -- sentences --------------------------------------------------------------------------------------------

    def _sentence(self, st: SentenceTrace) -> _Sentence:
        i = st.sent.index
        spots = {sp.splice: sp for sp in self.watch.spots if sp.sent.index == i and sp.rec.substituted}
        dialect = {d.span: d for d in self.result.dialect if d.sentence == i}
        splices: list[_Splice] = []
        for k, (a, b, text) in enumerate(st.splices):
            spot, image = spots.get(k), self.watch.images.get((i, k))
            if spot is not None and image is not None:   # contextual imagery rides on the swap
                splices.append(_Splice(a, b, text[:-len(image[1])], "substitution", spot))
                splices.append(_Splice(b, b, image[1], "imagery", image[0]))
            elif spot is not None:
                splices.append(_Splice(a, b, text, "substitution", spot))
            elif image is not None:
                splices.append(_Splice(a, b, text, "imagery", image[0]))
            else:
                splices.append(_Splice(a, b, text, "dialect", dialect.get((a, b))))
        ops = self.watch.ops.get(i, [])
        layout = _Layout(self._splice_edits(st.sent.tokens[0].start, splices), [op.edit for op in ops], st.garnished)
        return _Sentence(st, splices, ops, first_replaced(st.records, st.sent.tokens), layout)

    @staticmethod
    def _splice_edits(base: int, splices: list[_Splice]) -> list[Edit]:
        return sorted((s.start - base, s.end - base, len(s.text)) for s in splices)

    def _telling(self, sentence: _Sentence, splices: list[_Splice], first: bool,
                 ops: Sequence[_Op | None] | None = None) -> _Layout:
        """The sentence told with these splices and this garnish (its own unless given; None leaves one out), each
        garnish put in as the engine put it. first: whether it now starts with a lower-case swap."""
        st, start = sentence.trace, sentence.offset
        spliced = st.sent.text
        for s in sorted(splices, key=lambda s: (s.start, s.end), reverse=True):
            spliced = spliced[:s.start - start] + s.text + spliced[s.end - start:]
        ops = sentence.ops if ops is None else ops
        text, edits = self.translator.replay_garnish(spliced, st.sent, self.run,
                                                     [(o.placement, o.form) for o in ops if o], first)
        placed = iter(edits)
        return _Layout(self._splice_edits(start, splices), [next(placed) if o else None for o in ops], text)

    # -- from a sentence to the final text, and back ----------------------------------------------------------------

    def _joined(self, pos: int, bias: Bias) -> int:
        """A position in the joined text (before phonetic), past the closer."""
        return map_position([self.closer.edit], pos, bias) if self.closer is not None else pos

    def _to_final(self, sentence: _Sentence, ga: int, gb: int) -> tuple[int, int]:
        """A span of a sentence's garnished text in the final text."""
        base = sentence.trace.start
        return self._final_span(self._joined(base + ga, "right"), self._joined(base + gb, "left"))

    def _bounds(self, a: int, b: int, flags: set[str]) -> tuple[list[tuple[int, int]], tuple[int, int]]:
        """A region of the joined text: its bounds in each phonetic pass's input, and in the final text. An
        insertion at the region's start (a zero-width match there) belongs to it; one at its end doesn't."""
        bounds = []
        for p in self.passes:
            bounds.append((a, b))
            a, inside = _walk(p.edits, a, False)
            if inside is not None:
                flags.add("straddle-left")
                a = inside[0]
            b, inside = _walk(p.edits, b, False)
            if inside is not None:
                flags.add("straddle-right")
                b = inside[1]
        return bounds, (a, b)

    def _final_span(self, a: int, b: int, first_pass: int = 0) -> tuple[int, int]:
        """A span in pass first_pass's input in the final text, taking in a phonetic edit across either end."""
        for p in self.passes[first_pass:]:
            a, b = map_outward(p.edits, a, "start"), map_outward(p.edits, b, "end")
            b = max(a, b)
        return a, b

    def _source(self, pos: int, side: Side) -> int:
        """A position in the joined text (the closer in it) back in the source."""
        if self.closer is not None:
            pos = unmap_position([self.closer.edit], pos, side)
        i = bisect_right(self.starts, pos) - 1
        if i < 0:
            return pos
        sentence = self.sentences[i]
        local = pos - sentence.trace.start
        if local > len(sentence.layout.text):   # between sentences, kept as written
            return sentence.trace.sent.end + local - len(sentence.layout.text)
        return sentence.offset + sentence.layout.back(local, side)

    # -- the region phonetic pass ---------------------------------------------------------------------------------

    def _plan(self, bounds: list[tuple[int, int]]) -> list[_PassView]:
        """What each pass reads around a region, worked out once for every text rendered over it."""
        key = tuple(bounds)
        plan = self._plans.get(key)
        if plan is None:
            plan = self._plans[key] = [_PassView(p, a, b) for p, (a, b) in zip(self.passes, bounds)]
        return plan

    def _phonetic_region(self, text: str, bounds: list[tuple[int, int]], flags: set[str]) -> tuple[str, int]:
        """Each rule's pass over a region's text only. Its count starts from the matches before the region in the
        base text, and each match is gated as the engine gates it (garnish.phonetic_admits), reading the base text
        either side (lookaround, the text before, quotes, questions, kept and preserved spans). Flags a match
        across the region's edge, or a neighbour's match its lookaround makes depend on the region. Returns the
        text and the strongest swear infix it put in."""
        seed, infix, trace = self.result.seed, 0, self.watch.trace
        for v in self._plan(bounds):
            p, rule = v.pass_, v.pass_.rule
            window = v.left + text + v.right
            if v.quiet:
                folded = window.casefold()
                if not any(t in folded for t in v.triggers):
                    continue   # no match can be in the window, and the base has none beside the region either
            off, end, n = len(v.left), len(v.left) + len(text), v.count
            if v.straddle:
                flags.add("straddle-left")
            pieces, last = [], off
            context_left, context_right = [], []
            for m in rule.pattern.finditer(window):
                ms, me = m.start(), m.end()
                if ms < off:
                    if me > off:
                        flags.add("straddle-left")
                    elif ms >= off - CONTEXT + MARGIN:
                        context_left.append((ms - off, m.group(0)))
                    continue
                if ms >= end:
                    if ms < end + CONTEXT - MARGIN:
                        context_right.append((ms - end, m.group(0)))
                    continue
                if me > end:
                    flags.add("straddle-right")
                n += 1
                pos = v.position(ms - off)
                if not phonetic_admits(rule, pos, lambda: p.before[:v.a] + text[:ms - off], p.questions,
                                       lambda: trace.kept(p) + trace.preserved(p)):
                    continue
                out = phonetic_replacement(rule, m, n, seed, p.scale, in_dialogue(pos, p.quotes))
                if out is None:
                    continue
                pieces += [window[last:ms], out]
                last = me
                infix = max(infix, rule.vulgarity)
            if pieces:
                pieces.append(window[last:end])
                text = "".join(pieces)
            if context_left != v.base_left:
                flags.add("context-left")
            if context_right != v.base_right:
                flags.add("context-right")
        return text, infix

    # -- substitutions ----------------------------------------------------------------------------------------------

    def _substitution(self, spot: Spot) -> Draft:
        sentence = self.sentences[spot.sent.index]
        options = [self._option(spot, spot.rec.chosen)]
        options += [self._option(spot, c) for c in spot.keep if c.entry.id != spot.rec.chosen.entry.id]
        options += [self._option(spot, c, v) for v, c in self._locked(spot)]
        options = [o for o in options if not o.rendering.echo]
        region, unsettled = self._render_spot(sentence, spot, options)
        a, b = region.final
        pick = options[0]
        withheld = self._withheld(self.restore(pick.text, whole=False), region.final, unsettled)
        if withheld:   # offer the pick alone, as the output has it, rather than a swap that may read wrong
            options = [pick]
            pick.text = self.final[a:b]
        toks = spot.sent.tokens
        total = sum(o.candidate.weight for o in options if o.locked_at is None)
        offered = [o for o in options if o.locked_at is None]
        locked = [o for o in options if o.locked_at is not None]
        change = self._change(
            "substitution", (toks[region.start].start, toks[region.end - 1].end), (a, b), pick.entry,
            self._vulgarity(pick),
            alternatives=[{"entry_id": o.entry.id, "weight": round(o.candidate.weight / total, 4),
                           "rendered": self.restore(o.text, whole=False), "out_span": [a, b],
                           "vulgarity": self._vulgarity(o)} for o in offered],
            locked=[{"entry_id": o.entry.id, "vulgarity": max(o.locked_at, self._vulgarity(o)),
                     "rendered": self.restore(o.text, whole=False), "out_span": [a, b]} for o in locked])
        return Draft(change, "", pick.entries, [o.entries for o in offered + locked], withheld)

    def _withheld(self, pick: str, region: tuple[int, int], unsettled: bool) -> str | None:
        """Why a change's renderings are withheld, if they are: its pick, rendered over its region (protected spans
        restored), isn't the output there, or a phonetic match still reads across the region's edge."""
        if pick != self.final[region[0]:region[1]]:
            return PICK_DIFFERS
        return REGION_UNSETTLED if unsettled else None

    def _option(self, spot: Spot, candidate: Candidate, locked_at: int | None = None) -> _Option:
        rendering = self.translator.render_at_spot(candidate, spot, replace(self.run, state=spot.state.copy()))
        return _Option(candidate, rendering, locked_at)

    @staticmethod
    def _vulgarity(o: _Option) -> int:
        """What a rendering needs: the strongest of its entry, a stacked idiom, its riff and any infix in it."""
        r = o.rendering
        riff = next((x.vulgarity for x in o.entry.riffs if x.text == r.riff), 0) if r.riff else 0
        return max(o.entry.vulgarity, r.stacked.entry.vulgarity if r.stacked else 0, riff, o.infix)

    def _locked(self, spot: Spot) -> list[tuple[int, Candidate]]:
        """The candidates the vulgarity cap alone holds back: eligible with only the cap raised (every other check
        as it is: level, registers, gates, grammar, span, document type, what the text has said, variety) and
        rated above the cap in effect, each with the lowest vulgarity that lets it in. Raising the cap also
        reweighs (swearing leans in), so variety's best few can take in a clean entry; that one isn't locked."""
        have = {c.entry.id for c in spot.keep}
        det, cap = spot.rec.det, self.run.eff.vulgarity
        out = []
        for v in range(cap + 1, 4):
            if v not in self._raised:
                self._raised[v] = resolve(replace(self.run.pol, vulgarity=v), self.translator.dictionary)
            keep, _ = self.translator.eligible(det, spot.sent, self.run, self._raised[v], spot.state, spot.taken,
                                               self.translator.dictionary.idioms_for(det.concepts))
            for c in keep:
                if c.entry.id not in have and c.entry.vulgarity > cap:
                    have.add(c.entry.id)
                    out.append((v, c))
        return out

    def _render_spot(self, sentence: _Sentence, spot: Spot, options: list[_Option]) -> tuple[_Region, bool]:
        """Every option over one region: the union of their token spans, widened a word where a phonetic match
        crosses its edge or a neighbour's lookaround reads it, and over any other splice it cuts. Also whether a
        match still reads across its edge (at the sentence's edge, or after widening as far as it goes)."""
        toks = spot.sent.tokens

        def render(start: int, end: int) -> tuple[_Region, set[str], tuple[int, int]]:
            start, end = self._join(sentence, spot, start, end)
            region = self._base_region(sentence, start, end)
            flags = set(region.flags)
            for o in options:
                o.text, o.infix = self._render_option(sentence, spot, o, region, flags)
            return region, flags, (start, end)

        return self._widen((min(o.rendering.start for o in options), max(o.rendering.end for o in options)),
                           render, lambda i, step: min(max(i + step, 0), len(toks)))

    @staticmethod
    def _widen(span: tuple[int, int], render: Callable[[int, int], tuple[Any, set[str], tuple[int, int]]],
               step: Callable[[int, int], int]) -> tuple[Any, bool]:
        """A region rendered (render: what it renders, its flags and the span it took), widened a word at an edge
        (step: a position one word out, -1 left or +1 right, or the same at the sentence's edge) where a phonetic
        match crosses that edge or a neighbour's lookaround reads it, up to WIDEN times. Also whether a match still
        reads across its edge (at the sentence's edge, or after widening as far as it goes)."""
        for _ in range(WIDEN + 1):
            rendered, flags, (lo, hi) = render(*span)
            left = bool(flags & {"straddle-left", "context-left"})
            right = bool(flags & {"straddle-right", "context-right"})
            span = (step(lo, -1) if left else lo, step(hi, 1) if right else hi)
            if span == (lo, hi):
                return rendered, left or right
        return rendered, True

    @staticmethod
    def _join(sentence: _Sentence, spot: Spot, start: int, end: int) -> tuple[int, int]:
        """Widen a token span over any other splice it cuts into."""
        toks = spot.sent.tokens
        while True:
            a, b = toks[start].start, toks[end - 1].end
            cut = [s for s in sentence.splices if s.owner is not spot and s.start < b and a < s.end
                   and not (a <= s.start and s.end <= b)]
            if not cut:
                return start, end
            for s in cut:
                start = min(start, next(i for i, t in enumerate(toks) if t.end > s.start))
                end = max(end, max(i for i, t in enumerate(toks) if t.start < s.end) + 1)

    def _base_region(self, sentence: _Sentence, start: int, end: int) -> _Region:
        toks = sentence.trace.sent.tokens
        a, b = toks[start].start - sentence.offset, toks[end - 1].end - sentence.offset
        ga, gb = sentence.layout.forward(a, "right"), sentence.layout.forward(b, "left")
        base = sentence.trace.start
        region = _Region(start, end)
        region.bounds, region.final = self._bounds(self._joined(base + ga, "right"), self._joined(base + gb, "left"),
                                                   region.flags)
        return region

    def _render_option(self, sentence: _Sentence, spot: Spot, o: _Option, region: _Region,
                       flags: set[str]) -> tuple[str, int]:
        """An option's text over the region: its splice in place of the pick's (contextual imagery on the pick
        follows it), the sentence's garnish put back, then the region's phonetic pass."""
        toks, r = spot.sent.tokens, o.rendering
        a, b = toks[r.start].start, toks[r.end - 1].end
        splices, rides = [], None
        for s in sentence.splices:
            if s.owner is spot:
                continue
            if s.kind == "imagery" and s.start == spot.rec.out_span[1] and any(
                    x.owner is spot and x.end == s.start for x in sentence.splices):
                rides = s
                continue
            if s.kind != "imagery" and s.start < b and a < s.end:
                continue     # a neighbour this option's span takes in
            splices.append(s)
        splices.append(_Splice(a, b, r.text, "substitution", spot))
        if rides is not None:
            splices.append(_Splice(b, b, rides.text, "imagery", rides.owner))
        first = first_replaced(sentence.trace.records, toks, (spot.rec, a, o.entry))
        layout = self._telling(sentence, splices, first)
        lo, hi = toks[region.start].start - sentence.offset, toks[region.end - 1].end - sentence.offset
        ga, gb = layout.forward(lo, "right"), layout.forward(hi, "left")
        return self._phonetic_region(layout.text[ga:gb], region.bounds, flags)

    # -- dialect and imagery --------------------------------------------------------------------------------------

    def _dialect(self, sentence: _Sentence, s: _Splice) -> Draft:
        layout = sentence.layout
        ga = layout.forward(s.start - sentence.offset, "right")
        gb = max(ga, layout.forward(s.end - sentence.offset, "left"))
        d = s.owner
        pair = ({"english": d.english, "before": d.before, "after": d.after} if d is not None
                else {"english": None, "before": self.source[s.start:s.end], "after": s.text})
        return Draft(self._change("dialect", (s.start, s.end), self._to_final(sentence, ga, gb), None, 0, pair=pair))

    def _imagery(self, sentence: _Sentence, s: _Splice) -> Draft:
        """A contextual image after a term: garnish with no entry, which goes without a trace when removed."""
        layout, base = sentence.layout, sentence.trace.start
        at = map_position(layout.splices, s.start - sentence.offset, "left")
        ga, gb = layout.after_garnish(at, "right", 0), layout.after_garnish(at + len(s.text), "left", 0)
        out = self._to_final(sentence, ga, gb)
        flags: set[str] = set()
        bounds, region = self._bounds(self._joined(base + ga, "right"), self._joined(base + gb, "left"), flags)
        pick = self.restore(self._phonetic_region(layout.text[ga:gb], bounds, flags)[0], whole=False)
        self._phonetic_region("", bounds, flags)   # its removal, for what a neighbour's lookaround reads there
        withheld = self._withheld(pick, region, bool(flags))
        removed = {} if withheld else {"removed": {"out_span": list(out), "rendered": ""}}
        change = self._change("garnish", (s.start, s.start), out, None, 0, original="", placement="riff",
                              image_id=s.owner, **removed)
        return Draft(change, "riff", withheld=withheld)

    # -- garnish ------------------------------------------------------------------------------------------------

    def _garnish(self, sentence: _Sentence, k: int) -> Draft:
        """A placed garnish: its words; the region a swap or its removal replaces (an opener's or a connective's
        takes in the next word, whose capital it lowered); the other garnish the engine weighed there. Each one,
        the pick and the removal included, is told with the sentence's other garnish and put through the region's
        phonetic pass. The region widens a word as a swap's does (_widen), never cutting another change's words.
        Where the pick doesn't read as the output there, or a match still reads across the region's edge, the pick
        is offered alone, without a removal, and the change is named under withheld."""
        op, base = sentence.ops[k], sentence.trace.start
        p, _, n = op.edit
        a = sentence.layout.after_garnish(p, "right", k + 1)
        out = self._to_final(sentence, a, sentence.layout.after_garnish(p + n, "left", k + 1))
        src = self._source(base + a, "start")
        before = self._before(sentence, k)
        q = _first_word_end(before, p) if op.placement in ("opener", "connective") else p
        words = [m.span() for m in _WORD_RE.finditer(before)]
        held = self._held(sentence, k)
        # the removal, then the pick and every other garnish of its placement (each fits where it did: a
        # connective refuses only what precedes it)
        swaps = [None] + [op if entry is op.entry else replace(op, entry=entry, form=op.offer.words(entry))
                          for entry in op.offer.pool]

        def render(lo: int, hi: int) -> tuple[tuple[tuple[int, int], list[str]], set[str], tuple[int, int]]:
            lo, hi = _outside(held, lo, hi)
            flags: set[str] = set()
            ra, rb = self._garnish_region(sentence.layout, k, lo, hi, True)
            bounds, region = self._bounds(self._joined(base + ra, "right"), self._joined(base + rb, "left"), flags)
            texts = []
            for swap in swaps:   # each told with the k-th garnish swapped (None: taken out), after the phonetic pass
                layout = self._telling(sentence, sentence.splices, sentence.first_replaced,
                                       [swap if i == k else o for i, o in enumerate(sentence.ops)])
                ga, gb = self._garnish_region(layout, k, lo, hi, swap is not None)
                texts.append(self.restore(self._phonetic_region(layout.text[ga:gb], bounds, flags)[0], whole=False))
            return (region, texts), flags, (lo, hi)

        def step(pos: int, way: int) -> int:
            if way < 0:
                return max((s for s, _ in words if s < pos), default=pos)
            return min((e for _, e in words if e > pos), default=pos)

        (region, (removal, *texts)), unsettled = self._widen((p, q), render, step)
        alternatives, withheld = self._garnish_alternatives(op, texts, region, unsettled)
        change = self._change("garnish", (src, src), out, op.entry, op.entry.vulgarity, original="",
                              alternatives=alternatives, placement=op.placement,
                              **({} if withheld else {"removed": {"out_span": list(region), "rendered": removal}}))
        return Draft(change, op.placement, [op.entry.id], [[o["entry_id"]] for o in alternatives], withheld)

    @staticmethod
    def _held(sentence: _Sentence, k: int) -> list[tuple[int, int]]:
        """The other changes' words in the text before the k-th garnish went in: each splice's text, and each
        garnish before it. A garnish's region widens over them whole."""
        layout, spans, delta = sentence.layout, [], 0
        for a, b, n in layout.splices:
            spans.append((a + delta, a + delta + n))
            delta += n - (b - a)
        for e in layout.garnish[:k]:
            if e is not None:
                spans = [(map_position([e], s, "right"), map_position([e], t, "left")) for s, t in spans]
                spans.append((e[0], e[0] + e[2]))
        return spans

    def _garnish_alternatives(self, op: _Op, texts: list[str], region: tuple[int, int],
                              unsettled: bool) -> tuple[list[dict[str, Any]], str | None]:
        """A garnish's alternatives from each pool entry's rendering over the region, and why they're withheld
        (the pick then offered alone, as the output has it), if they are."""
        withheld = self._withheld(texts[op.offer.pool.index(op.entry)], region, unsettled)
        alternatives = [{"entry_id": entry.id, "weight": weight, "rendered": text, "out_span": list(region),
                         "vulgarity": entry.vulgarity}
                        for entry, weight, text in zip(op.offer.pool, op.offer.weights, texts)
                        if not withheld or entry is op.entry]
        if withheld:
            alternatives[0]["rendered"] = self.final[region[0]:region[1]]
        return _shares(alternatives), withheld

    def _before(self, sentence: _Sentence, k: int) -> str:
        """The sentence's text just before its k-th garnish went in."""
        if sentence.before is None:
            st, texts = sentence.trace, [sentence.trace.spliced]
            for o in sentence.ops:
                texts.append(self.translator.replay_garnish(texts[-1], st.sent, self.run, [(o.placement, o.form)],
                                                            sentence.first_replaced)[0])
            sentence.before = texts
        return sentence.before[k]

    @staticmethod
    def _garnish_region(layout: _Layout, k: int, lo: int, hi: int, placed: bool) -> tuple[int, int]:
        """The k-th garnish's region in a telling: lo to hi in the text before it went in (from where it goes, or
        a word or more before, to the end of the word an opener lowers, or where it goes, or a word or more
        after), through itself where the telling has it, and the garnish after."""
        b = map_position([layout.garnish[k]], hi, "right") if placed else hi
        return layout.after_garnish(lo, "right", k + 1), layout.after_garnish(b, "left", k + 1)

    def _closer(self) -> Draft:
        """The closer, as a placed garnish is built: the pick and each other closer the engine weighed put at the
        end of the text without it, then through the region's phonetic pass; its removal leaves nothing there."""
        op = self.closer
        x, _, n = op.edit
        flags: set[str] = set()
        bounds, region = self._bounds(x, x + n, flags)
        body = self.watch.joined[:x] + self.watch.joined[x + n:]

        def told(form: str) -> str:
            placed, (at, _, m) = place_garnish(body, "closer", form)
            return self.restore(self._phonetic_region(placed[at:at + m], bounds, flags)[0], whole=False)

        self._phonetic_region("", bounds, flags)   # its removal, for what a neighbour's lookaround reads there
        texts = [told(op.form if entry is op.entry else op.offer.words(entry)) for entry in op.offer.pool]
        alternatives, withheld = self._garnish_alternatives(op, texts, region, bool(flags))
        src = self._source(x, "start")
        change = self._change("garnish", (src, src), region, op.entry, op.entry.vulgarity, original="",
                              alternatives=alternatives, placement="closer",
                              **({} if withheld else {"removed": {"out_span": list(region), "rendered": ""}}))
        return Draft(change, "closer", [op.entry.id], [[o["entry_id"]] for o in alternatives], withheld)

    # -- phonetic --------------------------------------------------------------------------------------------------

    def _phonetic(self) -> list[Draft]:
        """Each drawl, spelling or swear infix edit, in the final text (taking in a later rule's edit across it) and
        in the source (the text it came from: inside a swap or garnish, that whole span)."""
        out = []
        for k, p in enumerate(self.passes):
            after = self.passes[k + 1].before if k + 1 < len(self.passes) else self.watch.final
            delta = 0
            for s, e, n in p.edits:
                a = s + delta
                delta += n - (e - s)
                src = (self._pass_source(k, s, "start"), self._pass_source(k, e, "end"))
                kind = "swear_infix" if p.rule.is_infix else "phonetic"
                rule = {"id": p.rule.id, "kind": "infix" if p.rule.is_infix else p.rule.kind,
                        "min_level": p.rule.min_level, "before": p.before[s:e], "after": after[a:a + n]}
                out.append(Draft(self._change(kind, src, self._final_span(a, a + n, k + 1), None, p.rule.vulgarity,
                                              original=self.source[src[0]:src[1]], rule=rule), p.rule.id))
        return out

    def _pass_source(self, k: int, pos: int, side: Side) -> int:
        for p in reversed(self.passes[:k]):
            pos = unmap_position(p.edits, pos, side)
        return self._source(pos, side)


# -- helpers ----------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _triggers(pattern) -> frozenset[str] | None:
    """Words one of which (case folded) every match of a pattern contains, read from its literal runs; None where
    there are none to read (a rule that is all lookaround) or the pattern can't be read, which costs the region
    pass a full look at that rule, nothing more. A window with none of them holds no match."""
    try:   # Python's own regular expression parser (re._parser from 3.11, sre_parse before)
        try:
            from re import _constants as constants
            from re import _parser as parser
        except ImportError:   # pragma: no cover - Python 3.10
            import sre_constants as constants
            import sre_parse as parser
        found = _required(parser.parse(pattern.pattern, pattern.flags), constants)
    except Exception:   # an internal API: whatever it does, fall back to the full pass
        return None
    return frozenset(found) if found else None


def _required(seq, constants) -> set[str] | None:
    """For a parsed pattern sequence: a set of words one of which every match contains (the most telling one), or
    None. Consecutive literals are a word; a group, a branch (each way's words) and a repeat of at least one
    count too."""
    repeats = tuple(op for op in (constants.MAX_REPEAT, constants.MIN_REPEAT,
                                  getattr(constants, "POSSESSIVE_REPEAT", None)) if op)
    options: list[set[str]] = []
    run: list[str] = []
    for op, arg in seq:
        if op is constants.LITERAL:
            run.append(chr(arg))
            continue
        if run:
            options.append({"".join(run).casefold()})
            run = []
        inner = None
        if op is constants.SUBPATTERN:
            inner = _required(arg[-1], constants)
        elif op is constants.BRANCH:
            ways = [_required(way, constants) for way in arg[1]]
            inner = set().union(*ways) if all(ways) else None
        elif op in repeats and arg[0] >= 1:
            inner = _required(arg[2], constants)
        if inner:
            options.append(inner)
    if run:
        options.append({"".join(run).casefold()})
    return max(options, key=lambda o: min(map(len, o))) if options else None


_WORD_RE = re.compile(r"[\w'\u2019]+")   # a word a garnish's region widens by


def _outside(held: list[tuple[int, int]], lo: int, hi: int) -> tuple[int, int]:
    """A span widened over any held span (another change's words) its ends cut into."""
    for s, e in held:
        if s < lo < e:
            lo = s
        if s < hi < e:
            hi = e
    return lo, hi


def _first_word_end(text: str, at: int) -> int:
    """Where the word an opener or connective lowers ends, in the text before it went in at `at`."""
    m = FIRST_WORD_RE.match(text, at)
    return m.end() if m else at


def _shares(alternatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(o["weight"] for o in alternatives)
    for o in alternatives:
        o["weight"] = round(o["weight"] / total, 4)
    return alternatives


def _cover(drafts: list[Draft]) -> None:
    """Fills each change's covers: in output order, the other changes whose output or region overlaps one of its
    regions. Swapping or removing the change rewrites text those stand on. Two changes with regions that overlap
    cover each other; a change with no region (a drawl, an infix, a US word) covers nothing."""
    regions = [sorted({tuple(r["out_span"]) for r in d.renderings()}) for d in drafts]
    spans = [[tuple(d.change["out_span"]), *rs] for d, rs in zip(drafts, regions)]
    reach = [_extent(rs) for rs in regions]          # where a change's regions lie, None for none
    extent = [_extent(ss) for ss in spans]           # where a change's output and regions lie
    for i, d in enumerate(drafts):
        d.change["covers"] = [
            other.change["id"] for k, other in enumerate(drafts)
            if k != i and reach[i] is not None and _reaches(reach[i], extent[k])
            and any(_reaches(r, s) for r in regions[i] for s in spans[k])]


def _extent(spans: list[tuple[int, int]]) -> tuple[int, int] | None:
    """The span from the first start to the last end, or None for no spans."""
    return (min(a for a, _ in spans), max(b for _, b in spans)) if spans else None


def _reaches(region: tuple[int, int], span: tuple[int, int]) -> bool:
    """Whether replacing region rewrites any of span: they share a character, or an empty span sits strictly inside
    region (an empty span at its edge is left alone)."""
    lo, hi = region
    a, b = span
    return a < hi and lo < b
