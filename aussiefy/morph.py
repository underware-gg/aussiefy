"""Small morphology layer: pronoun cases, verb agreement and inflection.

Enough grammar to realise idiom slots ({subj} {have} ... {poss}) and to inflect
the head verb of a verb-phrase idiom to match what it replaces.
"""

from __future__ import annotations

import re

# subject -> (person, number, object, possessive)
PRONOUNS = {
    "i": (1, "sg", "me", "my"),
    "you": (2, "pl", "you", "your"),   # agrees like a plural ("you are", "you have")
    "he": (3, "sg", "him", "his"),
    "she": (3, "sg", "her", "her"),
    "it": (3, "sg", "it", "its"),
    "we": (1, "pl", "us", "our"),
    "they": (3, "pl", "them", "their"),
    "that": (3, "sg", "that", "its"),
    "this": (3, "sg", "this", "its"),
    "who": (3, "sg", "who", "whose"),
}
PERSON_PRONOUNS = {"i", "you", "he", "she", "we", "they"}
# words that stand for people without naming them ("everybody seemed delighted")
PERSON_INDEFINITES = {"everybody", "everyone", "somebody", "someone", "anybody", "anyone", "nobody", "no-one"}
OBJECT_PRONOUNS = {"me", "you", "him", "her", "it", "us", "them"}
POSSESSIVES = {"my", "your", "his", "her", "its", "our", "their"}
BE_FORMS = {"am", "is", "are", "was", "were", "be", "been", "being"}
HAVE_FORMS = {"have", "has", "had"}
DO_FORMS = {"do", "does", "did"}
LINKING_VERBS = {
    "am", "is", "are", "was", "were", "be", "been", "being",
    "seem", "seems", "seemed", "look", "looks", "looked", "feel", "feels", "felt",
    "sound", "sounds", "sounded", "get", "gets", "got", "getting", "become", "becomes", "became",
    "sit", "sits", "sat", "stand", "stands", "stood", "stay", "stays", "stayed", "remain", "remains", "remained",
}
INTENSIFIERS = {
    "very": 1, "really": 1, "so": 1, "pretty": 0, "quite": 0, "rather": 0, "too": 1,
    "altogether": 1, "simply": 1, "extremely": 2, "incredibly": 2, "super": 1, "totally": 2, "completely": 2, "utterly": 2,
    "absolutely": 2, "seriously": 1, "terribly": 2, "awfully": 2, "insanely": 2, "ridiculously": 2,
    "a bit": -1, "slightly": -1, "kind of": -1, "sort of": -1, "just": 0, "a little": -1,
}
HEDGES = {"just", "still", "always", "also", "probably", "definitely", "all", "being", "getting"}


def subject_features(subj: str) -> tuple[int, str]:
    """(person, number) for a subject word; names and nouns are 3rd singular."""
    info = PRONOUNS.get(subj.lower())
    return (info[0], info[1]) if info else (3, "sg")


def possessive_of(subj: str) -> str:
    info = PRONOUNS.get(subj.lower())
    return info[3] if info else "their"


def possessive_of_object(obj: str) -> str:
    """"her" -> "her", "him" -> "his", a name -> "Mary's": whose thing it is, from the object."""
    for _, _, o, p in PRONOUNS.values():
        if obj.lower() == o:
            return p
    return obj + ("'" if obj.endswith("s") else "'s")


def object_of(subj: str) -> str:
    info = PRONOUNS.get(subj.lower())
    return info[2] if info else "them"


def tense_of(verb_norm: str) -> str:
    return "past" if verb_norm in ("was", "were", "had", "did") or verb_norm.endswith("ed") else "present"


def agree(lemma: str, subj: str, tense: str = "present") -> str:
    person, number = subject_features(subj)
    if lemma == "be":
        if tense == "past":
            return "was" if number == "sg" and person in (1, 3) else "were"
        if person == 1 and number == "sg":
            return "am"
        return "is" if (person == 3 and number == "sg") else "are"
    if tense == "past":
        return inflect(lemma, "past")
    if person == 3 and number == "sg":
        return inflect(lemma, "3sg")
    return lemma


