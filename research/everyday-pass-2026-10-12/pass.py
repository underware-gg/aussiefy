"""The first manual pass over the everyday corpus: engine, yarn mode and an unharnessed retelling of each text,
judged blind, with what the retellings say that the dictionary can't harvested for a round.

    python pass.py prepare     # texts/NAME/: the engine's output and verify report, briefs for the agents
    python pass.py packets     # once yarn.txt and unharnessed.txt exist: blind packets for the judges
    python pass.py collect     # once the reports exist: verdicts, tallies, verify counts, harvest, SUMMARY.md

Each text gets one level, round-robin 2-5 over the sorted list (vulgarity: the level's own), so the pass
covers the dial instead of sitting at full strength. Everything is deterministic given the agents' files.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from aussiefy import harness, judge  # noqa: E402
from aussiefy.engine import default_translator  # noqa: E402
from aussiefy.loader import load_dictionary  # noqa: E402
from aussiefy.scrape.harvest import harvest  # noqa: E402
from aussiefy.scrape.normalise import Staged  # noqa: E402

EVERYDAY = ROOT / "tests" / "corpus" / "everyday"
INTERFOLD = ["learn_use_cases", "faq_fold_token", "faq_auction", "build_hello_world"]
LEVELS = [2, 3, 4, 5]
SEED = 1
TEXTS, BLIND = HERE / "texts", HERE / "judge-blind"
CANDIDATES = ("engine", "yarn", "unharnessed")


def sources() -> list[tuple[str, str, Path]]:
    """(name, group, path) for every text in the pass."""
    out = [(f"{p.parent.name}__{p.stem}", p.parent.name, p) for p in sorted(EVERYDAY.glob("*/*"))
           if p.suffix in (".txt", ".md")]
    out += [(f"interfold__{n}", "interfold", EVERYDAY / "interfold" / f"{n}.mdx") for n in INTERFOLD]
    return out


def plan() -> list[dict]:
    return [{"name": name, "group": group, "source": str(path.relative_to(ROOT)), "level": LEVELS[i % 4],
             "markup": {".mdx": "mdx", ".md": "markdown"}.get(path.suffix, "text")}
            for i, (name, group, path) in enumerate(sources())]


def prepare() -> None:
    tr = default_translator()
    items = plan()
    for it in items:
        d = TEXTS / it["name"]
        d.mkdir(parents=True, exist_ok=True)
        original = (ROOT / it["source"]).read_text(encoding="utf-8")
        engine = harness.translate(original, level=it["level"], seed=SEED, markup=it["markup"], translator=tr)
        it["vulgarity"] = engine["vulgarity"]
        (d / "engine.txt").write_text(engine["text"], encoding="utf-8")
        report = harness.verify(engine["text"], original=original, level=it["level"], markup=it["markup"],
                                translator=tr)
        (d / "verify-engine.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        (d / "unharnessed-brief.txt").write_text(judge.unharnessed_prompt(
            original, level=it["level"], vulgarity=it["vulgarity"], markup=it["markup"]), encoding="utf-8")
    (HERE / "manifest.yaml").write_text(yaml.safe_dump(items, sort_keys=False), encoding="utf-8")
    print(f"prepared {len(items)} texts -> {TEXTS.relative_to(ROOT)}")


def items() -> list[dict]:
    return yaml.safe_load((HERE / "manifest.yaml").read_text(encoding="utf-8"))


def packets() -> None:
    tr = default_translator()
    rubric = judge.Rubric.load()
    BLIND.mkdir(exist_ok=True)
    missing = []
    for it in items():
        d = TEXTS / it["name"]
        have = {c: (d / f"{c}.txt") for c in CANDIDATES if (d / f"{c}.txt").exists()}
        if len(have) < len(CANDIDATES):
            missing.append(f"{it['name']}: {', '.join(c for c in CANDIDATES if c not in have)}")
            continue
        original = (ROOT / it["source"]).read_text(encoding="utf-8")
        packet = judge.blind(original, {c: p.read_text(encoding="utf-8") for c, p in have.items()},
                             level=it["level"], seed=SEED, translator=tr)
        (d / "packet.json").write_text(json.dumps(packet.to_dict(rubric), indent=1, ensure_ascii=False),
                                       encoding="utf-8")
        view = {k: v for k, v in packet.to_dict(rubric).items() if k in ("instructions", "prompt", "schema")}
        (BLIND / f"{it['name']}.json").write_text(json.dumps(view, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"packets for {len(items()) - len(missing)} texts -> {BLIND.relative_to(ROOT)}")
    for m in missing:
        print(f"  missing {m}")


def collect() -> None:
    tr = default_translator()
    rubric = judge.Rubric.load()
    verdicts, by_level, by_group, bad = [], defaultdict(list), defaultdict(list), []
    checks = defaultdict(lambda: defaultdict(int))
    staged: dict[str, Staged] = {}
    d0 = load_dictionary()
    for it in items():
        d = TEXTS / it["name"]
        original = (ROOT / it["source"]).read_text(encoding="utf-8")
        report_path = BLIND / f"{it['name']}.report.json"
        if (d / "packet.json").exists() and report_path.exists():
            packet = judge.Packet.from_dict(json.loads((d / "packet.json").read_text(encoding="utf-8")))
            try:
                v = judge.read(packet, json.loads(report_path.read_text(encoding="utf-8")), rubric, judge="subagent")
            except judge.BadReport as exc:
                bad.append(f"{it['name']}: {exc}")
            else:
                (d / "verdict.json").write_text(json.dumps(v.to_dict(), indent=1, ensure_ascii=False), encoding="utf-8")
                (d / "card.txt").write_text(v.card() + "\n", encoding="utf-8")
                verdicts.append(v)
                by_level[it["level"]].append(v)
                by_group[it["group"]].append(v)
        for c in CANDIDATES:
            path = d / f"{c}.txt"
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            rep = harness.verify(text, original=original, level=it["level"], markup=it["markup"], translator=tr)
            for sev, n in rep["counts"].items():
                checks[c][sev] += n
            checks[c]["untouched"] += sum(p["kind"] == "untouched" for p in rep["problems"])
            checks[c]["sentences"] += rep["metrics"]["sentences"]
            if c != "engine" and it["markup"] == "text":
                for s in harvest(original, text, d0, source=f"{c}:{it['name']}"):
                    key = s.form.lower()
                    if key in staged:
                        staged[key].source_meanings += [m for m in s.source_meanings if m not in staged[key].source_meanings]
                        staged[key].usage += s.usage
                        staged[key].sources += s.sources
                    else:
                        staged[key] = s
    (HERE / "harvest.yaml").write_text(yaml.safe_dump([s.to_dict() for s in staged.values()], sort_keys=False,
                                                      allow_unicode=True), encoding="utf-8")
    summary = {"overall": judge.tally(verdicts) if verdicts else {},
               "by_level": {lv: judge.tally(vs) for lv, vs in sorted(by_level.items())},
               "by_group": {g: judge.tally(vs) for g, vs in sorted(by_group.items())},
               "verify": {c: dict(v) for c, v in checks.items()}, "bad_reports": bad,
               "harvested": len(staged)}
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("overall", "verify", "bad_reports", "harvested")}, indent=1))


if __name__ == "__main__":
    {"prepare": prepare, "packets": packets, "collect": collect}[sys.argv[1]]()
