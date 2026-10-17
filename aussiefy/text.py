"""Tokenising, sentence splitting and casing helpers, and the shape patterns the genre reader and the engine
share (DATELINE, SCRIPT_LINE).

Tokens keep character offsets into the original text so substitutions can be
spliced back without disturbing anything we did not touch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .protected import BLOCK_RUN, INLINE_CHARS, INLINE_RUN

INLINE_CHAR = re.compile(f"[{INLINE_CHARS}]")   # a masked inline span's placeholder

# a news dateline, "PARIS (AP) —", "MAMMOTH HOT SPRINGS, Wyo. –", "WASHINGTON, Dec. 27.—", "DETROIT, Dec. 13
# (AP).—": the place in capitals, then a state and a date if any, then a dash after a space, stop or bracket
# (not "COVID-19")
DATELINE = re.compile(r"^[A-Z][A-Z .,'-]{2,40}(?:,\s*[A-Z][a-z]{1,4}\.?)?(?:,?\s*[A-Z][a-z]{2,4}\.?\s*\d{1,2})?\.?"
                      r"\s*(?:\([A-Z]{2,4}\)\.?)?\s*(?<=[\s.)])[-—–]", re.M)
# a capitalised word mid-sentence, read as a name: genre counts them, the engine keeps a command they name lower
MID_SENTENCE_NAME = re.compile(r"(?<=[a-z,;] )[A-Z][a-z]+")
# a script's speaker label, or a "NOTE:" or "PS:" at the start of a line
SCRIPT_LINE = re.compile(r"^\s*[A-Z][A-Z .']{1,30}:", re.M)

APOSTROPHES = "'’‘"
_WORD = r"[A-Za-z0-9]+(?:[" + APOSTROPHES + r"][A-Za-z]+)*"
# a number with its own punctuation is one token: a fraction, a decimal, a time ("1/4", "4.5", "10:30")
_NUMBER = r"\d+(?:[/.:]\d+)+(?:[ap]m\b)?(?![A-Za-z0-9])"
# a masked span (markup.mask) is one token: an inline one sits in its sentence like an unswappable word; a
# block one gives no token at all and ends the sentence
TOKEN_RE = re.compile(f"(?P<block>{BLOCK_RUN})|{INLINE_RUN}|{_NUMBER}|{_WORD}|[^\\sA-Za-z0-9]")

# Contraction suffix -> normalised form. "'s" is resolved by context in _norm_s.
# the words "n't" attaches to (with "ai" for "ain't" and "sha" for "shan't"); after any other ("warn't") it's
# dialect, kept whole, so "war" isn't found inside "warn't"
NOT_STEMS = {"do", "does", "did", "is", "are", "was", "were", "has", "have", "had", "could", "would", "should",
             "might", "must", "need", "ought", "dare", "may", "ai", "sha"}
CONTRACTIONS = {
    "n't": "not", "'re": "are", "'m": "am", "'ve": "have", "'ll": "will", "'d": "would", "'s": "'s",
}
SUBJECT_PRONOUNS = {"i", "you", "he", "she", "it", "we", "they", "that", "this", "there", "who"}
CLAUSE_BREAK = {",", ";", ":", "—", "-", "(", ")", '"'}
SENTENCE_END = {".", "!", "?"}
PARAGRAPH_BREAK = re.compile(r"\n[^\S\n]*\n")   # a blank line, "\r\n" endings too
LEAD_IN = {",", ":", ";", "—", "-"}


@dataclass
class Token:
    text: str
    start: int
    end: int
    norm: str          # lowercased, contractions expanded ("'re" -> "are")
    sent: int = 0      # sentence index
    i: int = 0         # index in token list

    @property
    def is_word(self) -> bool:
        return self.text[0].isalnum() or self.text[0] in APOSTROPHES

    @property
    def is_punct(self) -> bool:
        return not self.is_word


def _split_contraction(text: str, start: int) -> list[tuple[str, int]]:
    unified = text
    for ch in "’‘":
        unified = unified.replace(ch, "'")
    low = unified.lower()
    if low.endswith("n't") and len(low) > 3:
        stem = len(text) - 3
        if low in ("can't",):
            return [(text[:2], start), (text[2:], start + 2)]  # ca + n't, Penn style
        if low == "won't":
            return [(text[:2], start), (text[2:], start + 2)]
        if low[:-3] not in NOT_STEMS:
            return [(text, start)]
        return [(text[:stem], start), (text[stem:], start + stem)]
    for suf in ("'re", "'m", "'ve", "'ll", "'d", "'s"):
        if low.endswith(suf) and len(low) > len(suf):
            cut = len(text) - len(suf)
            return [(text[:cut], start), (text[cut:], start + cut)]
    return [(text, start)]


def _base_norm(text: str) -> str:
    low = text.lower()
    for ch in "’‘":
        low = low.replace(ch, "'")
    if low in CONTRACTIONS:
        return CONTRACTIONS[low]
    if low == "ca":
        return "can"
    if low == "wo":
        return "will"
    return low


# "Mr. Bennet" is one sentence: the full stop after these, before a capital, doesn't end it
HONORIFICS = {"mr", "mrs", "ms", "messrs", "dr", "prof", "rev", "st", "mt", "capt", "col", "gen", "lt", "sgt",
              "jr", "sr"}
# nor after these ("Dec. 13", "No. 5", "vs. Cleveland"), nor after a single letter ("U.S. Food", "Lorie K. Logan",
# "10 a.m."), nor before a lower-case word ("10 a.m. on Monday")
ABBREVIATIONS = HONORIFICS | {"jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
                              "no", "nos", "vs", "approx", "dept", "gov", "sen", "rep", "ave", "inc", "ltd", "corp",
                              "fig", "vol", "pp", "est", "ft", "oz", "lb", "lbs"}


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    breaks: set[int] = set()        # tokens that start a sentence whatever comes before them
    for m in TOKEN_RE.finditer(text):
        if m.group("block"):
            breaks.add(len(tokens))
            continue
        for piece, start in _split_contraction(m.group(), m.start()):
            tokens.append(Token(piece, start, start + len(piece), _base_norm(piece)))
    sent = 0
    for i, tok in enumerate(tokens):
        tok.i = i
        if i and tokens[i - 1].sent == sent and (i in breaks or _paragraph_ends(text, tokens[i - 1], tok)):
            sent += 1
        tok.sent = sent
        # 's after a pronoun is "is" (or "has" before "got"/"been"); otherwise possessive
        if tok.norm == "'s":
            prev = tokens[i - 1].norm if i else ""
            nxt = tokens[i + 1].norm if i + 1 < len(tokens) else ""
            if prev in SUBJECT_PRONOUNS or prev in ("what", "where", "how", "here"):
                tok.norm = "has" if nxt in ("got", "been") else "is"
        nxt_tok = tokens[i + 1] if i + 1 < len(tokens) else None
        prev_tok = tokens[i - 1] if i else None
        honorific = (tok.text == "." and prev_tok is not None and prev_tok.end == tok.start and nxt_tok is not None
                     and ((prev_tok.norm in ABBREVIATIONS and (nxt_tok.text[:1].isupper() or nxt_tok.text[:1].isdigit()))
                          or (len(prev_tok.text) == 1 and prev_tok.text.isalpha())
                          or nxt_tok.text[:1].islower()))
        if tok.text in SENTENCE_END and not honorific and (nxt_tok is None or (nxt_tok.text not in SENTENCE_END
                                                                               and nxt_tok.start > tok.end)):
            sent += 1   # "4.1" and "?!" don't split; ". " does
    return tokens


UNENDED_RE = re.compile(r"[^\s.!?,;:\"'\u201d\u2019)\]]\s*$")   # a line not ending as a sentence does


def heading_lines(text: str) -> list[tuple[int, int]]:
    """Lines that read as headings in plain text ("Food Safety Tips"): short, not ending as a sentence does, and
    standing alone: the text's first line or after a blank one, and before a blank line or mostly Title Case,
    with more text after it (one unpunctuated line, "I reckon we should go", is a message, not a heading).
    A line inside a wrapped paragraph or a stanza follows another line, so it's prose ("...my old friend\n
    Margaret Thompson at her farm")."""
    out, pos = [], 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        words = line.split()
        alone_before = i == 0 or not lines[i - 1].strip()
        alone_after = i + 1 == len(lines) or not lines[i + 1].strip()
        title = sum(w[:1].isupper() for w in words) >= max(2, len(words) / 2)
        prose_after = any(ln.strip() for ln in lines[i + 1:])   # a one-line message isn't a heading
        if 0 < len(words) <= 10 and UNENDED_RE.search(line) and alone_before and (alone_after or title) \
                and prose_after:
            out.append((pos, pos + len(line)))
        pos += len(line) + 1
    return out


