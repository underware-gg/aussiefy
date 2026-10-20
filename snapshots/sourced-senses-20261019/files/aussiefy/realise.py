"""Slot filling and agreement for a chosen entry."""

from __future__ import annotations

import re

from . import morph
from .detect import DETERMINERS, VERB_LEADERS, NP_BREAKS, Detection, after_determiner, opening_determiner
from .matcher import NP_BOUNDARY, is_name
from .schema import Entry
from .text import Token, capital_is_positional

QUESTION_RE = re.compile(r"^\{subj\}\s+\{(be|have|do)\}\s+(.+)$")
ARTICLES = {"a", "an", "the"}

# --- a noun phrase's determiner and number -------------------------------------------------------------------
# words after which a noun phrase has ended: "the dead [shall]", "the poor [are]", "the fallen [who]"
NP_ENDS = (NP_BOUNDARY | NP_BREAKS | morph.BE_FORMS | morph.HAVE_FORMS | morph.DO_FORMS | VERB_LEADERS
           | {"here", "there", "now", "then", "too", "also", "again", "today", "yet", "still"})
# the determiners a swap keeps when its term has none ("the dead" -> "the poor buggers"); not "no" or "a",
# which the term carries in its sense ("no chance" -> "Buckley's", "a long time" -> "yonks")
KEPT_DETERMINERS = {"the", "this", "that", "these", "those"} | morph.POSSESSIVES
OWN_ARTICLE_RE = re.compile(r"(?:the|a|an|some) ", re.I)
# a term that opens on one of these is a phrase, not a noun a determiner can go before ("out in the mulga")
NOT_AFTER_DETERMINER = NP_BOUNDARY | NP_BREAKS | {"beyond", "out", "up", "down", "over", "off", "back", "away"}
# words for a body of people, which a plural term can stand for: collective nouns ("the public" -> "the
# punters") and adjectives used as nouns ("the dead" -> "the poor buggers", "the poor" -> "the battlers")
SINGULAR_VERBS = {"is", "was", "has", "does", "seems", "appears", "remains", "wants", "needs", "says", "thinks",
                  "knows", "feels", "likes", "loves", "hates", "deserves", "expects"}
COLLECTIVES = {"public", "people", "folk", "crowd", "audience", "family", "team", "staff", "police", "government",
               "mob", "community", "population", "electorate", "everyone", "everybody", "masses", "populace",
               "dead", "fallen", "departed", "living", "wounded", "poor", "rich", "young", "old", "elderly",
               "homeless", "unemployed", "sick", "needy", "brave", "faithful"}


def kept_determiner(det: Detection, toks: list[Token]) -> str | None:
    """The determiner a noun-phrase span opens with, when a term without one should keep it ("the" of "the
    dead")."""
    first = toks[det.start].norm
    return first if det.frame == "np" and det.end - det.start > 1 and first in KEPT_DETERMINERS else None


def has_own_article(form: str) -> bool:
    return OWN_ARTICLE_RE.match(form) is not None or form.split(" ", 1)[0].lower() in morph.POSSESSIVES \
        or form.startswith("{poss}")


def is_plural_term(entry: Entry) -> bool:
    """A term already plural in form ("strides", "the olds", "togs"), which a plural span leaves as it is."""
    head = entry.form.split()[-1]
    return not entry.form.lower().startswith(("a ", "an ")) and morph.singular_of(head) is not None


def phrase_continues(det: Detection, toks: list[Token], end: int) -> bool:
    """A word after a "the X" span carries the noun phrase on ("the poor [old] minister"): the trigger caught an
    adjective, not the noun it stands for."""
    if kept_determiner(det, toks) is None or end >= len(toks):
        return False
    nxt = toks[end]
    return nxt.is_word and nxt.norm not in NP_ENDS and not nxt.text[:1].isupper()


