"""Garnish (openers, tag-ons, closers) and phonetic respelling."""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field

from .context import CLOSING_TONES_FOR, tone_weight
from .model import PhoneticRule
from .policy import Effective, pick_form, roll, weighted_index
from .schema import DEFAULT_WHEN, Entry
from .select import policy_rejection
from .text import OPEN_QUOTES, QUOTES, lower_first_word, match_case, sentences, tokenize

VOWEL_RE = re.compile(r"[aeiou]", re.I)
QUOTE_RE = re.compile(r"[\"\u201c][^\"\u201c\u201d]*[\"\u201d]")


@dataclass
class GarnishRecord:
    placement: str
    sentence: int
    entry_id: str | None
    text: str | None
    decision: str
    rejected: list[tuple[str, str]]
    image_id: str | None = None

    @classmethod
    def rolled(cls, placement: str, sentence: int, entry: Entry | None, text: str | None, r: float, p: float,
               rejected: list[tuple[str, str]]) -> "GarnishRecord":
        """A placement whose roll came in under its probability, with what (if anything) was picked."""
        return cls(placement, sentence, entry.id if entry else None, text,
                   f"roll {r:.3f} < p {p:g}" + ("" if entry else f"; no eligible {placement}"), rejected)

    def to_dict(self) -> dict:
        return {"kind": "garnish", "placement": self.placement, "sentence": self.sentence,
                "entry": self.entry_id, "text": self.text, "decision": self.decision,
                "rejected": [{"entry": i, "reason": r} for i, r in self.rejected],
                **({"image_id": self.image_id} if self.image_id else {})}


@dataclass
class PhoneticRecord:
    rule: str
    before: str
    after: str
    offset: int

    def to_dict(self) -> dict:
        return {"kind": "phonetic", "rule": self.rule, "before": self.before, "after": self.after,
                "offset": self.offset}


def stretch_word(text: str, times: int) -> str:
    m = VOWEL_RE.search(text)
    if not m:
        return text
    return text[: m.end()] + m.group() * (times - 1) + text[m.end():]


def realise_garnish(entry: Entry, seed: int, key: tuple, eff: Effective) -> str:
    """The words a garnish entry says, picked (and stretched) by its key: the same entry, key and seed say the
    same."""
    forms = entry.all_forms
    form = pick_form(forms, seed, entry.id, *key)
    if entry.stretch:
        lo, hi = eff.profile.stretch
        n = lo + int(roll(seed, "stretch", entry.id, *key) * (hi - lo + 1))
        form = stretch_word(form, n)
    return form



def tier_match(tier: int, asked: int) -> float:
    """How strongly a swear of one tier comes through at the vulgarity asked for: fully at that tier, half one
    tier below, a quarter two below. So each vulgarity sounds like itself rather than like the mildest swear."""
    return 0.5 ** max(0, asked - tier)


@dataclass(frozen=True)
class GarnishOffer:
    """What the engine weighs for one garnish placement: the eligible entries in the order it weighs them, each
    one's weight, the key its roll and words are drawn by, and why the rest were passed over. The engine picks from
    it; the changes builder offers the same entries as alternatives, each with the words it would have said."""
    placement: str
    pool: tuple[Entry, ...]
    weights: tuple[float, ...]
    key: tuple
    seed: int
    eff: Effective
    rejected: list[tuple[str, str]]

    def pick(self) -> Entry | None:
        if not self.pool:
            return None
        return self.pool[weighted_index(list(self.weights), roll(self.seed, "garnish-pick", self.placement, *self.key))]

    def words(self, entry: Entry) -> str:
        return realise_garnish(entry, self.seed, self.key, self.eff)


