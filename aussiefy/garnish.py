"""Garnish (openers, tag-ons, closers) and phonetic respelling."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from .context import CLOSING_TONES_FOR, riff_weight
from .model import PhoneticRule
from .policy import Effective, pick_form, roll, weighted_index
from .schema import DEFAULT_WHEN, Entry, Riff
from .select import policy_rejection
from .text import OPEN_QUOTES, QUOTES, lower_first_word, match_case

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

    @classmethod
    def rolled(cls, placement: str, sentence: int, entry: Entry | None, text: str | None, r: float, p: float,
               rejected: list[tuple[str, str]]) -> "GarnishRecord":
        """A placement whose roll came in under its probability, with what (if anything) was picked."""
        return cls(placement, sentence, entry.id if entry else None, text,
                   f"roll {r:.3f} < p {p:g}" + ("" if entry else f"; no eligible {placement}"), rejected)

    def to_dict(self) -> dict:
        return {"kind": "garnish", "placement": self.placement, "sentence": self.sentence,
                "entry": self.entry_id, "text": self.text, "decision": self.decision,
                "rejected": [{"entry": i, "reason": r} for i, r in self.rejected]}


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


SENT_END_RE = re.compile(r"([.!?]+)([\"')\]]*)\s*$")


def add_opener(sentence: str, opener: str, common: set[str] | None = None, force_lower: bool = False) -> str:
    lead = len(sentence) - len(sentence.lstrip())
    if sentence[lead:lead + 1] in OPEN_QUOTES:   # the speaker says it: '"Oi, some bugger's been ..."'
        lead += 1
    body = sentence[lead:]
    return sentence[:lead] + match_case(opener, "A") + ", " + lower_first_word(body, common, force_lower)


CONNECTIVE_STARTS = {"then", "so", "and", "but", "when", "now", "well", "anyway", "after", "before", "meanwhile",
                     "once", "finally", "next", "suddenly"}


def add_connective(sentence: str, connective: str, common: set[str] | None = None) -> str | None:
    """'Anyway, she found...'. None if the sentence already opens with a connective or a quote."""
    lead = len(sentence) - len(sentence.lstrip())
    body = sentence[lead:]
    first = re.match(r"[A-Za-z']+", body)
    if not first or first.group().lower() in CONNECTIVE_STARTS:
        return None
    return sentence[:lead] + match_case(connective, "A") + ", " + lower_first_word(body, common)


def _speech_end(sentence: str) -> re.Match | None:
    """Where quoted speech ends in the sentence (its closing punctuation), if it has any."""
    q = re.search(r"([.!?])([\"\u201d])", sentence)
    return q if q and re.search(r"[\"\u201c]", sentence[: q.start()]) else None


def tag_in_speech(sentence: str) -> bool:
    """Whether add_tag puts the tag inside quoted speech ('"...my porridge, mate!" he said.') rather than at the end."""
    return _speech_end(sentence) is not None


def add_tag(sentence: str, tag: str) -> str:
    # dialogue: the tag belongs to the speaker, inside the quote ('"...my porridge, mate!" he said.')
    q = _speech_end(sentence)
    if q:
        return sentence[: q.start()] + ", " + tag + sentence[q.start():]
    stripped = sentence.rstrip()
    trail = sentence[len(stripped):]
    m = SENT_END_RE.search(stripped)
    if m:
        return stripped[: m.start()] + ", " + tag + stripped[m.start():] + trail
    return stripped + ", " + tag + trail


# a list closing the sentence: "their brains and imagination?", "trees, radios, tons!"
LIST_END_RE = re.compile(r"(?:\b(?:their|his|her|my|our|your|its|the)\s+[a-z]+(?:,\s*[a-z]+)*,?\s+and\s+[a-z]+"
                         r"|\b[a-z]+,\s*[a-z]+,\s*(?:and\s+)?[a-z]+)(?=[?!.]\s*$)", re.I)


def ends_in_list(sentence: str) -> bool:
    """A narrated sentence that closes on a list ("their brains and imagination?"), where a tail can go."""
    stripped = sentence.rstrip()
    return not any(q in stripped for q in QUOTES) and LIST_END_RE.search(stripped) is not None


def add_tail(sentence: str, tail: str) -> str | None:
    """Round off a closing list the way a talker does: "...their brains and imagination, the whole bloody works?"
    None when the sentence doesn't end in a list (or is speech)."""
    if not ends_in_list(sentence):
        return None
    stripped = sentence.rstrip()
    m = LIST_END_RE.search(stripped)
    return stripped[: m.end()] + ", " + tail + stripped[m.end():] + sentence[len(stripped):]


