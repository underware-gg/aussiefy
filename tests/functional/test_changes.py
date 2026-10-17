"""The `changes` contract: every change a translation made, placed in its output, with each spot's alternatives and
locked options rendered where they stand (aussiefy.translate_changes; DD-029). The renderings are checked against
whole pinned re-renders in test_changes_oracle.py."""

import inspect
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import aussiefy
from aussiefy import changes as C
from aussiefy import harness
from aussiefy.cards import entry_card
from aussiefy.policy import resolve
from aussiefy.select import fit_rejection, policy_rejection

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "changes"
sys.path.insert(0, str(ROOT / "scripts"))

from regen_changes_fixtures import CASES, build as fixture  # noqa: E402

KINDS = json.loads((FIXTURES / "every-kind.json").read_text(encoding="utf-8"))["request"]


def _every_kind(translator):
    options = {k: v for k, v in KINDS.items() if k != "text"}
    return aussiefy.translate_changes(KINDS["text"], translator=translator, **options)


def _schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(C.SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema, schema


def test_the_python_api_takes_translates_parameters():
    def params(fn):
        return {n: p.default for n, p in inspect.signature(fn).parameters.items()}

    assert params(aussiefy.translate_changes) == params(aussiefy.translate)
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY
               for n, p in inspect.signature(aussiefy.translate_changes).parameters.items() if n != "text")


def test_changes_leave_the_translation_as_translate_gives_it(translator):
    options = {k: v for k, v in KINDS.items() if k != "text"}
    assert _every_kind(translator).text == aussiefy.translate(KINDS["text"], translator=translator, **options).text


@pytest.mark.parametrize("mode", [{}, {"markup": "markdown"}, {"markdown": True}])
@pytest.mark.parametrize("prefix", ["🦘", "e\u0301", "👨‍👩‍👧‍👦"])
def test_change_offsets_count_unicode_code_points(translator, mode, prefix):
    cs = aussiefy.translate_changes(prefix + " toilet", translator=translator, level=4, vulgarity=0,
                                    embellishment=0, **mode)
    assert cs.text == prefix + " dunny"
    change, = cs.changes
    start = len(prefix) + 1
    assert change["src_span"] == [start, start + 6]
    assert change["out_span"] == [start, start + 5]
    assert change["original"] == "toilet" and change["output"] == "dunny"
    own = next(o for o in change["alternatives"] if o["entry_id"] == change["entry_id"])
    assert own["out_span"] == change["out_span"] and own["rendered"] == "dunny"


def test_every_kind_is_placed_in_the_output(translator):
    cs = _every_kind(translator)
    seen = {c["kind"] + (f":{c['placement']}" if c["kind"] == "garnish" else "") for c in cs.changes}
    assert seen >= {"substitution", "dialect", "phonetic", "swear_infix", "garnish:opener", "garnish:connective",
                    "garnish:tag", "garnish:tail", "garnish:aside", "garnish:closer", "garnish:riff"}
    text, source = cs.text, KINDS["text"]
    for c in cs.changes:
        a, b = c["out_span"]
        assert text[a:b] == c["output"], c["id"]
        if c["kind"] in ("substitution", "dialect"):
            assert source[slice(*c["src_span"])] == c["original"] and c["output"] != c["original"], c["id"]
        if c["kind"] == "garnish":
            assert c["src_span"][0] == c["src_span"][1] and c["original"] == ""
        if c["kind"] in ("phonetic", "swear_infix"):
            rule = c["rule"]
            assert rule["after"] in c["output"] or c["covers"] or any(c["id"] in d["covers"] for d in cs.changes)
            assert (c["kind"] == "swear_infix") == (rule["kind"] == "infix") and c["vulgarity"] >= (rule["kind"] == "infix")
        if c["kind"] == "dialect":
            assert c["pair"]["english"] == "us" and c["pair"]["after"] == c["output"]


def test_every_swap_and_removal_reads_true_in_place(translator):
    """Swapping any one alternative, locked option or removal into the output changes only its span, and the
    pick's own rendering is the output there."""
    cs = _every_kind(translator)
    for c in cs.changes:
        for o in c["alternatives"]:
            if o["entry_id"] == c["entry_id"]:
                assert cs.text[slice(*o["out_span"])] == o["rendered"], c["id"]
        for o in c["alternatives"] + c["locked"] + ([c["removed"]] if c.get("removed") else []):
            a, b = o["out_span"]
            assert a <= c["out_span"][0] <= c["out_span"][1] <= b, c["id"]
        if c.get("removed"):
            a, b = c["removed"]["out_span"]
            rest = cs.text[:a] + c["removed"]["rendered"] + cs.text[b:]
            assert len(rest) < len(cs.text) and c["output"].strip(" ,.") not in rest[a - 2:a + 2]