def _paragraph_ends(text: str, last: Token, nxt: Token) -> bool:
    """A blank line between two tokens ends a sentence, whatever the punctuation (a heading, a list's lead), unless
    the sentence carries on over it: a lead-in ("said to his wife,\n\n\"What will become of us?\""), but not a
    salutation ("Dear John,\n\nI hope ..."), or a stanza's sentence going on in lower case."""
    if not PARAGRAPH_BREAK.search(text, last.end, nxt.start):
        return False
    if nxt.text[:1].islower():
        return False
    if last.text in LEAD_IN:
        line = text[text.rfind("\n", 0, last.start) + 1:last.end]
        return len(line.split()) <= 4   # "Dear John," is a line of its own
    return True


# quoted speech or a quoted document: straight or curly, double or single. A straight double
# quote after a digit is an inch mark ('a 6" pipe'); an apostrophe inside a word ("don't", "the faucet's") never
# opens or closes a single quote
QUOTED_RE = re.compile(
    r'(?<!\d)"[^"]*"'
    "|“[^”]*”"
    # a straight single quote: not the drawl's own marks ("'cause", "'em", "'n" don't open one; "pursuin'" doesn't
    # close one)
    r"|(?<![\w'])'(?!(?:cause|cos|em|n|til|tis|twas|round|bout|ere|ow|e|im|er)\b)(?=\S)(?:\w'\w|[^'\n])*?"
    r"(?<=\S)(?<!in)'(?!\w)"
    "|(?<!\\w)‘(?:\\w’\\w|[^’\\n])*?’(?!\\w)")
