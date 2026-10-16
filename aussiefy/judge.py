"""The judge: a structured, blind comparison of Aussie translations of one original, as a report card.

Candidates (the engine's output, a yarn, an earlier version, an unharnessed model's retelling ...) are shuffled
under anonymous labels (A, B, C), and a language model scores each against the rubric in data/judge.yaml:
every criterion 1-5 with evidence first, specific problems with verbatim quotes, and rankings. The report is
validated (every score present and in range, every quote really in its candidate, rankings complete) and
unblinded into a Verdict; tally() averages verdicts across texts, which is what the tuning loop compares.

The core is pure and deterministic: blind() makes the packet, read() validates and unblinds a report. The model
is a thin adapter (run(), and unharnessed() for the reference retelling), so the same packet can be judged by
the API, or written to a file for an agent to judge and read back (`aussiefy judge brief` / `judge read`).
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import claude, translation
from .claude import DEFAULT_MODEL
from .engine import Translator, default_translator
from .errors import UserError
from .loader import DATA_DIR
from .markup import detect_markup
from .terms import fold
from .policy import DocumentOverrides
from .profile import PROFILE_KEYS, ProfileOverrides
from .markup import MARKUPS
from .schema import CLASSES, GARNISH_KEYS
from .model import RewriteThresholds, SwearProfile
from .retelling import MARKUP_RULE

SEVERITIES = ("critical", "major", "minor")
PROBLEM_KEYS = ("quote", "original", "severity", "why")   # each a string; "original" empty for an addition
LABELS = "ABCDEFGH"
EVALUATION_PROTOCOL = 2
CONTRACT_GUIDANCE = """
The effective contract overrides generic descriptions of the requested voice. Level measures Australian
vocabulary, idiom and cadence in eligible prose. Level 5 means broad Australian prose; performance and
added garnish depend on the effective embellishment/document settings, not the level alone. Use no
prohibited openings, insults, infixes or other garnish. Empty garnish still permits idiomatic paraphrase
within the original propositions; preserving facts does not require leaving all connecting prose neutral.
Respect exact quotes, protected technical terms, markup and headings where the contract requires them to
stay unchanged. Bold prose labels are not automatically headings. Vulgarity is a cap, not a quota. Disabled
behaviours stay disabled; profile probabilities are not exact output quotas.
"""
CONTRACT_INSTRUCTIONS = ("Apply EVALUATION_CONTRACT to every anonymous candidate.\n" + CONTRACT_GUIDANCE
                         + "Do not penalise required preservation. Keep the eight rubric criteria and score "
                           "each weakness once.")


@dataclass(frozen=True)
class Criterion:
    id: str
    question: str
    anchors: dict[int, str]
    compare: bool = False


@dataclass(frozen=True)
class Rubric:
    version: int
    instructions: str
    criteria: tuple[Criterion, ...]

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Rubric":
        data = yaml.safe_load(Path(path or DATA_DIR / "judge.yaml").read_text(encoding="utf-8"))
        return cls(data["version"], data["instructions"].strip(), tuple(
            Criterion(c["id"], c["question"], {int(k): v for k, v in c["anchors"].items()}, c.get("compare", False))
            for c in data["criteria"]))

    @property
    def compared(self) -> list[str]:
        return [c.id for c in self.criteria if c.compare] + ["overall"]

    def text(self) -> str:
        lines = [self.instructions, "", "CRITERIA"]
        for c in self.criteria:
            lines.append(f"- {c.id}: {c.question}" + (" (also ranked across candidates)" if c.compare else ""))
            lines += [f"    {score}: {anchor}" for score, anchor in sorted(c.anchors.items())]
        return "\n".join(lines)


@dataclass(frozen=True)
class Packet:
    """One blind judgement to make: the original, the brief, and the candidates under their labels."""
    original: str
    level: int
    vulgarity: int
    candidates: dict[str, str]          # label -> text
    names: dict[str, str]               # label -> candidate name (kept from the judge)
    rubric_version: int
    evaluation_contract: dict[str, Any] | None = None

    @property
    def evaluation_protocol(self) -> int:
        return EVALUATION_PROTOCOL if self.evaluation_contract is not None else 1

    def instructions(self, rubric: Rubric) -> str:
        return rubric.text() + ("\n" + CONTRACT_INSTRUCTIONS if self.evaluation_contract is not None else "")

    def judging(self, rubric: Rubric) -> dict[str, Any]:
        """The complete key-free request for either an agent or an API judge."""
        return {"instructions": self.instructions(rubric), "prompt": self.prompt(), "schema": self.schema(rubric)}

    def prompt(self) -> str:
        parts = [f"BRIEF: level {self.level}, vulgarity {self.vulgarity}"]
        if self.evaluation_contract is not None:
            parts += ["", "EVALUATION_CONTRACT (protocol 2):", json.dumps(self.evaluation_contract,
                                                                         ensure_ascii=False, sort_keys=True)]
        parts += ["", "ORIGINAL:", self.original.strip()]
        for label, text in self.candidates.items():
            parts += ["", f"CANDIDATE {label}:", text.strip()]
        return "\n".join(parts)

    def schema(self, rubric: Rubric) -> dict[str, Any]:
        """The report's JSON schema: what the judge must fill in, evidence before score."""
        labels = list(self.candidates)
        score = {"type": "object", "properties": {"evidence": {"type": "string"}, "score": {"type": "integer"}},
                 "required": ["evidence", "score"], "additionalProperties": False}
        problem = {"type": "object", "properties": {
            "quote": {"type": "string"}, "original": {"type": "string"},
            "severity": {"type": "string", "enum": list(SEVERITIES)}, "why": {"type": "string"}},
            "required": list(PROBLEM_KEYS), "additionalProperties": False}
        candidate = {"type": "object", "properties": {
            "scores": {"type": "object", "properties": {c.id: score for c in rubric.criteria},
                       "required": [c.id for c in rubric.criteria], "additionalProperties": False},
            "problems": {"type": "array", "items": problem}, "summary": {"type": "string"}},
            "required": ["scores", "problems", "summary"], "additionalProperties": False}
        # best first, in tiers: candidates the judge can't separate share one
        ranking = {"type": "array", "items": {"type": "array", "items": {"type": "string", "enum": labels}}}
        return {"type": "object", "properties": {
            "candidates": {"type": "object", "properties": {lb: candidate for lb in labels},
                           "required": labels, "additionalProperties": False},
            "rankings": {"type": "object", "properties": {k: ranking for k in rubric.compared},
                         "required": rubric.compared, "additionalProperties": False}},
            "required": ["candidates", "rankings"], "additionalProperties": False}

    def to_dict(self, rubric: Rubric) -> dict[str, Any]:
        """For an agent judging by hand: everything it needs, and the key to unblind it (keep that from it)."""
        return {"rubric_version": self.rubric_version, **self.judging(rubric),
                "original": self.original, "level": self.level, "vulgarity": self.vulgarity,
                "candidates": self.candidates, "key": self.names,
                **({"evaluation_protocol": self.evaluation_protocol, "evaluation_contract": self.evaluation_contract}
                   if self.evaluation_contract is not None else {})}

    @classmethod
    def from_dict(cls, d: dict[str, Any], *, where: str = "judge packet") -> "Packet":
        required = {"original", "level", "vulgarity", "candidates", "key", "rubric_version"}
        if not isinstance(d, dict) or not required <= d.keys():
            raise UserError(f"{where}: packet needs {', '.join(sorted(required))}")
        if (not isinstance(d["original"], str) or type(d["level"]) is not int or d["level"] not in range(1, 6)
                or type(d["vulgarity"]) is not int or d["vulgarity"] not in range(4)
                or type(d["rubric_version"]) is not int or d["rubric_version"] < 1):
            raise UserError(f"{where}: invalid packet text, dials or rubric version")
        candidates, names = d["candidates"], d["key"]
        if (not isinstance(candidates, dict) or not 2 <= len(candidates) <= len(LABELS)
                or any(not isinstance(label, str) or label not in LABELS or len(label) != 1
                       or not isinstance(text, str) for label, text in candidates.items())):
            raise UserError(f"{where}: candidates must map 2–8 blind labels to text")
        if (not isinstance(names, dict) or set(names) != set(candidates)
                or any(not isinstance(name, str) or not name.strip() for name in names.values())
                or len(set(names.values())) != len(names)):
            raise UserError(f"{where}: key must name every candidate exactly once")
        protocol = d.get("evaluation_protocol", 1)
        contract = d.get("evaluation_contract")
        if type(protocol) is not int or protocol not in (1, EVALUATION_PROTOCOL):
            raise UserError(f"{where}: unknown evaluation protocol {protocol!r}")
        if protocol == 1 and contract is not None:
            raise UserError(f"{where}: evaluation_contract requires protocol {EVALUATION_PROTOCOL}")
        if protocol == EVALUATION_PROTOCOL:
            _check_contract(contract, where)
            if (contract["level"], contract["vulgarity"]) != (d["level"], d["vulgarity"]):
                raise UserError(f"{where}: evaluation_contract dials do not match packet")
        return cls(d["original"], d["level"], d["vulgarity"], d["candidates"], d["key"], d["rubric_version"], contract)


