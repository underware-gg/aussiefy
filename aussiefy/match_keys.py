"""Canonical source-match identities contain dictionary patterns, never the caller's words."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .degree import realised_degree
from .errors import UserError
from .matcher import Pattern, compile_pattern
from .schema import FRAMES, HOLDING_CONCEPT
from .identifiers import CONCEPT_ID

QUALIFIERS = ("degree",)
DEGREES = {"mild", "unmarked", "strong"}
FINGERPRINT = re.compile(r"[0-9a-f]{64}")


def pattern_fingerprint(frame: str, pattern: str | Pattern) -> str:
    """Hash the dictionary pattern's grammar, including context which is absent from its display text."""
    try:
        parsed = compile_pattern(pattern, frame, (), 3) if isinstance(pattern, str) else pattern
    except ValueError as exc:
        raise UserError(f"invalid source pattern: {exc}") from exc
    if not isinstance(parsed, Pattern) or parsed.frame != frame:
        raise UserError("source pattern must have the match's grammatical frame")
    shape = {"elements": [(e.kind, sorted(e.values), e.optional, e.slot, e.role, sorted(e.forms), e.reach)
                          for e in parsed.elements],
             "person_only": parsed.person_only, "before_modifier": parsed.before_modifier,
             "clause_start": parsed.clause_start, "clause_end": parsed.clause_end,
             "object_argument": parsed.object_argument}
    payload = json.dumps(["pattern-v1", frame, shape], ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def make_match_root(concepts, frame: str, pattern: str | Pattern) -> str:
    if (not isinstance(concepts, (tuple, list)) or not concepts
            or any(not isinstance(cid, str) or not CONCEPT_ID.fullmatch(cid) for cid in concepts)
            or not isinstance(frame, str) or frame not in FRAMES
            or not isinstance(pattern, (str, Pattern)) or isinstance(pattern, str) and not pattern):
        raise UserError("a match root needs concept IDs, a grammatical frame and a dictionary pattern")
    return "+".join(sorted(set(concepts))) + "/" + frame + "/" + pattern_fingerprint(frame, pattern)


@dataclass(frozen=True)
class SourceMatch:
    root: str
    degree: str | None = None

    @property
    def key(self):
        return self.root + (";degree=" + self.degree if self.degree else "")

    def to_dict(self):
        return {"key": self.key, "root": self.root, "qualifiers": {"degree": self.degree} if self.degree else {}}


def _parse_root(root):
    if not isinstance(root, str):
        raise UserError("match root must be text")
    parts = root.split("/")
    if len(parts) != 3:
        raise UserError("match root must name concepts, frame and pattern fingerprint")
    concepts, frame, fingerprint = parts[0].split("+"), parts[1], parts[2]
    if (not concepts or any(not CONCEPT_ID.fullmatch(cid) for cid in concepts)
            or concepts != sorted(set(concepts)) or frame not in FRAMES or not FINGERPRINT.fullmatch(fingerprint)):
        raise UserError("match root is not canonical")
    return concepts, frame, fingerprint


def make_match_key(root: str, *, degree: str | None = None) -> str:
    _parse_root(root)
    if degree is not None and (not isinstance(degree, str) or degree not in DEGREES):
        raise UserError("match degree must be mild, unmarked or strong")
    return SourceMatch(root, degree if degree != "unmarked" else None).key


def parse_match_key(key: str) -> SourceMatch:
    if not isinstance(key, str):
        raise UserError("match key must be text")
    parts = key.split(";")
    _parse_root(parts[0])
    if len(parts) == 1:
        return SourceMatch(parts[0])
    if len(parts) != 2 or parts[1] not in {"degree=mild", "degree=strong"}:
        raise UserError("match qualifiers must be canonical; only non-default degree is currently supported")
    return SourceMatch(parts[0], parts[1].split("=", 1)[1])


def known_match(key: str, dictionary) -> bool:
    """Validate syntax and an authored root; contextual reachability belongs to detection.

    A supported qualifier can be dormant for this root. Adjustments only apply if detection emits
    that exact key, using its reviewed degree evidence and conflict checks.
    """
    match = parse_match_key(key)
    concepts, frame, fingerprint = _parse_root(match.root)
    return any(set(concepts) <= set(pattern.concepts)
               for pattern in dictionary.source_match_patterns.get((frame, fingerprint), ()))


def detection_match(det) -> SourceMatch | None:
    """Describe a detected dictionary meaning independently of its chosen target and source spelling."""
    if HOLDING_CONCEPT in det.concepts:
        return None
    concepts = tuple(cid for cid in det.source_concepts if cid in det.concepts)
    if not concepts:
        return None
    root = make_match_root(concepts, det.frame, det.source_pattern or det.pattern)
    bands = {realised_degree(det.semantic_degree.get(cid), det.degree_qualifier)
             for cid in det.degree_concepts if cid in concepts}
    degree = bands.pop() if len(bands) == 1 and not set(concepts).intersection(det.degree_conflicts) else None
    return parse_match_key(make_match_key(root, degree=degree))
