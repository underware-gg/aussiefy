"""The `changes` contract: every change a translation made, placed in its output, with each spot's alternatives and
locked options rendered where they stand (aussiefy.translate_changes; DD-029). The renderings are checked against
whole pinned re-renders in test_changes_oracle.py."""

import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from string import Formatter

import pytest

import aussiefy
from aussiefy import changes as C
from aussiefy import harness
from aussiefy.engine import PassObserver
from aussiefy.policy import resolve
from aussiefy.schema import PLACEHOLDER_RE
from aussiefy.terms import fold, restore_g

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "changes"
sys.path.insert(0, str(ROOT / "scripts"))

from regen_changes_fixtures import CASES, build as fixture  # noqa: E402

KINDS = json.loads((FIXTURES / "every-kind.json").read_text(encoding="utf-8"))["request"]
# the contract each VERSION names: its schema's sha256 and its id format. Changing either means a new VERSION.
CONTRACTS = {1: ("4dd5a362", "{kind}:{start}-{end}[:{placement or rule}][#{n}]")}
LIVELY = dict(level=5, vulgarity=2, embellishment=2, document_config={"profile": {
    "stack": 0.9, "garnish": {"riff": 1.0}, "max_garnish": {"riff": 30}, "garnish_gap": 0, "swearing": {"infix": 6.0}}})


def _every_kind(translator, **overrides):
    options = {**{k: v for k, v in KINDS.items() if k != "text"}, **overrides}
    return aussiefy.translate_changes(KINDS["text"], translator=translator, **options)


def _schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(C.SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema, schema


def _valid(cs):
    """A response checked against the schema, and what the schema can't say: a garnish has its removal unless it
    is named under withheld, and then offers its pick alone (a contextual image, nothing), as the output has it
    over its region."""
    jsonschema, schema = _schema()
    jsonschema.validate(cs.to_dict(), schema)
    withheld = {w["id"] for w in cs.withheld}
    for c in cs.changes:
        if c["kind"] == "garnish":
            assert ("removed" in c) == (c["id"] not in withheld), c["id"]
        if c["id"] in withheld:
            offered = [(o["entry_id"], o["rendered"], o["weight"]) for o in c["alternatives"]]
            assert not c["locked"] and offered == [(c["entry_id"], cs.text[slice(*o["out_span"])], 1.0)
                                                   for o in c["alternatives"][:bool(c["entry_id"])]], c["id"]
    return cs


def _id_pattern(format_: str) -> re.Pattern:
    """A regular expression for the ids an id format makes (its [...] parts optional), naming kind, start and end."""
    fields = {"kind": r"(?P<kind>[a-z_]+)", "start": r"(?P<start>\d+)", "end": r"(?P<end>\d+)",
              "placement or rule": r"[a-z0-9-]+", "n": r"[2-9]\d*|1\d+"}
    out = ""
    for m in re.finditer(r"\[([^\]]*)\]|[^\[]+", format_):
        part = m.group(1) if m.group(1) is not None else m.group(0)
        rx = "".join(re.escape(text) + (f"(?:{fields[name]})" if name else "")
                     for text, name, _, _ in Formatter().parse(part))
        out += f"(?:{rx})?" if m.group(1) is not None else rx
    return re.compile(out)


def test_the_python_api_takes_translates_parameters_and_an_embedder():
    def params(fn):
        return {n: p.default for n, p in inspect.signature(fn).parameters.items()}

    assert params(aussiefy.translate_changes) == {**params(aussiefy.translate), "embedder": None}
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY
               for n, p in inspect.signature(aussiefy.translate_changes).parameters.items() if n != "text")


def test_the_embedder_is_the_translations(translator):
    text = "He was exhaustedd and the toilet is broken."
    for embedder in ("none", "ngram"):
        assert (aussiefy.translate_changes(text, translator=translator, embedder=embedder).text
                == translator.translate(text, embedder=embedder).text)
    with pytest.raises(aussiefy.UserError, match="ngram or none"):
        aussiefy.translate_changes("# Hi\n\nShe was tired.", translator=translator, markdown=True, embedder="bundled")


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


