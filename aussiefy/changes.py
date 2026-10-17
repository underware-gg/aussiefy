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
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

from .cards import entry_card
from .engine import PassObserver, Result, SentenceTrace, Spot, SpotRendering, SubstitutionRecord, Translator
from .garnish import (Edit, PhoneticPass, PhoneticTrace, phonetic_replacement, place_garnish, realise_garnish,
                      tier_match)
from .masks import masks
from .model import Dictionary
from .policy import resolve
from .schema import Entry
from .select import Candidate

try:   # the regular expression parser, for the literal words a phonetic rule needs (Python 3.11 moved it)
    from re import _constants as _C
    from re import _parser as _regex
except ImportError:   # pragma: no cover - Python 3.10
    import sre_constants as _C
    import sre_parse as _regex

VERSION = 1          # the changes contract; a change to its shape or to how ids are made bumps it
SCHEMA = Path(__file__).resolve().parent / "data" / "changes.schema.json"   # its JSON Schema
CONTEXT = 64         # characters of whole-text context read either side of a region, for the rules' lookaround
MARGIN = 16          # ... the outer part of which is read, never compared (a match there may be cut short)
WIDEN = 4            # the most words a region widens by, each side, for a phonetic match across its edge
KINDS = ("substitution", "dialect", "garnish", "swear_infix", "phonetic")   # also the order covers ranks them in
_REPEATS = tuple(op for op in (_C.MAX_REPEAT, _C.MIN_REPEAT, getattr(_C, "POSSESSIVE_REPEAT", None)) if op)


@dataclass
class ChangeSet:
    """A translation and its changes under the contract VERSION: `changes` in output order, and the card of every
    entry they name, each sent once."""
    result: Any                       # engine.Result, or markdown.DocumentResult for a Markdown document
    changes: list[dict[str, Any]]
    entries: dict[str, dict[str, Any]]
    version: int = VERSION

    @property
    def text(self) -> str:
        return self.result.text

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "text": self.result.text, "changes": self.changes, "entries": self.entries}


def build(translator: Translator, text: str, **options) -> ChangeSet:
    """Translate text (Translator.translate's options, without a rewriter) and build its changes in the same pass."""
    result, raw = collect(translator, text, **options)
    return finish(result, raw, translator.dictionary, result.vulgarity)


def collect(translator: Translator, text: str, _observer: Watch | None = None,
            **options) -> tuple[Result, list[dict[str, Any]]]:
    """The translation and its changes before finish(): in its own output's and source's coordinates, the id field
    holding only the placement or rule that finish() adds to the kind and source span. A document adapter offsets
    each unit's changes, then finishes them together."""
    if options.get("rewriter") is not None:
        raise ValueError("a sentence rewritten whole has no changes to swap; build changes without a rewriter")
    watch = _observer if _observer is not None else Watch()
    result = translator.translate(text, **options, _observer=watch)
    return result, _Builder(translator, watch, result).changes()


def finish(result: Any, raw: list[dict[str, Any]], dictionary: Dictionary, cap: int) -> ChangeSet:
    """Order the changes, number repeated ids, list what each one's swap covers, mark each rendering's maskable
    words, and gather the cards of the entries they name (riffs under the cap)."""
    for c in raw:   # its kind and source span, and a placement or rule where those alone could repeat
        (a, b), key = c["src_span"], c["id"]
        c["id"] = f"{c['kind']}:{a}-{b}" + (f":{key}" if key else "")
    changes = sorted(raw, key=lambda c: (c["out_span"][0], c["out_span"][1], KINDS.index(c["kind"]), c["id"]))
    seen: dict[str, int] = {}
    for c in changes:
        n = seen[c["id"]] = seen.get(c["id"], 0) + 1
        if n > 1:
            c["id"] += f"#{n}"
    _cover(changes)
    names: set[str] = set()

    def masked(text: str, rendering: dict[str, Any]) -> list[dict[str, Any]]:
        """A rendering's maskable words: listed swears, compounds, and its own entries' mask words."""
        ids = [i for i in [rendering.get("entry_id"), *rendering.pop("_with", ())] if i]
        words: dict[str, int] = {}
        for e in (dictionary.entries[i] for i in ids):
            for w in e.mask:
                words[w] = max(words.get(w, 0), e.vulgarity)
        return masks(text, dictionary.swears, dictionary.swear_compounds, words)

    for c in changes:
        for o in c["alternatives"] + c["locked"]:
            o["masks"] = masked(o["rendered"], o)
            names.add(o["entry_id"])
        c["masks"] = masked(c["output"], c)
        if c["entry_id"]:
            names.add(c["entry_id"])
    return ChangeSet(result, changes, {i: entry_card(dictionary.entries[i], cap) for i in sorted(names)})


