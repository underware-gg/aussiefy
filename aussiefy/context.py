"""Reading a sentence and a text: what kind of sentence it is (dialogue, a question, narration ending on a deed)
and what mood the whole text is in (solemn, dark or light). Pure functions over tokens and text; the engine
uses them to decide which garnish fits, lint and the harness to explain it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple

from . import morph
from .morph import is_past
from . import pos
from .matcher import phrase_token
from .text import INLINE_CHAR, QUOTES, Token

# not "must" ("nobody must know it") or "fair" (also the noun: "going to the fair")
OPINION_WORDS = {"reckon", "reckons", "think", "thinks", "believe", "believes", "should", "ought",
                 "deserve", "deserves", "equal", "proposition", "unfair"}


CLAUSE_JOINS = {"and", "but", "until", "till", "when", "while", "so", "then", "because", "though", "or"}


FINITE_HINTS = {"am", "is", "are", "was", "were", "have", "has", "had", "do", "does", "did", "will", "would", "can",
                "could", "shall", "should", "may", "might", "must", "not", "i", "we", "they", "he", "she", "you"}

CLAUSE_END = {".", "!", "?", ";", ":"}
TIME_ADVERBS = frozenset({"today", "tomorrow", "yesterday", "tonight"})
AUXILIARIES = (morph.BE_FORMS | morph.HAVE_FORMS | morph.DO_FORMS
               | {"will", "would", "can", "could", "shall", "should", "may", "might", "must"})
NEGATION = {"not", "n't", "never", "no", "without", "nobody", "nothing", "neither", "none"}
DEGREE_PREFIXES = tuple(tuple(words.split()) for words in morph.INTENSIFIERS if " " in words)
TIME_UNITS = {"second", "minute", "hour", "day", "week", "fortnight", "month", "year", "morning", "afternoon",
              "evening", "night", "time"}
TIME_MODIFIERS = {"every", "each", "all", "this", "that", "these", "those", "next", "last"}
RELATIVE_TIMES = {"today", "tomorrow", "yesterday", "tonight"}
AMOUNT_HEADS = {'lot', 'bit', 'deal', 'amount', 'quantity', 'much', 'more', 'less', 'plenty'}
AMOUNT_MODIFIERS = {'DT', 'PDT', 'CD', 'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS'}
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


def following_shape(tokens: list[Token], end: int, tags: list[str], *, complete: bool = True) -> str | None:
    """The whole phrase's next grammatical boundary; None is insufficient or ambiguous source evidence."""
    if end >= len(tokens):
        return 'none' if complete else None
    token = tokens[end]
    if INLINE_CHAR.match(token.text):
        return None
    if token.text in CLAUSE_END:
        return 'none'
    if token.text == ',' and end + 1 < len(tokens) and tokens[end + 1].norm in CLAUSE_JOINS:
        return 'none'
    if token.text == ',' and end + 1 < len(tokens):
        subject_end = noun_phrase_end(tokens, end + 1, tags)
        verb = _clause_verb_after(tokens, subject_end, tags) if subject_end > end + 1 else None
        if verb is not None and verb.settled:
            return 'none'
    if token.is_punct:
        return None
    word = token.norm
    if word in CLAUSE_JOINS:
        return 'none'
    if word in {'that', 'whether', 'if'}:
        return 'content'
    if word == 'to' and end + 1 < len(tokens) and tags[end + 1] == 'VB':
        return 'infinitive'
    if tags[end] in {'IN', 'TO'} or word in NOUN_PREPOSITIONS_FOR_BOUNDARY:
        if end + 1 < len(tokens):
            argument = context_object(tokens, end + 1, tags)
            if argument is not None and argument.settled:
                return 'prep:' + word
        return None
    if tags[end] == 'VB':
        return 'verb_base'
    if tags[end].startswith('RB') or word in TIME_ADVERBS:
        return 'adverb'
    nominal_end = noun_phrase_end(tokens, end, tags)
    if word in TIME_MODIFIERS and nominal_end > end and tokens[nominal_end - 1].norm in TIME_UNITS:
        return 'adverb'
    argument = context_object(tokens, end, tags)
    if argument is not None and argument.settled:
        if word in TIME_MODIFIERS and tokens[argument.end - 1].norm in TIME_UNITS:
            return 'adverb'
        return 'np'
    verb = _clause_verb_after(tokens, nominal_end, tags) if nominal_end > end else None
    return 'content' if verb is not None and verb.settled else None


NOUN_PREPOSITIONS_FOR_BOUNDARY = frozenset({'for', 'from', 'with', 'about', 'at', 'on', 'in', 'into', 'of', 'to',
                                          'through', 'by', 'over', 'against'})


