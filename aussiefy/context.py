"""Reading a sentence and a text: what kind of sentence it is (dialogue, a question, narration ending on a deed)
and what mood the whole text is in (solemn, dark or light). Pure functions over tokens and text; the engine
uses them to decide which garnish fits, lint and the harness to explain it."""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import morph
from .morph import is_past
from . import pos
from .text import INLINE_CHAR, QUOTES, Token

# not "must" ("nobody must know it") or "fair" (also the noun: "going to the fair")
OPINION_WORDS = {"reckon", "reckons", "think", "thinks", "believe", "believes", "should", "ought",
                 "deserve", "deserves", "equal", "proposition", "unfair"}


CLAUSE_JOINS = {"and", "but", "until", "till", "when", "while", "so", "then", "because", "though", "or"}


FINITE_HINTS = {"am", "is", "are", "was", "were", "have", "has", "had", "do", "does", "did", "will", "would", "can",
                "could", "shall", "should", "may", "might", "must", "not", "i", "we", "they", "he", "she", "you"}

CLAUSE_END = {".", "!", "?", ";", ":"}
AUXILIARIES = (morph.BE_FORMS | morph.HAVE_FORMS | morph.DO_FORMS
               | {"will", "would", "can", "could", "shall", "should", "may", "might", "must"})
NEGATION = {"not", "n't", "never", "no", "without", "nobody", "nothing", "neither", "none"}
DEGREE_PREFIXES = tuple(tuple(words.split()) for words in morph.INTENSIFIERS if " " in words)
TIME_UNITS = {"second", "minute", "hour", "day", "week", "fortnight", "month", "year", "morning", "afternoon",
              "evening", "night", "time"}
TIME_MODIFIERS = {"every", "each", "all", "this", "that", "these", "those", "next", "last"}
RELATIVE_TIMES = {"today", "tomorrow", "yesterday", "tonight"}
FREQUENCY_COUNTS = {"once", "twice", "thrice"}


@dataclass(frozen=True)
class FollowingContext:
    word: str | None = None
    known: bool = True


def following_context(tokens: list[Token], end: int, complete: bool = True) -> FollowingContext:
    """The next clause word, an established boundary, or context hidden by markup."""
    for i in range(end, len(tokens)):
        token = tokens[i]
        if token.text in CLAUSE_END:
            return FollowingContext()
        if INLINE_CHAR.match(token.text):
            return FollowingContext(known=False)
        if token.is_word:
            return FollowingContext(token.norm)
    return FollowingContext(known=complete)


def positive_context(tokens: list[Token], start: int, end: int) -> bool:
    while start > 0 and tokens[start - 1].text not in CLAUSE_END and tokens[start - 1].norm not in {"and", "but", "or"}:
        start -= 1
    return not any(t.norm in NEGATION for t in tokens[start:end])


def verb_subject(tokens: list[Token], start: int, tags: list[str] | None) -> Token | None:
    """A local subject through auxiliaries and adverbs; never through another lexical verb or clause."""
    j = start - 1
    while j >= 0:
        token = tokens[j]
        if token.norm in morph.PRONOUNS or token.norm in morph.PERSON_INDEFINITES:
            return token
        if token.norm in AUXILIARIES or token.norm in {"not", "n't", "never"} or (
                tags is not None and tags[j] in {"RB", "RBR", "RBS"}):
            j -= 1
            continue
        if tags is not None and tags[j] in pos.NOUNS | pos.NAMES:
            return token
        return None
    return None


def _noun_argument_head(words: tuple[str, ...], tags: list[str]) -> str | None:
    if words[:2] in {("at", "least"), ("at", "most")}:
        words, tags = words[2:], tags[2:]
    # A short degree phrase can be mistagged as nominal ("a bit harder"). Leave ambiguous heads plain.
    if any(len(words) == len(prefix) + 1 and words[:len(prefix)] == prefix for prefix in DEGREE_PREFIXES):
        return None
    # The tagger can mistake "thrice" for a participle; frequency adverbs do not head a gerund argument.
    head = next((tag for word, tag in zip(words, tags) if tag not in {"RB", "RBR", "RBS"}
                 and not (word in FREQUENCY_COUNTS and tag == "VBG")), None)
    nominal = pos.NOUNS | pos.NAMES | {"PRP", "WP", "CD"}
    if head in {"IN", "TO"}:
        return None
    if (bool(tags) and tags[-1] in nominal or head == "VBG"
            or len(words) == 1 and words[0] in {
                "this", "that", "these", "those", "some", "any", "both", "all", "another", "each", "either", "neither"}):
        return head
    return None