def test_a_changes_renderings_share_its_region(translator):
    """Every alternative and locked option of a change goes over one region, which takes in the change's own span;
    the pick's rendering is the output there; a removal takes the garnish's words out of its region."""
    cs = _every_kind(translator)
    for c in cs.changes:
        renderings = c["alternatives"] + c["locked"]
        assert len({tuple(o["out_span"]) for o in renderings}) <= 1, c["id"]
        for o in renderings:
            a, b = o["out_span"]
            assert a <= c["out_span"][0] <= c["out_span"][1] <= b, c["id"]
            if o["entry_id"] == c["entry_id"]:
                assert cs.text[a:b] == o["rendered"], c["id"]
        if c.get("removed"):
            a, b = c["removed"]["out_span"]
            words = c["output"].strip(" ,.!?").lower()
            assert words and words not in c["removed"]["rendered"].lower(), c["id"]
            assert len(c["removed"]["rendered"]) < b - a and a <= c["out_span"][0] <= c["out_span"][1] <= b


@pytest.mark.parametrize("text, options, original, alternatives", [
    # "a" turns "an" with the alternative after it, taking the article into the span
    ("We let a toddler win the game.", {"level": 5, "vulgarity": 1}, "a toddler",
     {"nipper": "a nipper", "ankle-biter": "an ankle biter"}),
    # a riff the entry brings, a stacked second idiom, and a swear infix inside a spot
    ("You are very tired and hungry, and your car is broken.", {**LIVELY, "seed": 0}, "broken",
     {"cactus": "cactus, like a flat-pack in a cyclone"}),
    ("The toilet is broken and I am exhausted.", {**LIVELY, "seed": 2}, "exhausted",
     {"buggered": "buggered, rooted", "fucked-broken": "fucked, out on my bloody feet"}),
    # "very cold" as "cold as fuck": the intensifier rule takes the place of the entry's own word
    ("The weather was very cold and the beer was very good.", {**LIVELY, "seed": 0}, "very cold",
     {"flamin": "cold as fuck", "bloody": "cold as fuck"}),
])
def test_named_renderings(translator, text, options, original, alternatives):
    cs = aussiefy.translate_changes(text, translator=translator, **options)
    c = next(c for c in cs.changes if c["kind"] == "substitution" and c["original"] == original)
    got = {o["entry_id"]: o["rendered"] for o in c["alternatives"]}
    assert all(got.get(k) == v for k, v in alternatives.items()), got


def test_locked_options_render_at_the_readers_cap(translator):
    """A locked option renders with the reader's riffs and infix rates, as the page shows it before unlocking: at
    dad, "very" in "very cold" as fuckin' (tagged uncle-bob) reads "fuckin'", where a whole re-render at uncle-bob
    would read "cold as fuck" (an uncle-bob infix)."""
    text = "The weather was very cold and the beer was very good."
    cs = aussiefy.translate_changes(text, translator=translator, **{**LIVELY, "vulgarity": 1, "seed": 0})
    c = next(c for c in cs.changes if c["kind"] == "substitution" and c["original"] == "very")
    assert {o["entry_id"]: (o["rendered"], o["vulgarity"]) for o in c["locked"]}["fuckin-very"] == ("fuckin'", 2)


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


def _words(text):
    return re.findall(r"[a-z']{3,}", fold(restore_g(text.lower())))


def test_each_rendering_says_its_entry_or_a_rule_rewrote_it(translator, dictionary):
    """A swap's rendering holds a word of its entry's forms (inflected), unless a phonetic rule wrote over it:
    "very cold" as flamin' reads "cold as fuck". For the pick, that rule's change is one it covers."""
    rewriting = {r.id: _words(re.sub(r"\\\d|\\g<\w+>", " ", r.replace)) for r in dictionary.phonetic}
    texts = [KINDS["text"], "The weather was very cold and the beer was very good.", "He is very drunk and broke."]
    checked = rewritten = 0
    for text in texts:
        for seed in (0, 1):
            cs = aussiefy.translate_changes(text, translator=translator, **{**LIVELY, "seed": seed})
            for c in (c for c in cs.changes if c["kind"] == "substitution"):
                for o in c["alternatives"] + c["locked"]:
                    entry = dictionary.entries[o["entry_id"]]
                    stems = {w[:max(3, len(w) - 2)] for f in entry.all_forms for w in _words(PLACEHOLDER_RE.sub(" ", f))}
                    checked += 1
                    if any(w.startswith(s) for w in _words(o["rendered"]) for s in stems):
                        continue
                    rules = [r for r, ws in rewriting.items() if ws and set(ws) <= set(_words(o["rendered"]))]
                    assert rules, (o["entry_id"], o["rendered"])
                    if o["entry_id"] == c["entry_id"]:
                        assert any(i.split(":")[2] in rules for i in c["covers"]), c
                    rewritten += 1
    assert checked > 50 and rewritten >= 2


