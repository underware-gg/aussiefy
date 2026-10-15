import json

from conftest import FakeClaude, json_reply, reply, text_block

from aussiefy.llm import surface_rewrite


def says(text, stop="end_turn"):
    """Claude replying {"text": text} once."""
    return FakeClaude(json_reply({"text": text}, stop=stop))


TEXT = "You're overreacting and I'm extremely busy."


def planned_result(translator):
    for seed in range(20):
        r = translator.translate(TEXT, level=4, seed=seed)
        if len([x for x in r.records if x.substituted]) == 2:
            return r
    raise AssertionError("no seed substituted both spans")


def test_surface_applied_when_plan_kept(translator):
    r = planned_result(translator)
    draft = r.text
    client = says(draft.replace(" and ", ", and "))
    surface_rewrite(r, client=client)
    assert r.surface["status"] == "applied" and r.text != draft and r.deterministic_text == draft
    sent = json.loads(client.kwargs["messages"][0]["content"])
    assert sent["DRAFT"] == draft and sent["PLANNED"] == r.surface["planned"]
    assert client.kwargs["fallbacks"] == "default"


def test_surface_rejected_when_plan_dropped(translator):
    r = planned_result(translator)
    draft = r.text
    surface_rewrite(r, client=says("You are overreacting and I am very busy."))
    assert r.text == draft and "dropped planned" in r.surface["status"]


def test_surface_failures_keep_deterministic(translator, api_error):
    for client in (FakeClaude(api_error("offline")), says("x", stop="refusal")):
        r = planned_result(translator)
        draft = r.text
        surface_rewrite(r, client=client)
        assert r.text == draft and r.surface["status"].startswith("kept deterministic")
        assert r.surface["outcome"] == "fell_back"


def test_surface_with_nothing_to_polish_is_skipped_not_a_fallback(translator):
    r = translator.translate("The.", level=1)
    surface_rewrite(r, client=FakeClaude())
    assert r.surface["outcome"] == "skipped"


def test_a_bug_at_the_call_still_raises(translator, api_error):
    """Only the SDK's failures keep the draft: a TypeError of ours (a wrong keyword, say) surfaces."""
    import pytest

    r = planned_result(translator)
    with pytest.raises(TypeError):
        surface_rewrite(r, client=FakeClaude(TypeError("create() got an unexpected keyword argument 'betas'")))


# --- whole-sentence rewriter -------------------------------------------------------

from aussiefy.llm import ClaudeRewriter  # noqa: E402

HARD = "The Hare, believing her assertion to be simply impossible, assented to the proposal. It was appointed comfortably."
PLAIN = "She was tired and very hungry, and she found a small house."


def test_rewriter_only_gets_difficult_sentences(translator):
    sent = []

    class Spy:
        model = "spy"

        def rewrite(self, original, draft, planned, **kw):
            sent.append((original, draft, planned, kw))
            return None, "spy"

    translator.translate(PLAIN, level=5, seed=0, rewriter=Spy())
    assert sent == []
    r = translator.translate("Our ancestors conceived this proposition with considerable deliberation.",
                             level=5, seed=0, rewriter=Spy())
    assert len(sent) == 1 and sent[0][3]["level"] == 5 and "proposition" in r.rewrites[0].reason
    translator.translate(PLAIN, level=5, seed=0, rewriter=Spy(), rewrite_mode="all")
    assert len(sent) == 2
    translator.translate("Our ancestors conceived this proposition with considerable deliberation.",
                         level=2, seed=0, rewriter=Spy())
    assert len(sent) == 2, "below the profile's min_level nothing is rewritten"


def test_claude_rewriter_applies_validates_and_caches(tmp_path, translator):
    text = "Our ancestors conceived this proposition with considerable deliberation."
    client = says("Our old fellas dreamt up this idea after a fair bit of chewin' it over.")
    rw = ClaudeRewriter(client=client, cache_dir=str(tmp_path))
    r = translator.translate(text, level=5, seed=0, rewriter=rw)
    assert "dreamt up this idea" in r.text and r.rewrites[0].status == "rewritten"
    payload = json.loads(client.kwargs["messages"][0]["content"])
    assert payload["ORIGINAL"] == text and "Level 5/5" in payload["VOICE"]
    assert client.kwargs["model"] == "claude-opus-5-5"

    # second run is served from the cache: no API call, same output
    offline = ClaudeRewriter(client=FakeClaude(), cache_dir=str(tmp_path))
    again = translator.translate(text, level=5, seed=0, rewriter=offline)
    assert again.text == r.text and again.rewrites[0].status == "rewritten (cached)"


