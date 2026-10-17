"""Measure what the `changes` builder costs over a plain translation, against its budget (1.5x translate).

Run from an installed development checkout: python scripts/benchmark_changes.py [--repeats 7] [--output report.json]

Each text's ratio is translate_changes over translate on the same text, warm, each the median of the repeats, the
two timed in turn (interleaved) in process time, so other load on the machine moves both alike. The gate: every
5,000-character text's ratio is within budget for each setting the website's service allows (its default, the
strongest dials, and every document type it offers). Larger texts (10,000 and 15,000 characters), Markdown
documents and a stress setting (every garnish, stacks and infixes at full rate) are reported, not gated. The texts
are the everyday corpus's conversational, instructions and news groups, each half concatenated and cut at a
sentence near the size.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from aussiefy import translate, translate_changes
from aussiefy.engine import Translator

ROOT = Path(__file__).resolve().parents[1]
EVERYDAY = ROOT / "tests" / "corpus" / "everyday"
BUDGET = 1.5
GATED_SIZE = 5000
SITE = {"level": 4, "vulgarity": 1}   # larrikin, dad, the general document type's dinkum
STRESS = {"stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6},
          "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10}, "garnish_gap": 0,
          "swearing": {"infix": 6.0, "exclaim": 0.5}}
HOSTED_TYPES = ("general", "auto", "story", "personal", "news", "instructions", "technical", "official")
GATED = {"site default (larrikin, dinkum, dad)": SITE,
         "swaggie, troppo, tradie": {"level": 5, "vulgarity": 3, "embellishment": 2},
         **{f"site default, {t}": {**SITE, "document_type": t} for t in HOSTED_TYPES if t != "general"}}
REPORTED = {"stress (every garnish, stacks, infixes)": {"level": 5, "vulgarity": 2, "embellishment": 2,
                                                        "document_config": {"profile": STRESS}}}


def cut(text: str, n: int) -> str:
    """text cut at the last sentence end before n characters (or at n, if none is past halfway)."""
    if len(text) <= n:
        return text
    head = text[:n]
    k = max(head.rfind(". "), head.rfind(".\n"), head.rfind("? "), head.rfind("! "))
    return head[:k + 1] if k > n // 2 else head


def texts(size: int = GATED_SIZE) -> list[tuple[str, str]]:
    out = []
    for group in ("conversational", "instructions", "news"):
        files = sorted((EVERYDAY / group).glob("*.txt"))
        for half, part in (("a", files[: len(files) // 2]), ("b", files[len(files) // 2:])):
            text = ""
            for f in part:
                text += f.read_text(encoding="utf-8").strip() + "\n\n"
                if len(text) > size + 1000:
                    break
            out.append((f"{group}-{half}", cut(text, size)))
    return out


def documents(size: int = GATED_SIZE, n: int = 4) -> list[tuple[str, str]]:
    return [(p.name, cut(p.read_text(encoding="utf-8"), size)) for p in sorted(EVERYDAY.rglob("*.md"))[:n]]


def ratio(text: str, options: dict, repeats: int, tr: Translator) -> dict:
    """translate and translate_changes on one text, timed in turn (process time), and the ratio of their medians."""
    translate(text, translator=tr, **options)
    built = translate_changes(text, translator=tr, **options)
    plain, changes = [], []
    for _ in range(repeats):
        for fn, times in ((translate, plain), (translate_changes, changes)):
            start = time.process_time()
            fn(text, translator=tr, **options)
            times.append(time.process_time() - start)
    p, c = statistics.median(plain), statistics.median(changes)
    return {"characters": len(text), "translate_ms": round(p * 1e3, 1), "changes_ms": round(c * 1e3, 1),
            "ratio": round(c / p, 3), "renderings": sum(len(x["alternatives"]) + len(x["locked"]) for x in built.changes)}


def measure(repeats: int = 7, size: int = GATED_SIZE, translator: Translator | None = None,
            larger: tuple[int, ...] = (10000, 15000)) -> list[dict]:
    tr = translator or Translator(lookup_embedder=None)
    rows = []
    for gated, settings in ((True, GATED), (False, REPORTED)):
        for setting, options in settings.items():
            for name, text in texts(size):
                rows.append({"setting": setting, "gated": gated, "text": name, **ratio(text, options, repeats, tr)})
    for n in larger:
        for name, text in texts(n)[::2]:
            rows.append({"setting": f"site default at {n:,} characters", "gated": False, "text": name,
                         **ratio(text, SITE, repeats, tr)})
    for name, text in documents(size):
        rows.append({"setting": "site default, Markdown", "gated": False, "text": name,
                     **ratio(text, {**SITE, "markdown": True}, repeats, tr)})
    return rows


def summary(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        s = out.setdefault(r["setting"], {"gated": r["gated"], "ratios": []})
        s["ratios"].append(r["ratio"])
    return {k: {"gated": v["gated"], "median": round(statistics.median(v["ratios"]), 2), "max": round(max(v["ratios"]), 2)}
            for k, v in out.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--size", type=int, default=GATED_SIZE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = measure(args.repeats, args.size)
    for r in rows:
        print(f"{r['setting'][:40]:40} {r['text'][:28]:28} translate {r['translate_ms']:7.1f} ms   changes "
              f"{r['changes_ms']:7.1f} ms   {r['ratio']:.2f}x   {r['renderings']} renderings")
    totals = summary(rows)
    for setting, s in totals.items():
        print(f"{setting}: median {s['median']:.2f}x, at most {s['max']:.2f}x"
              + (f" (gate: at most {BUDGET}x)" if s["gated"] else " (reported)"))
    passed = all(s["max"] <= BUDGET for s in totals.values() if s["gated"])
    print("gate:", "within budget" if passed else "OVER BUDGET")
    if args.output:
        args.output.write_text(json.dumps({"budget": BUDGET, "passed": passed, "summary": totals, "rows": rows},
                                          indent=1) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
