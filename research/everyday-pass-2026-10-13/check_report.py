"""Check a judge's report against its packet without unblinding it: prints "ok" or what to fix.

    python check_report.py NAME
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from aussiefy import judge  # noqa: E402

name = sys.argv[1]
packet = judge.Packet.from_dict(json.loads((HERE / "texts" / name / "packet.json").read_text(encoding="utf-8")))
try:
    report = json.loads((HERE / "judge-blind" / f"{name}.report.json").read_text(encoding="utf-8"))
    judge.read(packet, report, judge.Rubric.load(), judge="subagent")
except (OSError, json.JSONDecodeError, judge.BadReport) as exc:
    sys.exit(f"fix: {exc}")
print("ok")
