"""Prepare fresh yarn briefs, blind independent reports, and validate/tally the pinned comparison.

    python research/document-refinement-2026-10-15/study.py prepare
    python research/document-refinement-2026-10-15/study.py packets
    python research/document-refinement-2026-10-15/study.py check CASE
    python research/document-refinement-2026-10-15/study.py collect
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from aussiefy import harness, judge  # noqa: E402
from aussiefy.engine import Translator  # noqa: E402
from aussiefy.yarn import brief, dispatch_tool  # noqa: E402

PLAN = ROOT / "research/maintenance-check-2026-10-15/retelling-study.yaml"
RUN = HERE / "study"


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def frozen(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"issued evidence changed: {path}")
    else:
        with path.open("xb") as f:
            f.write(content)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan() -> dict:
    data = yaml.safe_load(PLAN.read_text())
    if data["rubric_version"] != judge.Rubric.load().version:
        raise ValueError("pinned plan and loaded rubric versions differ")
    return data


def cases() -> list[dict]:
    return plan()["cases"]


def checked(path: str, expected: str) -> Path:
    p = ROOT / path
    if digest(p) != expected:
        raise ValueError(f"pinned input changed: {path}")
    return p


def engine_snapshot() -> dict[str, str]:
    package = ROOT / "aussiefy"
    files = set(package.rglob("*.py"))
    files.update(p for p in (package / "data").rglob("*") if p.is_file())
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)}


def prepare() -> None:
    if (RUN / "manifest.json").exists():
        raise ValueError("study already prepared; retain its evidence rather than overwrite it")
    tr = Translator(lookup_embedder="bundled")
    manifest = []
    for item in cases():
        source = checked(item["source"], item["source_sha256"])
        for anchor in item["anchors"].values():
            checked(anchor["path"], anchor["sha256"])
        d = RUN / "texts" / item["name"]
        d.mkdir(parents=True, exist_ok=True)
        session = brief(source.read_text(), translator=tr, **item["policy"])
        frozen(d / "brief.json", encoded({"system": session.system, "payload": session.payload}))
        frozen(d / "original.txt", source.read_bytes())
        frozen(d / "policy.json", encoded(item["policy"]))
        manifest.append({**item, "brief_sha256": digest(d / "brief.json"),
                         "policy_sha256": digest(d / "policy.json")})
    write(RUN / "manifest.json", {"source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "plan_sha256": digest(PLAN),
        "driver_sha256": digest(Path(__file__)),
        "rubric_version": judge.Rubric.load().version, "engine_files": engine_snapshot(), "cases": manifest,
        "writer": "fresh Codex agent contexts using yarn tools; no historical candidates shown",
        "judge": "independent fresh Codex agent contexts; candidate names withheld"})
    print(f"prepared {len(manifest)} fresh briefs")


def manifest() -> dict:
    data = json.loads((RUN / "manifest.json").read_text())
    checked(str(PLAN.relative_to(ROOT)), data["plan_sha256"])
    if digest(Path(__file__)) != data["driver_sha256"]:
        raise ValueError("study driver changed after freeze")
    if engine_snapshot() != data["engine_files"]:
        raise ValueError("engine files changed after freeze")
    return data


def evidence(item: dict, tr: Translator) -> dict:
    d = RUN / "texts" / item["name"]
    source = checked(item["source"], item["source_sha256"])
    for anchor in item["anchors"].values():
        checked(anchor["path"], anchor["sha256"])
    expected = {"original.txt": item["source_sha256"], "brief.json": item["brief_sha256"],
                "policy.json": item["policy_sha256"]}
    for name, sha in expected.items():
        if digest(d / name) != sha:
            raise ValueError(f"writer evidence changed: {item['name']}/{name}")
    session = brief(source.read_text(), translator=tr, **item["policy"])
    if encoded({"system": session.system, "payload": session.payload}) != (d / "brief.json").read_bytes():
        raise ValueError(f"brief cannot be reproduced: {item['name']}")
    if encoded(item["policy"]) != (d / "policy.json").read_bytes():
        raise ValueError(f"policy differs from pinned plan: {item['name']}")
    text = (d / "current.txt").read_text()
    log = [json.loads(line) for line in (d / "tools.jsonl").read_text().splitlines()]
    matched = False
    for row in log:
        actual, accepted = dispatch_tool(session, row["step"], row["args"])
        if actual != row["result"]:
            raise ValueError(f"tool diagnostics do not replay: {item['name']}/{row['step']}")
        if accepted and row["args"]["text"] == text.strip():
            matched = True
    if not matched:
        raise ValueError(f"output has no replayed accepted submission: {item['name']}")
    return {name: digest(d / name) for name in (*expected, "current.txt", "tools.jsonl")}


def issued(item: dict, tr: Translator, bindings: dict) -> None:
    d = RUN / "texts" / item["name"]
    actual = {**evidence(item, tr), "packet.json": digest(d / "packet.json"),
              "judge_packet": digest(RUN / "judge-blind" / f"{item['name']}.json")}
    if actual != bindings[item["name"]]:
        raise ValueError(f"issued packet evidence changed: {item['name']}")


def packets() -> None:
    data = manifest()
    rubric = judge.Rubric.load()
    tr = Translator(lookup_embedder="bundled")
    bindings = {}
    for index, item in enumerate(data["cases"]):
        d = RUN / "texts" / item["name"]
        current = d / "current.txt"
        bound = evidence(item, tr)
        values = {"current": current.read_text(), **{name: checked(a["path"], a["sha256"]).read_text()
                    for name, a in item["anchors"].items()}}
        packet = judge.blind(checked(item["source"], item["source_sha256"]).read_text(), values,
                             level=item["policy"]["level"], vulgarity=item["policy"]["vulgarity"], seed=71 + index)
        frozen(d / "packet.json", encoded(packet.to_dict(rubric)))
        blind = RUN / "judge-blind" / f"{item['name']}.json"
        frozen(blind, encoded({
            "rubric_version": rubric.version, "instructions": rubric.text(), "prompt": packet.prompt(),
            "schema": packet.schema(rubric)}))
        bindings[item["name"]] = {**bound, "packet.json": digest(d / "packet.json"),
                                  "judge_packet": digest(blind)}
    frozen(RUN / "packets-manifest.json", encoded(bindings))
    print(f"prepared {len(data['cases'])} key-free blind packets")


def report(item: dict, tr: Translator, bindings: dict) -> judge.Verdict:
    name = item["name"]
    issued(item, tr, bindings)
    d = RUN / "texts" / name
    packet = judge.Packet.from_dict(json.loads((d / "packet.json").read_text()))
    report = json.loads((RUN / "judge-blind" / f"{name}.report.json").read_text())
    result = judge.read(packet, report, judge="independent Codex agent; blind rubric3")
    print(f"{name}: ok")
    return result


def check(name: str) -> judge.Verdict:
    data = manifest()
    item = next((item for item in data["cases"] if item["name"] == name), None)
    if item is None:
        raise ValueError(f"unknown study case {name!r}")
    bindings = json.loads((RUN / "packets-manifest.json").read_text())
    return report(item, Translator(lookup_embedder="bundled"), bindings)


def collect() -> None:
    data = manifest()
    verdicts = []
    checks = {}
    tr = Translator(lookup_embedder="bundled")
    bindings = json.loads((RUN / "packets-manifest.json").read_text())
    report_hashes = {item["name"]: digest(RUN / "judge-blind" / f"{item['name']}.report.json")
                     for item in data["cases"]}
    for item in data["cases"]:
        result = report(item, tr, bindings)
        verdicts.append(result)
    frozen(RUN / "reports-manifest.json", encoded({"packets_manifest_sha256": digest(
        RUN / "packets-manifest.json"), "reports": report_hashes}))
    for item, result in zip(data["cases"], verdicts, strict=True):
        d = RUN / "texts" / item["name"]
        write(d / "verdict.json", result.to_dict())
        policy = {k: v for k, v in item["policy"].items() if k != "seed"}
        verification = harness.verify((d / "current.txt").read_text(), original=(d / "original.txt").read_text(),
                                      translator=tr, **policy)
        write(d / "verify.json", verification)
        checks[item["name"]] = {"ok": verification["ok"], "counts": verification["counts"],
            "output_sha256": digest(d / "current.txt"), "report_sha256": digest(
                RUN / "judge-blind" / f"{item['name']}.report.json")}
    write(HERE / "study-summary.json", {"status": "completed", "source_commit": data["source_commit"],
        "rubric_version": data["rubric_version"], "cases": len(verdicts), "tally": judge.tally(verdicts),
        "verification": checks,
        "limits": "One independent blind report per text; different current and historical writer contexts. "
                  "This is a bounded comparison, not an isolated causal test of engine or model quality."})
    print(json.dumps(judge.tally(verdicts), indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "packets", "check", "collect"))
    p.add_argument("name", nargs="?")
    args = p.parse_args()
    if args.action == "check":
        check(args.name)
    else:
        {"prepare": prepare, "packets": packets, "collect": collect}[args.action]()