IRREGULAR = {
    # base: (3sg, past, past participle, -ing)
    "be": ("is", "was", "been", "being"),
    "have": ("has", "had", "had", "having"),
    "do": ("does", "did", "done", "doing"),
    "go": ("goes", "went", "gone", "going"),
    "get": ("gets", "got", "got", "getting"),
    "make": ("makes", "made", "made", "making"),
    "take": ("takes", "took", "taken", "taking"),
    "give": ("gives", "gave", "given", "giving"),
    "lose": ("loses", "lost", "lost", "losing"),
    "throw": ("throws", "threw", "thrown", "throwing"),
    "spit": ("spits", "spat", "spat", "spitting"),
    "come": ("comes", "came", "come", "coming"),
    "run": ("runs", "ran", "run", "running"),
    "win": ("wins", "won", "won", "winning"),
    "sit": ("sits", "sat", "sat", "sitting"),
    "swim": ("swims", "swam", "swum", "swimming"),
    "begin": ("begins", "began", "begun", "beginning"),
    "spin": ("spins", "spun", "spun", "spinning"),
    "sting": ("stings", "stung", "stung", "stinging"),
    "dig": ("digs", "dug", "dug", "digging"),
    "let": ("lets", "let", "let", "letting"),
    "tell": ("tells", "told", "told", "telling"),
    "eat": ("eats", "ate", "eaten", "eating"),
    "drink": ("drinks", "drank", "drunk", "drinking"),
    "know": ("knows", "knew", "known", "knowing"),
    "think": ("thinks", "thought", "thought", "thinking"),
    "bring": ("brings", "brought", "brought", "bringing"),
    "build": ("builds", "built", "built", "building"),
    "break": ("breaks", "broke", "broken", "breaking"),
    "bid": ("bids", "bade", "bidden", "bidding"),
    "weep": ("weeps", "wept", "wept", "weeping"),
    "bust": ("busts", "busted", "busted", "busting"),
    "scream": ("screams", "screamed", "screamed", "screaming"),
    "smash": ("smashes", "smashed", "smashed", "smashing"),
    "rock": ("rocks", "rocked", "rocked", "rocking"),
    "swear": ("swears", "swore", "sworn", "swearing"),
    "say": ("says", "said", "said", "saying"),
    "pay": ("pays", "paid", "paid", "paying"),
    "lie": ("lies", "lied", "lied", "lying"),
    "put": ("puts", "put", "put", "putting"),
    "cut": ("cuts", "cut", "cut", "cutting"),
    "set": ("sets", "set", "set", "setting"),
    "hit": ("hits", "hit", "hit", "hitting"),
    "fall": ("falls", "fell", "fallen", "falling"),
    "leave": ("leaves", "left", "left", "leaving"),
    "feel": ("feels", "felt", "felt", "feeling"),
    "keep": ("keeps", "kept", "kept", "keeping"),
    "sleep": ("sleeps", "slept", "slept", "sleeping"),
    "chuck": ("chucks", "chucked", "chucked", "chucking"),
    "whinge": ("whinges", "whinged", "whinged", "whingeing"),
    "bludge": ("bludges", "bludged", "bludged", "bludging"),
    "see": ("sees", "saw", "seen", "seeing"),
    "tear": ("tears", "tore", "torn", "tearing"),
    "shoot": ("shoots", "shot", "shot", "shooting"),
    "pull": ("pulls", "pulled", "pulled", "pulling"),
    "hang": ("hangs", "hung", "hung", "hanging"),
    "show": ("shows", "showed", "shown", "showing"),
    "wake": ("wakes", "woke", "woken", "waking"),
    "shut": ("shuts", "shut", "shut", "shutting"),
    "stop": ("stops", "stopped", "stopped", "stopping"),
    "dob": ("dobs", "dobbed", "dobbed", "dobbing"),
    "drop": ("drops", "dropped", "dropped", "dropping"),
    "chat": ("chats", "chatted", "chatted", "chatting"),
    "nap": ("naps", "napped", "napped", "napping"),
    "plan": ("plans", "planned", "planned", "planning"),
    "stand": ("stands", "stood", "stood", "standing"),
    "buy": ("buys", "bought", "bought", "buying"),
    "sell": ("sells", "sold", "sold", "selling"),
    "find": ("finds", "found", "found", "finding"),
    "hold": ("holds", "held", "held", "holding"),
    "catch": ("catches", "caught", "caught", "catching"),
    "write": ("writes", "wrote", "written", "writing"),
    "drive": ("drives", "drove", "driven", "driving"),
    "speak": ("speaks", "spoke", "spoken", "speaking"),
    "wear": ("wears", "wore", "worn", "wearing"),
    "hear": ("hears", "heard", "heard", "hearing"),
    "send": ("sends", "sent", "sent", "sending"),
    "spend": ("spends", "spent", "spent", "spending"),
    "teach": ("teaches", "taught", "taught", "teaching"),
    "grow": ("grows", "grew", "grown", "growing"),
    "fly": ("flies", "flew", "flown", "flying"),
    "ride": ("rides", "rode", "ridden", "riding"),
    "fight": ("fights", "fought", "fought", "fighting"),
    "forget": ("forgets", "forgot", "forgotten", "forgetting"),
    "meet": ("meets", "met", "met", "meeting"),
}

