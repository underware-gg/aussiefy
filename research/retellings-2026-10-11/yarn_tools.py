"""Yarn mode's tools on the command line, for an agent running the yarn loop without the Anthropic API.

A thin shell over aussiefy.yarn: brief() builds exactly what yarn mode sends the model, and dispatch_tool()
answers lookup, lint and submit exactly as the API loop does. Every call is appended to harnessed/NAME.log.jsonl.

    python3 yarn_tools.py brief  NAME                   # the system prompt and the user payload
    python3 yarn_tools.py lookup NAME "query"           # lookup
    python3 yarn_tools.py lint   NAME DRAFT             # lint (DRAFT is a file)
    python3 yarn_tools.py submit NAME DRAFT [DECLINED]  # submit: accepted (saved to harnessed/NAME.txt) or the
                                                        # problems; DECLINED is an optional YAML list of {phrase, reason}

NAME is a file in tests/corpus/reference/ (or, for a copyrighted text, tests/corpus/local/) without .txt. Level 5,
seed 0, as `aussiefy yarn` defaults. A copyrighted text's accepted yarn is saved locally instead, as
tests/corpus/local/NAME_yarn_harnessed.target.
"""

import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from aussiefy.yarn import brief, dispatch_tool  # noqa: E402

LEVEL, SEED = 5, 0
OUT = HERE / "harnessed"


def source(name: str) -> Path:
    """A reference text, or a copyrighted one in tests/corpus/local/ (fetched by aussiefy dev ingest)."""
    ref = ROOT / "tests" / "corpus" / "reference" / f"{name}.txt"
    return ref if ref.exists() else ROOT / "tests" / "corpus" / "local" / f"{name}.txt"


def log(name: str, entry: dict) -> None:
    OUT.mkdir(exist_ok=True)
    with (OUT / f"{name}.log.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def save(name: str, text: str) -> None:
    """Write an accepted yarn. A retelling of a copyrighted source stays local and uncommitted, next to its
    source (tests/corpus/local/NAME_yarn_harnessed.target); only a short excerpt is committed, by hand (see
    harnessed/moloch.txt)."""
    src = source(name)
    dest = src.with_name(f"{name}_yarn_harnessed.target") if src.parent.name == "local" else OUT / f"{name}.txt"
    dest.write_text(text + "\n", encoding="utf-8")


def main() -> None:
    cmd, name = sys.argv[1], sys.argv[2]
    session = brief(source(name).read_text(encoding="utf-8"), level=LEVEL, seed=SEED)
    if cmd == "brief":
        print("=== SYSTEM ===\n" + session.system)
        print("=== USER ===\n" + json.dumps(session.payload, ensure_ascii=False, indent=1))
        return
    if cmd == "lookup":
        args = {"query": sys.argv[3]}
    elif cmd in ("lint", "submit"):
        args = {"text": Path(sys.argv[3]).read_text(encoding="utf-8").strip()}
        if cmd == "submit":
            args["declined"] = (yaml.safe_load(Path(sys.argv[4]).read_text(encoding="utf-8")) or []
                                if len(sys.argv) > 4 else [])
    else:
        sys.exit(f"unknown command {cmd}")
    out, accepted = dispatch_tool(session, cmd, args)
    log(name, {"tool": cmd, **({"query": args["query"], "results": [r["form"] for r in out.get("results", [])]}
                               if cmd == "lookup" else {"issues": len(out.get("issues", []))} if cmd == "lint"
                               else out | {"declined": args.get("declined", [])})})
    if accepted:
        save(name, args["text"])
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