RESULT_DEGREE = frozenset({"so", "too", "such"})   # degree words that license a "that"/"to" result complement


def claimed_result_degree(tokens: list[Token], start: int, end: int, reading_end: int) -> str:
    """A so/too/such inside the span whose result complement comes straight after the reading ("thought so
    much of new clothes that he spent ...", "too hot to sleep"): a replacement must keep it, or the
    complement dangles. A later "to" or "that" ("too hot and we went to the beach", "thank you so much,
    that's ...") is not its complement."""
    degree = next((t.norm for t in tokens[start:end] if t.norm in RESULT_DEGREE), "")
    return degree if degree and reading_end < len(tokens) and tokens[reading_end].norm in {"that", "to"} else ""


NP_DETERMINER_TAGS = frozenset({"DT", "PDT", "PRP$", "CD"})
NP_MODIFIER_TAGS = frozenset({"JJ", "JJR", "JJS", "CD"}) | pos.NOUNS | pos.NAMES
FINITE_TAGS = frozenset({"VBD", "VBP", "VBZ", "MD"})
COMPARATIVE_MODIFIERS = frozenset({'much', 'far'})


def _comparative_adjective(word: str, adjective_words: frozenset[str]) -> bool:
    if not word.endswith('er'):
        return False
    stems = {word[:-2], word[:-1], word[:-3] + 'y'}
    if len(word) > 3 and word[-3] == word[-4]:
        stems.add(word[:-3])
    return bool(stems & adjective_words)


def nominal_role(tokens: list[Token], start: int, end: int, tags: list[str], *,
                 predicate: bool = False, adjective_words: frozenset[str] = frozenset()) -> str:
    """A nominal span's grammatical role, without treating a noun modifier as an unsafe substitution."""
    head = end - 1
    after = tags[end] if end < len(tags) else None
    if after == 'POS' or (end < len(tokens) and tokens[end].norm in {"'s", "'"}
                         and tokens[end].start == tokens[head].end):
        return 'possessor'
    word = tokens[head].norm
    comparative = _comparative_adjective(word, adjective_words)
    nominal_end = noun_phrase_end(tokens, end, tags) if end < len(tokens) else end
    before_noun = nominal_end > end and tags[nominal_end - 1] in pos.NOUNS | pos.NAMES
    temporal = end < len(tokens) and (tokens[end].norm in TIME_ADVERBS
        or tokens[end].norm in TIME_MODIFIERS and nominal_end > end
        and tokens[nominal_end - 1].norm in TIME_UNITS)
    if temporal:
        before_noun = False
    if comparative and before_noun and (morph.singular_of(tokens[nominal_end - 1].norm)
                                        or tokens[nominal_end - 1].norm) in TIME_UNITS:
        return 'adjective'
    if before_noun:
        return 'modifier'
    determined = any(tags[i] in NP_DETERMINER_TAGS for i in range(start, head)) or (
        start > 0 and tags[start - 1] in NP_DETERMINER_TAGS)
    if comparative and end + 1 < len(tokens) and tokens[end].text == ',':
        if _comparative_adjective(tokens[end + 1].norm, adjective_words) and (
                not determined or noun_phrase_end(tokens, end + 2, tags) > end + 2):
            return 'adjective'
    if determined:
        return 'head'
    if (tags[head].startswith('JJ') or comparative) and predicate:
        return 'adjective'
    if tags[head] in pos.NOUNS | pos.NAMES:
        return 'head'
    return 'unknown'


SUBORDINATORS = frozenset({"when", "whenever", "because", "if", "although", "though", "while", "since", "unless",
                           "until", "before", "after", "as", "where", "than"})
RELATIVES = frozenset({"who", "whom", "which", "that"})
FREE_RELATIVES = frozenset({"what", "whatever"})   # a relative clause with no noun: "believe what he says"


def lone_pronoun_object(tokens: list[Token], start: int, tags: list[str]) -> bool:
    """A pronoun is a phrase on its own, and an object pronoun is one whatever the tagger says ("her" before
    "that" reads as possessive); "her" before a nominal is a possessive determiner ("her dog")."""
    possessive = tokens[start].norm == "her" and start + 1 < len(tokens) and tags[start + 1] in NP_MODIFIER_TAGS
    return tags[start] == "PRP" or (tokens[start].norm in morph.OBJECT_PRONOUNS and not possessive)


