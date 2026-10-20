import json
from types import SimpleNamespace

import pytest

from aussiefy import harness
from aussiefy.yarn import tool_definitions, yarn


def test_lookup_meaning_and_term(translator):
    busy = [r["form"] for r in harness.lookup("very busy", translator=translator)["results"]]
    assert "flat out like a lizard drinking" in busy
    goog = harness.lookup("goog", translator=translator)["results"]
    assert goog[0]["match"] == "slang term" and any(r["form"] == "goog" for r in goog)
    clean = harness.lookup("someone", vulgarity=0, translator=translator)["results"]
    assert all(r["vulgarity"] == 0 for r in clean)


def test_lint_finds_problems(translator):
    out = harness.lint("Y'all, that dog won't hunt. He honored his mom. Fuck me.", level=4, translator=translator)
    kinds = {(i["kind"], i["phrase"]) for i in out["issues"]}
    assert ("flagged", "that dog won't hunt") in kinds
    assert ("dialect", "y'all") in kinds and ("spelling", "honored") in kinds and ("spelling", "mom") in kinds
    assert ("too_vulgar", "fuck") in kinds  # level 4 caps at 1
    assert not out["ok"]
    assert harness.lint("G'day mate, she's flat out like a lizard drinking.", level=5, translator=translator)["ok"]


def test_lint_suggests_more_aussie(translator):
    out = harness.lint("I'm extremely busy and my friend is tired.", level=5, translator=translator)
    assert any("flat out like a lizard drinking" in s["options"] for s in out["suggestions"])


def test_guide_and_plan(translator):
    g = harness.guide(level=5, translator=translator)
    assert g["vulgarity"] == 2 and "c-word" in g["language"]
    assert "connectives" in harness.guide(level=5, embellishment="troppo", translator=translator)["craft"]
    p = harness.plan("Our ancestors conceived this proposition with considerable deliberation. I'm very busy.",
                     level=5, translator=translator)
    assert p["draft"] and p["planned"] and p["difficult_sentences"]
    assert "proposition" in p["difficult_sentences"][0]["reason"]


# --- yarn mode: a scripted Claude driving the tool loop ---------------------------------

def _resp(*blocks, stop="tool_use"):
    return SimpleNamespace(stop_reason=stop, content=list(blocks))


def _use(i, name, **inp):
    return SimpleNamespace(type="tool_use", id=f"t{i}", name=name, input=inp)


class Scripted:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(json.loads(json.dumps(kwargs, default=lambda o: getattr(o, "__dict__", str(o)))))
        return self.responses.pop(0)


STORY = "She was tired and very hungry. She went into the woods. The porridge was too hot."


def test_yarn_loop_lookup_check_reject_then_accept(tmp_path, translator):
    # pinned to nan: the scripted good text keeps the clean plan, so the loop is tested, not the dictionary
    from aussiefy.yarn import brief
    good = brief(STORY, level=5, vulgarity="nan", translator=translator).plan["draft"]
    client = Scripted([
        _resp(_use(1, "lookup", query="too hot")),
        _resp(_use(2, "lint", text="She was tired. Y'all know the porridge was hot.")),
        _resp(_use(3, "submit", text="Y'all, she was tired.", declined=[])),          # rejected: dialect word, short
        _resp(_use(4, "submit", text=good, declined=[])),
    ])
    r = yarn(STORY, level=5, vulgarity="nan", client=client, translator=translator, cache_dir=str(tmp_path))
    assert r.status == "yarned" and r.text == good
    assert r.tool_calls == {"lookup": 1, "lint": 1, "submit": 2}
    first = client.calls[0]
    assert first["model"] == "claude-opus-5-5" and {t["name"] for t in first["tools"]} == {
        "lookup", "lint", "submit"}
    system = first["system"][0]["text"]   # one cached block
    assert "STYLE GUIDE" in system and "Translate meanings, not words" in system
    rejection = client.calls[3]["messages"][-1]["content"][0]
    assert rejection["is_error"] and "dialect: y'all" in rejection["content"]

    again = yarn(STORY, level=5, vulgarity="nan", client=Scripted([]), translator=translator, cache_dir=str(tmp_path))
    assert again.text == good and again.status == "yarned (cached)"


