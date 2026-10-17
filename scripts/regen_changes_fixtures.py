"""Regenerate the `changes` contract fixtures (tests/fixtures/changes/*.json): one request and its response each,
which tests/functional/test_changes.py checks against the JSON Schema and the current builder. Run it when a change
to the engine or the dictionary deliberately alters them, and review the diff. A service that builds on the
contract reads these fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "changes"

STRESS = {"stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6, "aside": 1.0},
          "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10, "aside": 10}, "garnish_gap": 0,
          "swearing": {"infix": 6.0, "exclaim": 0.5}}
# name -> (what it shows, translate_changes' arguments)
CASES = {
    "every-kind": (
        "Every kind of change: swaps with alternatives, locked options and their masks, a stacked idiom and a riff; "
        "garnish of each placement, with removals; drawl and a swear infix inside a swap's region (covers); a US "
        "word swapped.",
        {"text": "Good grief, are you crazy? You're overreacting, you're stupid and all talk, and I'm extremely busy "
                 "cleaning up after you. I'm starving, let's get something to eat at McDonald's. The faucet in my "
                 "apartment is broken. Then they lost their tents and chairs. He is an idiot and a liar. Calm down and "
                 "stop complaining. I am going to the store.",
         "level": 5, "vulgarity": 1, "seed": 10, "embellishment": 2, "english": "us",
         "document_type": "general", "document_config": {"profile": STRESS}}),
    "site-defaults": (
        "The website's defaults: Larrikin, Dinkum, Dad, seed 0.",
        {"text": "I'm exhausted and the toilet is broken. Thanks for breakfast, my friend. You are very tired and "
                 "hungry, and your car is broken. We let a toddler win the game.",
         "level": 4, "vulgarity": 1, "seed": 0, "embellishment": 1}),
}


def build(name: str, translator=None) -> dict:
    from aussiefy import translate_changes

    about, request = CASES[name]
    options = {k: v for k, v in request.items() if k != "text"}
    return {"about": about, "request": request,
            "response": translate_changes(request["text"], translator=translator, **options).to_dict()}


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name in CASES:
        path = FIXTURES / f"{name}.json"
        path.write_text(json.dumps(build(name), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