def _check_contract(contract, where: str) -> None:
    required = {"level", "vulgarity", "document_type", "genre", "document_config", "profile_config", "embellishment", "markup",
                "markup_rules", "english"}
    if not isinstance(contract, dict) or set(contract) != required:
        raise UserError(f"{where}: evaluation_contract needs {', '.join(sorted(required))}")
    if (type(contract["level"]) is not int or contract["level"] not in range(1, 6)
            or type(contract["vulgarity"]) is not int or contract["vulgarity"] not in range(4)):
        raise UserError(f"{where}: invalid evaluation_contract dials")
    document, profile = contract["document_config"], contract["profile_config"]
    if (not isinstance(document, dict) or set(document) != {f.name for f in fields(DocumentOverrides)} - {"profile"}
            or not isinstance(profile, dict) or set(profile) != set(PROFILE_KEYS)):
        raise UserError(f"{where}: evaluation_contract needs complete document_config and profile_config")
    nested = {"substitution": CLASSES, "garnish": GARNISH_KEYS, "max_garnish": GARNISH_KEYS,
              "rewrite": [f.name for f in fields(RewriteThresholds)],
              "swearing": [f.name for f in fields(SwearProfile)]}
    if any(not isinstance(profile[key], dict) or set(profile[key]) != set(keys) for key, keys in nested.items()):
        raise UserError(f"{where}: evaluation_contract needs complete nested profile_config maps")
    try:
        DocumentOverrides.parse(document)
        ProfileOverrides.parse(profile)
    except UserError as exc:
        raise UserError(f"{where}: invalid evaluation_contract: {exc}") from exc
    if contract["markup"] not in MARKUPS[:-1]:
        raise UserError(f"{where}: evaluation_contract markup must be resolved (text, markdown or mdx)")
    expected_rule = MARKUP_RULE.format(markup=contract["markup"]) if contract["markup"] != "text" else None
    if contract["markup_rules"] != expected_rule:
        raise UserError(f"{where}: evaluation_contract markup_rules do not match markup")
    if contract["english"] not in (None, "us", "uk", "none"):
        raise UserError(f"{where}: evaluation_contract english must be resolved")
    from .policy import DOCUMENT_TYPES, EMBELLISHMENT_NAMES
    if not isinstance(contract["document_type"], str) or contract["document_type"] not in DOCUMENT_TYPES:
        raise UserError(f"{where}: invalid evaluation_contract document_type")
    for key in ("genre", "embellishment"):
        value = contract[key]
        names = tuple(n for n in DOCUMENT_TYPES if n != "auto") if key == "genre" else EMBELLISHMENT_NAMES.values()
        if (not isinstance(value, dict) or set(value) != {"name", "guidance"}
                or not isinstance(value["name"], str) or value["name"] not in names
                or not isinstance(value["guidance"], str)):
            raise UserError(f"{where}: invalid evaluation_contract {key}")


