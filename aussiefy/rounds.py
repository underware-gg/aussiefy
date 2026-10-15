"""Apply a research round's verified verdicts to the dictionary: `aussiefy dev round DIR [--write]`.

A round directory (research/<round>/) holds:
  round.yaml                 name, output (entries/<file>.yaml), header, id_suffix, reference (the queries file)
  verify/verdicts-*.yaml     the verifiers' decisions (see a round's verify/BRIEF.md)
  concept_aliases.yaml       NEW concepts proposed twice under different names: {left: right}
  trigger_fixes.yaml         hand review of triggers: remove / add / intensity
  entry_fixes.yaml           hand repairs to entries, by id
  concept_fixes.yaml         explicit concept metadata/trigger overrides and entryless guards, by id
  extra_entries.yaml         hand-written entries that belong to the round (they may use its new concepts)

RoundConfig.load() reads the round; plan_round() is pure: from the round and a dictionary it says what would
change and what it drops, and why.
Guards, each reported: a form already in the dictionary or an id already used is skipped; a trigger that is
itself an Aussie form (it would swap slang for slang), copies a reference query word for word (it would teach to
the test) or already exists is dropped; every low-confidence accept ships gated. RoundPlan.write() writes the
output file and the concepts (appended triggers in place, new concepts in a section of their own), but only after
the result has loaded and validated in a scratch copy of the data directory. Planning sets aside the round's own
earlier output, so unchanged reapplication is a no-op. Replanning an earlier round while a
later one uses its concepts requires those dependent entries to be set aside while planning. Previously written
concept records retain hand edits; explicit concept_fixes replace only their named fields. A trigger appended
to an existing concept stays unless explicitly replaced through concept_fixes.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from copy import deepcopy
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from .errors import UserError
from .loader import _YAML_LOADER, DATA_DIR, load_dictionary, write_validated
from .model import Dictionary
from .schema import Concept, ENTRY_KEYS, SchemaError, parse_concept, parse_entry
from .terms import form_key


def _yaml(text: str) -> Any:
    """Parse with the loader's YAML reader (libyaml where installed: about 9x faster than pure Python)."""
    return yaml.load(text, Loader=_YAML_LOADER)


@dataclass
class RoundConfig:
    """Everything a round's directory says, read once: plan_round() reads nothing else."""
    name: str
    output: str
    header: str
    id_suffix: str
    directory: Path
    queries: set[str] = field(default_factory=set)      # the reference set's queries, as form keys
    verdicts: list[tuple[str, dict]] = field(default_factory=list)   # (file stem, verdict)
    unparsed: list[str] = field(default_factory=list)  # verdict files that don't parse
    aliases: dict[str, str] = field(default_factory=dict)
    entry_fixes: dict[str, dict] = field(default_factory=dict)
    trigger_fixes: dict[str, Any] = field(default_factory=dict)
    extra_entries: list[dict] = field(default_factory=list)
    concept_fixes: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def load(cls, directory: str | Path) -> "RoundConfig":
        d = Path(directory)
        raw = _yaml((d / "round.yaml").read_text(encoding="utf-8"))
        config = cls(raw["name"], raw["output"], raw.get("header", ""), raw.get("id_suffix", "-round"), d)
        if raw.get("reference"):   # configured, so it must exist: a silent skip would change what's filtered
            path = (d / raw["reference"]).resolve()
            if not path.exists():
                raise UserError(f"{d / 'round.yaml'}: reference {raw['reference']} not found ({path})")
            ref = _yaml(path.read_text(encoding="utf-8")) or {}
            config.queries = {form_key(c["query"]) for k in ("must_not", "should", "known") for c in ref.get(k) or ()}
        for p in sorted((d / "verify").glob("verdicts-*.yaml")):
            try:
                config.verdicts += [(p.stem, v) for v in _yaml(p.read_text(encoding="utf-8")) or ()]
            except yaml.YAMLError:   # a verifier still writing, or a broken file: report it, never half-apply it
                config.unparsed.append(p.name)
        config.aliases = config._optional("concept_aliases.yaml", {})
        config.entry_fixes = config._optional("entry_fixes.yaml", {})
        config.trigger_fixes = config._optional("trigger_fixes.yaml", {})
        config.extra_entries = config._optional("extra_entries.yaml", [])
        fixes = d / "concept_fixes.yaml"
        parsed = _yaml(fixes.read_text(encoding="utf-8")) if fixes.exists() else None
        config.concept_fixes = {} if parsed is None else parsed
        return config

    def _optional(self, name: str, default: Any) -> Any:
        path = self.directory / name
        return (_yaml(path.read_text(encoding="utf-8")) or default) if path.exists() else default

    @property
    def marker(self) -> str:
        """The comment that opens this round's section of concepts.yaml."""
        return f"# --- {self.name} ("