def test_claude_rewriter_rejects_bad_rewrites(tmp_path, translator, api_error):
    text = "The Hare, believing her assertion to be simply impossible, assented to the proposal with considerable deliberation."
    for client in (says("The Hare said no."),                       # drops the planned phrases
                   says("line one\nline two"),
                   FakeClaude(api_error("no key"))):
        r = translator.translate(text, level=5, seed=1, rewriter=ClaudeRewriter(client=client, cache_dir=str(tmp_path)))
        assert r.rewrites and r.rewrites[0].output is None and r.rewrites[0].status.startswith("kept draft")
        assert "Buckley's" in r.text or "no bloody way" in r.text


def test_sentence_rewriter_rejects_two_sentences_on_one_line():
    rw = ClaudeRewriter(client=says("This is one. This is two."), cache=False)
    text, status = rw.rewrite("This is one sentence.", "This is one sentence.", [], level=4, vulgarity=0)
    assert text is None and "not a single sentence" in status


def test_sentence_rewriter_accepts_an_honorific():
    rw = ClaudeRewriter(client=says("Dr. Brown reckons it is fine."), cache=False)
    text, status = rw.rewrite("Dr. Brown thinks it is fine.", "Dr. Brown thinks it is fine.", [], level=4, vulgarity=0)
    assert text == "Dr. Brown reckons it is fine." and status == "rewritten"


def test_old_cached_rewrites_use_the_current_acceptance_rule(tmp_path):
    original = "This is one sentence."
    rw = ClaudeRewriter(client=says("This is a sentence."), cache_dir=tmp_path)
    assert rw.rewrite(original, original, [], level=4, vulgarity=0)[0] == "This is a sentence."
    [path] = list(tmp_path.glob("*.json"))
    cached = json.loads(path.read_text())
    cached["text"] = "This is one. This is two."
    path.write_text(json.dumps(cached))
    client = says("This is a fresh sentence.")
    retry = ClaudeRewriter(client=client, cache_dir=tmp_path)
    assert retry.rewrite(original, original, [], level=4, vulgarity=0) == ("This is a fresh sentence.", "rewritten")
    assert len(client.calls) == 1
    assert json.loads(path.read_text())["text"] == "This is a fresh sentence."


def test_claude_requests_share_one_shape(tmp_path):
    import pytest

    from aussiefy import claude

    c = says("G'day.")
    assert claude.call_json(c, model="m", system="s", prompt="p", schema={"type": "object"}) == {"text": "G'day."}
    assert c.kwargs["betas"] == claude.BETAS and c.kwargs["output_config"]["format"]["type"] == "json_schema"
    assert "tools" not in c.kwargs
    with pytest.raises(claude.Refused):
        claude.call_json(says(None, stop="refusal"), model="m", system="s", prompt="p", schema={})
    cache = claude.Cache(tmp_path / "c")
    key = claude.Cache.key("m", 0, {"b": 1, "a": 2})
    assert key == claude.Cache.key("m", 0, {"a": 2, "b": 1}) and cache.get(key) is None
    cache.put(key, {"text": "x"})
    assert cache.get(key) == {"text": "x"} and claude.Cache(None).get(key) is None


def test_claude_reply_errors():
    import pytest

    from aussiefy import claude

    assert claude.json_reply(reply(text_block('{"text": "x"}')), ("text",)) == {"text": "x"}
    for bad, why in ((reply(text_block('{"te'), stop="max_tokens"), "truncated"), (reply(), "no text"),
                     (reply(text_block("nope")), "isn't JSON"), (reply(text_block("{}")), "lacks text")):
        with pytest.raises(claude.BadReply, match=why):
            claude.json_reply(bad, ("text",))
    with pytest.raises(claude.Refused):
        claude.json_reply(reply(stop="refusal"))


def test_api_failures_become_unavailable(api_error):
    import pytest

    from aussiefy import claude

    with pytest.raises(claude.Unavailable, match="offline"):
        claude.create(FakeClaude(api_error("offline")), model="m", system="s", messages=[{"role": "user", "content": "p"}],
                      max_tokens=10)


def test_prompt_cache_marks_the_stable_prefix():
    from aussiefy import claude

    c = says("x")
    claude.create(c, model="m", system="sys", messages=[{"role": "user", "content": "brief"}], max_tokens=10, cache=True)
    assert c.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert c.kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}


def test_corrupt_cache_entry_names_the_file(tmp_path):
    import pytest

    from aussiefy import claude

    cache = claude.Cache(tmp_path)
    cache.put("k", {"text": "x"})
    assert cache.get("k") == {"text": "x"} and not list(tmp_path.glob("*.tmp"))
    (tmp_path / "k.json").write_text('{"te')
    from aussiefy.errors import UserError

    with pytest.raises(UserError, match="k.json: corrupt cache entry"):   # the user can delete it: exit 2
        cache.get("k")


def test_claude_rewriter_caches_under_the_aussiefy_home(tmp_path, monkeypatch, translator):
    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path))
    assert ClaudeRewriter(translator=translator).cache.directory == tmp_path / "cache" / "rewrite"
    assert ClaudeRewriter(translator=translator, cache=False).cache.directory is None
