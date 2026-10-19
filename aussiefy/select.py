"""Candidate filtering and seeded, weighted selection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import morph
from .detect import Detection
from .policy import Effective, weighted_index
from .schema import Entry
from .realise import question_form
from .context import tone_weight

# detection frame -> entry frames that can fill it
COMPATIBLE = {
    "predicate_adj": ("predicate_adj", "adj", "clause"),
    "adj": ("adj",),
    "adv": ("adv",),
    "np": ("np",),
    "vp": ("vp",),
    "clause": ("clause", "predicate_adj"),
    "interjection": ("interjection",),
    "imperative": ("imperative",),
    "tag": ("tag",),
}


@dataclass
class Candidate:
    entry: Entry
    weight: float
    why: str


class Gated(str):
    """The reason a gated entry was passed over, and the flags that would lift the gate (none: only "all")."""
    locked: tuple[str, ...]

    def __new__(cls, locked: tuple[str, ...]) -> "Gated":
        reason = super().__new__(cls, f"gated by {', '.join(locked) or 'status'}")
        reason.locked = locked
        return reason


def dial_rejection(entry: Entry, eff: Effective) -> str | None:
    """What no surface may offer under this policy: omitted entries, gated ones still locked, and ones above
    the level or the vulgarity (shared with lookup)."""
    if entry.status == "omit":
        return f"status omit (flags: {', '.join(entry.flags) or 'none'})"
    if entry.status == "gate" and "all" not in eff.unlock:
        locked = tuple(sorted(set(entry.flags) - eff.unlock))
        if locked or not entry.flags:
            return Gated(locked)
    if entry.incoherence > eff.level:
        return f"needs level {entry.incoherence}"
    if entry.vulgarity > eff.vulgarity:
        return f"vulgarity {entry.vulgarity} exceeds cap {eff.vulgarity}"
    return None

def semantic_rejection(entry: Entry, *, narrator_opinion: bool) -> str | None:
    """A reviewed mapping's added meaning needs the corresponding resolved permission."""
    if "opinion" in entry.semantic_effects and not narrator_opinion:
        return "adds narrator opinion; narrator_opinion is false"
    return None


def policy_rejection(entry: Entry, eff: Effective) -> str | None:
    """Reasons that depend only on the entry and the policy (shared with garnish)."""
    reason = dial_rejection(entry, eff)
    if reason:
        return reason
    if entry.register not in eff.registers:
        return f"register '{entry.register}' not allowed (allowed: {', '.join(eff.registers)})"
    if eff.regions and entry.region and not set(entry.region) & set(eff.regions):
        return f"region {', '.join(entry.region)} outside {', '.join(eff.regions)}"
    return None


AGENT_PLURAL = re.compile(r"(?:er|or|ist|ian|ent|ant|ee)s$")


def _person_noun(word: str, person_nouns: frozenset[str]) -> bool:
    """A subject word that names a person: a person noun (the dictionary's), a person pronoun or indefinite
    ("she", "everyone"), or a plural agent noun."""
    return (word in person_nouns or word in morph.PERSON_PRONOUNS or word in morph.PERSON_INDEFINITES
            or AGENT_PLURAL.search(word) is not None)


def person_subject(det: Detection, person_nouns: frozenset[str]) -> bool:
    subj, noun = det.captures.get("subj") or det.captures.get("agent"), det.subject_noun
    return (subj is not None and (subj.norm in morph.PERSON_PRONOUNS or
                                  (subj.text[:1].isupper() and subj.norm not in morph.PRONOUNS))) or (
        subj is None and noun is not None and _person_noun(noun.norm, person_nouns))


def fit_rejection(entry: Entry, det: Detection, eff: Effective, person_concepts: set[str],
                  person_nouns: frozenset[str]) -> str | None:
    if entry.frame not in COMPATIBLE.get(det.frame, ()):
        return f"frame {entry.frame} cannot fill a {det.frame} span"
    if entry.frame not in eff.profile.frames:
        return f"frame {entry.frame} not enabled at level {eff.level}"
    if eff.profile.substitution.get(entry.substitution_class, 0) <= 0:
        return f"{entry.substitution_class} substitutions off at level {eff.level}"
    subj = det.captures.get("subj")
    is_person = person_subject(det, person_nouns)
    if (set(entry.concept) & person_concepts and entry.substitution_class == "idiom"
            and det.frame in ("predicate_adj", "clause") and not is_person):
        who = f"'{subj.text}'" if subj is not None else "the subject"
        return f"idiom describes a person but {who} isn't one"
    if det.person_only and not is_person and (subj is not None or det.subject_noun is not None):
        who = det.subject_noun if subj is None else subj
        if not _person_noun(who.norm, person_nouns):
            return f"said only of people, and '{who.text}' isn't one"
    if det.result_clause and entry.substitution_class != "lexical":
        return "'so ... that' construction: only a single-word swap keeps the grammar"
    if entry.frame == "clause" and det.frame != "clause":
        if subj is None or det.clause_start is None:
            return "clause idiom needs a subject to bind {subj}"
        if "be" not in det.captures:
            return "clause idiom needs a verb to carry tense"
    if entry.frame == "predicate_adj" and det.frame == "clause" and not {"subj", "be"} <= set(det.captures):
        return "predicate idiom needs {subj} {be} in the matched clause"
    if entry.frame == "clause" and det.question and not any(question_form(f) for f in entry.all_forms):
        return "clause has no supported question form"
    if not usable_forms(entry, det):
        return "no form fits: " + (form_problem(entry.form, det) or form_problem(entry.all_forms[-1], det) or "")
    return None