@dataclass
class RoundPlan:
    config: RoundConfig
    entries: list[dict] = field(default_factory=list)
    new_concepts: dict[str, dict] = field(default_factory=dict)
    added_triggers: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    dropped: list[tuple[str, str, str, str]] = field(default_factory=list)
    style_guide: list[tuple[str, str]] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)

    def summary(self) -> list[str]:
        gated = sum(e.get("status") == "gate" for e in self.entries)
        n_trig = sum(len(v) for f in self.added_triggers.values() for v in f.values())
        lines = [f"{len(self.entries)} entries ({gated} gated), {len(self.new_concepts)} new concepts, {n_trig} "
                 f"triggers on {len(self.added_triggers)} existing concepts; {len(self.dropped)} dropped"]
        if self.config.concept_fixes:
            lines.append(f"{len(self.config.concept_fixes)} explicit concept fixes requested:")
            lines += [f"  {cid}: {', '.join(sorted(patch))}" for cid, patch in self.config.concept_fixes.items()]
        lines += [f"  skipping {name}: doesn't parse" for name in self.unparsed]
        lines += ["  drop " + " ".join(map(str, x)) for x in self.dropped]
        if self.style_guide:
            lines.append("\nstyle guide items (fold the useful ones into data/guide.yaml by hand):")
            lines += [f"  - {c}: {g}" for c, g in self.style_guide]
        return lines

    def write(self, data_dir: Path = DATA_DIR) -> Dictionary:
        """Write the round into data_dir, after validating the result in a scratch copy. Returns the new dictionary."""
        if self.unparsed:
            raise SchemaError(f"verdict files don't parse: {', '.join(self.unparsed)}; nothing written")
        c = self.config
        concepts = (Path(data_dir) / "concepts.yaml").read_text(encoding="utf-8")
        return write_validated(data_dir, {
            f"entries/{c.output}": c.header + yaml.safe_dump(self.entries, sort_keys=False, allow_unicode=True,
                                                             width=110),
            "concepts.yaml": self._concepts_text(concepts)})

    def _concepts_text(self, current: str) -> str:
        """concepts.yaml with this round's triggers appended in place and its new concepts in a section of their own."""
        c = self.config
        lines = current.split("\n")
        for cid, frames in self.added_triggers.items():
            start = lines.index(f"{cid}:")
            end = next((i for i in range(start + 1, len(lines)) if re.match(r"^[A-Z][A-Z0-9_]*:\s*$", lines[i])),
                       len(lines))
            for frame, ps in frames.items():
                extra = ", ".join(f'"{p}"' for p in ps)
                fl = next((i for i in range(start, end) if re.match(rf"^\s+{frame}:", lines[i])), None)
                if fl is None:
                    tl = next(i for i in range(start, end) if lines[i].strip() == "triggers:")
                    lines.insert(tl + 1, f"    {frame}: [{extra}]")
                    end += 1
                    continue
                _append_to_flow_list(lines, fl, end, extra)
        text = "\n".join(lines)
        present = _yaml(text) or {}
        missing = {cid: raw for cid, raw in self.new_concepts.items() if cid not in present}
        if missing:
            addition = yaml.safe_dump(missing, sort_keys=False, allow_unicode=True, width=110,
                                      default_flow_style=None)
            section = next((i for i, line in enumerate(lines) if line.startswith(c.marker)), None)
            if section is None:
                text = text.rstrip("\n") + f"\n\n{c.marker}research/{c.directory.name}) {'-' * 34}\n" + addition
            else:
                end = next((i for i in range(section + 1, len(lines)) if lines[i].startswith("# --- ")), len(lines))
                text = "\n".join(lines[:end]).rstrip("\n") + "\n" + addition + "\n".join(lines[end:])
        present.update(missing)
        for cid in self.new_concepts:
            existing = present[cid]
            triggers = _fixed_triggers(existing.get("triggers") or {}, cid, c.trigger_fixes)
            if triggers != (existing.get("triggers") or {}):
                present[cid] = {**existing, "triggers": triggers}
                text = _replace_concept(text, cid, present[cid])
        for cid, patch in c.concept_fixes.items():
            existing = present[cid]
            merged = {**existing, **deepcopy(patch)}
            if merged != existing:
                text = _replace_concept(text, cid, merged)
        return text