# simple past forms: the irregular table's, plus common ones it doesn't conjugate
PAST_IRREGULAR = frozenset({v[1] for v in IRREGULAR.values()} | {
    "were", "went", "came", "ran", "gave", "took", "made", "said", "told", "got", "left", "sat", "ate", "drank",
    "fell", "broke", "threw", "sold", "bought", "forgot", "shut", "put", "let", "did", "saw", "found", "thought",
    "knew", "began", "brought", "stood", "woke"})


def is_past(word: str) -> bool:
    """A simple past verb form: irregular ("went"), or regular -ed ("consented"; not "need" or "indeed")."""
    w = word.lower()
    return w in PAST_IRREGULAR or (len(w) > 4 and w.endswith("ed") and w not in ("need", "indeed"))
VERB_FORMS = ("base", "3sg", "past", "pp", "ing")


def _doubles(lemma: str) -> bool:
    """A one-syllable verb ending consonant-vowel-consonant doubles it: lob -> lobbed, chat -> chatting."""
    return bool(re.fullmatch(r"[^aeiou]*[aeiou][bdgklmnprt]", lemma))


def inflect(lemma: str, form: str) -> str:
    if form == "base":
        return lemma
    if lemma in IRREGULAR:
        return IRREGULAR[lemma][VERB_FORMS.index(form) - 1]
    if form == "3sg":
        if lemma.endswith(("s", "sh", "ch", "x", "z", "o")):
            return lemma + "es"
        if lemma.endswith("y") and lemma[-2:-1] not in "aeiou":
            return lemma[:-1] + "ies"
        return lemma + "s"
    if form in ("past", "pp"):
        if lemma.endswith("e"):
            return lemma + "d"
        if lemma.endswith("y") and lemma[-2:-1] not in "aeiou":
            return lemma[:-1] + "ied"
        if _doubles(lemma):
            return lemma + lemma[-1] + "ed"
        return lemma + "ed"
    if form == "ing":
        if lemma.endswith("ie"):
            return lemma[:-2] + "ying"
        if lemma.endswith("e") and not lemma.endswith(("ee", "ye", "oe")):
            return lemma[:-1] + "ing"
        if _doubles(lemma):
            return lemma + lemma[-1] + "ing"
        return lemma + "ing"
    raise ValueError(form)


def verb_forms(lemma: str) -> dict[str, str]:
    """surface -> form name, for matching an inflected head verb."""
    out: dict[str, str] = {}
    for form in VERB_FORMS:
        out.setdefault(inflect(lemma, form), form)
    return out


IRREGULAR_PLURALS = {"man": "men", "woman": "women", "child": "children", "person": "people",
                     "foot": "feet", "tooth": "teeth", "mouse": "mice", "fella": "fellas"}


NOT_MAN_COMPOUNDS = {"human", "german", "roman", "shaman", "talisman", "caiman", "ottoman", "walkman"}


# words that end like plurals and aren't ("the news is", "a means to an end")
NOT_PLURAL = frozenset("""news means series species lens thanks physics maths politics economics kudos always
whereabouts ethics athletics gymnastics measles mumps crossroads headquarters christmas chaos atlas canvas bias
does lazybones shambles mcdonalds""".split())


SINGULARS = {p: s for s, p in IRREGULAR_PLURALS.items()}


def singular_of(word: str) -> str | None:
    """The singular a plural noun is the plural of ("horses" -> "horse", "ponies" -> "pony", "men" -> "man"),
    or None when the word doesn't read as a plural."""
    w = word.lower()
    if w in NOT_PLURAL or w.endswith(("ss", "us", "is", "'s", "\u2019s", "'", "\u2019")):
        return None   # "Buckley's" is a genitive, not a plural
    if w in SINGULARS:
        return SINGULARS[w]
    if w.endswith("ies"):
        cand = w[:-3] + "y"
    elif w.endswith("es") and w[:-2].endswith(("ss", "sh", "ch", "x", "z")):
        cand = w[:-2]   # "boxes" -> "box", not "boxe"; "horses" -> "horse"
    elif w.endswith("s"):
        cand = w[:-1]
    else:
        return None
    return cand if len(cand) >= 3 and pluralise(cand) == w else None


def pluralise(noun: str) -> str:
    """"a gutless wonder" -> "gutless wonders", "a swagman" -> "swagmen"."""
    words = noun.split()
    if len(words) > 1 and words[0].lower() in ("a", "an"):
        noun = " ".join(words[1:])
    last = noun.split()[-1]
    if last.lower().endswith("man") and len(last) > 4 and last.lower() not in NOT_MAN_COMPOUNDS:
        return noun[: len(noun) - 2] + "en"
    head = noun[: len(noun) - len(last)]
    if last.lower() in IRREGULAR_PLURALS:
        return head + IRREGULAR_PLURALS[last.lower()]
    if last.endswith(("s", "sh", "ch", "x", "z")):
        return head + last + "es"
    if last.endswith("y") and last[-2:-1] not in "aeiou":
        return head + last[:-1] + "ies"
    return head + last + "s"
