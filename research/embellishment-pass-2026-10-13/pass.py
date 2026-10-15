"""The third everyday pass: the embellishment dial. The first pass's 59 texts, levels and seed; yarn mode at each
setting (deadset, dinkum, troppo), the engine at the genre's own, and the first pass's unharnessed retellings,
judged blind together under the same rubric version, so a setting's scores line up against the unharnessed
agent's and against the earlier passes.

    python pass.py prepare     # texts/NAME/: engine output, its verify report, the original, the unharnessed copy
    python pass.py packets     # once every yarn-SETTING.txt exists: blind packets (five candidates each)
    python pass.py collect     # once the reports exist: verdicts, tallies, verify counts, summary.json
    python pass.py compare     # this pass against the second, by candidate
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / "everyday-pass-2026-10-12"
SECOND = HERE.parent / "everyday-pass-2026-10-13"
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

SETTINGS = ("deadset", "dinkum", "troppo")

# the first pass's steps, pointed at this directory, with this pass's candidates
_spec = importlib.util.spec_from_file_location("first_pass", FIRST / "pass.py")
first = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(first)
first.HERE, first.TEXTS, first.BLIND = HERE, HERE / "texts", HERE / "judge-blind"
first.CANDIDATES = ("engine", *(f"yarn-{s}" for s in SETTINGS), "unharnessed")


def prepare() -> None:
    """The first pass's plan again (the same texts at the same levels), with the genre each reads as."""
    from aussiefy.genre import text_genre
    from aussiefy.markup import mask

    first.prepare()
    old = {it["name"]: it["level"] for it in yaml.safe_load((FIRST / "manifest.yaml").read_text(encoding="utf-8"))}
    items = first.items()
    if old != {it["name"]: it["level"] for it in items}:
        sys.exit("the plan differs from the first pass's")
    for it in items:
        d = first.TEXTS / it["name"]
        shutil.copy(FIRST / "texts" / it["name"] / "unharnessed.txt", d / "unharnessed.txt")
        source = (ROOT / it["source"]).read_text(encoding="utf-8")
        (d / f"original{Path(it['source']).suffix}").write_text(source, encoding="utf-8")
        m = mask(source, it["markup"])
        g = text_genre(m.prose(), m.source)
        it["genre"], it["default_embellishment"] = g.name, g.setting().name
    (HERE / "manifest.yaml").write_text(yaml.safe_dump(items, sort_keys=False), encoding="utf-8")
    print("unharnessed retellings copied from the first pass; genres recorded")


def compare() -> None:
    """Mean and criteria by candidate, this pass beside the second (summary.json has them by group too)."""
    b = json.loads((SECOND / "summary.json").read_text(encoding="utf-8"))
    c = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    crit = list(c["overall"]["engine"]["scores"])
    lines = ["| candidate | pass | mean | first | " + " | ".join(crit) + " |", "|---" * (4 + len(crit)) + "|"]
    rows = [("engine", "second", b), ("yarn", "second", b), ("unharnessed", "second", b)]
    rows += [(cand, "third", c) for cand in first.CANDIDATES]
    for cand, label, run in rows:
        x = run["overall"].get(cand, {})
        scores = " | ".join(str(x.get("scores", {}).get(k, "-")) for k in crit)
        lines.append(f"| {cand} | {label} | {x.get('mean', '-')} | {x.get('first', '-')} | {scores} |")
    (HERE / "COMPARE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    {"prepare": prepare, "packets": first.packets, "collect": first.collect, "compare": compare}[sys.argv[1]]()
