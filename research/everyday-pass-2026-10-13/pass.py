"""The second everyday pass: the same 59 texts, levels and seed as the first (research/everyday-pass-2026-10-12),
after the genre, dialect, rails, tagger and yarn work. The engine and yarn mode are run anew; the unharnessed
retellings are the first pass's (they don't depend on the harness), so the comparison isolates the harness.
Judged blind under the same rubric version.

    python pass.py prepare     # texts/NAME/: engine output and verify report, the original, the yarn task;
                               # unharnessed.txt copied from the first pass
    python pass.py packets     # once every yarn.txt exists: blind packets for the judges
    python pass.py collect     # once the reports exist: verdicts, tallies, verify counts, summary.json
    python pass.py compare     # this pass against the first, by candidate, level and group
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
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# the first pass's steps, pointed at this directory: one pipeline, two runs
_spec = importlib.util.spec_from_file_location("first_pass", FIRST / "pass.py")
first = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(first)
first.HERE, first.TEXTS, first.BLIND = HERE, HERE / "texts", HERE / "judge-blind"



def prepare() -> None:
    """The first pass's plan run again; the texts must be the same ones, at the same levels."""
    first.prepare()
    old = {it["name"]: it["level"] for it in yaml.safe_load((FIRST / "manifest.yaml").read_text(encoding="utf-8"))}
    new = {it["name"]: it["level"] for it in first.items()}
    if old != new:
        sys.exit(f"the plan differs from the first pass's: {sorted(set(old) ^ set(new))}")
    for it in first.items():
        d = first.TEXTS / it["name"]
        shutil.copy(FIRST / "texts" / it["name"] / "unharnessed.txt", d / "unharnessed.txt")
        (d / f"original{Path(it['source']).suffix}").write_text((ROOT / it["source"]).read_text(encoding="utf-8"),
                                                                encoding="utf-8")
    print("unharnessed retellings copied from the first pass")


def compare() -> None:
    a = json.loads((FIRST / "summary.json").read_text(encoding="utf-8"))
    b = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    crit = list(a["overall"]["engine"]["scores"])
    lines = ["| candidate | pass | mean | first | " + " | ".join(crit) + " |", "|---" * (4 + len(crit)) + "|"]
    for c in first.CANDIDATES:
        for label, run in (("first", a), ("second", b)):
            x = run["overall"].get(c, {})
            scores = " | ".join(str(x.get("scores", {}).get(k, "-")) for k in crit)
            lines.append(f"| {c} | {label} | {x.get('mean', '-')} | {x.get('first', '-')} | {scores} |")
    lines += ["", "| level | " + " | ".join(f"{c} first / second" for c in first.CANDIDATES) + " |",
              "|---" * (1 + len(first.CANDIDATES)) + "|"]
    for lv in sorted(a["by_level"]):
        cells = [f"{a['by_level'][lv].get(c, {}).get('mean', '-')} / {b['by_level'].get(lv, {}).get(c, {}).get('mean', '-')}"
                 for c in first.CANDIDATES]
        lines.append(f"| {lv} | " + " | ".join(cells) + " |")
    lines += ["", "| verify | first pass | this pass |", "|---|---|---|"]
    for c in first.CANDIDATES:
        lines.append(f"| {c} | {a['verify'].get(c)} | {b['verify'].get(c)} |")
    (HERE / "COMPARE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    step = sys.argv[1]
    {"prepare": prepare, "packets": first.packets, "collect": first.collect, "compare": compare}[step]()
