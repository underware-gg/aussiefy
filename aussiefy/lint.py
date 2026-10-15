"""Lint: what's wrong with an Aussified draft, and what could be more Aussie.

Issues (flagged or non-Aussie phrases, swearing over the cap, US spelling, US and British words) are things to fix; warnings
are the style guide's mechanical rules and, given the original, fidelity (length, names, numbers);
suggestions are optional spots the engine would swap.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .context import sentence_contexts
from .dialect import Found, text_english
from .engine import Translator, default_translator
from . import morph
from .genre import Genre, resolve_document
from .markup import markup_changed, mask
from .model import Dictionary
from .schema import PLACEHOLDER_RE, Entry
from .terms import fold, strip_markup
from .text import document_spans, HONORIFICS, Token, capital_is_positional, heading_lines, held_spans, sentences, tokenize


def lint(text: str, *, level: int | str = 5, vulgarity: int | str | None = None,
         original: str | None = None, markup: str = "text", english: str | None = None,
         embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None, translator: Translator | None = None,
         suggest: bool = True) -> dict[str, Any]:
    """Lint an Aussified draft. Issues are things to fix; suggestions are optional extra Aussie.
    Pass the original text to also check fidelity: length, and names and numbers kept or invented.
    markup (markdown, mdx, auto) lints the prose only, and with the original checks that every piece of code
    and markup in it came through unchanged. english (us, uk, auto, none) is the original's English, as for
    translate: British "pants" in a draft is only flagged for uk. embellishment (deadset, dinkum, troppo; None =
    the selected document type's default) sets how much longer than the original a retelling may run.
    suggest=False skips the suggestions (a whole engine translation) for a check that doesn't show them:
    verify, and yarn mode's submit."""
    tr = translator or default_translator()
    pol = tr.policy(english=english, embellishment=embellishment, document_type=document_type, document_config=document_config)
    dial = pol.english
    changed = markup_changed(text, original, markup) if original is not None else []
    # the US and British words are read as the engine read the original: its English, and its genre (a
    # browser's cookies stay in a technical text)
    source = mask(original if original is not None else text, markup)
    read_as = resolve_document(source.prose(), source.source, config=tr.dictionary.genres,
                               document_type=pol.document_type, document_config=pol.document_config)
    genre = read_as.policy.term_domains
    text = mask(text, markup).prose()
    original = source.prose() if original is not None else None
    d = tr.dictionary
    eff = tr.effective(level=level, vulgarity=vulgarity)
    cap = eff.vulgarity
    low = " " + fold(text) + " "
    # what the original itself says isn't the translator's word ("cooked" in a recipe, a quoted swear)
    orig_low = " " + fold(original) + " " if original is not None else " "
    issues: list[dict[str, Any]] = []
    kept_spelling = []
    if original is not None:
        spans = document_spans(original, keep_quotes=read_as.policy.keep_quotes,
                               datelines=read_as.policy.dateline_context)
        protected = Counter(original[a:b] for a, b in spans)
        for phrase, count in protected.items():
            if text.count(phrase) < count:
                issues.append({"kind": "document_changed", "phrase": phrase,
                               "why": "quoted wording or a dateline protected by document_config changed or was dropped"})

        remaining = protected.copy()
        for a, b in document_spans(text, keep_quotes=read_as.policy.keep_quotes,
                                    datelines=read_as.policy.dateline_context):
            phrase = text[a:b]
            if remaining[phrase] > 0:
                kept_spelling.append((a, b))
                remaining[phrase] -= 1

    for e in d.entries.values():
        if e.status == "active" and e.vulgarity <= cap:
            continue
        # gated as general English ("dear" for expensive, "dicey"): not wrong, just not Aussie-specific
        if e.status == "gate" and "not_aussie" in e.flags:
            continue
        # gated for a doubtful slang sense, in words with a plain sense too ("a bit rough", "shame"): lint can't
        # tell the senses apart, and the plain one is fine
        if e.plain_sense:
            continue
        for form in e.all_forms:
            f = strip_markup(form)
            # "{poss} fella" stripped to "fella" would flag every fella
            if PLACEHOLDER_RE.search(form) and " " not in f:
                continue
            if e.status == "gate" and " " not in f and f in d.plain_words:
                continue   # a gated "blow" (boast) would flag every "blow over"
            word_re = r"(?<![a-z])" + re.escape(f) + r"(?![a-z])"
            # the original's own uses are its own; more than it has are the translator's
            if len(f) < 4 or len(re.findall(word_re, low)) <= len(re.findall(word_re, orig_low)):
                continue
            if e.status != "active":
                issues.append({"kind": "flagged", "phrase": form, "status": e.status, "flags": list(e.flags),
                               "why": e.notes or "flagged in the dictionary"})
            elif e.vulgarity > cap:
                issues.append({"kind": "too_vulgar", "phrase": form, "vulgarity": e.vulgarity, "cap": cap})
            break

    # single swear words over the cap
    d = tr.dictionary
    # the source's own language isn't the translator's swearing ("Cocksucker in Moloch!"), unless it says more
    source_words = Counter(re.findall(r"[a-z']+", orig_low))
    flagged = {i["phrase"].lower() for i in issues}
    for word, n in sorted(Counter(re.findall(r"[a-z']+", low)).items()):
        strength = d.swear_strength(word)
        if strength > cap and n > source_words[word] and word not in flagged:
            issues.append({"kind": "too_vulgar", "phrase": word, "vulgarity": strength, "cap": cap})

    read_english = text_english(dial, source.prose(), d.us_spellings)
    if dial != "none":
        issues += _dialect_issues(text, original, d, read_english, genre, read_as.policy.keep_quotes)
        for word, au in d.dialect.lint_only.items():
            said = re.compile(r"(?<![a-z'])" + re.escape(word.lower()) + r"(?![a-z])")
            # the original's own "y'all" (a quote, a character) isn't the translator's word, as many times as it has it
            if len(said.findall(low)) > len(said.findall(orig_low)):
                issues.append({"kind": "dialect", "english": "us", "phrase": word, "australian": au})

    # US spelling, via the dictionary's own spelling rules
    for rule in d.phonetic:
        if rule.kind != "spelling":
            continue
        for m in rule.pattern.finditer(text):
            if any(a <= m.start() and m.end() <= b for a, b in kept_spelling):
                continue
            issues.append({"kind": "spelling", "phrase": m.group(0), "australian": m.expand(rule.replace)})

    # where the text already uses dictionary slang (so we don't suggest replacing it): matched with the
    # engine's own matcher, so inflections and slots count ("smashed it to buggery", "kippin'")
    aussie_spans = _aussie_spans(text, tr)

    suggestions = _suggestions(text, low, aussie_spans, level, vulgarity, tr, read_as, read_english, dial, pol.embellishment) if suggest else []
    fixed = {fold(issue["phrase"]) for issue in issues if issue.get("australian")}
    suggestions = [item for item in suggestions if fold(item["text"]) not in fixed]

    warnings = _style_warnings(text, aussie_spans, tr) + _swear_warnings(text, d)
    covered = {fold(w["phrase"]) for w in warnings if w["kind"] == "repeated"}
    # a refrain the translation repeats is fine where the original repeats it too, said in Australian
    refrains = (_in_australian(original, d, read_english, genre) if original is not None and dial != "none"
                else original)
    warnings += _repeated_phrases(text, refrains, d.drawl_readings, covered)
    issues += changed
    if original is not None:
        warnings += fidelity(text, original, check_length=read_as.policy.check_length, max_length=read_as.setting(pol.embellishment).max_length,
                             translator=tr)
    return {"ok": not issues, **eff.envelope(), **read_as.envelope(pol.embellishment),
            "issues": issues, "warnings": warnings,
            "suggestions": suggestions[:20],
            "scope": ("Issues: flagged phrases, swearing over the cap, US spelling and US words. Warnings: the "
                      "guide's style rules and swearing density" +
                      ("; fidelity to the original (length, names, numbers)." if original is not None else
                       ". Pass the original to also check fidelity.") + " Not checked: invented slang.")}



def _suggestions(text: str, low: str, aussie_spans: list, level: int | str, vulgarity: int | str | None,
                 tr: Translator, genre: Genre, english: str | None, dial: str, embellishment: int | None = None) -> list[dict[str, Any]]:
    """What the rule engine would still Aussify in a draft: optional, ranked by how sure it is. A whole engine
    translation, so the checks that don't show suggestions (verify, yarn's submit) skip it. It reads the draft in
    the original's genre: a voiced policy reads as a story, but its gift is no pressie."""
    result = tr.translate(text, level=level, vulgarity=vulgarity, embedder="none", english=dial, embellishment=embellishment, _context=(genre, english))
    suggestions = []
    for r in result.records:
        a, b = r.span
        if any(s <= a < t or s < b <= t for s, t, _ in aussie_spans):
            continue  # already part of an Aussie phrase ("smack-bang in the middle of")
        if r.text.lower() == "great" and re.search(r"(bloody|flamin'?|fuckin'?|fucking|whoppin'?|whopping|big|"
                                                   r"ginormous|huge|almighty)\s+$", text[:a].lower()):
            continue  # "a bloody great stone", "whoppin' great bombs": great means big here
        # don't push a word the text already uses ("man" -> "bloke" right after "blokes")
        opts = [_readable(c.entry.form) for c in sorted(r.eligible, key=lambda c: -c.weight)
                if c.entry.form.lower() != r.text.lower()
                and not re.search(r"\b" + re.escape(PLACEHOLDER_RE.sub("", c.entry.form).strip().lower()), low)][:3]
        if opts:
            suggestions.append({"text": r.text, "meaning": "/".join(r.det.concepts), "options": opts})

    return suggestions

def _dialect_issues(text: str, original: str | None, d: Dictionary, english: str | None, genre: str | tuple[str, ...],
                    keep_quotes: bool) -> list[dict[str, Any]]:
    """US and British words Australians say differently, found as the engine finds them: plurals and
    inflections, its sense guards, names left alone, terms of art in their genre (a browser's cookies). Given
    the original, a word Australians also use (thong, jelly) is flagged only where the original had it: in the
    draft it may be the Australian for something else (flip-flops, jello). The original's own bracketed gloss
    ("cookies (biscuits)"), kept as written, isn't flagged, and nor is what the original holds as said (a word
    mentioned, a quote in a genre that keeps quotes: the Fed's "5 percent" stays), as many times as it holds it:
    a quote the draft adds is the writer's own. Spelling is still Australian there, as the engine writes it."""
    def finds(t: str):
        return [f for sent in sentences(tokenize(t)) for f in d.dialect.find(sent, english, genre)]

    def held_finds(t: str) -> list[tuple[list[Token], Found]]:
        spans = held_spans(t, keep_quotes)
        return [(sent, f) for sent in sentences(tokenize(t)) for f in d.dialect.find(sent, english, genre)
                if any(a <= sent[f.start].start and sent[f.end - 1].end <= b for a, b in spans)]

    in_original = {id(f.swap) for f in finds(original)} if original is not None else None
    def held_key(t: str, sent: list[Token], found: Found) -> tuple[int, str]:
        return id(found.swap), fold(t[sent[found.start].start:sent[found.end - 1].end])

    # The wording and count must survive: a held singular cannot excuse a new plural or changed slot.
    source = original if original is not None else text
    excused = Counter(held_key(source, sent, f) for sent, f in held_finds(source))
    held_here = {(sent[0].start, f.start) for sent, f in held_finds(text)}
    glossed = {fold(m) for m in re.findall(r"\(([^()\n]{1,40})\)", original or "")}
    out = []
    for sent in sentences(tokenize(text)):
        for f in d.dialect.find(sent, english, genre):
            if f.swap.known_only and in_original is not None and id(f.swap) not in in_original:
                continue
            bracketed = f.start >= 1 and sent[f.start - 1].text == "(" and f.end < len(sent) \
                and sent[f.end].text == ")"
            if bracketed and fold(text[sent[f.start].start:sent[f.end - 1].end]) in glossed:
                continue   # the original's own bracketed gloss ("cookies (biscuits)"), kept as written
            key = held_key(text, sent, f)
            if (sent[0].start, f.start) in held_here and excused[key] > 0:
                excused[key] -= 1
                continue
            out.append({"kind": "dialect", "english": f.swap.english,
                        "phrase": text[sent[f.start].start:sent[f.end - 1].end], "australian": f.text})
    return out


FUNCTION_WORDS = frozenset("""a an the of to in on at and or but is are was were be been it its you i he she we they
that this for with his her their my your our me him them us as by from so not no do does did have has had will
would can could just there here what it's don't i'm that's isn't wasn't didn't can't won't i'll you're they're
he's she's we're there's""".split())


def _phrase_words(t: str, drawl: dict[str, str]) -> list[list[str]]:
    """Each sentence's words, with literal drawl read through its dictionary annotations."""
    alternatives = [("" if word.startswith("'") else r"(?<![a-z'])") + re.escape(word) + r"(?![a-z'])"
                    for word in sorted(drawl, key=len, reverse=True)]
    out = []
    for sent in re.split(r"(?<=[.!?])\s+|\n\s*\n", fold(t)):
        if alternatives:
            sent = re.sub("|".join(alternatives), lambda m: " " + drawl[m[0]] + " ", sent)
        words = []
        for w in re.findall(r"[a-z']+", sent):
            w = "per cent" if w == "percent" else w
            words += (w[:-1] + "g" if w.endswith("in'") else w).split()
        out.append(words)
    return out


def _grams(sentences: list[list[str]]) -> dict[str, list[tuple[int, int, int]]]:
    """Every three-to-six-word phrase with a content word, and where it is: (sentence, start, end)."""
    found: dict[str, list[tuple[int, int, int]]] = {}
    for si, words in enumerate(sentences):
        for n in range(3, 7):
            for i in range(len(words) - n + 1):
                gram = words[i:i + n]
                if not set(gram) <= FUNCTION_WORDS:
                    found.setdefault(" ".join(gram), []).append((si, i, i + n))
    return found


def _in_australian(original: str, d: Dictionary, english: str | None, genre: str | tuple[str, ...]) -> str:
    """The original with its US and British words in Australian ("skillet or" -> "frying pan or"), so a retelling
    that says the Australian as often as the original said the American isn't repeating. english None (not
    known): read as American, the commoner case."""
    out, pos = [], 0
    for sent in sentences(tokenize(original)):
        for f in d.dialect.find(sent, english or "us", genre):
            a, b = sent[f.start].start, sent[f.end - 1].end
            out += [original[pos:a], f.text]
            pos = b
    return "".join(out) + original[pos:]


# a unit's conversion in brackets ("90°F (about 32°C)", "two gallons (about 7.5 litres)"): the brief's own form,
# said once per measurement, so it's no tic however often a text measures
_CONVERSION = re.compile(r"\(\s*(?:about|around|roughly|approx\.?|nearly|over|under)?\s*[\d.,]+(?:\s*(?:-|to)\s*[\d.,]+)?"
                         r"\s*(?:°\s*[CF]\b|[CF]\b|[a-zµ]+)[^()]*\)")


def _repeated_phrases(text: str, original: str | None, drawl: dict[str, str], covered: set[str] = frozenset(),
                      most: int = 5) -> list[dict[str, Any]]:
    """A phrase of three to six words said three times or more where the original doesn't repeat it: a tic the
    dictionary doesn't know ("has a go at you" four times). Measured against the original only: its own
    refrains are its own, even respelt or with a word swapped ("the man from Ironbark" -> "the bloke from
    Ironbark"). Pass the original in Australian (_in_australian): its "skillet or" is the retelling's "frying pan
    or". Overlapping windows of one repeat are reported once, as the longest."""
    if original is None:
        return []
    mine = _grams(_phrase_words(_CONVERSION.sub(" ", text), drawl))
    theirs = _grams(_phrase_words(_CONVERSION.sub(" ", original), drawl))
    refrains = [set(g.split()) - FUNCTION_WORDS for g, at in theirs.items() if len(at) >= 3]
    claimed: set[tuple[int, int]] = set()
    out = []
    for phrase, at in sorted(mine.items(), key=lambda kv: (-len(kv[0].split()), kv[0])):
        n = len(at)
        if n < 3 or n <= len(theirs.get(phrase, ())) or any(re.search(rf"\b{re.escape(c)}\b", phrase) for c in covered):
            continue
        spots = {(si, k) for si, a, b in at for k in range(a, b)}
        if all(any((si, k) in claimed for k in range(a, b)) for si, a, b in at):
            continue   # a window of a longer repeat already reported or excused
        claimed |= spots
        content = set(phrase.split()) - FUNCTION_WORDS
        if any(len(content & r) * 2 >= len(content) for r in refrains):
            continue   # the original's own refrain, said its way
        out.append({"kind": "repeated_phrase", "phrase": phrase, "times": n,
                    "why": f"said {n} times; vary it unless it is the text's own refrain"})
    return out[:most]


def _swear_warnings(text: str, d: Dictionary) -> list[dict[str, Any]]:
    """Swearing works as seasoning: one word leaned on, or a swear every few words, reads as a parody."""
    words = re.findall(r"[a-z']+", fold(text))
    hits = Counter(w for w in words if d.swear_strength(w))
    out: list[dict[str, Any]] = []
    if not words:
        return out
    allowed = max(3, len(words) // 80)            # about one of any given swear per 80 words
    for word, n in hits.most_common():
        if n > allowed:
            out.append({"kind": "swear_overuse", "phrase": word, "times": n,
                        "why": f"used {n} times in {len(words)} words (about {allowed} reads right); vary it or "
                               "cut most of them"})
    total = sum(hits.values())
    if total >= 4 and total / len(words) > 1 / 20:
        out.append({"kind": "swear_density", "phrase": f"{total} swears", "times": total,
                    "why": f"one swear every {len(words) // total} words; keep it under one in 20"})
    return out


NUMBER_RE = re.compile(r"\b\d[\d,.]*\b")
# a month or day written short, and what it is written out
DATE_WORDS = {"jan": "january", "feb": "february", "mar": "march", "apr": "april", "jun": "june", "jul": "july",
              "aug": "august", "sep": "september", "sept": "september", "oct": "october", "nov": "november",
              "dec": "december", "mon": "monday", "tue": "tuesday", "tues": "tuesday", "wed": "wednesday",
              "thu": "thursday", "thurs": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"}
def fidelity(text: str, original: str, *, max_length: float | None = None, check_length: bool = True,
             translator: Translator | None = None) -> list[dict[str, Any]]:
    """Does the Aussie version tell the same story? Length (up to max_length times the original, plus 20 words:
    the embellishment's; None: the loosest, troppo's), and the original's names and numbers.

    These are warnings, not issues: a yarn may trim a list or name a local thing ("Parliament House" for
    "Congress"), but each should be a choice, not drift."""
    tr = translator or default_translator()
    out: list[dict[str, Any]] = []
    n_text, n_orig = len(text.split()), len(original.split())
    if max_length is None:
        max_length = max(e.max_length for e in tr.dictionary.genres.embellishments.values())
    if check_length and n_orig and n_text > max_length * n_orig + 20:
        out.append({"kind": "too_long", "phrase": f"{n_text} words vs {n_orig}", "times": round(n_text / n_orig, 1),
                    "why": f"more than {max_length:g} times the original's length at this embellishment: trim what "
                           f"doesn't hang off anything in the original"})
    if check_length and n_orig and n_text < 0.6 * n_orig:
        out.append({"kind": "too_short", "phrase": f"{n_text} words vs {n_orig}", "times": round(n_text / n_orig, 1),
                    "why": "much shorter than the original: keep every event and line"})
    low = text.lower()
    for num in sorted(set(NUMBER_RE.findall(original))):
        if num.rstrip(".,") not in text:
            out.append({"kind": "number_dropped", "phrase": num.rstrip(".,"), "why": "a number in the original is missing"})
    orig_names = _names(original, tr)
    # a name broken across lines is still the name, and so is "Mr Gladden" for "Mr. Gladden" and the drawl's
    # "Thanksgivin'" for "Thanksgiving"
    orig_low = _same_name(" ".join(original.lower().split()))
    slang = " ".join(f.lower() for e in tr.dictionary.entries.values() for f in e.all_forms)
    flat = _same_name(" ".join(low.split()))
    for name in sorted(orig_names):
        word = _same_name(name.lower().rstrip("."))
        short = [k for k, v in DATE_WORDS.items() if v == word]
        if " ".join(word.split()) in flat or _dictionary_name_kept(name, flat, tr.dictionary) \
                or DATE_WORDS.get(word, "\0") in flat \
                or any(re.search(rf"\b{k.title()}\.|(?<=[\w,;] ){k.title()}\b", text) for k in short):
            continue   # kept, or a date localised ("Oct. 11" -> "11 October", "Monday" -> "Mon")
        out.append({"kind": "name_dropped", "phrase": name,
                    "why": "a name in the original is missing (fine if you localised it on purpose)"})
    english = tr.dictionary.plain_words
    forms = {f.lower() for e in tr.dictionary.entries.values() for f in e.all_forms}
    for name in sorted(_names(text, tr) - orig_names):
        short = [k for k, v in DATE_WORDS.items() if v == name.lower()]
        # the dictionary's own word, the plan's ("Yanks" for "Americans"), is no invented name
        known = name.lower() in slang or (morph.singular_of(name) or "").lower() in forms
        # a written-out date the original abbreviated: its "Sat." is a capital, not "he sat"
        if _same_name(name.lower()) not in orig_low and not known and name.lower() not in english \
                and not _derived_from(name, orig_names) \
                and name not in ("Aussie", "Aussies") and not any(re.search(rf"\b{k.title()}\b", original) for k in short):
            out.append({"kind": "name_added", "phrase": name,
                        "why": "a name not in the original: is it a deliberate local swap or invented content?"})
    return out


def _dictionary_name_kept(name: str, flat: str, dictionary: Dictionary) -> bool:
    """Only an explicitly reviewed whole-phrase alias excuses a changed capitalised phrase."""
    return any(re.search(r"(?<!\w)" + re.escape(_same_name(alias)) + r"(?!\w)", flat)
               for alias in dictionary.name_aliases.get(fold(name), ()))


# what turns a place into its people or their adjective: Colombia -> Colombian, Europe -> European, New England
# -> New Englanders, Japan -> Japanese, Israel -> Israeli, Britain -> British
_DEMONYM_ENDINGS = ("n", "an", "ian", "ns", "ans", "ians", "ese", "i", "is", "ish")
_LAND_ENDINGS = ("er", "ers")   # only after a "-land": New Englanders, Icelanders (not Smithers from Smith)


def _derived_from(name: str, names: set[str]) -> bool:
    """A people or an adjective made from a name the original has ("Colombian" from "Colombia")."""
    low = name.lower()
    for base in (n.lower() for n in names):
        stems = {base, base[:-1]} if base[-1:] in "aeiouy" else {base}
        endings = _DEMONYM_ENDINGS + (_LAND_ENDINGS if base.endswith("land") else ())
        if any(low == st + end for st in stems for end in endings):
            return True
    return False


_TITLE_STOP = re.compile(rf"\b({'|'.join(sorted(HONORIFICS))}|[a-z])\.(?=\s)")
_DROPPED_G = re.compile(r"(?<=[a-z]{3})in['’](?=\s|$|[,.;:!?])")


def _same_name(s: str) -> str:
    """A lower-cased name as written either way: "mr gladden" for "mr. gladden" (a title's or an initial's full
    stop, not a sentence's), "thanksgiving" for the drawl's "thanksgivin'"."""
    return _DROPPED_G.sub("ing", _TITLE_STOP.sub(r"\1", s))


def _names(text: str, tr: Translator) -> set[str]:
    """Capitalised words mid-sentence and mid-line: the names in a text. An ordinary English word counts only if
    it recurs capitalised and never appears in lower case (the Wolf, Mary); in a text that Capitalises Its
    Common Nouns (the Declaration's "Course", "Powers", "Tyranny") every word must recur."""
    runs: Counter[str] = Counter()
    headings = heading_lines(text)
    for sent in sentences(tokenize(text)):
        run: list[str] = []
        for i, t in enumerate(sent + [None]):
            word = t is not None and t.is_word and t.text[:1].isupper() and not t.text.isupper() \
                and not capital_is_positional(sent, i) \
                and not any(a <= t.start < b for a, b in headings) \
                and "\n" not in text[sent[i - 1].end:t.start]      # a verse line's first word isn't a name
            if word:
                run.append(t.text)
            elif run:
                runs[" ".join(run)] += 1
                run = []
    english = tr.dictionary.plain_words
    lower = set(re.findall(r"\b[a-z][a-z']*\b", text))
    common = lambda n: " " not in n and n.lower() in english
    # a text that Capitalises Its Common Nouns: many capitals, a good share of them ordinary words (of the
    # reference texts only the Declaration: 30 capitals, 53% ordinary; Pride and Prejudice has 17, 18%)
    title_case = len(runs) >= 10 and sum(1 for n in runs if common(n)) >= 0.4 * len(runs)
    names = {n for n, k in runs.items()
             if (not common(n) and not title_case) or (k >= 2 and n.lower() not in lower)}
    return {n for n in names if n not in {"I", "I'm", "I'll", "I've", "I'd", "God"}}


def _aussie_spans(text: str, tr: Translator) -> list[tuple[int, int, Entry]]:
    index = tr.dictionary.form_index
    spans = []
    for sent in sentences(tokenize(text)):
        for m in index.find(sent):
            spans.append((sent[m.start].start, sent[m.end - 1].end, tr.dictionary.entries[m.pattern.entry_id]))
    return spans


def _inside_quote(text: str, pos: int) -> bool:
    """Whether pos falls inside quoted speech that opened earlier (a quote running over several sentences)."""
    before = text[:pos]
    if before.rfind("\u201c") > before.rfind("\u201d"):
        return True
    return before.count('"') % 2 == 1


def _readable(form: str) -> str:
    form = re.sub(r"([\w']+)\|[\w']+", r"\1", form)
    return re.sub(r"\{(obj|np)\}", "...", re.sub(r"\{(poss|objposs)\}", "their", form))


def _style_warnings(text: str, aussie_spans: list, tr: Translator) -> list[dict[str, Any]]:
    """The style guide's mechanical rules: pile-ups, overused slang, tag-ons in narration."""
    warnings: list[dict[str, Any]] = []
    low = text.lower()
    # synonym pile-ups: two entries for the same concept joined by a comma or "and"
    spans = sorted({(s, t, e.id): e for s, t, e in aussie_spans}.items())
    for (s1, t1, _), e1 in spans:
        for (s2, t2, _), e2 in spans:
            if e2.id != e1.id and 0 <= s2 - t1 <= 6 and set(e1.concept) & set(e2.concept) \
                    and re.fullmatch(r"\s*(,|and|'n)\s*", low[t1:s2]) and len(text[s1:t2].split()) <= 8:
                warnings.append({"kind": "pile_up", "phrase": text[s1:t2].strip(),
                                 "why": "two slang words for the same thing back to back; pick one"})
    # overused slang (deliberate patterns like the three bears' lines are fine; this is a nudge)
    # one use per stretch of text: an entry's overlapping matches ("a bit full", and "full" inside it) are one,
    # and entries sharing a form ("fair dinkum" as a predicate and a question) are one term
    uses: dict[str, list[tuple[int, int]]] = {}
    plain = tr.dictionary.plain_words
    for s, t, e in sorted(aussie_spans, key=lambda x: (x[0], -x[1])):
        if e.substitution_class == "lexical":
            continue
        said = fold(text[s:t])
        if said != fold(e.form) and said in plain:
            continue   # a variant that is plain English ("full" for "a bit full") isn't a use of the slang
        spans = uses.setdefault(e.form, [])
        if not spans or s >= spans[-1][1]:
            spans.append((s, t))
    for form, spans in uses.items():
        if len(spans) >= 3:
            warnings.append({"kind": "repeated", "phrase": form, "times": len(spans),
                             "why": "used 3+ times; vary it unless the repetition is a deliberate pattern"})
    # tag-ons: in a story with dialogue, narration has nobody to address; in a monologue the speaker talks to
    # the listener, so tags are fine but shouldn't land on every other line
    story = bool(re.search(r"[\"\u201c\u201d]", text))
    tags = []
    tag_re = _tag_re(tr.dictionary)
    for sent in sentences(tokenize(text)):
        s_text = text[sent[0].start:sent[-1].end]
        ctx = sentence_contexts(sent)
        m = tag_re.search(s_text)
        if not m:
            continue
        tags.append(s_text)
        if story and not ctx & {"dialogue", "question", "second_person"} and not _inside_quote(text, sent[0].start):
            warnings.append({"kind": "tag_in_narration", "phrase": s_text[-40:],
                             "why": "tag-ons belong where someone is being spoken to"})
    words = len(text.split())
    if not story and len(tags) > max(3, words // 120):
        warnings.append({"kind": "tag_overuse", "phrase": f"{len(tags)} tag-ons", "times": len(tags),
                         "why": f"{len(tags)} tag-ons in {words} words; about one per 120 words reads right"})
    # the default opener: "Right, so" started 16 of 18 retellings
    if re.match(r"\s*righto?,?\s+so\b", low):
        warnings.append({"kind": "stock_opener", "phrase": text.strip()[:20],
                         "why": "\"Right, so\" is the opener every model reaches for; try one of the plan's openings, or start "
                                "straight in"})
    # a stock exclamation as the last line: every yarn ended "Gawd help us." when the guide named it
    last = re.split(r"(?<=[.!?])\s+", text.strip())[-1:]
    stock = {_norm_line(f) for f in tr.dictionary.closer_forms}
    if last and len(last[0].split()) <= 5 and _norm_line(last[0]) in stock:
        warnings.append({"kind": "stock_closer", "phrase": last[0],
                         "why": "a stock exclamation that would end any story; a punchline about this one lands "
                                "better"})
    return warnings


def _tag_re(d: Dictionary) -> re.Pattern:
    """A tag-on that addresses someone, at a sentence's end: the dictionary's own ("mate", "ya galah"), "eh", or
    any "ya X". (re caches the compiled pattern.)"""
    forms = sorted(d.tag_forms | {"eh"}, key=len, reverse=True)
    return re.compile(r",\s*(" + "|".join(map(re.escape, forms)) + r"|ya [a-z]+)[.!?]?\s*$", re.I)


def _norm_line(s: str) -> str:
    return re.sub(r"[^a-z' ]", "", fold(s)).strip()
