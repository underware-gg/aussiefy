"""The research comparison binds accepted writer evidence to immutable blind packets."""

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from aussiefy import Translator, judge
from aussiefy.yarn import brief, dispatch_tool


@pytest.fixture
def study(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "research/document-refinement-2026-10-15/study.py"
    spec = importlib.util.spec_from_file_location("refinement_study", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "RUN", tmp_path / "study")
    monkeypatch.setattr(module, "HERE", tmp_path)
    monkeypatch.setattr(module, "PLAN", tmp_path / "plan.yaml")
    monkeypatch.setattr(module.subprocess, "check_output", lambda *a, **k: "fixture-commit\n")
    source = tmp_path / "source.txt"
    source.write_text("The package works.\n")
    item = {"name": "case", "source": "source.txt", "source_sha256": module.digest(source),
            "policy": {"level": 1, "vulgarity": 0, "seed": 1, "embellishment": "dinkum",
                       "document_type": "general", "document_config": {}, "markup": "text"},
            "anchors": {name: {"path": "source.txt", "sha256": module.digest(source)}
                        for name in ("anchor-one", "anchor-two")}}
    module.PLAN.write_text(yaml.safe_dump({"rubric_version": 3, "cases": [item]}))
    module.prepare()
    d = module.RUN / "texts/case"
    session = brief(source.read_text(), translator=Translator(lookup_embedder="bundled"), **item["policy"])
    text = source.read_text().strip()
    rows = []
    for step, args in [("lint", {"text": text}), ("submit", {"text": text, "declined": []})]:
        result, accepted = dispatch_tool(session, step, args)
        rows.append({"step": step, "args": args, "result": result})
    assert accepted
    (d / "current.txt").write_text(text + "\n")
    (d / "tools.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return module


def write_report(study):
    packet = judge.Packet.from_dict(json.loads((study.RUN / "texts/case/packet.json").read_text()))
    rubric = judge.Rubric.load()
    report = {"candidates": {label: {"scores": {c.id: {"score": 3, "evidence": "The package works."}
                                               for c in rubric.criteria},
                                     "problems": [], "summary": "Grammatical and faithful."}
                              for label in packet.candidates},
              "rankings": {name: [list(packet.candidates)] for name in rubric.compared}}
    study.write(study.RUN / "judge-blind/case.report.json", report)


def test_replay_and_identical_packet_regeneration_preserve_issued_evidence(study):
    study.packets()
    write_report(study)
    paths = [study.RUN / "texts/case/packet.json", study.RUN / "packets-manifest.json",
             study.RUN / "judge-blind/case.json", study.RUN / "judge-blind/case.report.json"]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    study.packets()
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths] == before
    study.check("case")
    study.collect()
    assert json.loads((study.HERE / "study-summary.json").read_text())["cases"] == 1


@pytest.mark.parametrize("relative", ["texts/case/original.txt", "texts/case/brief.json",
                                    "texts/case/policy.json", "texts/case/current.txt",
                                    "texts/case/tools.jsonl", "texts/case/packet.json",
                                    "judge-blind/case.json"])
def test_changed_writer_or_issued_packet_evidence_is_rejected(study, relative):
    study.packets()
    write_report(study)
    path = study.RUN / relative
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        study.check("case")


def test_changed_pinned_source_is_rejected(study):
    study.packets()
    (study.ROOT / "source.txt").write_text("An entirely different original.\n")
    with pytest.raises(ValueError, match="pinned input changed"):
        study.check("case")


def test_false_accepted_claim_is_rejected_by_canonical_replay(study):
    d = study.RUN / "texts/case"
    row = {"step": "submit", "args": {"text": "", "declined": []},
           "result": {"accepted": True, "problems": []}}
    (d / "current.txt").write_text("")
    (d / "tools.jsonl").write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="diagnostics do not replay"):
        study.packets()


def test_changed_packet_cannot_replace_an_issued_one(study):
    study.packets()
    path = study.RUN / "texts/case/packet.json"
    changed = path.read_bytes() + b" "
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="issued evidence changed"):
        study.packets()
    assert path.read_bytes() == changed


def test_changed_report_cannot_replace_collected_evidence(study):
    study.packets()
    write_report(study)
    study.collect()
    path = study.RUN / "judge-blind/case.report.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="issued evidence changed"):
        study.collect()


def test_pinned_rubric_must_match_loaded_rubric(study):
    data = yaml.safe_load(study.PLAN.read_text())
    data["rubric_version"] = 2
    study.PLAN.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="rubric versions differ"):
        study.plan()


@pytest.mark.parametrize("suffix", ["yaml", "yml"])
def test_new_engine_file_invalidates_frozen_experiment(study, suffix):
    added = study.ROOT / f"aussiefy/data/entries/added.{suffix}"
    added.parent.mkdir(parents=True)
    added.write_text("[]\n")
    with pytest.raises(ValueError, match="engine files changed"):
        study.manifest()


def test_invalid_report_does_not_poison_first_collection(study):
    study.packets()
    study.write(study.RUN / "judge-blind/case.report.json", {})
    with pytest.raises(judge.BadReport):
        study.collect()
    assert not (study.RUN / "reports-manifest.json").exists()
    write_report(study)
    study.collect()
    assert (study.RUN / "reports-manifest.json").is_file()