# a word mentioned, not used: "the word 'guys'", "a term like “cookie”", "what Americans call it, a 'faucet'". A
# bare "called" is shouting ('She called "Help!"'): naming needs an object ("call it", "called me") or "so-called"
_CUE = (r"\b(?:(?:the|a|this|that)\s+)?(?:words?|terms?|phrases?|expressions?|nicknames?|slogans?|spelling)"
        r"(?:\s+(?:like|such as|as))?"
        r"|\bso-called"
        r"|\bcall(?:s|ed|ing)?\s+(?:it|them|this|that|him|her|me|us|you|one)(?:\s+(?:a|an|the))?")
MENTION_RE = re.compile(rf"(?:{_CUE})\s*([\"“‘']|(?<!\w)')"
                        r"((?:\w['’]\w|[^\"”’'\n]){1,40})"
                        r"(?:[\"”]|[’'](?!\w))", re.I)


def quoted_spans(text: str) -> list[tuple[int, int]]:
    """The spans of quoted speech and quoted documents, including their quote marks."""
    return [m.span() for m in QUOTED_RE.finditer(text)]


def document_spans(text: str, *, keep_quotes: bool = False, datelines: bool = False) -> list[tuple[int, int]]:
    """Literal document wording selected for preservation, including spelling."""
    return (quoted_spans(text) if keep_quotes else []) + ([m.span() for m in DATELINE.finditer(text)] if datelines else [])


# in a text that talks about words: a short quote ("“gals.”", "version of 'guys'"), and a list item's term before
# its colon ("- boys: too patronizing")
SHORT_QUOTE_RE = re.compile(r"(?<!\w)[\"“‘']((?:\w['’]\w|[^\"”’',!?\n]){1,30})[\"”’'](?!\w)")
LIST_TERM_RE = re.compile(r"^[^\S\n]*[-*+][^\S\n]+([^:\n]{1,30}):", re.M)
SPEECH_VERB = r"(?:said|says|asked|asks|cried|shouted|yelled|replied|answered|whispered|called|goes|went)"
SPOKEN_AFTER = re.compile(rf"\s*(?:\w+\s+)?{SPEECH_VERB}\b", re.I)
SPOKEN_REACH = 40   # SPOKEN_BEFORE is anchored at the quote: only the words just before it count
SPOKEN_BEFORE = re.compile(rf"\b{SPEECH_VERB}[,:]?\s*$", re.I)