def add_closer(text: str, closer: str) -> str:
    stripped = text.rstrip()
    trail = text[len(stripped):]
    if stripped and not re.search(r"[.!?][\"'\u201d\u2019)\]]*$", stripped):
        stripped += "."   # don't add a full stop after one that sits inside closing quotes
    closer = match_case(closer, "A")
    if closer[-1] not in ".!?":
        closer += "."
    return stripped + " " + closer + trail


def apply_phonetic(text: str, rules: list[PhoneticRule], eff: Effective, seed: int, infixes: bool = True,
                   keep: Callable[[str], list[tuple[int, int]]] | None = None) -> tuple[str, list[PhoneticRecord]]:
    """Apply each rule in order; every occurrence rolls independently. infixes: whether the swear infixes may
    go in (the embellishment's call: not in a manual or a policy). keep: the spans of a text the drawl and
    infixes stay out of (a heading, a link's text); Australian spelling still applies there."""
    records: list[PhoneticRecord] = []
    kept_for: list = [None, []]   # (text, its kept spans): the same until a rule changes the text
    for rule in rules:
        if rule.vulgarity > 0 and not infixes:
            continue
        # spelling always applies; the drawl scales with the level; a swear infix ("a bloody great stoush")
        # scales with the vulgarity, whatever the level
        if rule.vulgarity > 0:
            top = min(eff.vulgarity, max(r.vulgarity for r in rules))   # the strongest infix tier allowed
            scale = eff.swearing.infix * tier_match(rule.vulgarity, top) if rule.vulgarity <= eff.vulgarity else 0.0
        else:
            scale = 1.0 if rule.kind == "spelling" else eff.profile.phonetic
            if rule.min_level > eff.level:
                continue
        if scale <= 0:
            continue
        counter = {"n": 0}
        quotes = [q.span() for q in QUOTE_RE.finditer(text)] if rule.dialogue_prob is not None else []
        before = text   # the text this rule matches in, for the kept spans (read once, when a rule first matches)

        def kept() -> list[tuple[int, int]]:
            if keep is None or rule.kind == "spelling":
                return []
            if kept_for[0] != before:
                kept_for[:] = [before, keep(before)]
            return kept_for[1]

        def sub(m: re.Match) -> str:
            counter["n"] += 1   # counted either way, so a kept span doesn't shift the rolls after it
            if any(a <= m.start() < b for a, b in kept()):
                return m.group(0)
            in_dialogue = any(a <= m.start() < b for a, b in quotes)
            prob = rule.dialogue_prob if in_dialogue else rule.prob
            if roll(seed, "phonetic", rule.id, counter["n"], m.group(0).lower()) >= prob * scale:
                return m.group(0)
            out = m.expand(rule.replace)
            out = match_case(out, m.group(0)) if out and out[0].isalpha() and m.group(0) else out
            records.append(PhoneticRecord(rule.id, m.group(0), out, m.start()))
            return out

        text = rule.pattern.sub(sub, text)
    return text, records


def pick_riff(riffs: list[Riff], mood: str, r: float) -> Riff:
    """One of an entry's riffs for a roll r in [0, 1). Mood is a lean, not a rule: riffs that suit the text's mood
    weigh more, but a dark text can still take a laugh and a light one a shadow. The first-listed is the best,
    and weighs double."""
    return riffs[weighted_index([riff_weight(x.tone, mood) * (2 if i == 0 else 1) for i, x in enumerate(riffs)], r)]
