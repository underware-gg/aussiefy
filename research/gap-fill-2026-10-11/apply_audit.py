"""Apply verify/audit.yaml's corrections to existing entries, in place (the curated files keep their layout).

    python3 research/gap-fill-2026-10-11/apply_audit.py
"""

import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ENTRIES = HERE.parent.parent / "aussiefy" / "data" / "entries"


def scalar(v) -> str:
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (str, list)) else str(v)


for item in yaml.safe_load((HERE / "verify" / "audit.yaml").read_text()):
    change = item.get("change")
    if not isinstance(change, dict):
        continue
    eid = item["entry_id"]
    for path in sorted(ENTRIES.glob("*.yaml")):
        lines = path.read_text(encoding="utf-8").split("\n")
        try:
            start = lines.index(f"- id: {eid}")
        except ValueError:
            continue
        end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith("  ")), len(lines))
        for key, value in change.items():
            line = f"  {key}: {scalar(value)}"
            at = next((i for i in range(start, end) if re.match(rf"^  {key}:", lines[i])), None)
            if at is None:
                lines.insert(end, line)
                end += 1
            else:
                lines[at] = line
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"{eid}: {', '.join(change)} ({path.name})")
        break
    else:
        print(f"{eid}: not found")