def test_yarn_cache_misses_when_the_instructions_change(tmp_path, translator, monkeypatch, api_error):
    import importlib

    y = importlib.import_module("aussiefy.retelling")

    from aussiefy.yarn import brief

    good = brief(STORY, translator=translator).plan["draft"]   # the engine's own draft validates
    first = yarn(STORY, level=5, client=Scripted([_resp(_use(1, "submit", text=good, declined=[]))]),
                 translator=translator, cache_dir=str(tmp_path))
    assert first.outcome == "applied"
    assert yarn(STORY, level=5, client=Scripted([]), translator=translator, cache_dir=str(tmp_path)).status.endswith(
        "(cached)")
    monkeypatch.setattr(y, "YARN_SYSTEM", y.YARN_SYSTEM + "\nA new rule.")

    class Offline:
        beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **k: (_ for _ in ()).throw(api_error("offline"))))
    r = yarn(STORY, level=5, client=Offline(), translator=translator, cache_dir=str(tmp_path))
    assert "cached" not in r.status          # a changed guide or rule isn't answered from the old cache


@pytest.fixture
def accepted_yarn_cache(tmp_path, translator):
    from aussiefy.yarn import brief

    good = brief(STORY, vulgarity=0, translator=translator).plan["draft"]
    result = yarn(STORY, vulgarity=0, translator=translator, cache_dir=str(tmp_path),
                  client=Scripted([_resp(_use(1, "submit", text=good, declined=[]))]))
    assert result.outcome == "applied"
    return good, next(tmp_path.glob("*.json"))


@pytest.mark.parametrize("record", [
    [], {}, {"text": 123}, {"text": "text", "declined": "phrase"},
    {"text": "text", "declined": [{}]},
    {"text": "text", "declined": [{"phrase": "phrase", "reason": None}]},
    {"text": "text", "tool_calls": []}, {"text": "text", "tool_calls": {"submit": -1}},
    {"text": "text", "tool_calls": {"submit": True}},
])
def test_malformed_yarn_cache_names_the_file(record, accepted_yarn_cache, tmp_path, translator):
    from aussiefy.errors import UserError

    _, path = accepted_yarn_cache
    path.write_text(json.dumps(record))
    with pytest.raises(UserError, match=f"{path.name}: invalid yarn cache entry; delete it"):
        yarn(STORY, vulgarity=0, translator=translator, cache_dir=str(tmp_path), max_turns=0)


def test_stale_yarn_cache_gets_a_new_checked_reply(accepted_yarn_cache, tmp_path, translator):
    good, path = accepted_yarn_cache
    cached = json.loads(path.read_text())
    cached["text"] = "Y'all have a good day."
    path.write_text(json.dumps(cached))
    client = Scripted([_resp(_use(1, "submit", text=good, declined=[]))])
    result = yarn(STORY, vulgarity=0, translator=translator, cache_dir=str(tmp_path), client=client)
    assert result.text == good and result.status == "yarned" and len(client.calls) == 1
    assert json.loads(path.read_text())["text"] == good


def test_cached_declines_still_need_to_be_valid(accepted_yarn_cache, tmp_path, translator):
    _, path = accepted_yarn_cache
    cached = json.loads(path.read_text())
    cached["declined"] = [{"phrase": "not a planned phrase", "reason": "wrong sense"}]
    path.write_text(json.dumps(cached))
    result = yarn(STORY, vulgarity=0, translator=translator, cache_dir=str(tmp_path), max_turns=0)
    assert result.outcome == "fell_back" and result.text == result.draft


def test_yarn_cache_uses_current_dictionary_acceptance(tmp_path, dictionary):
    from dataclasses import replace
    from aussiefy import Translator
    from aussiefy.yarn import brief, validate

    source = "The sun is bright today and we will spend the whole afternoon sitting outside under the trees."
    good = source.replace("bright", "bloody bright")
    first = Translator(dictionary, lookup_embedder=None)
    stricter = Translator(replace(dictionary, swears={**dictionary.swears, "bloody": 3}), lookup_embedder=None)
    settings = dict(level=1, vulgarity=1, embellishment=0)
    old = brief(source, translator=first, **settings)
    new = brief(source, translator=stricter, **settings)
    assert (old.plan, old.payload, old.system) == (new.plan, new.payload, new.system)
    assert validate(old, good) == [] and "too_vulgar: bloody" in validate(new, good)
    assert yarn(source, translator=first, cache_dir=str(tmp_path), **settings,
                client=Scripted([_resp(_use(1, "submit", text=good, declined=[]))])).outcome == "applied"
    result = yarn(source, translator=stricter, cache_dir=str(tmp_path), max_turns=0, **settings)
    assert result.outcome == "fell_back" and result.text == result.draft and result.text != good