def _temporal_tail(words: tuple[str, ...], tags: list[str], following: list[Token]) -> bool:
    """A bounded time adjunct, including one swallowed after a nominal object."""
    if "of" in words:
        at = words.index("of")
        if at and _noun_argument_head(words[at + 1:], tags[at + 1:]) is not None \
                and _temporal_tail(words[:at], tags[:at], []):
            return True
    if tags[-1] in pos.NAMES:
        return False
    if words[-1] in RELATIVE_TIMES:
        return True
    unit = morph.singular_of(words[-1]) or words[-1]
    if unit not in TIME_UNITS:
        return False
    if len(words) >= 3 and words[-3] in FREQUENCY_COUNTS and words[-2] in {"a", "an"}:
        return True
    if len(words) >= 4 and words[-2] == "per" and tags[-4] == "CD" \
            and (morph.singular_of(words[-3]) or words[-3]) in TIME_UNITS:
        return True
    tail = tuple(t.norm for t in following[:2])
    if words[-1] == "time" and tail == ("and", "again") or tail == ("after", words[-1]):
        return True
    return any((word in TIME_MODIFIERS or tags[i] == "CD")
               and all(tag in {"DT", "PDT", "CD", "JJ", "JJR", "JJS", "VBG"} | pos.NOUNS
                       for tag in tags[i + 1:-1])
               for i, word in enumerate(words[:-1]))


def noun_argument(capture: Token, tokens: list[Token], tags: list[str], *, unanchored_object: bool = False) -> bool:
    """A nominal or gerund-headed argument, rather than an adjective/adverb mistaken for an object."""
    start = capture.i - tokens[0].i
    end = start
    while end < len(tokens) and tokens[end].end <= capture.end:
        end += 1
    phrase = tags[start:end]
    words = tuple(t.norm for t in tokens[start:end])
    head = _noun_argument_head(words, phrase)
    if head is None:
        return False
    if head != "VBG" and unanchored_object and _temporal_tail(words, phrase, tokens[end:]):
        return False
    return True


def sentence_contexts(sent: list[Token], tags: list[str] | None = None) -> set[str]:
    """What kind of sentence this is, for garnish that only suits some ("mate" needs someone addressed)."""
    norms = [t.norm for t in sent]
    texts = [t.text for t in sent]
    ctx = {"any"}
    if any(q in texts for q in QUOTES):
        ctx.add("dialogue")
    if "?" in texts:
        ctx.add("question")
    if "!" in texts:
        ctx.add("exclamation")
    if {"you", "your", "yourself", "ya", "yer"} & set(norms):
        ctx.add("second_person")
    if OPINION_WORDS & set(norms):
        ctx.add("opinion")
    if not ctx & {"dialogue", "question", "exclamation", "second_person"}:
        ctx.add("narration")
    finite = FINITE_HINTS & set(norms)
    if not finite:
        finite = _finite_clause(sent, tags if tags is not None else pos.tag(texts))
    if not finite and not ctx & {"dialogue"}:
        ctx.add("fragment")   # "Robot apartments! invisible suburbs!": an incantation, nobody to tag
    # narration that ends on someone doing something ("... until he consented."), so a jibe at the doer fits
    # ("..., like a drongo"); never on anything grim ("the old man died, like a drongo")
    # the last clause ("... until he consented") must have the doer and end on the deed, not a state
    # ("was always well dressed") or someone else ("nobody answered")
    cut = max((i for i, t in enumerate(sent) if t.text in (",", ";", ":") or t.norm in CLAUSE_JOINS), default=-1)
    clause = [t for t in sent[cut + 1:] if t.is_word]
    last = clause[-1].norm if clause else ""
    before = {t.norm for t in clause[-3:-1]}
    if "narration" in ctx and len(clause) >= 2 and clause[0].norm in ("he", "she", "they") \
            and is_past(last) and last not in ("was", "were", "had") \
            and not before & {"was", "were", "is", "are", "be", "been", "being", "well", "so", "very", "too"} \
            and not _hits(DARK_WORDS, " ".join(norms)):
        ctx.add("action_end")
    return ctx


def _finite_clause(sent: list[Token], tags: list[str]) -> bool:
    """Finite verbs need a subject and a main clause; noun/gerund headings do not qualify."""
    subject = False
    subordinate = False
    for token, tag in zip(sent, tags):
        if token.text in (",", ";", ":"):
            subject, subordinate = False, False
        elif ((token.norm in ("that", "which", "who") and tag in ("WDT", "WP"))
              or token.norm in ("if", "unless", "when", "while", "because", "although", "whether", "until",
                                "before", "after") and tag in ("IN", "WRB")):
            subordinate = True
        elif tag in ("VBD", "VBP", "VBZ") and subject and not subordinate:
            return True
        elif tag in (*pos.NOUNS, *pos.NAMES, "PRP"):
            subject = True
    return False


# Words of remembrance and reverence. A text full of them (a eulogy, Gettysburg) gets no comic riffs.
SOLEMN_WORDS = {"dedicate", "dedicated", "consecrate", "consecrated", "hallow", "hallowed", "sacred", "devotion",
                "nobly", "honoured", "honored", "perish", "perished", "mourn", "mourning", "memorial", "solemn",
                "sacrifice", "sacrificed", "fallen", "grave", "graves", "eulogy", "funeral", "condolences",
                "rest in peace", "resting place", "gave their lives", "laid down", "remembrance"}


