"""LLM tagging pass: propose schema fields for staged phrases, for human review.

The model proposes concept, frame, intensity, vulgarity, `replaces`, flags and
a fresh gloss. Nothing it says is trusted blindly. Proposals are validated
against the schema, the flags set the status (slur/not_aussie -> omit; dubious,
fabricated, archaic -> gate), and `aussiefy dev review` shows everything as a diff
before it lands.
"""

from __future__ import annotations

import json
from typing import Any

from .. import claude
from ..claude import DEFAULT_MODEL
from ..embed import NgramEmbedder
from ..errors import UserError
from ..model import Dictionary
from ..schema import FLAGS, FRAMES, REGISTERS, SchemaError, parse_entry
from .normalise import Staged


FLAG_STATUS = {"slur": "omit", "not_aussie": "omit", "fabricated": "gate", "dubious_meaning": "gate",
               "archaic": "gate"}

TAG_SCHEMA = {
    "type": "object",
    "properties": {
        "form": {"type": "string"},
        "variants": {"type": "array", "items": {"type": "string"}},
        "concept": {"type": "array", "items": {"type": "string"}},
        "new_concept": {
            "anyOf": [
                {"type": "null"},
                {"type": "object",
                 "properties": {"id": {"type": "string"}, "description": {"type": "string"},
                                "trigger": {"type": "string"}},
                 "required": ["id", "description", "trigger"], "additionalProperties": False},
            ]
        },
        "frame": {"type": "string", "enum": [f for f in FRAMES if f != "tag"]},
        "intensity": {"type": "integer"},
        "vulgarity": {"type": "integer"},
        "incoherence": {"type": "integer"},
        "register": {"type": "string", "enum": list(REGISTERS)},
        "region": {"type": "array", "items": {"type": "string"}},
        "replaces": {"type": "array", "items": {"type": "string"}},
        "flags": {"type": "array", "items": {"type": "string", "enum": [f for f in FLAGS if f != "untagged"]}},
        "gloss": {"type": "string"},
        "review_note": {"type": "string"},
    },
    "required": ["form", "variants", "concept", "new_concept", "frame", "intensity", "vulgarity", "incoherence",
                 "register", "region", "replaces", "flags", "gloss", "review_note"],
    "additionalProperties": False,
}

SYSTEM = """You are tagging candidate Australian slang phrases for a slang-translation dictionary.
Each phrase was scraped from a web listicle. Such sources are often wrong: phrases that are
American, British or invented, meanings that are inaccurate, and occasionally slurs. Be sceptical
and flag rather than guess.

Return the fields of one dictionary entry:
- form: the canonical surface form. For a clause idiom with a subject, use slots, e.g.
  "{subj} {have} a kangaroo loose in {poss} top paddock". Allowed slots: {subj} {be} {have} {do}
  {poss} {obj}. Only clause frames may use {subj}, and clause forms must start with {subj}.
- frame: predicate_adj (complement of a linking verb: "he's ___"), np, adj, adv, vp (verb phrase,
  base form first, e.g. "spit the dummy"), clause, interjection, imperative.
- concept: one or more IDs from the vocabulary below. If none fits, leave concept empty and propose
  new_concept (UPPER_SNAKE id, short description, and one plain-English trigger).
- intensity 1-5, vulgarity 0-3, calibrated to Australian ears rather than American ones: 0 clean;
  1 mild swearing in everyday use (bloody, bugger, bastard, donger); 2 common but impolite (piss, arse,
  balls, fuck); 3 strong (cunt), which is vulgar but often affectionate in Australia ("a good cunt").
- incoherence 1-5: the minimum translation level where this belongs. 1-2 means common, transparent
  words. 3-4 means colourful idioms. 5 means obscure or extreme.
- register: current, dated or archaic.
- replaces: 2-5 plain-English paraphrases that the phrase can stand in for, in the same frame,
  e.g. ["very busy", "swamped"]. Append @N to set the intensity a paraphrase expresses.
- flags: not_aussie (not of Australian origin or use), slur, dubious_meaning (the source's meaning
  looks wrong), archaic, fabricated (no evidence anyone says this).
- gloss: a short meaning in YOUR OWN WORDS. Never copy or lightly reword the source text.
- review_note: one sentence for the human reviewer about anything uncertain.
"""


def system_prompt(dictionary: Dictionary) -> str:
    """SYSTEM and the concept vocabulary: the same for every phrase in a run, so it can be cached."""
    vocabulary = "\n".join(f"{c.id}: {c.description}" for c in sorted(dictionary.concepts.values(), key=lambda c: c.id))
    return f"{SYSTEM}\nConcept vocabulary:\n{vocabulary}\n"