# -- offsets ------------------------------------------------------------------------------------------------------

class Straddle(Exception):
    """A position falls inside an edit: a match across a region's edge."""


def map_position(edits: Sequence[Edit], pos: int, bias: str) -> int:
    """A position through edits (start, end, new length), sorted, in the input's coordinates. At an insertion, bias
    "left" stays before it and "right" goes after; a position inside a replaced span raises Straddle."""
    delta = 0
    for a, b, n in edits:
        if pos < a or (pos == a and (b > a or bias == "left")):
            break
        if pos >= b:
            delta += n - (b - a)
            continue
        raise Straddle(a, b, pos)
    return pos + delta


def map_outward(edits: Sequence[Edit], pos: int, side: str) -> int:
    """map_position for one end of a span, which takes in an edit it falls inside: a "start" goes to the edit's
    start, an "end" to its end."""
    delta = 0
    for a, b, n in edits:
        if pos < a or (pos == a and (b > a or side == "start")):
            break
        if pos >= b:
            delta += n - (b - a)
            continue
        return a + delta if side == "start" else a + delta + n
    return pos + delta


def unmap_position(edits: Sequence[Edit], pos: int, side: str) -> int:
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
    """A garnish the engine placed, and where it went in the text before it."""
    placement: str
    entry: Entry
    form: str
    edit: Edit


class Watch(PassObserver):
    """Keeps what the builder needs from the pass: the state at each pick (copied), each sentence's splices and
    garnish, contextual imagery, the closer and the phonetic passes."""

    def __init__(self):
        self.spots: list[Spot] = []
        self.sentences: list[SentenceTrace] = []
        self.ops: dict[int, list[_Op]] = defaultdict(list)
        self.images: dict[tuple[int, int], tuple[str, str]] = {}   # (sentence, source end) -> (image id, words)
        self.closer: _Op | None = None

    def begin(self, run):
        self.run = run

    def spot(self, spot):
        self.spots.append(replace(spot, state=spot.state.copy(), replaced=set(spot.replaced), said=dict(spot.said),
                                  occupied=set(spot.occupied)))

    def imagery(self, sentence, image_id, end, suffix):
        self.images[(sentence, end)] = (image_id, suffix)

    def garnish(self, sentence, placement, entry, form, edit):
        if placement == "closer":
            self.closer = _Op(placement, entry, form, edit)
        else:
            self.ops[sentence].append(_Op(placement, entry, form, edit))

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

    def forward(self, pos: int, bias: str) -> int:
        return self.after_garnish(map_position(self.splices, pos, bias), bias, 0)

    def after_garnish(self, pos: int, bias: str, first: int) -> int:
        for e in self.garnish[first:]:
            if e is not None:
                pos = map_position([e], pos, bias)
        return pos

    def back(self, pos: int, side: str) -> int:
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
    layout: _Layout | None = None
    before: list[str] | None = None     # its text before each garnish went in (read on demand)

    @property
    def offset(self) -> int:
        return self.trace.sent.tokens[0].start