def _evaluation_contract(original: str, *, level: int | str, vulgarity: int | str | None,
                         markup: str, english: str | None, embellishment: int | str | None,
                         document_type: str, document_config: dict | None,
                         translator: Translator | None) -> dict[str, Any]:
    if markup == "auto":
        markup = detect_markup(original)
    result = translation.run(original, translator=translator or default_translator(), level=level,
                             vulgarity=vulgarity, markup=markup, english=english,
                             embellishment=embellishment, document_type=document_type, document_config=document_config)
    return {"level": result.level, "vulgarity": result.vulgarity, "document_type": result.genre.selected,
                "genre": {"name": result.genre.name, "guidance": result.genre.policy.guidance},
                "document_config": result.genre.envelope(result.embellishment.step)["document_config"],
                "profile_config": result.profile_config,
                "embellishment": {"name": result.embellishment.name, "guidance": result.embellishment.guidance},
                "markup": markup, "markup_rules": MARKUP_RULE.format(markup=markup) if markup != "text" else None,
                "english": result.english}


def blind(original: str, candidates: dict[str, str], *, level: int | str = 5, vulgarity: int | str | None = None,
          seed: int = 0, rubric: Rubric | None = None, translator: Translator | None = None,
          markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
          document_type: str = "general", document_config: dict | None = None) -> Packet:
    """Shuffle candidates under labels, with the source's effective writing contract for the judge.

    The contract comes from the same translation route as writing; it contains no candidate identities.
    Historical packets without a contract remain protocol 1 and retain their original instructions.
    """
    if not 2 <= len(candidates) <= len(LABELS):
        raise UserError(f"judge 2 to {len(LABELS)} candidates, not {len(candidates)}")
    rubric = rubric or Rubric.load()
    contract = _evaluation_contract(original, level=level, vulgarity=vulgarity, markup=markup, english=english,
                                    embellishment=embellishment, document_type=document_type,
                                    document_config=document_config, translator=translator)
    names = sorted(candidates)
    key = hashlib.sha256(json.dumps([seed, original, names]).encode()).hexdigest()
    random.Random(key).shuffle(names)
    labels = LABELS[:len(names)]
    return Packet(original, contract["level"], contract["vulgarity"], {lb: candidates[n] for lb, n in zip(labels, names)},
                  dict(zip(labels, names)), rubric.version, contract)


