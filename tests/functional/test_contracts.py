"""The shapes agents consume: what each toolkit operation returns, the yarn core (brief, dispatch_tool) and the
rules other modules lean on (terms.form_key, Result.difficult). Refactors keep these or change them on purpose."""

import pytest

from aussiefy import harness
from aussiefy.terms import fold, form_key

ENVELOPE = {"level", "level_name", "vulgarity", "vulgarity_name", "policy_warnings"}
DOCUMENT = {"document_type", "document_type_source", "genre", "genre_scores", "document_config", "document_overrides"}
TEXT = ('She was very tired and hungry. "Are you crazy?" he asked. The proposition was conceived with considerable '
        "deliberation and dedicated to posterity.")


def test_every_toolkit_result_carries_the_policy_envelope(translator):
    results = [harness.lookup("very tired", translator=translator), harness.lint("G'day.", translator=translator),
               harness.guide(translator=translator), harness.plan(TEXT, translator=translator),
               harness.translate(TEXT, translator=translator)]
    for r in results:
        assert ENVELOPE <= set(r), sorted(r)
    # the dials are independent: a level's default vulgarity, overridden either way, by number or name
    assert harness.guide(level="blow-in", translator=translator)["vulgarity_name"] == "nan"
    assert harness.guide(level=2, vulgarity="tradie", translator=translator)["vulgarity"] == 3
    assert harness.guide(level="swaggie", vulgarity=0, translator=translator)["vulgarity_name"] == "nan"


def test_plan_shape(translator):
    p = harness.plan(TEXT, translator=translator)
    assert set(p) == ENVELOPE | DOCUMENT | {"draft", "seed", "planned", "garnish", "dialect", "riffs", "openings", "mood", "genre",
                                 "embellishment", "embellishment_name", "guidance", "difficult_sentences",
                                 "untouched_sentences", "note"}
    assert set(p["guidance"]) == {"genre", "embellishment"}
    assert p["planned"] and all(set(x) == {"original", "span", "entry", "aussie", "gloss"} for x in p["planned"])
    assert all(set(g) == {"placement", "sentence", "entry", "text", "sentence_text"} for g in p["garnish"])
    assert all(set(d) == {"original", "draft", "reason"} for d in p["difficult_sentences"])
    assert p["difficult_sentences"][0]["original"].startswith("The proposition")
    assert p["mood"] in ("solemn", "dark", "light") and all(isinstance(o, str) for o in p["openings"])
    riffy = harness.plan("We put out the wheelie bin.", translator=translator)
    for card in riffy["riffs"]:
        assert set(card) == {"term", "for", "riffs"}
        assert all({"text", "tone", "suits_mood"} <= set(r) for r in card["riffs"])
        assert card["riffs"][0].get("best") is True


def test_lint_shape(translator):
    out = harness.lint("Y'all know the color is wrong, mate. Bloody bloody bloody bloody hell.",
                       original="You know the colour is wrong.", translator=translator)
    assert set(out) == ENVELOPE | DOCUMENT | {"ok", "issues", "warnings", "suggestions", "scope"}
    assert out["issues"] and all({"kind", "phrase"} <= set(i) for i in out["issues"])
    assert {i["kind"] for i in out["issues"]} >= {"dialect", "spelling"}
    assert all("australian" in i for i in out["issues"] if i["kind"] in ("dialect", "spelling"))
    assert out["warnings"] and all({"kind", "phrase", "why"} <= set(w) for w in out["warnings"])
    assert all({"text", "meaning", "options"} <= set(s) for s in out["suggestions"])


def test_lookup_shape(translator):
    out = harness.lookup("very tired", translator=translator)
    assert set(out) == ENVELOPE | {"query", "results"}
    assert all({"form", "gloss", "frame", "level", "vulgarity", "register", "concepts", "match", "score"} <= set(r)
               for r in out["results"])
    assert "note" in harness.lookup("zzqqxx", translator=translator)


def test_brief_is_what_yarn_sends(translator):
    from aussiefy.yarn import brief

    s = brief("She was very tired.", level=4, seed=3, embellishment="troppo", translator=translator)
    assert set(s.payload) == {"ORIGINAL", "LEVEL", "VULGARITY", "EMBELLISHMENT", "GENRE", "PLANNED_PHRASES",
                              "RIFFS", "OPENINGS", "DIFFICULT_SENTENCES", "DOCUMENT_CONFIG"}   # troppo writes first: no draft
    assert set(brief("She was very tired.", translator=translator).payload) == (   # a retelling's dinkum
        set(s.payload) | {"ENGINE_DRAFT"})
    assert s.payload["LEVEL"] == 4 and s.vulgarity == s.payload["VULGARITY"]
    assert s.planned == list(dict.fromkeys(p["aussie"] for p in s.plan["planned"])) and "STYLE GUIDE" in s.system
    assert all(set(p) == {"phrase", "replaces", "means"} for p in s.payload["PLANNED_PHRASES"])
    assert set(s.payload["GENRE"]) == {"name", "guidance"} == set(s.payload["EMBELLISHMENT"])


def test_dispatch_tool_answers_each_call(translator):
    from aussiefy.yarn import brief, dispatch_tool

    s = brief("She was very tired. She went to the shop.", translator=translator)
    assert dispatch_tool(s, "nope", {}) == ({"error": "unknown tool nope"}, False)
    out, ok = dispatch_tool(s, "submit", {"text": "x"})
    assert not ok and "missing argument declined" in out["error"]
    assert dispatch_tool(s, "lookup", {"query": "tired"})[0]["results"]
    out, ok = dispatch_tool(s, "lint", {"text": "Y'all went to the shop."})
    assert not ok and not out["ok"]
    out, ok = dispatch_tool(s, "submit", {"text": s.plan["draft"], "declined": []})
    assert ok and out == {"accepted": True, "problems": []}


def test_result_records_difficult_sentences_without_a_rewriter(translator):
    r = translator.translate(TEXT)
    assert [d.sentence for d in r.difficult] == [2]
    assert "formal word" in r.difficult[0].reason and r.difficult[0].original.startswith("The proposition")
    assert r.to_dict()["difficult_sentences"][0]["sentence"] == 2


@pytest.mark.parametrize("a, b", [
    ("chuck {poss} wobbly", "chuck your wobbly"), ("chuck {poss} wobbly", "a chuck yer wobbly"),
    ("spruiking", "spruikin'"), ("spruikin'", "spruikin"), ("top {poss}self", "top yourself"),
    ("kit 'n caboodle", "kit and caboodle"), ("great@4", "great"), ("great !war|deal", "great"),
    ("The Good Oil", "good oil"), ("off his tree", "off {poss} tree"), ("fair dinkum!", "fair dinkum"),
])
def test_form_key_same_term(a, b):
    assert form_key(a) == form_key(b)


@pytest.mark.parametrize("a, b", [("thing", "thin"), ("ripper", "rip"), ("a bit", "bitter"), ("king", "kin")])
def test_form_key_different_terms(a, b):
    assert form_key(a) != form_key(b)


def test_fold():
    assert fold("  It’s  ‘Fair’ ") == "it's 'fair'"


def test_verify_shape(translator):
    out = harness.verify("She was knackered.", original="She was very tired.", translator=translator)
    assert set(out) == ENVELOPE | DOCUMENT | {"ok", "counts", "problems", "metrics", "scope"}
    assert set(out["counts"]) == {"critical", "major", "minor"}
    assert all({"severity", "kind", "phrase", "why"} <= set(p) for p in out["problems"])
    assert set(out["metrics"]) == {"original_words", "translation_words", "sentences", "translation_sentences",
                                   "untouched_share"}