def garnish_pool(placement: str, entries: list[Entry], eff: Effective, used: dict[str, int],
                 contexts: set[str] | None = None, exclude: set[str] = frozenset(), mood: str = "light",
                 swear: bool | None = None, insults: bool = True) -> tuple[list[Entry], list[tuple[str, str]]]:
    """The garnish entries eligible for a placement, in the order they're weighed, and the rest with why not. swear
    picks the channel: False the level's clean garnish, True the swearing (vulgarity 1 and up), None both. insults:
    whether a garnish may call someone names ("ya galah"; not in a safety notice)."""
    rejected: list[tuple[str, str]] = []
    pool: list[Entry] = []
    for e in entries:
        if e.placement != placement:
            continue
        reason = policy_rejection(e, eff)
        if reason is None and swear is not None and (e.vulgarity > 0) != swear:
            reason = "clean garnish comes with the level" if not e.vulgarity else "swearing comes with the vulgarity"
        if reason is None and not insults and e.insult:
            reason = "no name-calling in this text's form"
        when = set(e.when or DEFAULT_WHEN[placement])
        if reason is None and placement == "tag" and "fragment" in contexts:
            reason = "no tag-ons on a verbless fragment"
        if reason is None and "any" not in when and not when & contexts:
            reason = f"suits {', '.join(sorted(when))}, not this sentence ({', '.join(sorted(contexts))})"
        if reason is None and placement in ("closer", "aside") and e.tone not in CLOSING_TONES_FOR[mood]:
            reason = f"{e.tone} in a {mood} text"
        if reason is None and used.get(e.id):
            reason = "already used in this text"
        if reason is None and e.id in exclude:
            reason = "used in the last few sentences"
        if reason:
            rejected.append((e.id, reason))
        else:
            pool.append(e)
    pool.sort(key=lambda e: e.id)
    return pool, rejected


def garnish_weights(pool: list[Entry], eff: Effective, swear: bool | None) -> list[float]:
    """Each entry's weight; swearing sounds like its tier, so a closer at tradie leans to "fuck me dead" over "well,
    I'll be buggered"."""
    return [e.weight * (tier_match(e.vulgarity, eff.vulgarity) if swear else 1.0) for e in pool]


def garnish_offer(placement: str, entries: list[Entry], eff: Effective, seed: int, key: tuple,
                  used: dict[str, int], contexts: set[str] | None = None, exclude: set[str] = frozenset(),
                  mood: str = "light", swear: bool | None = None, insults: bool = True) -> GarnishOffer:
    """What the engine weighs for a placement (garnish_pool, garnish_weights), keyed for its roll and words."""
    pool, rejected = garnish_pool(placement, entries, eff, used, contexts, exclude, mood, swear, insults)
    return GarnishOffer(placement, tuple(pool), tuple(garnish_weights(pool, eff, swear)), key, seed, eff, rejected)


SENT_END_RE = re.compile(r"([.!?]+)([\"'\u201d\u2019)\]]*)\s*$")


# An edit one garnish makes: (start, end, new length) in the text it was placed in. A placement inserts its words
# (the opener's capital change on the next word keeps its length), so start == end.
Edit = tuple[int, int, int]


def opener_edit(sentence: str, opener: str, common: set[str] | None = None,
                force_lower: bool = False) -> tuple[str, Edit]:
    """'Strewth, the bloke...': an exclamation before the sentence (inside an opening quote), lowering the first word
    where it's an ordinary one (common) or force_lower says so, with where it went."""
    lead = len(sentence) - len(sentence.lstrip())
    if sentence[lead:lead + 1] in OPEN_QUOTES:   # the speaker says it: '"Oi, some bugger's been ..."'
        lead += 1
    body = sentence[lead:]
    words = match_case(opener, "A") + ", "
    return sentence[:lead] + words + lower_first_word(body, common, force_lower), (lead, lead, len(words))


CONNECTIVE_STARTS = {"then", "so", "and", "but", "when", "now", "well", "anyway", "after", "before", "meanwhile",
                     "once", "finally", "next", "suddenly"}


def connective_edit(sentence: str, connective: str, common: set[str] | None = None) -> tuple[str, Edit] | None:
    """'Anyway, she found...', with where it went; None if the sentence already opens with a connective or a
    quote."""
    lead = len(sentence) - len(sentence.lstrip())
    body = sentence[lead:]
    first = re.match(r"[A-Za-z']+", body)
    if not first or first.group().lower() in CONNECTIVE_STARTS:
        return None
    words = match_case(connective, "A") + ", "
    return sentence[:lead] + words + lower_first_word(body, common), (lead, lead, len(words))