def noun_phrase_end(tokens: list[Token], start: int, tags: list[str]) -> int:
    """Where the noun phrase starting at tokens[start] ends, read from its tags: determiners, then modifiers
    and nouns, with genitives carrying it on ("the old man next door", "the man's story")."""
    if lone_pronoun_object(tokens, start, tags):
        return start + 1
    i, n = start, len(tokens)
    while i < n and tags[i] in NP_DETERMINER_TAGS:
        i += 1
    while i < n:
        before_modifier = i + 1 < n and tags[i + 1] in NP_MODIFIER_TAGS
        if tags[i] in NP_MODIFIER_TAGS or (tags[i] == "POS" and i > start):
            i += 1
        elif tags[i] in {"RB", "VBG", "VBN"} and before_modifier:
            i += 1   # "a very old man", "a running joke"
        else:
            break
    return i


def _finite(tokens: list[Token], i: int, tags: list[str]) -> bool:
    return tags[i] in FINITE_TAGS or tokens[i].norm in AUXILIARIES


SUBJECT_PRONOUNS = frozenset({"i", "you", "he", "she", "we", "they"})
NOMINATIVE_ONLY = SUBJECT_PRONOUNS - morph.OBJECT_PRONOUNS    # "i", "he", "she", "we", "they"
ACCUSATIVE_ONLY = morph.OBJECT_PRONOUNS - SUBJECT_PRONOUNS - {"it"}   # "me", "him", "her", "us", "them"


def _agrees(tokens: list[Token], subject: int, verb: int, tags: list[str]) -> bool:
    """False when the word at tokens[subject] plainly cannot be the subject of the finite verb at tokens[verb]
    ("you was", "it were", "the people is"); True whenever it could. A singular noun may take a plural verb
    ("the police were", "the team are"), so only a pronoun or a plural noun is reliable evidence."""
    singular_verb = tags[verb] == "VBZ" or tokens[verb].norm == "was"
    plural_verb = tags[verb] == "VBP" or tokens[verb].norm == "were"
    word = tokens[subject].norm
    plural = tags[subject] in {"NNS", "NNPS"} or word in {"we", "they", "you"}
    return not (plural and singular_verb or word in {"he", "she", "it"} and plural_verb)


class RelativeReach(NamedTuple):
    end: int
    maybe_main: int | None = None   # a finite verb read as its complement's that could as well be the main clause's


def _complement_subject(tokens: list[Token], subject: int, end: int, tags: list[str]) -> bool | None:
    """Whether the phrase tokens[subject:end] is the subject of the finite verb at tokens[end] in a relative
    clause's complement ("who said [he] was lying"), rather than the relative verb's object with the main
    clause's verb following ("who told [us] was honest"). None when either holds: "who said the man was lying"
    and "who told the police was lying" differ only in the relative verb's own grammar."""
    if end != subject + 1 or not lone_pronoun_object(tokens, subject, tags):
        return None
    word = tokens[subject].norm
    if word in NOMINATIVE_ONLY:
        return True
    if word in ACCUSATIVE_ONLY:
        return False
    return None if _agrees(tokens, subject, end, tags) else False   # "who told you was lying"


def _past_relative(tokens: list[Token], j: int, tags: list[str]) -> RelativeReach | None:
    """Past a relative clause opening at tokens[j], with its subject, verb group and object ("who called",
    "that he told", "he told", and a result clause such as "that he spent all his money"); None when it has
    no verb of its own, so it is not one."""
    n = len(tokens)
    if tokens[j].norm in RELATIVES | FREE_RELATIVES:
        j += 1
    if j < n and not _finite(tokens, j, tags) and (tags[j] == "PRP" or tags[j] in NP_DETERMINER_TAGS | NP_MODIFIER_TAGS):
        j = noun_phrase_end(tokens, j, tags)
    if j >= n or not _finite(tokens, j, tags):
        return None
    j = _past_verb_group(tokens, j + 1, tags)
    if j >= n or not (tags[j] == "PRP" or tags[j] in NP_DETERMINER_TAGS | NP_MODIFIER_TAGS):
        return RelativeReach(j)
    subject, j = j, noun_phrase_end(tokens, j, tags)
    nominal = tags[j - 1] in pos.NOUNS | pos.NAMES or lone_pronoun_object(tokens, subject, tags)
    if j >= n or not _finite(tokens, j, tags) or not nominal:
        return RelativeReach(j)
    role = _complement_subject(tokens, subject, j, tags)
    if role is False:
        return RelativeReach(j)
    verb = j
    # its complement clause ("who said [he was lying]"), not the main clause's verb
    j = _past_verb_group(tokens, j + 1, tags)
    if j < n and (tags[j] == "PRP" or tags[j] in NP_DETERMINER_TAGS | NP_MODIFIER_TAGS):
        j = noun_phrase_end(tokens, j, tags)
    return RelativeReach(j, verb if role is None else None)