class BadReport(ValueError):
    """The judge's report doesn't follow the rubric; problems lists every reason, to send back to the judge."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass
class Verdict:
    """A validated report, unblinded: everything keyed by candidate name."""
    rubric_version: int
    scores: dict[str, dict[str, int]]
    evidence: dict[str, dict[str, str]]
    problems: dict[str, list[dict[str, str]]]
    summaries: dict[str, str]
    rankings: dict[str, list[list[str]]]       # per criterion and "overall": tiers, best first
    judge: str = ""
    labels: dict[str, str] = field(default_factory=dict)       # name -> the label it was judged under

    evaluation_protocol: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {"rubric_version": self.rubric_version, "judge": self.judge, "labels": self.labels,
                **({"evaluation_protocol": self.evaluation_protocol} if self.evaluation_protocol != 1 else {}),
                "scores": self.scores, "evidence": self.evidence, "problems": self.problems,
                "summaries": self.summaries, "rankings": self.rankings}

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, where: str = "judge verdict") -> "Verdict":
        required = {"rubric_version", "scores", "evidence", "problems", "summaries", "rankings"}
        if not isinstance(data, dict) or not required <= data.keys() or set(data) - required - {"judge", "labels", "evaluation_protocol"}:
            raise UserError(f"{where}: invalid verdict fields; need {', '.join(sorted(required))}")
        if type(data["rubric_version"]) is not int or data["rubric_version"] < 1:
            raise UserError(f"{where}: rubric_version must be a positive integer")
        scores = data["scores"]
        if (not isinstance(scores, dict) or not 2 <= len(scores) <= len(LABELS)
                or any(not isinstance(name, str) or not name.strip() for name in scores)):
            raise UserError(f"{where}: scores must name 2–8 candidates")
        for name_field in ("evidence", "problems", "summaries"):
            if not isinstance(data[name_field], dict) or set(data[name_field]) != set(scores):
                raise UserError(f"{where}: {name_field} must name every scored candidate")
        criteria = None
        for name, values in scores.items():
            if (not isinstance(values, dict) or not values or any(not isinstance(key, str) or not key
                    or type(score) is not int or not 1 <= score <= 5 for key, score in values.items())):
                raise UserError(f"{where}: {name}: criterion scores must be integers 1–5")
            if criteria is not None and set(values) != criteria:
                raise UserError(f"{where}: all candidates must share the same criteria")
            criteria = set(values)
            evidence = data["evidence"][name]
            if (not isinstance(evidence, dict) or set(evidence) != criteria
                    or any(not isinstance(v, str) or not v.strip() for v in evidence.values())
                    or not isinstance(data["summaries"][name], str) or not data["summaries"][name].strip()):
                raise UserError(f"{where}: {name}: missing criterion evidence or summary")
            problems = data["problems"][name]
            if (not isinstance(problems, list) or any(not isinstance(p, dict) or set(p) != set(PROBLEM_KEYS)
                    or any(not isinstance(v, str) for v in p.values()) or p["severity"] not in SEVERITIES
                    or not p["quote"].strip() or not p["why"].strip() for p in problems)):
                raise UserError(f"{where}: {name}: invalid problem details")
        rankings = data["rankings"]
        if not isinstance(rankings, dict) or "overall" not in rankings or set(rankings) - criteria - {"overall"}:
            raise UserError(f"{where}: rankings need overall and known criteria")
        for key, tiers in rankings.items():
            if (not isinstance(tiers, list) or not tiers or any(not isinstance(tier, list) or not tier
                    or any(not isinstance(name, str) for name in tier) for tier in tiers)):
                raise UserError(f"{where}: {key}: rankings must be non-empty tiers")
            names = [name for tier in tiers for name in tier]
            if len(names) != len(scores) or set(names) != set(scores):
                raise UserError(f"{where}: {key}: rankings must include every candidate once")
        if not isinstance(data.get("judge", ""), str) or not isinstance(data.get("labels", {}), dict):
            raise UserError(f"{where}: judge and labels have invalid types")
        labels = data.get("labels", {})
        if labels and (set(labels) != set(scores) or any(not isinstance(v, str) or v not in LABELS or len(v) != 1
                                                        for v in labels.values())):
            raise UserError(f"{where}: labels must identify each candidate")
        protocol = data.get("evaluation_protocol", 1)
        if type(protocol) is not int or protocol not in (1, EVALUATION_PROTOCOL):
            raise UserError(f"{where}: unknown evaluation protocol {protocol!r}")
        return cls(**data)

    def card(self) -> str:
        """The report card as a table, then each candidate's problems."""
        names = [n for tier in self.rankings["overall"] for n in tier]
        criteria = list(next(iter(self.scores.values())))
        width = max(12, *(len(n) for n in names))
        lines = [f"{'':<14}" + "".join(f"{n:>{width + 2}}" for n in names)]
        for c in criteria:
            lines.append(f"{c:<14}" + "".join(f"{self.scores[n][c]:>{width + 2}}" for n in names))
        lines.append(f"{'mean':<14}" + "".join(f"{_mean(self.scores[n].values()):>{width + 2}.2f}" for n in names))
        lines += ["", "rankings: " + "; ".join(f"{k}: {' > '.join(' = '.join(t) for t in v)}"
                                             for k, v in self.rankings.items())]
        for n in names:
            lines += ["", f"{n}: {self.summaries[n]}"]
            lines += [f"  {p['severity']}: {p['quote']!r} ({_renders(p)}): {p['why']}" for p in self.problems[n]]
        return "\n".join(lines)


