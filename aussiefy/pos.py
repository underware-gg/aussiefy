"""Part-of-speech tags: which words are nouns, verbs, adjectives, names. Deterministic and offline. Also the
command verbs a sentence may open on (IMPERATIVES), which the genre reader and the engine share.

The averaged-perceptron tagger of NLTK (Honnibal's design, trained on the Penn Treebank's Wall Street Journal),
re-implemented here in a few lines with its weights vendored in data/pos/ (MIT; see data/pos/README.md). It
gives exactly NLTK's tags (checked over the corpus: 53,656 tokens, no difference), about 97% right on news text,
in about 20 microseconds a word. Tags are the Penn Treebank's: NN noun, NNS plural noun, NNP name, VB verb,
VBD past, VBG -ing, JJ adjective, RB adverb, and so on.
"""

from __future__ import annotations

import gzip
import json
from functools import lru_cache

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"   # not loader's: the dictionary's model imports this module
START, END = ["-START-", "-START2-"], ["-END-", "-END2-"]
# sentence-initial verbs that give a command: genre.py counts them (an instruction), and the engine lowers one
# after an opener ("Well, pour the batter") ("Place cold food in a cooler.")
IMPERATIVES = frozenset("""add adjust allow apply ask avoid bake be beat begin blend boil bring buy call carry change check
choose clean click close combine come complete connect consider contact cook cool cover create cut define delete
discard dispose do don't download drain drink drive eat enable enter fill find fold follow get give go grease heat
hike identify include install keep knead leave let limit look make measure melt mix monitor move never note open
pack pass pay pick place plan plant pour prepare press preheat print put read reduce refer remember remove repeat
replace rinse run save see seek select send serve set share sift soak sprinkle stay stir stop store submit
take tell test throw try turn type unplug update use visit wait wash watch wear whisk wrap write""".split())
# our tokens as the Penn Treebank writes them, which the weights were trained on
PENN = {'"': "``", "\u201c": "``", "\u201d": "''", "\u2018": "`", "\u2019": "'", "\u2014": "--", "\u2013": "--",
        "[": "(", "]": ")", "{": "(", "}": ")"}
# casual contractions the Treebank never saw, tagged as what they are ("gonna complain": complain is a verb)
FIXED = {"gonna": "MD", "wanna": "MD", "gotta": "MD", "hafta": "MD", "oughta": "MD", "outta": "IN"}
NOUNS = frozenset({"NN", "NNS"})
NAMES = frozenset({"NNP", "NNPS"})
VERBS = frozenset({"VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD"})


@lru_cache(maxsize=1)
def _model() -> tuple[list[str], dict[str, str], dict[str, dict[str, float]]]:
    d = json.loads(gzip.decompress((DATA_DIR / "pos" / "tagger.json.gz").read_bytes()))
    return d["classes"], d["tagdict"], d["weights"]


def _normalise(word: str) -> str:
    if "-" in word and word[0] != "-":
        return "!HYPHEN"
    if word.isdigit() and len(word) == 4:
        return "!YEAR"
    if word[:1].isdigit():
        return "!DIGITS"
    return word.lower()


@lru_cache(maxsize=1)
def lower_words() -> frozenset[str]:
    """Lower-case words the tagger's training text wrote consistently: ordinary English, never a name."""
    return frozenset(w for w in _model()[1] if w.islower())


def tag(words: list[str]) -> list[str]:
    """The tag of each word in a sentence's words, in order (NLTK's PerceptronTagger.tag, tags only), with our
    quotes and dashes written as the Treebank writes them and casual contractions tagged as what they are."""
    classes, tagdict, weights = _model()
    words = [PENN.get(w, w) for w in words]
    prev, prev2 = START
    ctx = START + [_normalise(w) for w in words] + END
    out = []
    for i, w in enumerate(words):
        t = FIXED.get(w.lower()) or tagdict.get(w)
        if not t:
            j = i + 2
            features = ("bias", "i suffix " + w[-3:], "i pref1 " + w[:1], "i-1 tag " + prev, "i-2 tag " + prev2,
                        f"i tag+i-2 tag {prev} {prev2}", "i word " + ctx[j], f"i-1 tag+i word {prev} {ctx[j]}",
                        "i-1 word " + ctx[j - 1], "i-1 suffix " + ctx[j - 1][-3:], "i-2 word " + ctx[j - 2],
                        "i+1 word " + ctx[j + 1], "i+1 suffix " + ctx[j + 1][-3:], "i+2 word " + ctx[j + 2])
            scores: dict[str, float] = {}
            for f in features:
                for label, weight in weights.get(f, {}).items():
                    scores[label] = scores.get(label, 0.0) + weight
            t = max(classes, key=lambda c: (scores.get(c, 0.0), c))
        out.append(t)
        prev2, prev = prev, t
    return out