@pytest.mark.parametrize("text, options, original, alternatives", [
    # "a" turns "an" with the alternative after it, taking the article into the span
    ("We let a toddler win the game.", {"level": 5, "vulgarity": 1}, "a toddler",
     {"nipper": "a nipper", "ankle-biter": "an ankle biter"}),
])
def test_an_alternative_fits_its_article(translator, text, options, original, alternatives):
    cs = aussiefy.translate_changes(text, translator=translator, **options)
    c = next(c for c in cs.changes if c["kind"] == "substitution" and c["original"] == original)
    got = {o["entry_id"]: o["rendered"] for o in c["alternatives"]}
    assert all(got[k] == v for k, v in alternatives.items()), got


def test_stacked_idioms_riffs_and_infixes_count_in_a_renderings_vulgarity(translator, dictionary):
    cs = _every_kind(translator)
    subs = [c for c in cs.changes if c["kind"] == "substitution"]
    assert any(", " in o["rendered"] for c in subs for o in c["alternatives"])   # a stack or a riff
    for c in subs:
        for o in c["alternatives"]:
            assert o["vulgarity"] >= dictionary.entries[o["entry_id"]].vulgarity
            infixes = [d for d in cs.changes if d["kind"] == "swear_infix" and d["id"] in c["covers"]]
            if o["entry_id"] == c["entry_id"]:
                assert c["vulgarity"] == o["vulgarity"] >= max([d["vulgarity"] for d in infixes], default=0)
    for d in (d for d in cs.changes if d["kind"] == "swear_infix"):
        assert d["vulgarity"] == next(r.vulgarity for r in dictionary.phonetic if r.id == d["rule"]["id"]) > 0


def test_a_swaps_region_covers_the_changes_inside_it(translator):
    cs = _every_kind(translator)
    ids = {c["id"]: c for c in cs.changes}
    assert any(c["covers"] for c in cs.changes if c["kind"] == "substitution")
    for c in cs.changes:
        for inner in c["covers"]:
            d = ids[inner]
            spans = [c["out_span"]] + [o["out_span"] for o in c["alternatives"] + c["locked"]]
            assert min(s[0] for s in spans) <= d["out_span"][0] <= d["out_span"][1] <= max(s[1] for s in spans)


def test_ids_are_unique_and_named_by_kind_and_source_span(translator):
    cs = _every_kind(translator)
    ids = [c["id"] for c in cs.changes]
    assert len(ids) == len(set(ids))
    for c in cs.changes:
        assert c["id"].startswith(f"{c['kind']}:{c['src_span'][0]}-{c['src_span'][1]}")