def test_yarn_falls_back_to_draft(tmp_path, translator, api_error):
    class Broken:
        beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **k: (_ for _ in ()).throw(api_error("no key"))))
    r = yarn(STORY, level=5, client=Broken(), translator=translator, cache_dir=str(tmp_path))
    assert r.text == r.draft and r.status.startswith("kept draft")
    stuck = Scripted([_resp(_use(i, "submit", text="nope", declined=[])) for i in range(3)])
    r = yarn(STORY, level=5, client=stuck, translator=translator, cache_dir=str(tmp_path), max_turns=3)
    assert r.text == r.draft and "no accepted yarn" in r.status


def test_tool_definitions_are_strict():
    for t in tool_definitions():
        assert t["strict"] and t["input_schema"]["additionalProperties"] is False


def test_lookup_partial_terms_and_no_match_note(translator):
    assert any(r["form"] == "been kippin' in" for r in harness.lookup("kip", translator=translator)["results"])
    assert any("witch's tit" in r["form"] for r in harness.lookup("witch's tit", translator=translator)["results"])
    none = harness.lookup("xylophone", translator=translator)
    assert not none["results"] and "No entry" in none["note"]


def test_lint_style_warnings(translator):
    out = harness.lint('She was buggered, rooted and hungry. On the table were three bowls, mate. "Yum!" she said.',
                        level=5, translator=translator)
    kinds = {w["kind"] for w in out["warnings"]}
    assert {"pile_up", "tag_in_narration"} <= kinds and out["ok"]   # warnings don't fail lint
    assert "Not checked" in out["scope"]
    # a monologue talks to the listener: the odd tag is fine, one on every line isn't
    one = harness.lint("Moloch! Gone for six, mate! The pollies are stunned mullets. Not a skerrick left!",
                        translator=translator)
    assert not {"tag_in_narration", "tag_overuse"} & {w["kind"] for w in one["warnings"]}
    many = harness.lint(" ".join(f"Line {i} is gone, mate!" for i in range(6)), translator=translator)
    assert "tag_overuse" in {w["kind"] for w in many["warnings"]}


def test_lint_does_not_suggest_what_is_already_aussie(translator):
    text = ("She's knackered, smack-bang in the middle of the bush. They've smashed it to buggery. "
            "She's scared stiff. \"Help!\" she screams. \"Mine!\" cries Baby Bear.")
    out = harness.lint(text, level=5, translator=translator)
    flagged = {s["text"].lower() for s in out["suggestions"]}
    for phrase in ("knackered", "in the middle of", "smashed it", "scared", "screams", "cries"):
        assert phrase not in flagged, (phrase, out["suggestions"])
    assert all("{" not in o for s in out["suggestions"] for o in s["options"])


def test_plan_lists_untouched_sentences(translator):
    p = harness.plan("She knocked on the door, but nobody answered. I'm very busy.", level=5, vulgarity="nan",
                     translator=translator)   # at nan, "nobody" has no swap (only no bugger, no bastard)
    assert "She knocked on the door, but nobody answered." in p["untouched_sentences"]
    assert "candidates, not obligations" in p["note"]


def test_lint_swear_overuse(translator):
    text = " ".join(["It was a bloody hot day and the bloody dog barked at the bloody postie."] * 3)
    kinds = {w["kind"]: w for w in harness.lint(text, translator=translator)["warnings"]}
    assert kinds["swear_overuse"]["phrase"] == "bloody" and kinds["swear_overuse"]["times"] == 9
    assert "swear_density" in kinds
    calm = "It was a bloody hot day and the dog barked at the postie all arvo long, as dogs do."
    assert not {"swear_overuse", "swear_density"} & {w["kind"] for w in harness.lint(calm, translator=translator)["warnings"]}