@dataclass
class _Option:
    candidate: Candidate
    rendering: SpotRendering
    stacked: Entry | None = None
    riff: str | None = None
    locked_at: int | None = None
    text: str = ""
    infix: int = 0

    @property
    def entry(self) -> Entry:
        return self.candidate.entry


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
    (where its count starts), the neighbours' matches to compare an option's with, and whether the region sits
    where the rule is kept out (a question, a kept or preserved span) or in dialogue."""

    def __init__(self, trace: PhoneticTrace, p: PhoneticPass, a: int, b: int):
        self.trace, self.pass_, self.a, self.b = trace, p, a, b
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

    @cached_property
    def blocked(self) -> bool:
        p, a, b = self.pass_, self.a, self.b
        return (bool(p.questions) and _inside(p.questions, a, b) or _inside(self.trace.kept(p), a, b)
                or _inside(self.trace.preserved(p), a, b))

    @cached_property
    def dialogue(self) -> bool:
        return _inside(self.pass_.quotes, self.a, self.b)


class _Builder:
    def __init__(self, translator: Translator, watch: Watch, result: Result):
        self.tr, self.w, self.result = translator, watch, result
        self.run = watch.run
        self.passes: list[PhoneticPass] = watch.trace.passes
        self.restore = self.run.masked.restore
        self.final = result.text            # the final text, protected spans restored (the same length)
        self.source = result.source
        self.closer = watch.closer
        self.starts = [st.start for st in watch.sentences]
        self.sentences = [self._sentence(st) for st in watch.sentences]
        self._raised: dict[int, Any] = {}
        self._plans: dict[tuple, list[_PassView]] = {}

    def changes(self) -> list[dict[str, Any]]:
        out = [self._substitution(spot) for spot in self.w.spots if spot.rec.substituted]
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
                key: str = "", original: str | None = None, **extra) -> dict[str, Any]:
        return {"id": key, "kind": kind,
                "src_span": list(src), "out_span": list(out),
                "original": self.source[src[0]:src[1]] if original is None else original,
                "output": self.final[out[0]:out[1]], "entry_id": entry.id if entry else None,
                "vulgarity": vulgarity, "masks": [], **extra,
                "alternatives": extra.get("alternatives", []), "locked": extra.get("locked", []), "covers": []}

    # -- sentences --------------------------------------------------------------------------------------------

    def _sentence(self, st: SentenceTrace) -> _Sentence:
        i = st.sent.index
        spots = {sp.splice: sp for sp in self.w.spots if sp.sent.index == i and sp.rec.substituted}
        dialect = {d.span: d for d in self.run.dialect if d.sentence == i}
        splices: list[_Splice] = []
        for k, (a, b, text) in enumerate(st.splices):
            spot = spots.get(k)
            if spot is not None:
                image = self.w.images.get((i, b))
                if image and text != spot.rec.output and text.endswith(image[1]):   # imagery rides on the swap
                    splices.append(_Splice(a, b, text[:-len(image[1])], "substitution", spot))
                    splices.append(_Splice(b, b, image[1], "imagery", image[0]))
                else:
                    splices.append(_Splice(a, b, text, "substitution", spot))
            elif a == b and (i, b) in self.w.images:
                splices.append(_Splice(a, b, text, "imagery", self.w.images[(i, b)][0]))
            else:
                splices.append(_Splice(a, b, text, "dialect", dialect.get((a, b))))
        toks = st.sent.tokens
        first = any(r.substituted and r.out_span[0] == toks[0].start and r.chosen.entry.form[:1].islower()
                    for r in st.records)
        sentence = _Sentence(st, splices, self.w.ops.get(i, []), first)
        sentence.layout = _Layout(self._splice_edits(sentence, splices), [op.edit for op in sentence.ops], st.garnished)
        return sentence

    @staticmethod
    def _splice_edits(sentence: _Sentence, splices: list[_Splice]) -> list[Edit]:
        base = sentence.offset
        return sorted((s.start - base, s.end - base, len(s.text)) for s in splices)

    def _telling(self, sentence: _Sentence, splices: list[_Splice], first_replaced: bool,
                 ops: Sequence[_Op | None] | None = None) -> _Layout:
        """The sentence told with these splices and this garnish (its own unless given; None leaves one out), each
        garnish put in as the engine put it."""
        st, start = sentence.trace, sentence.offset
        spliced = st.sent.text
        for s in sorted(splices, key=lambda s: (s.start, s.end), reverse=True):
            spliced = spliced[:s.start - start] + s.text + spliced[s.end - start:]
        ops = sentence.ops if ops is None else ops
        text, edits = self.tr.replay_garnish(spliced, st.sent, self.run, [(o.placement, o.form) for o in ops if o],
                                             first_replaced)
        placed = iter(edits)
        return _Layout(self._splice_edits(sentence, splices), [next(placed) if o else None for o in ops], text)

    # -- from a sentence to the final text, and back ----------------------------------------------------------------

    def _joined(self, pos: int, bias: str) -> int:
        """A position in the joined text (before phonetic), past the closer."""
        return map_position([self.closer.edit], pos, bias) if self.closer is not None else pos

    def _bounds(self, a: int, b: int, flags: set[str]) -> tuple[list[tuple[int, int]], tuple[int, int]]:
        """A region of the joined text: its bounds in each phonetic pass's input, and in the final text. An
        insertion at the region's start (a zero-width match there) belongs to it; one at its end doesn't."""
        bounds = []
        for p in self.passes:
            bounds.append((a, b))
            try:
                a = map_position(p.edits, a, "left")
            except Straddle:
                flags.add("straddle-left")
                a = map_outward(p.edits, a, "start")
            try:
                b = map_position(p.edits, b, "left")
            except Straddle:
                flags.add("straddle-right")
                b = map_outward(p.edits, b, "end")
        return bounds, (a, b)

    def _final_span(self, a: int, b: int) -> tuple[int, int]:
        """A span of the joined text in the final text, taking in a phonetic edit across either end."""
        for p in self.passes:
            a, b = map_outward(p.edits, a, "start"), map_outward(p.edits, b, "end")
            b = max(a, b)
        return a, b

    def _source(self, pos: int, side: str) -> int:
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
            plan = self._plans[key] = [_PassView(self.w.trace, p, a, b) for p, (a, b) in zip(self.passes, bounds)]
        return plan

    def _phonetic_region(self, text: str, bounds: list[tuple[int, int]], flags: set[str]) -> tuple[str, int]:
        """Each rule's pass over a region's text only. Its count starts from the matches before the region in the
        base text, and it reads the base text's context either side (lookaround, the text before, quotes,
        questions, kept and preserved spans). Flags a match across the region's edge, or a neighbour's match its
        lookaround makes depend on the region. Returns the text and the strongest swear infix it put in."""
        seed, infix = self.run.pol.seed, 0
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
                if v.blocked or (rule.unless_before is not None
                                 and rule.unless_before.search(p.before[:v.a] + text[:ms - off])):
                    continue
                out = phonetic_replacement(rule, m, n, seed, p.scale, v.dialogue)
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

    def _substitution(self, spot: Spot) -> dict[str, Any]:
        sentence = self.sentences[spot.sent.index]
        options = [self._option(spot, spot.rec.chosen)]
        options += [self._option(spot, c) for c in spot.keep if c.entry.id != spot.rec.chosen.entry.id]
        options += [self._option(spot, c, v) for v, c in self._locked(spot)]
        options = [o for o in options if not o.rendering.echo]
        region = self._render_spot(sentence, spot, options)
        a, b = region.final
        pick = options[0]
        if pick.text != self.final[a:b]:   # never seen: offer the pick alone, rather than a swap that may be wrong
            options, pick.text = [pick], self.final[a:b]
        toks = spot.sent.tokens
        total = sum(o.candidate.weight for o in options if o.locked_at is None) or 1.0
        alternatives = [{"entry_id": o.entry.id, "weight": round(o.candidate.weight / total, 4),
                         "rendered": self.restore(o.text, whole=False), "out_span": [a, b],
                         "vulgarity": self._vulgarity(o), "masks": [], "_with": _stacked(o)}
                        for o in options if o.locked_at is None]
        locked = [{"entry_id": o.entry.id, "vulgarity": max(o.locked_at, self._vulgarity(o)),
                   "rendered": self.restore(o.text, whole=False), "out_span": [a, b], "masks": [],
                   "_with": _stacked(o)}
                  for o in options if o.locked_at is not None]
        return self._change("substitution", (toks[region.start].start, toks[region.end - 1].end), (a, b),
                            pick.entry, self._vulgarity(pick), alternatives=alternatives, locked=locked,
                            _with=_stacked(pick))

    def _option(self, spot: Spot, candidate: Candidate, locked_at: int | None = None) -> _Option:
        rec = SubstitutionRecord(spot.rec.span, spot.rec.text, spot.rec.det, spot.sent.index)
        run = replace(self.run, state=spot.state.copy())
        rendering = self.tr.render_at_spot(candidate, rec, spot.keep, spot.sent, run, spot.replaced, spot.said)
        return _Option(candidate, rendering, rec.stacked and rec.stacked.entry, rec.riff, locked_at)

    @staticmethod
    def _vulgarity(o: _Option) -> int:
        """What a rendering needs: the strongest of its entry, a stacked idiom, its riff and any infix in it."""
        riff = next((r.vulgarity for r in o.entry.riffs if r.text == o.riff), 0) if o.riff else 0
        return max(o.entry.vulgarity, o.stacked.vulgarity if o.stacked else 0, riff, o.infix)

    def _locked(self, spot: Spot) -> list[tuple[int, Candidate]]:
        """The candidates that would be eligible if only the vulgarity cap were higher, every other check as it is
        (level, registers, gates, grammar, span, document type, what the text has said, variety), each with the
        lowest vulgarity that lets it in."""
        have = {c.entry.id for c in spot.keep}
        det = spot.rec.det
        taken = (spot.occupied - set(range(det.start, det.end))) | spot.replaced
        out = []
        for v in range(self.run.eff.vulgarity + 1, 4):
            if v not in self._raised:
                self._raised[v] = resolve(replace(self.run.pol, vulgarity=v), self.tr.dictionary)
            keep, _ = self.tr.eligible(det, spot.sent, self.run, self._raised[v], spot.state, taken,
                                       self.tr.dictionary.idioms_for(det.concepts))
            for c in keep:
                if c.entry.id not in have:
                    have.add(c.entry.id)
                    out.append((v, c))
        return out

    def _render_spot(self, sentence: _Sentence, spot: Spot, options: list[_Option]) -> _Region:
        """Every option over one region: the union of their token spans, widened a word where a phonetic match
        crosses its edge or a neighbour's lookaround reads it, and over any other splice it cuts."""
        toks = spot.sent.tokens
        start = min(o.rendering.start for o in options)
        end = max(o.rendering.end for o in options)
        for _ in range(WIDEN + 1):
            start, end = self._join(sentence, spot, start, end)
            region = self._base_region(sentence, start, end)
            flags = set(region.flags)
            for o in options:
                o.text, o.infix = self._render_option(sentence, spot, o, region, flags)
            left = start > 0 and bool(flags & {"straddle-left", "context-left"})
            right = end < len(toks) and bool(flags & {"straddle-right", "context-right"})
            if not left and not right:
                break
            start, end = start - left, end + right
        return region

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
        first = (r.start == 0 and o.entry.form[:1].islower()) or any(
            rec.substituted and rec is not spot.rec and rec.out_span[0] == toks[0].start
            and rec.chosen.entry.form[:1].islower() for rec in sentence.trace.records)
        layout = self._telling(sentence, splices, first)
        lo, hi = toks[region.start].start - sentence.offset, toks[region.end - 1].end - sentence.offset
        ga, gb = layout.forward(lo, "right"), layout.forward(hi, "left")
        return self._phonetic_region(layout.text[ga:gb], region.bounds, flags)

    # -- dialect and imagery --------------------------------------------------------------------------------------

    def _dialect(self, sentence: _Sentence, s: _Splice) -> dict[str, Any]:
        layout, base = sentence.layout, sentence.trace.start
        ga = layout.forward(s.start - sentence.offset, "right")
        gb = max(ga, layout.forward(s.end - sentence.offset, "left"))
        out = self._final_span(self._joined(base + ga, "right"), self._joined(base + gb, "left"))
        d = s.owner
        pair = ({"english": d.english, "before": d.before, "after": d.after} if d is not None
                else {"english": None, "before": self.source[s.start:s.end], "after": s.text})
        return self._change("dialect", (s.start, s.end), out, None, 0, pair=pair)

    def _imagery(self, sentence: _Sentence, s: _Splice) -> dict[str, Any]:
        """A contextual image after a term: garnish with no entry, which goes without a trace when removed."""
        layout, base = sentence.layout, sentence.trace.start
        at = map_position(layout.splices, s.start - sentence.offset, "left")
        ga, gb = layout.after_garnish(at, "right", 0), layout.after_garnish(at + len(s.text), "left", 0)
        out = self._final_span(self._joined(base + ga, "right"), self._joined(base + gb, "left"))
        return self._change("garnish", (s.start, s.start), out, None, 0, key="riff", original="",
                            placement="riff", image_id=s.owner, removed={"out_span": list(out), "rendered": ""})

    # -- garnish ------------------------------------------------------------------------------------------------

    def _garnish(self, sentence: _Sentence, k: int) -> dict[str, Any]:
        """A placed garnish: its words; the region a swap or its removal replaces (an opener's or a connective's
        takes in the next word, whose capital it lowered); the other garnish the engine weighed there."""
        op, base = sentence.ops[k], sentence.trace.start
        p, _, n = op.edit
        a = sentence.layout.after_garnish(p, "right", k + 1)
        b = sentence.layout.after_garnish(p + n, "left", k + 1)
        out = self._final_span(self._joined(base + a, "right"), self._joined(base + b, "left"))
        src = self._source(base + a, "start")
        q = _first_word_end(self._before(sentence, k), p) if op.placement in ("opener", "connective") else p
        flags: set[str] = set()
        ra, rb = self._garnish_region(sentence.layout, k, p, q, True)
        bounds, region = self._bounds(self._joined(base + ra, "right"), self._joined(base + rb, "left"), flags)
        if q == p:   # its words go and nothing else changes
            removed = {"out_span": list(out), "rendered": ""}
        else:
            ops = list(sentence.ops)
            ops[k] = None
            layout = self._telling(sentence, sentence.splices, sentence.first_replaced, ops)
            ga, gb = self._garnish_region(layout, k, p, q, False)
            text, _ = self._phonetic_region(layout.text[ga:gb], bounds, flags)
            removed = {"out_span": list(region), "rendered": self.restore(text, whole=False)}
        alternatives = []
        for entry, form, weight in self._pool(sentence.trace.sent.index, op):
            if entry.id == op.entry.id:
                text = self.final[region[0]:region[1]]
            else:
                ops = list(sentence.ops)
                ops[k] = _Op(op.placement, entry, form, op.edit)
                layout = self._telling(sentence, sentence.splices, sentence.first_replaced, ops)
                if layout.garnish[k] is None:
                    continue
                ga, gb = self._garnish_region(layout, k, p, q, True)
                text = self.restore(self._phonetic_region(layout.text[ga:gb], bounds, flags)[0], whole=False)
            alternatives.append({"entry_id": entry.id, "weight": weight, "rendered": text, "out_span": list(region),
                                 "vulgarity": entry.vulgarity, "masks": []})
        return self._change("garnish", (src, src), out, op.entry, op.entry.vulgarity, key=op.placement, original="",
                            placement=op.placement, removed=removed, alternatives=_shares(alternatives))

    def _before(self, sentence: _Sentence, k: int) -> str:
        """The sentence's text just before its k-th garnish went in."""
        if sentence.before is None:
            st, texts = sentence.trace, [sentence.trace.spliced]
            for o in sentence.ops:
                texts.append(self.tr.replay_garnish(texts[-1], st.sent, self.run, [(o.placement, o.form)],
                                                    sentence.first_replaced)[0])
            sentence.before = texts
        return sentence.before[k]

    @staticmethod
    def _garnish_region(layout: _Layout, k: int, p: int, q: int, placed: bool) -> tuple[int, int]:
        """The k-th garnish's region in a telling: from where it goes (p, in the text before it) to q (the end of
        the word an opener lowers, else p), through itself where the telling has it, and the garnish after."""
        b = map_position([layout.garnish[k]], q, "right") if placed else q
        return layout.after_garnish(p, "right", k + 1), layout.after_garnish(b, "left", k + 1)

    def _pool(self, sentence: int, op: _Op) -> list[tuple[Entry, str, float]]:
        """The garnish entries the engine weighed when it picked op (its record's rejections are the rest), each with
        the words it would have said there and its weight."""
        record = next((g for g in self.run.garnish if g.sentence == sentence and g.entry_id == op.entry.id
                       and g.placement == op.placement), None)
        swear = op.entry.vulgarity > 0
        if op.placement == "closer":
            key = ("swear-closer" if swear else "closer", self.run.text.lower())
        else:
            key = (("swear" if swear else "") + op.placement,) + self.w.sentences[sentence].sent.key
        seed, eff = self.run.pol.seed, self.run.eff
        if record is None or realise_garnish(op.entry, seed, key, eff) != op.form:
            return [(op.entry, op.form, op.entry.weight)]
        rejected = {i for i, _ in record.rejected}
        pool = sorted((e for e in self.tr.dictionary.garnish if e.placement == op.placement and e.id not in rejected),
                      key=lambda e: e.id)
        return [(e, op.form if e is op.entry else realise_garnish(e, seed, key, eff),
                 e.weight * (tier_match(e.vulgarity, eff.vulgarity) if swear else 1.0)) for e in pool]

    def _closer(self) -> dict[str, Any]:
        op = self.closer
        x, _, n = op.edit
        flags: set[str] = set()
        bounds, final = self._bounds(x, x + n, flags)
        body = self.w.joined[:x] + self.w.joined[x + n:]
        alternatives = []
        for entry, form, weight in self._pool(len(self.sentences) - 1, op):
            if entry.id == op.entry.id:
                text = self.final[final[0]:final[1]]
            else:
                placed, (at, _, m) = place_garnish(body, "closer", form)
                text = self.restore(self._phonetic_region(placed[at:at + m], bounds, flags)[0], whole=False)
            alternatives.append({"entry_id": entry.id, "weight": weight, "rendered": text, "out_span": list(final),
                                 "vulgarity": entry.vulgarity, "masks": []})
        src = self._source(x, "start")
        return self._change("garnish", (src, src), final, op.entry, op.entry.vulgarity, key="closer", original="",
                            placement="closer", removed={"out_span": list(final), "rendered": ""},
                            alternatives=_shares(alternatives))

    # -- phonetic --------------------------------------------------------------------------------------------------

    def _phonetic(self) -> list[dict[str, Any]]:
        """Each drawl, spelling or swear infix edit, in the final text (taking in a later rule's edit across it) and
        in the source (the text it came from: inside a swap or garnish, that whole span)."""
        out = []
        for k, p in enumerate(self.passes):
            after = self.passes[k + 1].before if k + 1 < len(self.passes) else self.w.final
            delta = 0
            for s, e, n in p.edits:
                a = s + delta
                delta += n - (e - s)
                fa, fb = a, a + n
                for later in self.passes[k + 1:]:
                    fa, fb = map_outward(later.edits, fa, "start"), max(fa, map_outward(later.edits, fb, "end"))
                src = (self._pass_source(k, s, "start"), self._pass_source(k, e, "end"))
                kind = "swear_infix" if p.rule.vulgarity else "phonetic"
                rule = {"id": p.rule.id, "kind": "infix" if p.rule.vulgarity else p.rule.kind,
                        "before": p.before[s:e], "after": after[a:a + n]}
                out.append(self._change(kind, src, (fa, fb), None, p.rule.vulgarity, key=p.rule.id,
                                        original=self.source[src[0]:src[1]], rule=rule))
        return out

    def _pass_source(self, k: int, pos: int, side: str) -> int:
        for p in reversed(self.passes[:k]):
            pos = unmap_position(p.edits, pos, side)
        return self._source(pos, side)