def test_a_swap_covers_the_changes_inside_it_and_a_change_with_nothing_to_swap_covers_nothing(translator):
    """A drawl or infix inside a swap's region goes with the swap. A drawl, an infix or a US word swapped has no
    region of its own to replace. Every change over the everyday corpus is held to the whole rule in
    test_changes_oracle.py."""
    cs = _every_kind(translator)
    inside = [(c, d) for c in cs.changes if c["kind"] == "substitution" for d in cs.changes
              if d["kind"] in ("phonetic", "swear_infix")
              and c["out_span"][0] <= d["out_span"][0] <= d["out_span"][1] <= c["out_span"][1]]
    assert inside and all(d["id"] in c["covers"] for c, d in inside)
    assert not [c["id"] for c in cs.changes if c["covers"] and not (c["alternatives"] or c.get("removed"))]


FAUCET = ("The faucet in the apartment is broken, so I called the color guy. He is an idiot and absolutely useless. "
          "What the hell is going on? Fantastic.")


def _overlap(x, y):
    return x[0] < y[1] and y[0] < x[1]


def test_a_garnish_region_and_a_swap_region_that_share_a_word_cover_each_other(translator):
    """A connective's region takes in "he's", the word it lowers, with the drawl on it, and so does the swap that
    starts there. Swapping or removing the connective rewrites part of the swap, and swapping in "he isn't the full
    quid" rewrites part of the connective's region, so each covers the other, and both cover the drawl. Found by
    the website, at Swaggie, Dinkum, Dad, seed 3."""
    cs = _valid(aussiefy.translate_changes(FAUCET, translator=translator, level=5, embellishment=1, vulgarity=1,
                                           seed=3))
    garnish = next(c for c in cs.changes if c.get("placement") == "connective")
    swap = next(c for c in cs.changes if c["original"] == "He is an idiot")
    drawl = next(c for c in cs.changes if c["kind"] == "phonetic" and c["output"] == "he's")
    region = garnish["removed"]["out_span"]
    assert cs.text[slice(*region)] == "Anyway, he's" and swap["output"].startswith("he's")
    assert _overlap(region, swap["out_span"]) and swap["out_span"][1] > region[1]   # part of the swap, not all
    assert any(not o["rendered"].startswith("he's") for o in swap["alternatives"])
    assert set(garnish["covers"]) == {swap["id"], drawl["id"]} and set(swap["covers"]) == {garnish["id"], drawl["id"]}


def test_a_rules_min_level_is_where_it_applies(translator, dictionary):
    """A drawl or spelling rule gives the lowest level it applies at, its min_level, so a page can say "from level
    5, swaggie". An infix has none: the vulgarity and the embellishment let it in at any level."""
    rules = {r.id: r for r in dictionary.phonetic}
    assert {r.min_level for r in rules.values() if r.is_infix} == {None}
    seen = set()
    faucet = aussiefy.translate_changes(FAUCET, translator=translator, level=5, vulgarity=1, seed=3)
    for c in (c for cs in (_every_kind(translator), faucet) for c in cs.changes
              if c["kind"] in ("phonetic", "swear_infix")):
        rule = c["rule"]
        assert rule["min_level"] == rules[rule["id"]].min_level and (c["kind"] == "swear_infix") == rules[
            rule["id"]].is_infix, c["id"]
        seen.add((rule["kind"], rule["min_level"]))
    assert {("spelling", 1), ("drawl", 4), ("drawl", 5), ("infix", None)} <= seen, seen
    low = aussiefy.translate_changes("It is a very good fight.", translator=translator, level=1, vulgarity=3,
                                     embellishment=2, seed=0, document_config={"profile": {"swearing": {"infix": 6.0}}})
    assert [c["rule"]["min_level"] for c in low.changes if c["kind"] == "swear_infix"][:1] == [None]


@pytest.mark.parametrize("region, span, reached", [
    ((2, 5), (0, 2), False), ((2, 5), (5, 8), False),     # touching either edge
    ((2, 5), (0, 3), True), ((2, 5), (4, 8), True), ((2, 5), (3, 4), True), ((2, 5), (0, 9), True),
    ((2, 5), (2, 2), False), ((2, 5), (5, 5), False), ((2, 5), (3, 3), True),   # an empty span: inside only
])
def test_a_region_reaches_a_span_it_shares_a_character_with_or_an_empty_one_inside_it(region, span, reached):
    assert C._reaches(region, span) is reached


