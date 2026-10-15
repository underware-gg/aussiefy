"""Pool the gap-fill round's candidates: three blind rephrasings plus the web research.

    python3 research/gap-fill-2026-10-11/merge.py      # writes merged.yaml next to this file

For every Aussie term proposed anywhere: which gaps it was used for, which rephrasing agents used it
independently, whether the web research attests it (and its sources), and whether the dictionary already has
it. Agreement between independent agents, or an agent plus a web source, is what makes a candidate worth
verifying; one agent alone is noted but weaker.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from aussiefy.loader import load_dictionary  # noqa: E402


def norm(term: str) -> str:
    t = term.lower().replace("’", "'").strip(" .!?,\"")
    t = re.sub(r"\{[a-z]+\}|\b(your|my|his|her|their|our|one's)\b", "", t)   # "chuck a wobbly" ~ "chuck {poss} wobbly"
    t = re.sub(r"in'\b", "ing", t)
    t = re.sub(r"^(a|an|the|some) ", "", t)                                 # "a chinwag" ~ "chinwag"
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    d = load_dictionary()
    existing = {}
    for e in d.entries.values():
        for f in e.all_forms:
            existing.setdefault(norm(f), e.id)

    pool: dict[str, dict] = defaultdict(lambda: {"forms": set(), "gaps": set(), "agents": set(), "meanings": [],
                                                 "frames": set(), "vulgarity": set(), "web": None, "examples": []})
    for uses in sorted((HERE / "rephrasings").glob("*/uses.yaml")):
        agent = uses.parent.name
        data = yaml.safe_load(uses.read_text(encoding="utf-8")) or {}
        for u in data.get("uses") or ():
            for term in [u.get("used")] + list(u.get("also") or ()):
                if not term:
                    continue
                p = pool[norm(term)]
                p["forms"].add(term)
                p["gaps"].add(str(u.get("gap")))
                p["agents"].add(agent)
                if u.get("meaning"):
                    p["meanings"].append(u["meaning"])
                if u.get("frame"):
                    p["frames"].add(u["frame"])
                if u.get("vulgarity") is not None:
                    p["vulgarity"].add(u["vulgarity"])
                if term == u.get("used") and u.get("aussie_line"):
                    p["examples"].append(u["aussie_line"])
        for f in data.get("fillers") or ():
            p = pool[norm(f["form"])]
            p["forms"].add(f["form"])
            p["gaps"].add("filler:" + str(f.get("function", "?")))
            p["agents"].add(agent)
            p["frames"].add("garnish")
            if f.get("example"):
                p["examples"].append(f["example"])
    wf = HERE / "web" / "findings.yaml"
    web = (yaml.safe_load(wf.read_text(encoding="utf-8")) or []) if wf.exists() else []
    for w in web:
        p = pool[norm(w["term"])]
        p["forms"].add(w["term"])
        p["gaps"] |= {str(c) for c in w.get("covers") or ()}
        p["web"] = {k: w.get(k) for k in ("concept", "frame", "register", "region", "vulgarity", "incoherence",
                                          "sources", "confidence", "notes", "meaning")}
        p["meanings"].append(w.get("meaning"))

    out = []
    for key, p in pool.items():
        n_agents = len(p["agents"])
        support = n_agents + (1 if p["web"] and p["web"].get("sources") else 0)
        out.append({"term": sorted(p["forms"], key=len)[0], "key": key, "in_dictionary": existing.get(key),
                    "support": support, "agents": sorted(p["agents"]), "web": p["web"],
                    "gaps": sorted(p["gaps"]), "frames": sorted(p["frames"]),
                    "vulgarity_guesses": sorted(p["vulgarity"]), "meanings": [m for m in p["meanings"] if m][:4],
                    "examples": p["examples"][:3]})
    out.sort(key=lambda r: (r["in_dictionary"] is not None, -r["support"], r["key"]))
    (HERE / "merged.yaml").write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=110),
                                      encoding="utf-8")
    new = [r for r in out if not r["in_dictionary"]]
    print(f"{len(out)} terms; {len(new)} not in the dictionary; support >= 2: "
          f"{sum(r['support'] >= 2 for r in new)}; web-attested: {sum(bool(r['web']) for r in new)}")


if __name__ == "__main__":
    main()
