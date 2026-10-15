"""Golden outputs per (input, level, seed). Regenerate deliberately with scripts/regen_golden.py."""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from regen_golden import build  # noqa: E402


def test_golden_outputs(translator):
    expected = yaml.safe_load((ROOT / "tests" / "corpus" / "golden.yaml").read_text(encoding="utf-8"))
    actual = build(translator)
    assert [g["input"] for g in actual] == [g["input"] for g in expected], "corpus changed: regenerate golden.yaml"
    diffs = [f"{a['input']!r} {k}:\n    expected {e['outputs'][k]!r}\n    actual   {v!r}"
             for a, e in zip(actual, expected) for k, v in a["outputs"].items() if e["outputs"].get(k) != v]
    assert not diffs, ("output drifted from golden.yaml (run scripts/regen_golden.py if intended):\n"
                       + "\n".join(diffs[:10]))
