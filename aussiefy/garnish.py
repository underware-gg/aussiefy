"""Garnish (openers, tag-ons, closers) and phonetic respelling."""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field

from .context import CLOSING_TONES_FOR, riff_weight
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


def _realise_garnish(entry: Entry, seed: int, key: tuple, eff: Effective) -> str:
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


def pick_garnish(placement: str, entries: list[Entry], eff: Effective, seed: int, key: tuple,
                 used: dict[str, int], contexts: set[str] | None = None, exclude: set[str] = frozenset(),
                 mood: str = "light", swear: bool | None = None,
                 insults: bool = True) -> tuple[Entry | None, str | None, list[tuple[str, str]]]:
    """One garnish entry for a placement, weighted, with the reasons the rest were passed over. swear picks the
    channel: False the level's clean garnish, True the swearing (vulgarity 1 and up), None both. insults: whether
    a garnish may call someone names ("ya galah"; not in a safety notice)."""
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
    if not pool:
        return None, None, rejected
    pool.sort(key=lambda e: e.id)
    # swearing sounds like its tier: a closer at tradie leans to "fuck me dead" over "well, I'll be buggered"
    weights = [e.weight * (tier_match(e.vulgarity, eff.vulgarity) if swear else 1.0) for e in pool]
    chosen = pool[weighted_index(weights, roll(seed, "garnish-pick", placement, *key))]
    return chosen, _realise_garnish(chosen, seed, key, eff), rejected


SENT_END_RE = re.compile(r"([.!?]+)([\"'\u201d\u2019)\]]*)\s*$")


# An edit one garnish makes: (start, end, new length) in the text it was placed in. A placement inserts its words
# (the opener's capital change on the next word keeps its length), so start == end.
Edit = tuple[int, int, int]


def opener_edit(sentence: str, opener: str, common: set[str] | None = None,
                force_lower: bool = False) -> tuple[str, Edit]:
    """add_opener, with where it went."""
    lead = len(sentence) - len(sentence.lstrip())
    if sentence[lead:lead + 1] in OPEN_QUOTES:   # the speaker says it: '"Oi, some bugger's been ..."'
        lead += 1
    body = sentence[lead:]
    words = match_case(opener, "A") + ", "
    return sentence[:lead] + words + lower_first_word(body, common, force_lower), (lead, lead, len(words))


def add_opener(sentence: str, opener: str, common: set[str] | None = None, force_lower: bool = False) -> str:
    return opener_edit(sentence, opener, common, force_lower)[0]


CONNECTIVE_STARTS = {"then", "so", "and", "but", "when", "now", "well", "anyway", "after", "before", "meanwhile",
                     "once", "finally", "next", "suddenly"}


def connective_edit(sentence: str, connective: str, common: set[str] | None = None) -> tuple[str, Edit] | None:
    """add_connective, with where it went."""
    lead = len(sentence) - len(sentence.lstrip())
    body = sentence[lead:]
    first = re.match(r"[A-Za-z']+", body)
    if not first or first.group().lower() in CONNECTIVE_STARTS:
        return None
    words = match_case(connective, "A") + ", "
    return sentence[:lead] + words + lower_first_word(body, common), (lead, lead, len(words))


def add_connective(sentence: str, connective: str, common: set[str] | None = None) -> str | None:
    """'Anyway, she found...'. None if the sentence already opens with a connective or a quote."""
    placed = connective_edit(sentence, connective, common)
    return placed and placed[0]


def _speech_end(sentence: str) -> re.Match | None:
    """Where quoted speech ends in the sentence (its closing punctuation), if it has any."""
    q = re.search(r"([.!?])([\"\u201d])", sentence)
    return q if q and re.search(r"[\"\u201c]", sentence[: q.start()]) else None


def tag_in_speech(sentence: str) -> bool:
    """Whether add_tag puts the tag inside quoted speech ('"...my porridge, mate!" he said.') rather than at the end."""
    return _speech_end(sentence) is not None


def tag_edit(sentence: str, tag: str) -> tuple[str, Edit]:
    """add_tag, with where it went."""
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


