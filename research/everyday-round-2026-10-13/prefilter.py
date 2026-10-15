"""Cut the everyday pass's harvest down to plausible vocabulary for the verifiers, deterministically.

    python prefilter.py      # -> candidates.yaml, existing_forms.txt, and slices verify/slice-N.yaml

Dropped: drawl and plain English (every word ordinary once "workin'" is "working"), spellings (one word that differs from what it replaces only by spelling, which the spelling rules
own), long spans (six words or more: retold sentences, not terms), and additions of more than three words
(narrative colour, not a term). Kept: everything else, with how many texts used it, so the commonest come first.
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from aussiefy.loader import load_dictionary  # noqa: E402

HARVEST = ROOT / "research" / "everyday-pass-2026-10-12" / "harvest.yaml"
SLICES = 5


DRAWL = {"em", "ya", "yer", "ain't", "gonna", "gotta", "wanna", "cause", "n", "me", "there's", "it's", "that's",
         "what's", "'ll", "'d", "y'know", "dunno", "outta", "kinda", "sorta", "'til", "till", "nothin", "somethin",
         "anythin", "everythin", "fella"}


def plain(word: str, plain_words: frozenset[str]) -> bool:
    """A plain English word, or one the drawl rules make ("workin'", "'em", "ya"), or a contraction of one."""
    w = word.lower().strip("'’\".,;:!?()")
    if "'" in w and plain(w.split("'")[0], plain_words):
        return True
    return (not w or w in DRAWL or w in plain_words or (w.endswith("in") and w + "g" in plain_words)
            or w.replace("'", "") in plain_words or (w.endswith("s") and w[:-1] in plain_words)
            or (w.endswith("ed") and (w[:-2] in plain_words or w[:-1] in plain_words)))


def keep(item: dict, plain_words: frozenset[str] = frozenset()) -> bool:
    words = item["form"].split()
    replaced = [m.removeprefix("replaces: ") for m in item["source_meanings"] if m.startswith("replaces: ")]
    if plain_words and all(plain(w, plain_words) for w in words):
        # ordinary English: kept only as a short swap for different words, where it may be the Australian
        # choice ("autumn" for "fall", "fridge" for "refrigerator")
        swaps = [r for r in replaced if len(r.split()) <= 3 and not set(r.lower().split()) & set(item["form"].lower().split())]
        drawl = any(w.lower().strip("'’") in DRAWL or "'" in w or "’" in w or w.lower().endswith("in'") for w in words)
        if drawl or not (swaps and len(words) <= 3):
            return False
    replaced = [m.removeprefix("replaces: ") for m in item["source_meanings"] if m.startswith("replaces: ")]
    if len(words) >= 6 or (not replaced and len(words) > 3):
        return False
    spelling = len(words) == 1 and replaced and all(
        len(r.split()) == 1 and difflib.SequenceMatcher(a=r.lower(), b=words[0].lower()).ratio() > 0.8 for r in replaced)
    return not spelling


def english_words(d) -> frozenset[str]:
    """Common English words: the bundled model's whole-word vocabulary, less the dictionary's own slang."""
    from aussiefy.static import bundled

    slang = {w.lower() for e in d.entries.values() for f in e.all_forms for w in f.split()}
    model = bundled()
    return frozenset(t for t in (model.vocab if model else ()) if t.isalpha() and t not in slang)


def main() -> None:
    d = load_dictionary()
    english = d.plain_words | english_words(d)
    items = [i for i in yaml.safe_load(HARVEST.read_text(encoding="utf-8")) if keep(i, english)]
    out = []
    for i in items:
        texts = sorted({s.split(":", 1)[1] for s in i["sources"]})
        out.append({"term": i["form"], "texts": len(texts), "by": sorted({s.split(":", 1)[0] for s in i["sources"]}),
                    "meanings": i["source_meanings"][:6], "examples": i["usage"][:4], "from_texts": texts[:6]})
    out.sort(key=lambda c: (-c["texts"], c["term"].lower()))
    (HERE / "candidates.yaml").write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=120),
                                          encoding="utf-8")
    lines = []
    for cid, c in sorted(d.concepts.items()):
        forms = sorted({e.form for e in d.entries.values() if cid in e.concept})
        trig = "; ".join(f"{fr}: {', '.join(ts)}" for fr, ts in c.triggers.items())
        lines.append(f"{cid}: {c.description}\n  triggers: {trig}\n  forms: {', '.join(forms) or '-'}")
    (HERE / "existing_forms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for n in range(SLICES):
        (HERE / "verify" / f"slice-{n}.yaml").write_text(
            yaml.safe_dump(out[n::SLICES], sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(f"{len(out)} of {len(yaml.safe_load(HARVEST.read_text(encoding='utf-8')))} candidates kept, "
          f"{SLICES} slices of ~{len(out) // SLICES}")


if __name__ == "__main__":
    main()