def test_lint_fidelity_against_original(translator):
    original = "In 1863 Lincoln spoke at Gettysburg about the war."
    kept = "Back in 1863 Lincoln had a yarn at Gettysburg about the stoush."
    assert harness.fidelity(kept, original, translator=translator) == []
    drifted = ("Lincoln had a yarn about the stoush, and then old Bazza from Wagga shouted the whole mob a beer "
               "and they all got stuck into it till sparrow's fart, and it went on and on and on for hours, "
               "with more beers and more yarns and more beers than you could poke a stick at.")
    found = [(w["kind"], w["phrase"]) for w in harness.fidelity(drifted, original, translator=translator)]
    assert ("number_dropped", "1863") in found and ("name_dropped", "Gettysburg") in found
    assert ("name_added", "Bazza") in found and ("name_added", "Wagga") in found
    assert any(kind == "too_long" for kind, _ in found)
    assert "fidelity" in harness.lint(kept, original=original, translator=translator)["scope"]


def test_lint_exempts_the_sources_own_language(translator):
    text = "Cocksucker in Moloch! Ya'll never get yer mitts on it."
    plain = harness.lint(text, translator=translator)
    assert ("too_vulgar", "cocksucker") in {(i["kind"], i.get("phrase")) for i in plain["issues"]}
    assert any(i["kind"] == "dialect" and i["phrase"] == "ya'll" for i in plain["issues"])
    kept = harness.lint(text, original="Cocksucker in Moloch! You'll never get it.", translator=translator)
    assert not any(i.get("phrase") == "cocksucker" for i in kept["issues"])


def test_lookup_single_words_avoid_lookalikes(translator):
    cry = [r["form"] for r in harness.lookup("cry", translator=translator)["results"]]
    assert "bawl" in cry and "have a sook" in cry
    lonely = [r["form"] for r in harness.lookup("lonely", translator=translator)["results"]]
    assert "beaut" not in lonely and "as lonely as a shag on a rock" in lonely
    alone = [r["form"] for r in harness.lookup("alone", translator=translator)["results"]]
    assert "on {poss} Pat Malone" in alone


def test_riffs_in_lookup_and_plan(translator):
    card = harness.lookup("wheelie bin", translator=translator)["results"][0]
    assert card["form"] == "wheelie bin" and any("bin chickens" in r["text"] for r in card["riffs"])
    assert {r["tone"] for r in card["riffs"]} <= {"comic", "grim", "plain"}
    # riffs are rated for swearing, so the cap applies to them
    clean = harness.lookup("the pollies", vulgarity=0, translator=translator)["results"]
    assert all("piss" not in r["text"] for c in clean for r in c.get("riffs", []))
    p = harness.plan("The wheeled rubbish bins were full.", translator=translator)
    bins = next(r for r in p["riffs"] if r["term"] == "wheelie bin")
    assert p["mood"] == "light"
    assert all(r["suits_mood"] == (r["tone"] != "grim") for r in bins["riffs"])


def test_harvested_insult_riffs_keep_a_clean_option_and_respect_the_swear_cap(translator):
    def riffs(cap):
        card = harness.lookup("drongo", vulgarity=cap, translator=translator)["results"][0]
        return {r["text"] for r in card["riffs"]}

    clean = "with the brains of a fence post"
    assert riffs(0) == riffs(1) == {clean}
    assert {clean, "with the brains of a fucking fence post", "with the brains of a fucking wheelie bin"} <= riffs(2)


def test_harvested_trade_riffs_are_offered_only_when_the_document_allows_them(translator):
    config = {"garnish": ["riff"], "profile": {"garnish": {"riff": 1}, "max_garnish": {"riff": 1}, "stack": 0}}
    text = "He is furious."
    allowed = harness.plan(text, vulgarity=0, document_type="custom", document_config=config, translator=translator)
    assert any("brickie" in riff["text"] for card in allowed["riffs"] for riff in card["riffs"])
    result = translator.translate(text, vulgarity=0, document_type="custom", document_config=config)
    assert any(record.riff for record in result.records)
    blocked = harness.plan(text, vulgarity=0, document_type="custom", translator=translator)
    assert blocked["riffs"] == []
    assert not any(record.riff for record in translator.translate(text, vulgarity=0, document_type="custom").records)


def test_lookup_normalises_spelling(translator):
    for query, form in [("yeah but nah", "yeah, but nah"), ("dob in", "dob {obj} in"), ("the clink", "clink"),
                        ("flamin", "flamin'"), ("top yourself", "top {poss}self"), ("gawd", "Gawd help us.")]:
        forms = [r["form"] for r in harness.lookup(query, translator=translator)["results"]]
        assert form in forms, (query, forms)


