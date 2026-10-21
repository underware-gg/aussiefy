"""Apply the reviewed, complete-sense cohort from the frozen inherited-source audit.

Run from the repo root; without --apply this only reports the proposed data changes.
The ledger retains partial, variant, inaccessible and disputed references for later review.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aussiefy.dump import dump_yaml  # noqa: E402
from aussiefy.evidence import SUPPORTS, parse_sources  # noqa: E402
from aussiefy.loader import DATA_DIR, write_validated  # noqa: E402

HERE = Path(__file__).parent


def replace_sources(text, rows):
    """Replace only the sources field in affected entry mappings, retaining other bytes."""
    document = yaml.compose(text, Loader=yaml.SafeLoader)
    edits = []
    for entry, raw in zip(document.value, yaml.safe_load(text), strict=True):
        keys = {key.value: (key, value) for key, value in entry.value}
        eid = keys["id"][1].value
        if eid not in rows or "sources" not in keys:
            continue
        key, value = keys["sources"]
        start = text.rfind("\n", 0, key.start_mark.index) + 1
        # A block node may consume the indentation of the following field.
        end = value.end_mark.index
        if text[text.rfind("\n", 0, end) + 1:end].strip() == "":
            end = text.rfind("\n", 0, end) + 1
        elif end < len(text) and text[end] == "\n":
            end += 1
        sources = [rows[eid].get(source["url"], source) for source in raw.get("sources", [])]
        replacement = "".join("  " + line if line.strip() else line
                              for line in dump_yaml({"sources": sources}).splitlines(keepends=True))
        edits.append((start, end, replacement))
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text


def propose():
    audit = json.loads((HERE / "inherited-source-audit.json").read_text())
    policy = json.loads((HERE / "source-integration-policy.json").read_text())
    base = audit["repository_at_completion"]

    def baseline(path):
        return subprocess.check_output(["git", "show", f"{base}:{path.relative_to(ROOT)}"],
                                       cwd=ROOT, text=True)

    sidecar_path = DATA_DIR / "sources.yaml"
    sidecar = yaml.safe_load(baseline(sidecar_path))
    originals = {}
    targets = {}
    paths = sorted((DATA_DIR / "entries").glob("*.yaml"))
    stored = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", base,
                                      "--", "aussiefy/data/entries"], cwd=ROOT, text=True).splitlines()
    expected = {ROOT / path for path in stored if path.endswith((".yaml", ".yml"))}
    live = set(paths) | set((DATA_DIR / "entries").glob("*.yml"))
    if live != expected:
        raise ValueError("entry files changed since the frozen inventory; review before replaying")
    entry_texts = {path: baseline(path) for path in paths}
    for path, text in entry_texts.items():
        original = yaml.safe_load(text)
        current = yaml.safe_load(path.read_text())
        without_sources = lambda entries: [{key: value for key, value in entry.items() if key != "sources"}
                                           for entry in entries]
        if without_sources(original) != without_sources(current):
            raise ValueError(f"{path.relative_to(ROOT)}: non-source entry fields changed; refusing replay")
        for raw in original:
            targets[raw["id"]] = raw
            for source in raw.get("sources", []):
                originals.setdefault((raw["id"], source["url"]), source)
    for eid, sources in sidecar.items():
        for source in sources:
            originals.setdefault((eid, source["url"]), source)

    deferred = {(row["id"], row["url"]) for row in policy["deferred_pairs"]}
    updates = {}
    selected = []
    skipped = Counter()
    for row in audit["checks"]:
        pair = row["id"], row["url"]
        if row["id"] not in targets:
            skipped["imagery_separate_cohort"] += 1
            continue
        if row["status"] != "sense_confirmed" or pair in deferred:
            skipped[row["status"]] += 1
            continue
        target = targets[row["id"]]
        snapshot = row["target"]
        for key in ("form", "gloss", "concept", "frame", "variants", "spellings", "plural"):
            if target.get(key) != snapshot.get(key):
                raise ValueError(f"{row['id']}: audited {key} changed; review the evidence again")
        if not row.get("inspected"):
            raise ValueError(f"{pair}: complete-sense support needs an actual inspection")
        previous = originals.get(pair, {})
        group = row.get("independence_group")
        publisher = policy["publisher_groups"].get(group)
        if publisher is None:
            publisher = previous.get("publisher", urlsplit(row["url"]).hostname.removeprefix("www."))
        kind = policy["kind_groups"].get(group, previous.get("kind", "media"))
        if group == "andc" and "/australian-words-" in row["url"]:
            kind = "scholarly_dictionary"
        kind = policy["kind_urls"].get(row["url"], kind)
        supports = set(previous.get("supports", [])) | set(row["supports"])
        cited_date = previous.get("cited_date")
        reported_date = row.get("date", {})
        value = reported_date.get("value", "")
        if "date" in row["supports"] and re.fullmatch(r"\d{4}(?:s|[–-]\d{4}|-\d{2}-\d{2})?", value):
            cited_date = value
        if not cited_date:
            supports.discard("date")
        notes = [f"Reviewed {row['inspected']}: selected form/sense; {row['locator']}."]
        if row.get("assessment"):
            notes.append(row["assessment"])
        if reported_date:
            notes.append(f"Reported date: {value} ({reported_date['kind']}); not a claim of absolute first use.")
        if group:
            notes.append(f"Source family: {group}; not a current-commonness survey.")
        source = {"url": row["url"], "kind": kind, "publisher": publisher,
                  "supports": [name for name in SUPPORTS if name in supports], "note": " ".join(notes)}
        if cited_date:
            source["cited_date"] = cited_date
        parse_sources([source], row["id"])
        updates.setdefault(row["id"], {})[row["url"]] = source
        selected.append({"id": row["id"], "url": row["url"], "supports": source["supports"]})

    for eid, sources in updates.items():
        current = sidecar.setdefault(eid, [])
        existing = {source["url"] for source in current}
        sidecar[eid] = [sources.get(source["url"], source) for source in current]
        # Inline-only references stay inline, rather than creating a second stored citation.
        sidecar[eid].extend(source for url, source in sources.items()
                            if url not in existing and (eid, url) not in originals)
        if not sidecar[eid]:
            del sidecar[eid]

    files = {"sources.yaml": "# Structured supplemental citations. Empty supports remains reference-only.\n" + dump_yaml(sidecar)}
    for path, before in entry_texts.items():
        after = replace_sources(before, updates)
        if before != after:
            files[str(path.relative_to(DATA_DIR))] = after
    manifest = {"selected_pairs": len(selected), "selected_ids": len(updates),
                "deferred_statuses": dict(sorted(skipped.items())), "selected": selected}
    return files, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    files, manifest = propose()
    if args.apply:
        audit = json.loads((HERE / "inherited-source-audit.json").read_text())
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if head != audit["repository_at_completion"]:
            parser.error("this one-off migration applies only on its frozen inventory commit")
        write_validated(DATA_DIR, files)
        (HERE / "source-integration-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in manifest.items() if key != "selected"}, indent=2))
