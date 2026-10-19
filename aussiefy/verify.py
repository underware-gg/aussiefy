"""Verify a translation against its original: a log of potential problems, each with a severity.

Deterministic: the same pair and policy always give the same report, and it costs nothing to run, so it suits
a person checking one translation, an agent checking its own, and the hill climb scoring thousands. It works
on any translation (the engine's, a yarn, a person's), because it reads only the two texts.

What it can see: policy and craft breaches (lint), lost facts and lost markup (fidelity, markup_changed), and
sentence-level structure: an original sentence nothing near it in the translation says again, in words or in
meaning (unmatched: dropped, or reworded past recognition), and long sentences left exactly as they were
(untouched, for the coverage metric). It can't judge tone, flow or whether a swap took the right sense; that
is the judge's work.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .engine import UNTOUCHED_MIN_WORDS, Translator, default_translator
from .lint import lint
from .markup import mask
from .align import content_words, sentence_texts, counterparts

SEVERITIES = ("critical", "major", "minor", "info")
# what each kind of problem costs a translation: critical breaks the document or the facts, major breaks the
# brief (the level's policy, Australian English), minor is a craft weakness worth a look
# every kind lint can report has one (tests/test_verify.py checks): a new kind must be given its severity here
SEVERITY = {
    "markup_changed": "critical", "number_dropped": "critical", "empty": "critical", "unmatched": "minor",
    "too_vulgar": "major", "dialect": "major", "spelling": "major", "flagged": "major",
    "too_short": "major", "document_changed": "major", "semantic_effect": "major",
    "predicate_composition": "major", "semantic_degree": "major",
    "swear_overuse": "minor", "swear_density": "minor", "tag_in_narration": "minor", "tag_overuse": "minor",
    "pile_up": "minor", "repeated": "minor", "repeated_phrase": "minor", "stock_opener": "minor", "stock_closer": "minor",
    "too_long": "minor", "name_added": "minor", "name_dropped": "minor", "untouched": "info",
}
# unmatched: an original sentence whose best counterpart keeps under a quarter of its content words AND means
# little the same to the meaning model. Calibrated on the 2026-10-11 retellings (374 aligned pairs): 5% of true
# counterparts score under 0.44, while 30% of wrong sentences from the same story score under 0.35
# below local (level 3) the brief is light, so a sentence left as it was is expected, not worth a note
UNTOUCHED_MIN_LEVEL = 3
UNMATCHED_RETAINED = 0.25
UNMATCHED_SIMILARITY = 0.35
@dataclass(frozen=True)
class Problem:
    severity: str
    kind: str
    phrase: str
    why: str
    sentence: int | None = None     # the original sentence it concerns, when there is one

    def to_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "kind": self.kind, "phrase": self.phrase, "why": self.why,
                **({"sentence": self.sentence} if self.sentence is not None else {})}


def verify(text: str, *, original: str, level: int | str = 5, vulgarity: int | str | None = None,
           markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
              document_type: str = "general", document_config: dict | None = None,
           translator: Translator | None = None) -> dict[str, Any]:
    """Problems in text as a translation of original, worst first, each with a severity: critical (broke the
    document or a fact), major (breaks the brief: the policy, Australian English), minor (craft, or a hint
    worth a look), info (coverage); and metrics that put them in proportion. ok is true with no critical or
    major problem. markup (markdown, mdx, auto) reads the prose only and checks the markup came through.
    english (us, uk, auto, none) is the original's English, for its US and British words; embellishment
    (deadset, dinkum, troppo; None = the selected document type's default) how much longer than the original it may run."""
    tr = translator or default_translator()
    eff = tr.effective(level=level, vulgarity=vulgarity, document_config=document_config)
    checked = lint(text, original=original, level=level, vulgarity=vulgarity, markup=markup,
                   english=english, embellishment=embellishment, document_type=document_type, document_config=document_config, translator=tr, suggest=False)
    problems = [Problem(SEVERITY[i["kind"]], i["kind"], i["phrase"],
                        i.get("why") or (f"use {i['australian']}" if i.get("australian") else "fix it"))
                for i in checked["issues"]]
    problems += [Problem(SEVERITY[w["kind"]], w["kind"], w["phrase"], w["why"])
                 for w in checked["warnings"]]

    src, out = sentence_texts(mask(original, markup).prose()), sentence_texts(mask(text, markup).prose())
    emb = tr.lookup_embedder
    for i, c in enumerate(counterparts(src, out, emb)):
        kept = content_words(src[i])
        if c is None:
            break
        if eff.level >= UNTOUCHED_MIN_LEVEL and len(src[i].split()) >= UNTOUCHED_MIN_WORDS and any(
                _same(src[i], t) for t in out[c.start:c.end]):
            problems.append(Problem("info", "untouched", src[i][:120], "left exactly as it was", i))
        # too little to judge in a short line ("Good heavens!"); a good retelling rewords, so without a
        # meaning model few shared words is only a hint
        if len(kept) >= 4 and c.retained < UNMATCHED_RETAINED and (c.similarity is None
                                                                   or c.similarity < UNMATCHED_SIMILARITY):
            near = " ".join(out[c.start:c.end])[:80]
            problems.append(Problem("minor" if emb else "info", "unmatched", src[i][:120],
                                    f"nothing near it in the translation says the same (closest: {near!r}"
                                    + (f", meaning similarity {c.similarity:.2f}" if c.similarity is not None else "")
                                    + "): dropped, or reworded past recognition?", i))
    if not out and src:
        problems.append(Problem("critical", "empty", "", "the translation has no sentences"))

    problems.sort(key=lambda p: (SEVERITIES.index(p.severity), p.sentence if p.sentence is not None else -1))
    counts = {s: sum(p.severity == s for p in problems) for s in SEVERITIES[:3]}
    return {
        "ok": not counts["critical"] and not counts["major"],
        **eff.envelope(),
        **{k: checked[k] for k in ("document_type", "document_type_source", "genre", "genre_scores",
                                  "document_config", "document_overrides")},
        "counts": counts,
        "problems": [p.to_dict() for p in problems],
        "metrics": {"original_words": len(original.split()), "translation_words": len(text.split()),
                    "sentences": len(src), "translation_sentences": len(out),
                    "untouched_share": round(sum(p.kind == "untouched" for p in problems) / len(src), 2) if src else 0.0},
        "scope": "Deterministic checks: policy, spelling, facts, markup, sentence structure. Not judged: tone, "
                 "flow, whether each swap took the right sense (use the judge for those).",
    }


def _same(a: str, b: str) -> bool:
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()   # noqa: E731
    return norm(a) == norm(b)