def _speech_end(sentence: str) -> re.Match | None:
    """Where quoted speech ends in the sentence (its closing punctuation), if it has any."""
    q = re.search(r"([.!?])([\"\u201d])", sentence)
    return q if q and re.search(r"[\"\u201c]", sentence[: q.start()]) else None


def tag_in_speech(sentence: str) -> bool:
    """Whether tag_edit puts the tag inside quoted speech ('"...my porridge, mate!" he said.') rather than at the end."""
    return _speech_end(sentence) is not None


def tag_edit(sentence: str, tag: str) -> tuple[str, Edit]:
    """', mate' before the sentence's closing punctuation, or for dialogue inside the quote ('"...my porridge, mate!"
    he said.'), with where it went."""
    words = ", " + tag
    # dialogue: the tag belongs to the speaker, inside the quote ('"...my porridge, mate!" he said.')
    q = _speech_end(sentence)
    if q:
        at = q.start()
        return sentence[:at] + words + sentence[at:], (at, at, len(words))
    stripped = sentence.rstrip()
    trail = sentence[len(stripped):]
    m = SENT_END_RE.search(stripped)
    at = m.start() if m else len(stripped)
    return stripped[:at] + words + stripped[at:] + trail, (at, at, len(words))


# a list closing the sentence: "their brains and imagination?", "trees, radios, tons!"
LIST_END_RE = re.compile(r"(?:\b(?:their|his|her|my|our|your|its|the)\s+[a-z]+(?:,\s*[a-z]+)*,?\s+and\s+[a-z]+"
                         r"|\b[a-z]+,\s*[a-z]+,\s*(?:and\s+)?[a-z]+)(?=[?!.]\s*$)", re.I)


def ends_in_list(sentence: str) -> bool:
    """A narrated sentence that closes on a list ("their brains and imagination?"), where a tail can go."""
    stripped = sentence.rstrip()
    return not any(q in stripped for q in QUOTES) and LIST_END_RE.search(stripped) is not None


def tail_edit(sentence: str, tail: str) -> tuple[str, Edit] | None:
    """Round off a closing list the way a talker does: "...their brains and imagination, the whole bloody works?",
    with where it went. None when the sentence doesn't end in a list (or is speech)."""
    if not ends_in_list(sentence):
        return None
    stripped = sentence.rstrip()
    at = LIST_END_RE.search(stripped).end()
    words = ", " + tail
    return stripped[:at] + words + stripped[at:] + sentence[len(stripped):], (at, at, len(words))


def closer_edit(text: str, closer: str) -> tuple[str, Edit]:
    """A closing remark after the text's last sentence, with where it went (a full stop it adds included)."""
    stripped = text.rstrip()
    trail = text[len(stripped):]
    words = ""
    if stripped and not re.search(r"[.!?][\"'\u201d\u2019)\]]*$", stripped):
        words = "."   # don't add a full stop after one that sits inside closing quotes
    closer = match_case(closer, "A")
    if closer[-1] not in ".!?":
        closer += "."
    words += " " + closer
    return stripped + words + trail, (len(stripped), len(stripped), len(words))


def place_garnish(text: str, placement: str, form: str, lowerable: set[str] | None = None,
                  first_replaced: bool = False) -> tuple[str, Edit] | None:
    """One garnish placed in a sentence (an aside or closer at the end of a text), with where it went; None
    where it doesn't fit (a connective before a connective, a tail with no closing list). The engine places
    garnish this way, and the changes builder replays it the same way on a sentence with a swap in it."""
    if placement == "opener":
        return opener_edit(text, form, lowerable, first_replaced)
    if placement == "connective":
        return connective_edit(text, form, lowerable)
    if placement == "tag":
        return tag_edit(text, form)
    if placement == "tail":
        return tail_edit(text, form)
    if placement in ("aside", "closer"):
        return closer_edit(text, form)
    raise ValueError(f"no garnish placement {placement!r}")


