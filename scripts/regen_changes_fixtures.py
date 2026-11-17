"""Regenerate the `changes` contract fixtures (tests/fixtures/changes/*.json): one request and its response each,
which tests/functional/test_changes.py checks against the JSON Schema and the current builder. Run it when a change
to the engine or the dictionary deliberately alters them, and review the diff. A service that builds on the
contract reads these fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIXTURES = ROOT / "tests" / "fixtures" / "changes"

STRESS = {"stack": 0.9, "garnish": {"riff": 1.0, "opener": 0.8, "tag": 0.8, "tail": 1.0, "connective": 0.6, "aside": 1.0},
          "max_garnish": {"riff": 30, "opener": 20, "tag": 20, "tail": 10, "aside": 10}, "garnish_gap": 0,
          "swearing": {"infix": 6.0, "exclaim": 0.5}}
# name -> (what it shows, translate_changes' arguments)
CASES = {
    "v4-owned": (
        "Source-owned swearing above the cap and ambiguous Australian meanings retain exact words and explicit English choices.",
        {"text": "Bugger me sideways! He is stonkered. Oi!", "level": 1, "vulgarity": 0, "embellishment": 0, "embedder": "none"}),
    "v4-held": (
        "A genuinely waiting meaning is held without masks or replacement rolls.",
        {"text": "Their loyalty never wavered.", "level": 1, "vulgarity": 0, "embellishment": 0, "embedder": "none"}),
    "v4-personal": (
        "Call-local wording, bound people and Markdown escaping, without invented dictionary IDs.",
        {"text": "🦘 She **adores Jane**. A spreadsheet. `spreadsheet`", "level": 1, "vulgarity": 0,
         "embellishment": 0, "markdown": True, "embedder": "none", "personal_terms": [
             {"phrase": "adore Jane", "term": "love the boss"}, {"phrase": "spreadsheet", "term": "number wrangler"}]}),
    "v4-near": (
        "An exact crying word stays separate from curated stand-ins, which cite each near option.",
        {"text": "They wept. She loved him wholeheartedly.", "level": 5, "vulgarity": 0,
         "embellishment": 2, "seed": 0, "embedder": "none", "document_config": {"garnish": [], "profile": {
             "phonetic": 0, "stack": 0, "substitution": {"lexical": 1, "phrase": 1, "idiom": 1}}}}),
    "v4-selected-reading": (
        "An explicit offered alternate reading retains both the inferred and selected meanings via existing source replay pins.",
        {"text": "He believes a liar.", "level": 5, "vulgarity": 0, "embellishment": 0, "embedder": "none"}),
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
    "v3-construction": (
        "A real reviewed constructed opener, with canonical and rendering-local part spans and maker labels.",
        {"text": "The river is flowing through the valley.", "level": 5, "vulgarity": 2,
         "seed": 0, "embellishment": 2, "document_config": {"garnish": ["opener"],
            "profile": {"garnish": {"opener": 0}, "max_garnish": {"opener": 1}, "swearing": {"exclaim": 1}}}}),
    "v3-markdown": (
        "Multiple real prose units, Unicode, emphasis, untouched code and local occurrence spans.",
        {"text": "# Heading\n\n🦘 She was **very tired**. `She is hungry.`\n\nHe is hungry and his car is broken.",
         "level": 5, "vulgarity": 2, "seed": 4, "embellishment": 2, "markdown": True}),
    "v3-imagery": (
        "A real contextual image has its own rich card and maker, alongside a retained source or substitution.",
        {"text": "She is hungry.", "level": 5, "vulgarity": 0, "seed": 0, "embellishment": 2,
         "document_config": {"garnish": ["riff"], "profile": {"garnish": {"riff": 1}}}}),
    "v3-warnings": (
        "Unknown preference records retain Result warnings and stable codes, even with no prose.",
        {"text": "`She is tired.`", "level": 5, "seed": 0, "markdown": True,
         "popularity": True, "preferences": [{"match": "not-a-match", "term": "missing-term", "weight": 2}]})

}


def build(name: str, translator=None) -> dict:
    from aussiefy import translate_changes

    about, request = CASES[name]
    request = dict(request)
    if name == 'v4-selected-reading':
        first = translate_changes(translator=translator, **request)
        held = next(c for c in first.changes if c['kind'] == 'held')
        word = next(word for reading in held['ruled_out'] for word in reading['words'] if word['entry_id'] == 'reckon')
        request['pins'] = first.replay_pins({held['id']: word['key']})
    options = {k: v for k, v in request.items() if k != "text"}
    return {"about": about, "request": request,
            "response": translate_changes(request["text"], translator=translator, **options).to_dict()}



def support(translator=None):
    from aussiefy import Translator, translate_changes
    from aussiefy.harness import lookup
    from aussiefy.match_keys import detection_match
    tr = Translator(translator.dictionary if translator else None, lookup_embedder=None)
    lookups = {"lookup_embedder": None, "cases": [
        {"request": {"query": query}, "response": lookup(query, translator=tr)}
        for query in ("knackered", "quantum entanglement")]}
    request = {"text": "She was exhausted. He is hungry.", "level": 5, "vulgarity": 2,
               "embellishment": 2, "variety": 1, "seed": 4}
    baseline = translate_changes(translator=tr, **request)
    match = detection_match(next(r for r in baseline.result.records if 'TIRED' in r.det.concepts).det).key
    tuned_request = {**request, "popularity": True,
                     "preferences": [{"match": match, "term": "stonkered-tired", "weight": 100000}]}
    tuned = translate_changes(translator=tr, **tuned_request)
    pins = tuned.replay_pins()
    untuned_request = {**request, "pins": pins}
    replay = translate_changes(translator=tr, **untuned_request)
    if replay.text != tuned.text:
        raise RuntimeError('real fixture did not replay exactly without tuning')
    return {"lookup.json": lookups,
            "replay.json": {"tuned_request": tuned_request, "tuned_response": tuned.to_dict(),
                            "untuned_request": untuned_request, "untuned_response": replay.to_dict(),
                            "editor_options": tuned.replay_options()}}


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name in CASES:
        path = FIXTURES / f"{name}.json"
        path.write_text(json.dumps(build(name), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    other = ROOT / "tests/fixtures/v3"
    other.mkdir(parents=True, exist_ok=True)
    for name, body in support().items():
        path = other / name
        path.write_text(json.dumps(body, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
