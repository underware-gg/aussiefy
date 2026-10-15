"""A check on dinkum's voice after the fourth pass: the fourth pass found the new dinkum as good as the third
pass's but less Aussie (register 4.19 against 4.51), most in official prose and news. Its fix was dinkum's
guidance (voice in the connecting prose of strict forms) and the fourth-pass dictionary round. This pass retells
the fourth pass's news and official texts at dinkum again and judges three candidates blind, under the same
rubric version:

- yarn-dinkum: yarn mode by hand now;
- dinkum-4: the fourth pass's yarn-dinkum, unchanged;
- dinkum-3: the third pass's yarn-dinkum, unchanged.

    python pass.py prepare     # texts/NAME/: the original and the two fixed candidates
    python pass.py packets     # once every yarn-dinkum.txt exists: blind packets (three candidates each)
    python pass.py collect     # once the reports exist: verdicts, tallies, summary.json
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / "everyday-pass-2026-10-12"
THIRD = HERE.parent / "embellishment-pass-2026-10-13"
FOURTH = HERE.parent / "fourth-pass-2026-10-14"
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
GENRES = ("news", "official")

_spec = importlib.util.spec_from_file_location("first_pass", FIRST / "pass.py")
first = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(first)
first.HERE, first.TEXTS, first.BLIND = HERE, HERE / "texts", HERE / "judge-blind"
first.CANDIDATES = ("yarn-dinkum", "dinkum-4", "dinkum-3")


def prepare() -> None:
    """The fourth pass's news and official texts, at its levels, with its and the third pass's dinkum."""
    items = [it for it in yaml.safe_load((FOURTH / "manifest.yaml").read_text(encoding="utf-8"))
             if it["genre"] in GENRES]
    for it in items:
        d = first.TEXTS / it["name"]
        d.mkdir(parents=True, exist_ok=True)
        src = FOURTH / "texts" / it["name"]
        shutil.copy(src / "yarn-dinkum.txt", d / "dinkum-4.txt")
        shutil.copy(THIRD / "texts" / it["name"] / "yarn-dinkum.txt", d / "dinkum-3.txt")
        original = next(src.glob("original.*"))
        shutil.copy(original, d / original.name)
    (HERE / "manifest.yaml").write_text(yaml.safe_dump(items, sort_keys=False), encoding="utf-8")
    print(f"prepared {len(items)} texts ({', '.join(GENRES)})")


if __name__ == "__main__":
    {"prepare": prepare, "packets": first.packets, "collect": first.collect}[sys.argv[1]]()