def mentioned_spans(text: str) -> list[tuple[int, int]]:
    """The spans of words talked about rather than used, a few words in quotes after "the word", "a term",
    "called": the post about the word "guys" is about "guys", whatever the Aussie for it. Once a text talks
    about words, its list items' terms ("- boys: too patronizing") are mentions too, the candidates it weighs,
    and so are its short quotes that read as words, not speech: not next to a "said", and lower case ("“gals.”"),
    a single word ("“Guys” can be used"), or sharing a word with another mention ("“Guys and gals”"). "Run.",
    "I know." and "Good morning." stay speech."""
    cued = [m.span(2) for m in MENTION_RE.finditer(text) if len(m.group(2).split()) <= 4]
    if not cued:
        return cued
    more = [m.span(1) for m in LIST_TERM_RE.finditer(text) if len(m.group(1).split()) <= 3]
    named = {w.lower() for a, b in cued + more for w in re.findall(r"\w+", text[a:b])}
    for m in SHORT_QUOTE_RE.finditer(text):
        said, words = m.group(1), m.group(1).split()
        if (len(words) > 3 or SPOKEN_AFTER.match(text, m.end()) or SPOKEN_BEFORE.search(text, max(0, m.start() - SPOKEN_REACH), m.start())):
            continue
        if said[:1].islower() or len(words) == 1 and not said.endswith(".") or named & {
                w.lower() for w in re.findall(r"\w+", said)}:
            more.append(m.span(1))
    return sorted(set(cued + more))


def held_spans(text: str, keep_quotes: bool) -> list[tuple[int, int]]:
    """What the text holds as said: words mentioned rather than used, and in a genre that keeps quotes, the quoted
    speech and documents. No swap touches them (engine._Run.held), nor the drawl (engine._no_drawl); lint asks for no
    dialect swap in what the original held."""
    return mentioned_spans(text) + (quoted_spans(text) if keep_quotes else [])


def sentences(tokens: list[Token]) -> list[list[Token]]:
    out: dict[int, list[Token]] = {}
    for tok in tokens:
        out.setdefault(tok.sent, []).append(tok)
    return [out[k] for k in sorted(out)]


def match_case(replacement: str, original: str) -> str:
    """Carry the original span's capitalisation onto the replacement."""
    if not replacement or not original:
        return replacement
    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


# Words that are safe to lower-case when a garnish opener is put in front of them.
QUOTES = ('"', "\u201c", "\u201d")           # straight and curly double quotes
OPEN_QUOTES = ('"', "\u201c")


def _is_markup(tok: Token) -> bool:
    """Emphasis marks and masked inline markup, which a capital's position is judged through."""
    return tok.text in ("*", "_") or INLINE_CHAR.match(tok.text) is not None


def capital_is_positional(sent: list[Token], i: int) -> bool:
    """A capital at tokens[i] says where it is (a sentence's or a quote's start), not that it's a name. Markup
    in between doesn't count: after a bold label ("**Avoiding pitfalls:** Steering clear") the capital starts
    what follows, but "I met *Candy*" is a name. After a news dateline's dash ("WASHINGTON, Dec. 27.—") only a
    word that starts sentences or that a capital doesn't follow ("Effective immediately"): "Candy Smith said"
    is a name."""
    j = i - 1
    while j >= 0 and _is_markup(sent[j]):
        j -= 1
    prev = sent[j].text if j >= 0 else ""
    if j < 0 or prev in (*OPEN_QUOTES, "(", ":") or prev in ".!?":
        return True
    if prev in ("–", "—") and (j == 0 or _after_dateline(sent, j)):
        nxt = sent[i + 1].text if i + 1 < len(sent) else ""
        return sent[i].text.lower() in COMMON_STARTERS or not nxt[:1].isupper()
    return False


def _after_dateline(sent: list[Token], dash: int) -> bool:
    """Whether the dash at sent[dash] ends a news dateline ("MAMMOTH HOT SPRINGS, Wyo. –"): capitals and
    abbreviations only before it."""
    words = [(j, t) for j, t in enumerate(sent[:dash]) if t.is_word]
    return bool(words) and all(t.text.isupper() or j + 1 < dash and sent[j + 1].text == "." for j, t in words)


COMMON_STARTERS = set("""
a an the this that these those it its he she we they you your my our their his her
is are was were be been am do does did have has had will would can could should shall may might must
what why how when where who which there here so but and or if then well yes no not
just really very please get go come let let's give take make look tell keep stop don't
everyone everybody nobody someone something nothing all some any every
hello hi hey thanks thank sorry okay ok oh good great wow right sure maybe now then
once upon after before while since until though although because unless whether
at on in into onto by for from with without under over up down out off near across through behind
one two three four five six seven eight nine ten first second third last next many few several
little big small long short old new other another each both either neither such same
nobody somebody anybody everything anything someone anyone people
surely perhaps indeed suddenly eagerly presently soon thus hence besides meanwhile alas ah certainly clearly
obviously luckily sadly finally instead otherwise therefore however nevertheless later earlier today tonight
tomorrow yesterday distinctly slowly quietly only even still effective
yes yeah no not never always often sometimes still already soon later today tomorrow yesterday
here there where everywhere somewhere anyway however instead also too even only
said says say went came saw got had made took gave put ran sat stood fell woke looked
""".split())