def add_tag(sentence: str, tag: str) -> str:
    return tag_edit(sentence, tag)[0]


# a list closing the sentence: "their brains and imagination?", "trees, radios, tons!"
LIST_END_RE = re.compile(r"(?:\b(?:their|his|her|my|our|your|its|the)\s+[a-z]+(?:,\s*[a-z]+)*,?\s+and\s+[a-z]+"
                         r"|\b[a-z]+,\s*[a-z]+,\s*(?:and\s+)?[a-z]+)(?=[?!.]\s*$)", re.I)


def ends_in_list(sentence: str) -> bool:
    """A narrated sentence that closes on a list ("their brains and imagination?"), where a tail can go."""
    stripped = sentence.rstrip()
    return not any(q in stripped for q in QUOTES) and LIST_END_RE.search(stripped) is not None


def tail_edit(sentence: str, tail: str) -> tuple[str, Edit] | None:
    """add_tail, with where it went."""
    if not ends_in_list(sentence):
        return None
    stripped = sentence.rstrip()
    at = LIST_END_RE.search(stripped).end()
    words = ", " + tail
    return stripped[:at] + words + stripped[at:] + sentence[len(stripped):], (at, at, len(words))


def add_tail(sentence: str, tail: str) -> str | None:
    """Round off a closing list the way a talker does: "...their brains and imagination, the whole bloody works?"
    None when the sentence doesn't end in a list (or is speech)."""
    placed = tail_edit(sentence, tail)
    return placed and placed[0]


def closer_edit(text: str, closer: str) -> tuple[str, Edit]:
    """add_closer, with where it went (a full stop it adds included)."""
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


def add_closer(text: str, closer: str) -> str:
    return closer_edit(text, closer)[0]


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

    def kept(self, p: PhoneticPass) -> list[tuple[int, int]]:
        if p.kept is None:
            p.kept = [] if self.keep is None or p.rule.kind == "spelling" else self.keep(p.before)
        return p.kept

    def preserved(self, p: PhoneticPass) -> list[tuple[int, int]]:
        if p.preserved is None:
            p.preserved = [] if self.preserve is None else self.preserve(p.before)
        return p.preserved


def phonetic_scale(rule: PhoneticRule, rules: list[PhoneticRule], eff: Effective, infixes: bool) -> float:
    """How strongly a rule applies under the policy (0: not at all). Spelling always applies; the drawl scales with
    the level; a swear infix ("a bloody great stoush") scales with the vulgarity, whatever the level, and only
    where the embellishment takes infixes (not in a manual or a policy)."""
    if rule.vulgarity > 0:
        if not infixes:
            return 0.0
        top = min(eff.vulgarity, max(r.vulgarity for r in rules))   # the strongest infix tier allowed
        return eff.swearing.infix * tier_match(rule.vulgarity, top) if rule.vulgarity <= eff.vulgarity else 0.0
    if rule.min_level > eff.level:
        return 0.0
    return 1.0 if rule.kind == "spelling" else eff.profile.phonetic


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

        def sub(m: re.Match) -> str:
            counter["n"] += 1   # counted either way, so a kept span doesn't shift the rolls after it
            if traced is not None:
                traced.starts.append(m.start())
                traced.ends.append(m.end())
            question = bisect_right(questions, m.start(), key=lambda span: span[0]) - 1
            if question >= 0 and m.start() < questions[question][1]:
                return m.group(0)
            if rule.unless_before is not None and rule.unless_before.search(before[:m.start()]):
                return m.group(0)
            if preserve is not None and preserved_for[0] != before:
                preserved_for[:] = [before, preserve(before)]
            if any(a <= m.start() < b for a, b in kept() + preserved_for[1]):
                return m.group(0)
            in_dialogue = any(a <= m.start() < b for a, b in quotes)
            out = phonetic_replacement(rule, m, counter["n"], seed, scale, in_dialogue)
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
    return riffs[weighted_index([riff_weight(x.tone, mood) * (2 if i == 0 else 1) for i, x in enumerate(riffs)], r)]