@dataclass
class PhoneticPass:
    """One rule's pass over the text, as the changes builder replays it on a spot: the text the rule matched in,
    every match (the roll counter counts each, fired or not), the edits it made and the context it read."""
    rule: PhoneticRule
    scale: float
    before: str
    starts: list[int] = field(default_factory=list)
    ends: list[int] = field(default_factory=list)
    edits: list[tuple[int, int, int]] = field(default_factory=list)   # (start, end, new length) in `before`
    quotes: list[tuple[int, int]] = field(default_factory=list)
    questions: list[tuple[int, int]] = field(default_factory=list)
    kept: list[tuple[int, int]] | None = None        # the keep spans of `before`, where the pass read them
    preserved: list[tuple[int, int]] | None = None


@dataclass
class PhoneticTrace:
    """Every pass of one apply_phonetic call, with the span functions it read context through."""
    keep: Callable[[str], list[tuple[int, int]]] | None
    preserve: Callable[[str], list[tuple[int, int]]] | None
    passes: list[PhoneticPass] = field(default_factory=list)

    _cache: dict = field(default_factory=dict)   # the last text each span function read, and its spans

    def kept(self, p: PhoneticPass) -> list[tuple[int, int]]:
        if p.kept is None:
            p.kept = [] if self.keep is None or p.rule.kind == "spelling" else self._spans("keep", self.keep, p.before)
        return p.kept

    def preserved(self, p: PhoneticPass) -> list[tuple[int, int]]:
        if p.preserved is None:
            p.preserved = [] if self.preserve is None else self._spans("preserve", self.preserve, p.before)
        return p.preserved

    def _spans(self, name: str, fn: Callable[[str], list[tuple[int, int]]], text: str) -> list[tuple[int, int]]:
        """fn(text), read again only once a rule has changed the text (as the pass itself does)."""
        last = self._cache.get(name)
        if last is None or last[0] != text:
            last = self._cache[name] = (text, fn(text))
        return last[1]


def phonetic_scale(rule: PhoneticRule, rules: list[PhoneticRule], eff: Effective, infixes: bool) -> float:
    """How strongly a rule applies under the policy (0: not at all). Spelling always applies; the drawl scales with
    the level; a swear infix ("a bloody great stoush") scales with the vulgarity, whatever the level, and only
    where the embellishment takes infixes (not in a manual or a policy)."""
    if rule.is_infix:
        if not infixes:
            return 0.0
        top = min(eff.vulgarity, max(r.vulgarity for r in rules))   # the strongest infix tier allowed
        return eff.swearing.infix * tier_match(rule.vulgarity, top) if rule.vulgarity <= eff.vulgarity else 0.0
    if rule.min_level > eff.level:
        return 0.0
    return 1.0 if rule.kind == "spelling" else eff.profile.phonetic


def phonetic_admits(rule: PhoneticRule, pos: int, prefix: Callable[[], str], questions: list[tuple[int, int]],
                     spans: Callable[[], list[tuple[int, int]]]) -> bool:
    """Whether a match at pos may change at all: not in a question (a rule that keeps out of them), not after its
    unless_before context (prefix: the text before the match), and not in a kept or preserved span (spans). The
    engine's pass and the changes builder's pass over a spot both ask this, for each match."""
    question = bisect_right(questions, pos, key=lambda span: span[0]) - 1
    if question >= 0 and pos < questions[question][1]:
        return False
    if rule.unless_before is not None and rule.unless_before.search(prefix()):
        return False
    return not any(a <= pos < b for a, b in spans())


def in_dialogue(pos: int, quotes: list[tuple[int, int]]) -> bool:
    """Whether a match at pos is inside quoted speech, where a rule drawls at its dialogue rate."""
    return any(a <= pos < b for a, b in quotes)