def build_prompt(item: Staged) -> str:
    return (f"Phrase: {item.form}\n"
            f"Variants seen: {json.dumps(item.variants)}\n"
            f"Source meanings (context only, do not copy): {json.dumps(item.source_meanings)}\n"
            f"Usage examples from sources: {json.dumps(item.usage)}\n"
            f"Seen at {len(item.sources)} source(s).")


def proposal_to_entry(item: Staged, proposal: dict, dictionary: Dictionary) -> tuple[dict, list[str]]:
    """Turn a model proposal into a raw entry dict and a list of review notes. The proposal has every key
    TAG_SCHEMA requires (claude.json_reply checks), so they are indexed directly."""
    notes = [proposal["review_note"]] if proposal["review_note"] else []
    concepts = [c for c in proposal["concept"] if c in dictionary.concepts]
    dropped = set(proposal["concept"]) - set(concepts)
    if dropped:
        notes.append(f"dropped unknown concepts {sorted(dropped)}")
    if proposal["new_concept"]:
        nc = proposal["new_concept"]
        notes.append(f"proposed new concept {nc['id']}: {nc['description']} (trigger: {nc['trigger']})")
    flags = sorted(set(proposal["flags"]) & set(FLAGS))
    status = "active"
    for f in flags:
        target = FLAG_STATUS.get(f)
        if target == "omit" or (target == "gate" and status == "active"):
            status = target
    if not concepts:
        status = "omit" if status == "omit" else "gate"
        flags = sorted(set(flags) | {"untagged"})
        notes.append("no known concept; gated until the vocabulary is extended")

    # A gloss too close to the source text has to be rewritten by a person.
    sim = NgramEmbedder()
    gloss = proposal["gloss"]
    for meaning in item.source_meanings:
        if gloss and sim.similarity(gloss, meaning) > 0.8:
            notes.append("gloss is too close to a source description; rewrite it")
            gloss = ""
    raw = {
        "id": item.id,
        "form": proposal["form"] or item.form,
        "variants": [v for v in dict.fromkeys(proposal["variants"] + item.variants) if v != proposal["form"]],
        "concept": concepts,
        "frame": proposal["frame"],
        "intensity": max(1, min(5, int(proposal["intensity"]))),
        "vulgarity": max(0, min(3, int(proposal["vulgarity"]))),
        "incoherence": max(1, min(5, int(proposal["incoherence"]))),
        "register": proposal["register"],
        "region": proposal["region"],
        "replaces": proposal["replaces"],
        "status": status,
        "flags": flags,
        "sources": item.sources,
        "gloss": gloss,
        "notes": "; ".join(n for n in notes if n),
    }
    return raw, notes


def tag_all(items: list[Staged], dictionary: Dictionary, client: Any = None, model: str = DEFAULT_MODEL,
            log=print, *, cache: bool = True) -> list[dict]:
    """Tag every staged item. A phrase the model refuses or answers badly is staged gated and untagged; an outage
    (claude.Unavailable) stops the run. Accepted proposals are cached per item, so a retry keeps completed paid
    work; each cached proposal is converted and validated again. cache=False bypasses reads and writes."""
    replies = claude.Cache(claude.default_cache_dir("tag") if cache else None)
    system = system_prompt(dictionary)
    out = []
    for item in items:
        if item.known_as:
            out.append({"id": item.id, "known_as": item.known_as, "known_status": item.known_status,
                        "sources": item.sources, "form": item.form})
            continue
        prompt = build_prompt(item)
        key = claude.Cache.key(model, system, TAG_SCHEMA, item.to_dict(), prompt)
        proposal = replies.get(key)
        cached = proposal is not None
        if cached and (not isinstance(proposal, dict) or set(TAG_SCHEMA["required"]) - set(proposal)):
            raise UserError(f"{replies.directory / (key + '.json')}: invalid cached tag proposal; delete it")
        try:
            if not cached:
                client = client or claude.client()
                proposal = claude.call_json(client, model=model, system=system, prompt=prompt,
                                            schema=TAG_SCHEMA, cache=True)
            raw, notes = proposal_to_entry(item, proposal, dictionary)
            parse_entry(raw)  # schema check now, so review only ever sees valid entries
            if not cached:
                replies.put(key, proposal)
        except (claude.Refused, claude.BadReply, SchemaError) as exc:   # this phrase only
            log(f"  ! {item.form}: {exc}")
            raw = {"id": item.id, "form": item.form, "concept": [], "frame": "interjection",
                   "status": "gate", "flags": ["untagged"], "sources": item.sources,
                   "notes": f"tagging failed: {exc}"}
        out.append(raw)
        log(f"  {raw['status']:<6} {raw['id']}  {raw.get('notes', '')}")
    return out