def number_problem(entry: Entry, det: Detection, toks: list[Token]) -> str | None:
    """Why a term can't go in this span for its number: a term plural in form after "a" ("a togs"), or a
    plural-only term for one ("a young politician" isn't "a young pollies"),
    unless the span names a body of people ("the public" -> "the punters")."""
    if entry.frame != "np" or det.inflection in ("plural", "written_plural"):
        return None
    # "my togs", but not "a togs": the span's own "a" goes with it ("a long time" -> "yonks"), so only an "a"
    # before the span counts
    if is_plural_term(entry) and opening_determiner(toks, det.start) in ("a", "an"):
        return "a term plural in form (togs, sunnies) after 'a'"
    if is_plural_term(entry):
        before = det.start - 1
        while before >= 0 and toks[before].norm in DETERMINERS | {"not", "n't"}:
            before -= 1
        after = toks[det.end].norm if det.end < len(toks) else ""
        object_question = (toks[0].norm in {"what", "which", "whose"} and det.end + 1 < len(toks)
                           and (toks[det.end + 1].norm in morph.PRONOUNS or is_name(toks[det.end + 1])))
        if after in SINGULAR_VERBS and not object_question or before >= 0 and toks[before].norm in {"is", "was"}:
            return "a term plural in form with a singular agreeing verb"
    if entry.number != "plural":
        return None
    if toks[det.end - 1].norm in COLLECTIVES:
        # a body of people takes a plural term, unless the verb after it is singular: "the public is angry"
        # isn't "the punters is"
        nxt = toks[det.end].norm if det.end < len(toks) else ""
        return "a plural term before a singular verb" if nxt in SINGULAR_VERBS else None
    return "a plural term for one"


def fit_article(out: str, entry: Entry, det: Detection, toks: list[Token]) -> str:
    """A noun phrase's swap with the phrase's own determiner: kept where the term has none ("the dead" -> "the
    poor buggers", "his wife" -> "his missus"), and the term's own a/an/the dropped where the phrase already
    has a determiner ("the old waterhole" -> "the old billabong") or is plural ("wild horses" -> "brumbies").
    "some" stays: it is the term's sense ("some bugger")."""
    if entry.frame != "np":
        return out
    lead = kept_determiner(det, toks)
    first = out.split(" ", 1)[0]
    if lead and not has_own_article(out):
        # not before a place said as a phrase or a name: "in the sticks" -> "in beyond the black stump",
        # "in Woop Woop"
        return out if first.lower() in NOT_AFTER_DETERMINER or first[:1].isupper() else f"{lead} {out}"
    plural = det.inflection == "plural" or (det.inflection == "written_plural" and bool(entry.plural))
    opens_with_determiner = toks[det.start].norm in DETERMINERS   # "a shambles" keeps "a shemozzle"
    if lead is None and not opens_with_determiner and first.lower() in ("a", "an", "the") and " " in out and (
            plural and first.lower() in ("a", "an") or after_determiner(toks, det.start)
            or _after_proper_modifier(toks, det.start)):
        return out.split(" ", 1)[1]
    return out


def _after_proper_modifier(toks: list[Token], start: int) -> bool:
    """A capitalised word just before the span that isn't there for its position ("the family of American
    musician Bob Weir"): a proper modifier in a bare noun phrase, so a term's article ("a muso") goes."""
    return start > 0 and toks[start - 1].is_word and toks[start - 1].text[:1].isupper() \
        and toks[start - 1].text != "I" and not capital_is_positional(toks, start - 1)


REFLEXIVES = {"hisself": "himself", "theirself": "themselves", "ourself": "ourselves", "itsself": "itself"}
REFLEXIVE_RE = re.compile(r"\b(" + "|".join(REFLEXIVES) + r")\b", re.I)


def question_form(form: str) -> str | None:
    """Invert a modular clause. Fixed finite/negative idioms need an explicit question form instead."""
    if form.startswith("there {be} "):
        return "{be} there " + form[len("there {be} "):]
    m = QUESTION_RE.fullmatch(form)
    if not m:
        return None
    slot, rest = m.groups()
    if slot == "be" or slot == "have" and morph.is_participle(rest.split()[0]):
        return "{" + slot + "} {subj} " + rest
    return "{do} {subj} " + slot + " " + rest


def replacement_span(entry: Entry, det: Detection, sent: list[Token]) -> tuple[int, int]:
    """Token range (sentence-local) the realised entry replaces."""
    if entry.frame == "clause" and det.clause_start is not None:
        start = det.clause_start
        if det.question:  # "are you crazy": the inverted verb starts the clause
            be = det.captures.get("be")
            if be is not None:
                start = min(start, be.i - sent[0].i)
        return start, det.end
    if entry.frame == "predicate_adj" and det.frame == "clause":
        after = max(det.captures[k].i for k in ("subj", "be")) - sent[0].i + 1
        return after, det.end
    return det.start, det.end