def _replace_concept(text: str, cid: str, raw: dict) -> str:
    """An explicit fix rewrites only its record, retaining neighbouring records and section comments."""
    root = yaml.compose(text, Loader=_YAML_LOADER)
    key, value = next((key, value) for key, value in root.value if key.value == cid)
    lines = text.splitlines(keepends=True)
    start, end = key.start_mark.line, value.end_mark.line + bool(value.end_mark.column)
    while end > start and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    rewritten = yaml.safe_dump({cid: raw}, sort_keys=False, allow_unicode=True, width=110,
                               default_flow_style=None)
    return "".join(lines[:start]) + rewritten + "".join(lines[end:])



def _append_to_flow_list(lines: list[str], start: int, end: int, extra: str) -> None:
    """Add extra to the end of the YAML flow list that opens on lines[start], in place: on the line whose code
    (a comment after it may mention "]") ends in "]"."""
    close = next(i for i in range(start, end) if _code(lines[i]).rstrip().endswith("]"))
    code = _code(lines[close]).rstrip()
    sep = "" if code.endswith("[]") else ", "
    lines[close] = code[:-1] + f"{sep}{extra}]" + lines[close][len(code):]


def _code(line: str) -> str:
    """A YAML line without its comment: from a # outside quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def _split_section(text: str, marker: str) -> tuple[str, str]:
    """concepts.yaml without the section a round appended (from its marker to the next section or the end), and
    that section ("" if there is none)."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith(marker)), None)
    if start is None:
        return text, ""
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("# --- ")), len(lines))
    return "\n".join(lines[:start] + lines[end:]).rstrip("\n") + "\n", "\n".join(lines[start:end])


