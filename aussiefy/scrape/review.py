"""Turn tagged proposals into a reviewable diff against the dictionary, and apply it."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..dump import dump_entries, dump_yaml
from ..loader import DATA_DIR, write_validated
from ..model import Dictionary
from ..schema import parse_entry

SCRAPED_HEADER = """# Entries accepted from the scrape/tag/review pipeline. Machine-managed:
# `aussiefy dev review --apply` rewrites this file. Move an entry to a hand-curated
# file once you have edited it by hand."""
SOURCES_HEADER = """# Extra source URLs per entry id, written by `aussiefy dev review --apply`.
# Kept separate so hand-curated entry files are never rewritten."""


@dataclass
class ReviewPlan:
    data_dir: Path
    scraped_path: Path
    sources_path: Path
    old_scraped: str
    new_scraped: str
    old_sources: str
    new_sources: str
    summary: list[str]

    def diff(self) -> str:
        parts = []
        for path, old, new in ((self.scraped_path, self.old_scraped, self.new_scraped),
                               (self.sources_path, self.old_sources, self.new_sources)):
            parts.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                              fromfile=f"a/{path.name}", tofile=f"b/{path.name}"))
        return "".join(parts)

    def apply(self, extra: tuple = ()) -> Dictionary:
        """Write both files, after the dictionary they make has loaded in a scratch copy. Returns it."""
        return write_validated(self.data_dir, {str(self.scraped_path.relative_to(self.data_dir)): self.new_scraped,
                                               str(self.sources_path.relative_to(self.data_dir)): self.new_sources},
                               extra)


def plan_review(tagged: list[dict], dictionary: Dictionary, data_dir: str | Path | None = None) -> ReviewPlan:
    data = Path(data_dir) if data_dir else DATA_DIR
    scraped_path = data / "entries" / "scraped.yaml"
    sources_path = data / "sources.yaml"
    old_scraped = scraped_path.read_text(encoding="utf-8") if scraped_path.exists() else ""
    old_sources = sources_path.read_text(encoding="utf-8") if sources_path.exists() else ""
    scraped: list[dict] = yaml.safe_load(old_scraped) or []
    overlay: dict[str, list[str]] = yaml.safe_load(old_sources) or {}
    by_id = {e["id"]: e for e in scraped}
    summary: list[str] = []

    for item in tagged:
        known = item.get("known_as")
        if known:
            entry = dictionary.entries.get(known)
            have = set(entry.sources if entry else ()) | set(overlay.get(known, []))
            new_urls = [u for u in item.get("sources", []) if u not in have]
            if known in by_id:
                by_id[known]["sources"] = list(dict.fromkeys(by_id[known].get("sources", []) + new_urls))
            elif new_urls:
                overlay[known] = list(dict.fromkeys(overlay.get(known, []) + new_urls))
            status = item.get("known_status")
            verb = "blocked (omitted)" if status == "omit" else f"already present ({status})"
            summary.append(f"{verb}: '{item['form']}' = {known}" + (f", +{len(new_urls)} source(s)" if new_urls else ""))
            continue
        item = parse_entry(item).to_dict()  # refuse anything that would not load; canonical field order
        current = by_id.get(item["id"])
        if current is None:
            by_id[item["id"]] = item
            scraped.append(item)
            summary.append(f"new {item.get('status', 'active')}: {item['id']} '{item['form']}'"
                           + (f" [{', '.join(item['flags'])}]" if item.get("flags") else ""))
        else:
            # a re-tag never overrides human edits: only fill blanks and merge sources/variants
            for key, value in item.items():
                if key in ("sources", "variants"):
                    current[key] = list(dict.fromkeys(current.get(key, []) + value))
                elif not current.get(key) and value:
                    current[key] = value
            summary.append(f"updated: {item['id']} (sources/variants merged, human edits kept)")

    clean = [{k: v for k, v in e.items() if v not in ([], "", None) or k in ("concept",)} for e in scraped]
    new_scraped = dump_entries(clean, SCRAPED_HEADER) if clean else SCRAPED_HEADER + "\n[]\n"
    new_sources = SOURCES_HEADER + "\n" + (dump_yaml(overlay) if overlay else "{}\n")
    return ReviewPlan(data, scraped_path, sources_path, old_scraped, new_scraped, old_sources, new_sources, summary)