def _subject_text(tok: Token | None) -> str:
    if tok is None:
        return "you"
    return tok.text if tok.norm == "i" or tok.text[:1].isupper() and tok.norm not in morph.PRONOUNS else tok.norm


def noun_slots(det: Detection) -> dict[str, str]:
    caps = det.captures
    subj = caps.get("subj")
    return {
        "poss": caps["poss"].norm if "poss" in caps else (
            morph.possessive_of(subj.norm) if subj is not None
            else morph.possessive_of(caps["agent"].norm) if "agent" in caps else "your"),
        "obj": caps["obj"].text if "obj" in caps else "",
        "objposs": caps["objposs"].text if "objposs" in caps else (
            morph.possessive_of_object(caps["obj"].text) if "obj" in caps else "their"),
        "np": caps["np"].text if "np" in caps else "",
    }


def realise(entry: Entry, form: str, det: Detection) -> str:
    caps = det.captures
    subj_tok = caps.get("subj")
    subj = subj_tok.norm if subj_tok is not None else "you"
    verb = caps.get("be") or caps.get("have") or caps.get("do")
    if verb is not None:
        tense = morph.tense_of(verb.norm)
    elif det.inflection in ("past", "pp"):
        tense = "past"
    else:
        tense = det.tense
    # with no subject captured, a {np} is what the verb slots agree with ("her assertion had Buckley's")
    agree_subj = subj if subj_tok is not None else ("it" if "np" in caps or form.startswith("there ") else "you")

    text = form
    if entry.frame == "vp" and det.inflection in morph.VERB_FORMS:
        head, _, rest = text.partition(" ")
        if not head.startswith("{"):
            text = (morph.inflect(head, det.inflection) + (" " + rest if rest else ""))
    # a later verb that follows the tense: "think the sun shines|shone out of ..."
    text = re.sub(r"([\w']+)\|([\w']+)", lambda m: m.group(2) if tense == "past" else m.group(1), text)
    # a term already plural ("strides", "the olds") stays as it is; a trigger written as a plural takes the
    # entry's own plural, or the term as written (spelling can't tell "wild horses" from "a shambles")
    if entry.frame == "np" and det.inflection == "plural" and not is_plural_term(entry):
        text = entry.plural or morph.pluralise(text)
    elif entry.frame == "np" and det.inflection == "written_plural" and entry.plural:
        text = entry.plural
    # a simile with a plural subject: "we were like koalas up a gum tree"
    if entry.frame == "predicate_adj" and entry.plural and verb is not None \
            and verb.norm in ("are", "were", "'re") and subj not in ("you", "i"):
        text = entry.plural

    if entry.frame == "clause" and det.question:
        text = question_form(text)
        assert text is not None, "selection must reject clauses without a supported question form"

    values = {
        "subj": _subject_text(subj_tok),
        **noun_slots(det),
        "be": morph.agree("be", agree_subj, tense),
        "have": morph.agree("have", agree_subj, tense),
        "do": morph.agree("do", agree_subj, tense),
        "will": "would" if tense == "past" else "will",
    }
    out = re.sub(r"\{(\w+)\}", lambda m: values[m.group(1)], text).strip()
    out = REFLEXIVE_RE.sub(lambda m: REFLEXIVES[m.group(1).lower()], out)   # "{poss}self" for they: themselves
    if entry.frame == "clause" and not det.question and subj_tok is not None and verb is not None:
        # "it's pouring" -> "it's bucketing down", not "it is bucketing down"
        m = re.match(r"\{subj\}\s+\{(be|have)\}", form)
        if m and verb.text.startswith(("'", "\u2019")) and verb.i == subj_tok.i + 1:
            lemma = m.group(1)
            realised = values[lemma]
            if realised == verb.norm or (lemma == "have" and realised == "has" and verb.text[1:] == "s"):
                head = f"{values['subj']} {realised}"
                if out.startswith(head):
                    out = values["subj"] + verb.text + out[len(head):]
    return out