def read(packet: Packet, report: dict[str, Any], rubric: Rubric | None = None, judge: str = "") -> Verdict:
    """Validate a judge's report against the packet and unblind it. Raises BadReport with every problem."""
    rubric = rubric or Rubric.load()
    if packet.rubric_version != rubric.version:
        raise BadReport([f"the packet was made under rubric version {packet.rubric_version}, not {rubric.version}"])
    if not isinstance(report, dict):
        raise BadReport(["the report must be a JSON object (see the packet's schema)"])
    bad: list[str] = []
    cands = report.get("candidates") or {}
    if not isinstance(cands, dict):
        raise BadReport(["candidates must be an object keyed by label"])
    labels = list(packet.candidates)
    for lb in labels:
        if lb not in cands:
            bad.append(f"candidate {lb} not reported")
            continue
        got = cands[lb]
        if not isinstance(got, dict) or not isinstance(got.get("scores") or {}, dict):
            bad.append(f"candidate {lb} must be an object with scores, problems and a summary")
            continue
        for c in rubric.criteria:
            s = (got.get("scores") or {}).get(c.id) or {}
            if not isinstance(s, dict):
                bad.append(f"{lb} {c.id}: must be an object with evidence and a score")
                continue
            if type(s.get("score")) is not int or not 1 <= s["score"] <= 5:
                bad.append(f"{lb} {c.id}: score must be a whole number 1-5")
            if not isinstance(s.get("evidence"), str) or not s["evidence"].strip():
                bad.append(f"{lb} {c.id}: evidence is missing")
        if not isinstance(got.get("summary"), str) or not got["summary"].strip():
            bad.append(f"{lb}: summary must be non-empty text")
        problems = got.get("problems")
        if not isinstance(problems, list):
            bad.append(f"{lb} problems must be a list")
            continue
        for p in problems:
            if not isinstance(p, dict) or not all(isinstance(p.get(k), str) for k in PROBLEM_KEYS):
                bad.append(f"{lb} problem {str(p)[:40]!r}: needs {', '.join(PROBLEM_KEYS)}, each a string")
                continue
            if p["severity"] not in SEVERITIES:
                bad.append(f"{lb} problem {p['quote'][:30]!r}: severity must be one of {', '.join(SEVERITIES)}")
            if not _quoted(p["quote"], packet.candidates[lb]):
                bad.append(f"{lb} problem quote {p['quote'][:40]!r} isn't in candidate {lb}, verbatim")
    rankings = report.get("rankings")
    if not isinstance(rankings, dict):
        bad.append("rankings must be an object")
        rankings = {}
    for k in rubric.compared:
        tiers = rankings.get(k)
        flat = [lb for tier in tiers for lb in tier] if isinstance(tiers, list) and all(
            isinstance(t, list) and t for t in tiers) else None
        if flat is None or any(not isinstance(label, str) for label in flat) or sorted(flat) != sorted(labels):
            bad.append(f"ranking {k!r} must be tiers (lists, best first) holding each of {', '.join(labels)} once")
    if bad:
        raise BadReport(bad)
    name = packet.names
    return Verdict(
        rubric.version,
        {name[lb]: {c.id: cands[lb]["scores"][c.id]["score"] for c in rubric.criteria} for lb in labels},
        {name[lb]: {c.id: cands[lb]["scores"][c.id]["evidence"] for c in rubric.criteria} for lb in labels},
        {name[lb]: list(cands[lb].get("problems") or []) for lb in labels},
        {name[lb]: cands[lb].get("summary", "") for lb in labels},
        {k: [[name[lb] for lb in tier] for tier in report["rankings"][k]] for k in rubric.compared},
        judge, {n: lb for lb, n in name.items()}, packet.evaluation_protocol)