def binding_problem(form: str, det: Detection) -> str | None:
    """Why this one form of an entry can't fill the span: a slot with nothing to fill it."""
    needs = set(re.findall(r"\{(\w+)\}", form)) - {"subj", "be", "have", "do"}
    if "poss" in needs and not {"poss", "subj", "agent"} & det.captures.keys() and det.frame != "imperative":
        return "cannot fill {poss}: no subject or possessive in the span"
    if "obj" in needs and "obj" not in det.captures:
        return "cannot fill {obj}: no object in the span"
    if "objposs" in needs and not {"obj", "objposs"} & det.captures.keys():
        return "cannot fill {objposs}: no object or object possessive in the span"
    if "np" in needs and "np" not in det.captures:
        return "cannot fill {np}: no noun phrase in the span"
    return None


def form_problem(form: str, det: Detection) -> str | None:
    reason = binding_problem(form, det)
    if reason:
        return reason
    needs = set(re.findall(r"\{(\w+)\}", form))
    for slot in ("np", "obj", "objposs"):
        captured = det.captures.get(slot)
        represented = slot in needs or slot == "obj" and "objposs" in needs
        if captured is not None and not represented:
            literal = re.sub(r"\{\w+\}", "", form).lower()
            if not re.search(r"(?<!\w)" + re.escape(captured.norm) + r"(?!\w)", literal):
                return f"would discard {{{slot}}}: {captured.text}"
    return None


def usable_forms(entry: Entry, det: Detection) -> list[str]:
    """The entry's forms (its form and variants) whose slots this span can fill: "his wife" takes "{poss}
    missus", a bare "wife" takes "the missus"."""
    return [f for f in entry.all_forms if form_problem(f, det) is None
            and (entry.frame != "clause" or not det.question or question_form(f) is not None)]


def candidates(det: Detection, entries: list[Entry], eff: Effective, used: dict[str, int],
               person_concepts: set[str], person_nouns: frozenset[str], *, mood: str | None = None
               ) -> tuple[list[Candidate], list[tuple[Entry, str]]]:
    eligible: list[Candidate] = []
    rejected: list[tuple[Entry, str]] = []
    concepts = set(det.concepts)
    for e in entries:
        if not concepts & set(e.concept):
            continue
        reason = policy_rejection(e, eff) or fit_rejection(e, det, eff, person_concepts, person_nouns)
        if reason:
            rejected.append((e, reason))
            continue
        p_class = eff.profile.substitution[e.substitution_class]
        intensity_fit = 1.0 / (1.0 + abs(e.intensity - det.intensity))
        direct = 2.0 if e.id in det.direct else 1.0
        sources = 1.0 + 0.1 * min(len(e.sources), 5)
        repeat = 0.2 ** used.get(e.id, 0)
        regional = 1.5 if eff.regions and set(e.region) & set(eff.regions) else 1.0
        # where a level allows dated words they're colour, not the default: "bloke" over "cove"
        dated = 0.25 if e.register in ("dated", "archaic") else 1.0
        lean = eff.swearing.lean if e.vulgarity else 1.0   # how a vulgarity leans towards the swearing option
        if lean == 0:
            rejected.append((e, "swear weighting disabled"))
            continue
        tone_fit = tone_weight(e.tone, mood) if mood is not None else 1.0
        w = e.weight * intensity_fit * direct * sources * repeat * regional * p_class * dated * lean * tone_fit
        why = (f"w={w:.3f} (base {e.weight:g} x intensity-fit {intensity_fit:.2f} [{e.intensity} vs {det.intensity}]"
               f" x direct {direct:g} x sources {sources:.1f} x repeat {repeat:.2f}"
               + (f" x region {regional:g}" if regional != 1 else "") + (f" x {e.register} {dated:g}" if dated != 1 else "")
               + f" x p({e.substitution_class}) {p_class:g}"
               + (f" x tone-fit {tone_fit:g} ({e.tone}/{mood})" if mood is not None else "") + ")")
        eligible.append(Candidate(e, w, why))
    eligible.sort(key=lambda c: c.entry.id)
    return eligible, rejected


def weighted_pick(cands: list[Candidate], r: float) -> Candidate:
    return cands[weighted_index([c.weight for c in cands], r)]