def test_ids_are_unique_and_made_by_the_contracts_id_format(translator):
    cs = _every_kind(translator)
    ids = [c["id"] for c in cs.changes]
    assert len(ids) == len(set(ids))
    pattern = _id_pattern(CONTRACTS[C.VERSION][1])
    for c in cs.changes:
        m = pattern.fullmatch(c["id"])
        assert m and (m["kind"], int(m["start"]), int(m["end"])) == (c["kind"], *c["src_span"]), c["id"]
    assert pattern.fullmatch("garnish:40-40:connective#2") and not pattern.fullmatch("garnish:40-40#1")


def test_the_contract_version_names_its_schema_and_id_format():
    """Changing the schema or how ids are made changes the contract: bump changes.VERSION and add it here."""
    schema = hashlib.sha256(C.SCHEMA.read_bytes()).hexdigest()[:8]
    assert (schema, C.ID_FORMAT) == CONTRACTS[C.VERSION], \
        f"the changes contract changed (schema {schema}): bump changes.VERSION and record it in CONTRACTS"


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


LOCKED_CASES = [(name, {k: v for k, v in request.items() if k != "text"}, request["text"])
                for name, (_, request) in CASES.items()]
LOCKED_CASES += [(f"variety {n}", {"level": 5, "vulgarity": v, "variety": n, "seed": s}, text)
                 for n in (1, 2) for v in (0, 1) for s in (0, 1)
                 for text in ["He was very tired and very drunk, and the toilet is very broken. She is an idiot."]]


@pytest.mark.parametrize("name, options, text", LOCKED_CASES, ids=[c[0] + str(i) for i, c in enumerate(LOCKED_CASES)])
def test_locked_options_are_held_back_by_the_cap_alone(translator, dictionary, name, options, text):
    """A locked option is rated above the cap in effect (at any variety), selection takes it with only the cap
    raised to its tag, and with the cap one below that it doesn't, unless a riff or an infix is what raised the
    tag."""
    watch = C.Watch()
    result, drafts = C.collect(translator, text, _observer=watch, **options)
    run, cap = watch.run, watch.run.eff.vulgarity
    for d in drafts:
        if d.change["kind"] != "substitution":
            continue
        spot = next(s for s in watch.spots if s.rec.substituted
                    and d.change["src_span"][0] <= s.rec.span[0] < d.change["src_span"][1])
        for o in d.change["locked"]:
            entry, tag = dictionary.entries[o["entry_id"]], o["vulgarity"]
            assert entry.vulgarity > cap, (o["entry_id"], entry.vulgarity, cap)

            def eligible(v):
                eff = resolve(replace(run.pol, vulgarity=v), dictionary)
                keep, _ = translator.eligible(spot.rec.det, spot.sent, run, eff, spot.state, spot.taken)
                return o["entry_id"] in {c.entry.id for c in keep}

            assert eligible(tag), (o["entry_id"], tag)
            if tag == entry.vulgarity:
                assert not eligible(tag - 1), (o["entry_id"], tag)


def test_locked_options_follow_the_gates_in_effect(translator):
    """A gated entry is never offered behind a lock, unless the caller unlocked it (a local --unlock)."""
    d = translator.dictionary
    for text, gated in (("He's a rascal.", "cheeky-bugger"), ("I am broke this week.", "on-the-bones-of-arse")):
        plain = aussiefy.translate_changes(text, translator=translator, level=5, vulgarity=0)
        unlocked = aussiefy.translate_changes(text, translator=translator, level=5, vulgarity=0, unlock=["all"])
        assert d.entries[gated].status == "gate"
        assert gated not in {o["entry_id"] for c in plain.changes for o in c["alternatives"] + c["locked"]}
        assert gated in {o["entry_id"] for c in unlocked.changes for o in c["locked"]}
        assert unlocked.entries[gated]["gated"] == list(d.entries[gated].flags)
        _valid(unlocked)


@pytest.mark.parametrize("options", [{"embellishment": 0}, {"embellishment": 1}, {"embellishment": 2},
                                     {"embellishment": 2, "unlock": ["all"], "text": "He's a rascal and a liar."}])
