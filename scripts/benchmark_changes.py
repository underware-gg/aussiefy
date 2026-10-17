"""Measure what the `changes` builder costs over a plain translation, at 5,000 characters (the budget: 1.5x).

Run from an installed development checkout: python scripts/benchmark_changes.py [--repeats 7] [--output report.json]
Each timing is one fresh request: translate_changes against translate on the same text, warm, the median of the
repeats. The texts are the everyday corpus's conversational, instructions and news groups, each half concatenated
and cut at a sentence near 5,000 characters. Absolute times depend on the machine and its load; the ratios hold.
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
STRESS = {"stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6},
          "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10}, "garnish_gap": 0,
          "swearing": {"infix": 6.0, "exclaim": 0.5}}
SETTINGS = {
    "site default (larrikin, dinkum, dad)": {"level": 4, "vulgarity": 1},
    "swaggie, troppo, tradie": {"level": 5, "vulgarity": 3, "embellishment": 2},
    "stress (every garnish, stacks, infixes)": {"level": 5, "vulgarity": 2, "embellishment": 2,
                                                "document_config": {"profile": STRESS}},
}


def cut(text: str, n: int) -> str:
    """text cut at the last sentence end before n characters (or at n, if none is past halfway)."""
    if len(text) <= n:
        return text
    head = text[:n]
    k = max(head.rfind(". "), head.rfind(".\n"), head.rfind("? "), head.rfind("! "))
    return head[:k + 1] if k > n // 2 else head


def texts(size: int = 5000) -> list[tuple[str, str]]:
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


def median_seconds(fn, repeats: int) -> float:
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def measure(repeats: int = 7, size: int = 5000, translator: Translator | None = None) -> list[dict]:
    tr = translator or Translator(lookup_embedder=None)
    rows = []
    for setting, options in SETTINGS.items():
        for name, text in texts(size):
            translate(text, translator=tr, **options)
            built = translate_changes(text, translator=tr, **options)
            plain = median_seconds(lambda: translate(text, translator=tr, **options), repeats)
            changes = median_seconds(lambda: translate_changes(text, translator=tr, **options), repeats)
            rows.append({"setting": setting, "text": name, "characters": len(text),
                         "translate_ms": round(plain * 1e3, 1), "changes_ms": round(changes * 1e3, 1),
                         "ratio": round(changes / plain, 3),
                         "renderings": sum(len(c["alternatives"]) + len(c["locked"]) for c in built.changes)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--size", type=int, default=5000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = measure(args.repeats, args.size)
    summary = {}
    for setting in SETTINGS:
        ratios = [r["ratio"] for r in rows if r["setting"] == setting]
        summary[setting] = {"median": round(statistics.median(ratios), 2), "max": round(max(ratios), 2)}
    for r in rows:
        print(f"{r['setting'][:24]:24} {r['text']:16} translate {r['translate_ms']:7.1f} ms   changes "
              f"{r['changes_ms']:7.1f} ms   {r['ratio']:.2f}x   {r['renderings']} renderings")
    for setting, s in summary.items():
        print(f"{setting}: median {s['median']:.2f}x, at most {s['max']:.2f}x (budget {BUDGET}x)")
    if args.output:
        args.output.write_text(json.dumps({"budget": BUDGET, "summary": summary, "rows": rows}, indent=1) + "\n",
                               encoding="utf-8")
    return 0 if all(s["median"] <= BUDGET for s in summary.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