def test_lookup_finds_phrases_by_their_parts(translator):
    for query, form in [("kit and caboodle", "the whole kit 'n caboodle"), ("chuck in", "chuck it in"),
                        ("give the flick", "give {obj} the flick"), ("off his tree", "off {poss} tree"),
                        ("crying", "bawl"), ("laughing", "crack up")]:
        forms = [r["form"] for r in harness.lookup(query, translator=translator)["results"]]
        assert form in forms, (query, forms)


def test_suggestions_skip_size_great_and_words_already_used(translator):
    out = harness.lint("Whoppin' great bombs fell on the blokes. A man ran.", translator=translator)
    texts = {s["text"].lower(): s["options"] for s in out["suggestions"]}
    assert "great" not in texts
    assert "bloke" not in texts.get("man", [])


def test_lint_warns_on_stock_closer_not_story_punchline():
    kinds = lambda t: [w["kind"] for w in harness.lint(t, level=5)["warnings"]]
    assert "stock_closer" in kinds("The wolf ate the lot of 'em. Gawd help us.")
    assert "stock_closer" not in kinds("The wolf got boiled for tea. Serves the mongrel right.")


def test_lint_ignores_general_english_gated_entries():
    issues = harness.lint("Petrol's dear and the young fella knows it.", level=5)["issues"]
    assert not [i for i in issues if i["kind"] == "flagged"]


def test_openings_vary_by_text_and_lint_flags_the_default():
    texts = ["Once upon a time there were three bears.", "It is a truth universally acknowledged.",
             "When in the Course of human events.", "A Shepherd-boy, who tended his flock."]
    picks = [tuple(harness.openings(t)) for t in texts]
    assert all(len(p) == 3 for p in picks) and len(set(picks)) == len(picks)
    assert harness.plan(texts[0], level=5)["openings"] == list(picks[0])
    kinds = lambda t: [w["kind"] for w in harness.lint(t, level=5)["warnings"]]
    assert "stock_opener" in kinds("Righto, so there's this bloke. He went home.")
    assert "stock_opener" not in kinds("So get this. There's this bloke. He went home.")


def test_validate_counts_declined_phrases_with_reasons(translator):
    from aussiefy.loader import load_genres
    from aussiefy.yarn import YarnSession, validate
    planned = ["battlers", "the pollies", "a fair shake", "the joint"]
    s = YarnSession(text="x", level=5, seed=0, vulgarity=2, translator=translator, plan={"planned": []}, planned=planned,
                    system="", payload={}, embellishment=load_genres().embellishments[1])
    text = "One mob of people cuts the ties. Every bloke deserves a fair shake from the pollies."
    assert any("kept only 50%" in p for p in validate(s, text))
    declined = [{"phrase": "battlers", "reason": "means people doing it tough, not a nation"},
                {"phrase": "The joint", "reason": "a place, not the act of setting something up"}]
    assert not [p for p in validate(s, text, declined) if "planned" in p]   # matched as the same term
    assert any("needs a reason" in p for p in validate(s, text, [{"phrase": "battlers", "reason": ""}]))
    assert any("aren't planned" in p for p in validate(s, text, [{"phrase": "ripper", "reason": "no"}]))
    # every phrase declined with a reason: nothing left to keep, so no share to meet
    assert not [p for p in validate(s, "Nothing kept.", [{"phrase": p, "reason": "wrong sense"} for p in planned])
                if "kept only" in p]
    # a plan too short for a share (one wrong sense would block it) asks for none
    short = YarnSession(text="x", level=5, seed=0, vulgarity=2, translator=translator, plan={"planned": []},
                        planned=planned[:3], system="", payload={}, embellishment=load_genres().embellishments[1])
    assert not [p for p in validate(short, "Nothing kept.") if "kept only" in p]
    # declining most of a long plan doesn't let the rest be dropped quietly
    assert any("kept only 0%" in p for p in validate(s, "Nothing kept.", declined[:1]))


def test_yarn_returns_malformed_tool_calls_to_the_model(tmp_path, translator):
    from aussiefy.yarn import brief
    good = brief(STORY, level=5, vulgarity="nan", translator=translator).plan["draft"]
    client = Scripted([_resp(_use(1, "lookup")), _resp(_use(2, "submit", text=good, declined=[]))])
    r = yarn(STORY, level=5, vulgarity="nan", client=client, translator=translator, cache_dir=str(tmp_path))
    assert r.status == "yarned"
    error = client.calls[1]["messages"][-1]["content"][0]
    assert error["is_error"] and "missing argument" in error["content"]