def test_cards_are_lookups(translator, dictionary, options):
    """The entries a changes response sends are the cards lookup shows for the same entries under the same policy
    (aussiefy.cards): riffs only where the embellishment takes them, flags for an unlocked gated entry."""
    options = {**{k: v for k, v in KINDS.items() if k != "text"}, **options}
    text = options.pop("text", KINDS["text"])
    cs = aussiefy.translate_changes(text, translator=translator, **options)
    looked = {k: options.get(k) for k in ("level", "vulgarity", "embellishment", "document_type", "document_config")}
    matched = 0
    for entry_id, card in cs.entries.items():
        query = PLACEHOLDER_RE.sub("", dictionary.entries[entry_id].form).strip()
        found = [r for r in harness.lookup(query, limit=100, include_gated=bool(options.get("unlock")), **looked,
                                           translator=translator)["results"] if r["id"] == entry_id]
        if found:
            assert {k: v for k, v in found[0].items() if k not in ("match", "score")} == card, entry_id
            matched += 1
    assert matched >= 0.8 * len(cs.entries), (matched, len(cs.entries))
    if not options["embellishment"]:   # deadset takes no riffs, so its cards show none
        assert not any("riffs" in card for card in cs.entries.values())
    elif text == KINDS["text"]:
        assert any("riffs" in card for card in cs.entries.values())


def test_the_contract_validates_against_its_schema(translator):
    _valid(_every_kind(translator))
    _valid(aussiefy.translate_changes("", translator=translator))


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


def test_the_watch_only_watches():
    """The builder's watch steers nothing: the pick and the garnish words stay the engine's own."""
    assert C.Watch.choose is PassObserver.choose and C.Watch.placing is PassObserver.placing


def _withheld(cs, kind):
    reasons = {w["id"]: w["reason"] for w in cs.withheld}
    return {c["id"]: reasons.get(c["id"]) for c in cs.changes if c["kind"] == kind}


def test_a_pick_that_doesnt_render_true_is_offered_alone_and_named(translator, monkeypatch):
    """Where the pick's own rendering isn't the output over its region (never seen in the corpora), the swap
    offers the pick alone and the response names it under withheld."""
    real = C._Builder._render_option

    def off(self, sentence, spot, o, region, flags):
        text, infix = real(self, sentence, spot, o, region, flags)
        return (text + "?" if o.candidate is spot.rec.chosen else text), infix

    monkeypatch.setattr(C._Builder, "_render_option", off)
    subs = _withheld(_valid(_every_kind(translator)), "substitution")
    assert subs and set(subs.values()) == {C.PICK_DIFFERS}


def test_a_swap_whose_region_cant_settle_is_offered_alone_and_named(translator, monkeypatch):
    """Where a phonetic match still reads across a swap's region once it can widen no further (never seen in the
    corpora), the swap offers the pick alone and the response names it under withheld."""
    real = C._Builder._render_spot
    monkeypatch.setattr(C._Builder, "_render_spot", lambda self, *args: (real(self, *args)[0], True))
    subs = _withheld(_valid(_every_kind(translator)), "substitution")
    assert subs and set(subs.values()) == {C.REGION_UNSETTLED}


def test_a_garnish_whose_pick_doesnt_render_true_is_offered_alone_without_its_removal(translator, monkeypatch):
    """A garnish's pick is rendered over its region as its alternatives are: where it isn't the output there, the
    garnish of every placement, a contextual image and the closer included, offers its pick alone and no removal,
    and the response names it under withheld."""
    real = C._Builder._phonetic_region

    def off(self, text, bounds, flags):
        out, infix = real(self, text, bounds, flags)
        return (out + "?" if out else out), infix

    monkeypatch.setattr(C._Builder, "_phonetic_region", off)
    cs = _valid(_every_kind(translator))
    garnish = _withheld(cs, "garnish")
    assert {c["placement"] for c in cs.changes if c["id"] in garnish} >= {"opener", "connective", "tag", "aside",
                                                                         "tail", "closer", "riff"}
    assert set(garnish.values()) == {C.PICK_DIFFERS}


def test_a_garnish_region_widens_over_a_match_across_its_edge(translator):
    """A garnish's region widens a word as a swap's does: a connective's takes in "it", the word it lowers, and a
    drawl match runs on ("it is"), so its region takes in "is" too, and nothing is withheld."""
    cs = _valid(aussiefy.translate_changes(
        "We went home. It is easy to make.", translator=translator, level=4, vulgarity=1, embellishment=1, seed=0,
        document_config={"profile": {"garnish": {"opener": 1.0, "connective": 1.0}, "garnish_gap": 0}}))
    assert cs.text == "Crikey, we went home. Well, it is easy to make." and not cs.withheld
    c = next(c for c in cs.changes if c["id"] == "garnish:14-14:connective")
    assert cs.text[slice(*c["removed"]["out_span"])] == "Well, it is" and c["removed"]["rendered"] == "It is"
    assert {o["rendered"] for o in c["alternatives"]} >= {"Well, it is", "Anyway, it is"}