def phonetic_replacement(rule: PhoneticRule, m: re.Match, n: int, seed: int, scale: float,
                         in_dialogue: bool) -> str | None:
    """What the n-th match of a rule's pass becomes, once nothing keeps it out, or None where its roll says no."""
    prob = rule.dialogue_prob if in_dialogue else rule.prob
    if roll(seed, "phonetic", rule.id, n, m.group(0).lower()) >= prob * scale:
        return None
    out = m.expand(rule.replace)
    return match_case(out, m.group(0)) if out and out[0].isalpha() and m.group(0) else out


def apply_phonetic(text: str, rules: list[PhoneticRule], eff: Effective, seed: int, infixes: bool = True,
                   keep: Callable[[str], list[tuple[int, int]]] | None = None,
                   preserve: Callable[[str], list[tuple[int, int]]] | None = None,
                   trace: PhoneticTrace | None = None) -> tuple[str, list[PhoneticRecord]]:
    """Apply each rule in order; every occurrence rolls independently. infixes: whether the swear infixes may
    go in (the embellishment's call: not in a manual or a policy). keep: the spans of a text the drawl and
    infixes stay out of (a heading, a link's text); Australian spelling still applies there. preserve protects
    literal wording from every rule. trace, when given, collects each rule's pass (PhoneticPass)."""
    records: list[PhoneticRecord] = []
    preserved_for: list = [None, []]
    kept_for: list = [None, []]   # (text, its kept spans): the same until a rule changes the text
    for rule in rules:
        scale = phonetic_scale(rule, rules, eff, infixes)
        if scale <= 0:
            continue
        counter = {"n": 0}
        quotes = [q.span() for q in QUOTE_RE.finditer(text)] if rule.dialogue_prob is not None else []
        before = text   # the text this rule matches in, for the kept spans (read once, when a rule first matches)
        questions = [(s[0].start, s[-1].end) for s in sentences(tokenize(before))
                     if any(t.text == "?" for t in s)] if rule.unless_question else []
        traced = None if trace is None else PhoneticPass(rule, scale, before, quotes=quotes, questions=questions)

        def kept() -> list[tuple[int, int]]:
            if keep is None or rule.kind == "spelling":
                return []
            if kept_for[0] != before:
                kept_for[:] = [before, keep(before)]
            return kept_for[1]

        def spans() -> list[tuple[int, int]]:
            if preserve is not None and preserved_for[0] != before:
                preserved_for[:] = [before, preserve(before)]
            return kept() + preserved_for[1]

        def sub(m: re.Match) -> str:
            counter["n"] += 1   # counted either way, so a kept span doesn't shift the rolls after it
            if traced is not None:
                traced.starts.append(m.start())
                traced.ends.append(m.end())
            if not phonetic_admits(rule, m.start(), lambda: before[:m.start()], questions, spans):
                return m.group(0)
            out = phonetic_replacement(rule, m, counter["n"], seed, scale, in_dialogue(m.start(), quotes))
            if out is None:
                return m.group(0)
            records.append(PhoneticRecord(rule.id, m.group(0), out, m.start()))
            if traced is not None:
                traced.edits.append((m.start(), m.end(), len(out)))
            return out

        text = rule.pattern.sub(sub, text)
        if traced is not None:   # keep the context spans the pass read, so a replay needn't work them out again
            if rule.kind == "spelling" or keep is None:
                traced.kept = []
            elif kept_for[0] is before:
                traced.kept = kept_for[1]
            if preserve is None:
                traced.preserved = []
            elif preserved_for[0] is before:
                traced.preserved = preserved_for[1]
            trace.passes.append(traced)
    return text, records


def pick_riff(riffs, mood: str, r: float):
    """One of an entry's riffs for a roll r in [0, 1). Mood is a lean, not a rule: riffs that suit the text's mood
    weigh more, but a dark text can still take a laugh and a light one a shadow. The first-listed is the best,
    and weighs double."""
    return riffs[weighted_index([tone_weight(x.tone, mood) * (2 if i == 0 else 1) for i, x in enumerate(riffs)], r)]
