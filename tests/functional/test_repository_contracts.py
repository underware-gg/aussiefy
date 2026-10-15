"""The shapes agents consume: what each toolkit operation returns, the yarn core (brief, dispatch_tool) and the
rules other modules lean on (terms.form_key, Result.difficult). Refactors keep these or change them on purpose."""

import re

import pytest

from aussiefy import harness
from aussiefy.terms import fold, form_key, phrase_kept, restore_g, strip_markup

ENVELOPE = {"level", "level_name", "vulgarity", "vulgarity_name", "policy_warnings"}
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


@pytest.mark.parametrize("op, subject", [("lookup", "very tired"), ("lint", "G'day."), ("guide", None),
                                         ("plan", TEXT), ("translate", TEXT)])
def test_every_toolkit_operation_takes_the_dials_by_name(translator, op, subject):
    args = (subject,) if subject else ()
    named = getattr(harness, op)(*args, level="larrikin", vulgarity="nan", translator=translator)
    numbered = getattr(harness, op)(*args, level=4, vulgarity=0, translator=translator)
    assert named == numbered and (named["level"], named["vulgarity_name"]) == (4, "nan")


def test_cli_json_translate_is_a_superset_of_the_toolkits(translator):
    args = {"level": "local", "seed": 3, "variety": 2, "regions": ["qld"]}
    toolkit = harness.translate(TEXT, translator=translator, **args)
    full = translator.translate(TEXT, **args).to_dict()
    assert ENVELOPE <= set(full) and {k: full[k] for k in toolkit} == toolkit


def test_policy_warnings_name_settings_the_dictionary_gives_nothing_to_act_on(translator):
    out = harness.plan(TEXT, regions=["qld", "atlantis"], unlock=["slur"], translator=translator)
    assert out == harness.plan(TEXT, regions=["qld", "atlantis"], unlock=["slur"], translator=translator)
    warned = " ".join(out["policy_warnings"])
    assert "'atlantis'" in warned and "'slur'" in warned and "'qld'" not in warned
    assert harness.translate(TEXT, regions=["atlantis"], translator=translator)["policy_warnings"]
    assert not harness.translate(TEXT, regions=["qld"], unlock=["all"], translator=translator)["policy_warnings"]


@pytest.mark.parametrize("bad, message", [({"registers": "current"}, "must be a list"),
                                          ({"registers": ["bogus"]}, "unknown register"),
                                          ({"unlock": ["nope"]}, "unknown unlock flag"),
                                          ({"regions": "qld"}, "must be a list")])
def test_policy_rejects_values_outside_its_closed_sets(translator, bad, message):
    from aussiefy import UserError

    with pytest.raises(UserError, match=message):
        harness.translate(TEXT, translator=translator, **bad)


def test_plan_shape(translator):
    p = harness.plan(TEXT, translator=translator)
    assert set(p) == ENVELOPE | {"draft", "seed", "planned", "garnish", "riffs", "openings", "mood",
                                 "difficult_sentences", "untouched_sentences", "note", "genre", "embellishment", "embellishment_name", "dialect", "mood", "guidance"}
    assert p["planned"] and all(set(x) == {"original", "span", "entry", "aussie", "gloss"} for x in p["planned"])
    assert all(set(g) == {"placement", "sentence", "entry", "text", "sentence_text"} for g in p["garnish"])
    assert all(set(d) == {"original", "draft", "reason"} for d in p["difficult_sentences"])
    assert p["difficult_sentences"][0]["original"].startswith("The proposition")
    assert p["mood"] in ("solemn", "dark", "light") and all(isinstance(o, str) for o in p["openings"])
    riffy = harness.plan("The ashcans were full.", translator=translator)
    assert riffy["riffs"]
    for card in riffy["riffs"]:
        assert set(card) == {"term", "for", "riffs"}
        assert all({"text", "tone", "suits_mood"} <= set(r) for r in card["riffs"])
        assert card["riffs"][0].get("best") is True


def test_lint_shape(translator):
    out = harness.lint("Y'all know the color is wrong, mate. Bloody bloody bloody bloody hell.",
                       original="You know the colour is wrong.", translator=translator)
    assert set(out) == ENVELOPE | {"ok", "issues", "warnings", "suggestions", "scope"}
    assert out["issues"] and all({"kind", "phrase"} <= set(i) for i in out["issues"])
    assert {i["kind"] for i in out["issues"]} >= {"dialect", "spelling"}
    assert all("australian" in i for i in out["issues"] if i["kind"] in ("dialect", "spelling"))
    assert out["warnings"] and all({"kind", "phrase", "why"} <= set(w) for w in out["warnings"])
    suggested = harness.lint("I'm extremely busy and my friend is tired.", translator=translator)["suggestions"]
    assert suggested and all({"text", "meaning", "options"} <= set(s) for s in suggested)