# Words of darkness. A light text (a fairy tale) gets no grim riffs.
DARK_WORDS = {"dead", "death", "die", "died", "dying", "kill", "killed", "war", "wars", "battle", "blood", "bomb",
              "bombs", "prison", "jail", "grave", "tomb", "nightmare", "despair", "suicide", "suicides", "sorrow",
              "sorrows", "misery", "weep", "weeping", "sobbing", "scream", "screaming", "screams", "filth", "poverty",
              "corpse", "murder", "cruel", "agony", "grief", "horror", "doom", "madness", "insane", "crucifixion",
              "crucifixions", "loveless", "soulless", "hell",
              # gloom and lament (Hamlet's soliloquy, The Raven)
              "dreary", "bleak", "ghost", "ghosts", "mortal", "calamity", "dread", "heartache", "pangs",
              "nevermore", "darkness", "lost", "weary", "oppressor", "tombs", "mourned", "dying"}
# grave public prose (the Declaration): no comic garnish, like a eulogy
GRAVE_WORDS = {"tyranny", "despotism", "usurpations", "unalienable", "self-evident", "oppression", "grievances",
               "solemnly", "hereby", "whereas", "inalienable", "providence"}


def _hits(words: set[str], low: str) -> int:
    return sum(1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", low))


# an obituary: a death and the age at death, with its rites or the family left. Each group counts once ("died" and
# "death" are one cue); an engine that "died" in a yarn about a boat, or a fable's funeral, has no age at death
OBITUARY_CUES = {
    "death": {"died", "death", "passed away"},
    "rites": {"funeral", "funerals", "laid to rest", "memorial service", "buried", "burial", "in lieu of flowers"},
    "family": {"survived by", "is survived", "widow", "widower", "predeceased", "loved ones"},
}
AGE_AT_DEATH = re.compile(r"\baged \d{2,3}\b|\bwas \d{2,3}(?: years old\b|\.)|\bat (?:the )?age (?:of )?\d{2,3}\b")


def is_obituary(low: str) -> bool:
    """A death and the age at death, with its rites or the family left (lower-cased text)."""
    found = {g for g, cues in OBITUARY_CUES.items() if _hits(cues, low)}
    return "death" in found and bool(AGE_AT_DEATH.search(low)) and bool(found & {"rites", "family"})


def is_solemn(text: str) -> bool:
    low = text.lower()
    return _hits(SOLEMN_WORDS, low) >= 3 or _hits(GRAVE_WORDS, low) >= 2 or is_obituary(low)


def text_mood(text: str) -> str:
    """solemn (a eulogy, Gettysburg, an obituary: no comic riffs or terms), dark (a rant or lament: anything
    goes) or light (a fairy tale: no grim riffs)."""
    low = text.lower()
    if is_solemn(text):
        return "solemn"
    # dark by density: Hamlet and The Raven are dark; Hansel and Gretel, with its one famine, isn't
    hits, words = _hits(DARK_WORDS, low), max(1, len(low.split()))
    return "dark" if hits >= 4 and hits * 100 / words >= 1.2 else "light"


# Which garnish tones suit a text's mood: riffs off mood are down-weighted, closers and asides off mood never run.
RIFF_TONES_FOR = {"solemn": {"grim", "plain"}, "dark": {"comic", "grim", "plain"}, "light": {"comic", "plain"}}
OFF_MOOD_WEIGHT = 0.25   # a riff against the text's mood is a quarter as likely, not banned


# ...and the tones a closing exclamation may take: "Fuck me dead." doesn't end Hamlet's soliloquy, nor
# "Too easy." The Raven
CLOSING_TONES_FOR = {"light": {"comic", "plain", "grim"}, "dark": {"plain", "grim"}, "solemn": {"grim"}}


def tone_weight(tone: str, mood: str) -> float:
    return 1.0 if tone in RIFF_TONES_FOR[mood] else OFF_MOOD_WEIGHT


def is_chant(sents: list[list[Token]]) -> bool:
    """A poem or litany of short exclamations ("Moloch! Solitude! Filth!"): garnish at the edges of each line
    breaks its rhythm, so only stanza-end asides and the closer apply."""
    if len(sents) < 6:
        return False
    shouts = sum(1 for s in sents if s[-1].text == "!")
    words = sum(1 for s in sents for t in s if t.is_word)
    return shouts / len(sents) >= 0.6 and words / len(sents) <= 10



# Latinate shapes that read as formal register: proposition, consecrated, devotion, comfortably, honored.
FORMAL_RE = re.compile(r"(tion|sion|ment|ity|ence|ance|ive|ous|ated?|ates|i[sz]ed?|ible|able|ably|ibly|ary|ory|"
                       r"ial|ual|ored)s?$|^(con|pro|sub|trans|inter|per|ad|as|ap)\w{4,}ed$")