def _past_verb_group(tokens: list[Token], j: int, tags: list[str]) -> int:
    """Past the non-finite rest of a verb group ("who has [called]"), short of any finite verb."""
    while j < len(tokens) and tags[j] in {"VB", "VBN", "VBG", "RB", "RBR", "RBS"} and not _finite(tokens, j, tags):
        j += 1
    return j


class ClauseVerb(NamedTuple):
    at: int
    settled: bool   # False: it may instead end a relative clause's complement ("who told the police [was] lying")


def _unsettled(maybe_main: int | None) -> ClauseVerb | None:
    return None if maybe_main is None else ClauseVerb(maybe_main, False)


def _clause_verb_after(tokens: list[Token], end: int, tags: list[str]) -> ClauseVerb | None:
    """The finite verb a noun phrase is the subject of, past its post-modifiers ("the man [in the car] is",
    "the people [here] are", "the man [who called] was", "the story [he told] was"); None when the clause
    moves on without one ("believe a liar even when he ...", "believe a liar who tells lies"). A relative
    clause's complement that could be read either way leaves the verb unsettled, unless a later verb is the
    main clause's under both readings ("the woman who said the man was lying [is] honest") or the phrase
    cannot be its subject ("the people who say it [is] safe")."""
    j, n = end, len(tokens)
    maybe_main = None
    while j < n and not tokens[j].is_punct and tokens[j].norm not in SUBORDINATORS | {"and", "or", "but"}:
        if _finite(tokens, j, tags):
            return ClauseVerb(j, True)
        if tags[j] in {"RB", "RBR", "RBS"} or tokens[j].norm in {"here", "there"}:
            j += 1
        elif tokens[j].norm in RELATIVES | SUBJECT_PRONOUNS:
            after = _past_relative(tokens, j, tags)
            if after is None:
                break
            j = after.end
            if maybe_main is None and after.maybe_main is not None and _agrees(tokens, end - 1, after.maybe_main, tags):
                maybe_main = after.maybe_main
        elif tags[j] == "IN" and j + 1 < n and noun_phrase_end(tokens, j + 1, tags) > j + 1:
            j = noun_phrase_end(tokens, j + 1, tags)
        else:
            break
    return _unsettled(maybe_main)


VERBAL_FOLLOWERS = frozenset({"DT", "PDT", "PRP", "PRP$", "CD", "RB", "RBR", "RBS", "IN", "TO"})
# counts the tagger may read as adjectives ("walking [ten] miles"): they open a noun phrase like a determiner
QUANTITY_WORDS = frozenset({"two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
                            "twelve", "twenty", "thirty", "forty", "fifty", "hundred", "hundreds", "thousand",
                            "thousands", "dozen", "dozens", "few", "several", "many"})


def _opens_gerund(tokens: list[Token], start: int, tags: list[str]) -> bool:
    """A VBG heading its own verbal phrase ("walking [ten miles]", "driving [all night]", "spending [a
    fortune]"), not a participle modifying a noun ("working mums", "running water")."""
    after = start + 1
    return tags[start] == "VBG" and (after >= len(tokens) or tokens[after].is_punct or tags[after] in VERBAL_FOLLOWERS
                                     or tokens[after].norm in QUANTITY_WORDS)


class ObjectReading(NamedTuple):
    end: int
    settled: bool   # False: the words could as well be a clause's subject, so neither reading is safe


def _gerund_object(tokens: list[Token], start: int, tags: list[str]) -> ObjectReading | None:
    """A gerund object read as context ("think nothing of walking ten miles"): the verb, its non-finite rest
    and one object. Unsettled when a bare noun follows ("eating apples": a gerund or a noun phrase)."""
    if tags[start] != "VBG":
        return None
    end = _past_verb_group(tokens, start + 1, tags)
    if end < len(tokens) and (tags[end] == "PRP" or tags[end] in NP_DETERMINER_TAGS | NP_MODIFIER_TAGS):
        end = noun_phrase_end(tokens, end, tags)
    return ObjectReading(end, _opens_gerund(tokens, start, tags))


def context_object(tokens: list[Token], start: int, tags: list[str], kind: str = "np") -> ObjectReading | None:
    """The object a pattern reads as context: a gerund for kind "ing", else a nominal. See _gerund_object."""
    if kind == "ing":
        return _gerund_object(tokens, start, tags)
    if kind != "np":
        raise ValueError(f"unknown context object kind {kind!r}")
    if _opens_gerund(tokens, start, tags):
        return None   # a gerund heading its own phrase is a clause, not a nominal object
    return _nominal_object(tokens, start, tags)