def test_lookup_shape(translator):
    out = harness.lookup("very tired", translator=translator)
    assert set(out) == ENVELOPE | {"query", "results"}
    assert all({"form", "gloss", "frame", "level", "vulgarity", "register", "concepts", "match", "score"} <= set(r)
               for r in out["results"])
    assert "note" in harness.lookup("zzqqxx", translator=translator)
    riffs = [r["riffs"] for r in harness.lookup("wheelie bin", translator=translator)["results"] if r.get("riffs")]
    assert riffs and all(rs[0].get("best") is True and not any("best" in r for r in rs[1:]) for rs in riffs)
    from aussiefy import UserError

    with pytest.raises(UserError, match="limit must be 1 or more"):
        harness.lookup("very tired", limit=-1, translator=translator)


def test_lookup_offers_what_translate_may_use_and_marks_gates(translator):
    plain = harness.lookup("all talk", translator=translator)["results"]
    gated = harness.lookup("all talk", include_gated=True, translator=translator)["results"]
    assert not any("gated" in r for r in plain)
    assert any(r.get("gated") == ["not_aussie"] for r in gated)
    assert all(r["level"] <= 2 and r["vulgarity"] == 0 for r in harness.lookup("very tired", level="blow-in",
                                                                                 translator=translator)["results"])


def test_brief_is_what_yarn_sends(translator):
    from aussiefy.yarn import brief

    s = brief("She was very tired.", level=4, seed=3, translator=translator)
    assert set(s.payload) == {"ORIGINAL", "LEVEL", "VULGARITY", "ENGINE_DRAFT", "PLANNED_PHRASES", "RIFFS",
                              "OPENINGS", "DIFFICULT_SENTENCES", "GENRE", "EMBELLISHMENT"}
    assert s.payload["LEVEL"] == 4 and s.vulgarity == s.payload["VULGARITY"]
    assert s.planned == [p["aussie"] for p in s.plan["planned"]] and "STYLE GUIDE" in s.system


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


def test_restore_g_puts_back_only_an_apostrophed_g():
    assert restore_g("spruikin' and goin' on, fightin'.") == "spruiking and going on, fighting."
    assert restore_g("a noggin, the in-laws, rock 'n' roll") == "a noggin, the in-laws, rock 'n' roll"


def test_strip_markup_is_a_form_as_plain_words():
    assert strip_markup("Chuck {poss}  wobbly") == "chuck wobbly"
    assert strip_markup("great@4 !war|wars") == "great"


@pytest.mark.parametrize("text, phrase", [
    ("Pull yer head in, ya galah.", "pull your head in"),               # a possessive respelt
    ("Ya carryin' on like a pork chop.", "carrying on like a pork chop"),  # the dropped g
    ("He chucked a wobbly.", "chuck a wobbly"),                         # inflected
    ("Give it a burl, 'ave a go.", "have a go"),                        # a word the phonetic rules respell
    ("It's abso-bloody-lutely ripper.", "absolutely ripper"),           # a swear infix
    ("How ya goin'?", "how ya going"),                                  # a dropped g on a short word
    ("What're ya doin' bein' a galah?", "what are you doing being a galah"),
])
def test_phrase_kept_tolerates_drawl_and_inflection(translator, text, phrase):
    assert phrase_kept(text, phrase, translator.dictionary.phonetic)


@pytest.mark.parametrize("text, phrase", [("Calm down.", "pull your head in"),
                                          ("She was flat out.", "flat out like a lizard drinking"),
                                          ("A ripper of a yarn.", "rip snorter")])
def test_phrase_kept_notices_a_dropped_phrase(translator, text, phrase):
    assert not phrase_kept(text, phrase, translator.dictionary.phonetic)


def test_the_engine_keeps_its_own_planned_phrases(translator):
    """Every LLM mode checks a rewrite with phrase_kept, so the engine's own draft (drawled, contracted, sworn
    at) must pass it."""
    from pathlib import Path

    texts = sorted((Path(__file__).parents[1] / "corpus" / "reference").glob("*.txt"))[:5]
    assert texts
    for path in texts:
        source = path.read_text(encoding="utf-8")
        for level, seed in ((4, 0), (5, 0), (5, 3)):
            r = translator.translate(source, level=level, seed=seed)
            decided = r.decisions()
            planned = [s["replacement"] for s in decided["substitutions"]] + [g["text"] for g in decided["garnish"]]
            assert planned, path.name
            # as the engine wrote it, and as a model drawls it: every g dropped
            for text in (r.text, re.sub(r"\b(\w+)ing\b", r"\1in'", r.text)):
                dropped = [p for p in planned if not phrase_kept(text, p, translator.dictionary.phonetic)]
                assert not dropped, (path.name, level, seed, dropped)