def tally(verdicts: list[Verdict]) -> dict[str, dict[str, Any]]:
    """Each candidate name across verdicts (one per text, or per seed): mean score per criterion, the overall
    mean, its share of first places (a tie for first shares it), and its problems by severity. What the tuning
    loop compares."""
    if len({v.evaluation_protocol for v in verdicts}) > 1:
        raise UserError("verdicts under different evaluation protocols don't compare")
    if len({v.rubric_version for v in verdicts}) > 1:
        raise UserError("verdicts under different rubric versions don't compare")
    if len({frozenset(values) for v in verdicts for values in v.scores.values()}) > 1:
        raise UserError("verdicts with different criteria don't compare")
    out: dict[str, dict[str, Any]] = {}
    for name in sorted({n for v in verdicts for n in v.scores}):
        mine = [v for v in verdicts if name in v.scores]
        criteria = list(mine[0].scores[name])
        means = {c: round(_mean(v.scores[name][c] for v in mine), 2) for c in criteria}
        out[name] = {"texts": len(mine), "scores": means, "mean": round(_mean(means.values()), 2),
                     "first": round(sum(_first_share(v, name) for v in mine) / len(mine), 2),
                     "problems": {s: sum(p["severity"] == s for v in mine for p in v.problems[name])
                                  for s in SEVERITIES}}
    return out


def _renders(problem: dict[str, str]) -> str:
    return f"for {problem['original']!r}" if problem.get("original") else "added"


def _first_share(verdict: Verdict, name: str) -> float:
    top = verdict.rankings["overall"][0]
    return 1 / len(top) if name in top else 0.0


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _quoted(quote: str, text: str) -> bool:
    """quote appears in text, ignoring case, curly quotes and runs of whitespace (and an ellipsis may join
    two quoted parts)."""
    norm = lambda s: re.sub(r"\s+", " ", fold(s)).strip(" .\"'")   # noqa: E731
    parts = [norm(p) for p in re.split(r"\.\.\.|…", quote) if norm(p)]
    return bool(parts) and all(p in norm(text) for p in parts)