def test_yarn_lets_harness_bugs_raise(tmp_path, translator, monkeypatch):
    from aussiefy import harness as h
    monkeypatch.setattr(h, "lint", lambda *a, **k: {}["boom"])
    client = Scripted([_resp(_use(1, "lint", text="G'day."))])
    with pytest.raises(KeyError):
        yarn(STORY, level=5, client=client, translator=translator, cache_dir=str(tmp_path))


def test_lint_knows_the_dictionarys_tags_and_narration_jibes(translator):
    text = 'She walked to the shop, like a drongo. He sat down, cobber. "Hello," she said.'
    flagged = [w["phrase"] for w in harness.lint(text, translator=translator)["warnings"]
               if w["kind"] == "tag_in_narration"]
    assert flagged == ["He sat down, cobber."]   # "like a drongo" is narration's own jibe (when: action_end)


# --- lint false positives and misses from the everyday pass ------------------------------------------------------

def test_lint_reads_a_dropped_g_and_spares_the_originals_own_words(translator):
    kinds = lambda t, **kw: {(i["kind"], i["phrase"]) for i in harness.lint(t, translator=translator, **kw)["issues"]}
    assert ("too_vulgar", "pissin'") in kinds("He was pissin' about all day.", vulgarity=1)
    quoted = 'She said "fuck off" and left.'
    assert not [k for k in kinds(quoted, vulgarity=0, original=quoted) if k[0] == "too_vulgar"]


def test_lint_warns_of_a_phrase_said_over_and_over(translator):
    t = "He has a go at you every time. Then he has a go at you again. Mate, he has a go at you and has a go at you."
    warned = {w["phrase"] for w in harness.lint(t, original="He criticises you.", translator=translator)["warnings"]
              if w["kind"] == "repeated_phrase"}
    assert "has a go at you" in warned
    bears = "Someone has been eating my porridge. Someone has been sitting in my chair. Someone has been in my bed."
    assert not [w for w in harness.lint(bears, original=bears, translator=translator)["warnings"]
                if w["kind"] == "repeated_phrase"]   # the original's own pattern


def test_names_survive_headings_dates_and_line_breaks(translator):
    original = "Food Safety Tips\nThe meeting is on Oct. 11 at Boston\nUniversity. The Water Board approved it."
    draft = "Food Safety Tips\nThe meetin's on 11 October at Boston University. The Water Board gave it the nod."
    assert not [w for w in harness.lint(draft, original=original, translator=translator)["warnings"]
                if w["kind"].startswith("name_")]


def test_template_macros_are_kept_in_markdown(translator):
    text = "Hello {{ user.name }}, your {% if paid %}receipt{% endif %} is ready. The kids loved it."
    out = __import__("aussiefy").translate(text, translator=translator, level=5, seed=1, markup="markdown").text
    assert "{{ user.name }}" in out and "{% if paid %}receipt{% endif %}" in out


def test_lookup_short_keeps_what_a_writer_needs(translator):
    out = harness.lookup("very tired", short=True, translator=translator)
    assert out["results"] and all({"id", "form", "gloss", "frame", "level", "vulgarity"} <= set(r) <= {
        "id", "form", "gloss", "frame", "level", "vulgarity", "register", "gated"} for r in out["results"])


def test_yarn_tools_reports_a_bad_declined_file(tmp_path, capsys):
    from aussiefy.cli import main
    (tmp_path / "o.txt").write_text("She was tired.")
    (tmp_path / "d.txt").write_text("She was knackered.")
    (tmp_path / "bad.yaml").write_text("- phrase: battlers\n  reason: wrong: means poor\n")
    assert main(["yarn-tools", "submit", str(tmp_path / "o.txt"), str(tmp_path / "d.txt"),
                 "--declined", str(tmp_path / "bad.yaml")]) == 2
    assert "not valid YAML" in capsys.readouterr().err


def test_the_originals_swears_cover_only_as_many_as_it_has(translator):
    original = "He told them to fuck off. It was cold."
    draft = "He told them to fuck off. Fuck off, it was cold. Fuck off and fuck off again."
    issues = harness.lint(draft, original=original, vulgarity=0, translator=translator)["issues"]
    assert [i for i in issues if i["kind"] == "too_vulgar"]