def _nominal_object(tokens: list[Token], start: int, tags: list[str]) -> ObjectReading | None:
    """A nominal object read as context ("believe a liar even when ...", "believe the old man next door
    completely", "believe what he says"). None when the words are not one: not nominal ("believe so", "believe in"), the subject of a
    complement clause ("believe he is lying", "believe the man in the car is lying"), of an infinitive
    ("believed him to be honest" is supposing, not taking his word) or of a coordinated clause ("believe
    you and he were friends"). Unsettled when a run of nouns meets a verb: "the stories people tell" is an
    object with a relative clause, "the bus driver lied" a clause, and the tags cannot tell them apart."""
    if tokens[start].norm in FREE_RELATIVES:
        reach = _past_relative(tokens, start, tags)
        if reach is None:
            return None
        verb = _clause_verb_after(tokens, reach.end, tags) or _unsettled(reach.maybe_main)
        if verb is None or not verb.settled:
            return ObjectReading(reach.end, verb is None)
        return None
    pronoun = lone_pronoun_object(tokens, start, tags)
    end = noun_phrase_end(tokens, start, tags)
    if end == start:
        return None
    if not pronoun and not noun_argument(phrase_token(tokens[start:end]), tokens, tags, unanchored_object=True):
        return None
    following = tokens[end].norm if end < len(tokens) else ""
    if following == "to" and end + 1 < len(tokens) and tags[end + 1] == "VB":
        return None
    if pronoun and tokens[start].norm in {"you", "it"} and following in {"and", "or"} \
            and end + 1 < len(tokens) and tokens[end + 1].norm in {"i", "he", "she", "we", "they"}:
        return None
    verb = _clause_verb_after(tokens, end, tags)
    if verb is None or not verb.settled:
        return ObjectReading(end, verb is None)
    run = tags[start:end]
    nouns = next((i for i, tag in enumerate(reversed(run)) if tag not in pos.NOUNS | pos.NAMES), len(run))
    if verb.at != end or nouns < 2 or all(tag in pos.NAMES for tag in run[-nouns:]):
        return None   # a clause, its subject a name ("John Smith lied") or plainly ended
    # after a preposition ("think highly of the stories people tell") the phrase cannot be a clause's subject
    return ObjectReading(end, start > 0 and tags[start - 1] in {"IN", "TO"})


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
    if unanchored_object and words and (morph.singular_of(words[-1]) or words[-1]) in AMOUNT_HEADS \
            and all(tag in AMOUNT_MODIFIERS for tag in phrase[:-1]):
        return False
    if head != "VBG" and unanchored_object and _temporal_tail(words, phrase, tokens[end:]):
        return False
    return True



def argument_complete(tokens: list[Token], end: int, tags: list[str] | None, complete: bool = True) -> bool:
    """A terminal object must not stop inside a name, possessive noun phrase or coordinated argument."""
    if end == len(tokens):
        return complete
    nominal = pos.NOUNS | pos.NAMES | {"PRP", "PRP$", "WP", "DT", "CD", "JJ", "JJR", "JJS", "POS", "VBG", "VBN"}
    i = end
    if INLINE_CHAR.match(tokens[i].text):
        return False
    if tokens[i].norm in TIME_ADVERBS:
        return True
    coordinated = tokens[i].text == ","
    if coordinated:
        i += 1
    for words in (("as", "well", "as"), ("and",), ("or",), ("'n",)):
        if tuple(t.norm for t in tokens[i:i + len(words)]) == words:
            i += len(words)
            coordinated = True
            break
    if coordinated:
        while i < len(tokens) and tags is not None and tags[i] in {"RB", "RBR", "RBS"}:
            i += 1
        if i == len(tokens) or tokens[i].is_punct:
            return False
        if tags is not None and tags[i] in {"VB", "VBD", "VBP", "VBZ", "MD"}:
            return True
        # A fresh subject followed by a finite verb starts another clause, rather than another object.
        if i + 1 < len(tokens) and tags is not None and tags[i] in nominal and tags[i + 1] in {"VBD", "VBP", "VBZ", "MD"}:
            return True
        return tags is not None and tags[i] not in nominal
    if tokens[i].norm == "of":
        return False
    if tokens[i].is_punct:
        return tokens[i].text not in {"'", "’", "-", "—", "–", "(", "[", "{", "/"}
    return tags is not None and tags[i] not in nominal

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