# --- the model: thin adapters over claude.py ------------------------------------------------------------------

@lru_cache(maxsize=1)
def _unharnessed() -> dict[str, Any]:
    """judge.yaml's unharnessed brief: its system prompt, and what each level and vulgarity sounds like."""
    raw = yaml.safe_load((DATA_DIR / "judge.yaml").read_text(encoding="utf-8"))["unharnessed"]
    return {"system": " ".join(raw["system"].split()), "levels": {int(k): v for k, v in raw["levels"].items()},
            "vulgarity": {int(k): v for k, v in raw["vulgarity"].items()}}


def unharnessed_prompt(original: str, *, level: int | str, vulgarity: int | str | None,
                       markup: str = "text", english: str | None = None, embellishment: int | str | None = None,
                       document_type: str = "general", document_config: dict | None = None,
                       translator: Translator | None = None) -> str:
    """A reference retelling brief without vocabulary/tools, under the same effective settings as judging."""
    contract = _evaluation_contract(original, level=level, vulgarity=vulgarity, markup=markup, english=english,
                                    embellishment=embellishment, document_type=document_type,
                                    document_config=document_config, translator=translator)
    voice = _unharnessed()
    return (f"Retell this in Australian English vernacular: {voice['levels'][contract['level']]}, "
            f"{voice['vulgarity'][contract['vulgarity']]}.\n{CONTRACT_GUIDANCE}\n"
            f"EVALUATION_CONTRACT (protocol 2):\n{json.dumps(contract, ensure_ascii=False, sort_keys=True)}\n"
            f"Reply with the retelling only.\n\n{original.strip()}")


def unharnessed(original: str, *, level: int | str = 5, vulgarity: int | str | None = None, markup: str = "text",
                client: Any = None, model: str = DEFAULT_MODEL, translator: Translator | None = None,
                english: str | None = None, embellishment: int | str | None = None,
                document_type: str = "general", document_config: dict | None = None) -> str:
    """A model's reference retelling, without the toolkit vocabulary. Raises claude.Error."""
    prompt = unharnessed_prompt(original, level=level, vulgarity=vulgarity, markup=markup, english=english,
                                embellishment=embellishment, document_type=document_type,
                                document_config=document_config, translator=translator)
    response = claude.create(client or claude.client(), model=model, system=_unharnessed()["system"], max_tokens=16000,
                             messages=[{"role": "user", "content": prompt}], effort="medium")
    if response.stop_reason in ("refusal", "max_tokens"):
        raise claude.BadReply(f"no retelling: {response.stop_reason}")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise claude.BadReply("reply has no text")
    return text


def run(packet: Packet, *, client: Any = None, model: str = DEFAULT_MODEL, rubric: Rubric | None = None,
        cache_dir: str | Path | None = None, retries: int = 1) -> Verdict:
    """Judge a packet with a model: the rubric as the system prompt, the report as schema-constrained JSON. A
    report that fails validation goes back once with the reasons. Raises claude.Error or BadReport."""
    rubric = rubric or Rubric.load()
    cache = claude.Cache(cache_dir if cache_dir is not None else claude.default_cache_dir("judge"))
    key = claude.Cache.key("judge", model, packet.instructions(rubric), packet.prompt())
    cached = cache.get(key)
    if cached is not None:
        return read(packet, cached, rubric, judge=model)
    cl = client or claude.client()
    messages = [{"role": "user", "content": packet.prompt()}]
    sent_back = 0
    while True:
        response = claude.create(cl, model=model, system=packet.instructions(rubric), messages=messages, max_tokens=16000,
                                 effort="high", schema=packet.schema(rubric))
        report = claude.json_reply(response, ("candidates", "rankings"))
        try:
            verdict = read(packet, report, rubric, judge=model)
        except BadReport as exc:
            sent_back += 1
            if sent_back > retries:
                raise
            messages += [{"role": "assistant", "content": json.dumps(report)},
                         {"role": "user", "content": "Your report doesn't follow the rubric: "
                                                     + "; ".join(exc.problems) + ". Send the whole report again, fixed."}]
            continue
        cache.put(key, report)
        return verdict