# -- helpers ----------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _triggers(pattern: re.Pattern) -> frozenset[str] | None:
    """Words one of which (case folded) every match of a pattern contains, read from its literal runs; None where
    there are none to read (a rule that is all lookaround). A window with none of them holds no match."""
    found = _required(_regex.parse(pattern.pattern, pattern.flags))
    return frozenset(found) if found else None


def _required(seq) -> set[str] | None:
    """For a parsed pattern sequence: a set of words one of which every match contains (the most telling one), or
    None. Consecutive literals are a word; a group, a branch (each way's words) and a repeat of at least one
    count too."""
    options: list[set[str]] = []
    run: list[str] = []
    for op, arg in seq:
        if op is _C.LITERAL:
            run.append(chr(arg))
            continue
        if run:
            options.append({"".join(run).casefold()})
            run = []
        inner = None
        if op is _C.SUBPATTERN:
            inner = _required(arg[-1])
        elif op is _C.BRANCH:
            ways = [_required(way) for way in arg[1]]
            inner = set().union(*ways) if all(ways) else None
        elif op in _REPEATS and arg[0] >= 1:
            inner = _required(arg[2])
        if inner:
            options.append(inner)
    if run:
        options.append({"".join(run).casefold()})
    return max(options, key=lambda o: min(map(len, o))) if options else None