# a sentence's first word, after any opening quote or bracket: the word an opener lowers
FIRST_WORD_RE = re.compile(r"([\"'(]*)([A-Za-z'\u2019]+)")
# a word as masks and the swear list read it: letters, with apostrophes inside or after ("fuckin'", "bastard's")
MASK_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\u2019]*")


def spoken_word(token: str) -> str:
    """A MASK_WORD_RE token as a word: without a closing quote mark after it, though a dropped g keeps its
    apostrophe ("fuckin'")."""
    bare = token.rstrip("'\u2019")
    return token if bare.lower().endswith("in") and bare != token else bare


def normalise_word(word: str) -> str:
    """A word in lower case with a straight apostrophe, as the swear list and mask words write it."""
    return word.lower().replace("\u2019", "'")


def lower_first_word(sentence_text: str, common: set[str] | None = None, force: bool = False) -> str:
    """Lower-case the first word if it is an ordinary word rather than a name or "I"."""
    m = FIRST_WORD_RE.match(sentence_text)
    if not m:
        return sentence_text
    word = m.group(2)
    base = re.split(r"['\u2019]", word)[0]
    known = common if common is not None else COMMON_STARTERS
    if (force or word.lower() in known or base.lower() in known) and not (word.isupper() and len(word) > 1) and base != "I":
        return sentence_text[: m.start(2)] + word[0].lower() + word[1:] + sentence_text[m.end(2):]
    return sentence_text


# words spelt with a vowel that start with a consonant sound ("a ute", "a uni", "a one-off", "a U-turn"), and
# the h words that start with a vowel sound ("an hour")
YOU_SOUND = re.compile(r"(?:uni(?![nmdl])|unan|ute|uter|use|usa|usu|uti|ura|ure|urin|uro|ufo|uke|uku|ubiq|uefa|unesco|"
                       r"eu|ewe|one\b|once|onesi|oui|u-|u\b)", re.I)
SILENT_H = ("hour", "honest", "honour", "honor", "heir")
# letters whose names start with a vowel sound: "an FBI agent", "an RSL", "an SUV" (but "a UFO", "a CSIRO bloke")
VOWEL_LETTERS = set("AEFHILMNORSX")
# initialisms with a vowel in them, said letter by letter; any other short all-caps word with a vowel is a word
# in capitals ("A HAT", "A MAN"), and one without a vowel is letters ("an RSL", "an NSW bloke")
SPELT_OUT = frozenset("ABC AFL AGM AI ATM ATO EU FBI ICU IOU IQ IVF OBE SUV UFO UN USB UK US USA".split())


def indefinite_article(word: str) -> str:
    """"a" or "an" before word, by its sound: an initialism by its first letter's name, a pronounced acronym
    ("a NASA probe", "an ANZAC") and an ordinary word by their first sound, a number as it is said."""
    if word[:1].isdigit():
        return "an" if word.startswith("8") or re.match(r"1[18](?:\D|$)", word) else "a"
    letters = re.sub(r"[^A-Za-z]", "", word.split("-")[0])
    if len(letters) >= 2 and letters.isupper() and (letters in SPELT_OUT or not re.search(r"[AEIOUY]", letters[1:])):
        return "an" if letters[0] in VOWEL_LETTERS else "a"
    low = word.lower()
    if low.startswith(SILENT_H):
        return "an"
    return "an" if low[:1] in "aeiou" and not YOU_SOUND.match(low) else "a"


def fix_articles(text: str) -> str:
    """Repair a/an after substitutions ("an breakfast" -> "a brekkie", "an ute" -> "a ute")."""
    def repl(m: re.Match) -> str:
        art, space, word = m.group(1), m.group(2), m.group(3)
        want = indefinite_article(word)
        if art.lower() == want:
            return m.group(0)
        if art[0].isupper():
            want = want.capitalize()
        return want + space + word
    return re.sub(r"\b([Aa]n?)(\s+)([A-Za-z0-9][\w'-]*)", repl, text)