def base_dictionary(config: RoundConfig, data_dir: Path = DATA_DIR) -> Dictionary:
    """The dictionary as it was before this round: its output file and its concepts section set aside, and with
    them any later entry (in another file) that uses one of the round's concepts."""
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "data"
        shutil.copytree(data_dir, scratch)
        (scratch / "entries" / config.output).unlink(missing_ok=True)
        concepts = scratch / "concepts.yaml"
        kept, section = _split_section(concepts.read_text(encoding="utf-8"), config.marker)
        ours = set(_yaml(section) or {})
        concepts.write_text(kept, encoding="utf-8")
        for path in (scratch / "entries").glob("*.yaml"):
            entries = _yaml(path.read_text(encoding="utf-8")) or []
            later = [e for e in entries if not set(e.get("concept") or ()) & ours]
            if len(later) < len(entries):   # scratch only: layout doesn't matter here
                path.write_text(yaml.safe_dump(later, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return load_dictionary(data_dir=scratch)


def plan_round(config: RoundConfig, d: Dictionary) -> RoundPlan:
    """What applying the round to d would change, and what it drops and why. Pure: it reads nothing."""
    plan = RoundPlan(config, unparsed=list(config.unparsed))
    name = _concept_namer(config.aliases)
    forms = {form_key(f) for e in d.entries.values() for f in e.all_forms}   # grows as entries are accepted
    _collect_new_concepts(plan, config.verdicts, d, name)   # an entry may use another verdict's concept
    _prepare_concept_fixes(plan, d)
    plan.style_guide = [(v.get("candidate"), v.get("guidance")) for _, v in config.verdicts
                        if v.get("decision") == "style_guide"]
    _accept_entries(plan, config, d, name, forms)
    _add_triggers(plan, config, d, name, forms)
    _guard_new_concept_triggers(plan, forms, config.queries)
    _drop_unused_new_concepts(plan)
    _guard_replaces(plan, forms, config.queries)
    _apply_trigger_fixes(plan, config.trigger_fixes, d)
    return plan


def _concept_namer(aliases: dict[str, str]):
    def name(c: str) -> str:   # NEW:X -> X, then hand-consolidated synonyms
        c = c.split(":", 1)[1] if str(c).startswith("NEW:") else c
        return aliases.get(c, c)
    return name


def _trigger_rejection(phrase: str, forms: set[str], queries: set[str], own_form: str | None = None) -> str | None:
    """Why a plain-English trigger or `replaces` paraphrase can't be used: it is itself an Aussie form (it would swap
    slang for slang), or copies a reference query word for word (it would teach to the test). An entry's own form
    may stand in its replaces."""
    key = form_key(phrase)
    if key in forms and key != own_form:
        return "is an Aussie form"
    if key in queries:
        return "copies a reference query"
    return None


CONCEPT_KEYS = frozenset(f.name for f in fields(Concept)) - {"id"}


def _concept_patch(raw: dict, where: str) -> dict:
    if not isinstance(raw, dict) or set(raw) - CONCEPT_KEYS:
        raise SchemaError(f"{where}: expected concept fields {', '.join(sorted(CONCEPT_KEYS))}")
    return deepcopy(raw)


def _collect_new_concepts(plan: RoundPlan, verdicts: list[tuple[str, dict]], d: Dictionary, name) -> None:
    for _, v in verdicts:
        nc = v.get("new_concept")
        if v.get("decision") in ("add_entry", "gate") and nc and nc.get("id") and name(nc["id"]) not in d.concepts:
            cid = name(nc["id"])
            raw = _concept_patch({k: value for k, value in nc.items() if k != "id"}, f"new concept {cid}")
            parse_concept(cid, raw)
            cur = plan.new_concepts.setdefault(cid, {"description": "", "triggers": {}})
            cur.update({k: value for k, value in raw.items() if k != "triggers"})
            for frame, ps in (raw.get("triggers") or {}).items():
                cur["triggers"].setdefault(frame, [])
                cur["triggers"][frame] += [p for p in ps or () if p not in cur["triggers"][frame]]


def _prepare_concept_fixes(plan: RoundPlan, d: Dictionary) -> None:
    if not isinstance(plan.config.concept_fixes, dict):
        raise SchemaError("concept_fixes.yaml: expected a mapping by concept id")
    for cid, patch in plan.config.concept_fixes.items():
        patch = _concept_patch(patch, f"concept_fixes.yaml {cid}")
        if cid not in d.concepts:
            raw = plan.new_concepts.setdefault(cid, {"description": "", "triggers": {}})
            raw.update(patch)
            raw["triggers"] = raw.get("triggers") or {}
        else:
            concept = d.concepts[cid]
            raw = {f.name: getattr(concept, f.name) for f in fields(Concept) if f.name != "id"}
            raw["triggers"] = {frame: list(patterns) for frame, patterns in concept.triggers.items()}
            raw.update(patch)
        parse_concept(cid, raw)


def _accept_entries(plan: RoundPlan, config: RoundConfig, d: Dictionary, name, forms: set[str]) -> None:
    """The proposed entries, with fixes applied, minus any whose form or id is taken or whose concepts are unknown.
    Accepted forms are added to forms."""
    ids = set(d.entries)
    meanings = {}
    for entry in d.entries.values():
        for form in entry.all_forms:
            meanings.setdefault(form_key(form), set()).update(entry.concept)
    proposed = [(src, v, dict(v["entry"])) for src, v in config.verdicts
                if v.get("decision") in ("add_entry", "gate") and v.get("entry")]
    proposed += [("extra_entries", {"decision": "add_entry"}, dict(e)) for e in config.extra_entries]
    for src, v, e in proposed:
        allow_existing = v.get("allow_existing_form", e.pop("allow_existing_form", False))
        if not isinstance(allow_existing, bool):
            raise SchemaError(f"{src}: allow_existing_form must be a boolean")
        e["concept"] = list(dict.fromkeys(name(c) for c in e.get("concept") or ()))
        e.update(config.entry_fixes.get(e.get("id"), {}))
        if v.get("decision") == "gate" or v.get("confidence") == "low":   # a low-confidence accept ships gated
            e["status"] = "gate"
            e.setdefault("flags", ["dubious_meaning"])
        e = {k: e[k] for k in ENTRY_KEYS if k in e and e[k] not in (None, [], "")}
        if e.get("id") in ids:
            e["id"] += config.id_suffix
            if e["id"] in ids:
                plan.dropped.append(("entry", e.get("id"), "id taken", src))
                continue
        try:
            parse_entry(e, config.output)
        except SchemaError as exc:
            plan.dropped.append(("entry", e.get("id"), f"schema: {exc}", src))
            continue
        keys = {form_key(f) for f in [e["form"], *(e.get("variants") or ())]}
        collisions = {form_key(e["form"])} & forms
        if collisions and not (allow_existing and all(set(e.get("concept", ())) - meanings.get(k, set())
                                                       for k in collisions)):
            plan.dropped.append(("entry", e.get("id"), "form already in the dictionary", src))
            continue
        if not e.get("concept") and e.get("type") != "garnish":   # garnish may carry no concept ("ya galah")
            plan.dropped.append(("entry", e.get("id"), "no concept", src))
            continue
        unknown = [c for c in e.get("concept", []) if c not in d.concepts and c not in plan.new_concepts]
        if unknown:
            plan.dropped.append(("entry", e["id"], f"unknown concept {unknown[0]}", src))
            continue
        forms |= keys
        for key in keys:
            meanings.setdefault(key, set()).update(e.get("concept", ()))
        ids.add(e["id"])
        plan.entries.append(e)


def _add_triggers(plan: RoundPlan, config: RoundConfig, d: Dictionary, name, forms: set[str]) -> None:
    """The verdicts' triggers_to_add, onto new concepts or as additions to existing ones."""
    triggers: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for src, v in config.verdicts:
        for cid, frames in (v.get("triggers_to_add") or {}).items():
            for frame, ps in (frames or {}).items():
                for p in ps or ():
                    triggers.setdefault((name(cid), frame), []).append((p, src))
    new_concepts, added = plan.new_concepts, plan.added_triggers
    have = {cid: {form_key(p) for ps in c.triggers.values() for p in ps} for cid, c in d.concepts.items()}
    for (cid, frame), ps in sorted(triggers.items()):
        if cid not in d.concepts and cid not in new_concepts:
            plan.dropped.append(("trigger", f"{cid}.{frame}", "unknown concept", ps[0][1]))
            continue
        target = new_concepts[cid]["triggers"] if cid in new_concepts else None
        for p, src in ps:
            why = _trigger_rejection(p, forms, config.queries)
            if why:
                plan.dropped.append(("trigger", f"{cid}.{frame}: {p}", why, src))
                continue
            n = form_key(p)
            if n in have.get(cid, set()) or (target and p in target.get(frame, [])):
                continue   # already a trigger: nothing to add or report
            if cid in new_concepts:
                new_concepts[cid]["triggers"].setdefault(frame, []).append(p)
            elif p not in added.setdefault(cid, {}).setdefault(frame, []):
                added[cid][frame].append(p)
            have.setdefault(cid, set()).add(n)


def _guard_new_concept_triggers(plan: RoundPlan, forms: set[str], queries: set[str]) -> None:
    """New concepts' own triggers get the same guards, and lose duplicates."""
    for cid, c in plan.new_concepts.items():
        for frame in list(c["triggers"]):
            keep = []
            for p in c["triggers"][frame]:
                why = _trigger_rejection(p, forms, queries)
                if why:
                    plan.dropped.append(("trigger", f"{cid}.{frame}: {p}", why, "new_concept"))
                elif p not in keep:
                    keep.append(p)
            c["triggers"][frame] = keep


def _drop_unused_new_concepts(plan: RoundPlan) -> None:
    for cid in [cid for cid in plan.new_concepts if cid not in plan.config.concept_fixes
                and not any(cid in e.get("concept", []) for e in plan.entries)]:
        plan.dropped.append(("concept", cid, "no accepted entry uses it", "-"))
        del plan.new_concepts[cid]


def _guard_replaces(plan: RoundPlan, forms: set[str], queries: set[str]) -> None:
    """Replaces are triggers too, so they get the same guards."""
    for e in plan.entries:
        keep = []
        for r in e.get("replaces") or ():
            why = _trigger_rejection(r, forms, queries, own_form=form_key(e["form"]))
            if why:
                plan.dropped.append(("replaces", f"{e['id']}: {r}", why, "-"))
            else:
                keep.append(r)
        if keep:
            e["replaces"] = keep
        else:
            e.pop("replaces", None)


def _without_intensity(pattern: str) -> str:
    return re.sub(r"@[1-5]$", "", pattern)


def _fixed_triggers(triggers: dict, cid: str, fixes: dict, existing: dict | None = None) -> dict:
    """Explicit review instructions applied to proposed or preserved triggers, without regenerating metadata."""
    result = deepcopy(triggers)
    for frame, patterns in (fixes.get("remove", {}).get(cid) or {}).items():
        result[frame] = [p for p in result.get(frame, ())
                         if p not in patterns and _without_intensity(p) not in patterns]
    for frame, patterns in (fixes.get("add", {}).get(cid) or {}).items():
        have = {form_key(p) for p in (existing or {}).get(frame, ())}
        added = [p for p in patterns if form_key(p) not in have]
        added_keys = {_without_intensity(p) for p in added}
        result[frame] = added + [p for p in result.get(frame, ()) if _without_intensity(p) not in added_keys]
    strength = fixes.get("intensity") or {}
    for frame, patterns in result.items():
        rewritten = []
        for pattern in patterns:
            base = _without_intensity(pattern)
            intensity = strength.get(pattern, strength.get(base))
            rewritten.append(f"{base}@{intensity}" if intensity is not None else pattern)
        result[frame] = rewritten
    return {frame: patterns for frame, patterns in result.items() if patterns}


def _apply_trigger_fixes(plan: RoundPlan, tf: dict, d: Dictionary) -> None:
    for cid, concept in plan.new_concepts.items():
        concept["triggers"] = _fixed_triggers(concept["triggers"], cid, tf)
    targets = set(plan.added_triggers) | set(tf.get("remove") or {}) | set(tf.get("add") or {})
    for cid in targets - plan.new_concepts.keys():
        if cid not in d.concepts:
            raise SchemaError(f"trigger_fixes.yaml: unknown concept {cid}")
        fixed = _fixed_triggers(plan.added_triggers.get(cid, {}), cid, tf, d.concepts[cid].triggers)
        if fixed:
            plan.added_triggers[cid] = fixed
        else:
            plan.added_triggers.pop(cid, None)