def _stacked(o: _Option) -> list[str]:
    """The entry stacked after an option's own, whose mask words its rendering also carries."""
    return [o.stacked.id] if o.stacked else []


def _first_word_end(text: str, at: int) -> int:
    """Where the word an opener or connective lowers ends, in the text before it went in at `at`."""
    m = re.match(r"[\"'(]*[A-Za-z'’]+", text[at:])
    return at + m.end() if m else at


def _inside(spans: list[tuple[int, int]], a: int, b: int) -> bool:
    """Whether a region [a, b) starts inside one of the spans (base coordinates)."""
    return any(x <= a < y for x, y in spans)


def _shares(alternatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(o["weight"] for o in alternatives) or 1.0
    for o in alternatives:
        o["weight"] = round(o["weight"] / total, 4)
    return alternatives


def _cover(changes: list[dict[str, Any]]) -> None:
    """Each change lists the changes inside the region its swap or removal replaces: those go with it."""
    for c in changes:
        spans = [c["out_span"]] + [o["out_span"] for o in c["alternatives"] + c["locked"]]
        if c.get("removed"):
            spans.append(c["removed"]["out_span"])
        lo, hi = min(s[0] for s in spans), max(s[1] for s in spans)
        rank = KINDS.index(c["kind"])
        for d in changes:
            a, b = d["out_span"]
            if d is c or not lo <= a <= b <= hi or (a == b and a in (lo, hi)):
                continue
            if b - a < hi - lo or KINDS.index(d["kind"]) > rank:
                c["covers"].append(d["id"])
