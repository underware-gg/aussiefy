"""Merge the five verifiers' verdicts into the round's one verdict file, with the integrator's choices.

    python integrate.py   # verify/raw/verdicts-*.yaml -> verify/verdicts-merged.yaml, americanisms.yaml

The slices were verified independently, so the same term came up several times under different new
concepts: keep one (KEEP picks the verdict, by slice and id). A plain US-to-Australian equivalent (faucet,
skillet, baking soda) goes to the dialect table instead of the dictionary (TO_DIALECT), and an entry whose
triggers can't be kept to its sense is dropped (DROP), with the reason; a trigger that catches the wrong
sense comes out (TRIM), with the reason.
"""

from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RAW = HERE / "verify" / "raw"

KEEP = {  # form -> the slice whose verdict wins
    "a chemist": "0", "bung {obj} in": "1", "a frypan": "0", "a muso": "2", "marg": "2", "fruit and veg": "1",
    "clapped-out": "1", "choc chips": "4", "{subj} {be} taking the piss": "0",
}
DROP = {
    "chuck {obj} in": "'chuck it in' is giving up: the slot can't keep it to putting something in",
    "a cracker of a {np}": "low confidence, and a slot inside a noun's form the engine doesn't fill",
    "{subj} {be} takin' the piss": "the same as 'taking the piss' (the drawl makes the dropped g)",
    "choc bits": "a variant of choc chips",
    "this {np} caper": "a slot inside a noun's form the engine doesn't fill",
}
TRIM = {  # concept or entry id -> triggers or replaces that catch the wrong sense
    "DISCARD": {"throw out {obj}": "'throw out a case', 'throw out the first pitch'",
                "throw {obj} out": "'throw him out' is ejecting a person"},
    "KEEP_QUIET": {"keep quiet": "a noise instruction ('keep quiet near the nest') isn't keeping mum"},
    "HIKER": {"backpacker !hostel|hostels": "an Aussie backpacker is a budget traveller, not a bushwalker"},
    "COMMON_SENSE": {"savvy !shopper|shoppers|investor|investors|consumer|consumers": "'she's very savvy' is an adjective"},
    "GET_DUMPED": {"be dumped": "'rubbish must not be dumped here' is waste, not a person"},
    "WORN_OUT_THING": {"run-down !by": "a run-down suburb isn't clapped-out, and a run-down person is tired"},
    "FUSS": {"shenanigans": "a mass noun: 'there were shenanigans' can't take 'a carry-on'",
             "tomfoolery": "a mass noun, as shenanigans"},
    "THINK": {"guess !what|who|where|when|which|how|why|the|a|an|right|wrong|correctly|again|at|my|his|her|their|your|its|our|so":
              "'you'll never guess' and 'can you guess' aren't reckoning"},
    "caper-racket": {"a scam !artist|artists|call|calls|email|emails|text|texts":
                     "'a caper' makes light of a fraud warning"},
}
TO_DIALECT = {  # plain equivalents: the dialect table swaps them at every level
    "a tap": ("faucet", "tap"), "a frypan": ("skillet", "frypan"), "bicarb soda": ("baking soda", "bicarb soda"),
    "queue up": ("stand in line", "queue up"),
}


def _trimmed(v: dict) -> dict:
    """The verdict without the triggers and replaces TRIM takes out."""
    entry, concept = v.get("entry") or {}, v.get("new_concept") or {}
    if entry.get("id") in TRIM:
        entry["replaces"] = [r for r in entry["replaces"] if r not in TRIM[entry["id"]]]
    if concept.get("id") in TRIM:
        concept["triggers"] = {frame: [t for t in ts if t not in TRIM[concept["id"]]]
                               for frame, ts in concept["triggers"].items()}
    added = v.get("triggers_to_add") or {}
    for cid in set(added) & set(TRIM):
        added[cid] = {frame: [t for t in ts if t not in TRIM[cid]] for frame, ts in added[cid].items()}
        added[cid] = {frame: ts for frame, ts in added[cid].items() if ts}
    v["triggers_to_add"] = {cid: frames for cid, frames in added.items() if frames}
    return v


def main() -> None:
    verdicts = []
    for path in sorted(RAW.glob("verdicts-*.yaml")):
        sl = path.stem.split("-")[1]
        verdicts += [{**v, "slice": sl} for v in yaml.safe_load(path.read_text(encoding="utf-8"))]
    merged, dialect = [], {}
    for v in verdicts:
        d = v["decision"]
        if d == "americanism":
            us = v["us"].strip()
            dialect.setdefault(us, v["australian"].split(" (")[0].strip())
            continue
        if d not in ("add_entry", "gate", "add_trigger", "style_guide"):
            continue
        form = (v.get("entry") or {}).get("form", "")
        if form in DROP:
            continue
        if form in TO_DIALECT:
            us, au = TO_DIALECT[form]
            dialect.setdefault(us, au)
            continue
        if form in KEEP and v["slice"] != KEEP[form]:
            continue
        merged.append(_trimmed({k: val for k, val in v.items() if k != "slice"}))
    (HERE / "verify" / "verdicts-merged.yaml").write_text(
        yaml.safe_dump(merged, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    (HERE / "americanisms.yaml").write_text(
        "# US -> Australian equivalents the verifiers found, for the dialect table\n"
        + yaml.safe_dump(dict(sorted(dialect.items())), allow_unicode=True, width=120), encoding="utf-8")
    entries = [v for v in merged if v["decision"] in ("add_entry", "gate")]
    print(f"{len(entries)} entries ({sum(v['decision'] == 'gate' for v in entries)} gated), "
          f"{sum(v['decision'] == 'add_trigger' for v in merged)} trigger sets, "
          f"{sum(v['decision'] == 'style_guide' for v in merged)} style notes, {len(dialect)} dialect swaps")


if __name__ == "__main__":
    main()