def test_a_garnish_whose_region_cant_settle_is_offered_alone_and_named(translator, monkeypatch):
    """Where a phonetic match still reads across a garnish's region once it can widen no further (never seen in
    the corpora), the garnish offers its pick alone and no removal, and the response names it under withheld."""
    real = C._Builder._phonetic_region

    def across(self, text, bounds, flags):
        flags.add("straddle-right")
        return real(self, text, bounds, flags)

    monkeypatch.setattr(C._Builder, "_phonetic_region", across)
    cs = _valid(_every_kind(translator))
    garnish = _withheld(cs, "garnish")
    assert {c["placement"] for c in cs.changes if c["id"] in garnish} >= {"opener", "connective", "tag", "aside",
                                                                         "tail", "closer", "riff"}
    assert set(garnish.values()) == {C.REGION_UNSETTLED}


def test_the_region_pass_counts_from_the_text_before_it(translator):
    """The phonetic pass over a spot reads only a window of the text around it, its count for each rule picking up
    from the matches before the spot: a spot after many matches of a rule still renders its pick as the output
    (and as a pinned re-render, test_changes_oracle.py)."""
    text = "You are tired. " * 12 + "You are very tired and you are broke."
    watch = C.Watch()
    result = translator.translate(text, level=5, vulgarity=1, _observer=watch)
    builder = C._Builder(translator, watch, result)
    late = [s for s in watch.spots if s.rec.substituted and s.rec.span[0] > len(text) - 40]
    assert late
    for spot in late:
        toks = spot.sent.tokens
        region = builder._base_region(builder.sentences[spot.sent.index], 0, len(toks))
        plan = builder._plan(region.bounds)
        assert max(v.count for v in plan) > 10 and all(len(v.left) <= C.CONTEXT for v in plan)
        draft = builder._substitution(spot)
        assert draft.withheld is None
        assert draft.change["output"] in [o["rendered"] for o in draft.change["alternatives"]]


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


MARKDOWN = sorted(p for p in (ROOT / "tests" / "corpus" / "everyday").rglob("*") if p.suffix in (".md", ".mdx"))


@pytest.mark.parametrize("path", MARKDOWN, ids=[p.name for p in MARKDOWN])
def test_changes_translate_each_corpus_document_as_translate_does(translator, path):
    text = path.read_text(encoding="utf-8")
    modes = [{"markup": "auto"}] + ([{"markdown": True}] if path.suffix == ".md" else [])
    for mode in modes:
        options = dict(level=5, vulgarity=2, embellishment=1, seed=1, **mode)
        assert (aussiefy.translate_changes(text, translator=translator, **options).text
                == aussiefy.translate(text, translator=translator, **options).text), mode


def test_the_escape_map_says_where_each_position_lands(translator):
    """A unit's escaping, with where each of its positions lands: in order, every one, the ends at the ends."""
    from aussiefy.markdown import _escape_map

    for text in ("1. Not a list", "  lead and *stars*  \r\nnext\nline", "a_b (c) [d] #e", ""):
        escaped, at = _escape_map(text)
        assert len(at) == len(text) + 1 and at == sorted(at) and at[-1] == len(escaped)
    escaped, at = _escape_map("go *now*")
    assert escaped == "go \\*now\\*" and escaped[at[3]:at[8]] == "\\*now\\*"


@pytest.mark.parametrize("newlines", [False, True])
def test_a_rendering_escaped_alone_reads_as_its_unit_escaped_with_it(newlines):
    """_escaped_in escapes a rendering inside its unit on its own: the same as escaping the whole unit with it in
    place, an opening "1." included, wherever the rendering sits."""
    import random

    from aussiefy.markdown import _escape_map, _escaped_in

    rng = random.Random(29)
    alphabet = "a1. \t*_#" + ("\n" if newlines else "")

    def text(n):
        return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, n)))

    for _ in range(20000):
        unit, rendered = text(10), text(4)
        a = rng.randint(0, len(unit))
        b = rng.randint(a, len(unit))
        escaped, at = _escape_map(unit[:a] + rendered + unit[b:])
        assert _escaped_in(unit, [a, b], rendered) == escaped[at[a]:at[a + len(rendered)]], (unit, a, b, rendered)