def test_names_still_count_in_wrapped_prose_verse_and_sign_offs(translator):
    original = "Dear Ann,\nI visited my old friend\nMargaret Thompson at her farm near Ballarat, and\nwe talked.\nLove from Mary Smith"
    draft = "Dear Ann,\nI visited me old mate\nat her farm, and\nwe yakked.\nLove from Smith"
    dropped = {w["phrase"] for w in harness.lint(draft, original=original, translator=translator)["warnings"]
               if w["kind"] == "name_dropped"}
    assert {"Ballarat", "Mary Smith"} <= dropped
    added = {w["phrase"] for w in harness.lint("He sat in the sun all day, on Saturday too.",
                                               original="He sat in the sun all day.", translator=translator)["warnings"]
             if w["kind"] == "name_added"}
    assert added == {"Saturday"}   # "sat" isn't "Sat."


def test_a_refrain_is_the_originals_even_respelt_or_swapped(translator):
    original = "\n".join(["It was the man from Ironbark who came."] * 4)
    draft = "\n".join(["It was the bloke from Ironbark who come."] * 4)
    assert not [w for w in harness.lint(draft, original=original, translator=translator)["warnings"]
                if w["kind"] == "repeated_phrase"]
    assert not [w for w in harness.lint(draft, translator=translator)["warnings"] if w["kind"] == "repeated_phrase"]


def test_an_entry_used_three_times_is_one_repeat_however_its_forms_overlap(translator):
    reps = [w for w in harness.lint("It's a bit full. It's a bit full. It's a bit full.", translator=translator)["warnings"]
            if w["kind"] == "repeated"]
    assert [(w["phrase"], w["times"]) for w in reps] == [("a bit full", 3)]


def test_separate_uses_of_an_inner_form_still_count_as_repetition(translator):
    text = "It's a bit full. He was full. She was full. They were full."
    reps = [w for w in harness.lint(text, translator=translator)["warnings"]
            if w["kind"] == "repeated"]
    assert [(w["phrase"], w["times"]) for w in reps] == [("full", 3)]


def test_an_unclosed_template_brace_doesnt_swallow_the_text(translator):
    text = "In Python, write {{ to get a brace. The kids were very tired.\n\nClose it with }} at the end."
    out = __import__("aussiefy").translate(text, translator=translator, level=4, seed=1, markup="markdown").text
    assert "kids were very tired" not in out


@pytest.mark.parametrize("apostrophe", ["'", "’"])
def test_lint_custom_gated_forms_use_canonical_apostrophe_matching(translator, apostrophe):
    from dataclasses import replace
    from aussiefy import Translator
    from aussiefy.schema import Entry

    entry = Entry(id="private-test", concept=("TIRED",), frame="np", form="somebody’s special slang", status="gate", flags=("fabricated",))
    tr = Translator(replace(translator.dictionary, entries={**translator.dictionary.entries, entry.id: entry}))
    text = "somebody" + apostrophe + "s special slang"
    result = harness.lint(text, translator=tr, suggest=False)
    assert any(i["kind"] == "flagged" and i["phrase"] == entry.form for i in result["issues"])


def test_lookup_honours_selected_dictionary_default_unlock(translator):
    from dataclasses import replace
    from aussiefy import Translator

    tr = Translator(replace(translator.dictionary, policy_defaults={**translator.dictionary.policy_defaults, "unlock": ["all"]}))
    results = harness.lookup("take a pull at {poss}self", translator=tr, level=5, vulgarity=3)["results"]
    assert any(r["form"] == "take a pull at {poss}self" for r in results)
def test_lint_suggests_in_the_originals_genre(translator):
    # a voiced retelling of a policy can read as a story, but its gift is still no pressie
    original = "Employees must not accept a gift from a vendor. Any gift over $150 must be reported to Legal."
    draft = "Once upon a time, a vendor gave me a gift for my birthday and I laughed."
    options = [o for s in harness.lint(draft, original=original, level=5, translator=translator, document_type="auto")["suggestions"]
               for o in s["options"]]
    assert not {"pressie", "prezzie"} & set(options)
    alone = [o for s in harness.lint(draft, level=5, translator=translator, document_type="auto")["suggestions"] for o in s["options"]]
    assert {"pressie", "prezzie"} & set(alone)