def test_ids_and_renderings_are_the_same_in_every_process():
    code = ("import json, aussiefy; from regen_changes_fixtures import build; "
            "print(json.dumps(build('every-kind')['response'], sort_keys=True))")
    outs = set()
    for hashseed in ("0", "1", "4242"):
        env = {**os.environ, "PYTHONHASHSEED": hashseed, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": os.pathsep.join([str(ROOT / "scripts"), str(ROOT)])}
        outs.add(subprocess.run([sys.executable, "-c", code], env=env, check=True, capture_output=True,
                                text=True).stdout)
    assert len(outs) == 1


def test_locked_options_pass_every_check_at_their_tagged_vulgarity(translator, dictionary):
    """A locked option is held back by the vulgarity cap alone: at the vulgarity it's tagged with, the policy and
    the grammar both take it, and at the one below they don't."""
    checked = 0
    for name, (_, request) in CASES.items():
        options = {k: v for k, v in request.items() if k != "text"}
        watch = C.Watch()
        result, raw = C.collect(translator, request["text"], _observer=watch,
                                **{k: v for k, v in options.items() if k != "markdown"})
        run = watch.run
        spots = {(s.rec.span): s for s in watch.spots if s.rec.substituted}
        for c in raw:
            for o in c["locked"]:
                spot = next(s for s in spots.values() if c["src_span"][0] <= s.rec.span[0] < c["src_span"][1])
                entry, v = dictionary.entries[o["entry_id"]], o["vulgarity"]
                at = resolve(replace(run.pol, vulgarity=entry.vulgarity), dictionary)
                assert entry.vulgarity > run.eff.vulgarity and entry.vulgarity <= v
                assert policy_rejection(entry, at) is None
                assert fit_rejection(entry, spot.rec.det, at, dictionary.person_concepts, dictionary.person_nouns) is None
                below = resolve(replace(run.pol, vulgarity=entry.vulgarity - 1), dictionary)
                assert policy_rejection(entry, below).startswith("vulgarity")
                checked += 1
    assert checked >= 5


def test_locked_options_follow_the_gates_in_effect(translator):
    """A gated entry is never offered behind a lock, unless the caller unlocked it (a local --unlock)."""
    d = translator.dictionary
    for text, gated in (("He's a rascal.", "cheeky-bugger"), ("I am broke this week.", "on-the-bones-of-arse")):
        plain = aussiefy.translate_changes(text, translator=translator, level=5, vulgarity=0)
        unlocked = aussiefy.translate_changes(text, translator=translator, level=5, vulgarity=0, unlock=["all"])
        assert d.entries[gated].status == "gate"
        assert gated not in {o["entry_id"] for c in plain.changes for o in c["alternatives"] + c["locked"]}
        assert gated in {o["entry_id"] for c in unlocked.changes for o in c["locked"]}


def test_cards_are_lookups(translator, dictionary):
    """The entries a changes response sends are the cards lookup shows for the same entries (aussiefy.cards)."""
    cs = _every_kind(translator)
    cap = KINDS["vulgarity"]
    matched = 0
    for entry_id, card in cs.entries.items():
        assert card == entry_card(dictionary.entries[entry_id], cap)
        e = dictionary.entries[entry_id]
        found = [r for r in harness.lookup(e.form, level=5, vulgarity=cap, limit=50, translator=translator)["results"]
                 if r["id"] == entry_id]
        if found:
            assert {k: v for k, v in found[0].items() if k not in ("match", "score")} == card
            matched += 1
    assert matched >= len(cs.entries) // 2


def test_the_contract_validates_against_its_schema(translator):
    jsonschema, schema = _schema()
    jsonschema.validate(_every_kind(translator).to_dict(), schema)
    jsonschema.validate(aussiefy.translate_changes("", translator=translator).to_dict(), schema)


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_fixtures_are_what_the_builder_returns(translator, name):
    """The fixtures a service builds against: valid under the schema, and current (scripts/regen_changes_fixtures.py
    rewrites them when a change means to alter them)."""
    jsonschema, schema = _schema()
    stored = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    jsonschema.validate(stored["response"], schema)
    assert stored == json.loads(json.dumps(fixture(name, translator))), \
        "the changes fixtures drifted: run scripts/regen_changes_fixtures.py and review the diff"


def test_a_rewriter_has_no_changes(translator):
    class Rewriter:
        model = "test"

        def rewrite(self, *a, **k):
            return None, "kept"

    with pytest.raises(ValueError, match="rewriter"):
        C.build(translator, "She was tired.", rewriter=Rewriter())
    with pytest.raises(aussiefy.UserError, match="rewrite"):
        from aussiefy.translation import run

        run("She was tired.", translator=translator, rewrite="hard", _changes=True)


# -- the Markdown route: protected spans restored, and document units composed ------------------------------------

DOCUMENT = ("# Notes\n\nI'm exhausted and the toilet is broken. See `make test` and [the docs](http://x.au/a_b).\n\n"
            "- You are very tired and hungry.\n- My friend's car is broken (really)!\n\nThe faucet is broken, mate.\n")


@pytest.mark.parametrize("mode", [{"markup": "markdown"}, {"markdown": True}])
def test_markdown_changes_keep_markup_and_read_true_in_place(translator, mode):
    cs = aussiefy.translate_changes(DOCUMENT, translator=translator, level=5, vulgarity=2, embellishment=2,
                                    english="us", **mode)
    assert cs.text == aussiefy.translate(DOCUMENT, translator=translator, level=5, vulgarity=2, embellishment=2,
                                         english="us", **mode).text
    assert {c["kind"] for c in cs.changes} >= {"substitution", "phonetic", "dialect"}
    for c in cs.changes:
        a, b = c["out_span"]
        assert cs.text[a:b] == c["output"], c["id"]
        if c["kind"] in ("substitution", "dialect"):
            assert DOCUMENT[slice(*c["src_span"])] == c["original"], c["id"]
        for o in c["alternatives"] + c["locked"]:
            x, y = o["out_span"]
            swapped = cs.text[:x] + o["rendered"] + cs.text[y:]
            assert "`make test`" in swapped and "[the docs](http://x.au/a_b)" in swapped and swapped.startswith("# Notes")
            if o["entry_id"] == c["entry_id"]:
                assert swapped == cs.text
    if mode.get("markdown"):   # a unit's escaping applies to what's swapped in too
        bang = next(c for c in cs.changes if c["kind"] == "substitution" and "broken" in c["original"]
                    and "really" in DOCUMENT[c["src_span"][1]:c["src_span"][1] + 10])
        assert cs.text[bang["out_span"][1]:].startswith(" \\(really\\)")
    jsonschema, schema = _schema()
    jsonschema.validate(cs.to_dict(), schema)


def test_a_markdown_unit_renders_as_the_engine_would_there(translator):
    """Within a document, each unit's changes are the unit's own, offset into the document and escaped."""
    from aussiefy.markdown import _escape, _escape_map

    for text in ("1. Not a list", "  lead and *stars*  \r\nnext\nline", "a_b (c) [d] #e", ""):
        escaped, at = _escape_map(text)
        assert escaped == _escape(text) and len(at) == len(text) + 1 and at == sorted(at) and at[-1] == len(escaped)
