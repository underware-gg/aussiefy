"""Parse and concept-detection stages.

Stage 1 (parse) is a frame checker. It decides whether a matched span sits in
a grammatical position its frame allows. For example, a predicate adjective
needs a linking verb before it, and an interjection must stand at the start of
a clause. It also collects the subject and verb the span hangs off, so
clause-level idioms can bind {subj}.

Stage 2 (detect) maps spans to concepts. It tries trigger patterns first (the
concept vocabulary's triggers and every entry's `replaces`). It then falls back
to similarity against those same paraphrases for predicate positions the
triggers missed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Callable, NamedTuple

from . import morph, pos
from .context import TIME_ADVERBS, argument_complete, following_context, noun_argument, verb_subject
from .embed import Embedder, NgramEmbedder, similarity_scorer
from .matcher import match_at, SLOT_MATCHERS, Match, Pattern, PatternIndex, is_name
from .schema import Concept
from .degree import QUALIFIER_WORDS
from .text import CLAUSE_BREAK, QUOTES, SENTENCE_END, Token


def applicable_concepts(concepts: tuple[str, ...], rules: dict[str, Concept] | None,
                        tokens: list[Token], end: int, complete: bool = True,
                        noun_use: str = "reference") -> tuple[str, ...]:
    """Meaning restrictions apply equally to exact triggers, direct entries and similarity matches."""
    if rules is None:
        return concepts
    following = following_context(tokens, end, complete)
    return tuple(cid for cid in concepts
                 if rules[cid].noun_use in {"any", noun_use}
                 and (not rules[cid].unless_after
                      or following.known and following.word not in rules[cid].unless_after))

DETERMINERS = {"a", "an", "the", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these",
               "those", "some", "any", "no", "every", "each"}
NOT_NOUNS = {"at", "of", "to", "for", "with", "in", "on", "and", "or", "but", "as", "than", "the", "a", "an",
             "enough", "about", "by", "from", "that", "if", "when", "so", "too"}
# adverbs that make a past participle an adjective: "long established", "well known"
PARTICIPLE_ADVERBS = {"long", "well", "newly", "firmly", "recently", "once", "so-called", "ill", "badly"}
CLAUSE_VERBS = {"am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
                "did", "will", "would", "can", "could", "shall", "should", "may", "might", "must", "to", "not",
                "keep", "keeps", "kept", "start", "started", "stop", "stopped", "go", "went", "come", "came",
                "i", "you", "he", "she", "it", "we", "they", "who", "that", "which"}
VOCATIVES = {"mate", "mates", "everyone", "everybody", "all", "guys", "folks", "there", "team", "love",
             "darling", "sir", "mum", "dad", "buddy", "pal"}
CLAUSE_OPENERS = {"and", "but", "so", "oh", "well", "because", "then", "or", "please", "just", "now"}


@dataclass
class Detection:
    start: int                     # token index in sentence (inclusive), core span
    end: int                       # exclusive
    concepts: tuple[str, ...]
    frame: str
    intensity: int
    method: str                    # "trigger" | "entry" | "embedding"
    pattern: str
    entry_id: str | None = None
    score: float = 1.0
    captures: dict[str, Token] = field(default_factory=dict)
    inflection: str = ""
    clause_start: int | None = None  # token index where a clause idiom would start
    question: bool = False           # subject/verb inverted ("are you crazy")
    direct: set[str] = field(default_factory=set)  # entries whose own `replaces` matched here
    subject_noun: Token | None = None  # a predicate's subject when it's a plain noun ("the tank" may be drained)
    person_only: bool = False          # the trigger is said only of people ("full", "drained": not of a tank)
    result_clause: bool = False      # "so X (that) ..." - only single-word swaps keep the grammar
    tense: str = "present"           # narrative tense of the sentence, for slots with no verb of their own
    noun_use: str = "reference"
    coordinated: bool = False        # shares its verb with another predicate ("tired and hungry")
    semantic_degree: dict[str, str] = field(default_factory=dict)
    degree_concepts: frozenset[str] = frozenset()
    degree_conflicts: frozenset[str] = frozenset()
    degree_qualifier: tuple[str, ...] = ()

    def describe_captures(self) -> dict[str, str]:
        return {k: v.text for k, v in self.captures.items()}



SPEECH_SENSE = {"SCREAM", "CRY"}
# concept ids the grammar rules here name; the loader checks they exist
CODE_CONCEPTS = SPEECH_SENSE | {"VERY"}


def _speech_tag(tokens: list[Token], start: int, end: int) -> bool:
    before = tokens[max(0, start - 3):start]
    after = tokens[end] if end < len(tokens) else None
    quote_before = any(t.text in QUOTES for t in before)
    name_after = after is not None and after.text[:1].isupper() and after.is_word
    return quote_before or name_after


# a linking verb's subject stops at one of these: "everyone at university is lazy", "everyone near home is"
SUBJECT_STOPS = {"at", "in", "on", "of", "with", "from", "near", "by", "for", "about", "under", "over", "behind",
                 "around", "across", "inside", "outside", "into", "through", "between", "like"}
# what may stand between a subject and its verb: modals, "to", "not", "never"
VERB_LEADERS = {"may", "might", "can", "could", "will", "would", "shall", "should", "must", "to", "not", "never"}


# auxiliaries and raising verbs a linking verb's subject reaches back past
VERB_CHAIN = (morph.BE_FORMS | morph.HAVE_FORMS | morph.DO_FORMS
              | {"n't", "going", "gonna", "got", "seem", "seems", "seemed", "appear", "appears", "appeared",
                 "feel", "feels", "felt", "get", "gets", "getting", "become", "becomes", "became"})
CLAUSE_JOINS = {"and", "or", "but", "so", "then", "yet", "nor"}


def _noun_before(tokens: list[Token], verb: Token) -> Token | None:
    """The word a linking verb's subject ends on, past modals and hedges ("the tank may be drained"): a plain
    lower-case word or a pronoun; None for a name or when the subject reaches back past a preposition."""
    k = verb.i - tokens[0].i - 1
    # back past modals, hedges and the verb chain: "you [are not going to] get rich", "everybody [seemed to] be"
    while k >= 0 and (tokens[k].norm in VERB_LEADERS or tokens[k].norm in morph.HEDGES or tokens[k].norm in VERB_CHAIN):
        k -= 1
    if k < 0 or not tokens[k].is_word or tokens[k].norm in CLAUSE_JOINS:
        return None   # "... and was comfortably asleep": the subject is the clause before's
    if tokens[k].norm in morph.PRONOUNS or tokens[k].norm in morph.PERSON_INDEFINITES:
        return tokens[k]   # past a modal the subject slot misses it: "this should be done in any case"
    if tokens[k].text[:1].isupper():
        return None        # a name, or a sentence's first word: can't tell
    if k >= 1 and tokens[k - 1].norm in SUBJECT_STOPS:
        return None   # "everyone at university is lazy": the subject is earlier than its last word
    return tokens[k]


def _capital(tokens: list[Token], k: int) -> bool:
    return 0 <= k < len(tokens) and tokens[k].is_word and tokens[k].text[:1].isupper()


def _in_a_name(tokens: list[Token], start: int, end: int) -> bool:
    """The span holds a word of a multi-word name: a capital that isn't the sentence's (or a quote's) first
    word, next to another capitalised word ("the United Nations", "Boston University"). A name on its own
    can still be swapped ("a merry Christmas")."""
    from .text import capital_is_positional

    for k in range(start, end):
        if _capital(tokens, k) and not capital_is_positional(tokens, k) and (_capital(tokens, k - 1)
                                                                             or _capital(tokens, k + 1)):
            if k > 0 and tokens[k - 1].norm in DETERMINERS and capital_is_positional(tokens, k - 1) and not _capital(tokens, k + 1):
                continue
            return True
    return False


def _possessed(tokens: list[Token], det: "Detection") -> bool:
    """A noun with a possessive 's after it ("a children's game"): the article belongs to what follows, and
    the swap's number and 's can't be made to agree."""
    nxt = tokens[det.end] if det.end < len(tokens) else None
    return det.frame == "np" and nxt is not None and nxt.norm == "'s" and nxt.start == tokens[det.end - 1].end \
        and tokens[det.end - 1].norm.endswith(("ren", "men", "people"))


def narrative_tense(tokens: list[Token], start: int, end: int) -> str:
    """Past if the rest of the sentence is told in the past ("..., assented to the proposal")."""
    for t in tokens[:start] + tokens[end:]:
        if morph.is_past(t.norm):
            return "past"
    return "present"


def at_clause_start(tokens: list[Token], i: int) -> bool:
    j = i - 1
    while j >= 0 and tokens[j].norm in CLAUSE_OPENERS:
        j -= 1
    return j < 0 or tokens[j].text in CLAUSE_BREAK or tokens[j].text in SENTENCE_END


def at_clause_end(tokens: list[Token], i: int, conjunctions: bool = False) -> bool:
    if i >= len(tokens) or tokens[i].text in CLAUSE_BREAK or tokens[i].text in SENTENCE_END:
        return True
    return conjunctions and tokens[i].norm in ("and", "but", "or", "so", "then", "please")


class PredicateLead(NamedTuple):
    start: int
    boost: int
    before: int
    negated: bool


def predicate_lead(tokens: list[Token], start: int, reviewed_degree: bool = False) -> PredicateLead:
    j, absorbed, boost = start - 1, start, 0
    while j >= 0:
        two = f"{tokens[j - 1].norm} {tokens[j].norm}" if j >= 1 else ''
        if two in morph.INTENSIFIERS:
            boost += morph.INTENSIFIERS[two]
            absorbed, j = j - 1, j - 2
        elif tokens[j].norm in morph.INTENSIFIERS:
            boost += morph.INTENSIFIERS[tokens[j].norm]
            absorbed, j = j, j - 1
        elif reviewed_degree and tokens[j].norm in QUALIFIER_WORDS:
            absorbed, j = j, j - 1
        elif tokens[j].norm in {'not', 'never', 'hardly'}:
            return PredicateLead(absorbed, boost, j, True)
        elif tokens[j].norm in morph.HEDGES:
            j -= 1
        else:
            break
    return PredicateLead(absorbed, boost, j, False)


def owned_degree_modifiers(tokens: list[Token], matches: list[Match]) -> set[int]:
    return {i for match in matches if match.pattern.frame in {'adj', 'predicate_adj'}
            for i in range(predicate_lead(tokens, match.start, reviewed_degree=True).start, match.start)}


def degree_modifier_spans(text: str, index: PatternIndex) -> list[tuple[int, int]]:
    from .text import tokenize
    tokens = tokenize(text)
    return [(tokens[i].start, tokens[i].end) for i in sorted(owned_degree_modifiers(tokens, index.find(tokens)))]


def interjection_recipient(tokens: list[Token], end: int) -> tuple[int, int] | None:
    start = end + int(end < len(tokens) and tokens[end].text == ',')
    if start < len(tokens) and (tokens[start].norm in VOCATIVES or is_name(tokens[start])):
        if at_clause_end(tokens, start + 1):
            return start, start + 1
    return None


def imperative_start(tokens: list[Token], i: int, tags: list[str]) -> bool:
    if i >= len(tokens):
        return False
    if tags[i] == 'VB':
        return True
    return (tokens[i].norm in {'do', 'have'} and tags[i] == 'VBP' and i + 1 < len(tokens)
            and tokens[i + 1].norm not in (set(morph.PRONOUNS) | morph.PERSON_INDEFINITES))


def finite_verb(token: Token, tag: str) -> bool:
    """A finite tag corroborated by morphology, rather than an ambiguous bare command form."""
    word = token.norm
    if tag == 'MD':
        return word in VERB_LEADERS
    if tag == 'VBD':
        return morph.is_past(word) and word not in morph.IRREGULAR
    if tag == 'VBZ':
        return word in {'is', 'has', 'does'} or (word.endswith('s') and not word.endswith(('ss', 'us', 'is'))
                                                and word not in pos.IMPERATIVES)
    return False


def noun_usage(tokens: list[Token], start: int, end: int, tags: list[str],
               address_starts: set[int]) -> str:
    """Read the role of the enclosing noun phrase; partial or ambiguous recipients stay uncommitted."""
    left, right = start, end
    modifiers = {'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS', 'DT', 'PRP$'}
    while left > 0 and tags[left - 1] in modifiers:
        left -= 1
    while right < len(tokens) and tags[right] in {'RB', 'RBR', 'RBS'}:
        right += 1
    qualified = (left, right) != (start, end)
    if left in address_starts:
        return 'address' if not qualified and at_clause_end(tokens, right) else 'unknown'
    if any(origin < left and all(tokens[i].is_word and tokens[i].norm not in morph.PRONOUNS
                                 for i in range(origin, left)) for origin in address_starts):
        return 'unknown'  # a tagger guess must not certify an unparsed recipient as a governed object
    before_comma = left > 0 and tokens[left - 1].text == ','
    after_comma = right < len(tokens) and tokens[right].text == ','
    initial = at_clause_start(tokens, left)
    if after_comma and initial:
        if any(t.text == ',' for t in tokens[right + 1:]):
            return 'unknown'  # a balanced detached phrase may be parenthetical rather than a command
        j = right + 1
        if j < len(tokens) and tokens[j].norm == 'please':
            j += 1
        if imperative_start(tokens, j, tags):
            return 'unknown' if qualified else 'address'
    if before_comma and at_clause_end(tokens, right):
        j = int(tokens[0].norm == 'please')
        if j < left - 1 and imperative_start(tokens, j, tags):
            return 'unknown' if qualified else 'address'
        return 'unknown'
    if right < len(tokens) and finite_verb(tokens[right], tags[right]):
        return 'reference'
    if left > 0:
        governor = left - 1
        if tags[governor] in {'IN', 'TO'} or finite_verb(tokens[governor], tags[governor]):
            return 'reference'
        if tags[governor] in {'VB', 'VBP'} and verb_subject(tokens, governor, tags) is not None:
            return 'reference'
    return 'unknown'


class PredicateContext(NamedTuple):
    """What lies left of a predicate: "she's [really] [tired]", "are you [crazy]"."""
    start: int                  # where the span starts once intensifiers before it are absorbed
    boost: int                  # the intensity those intensifiers add
    subj: Token | None
    verb: Token                 # the linking verb (borrowed from the first predicate when coordinated)
    clause_start: int | None    # where a clause idiom could start (the subject), or None
    question: bool              # inverted: "are you crazy"


def predicate_context(tokens: list[Token], start: int, reviewed_degree: bool = False) -> PredicateContext | None:
    """The context of a predicate starting at tokens[start], or None when the span isn't in predicate position."""
    absorbed, boost, j, negated = predicate_lead(tokens, start, reviewed_degree)
    if negated:
        return None
    if j < 0:
        return None
    if tokens[j].norm in ("and", "or", ",", "but") and j >= 2:
        # coordinated predicate ("you're stupid and all talk"): borrow the earlier verb
        k = j - 1
        while k >= 0 and k > j - 8 and tokens[k].text not in SENTENCE_END and tokens[k].norm not in morph.LINKING_VERBS:
            k -= 1
        if k >= 0 and tokens[k].norm in morph.LINKING_VERBS and k < j - 1:
            verb = tokens[k]
            subj = tokens[k - 1] if k >= 1 and SLOT_MATCHERS["subj"](tokens[k - 1]) else None
            return PredicateContext(absorbed, boost, subj, verb, None, False)
        return None
    if tokens[j].norm in morph.LINKING_VERBS:
        verb = tokens[j]
        k = j - 1
        subj = tokens[k] if k >= 0 and SLOT_MATCHERS["subj"](tokens[k]) else None
        governed = k > 0 and tokens[k - 1].norm in VERB_LEADERS | VERB_CHAIN
        return PredicateContext(absorbed, boost, subj, verb, k if subj and not governed else None, False)
    if SLOT_MATCHERS["subj"](tokens[j]) and j >= 1 and tokens[j - 1].norm in morph.BE_FORMS:
        return PredicateContext(absorbed, boost, tokens[j], tokens[j - 1], j - 1, True)
    return None


def check_frame(m: Match, tokens: list[Token], adjective_nouns: dict[str, frozenset[str]] | None = None,
                tags: list[str] | None = None, *, complete: bool = True,
                degree_concepts: frozenset[str] | None = None) -> Detection | None:
    p: Pattern = m.pattern
    det = Detection(m.start, m.end, p.concepts, p.frame, p.intensity,
                    "entry" if p.entry_id else "trigger", p.text, p.entry_id,
                    captures=dict(m.captures), inflection=m.inflection)
    if p.entry_id:
        det.direct.add(p.entry_id)
    det.person_only = p.person_only
    det.semantic_degree = dict(p.semantic_degree)
    det.degree_concepts = frozenset(p.semantic_degree) if degree_concepts is None else degree_concepts
    det.tense = narrative_tense(tokens, m.start, m.end)
    first, last = tokens[m.start], tokens[m.end - 1]
    if (m.start > 0 and tokens[m.start - 1].text == "-" and tokens[m.start - 1].end == first.start) or \
            (m.end < len(tokens) and tokens[m.end].text == "-" and tokens[m.end].start == last.end):
        return None   # part of a hyphenated word: "good-bye", "battle-field"
    terminal_argument = any(capture.end == last.end for slot, capture in m.captures.items()
                            if slot in {"obj", "objposs", "np"})
    if terminal_argument and not p.guard and not argument_complete(tokens, m.end, tags, complete):
        return None
    if "np" in m.captures and tags is not None:
        parts = [element for element in p.elements if element.kind != "not"]
        unanchored = (len(parts) == 2 and parts[0].role == "head_verb"
                      and parts[1].kind == "slot" and parts[1].slot == "np")
        if not noun_argument(m.captures["np"], tokens, tags, unanchored_object=unanchored):
            return None
    if p.frame == "vp":
        subject = verb_subject(tokens, m.start, tags)
        if subject is not None:
            if subject.norm in morph.PERSON_PRONOUNS:
                det.captures.setdefault("agent", subject)
            else:
                det.subject_noun = subject
    if p.frame == "clause" and m.start > 0 and tokens[m.start - 1].norm in VERB_LEADERS | VERB_CHAIN:
        return None  # An outer auxiliary must not be stranded before an independently finite clause.
    if p.clause_end:
        end = m.end
        while end < len(tokens) and tags is not None and tags[end] in {"RB", "RBR", "RBS"}:
            end += 1
        if not at_clause_end(tokens, end, conjunctions=True):
            return None
    if p.frame == "np" and m.end - m.start > 1 and first.norm in morph.POSSESSIVES:
        det.captures.setdefault("poss", first)   # "his wife": the possessive a "{poss} missus" keeps
    noun_limits = (adjective_nouns or {}).get(first.norm)
    next_is_noun = m.end < len(tokens) and (tags is not None and tags[m.end] in pos.NOUNS) \
        and tokens[m.end].norm not in TIME_ADVERBS
    if p.frame == "predicate_adj" and noun_limits is not None and next_is_noun:
        return None  # an attributive adjective must pass its noun-sense rule, even after a linking verb
    if p.frame == "predicate_adj":
        ctx = predicate_context(tokens, m.start, reviewed_degree=bool(det.degree_concepts))
        if ctx is None:
            return None
        absorbed, boost, subj, verb, clause_start, question = ctx
        det.start = absorbed
        if det.degree_concepts:
            det.degree_qualifier = tuple(t.norm for t in tokens[absorbed:m.start])
            det.start = m.start
        det.intensity = max(1, min(5, det.intensity + boost))
        degree = {t.norm for t in tokens[absorbed:m.start]}
        if degree & {"so", "too", "such"} and m.end < len(tokens) and tokens[m.end].is_word \
                and tokens[m.end].norm not in ("and", "but", "or", "today", "now", "lately", "again"):
            det.result_clause = True  # "so stingy he never pays": the idiom would strand the clause
            det.start = m.start       # keep "so" in place: "he's so tight-arsed he never pays"
        if subj is not None:
            det.captures.setdefault("subj", subj)
        else:
            det.subject_noun = _noun_before(tokens, verb)
            subject = verb_subject(tokens, verb.i - tokens[0].i, tags)
            if subject is not None and subject.norm in morph.PERSON_PRONOUNS:
                det.captures.setdefault("agent", subject)
        det.captures.setdefault("be", verb)
        det.clause_start = clause_start
        det.question = question
    elif p.frame in ("interjection",):
        recipient = interjection_recipient(tokens, m.end)
        end = recipient[1] if recipient is not None else m.end
        if not (at_clause_start(tokens, m.start) and at_clause_end(tokens, end)):
            return None
    elif p.frame == "imperative":
        if not (at_clause_start(tokens, m.start) and at_clause_end(tokens, m.end, conjunctions=True)):
            return None
    elif p.frame == "vp" and set(p.concepts) & SPEECH_SENSE and _speech_tag(tokens, m.start, m.end):
        return None  # '"Help!" she screams' / 'cried Baby Bear': saying, not screaming or crying
    elif p.frame == "vp" and m.inflection in ("ing", "pp", "past") and m.end - m.start == 1 \
            and _participle_adjective(tokens, m.start):
        return None   # "each separate dying ember", "governments long established": an adjective, not the verb
    elif p.frame == "vp" and m.inflection == "3sg" and m.end - m.start == 1:  # a multi-word phrase ("thinks the world of him") is no noun
        # "animal screams and suicides": a plural noun, not a verb, unless something can be its subject
        prev = tokens[m.start - 1] if m.start > 0 else None
        nxt = tokens[m.end] if m.end < len(tokens) else None
        ends_list = nxt is None or nxt.is_punct or nxt.norm in ("and", "or", "'n", "n")
        has_subject = prev is not None and (SLOT_MATCHERS["subj"](prev) or prev.norm in ("who", "which", "that"))
        if ends_list and not has_subject:
            return None
    elif p.frame == "clause":
        if "subj" in m.captures and "be" in m.captures:
            det.question = m.captures["be"].i < m.captures["subj"].i
        elif "be" in m.captures:
            det.question = m.captures["be"].i == tokens[m.start].i  # "is it impossible?"
        det.clause_start = m.start
    elif p.frame == "adv" and "VERY" in p.concepts:
        nxt = tokens[m.end] if m.end < len(tokens) else None
        if nxt is None or nxt.is_punct or nxt.norm in DETERMINERS:
            return None  # "absolutely a great game": intensifies a noun phrase, so "dead a ..." won't do
        if m.start > 0 and tokens[m.start - 1].norm in DETERMINERS:
            return None  # "the very things": the same things, not extremely
    elif p.frame == "adj":
        # an adjective swap needs a noun after it ("a ripper game") or a linking verb before it
        # ("it was ripper"); "for good." and "good at maths" are left alone
        nxt = tokens[m.end] if m.end < len(tokens) else None
        if m.start > 0 and tokens[m.start].text[:1].isupper():
            return None  # part of a name ("New York", "Great Britain")
        attributive = nxt is not None and nxt.is_word and nxt.norm not in NOT_NOUNS
        if not attributive and predicate_context(tokens, m.start) is None:
            return None
        if attributive and noun_limits is not None and nxt.norm not in noun_limits:
            return None  # "a great forest", "a great dearth": size, not quality
        if det.degree_concepts:
            lead = predicate_lead(tokens, m.start, reviewed_degree=True)
            det.degree_qualifier = tuple(t.norm for t in tokens[lead.start:m.start])
    elif p.frame == "np":
        # a bare noun swap shouldn't split a compound we can't see ("sausage roll")
        if p.elements[-1].role == "head_noun" and m.end < len(tokens) and tokens[m.end].norm in COMPOUND_HEADS:
            return None
        if (m.end < len(tokens) and tokens[m.end].text == "-") or (m.start > 0 and tokens[m.start - 1].text == "-"):
            return None  # part of a hyphenated compound ("battle-field")
        first, nxt = tokens[m.start], tokens[m.end] if m.end < len(tokens) else None
        if (m.start > 0 and first.text[:1].isupper() and nxt is not None and nxt.text[:1].isupper()
                and nxt.is_word):
            return None  # inside a multi-word name ("Father Bear", "Mother Teresa")
        if m.start > 0 and tokens[m.start - 1].norm in ("oh", "aw", "ah"):
            return None  # "oh man" is an exclamation, not a noun
        if m.start > 0 and tokens[m.start - 1].norm in ("i", "we", "they", "he", "she", "to"):
            return None  # "I kid you not", "to chat": a verb, not a noun
    return det


def _participle_adjective(tokens: list[Token], i: int) -> bool:
    """A one-word verb match in -ing or past-participle form that is working as an adjective: after a
    determiner ("the dying man"), after "long"/"well" ("long established"), or between a modifier and a noun
    ("each separate dying ember")."""
    prev = tokens[i - 1] if i > 0 else None
    nxt = tokens[i + 1] if i + 1 < len(tokens) else None
    if prev is None or not prev.is_word:
        return False
    if prev.norm in DETERMINERS or prev.norm in PARTICIPLE_ADVERBS:
        return True
    noun_next = nxt is not None and nxt.is_word and nxt.norm not in NOT_NOUNS and not nxt.norm.endswith("ly") \
        and nxt.norm not in DETERMINERS and nxt.norm not in CLAUSE_VERBS
    return noun_next and prev.norm not in CLAUSE_VERBS and not prev.text[:1].isupper()


COMPOUND_HEADS = {"roll", "rolls", "dog", "dogs", "sizzle", "time", "party"}


# tags that make the next word a noun: "a taste", "more taste", "his taste", "two tastes"; and prepositions
# ("of thought", "after a struggle"), but not "than", "if" or "like", which a verb can follow
NOUN_CONTEXT = frozenset({"DT", "PRP$", "JJ", "JJR", "JJS", "CD", "POS"})
NOUN_PREPOSITIONS = frozenset("""of in on at for with by from about after before into onto over under without between
through during against among across around behind beyond within upon""".split())
# what a finite verb's subject can be tagged: "the script loads", "that hands", "it loads"
SUBJECT_TAGS = frozenset({"NN", "NNS", "NNP", "NNPS", "PRP", "WDT"})
NOT_AFTER_A_VERB = frozenset({"CD", ".", ",", ":", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD"})


def _wrong_part_of_speech(m: Match, tokens: list[Token], tags: list[str]) -> bool:
    """A trigger matched a word in another part of speech: a verb idiom on a noun ("a taste of it", "more
    taste than") or a noun term on a verb ("that kids meself"). The tagger slips on rare words ("stop
    complaining" as a noun, "long endure"), so a verb trigger is refused only where the word before makes it a
    noun, and a noun trigger never after a determiner. (Refusing a noun before a noun, "food colouring", was
    tried: it lost "choccy bickies" and "the nan's bed"; the dictionary's triggers carry those exclusions.)"""
    if m.pattern.before_modifier:   # "really ^adj": "really cold", "really fast", not "really think"
        nxt = tags[m.end] if m.end < len(tags) else "."
        if not nxt.startswith(("JJ", "RB", "VBN")):
            return True
    elements = m.pattern.elements
    if m.pattern.frame == "vp" and elements[0].role == "head_verb":
        before = m.start - 1
        noun_context = before >= 0 and (tags[before] in NOUN_CONTEXT or tokens[before].norm in NOUN_PREPOSITIONS)
        return tags[m.start] in pos.NOUNS and noun_context
    if m.pattern.frame == "np" and any(e.role == "head_noun" for e in elements):
        head = m.end - 1
        if tags[head] not in pos.VERBS - {"VBG", "VBN"}:
            return False
        # a finite verb only with its subject before it and an object or a preposition after ("the script
        # loads the file"): the tagger also calls plurals and vocatives verbs ("Add eggs one at a time",
        # "Alright, guys")
        k = head - 1
        if k >= 0 and tags[k] == "RB":
            k -= 1
        subject = k >= 0 and tags[k] in SUBJECT_TAGS and tokens[k].norm not in ("me", "you")
        after = tags[head + 1] if head + 1 < len(tags) else "."
        return subject and after not in NOT_AFTER_A_VERB
    return False


FALLBACK_LENGTH_TOLERANCE = 2


def _fallback_literal(pattern: Pattern) -> str:
    return " ".join(sorted(e.values)[0] for e in pattern.elements if e.kind == "lit")


def fallback_scorer(embedder: Embedder, patterns: list[Pattern]) -> Callable[[str], dict[int, float]]:
    """Score mandatory, slot-free fallback patterns that can pass the detector's shape checks.

    N-grams already use a sparse inverted index. Meaning models avoid dense vector comparisons against
    patterns whose literal count or length the detector would reject afterwards.
    """
    if isinstance(embedder, NgramEmbedder):
        return similarity_scorer(embedder, [p.text for p in patterns])
    by_shape: dict[tuple[int, int], list[int]] = {}
    for i, pattern in enumerate(patterns):
        shape = (sum(e.kind == "lit" for e in pattern.elements), len(_fallback_literal(pattern)))
        by_shape.setdefault(shape, []).append(i)

    def score(query: str) -> dict[int, float]:
        words = len(query.split())
        indices = sorted(i for length in range(len(query) - FALLBACK_LENGTH_TOLERANCE,
                                               len(query) + FALLBACK_LENGTH_TOLERANCE + 1)
                         for i in by_shape.get((words, length), ()))
        return {i: embedder.similarity(query, patterns[i].text) for i in indices}

    return score


def detect(tokens: list[Token], index: PatternIndex, scorer: Callable[[str], dict[int, float]] | None = None,
           fallback_patterns: list[Pattern] | None = None, threshold: float = 0.72,
           tags: list[str] | None = None, adjective_nouns: dict[str, frozenset[str]] | None = None,
           concepts: dict[str, Concept] | None = None, complete: bool = True,
           degree_index: PatternIndex | None = None) -> list[Detection]:
    """Every concept the triggers find in the sentence, frame-checked. With a scorer (embed.similarity_scorer over
    the fallback patterns' texts), a predicate after a linking verb that no trigger matched is compared with
    the fallback patterns by similarity ("he was exhaustedd")."""
    found: list[Detection] = []
    tags = tags if tags is not None else pos.tag([t.text for t in tokens])
    matches = index.find(tokens)
    address_starts = {m.end + int(m.end < len(tokens) and tokens[m.end].text == ',')
                      for m in matches if m.pattern.frame == 'interjection'
                      and at_clause_start(tokens, m.start) and concepts is not None
                      and any(concepts[cid].takes_addressee for cid in m.pattern.concepts)}
    degree_matches = [m for m in matches if m.pattern.semantic_degree] if degree_index is None else degree_index.find(tokens)
    owned = owned_degree_modifiers(tokens, degree_matches)
    evidence: dict[tuple[int, int, str, str], set[str]] = {}
    families: set[tuple[int, int, str, str]] = set()
    for match in degree_matches:
        if check_frame(match, tokens, adjective_nouns, tags, complete=complete,
                       degree_concepts=frozenset(match.pattern.concepts)) is None:
            continue
        families.update((match.start, match.end, cid, match.pattern.frame) for cid in match.pattern.concepts)
        for cid, band in match.pattern.semantic_degree.items():
            evidence.setdefault((match.start, match.end, cid, match.pattern.frame), set()).add(band)
    for m in matches:
        if set(range(m.start, m.end)) & owned and not m.pattern.semantic_degree:
            continue
        bands = {}
        source_families = frozenset()
        if families:
            frames = {'adj', 'predicate_adj'} if m.pattern.frame in {'adj', 'predicate_adj'} else {m.pattern.frame}
            bands = {cid: set().union(*(evidence.get((m.start, m.end, cid, frame), set()) for frame in frames))
                     for cid in m.pattern.concepts}
            bands = {cid: values for cid, values in bands.items() if values}
            source_families = frozenset(cid for cid in m.pattern.concepts
                                        if any((m.start, m.end, cid, frame) in families for frame in frames))
        if bands:
            m = replace(m, pattern=replace(m.pattern, semantic_degree={cid: sorted(values)[0]
                                                                      for cid, values in bands.items()}))
        det = check_frame(m, tokens, adjective_nouns, tags, complete=complete, degree_concepts=source_families)
        if det and not det.degree_concepts and set(range(det.start, det.end)) & owned:
            continue
        if det:
            det.degree_conflicts = frozenset(cid for cid, values in bands.items() if len(values) > 1)
            if det.frame == "np":
                det.noun_use = noun_usage(tokens, det.start, det.end, tags, address_starts)
            det.concepts = applicable_concepts(det.concepts, concepts, tokens, det.end, complete, det.noun_use)
        if det and not _in_a_name(tokens, det.start, det.end) and not _possessed(tokens, det) \
                and det.concepts and not _wrong_part_of_speech(m, tokens, tags):
            found.append(det)

    if scorer and fallback_patterns:
        graded = {cid for p in degree_index.patterns for cid in p.concepts} if degree_index is not None else set()
        covered = {i for d in found for i in range(d.start, d.end)}
        for i, tok in enumerate(tokens):
            if tok.norm not in morph.LINKING_VERBS or i + 1 >= len(tokens):
                continue
            j = i + 1
            while j < len(tokens) and (tokens[j].norm in morph.INTENSIFIERS or tokens[j].norm in morph.HEDGES):
                j += 1
            if j < len(tokens) and tokens[j].norm in DETERMINERS:
                continue  # "was a great game" is a noun phrase, not a misspelt predicate
            best: tuple[float, int, Pattern] | None = None
            for n in (1, 2, 3):
                span = tokens[j:j + n]
                if len(span) < n or any(t.is_punct for t in span) or any(t.i - tokens[0].i in covered for t in span):
                    break
                text = " ".join(t.norm for t in span)
                if len(text) < 4:
                    continue
                scores = scorer(text)
                for k in sorted(k for k, score in scores.items() if score >= threshold):   # pattern order breaks ties
                    # a misspelling has its trigger's shape: as many words ("working" is not "not working",
                    # "under the" is not "under the weather") and about its length ("less" is not "legless")
                    p = fallback_patterns[k]
                    if p.semantic_degree or graded.intersection(p.concepts):
                        continue  # similarity is not exact evidence of a reviewed degree
                    matched = match_at(p, tokens, j, exact=False)
                    literal = _fallback_literal(p)
                    if (matched is None or matched.end != j + n
                            or not applicable_concepts(p.concepts, concepts, tokens, j + n, complete)
                            or abs(len(literal) - len(text)) > FALLBACK_LENGTH_TOLERANCE):
                        continue
                    if best is None or scores[k] > best[0]:
                        best = (scores[k], n, fallback_patterns[k])
            if best:
                score, n, p = best
                m = Match(p, j, j + n)
                det = check_frame(m, tokens, adjective_nouns, tags, complete=complete)
                if det:
                    det.concepts = applicable_concepts(det.concepts, concepts, tokens, det.end, complete)
                    det.method = "embedding"
                    det.score = round(score, 3)
                    found.append(det)
    return found


def resolve_overlaps(dets: list[Detection]) -> list[Detection]:
    """Keep the longest, most specific non-overlapping detections."""
    method_rank = {"entry": 0, "trigger": 1, "embedding": 2}
    ordered = sorted(dets, key=lambda d: (-(d.end - d.start), method_rank[d.method], -d.score, d.start, d.pattern))
    taken: set[int] = set()
    kept: list[Detection] = []
    for d in ordered:
        span = set(range(d.start, d.end))
        if span & taken:
            continue
        taken |= span
        kept.append(d)
    # Merge concept sets of identical spans so selection sees every reading.
    for d in kept:
        extra = [o for o in dets if o is not d and (o.start, o.end, o.frame) == (d.start, d.end, d.frame)]
        for o in extra:
            d.concepts = tuple(dict.fromkeys(d.concepts + o.concepts))
            d.direct |= o.direct
            conflicts = set(d.degree_conflicts) | set(o.degree_conflicts)
            for cid, band in o.semantic_degree.items():
                if cid in d.semantic_degree and d.semantic_degree[cid] != band:
                    conflicts.add(cid)
                else:
                    d.semantic_degree[cid] = band
            d.degree_conflicts = frozenset(conflicts)
            d.degree_concepts |= o.degree_concepts
    mark_coordination(kept)
    return sorted(kept, key=lambda d: d.start)


def mark_coordination(dets: list[Detection]) -> None:
    """Predicates sharing one linking verb ("he was ugly and drunk") are coordinated: a clause idiom would orphan
    the second, and stacking a synonym onto a list reads as a pile-up."""
    shared = Counter(d.captures["be"].i for d in dets if d.frame == "predicate_adj" and "be" in d.captures)
    for d in dets:
        if d.frame == "predicate_adj" and "be" in d.captures and shared[d.captures["be"].i] > 1:
            d.clause_start = None
            d.coordinated = True


NP_BREAKS = {"of", "to", "with", "in", "on", "at", "by", "for", "from", "and", "or", "but", "that", "who", "which"}


GENITIVES = {"'s", "\u2019s", "'", "\u2019"}   # a name's genitive determines the noun after it


def opening_determiner(sent: list[Token], start: int, reach: int = 4) -> str | None:
    """The determiner (or genitive) that opens the phrase this span ends, before the span: "the" of "the two old
    [statesmen]", "a" of "a [bloke]", "walker's" of "Walker's [wife]"; None if there is none."""
    for i in range(start - 1, max(-1, start - 1 - reach), -1):
        tok = sent[i]
        if tok.norm in DETERMINERS or tok.norm in GENITIVES:
            return tok.norm
        if not tok.is_word or tok.norm in NP_BREAKS:
            return None
    return None


def after_determiner(sent: list[Token], start: int, reach: int = 4) -> bool:
    """A determiner opens the phrase this span ends: "the two old [statesmen]", "a [bloke]", "Walker's [wife]"."""
    return opening_determiner(sent, start, reach) is not None
