from pathlib import Path

import pytest
import yaml
from conftest import FakeClaude, json_reply

from aussiefy import claude
from aussiefy.loader import DATA_DIR, load_dictionary
from aussiefy.schema import SchemaError
from aussiefy.scrape.fetch import reference_only
from aussiefy.scrape.normalise import Staged, merge_key, merge
from aussiefy.scrape.parse import extract_phrases
from aussiefy.scrape.review import plan_review
from aussiefy.scrape.tag import SYSTEM, proposal_to_entry, tag_all

FIX = Path(__file__).parents[1] / "fixtures"
URL_A, URL_B = "https://example.test/a", "https://example.test/b"


def parsed(name, url):
    pytest.importorskip("bs4")   # the HTML parser is optional (aussiefy[scrape]); everything after it isn't
    return extract_phrases((FIX / name).read_text(), url)


def raw_phrases():
    return parsed("listicle_a.html", URL_A) + parsed("listicle_b.html", URL_B)


def test_table_columns_found_by_header():
    rows = parsed("listicle_a.html", URL_A)
    assert [r.phrase for r in rows][:2] == ["Flat out like a lizard drinking",
                                           "Busier than a one-legged man in a bum-kicking contest"]
    pig = next(r for r in rows if r.phrase.startswith("That'll"))
    assert pig.meaning == "Test meaning three." and pig.usage == '"That\'ll do, pig."'.strip('"')
    assert rows[0].section == "Sayings about being busy"


def test_list_items_and_numbered_headings():
    rows = parsed("listicle_b.html", URL_B)
    assert {r.phrase for r in rows} == {"Flat out like a lizard drinkin'", "Ya flamin' galah",
                                       "Busier than a one-legged man in a bum-kicking contest", "Up a gum tree"}
    assert not any("Home" in r.phrase for r in rows)  # nav stripped


def test_merge_key_merges_spellings():
    assert merge_key("Flat out like a lizard drinkin'") == merge_key("flat out like a lizard drinking")
    assert merge_key("He's got kangaroos loose in the top paddock") == \
        merge_key("got kangaroos loose in the top paddock")
    assert merge_key("{subj} {have} a kangaroo loose in {poss} top paddock") == \
        merge_key("have a kangaroo loose in your top paddock")


def test_merge_across_sources_and_dictionary(dictionary):
    staged = {s.form: s for s in merge(raw_phrases(), dictionary)}
    busier = staged["Busier than a one-legged man in a bum-kicking contest"]
    assert busier.sources == [URL_A, URL_B] and busier.known_as is None
    lizard = staged["Flat out like a lizard drinking"]
    assert lizard.known_as == "flat-out-lizard" and lizard.variants == ["Flat out like a lizard drinkin'"]
    pig = staged["That'll do, pig"]
    assert pig.known_as == "thatll-do-pig" and pig.known_status == "omit"
    assert len(busier.source_meanings) == 2


def proposal(**kw):
    base = {"form": "busier than a one-legged man in a bum-kicking contest", "variants": [], "concept": ["BUSY"],
            "new_concept": None, "frame": "predicate_adj", "intensity": 5, "vulgarity": 1, "incoherence": 5,
            "register": "current", "region": [], "replaces": ["incredibly busy@5"], "flags": [],
            "gloss": "Rushed off one's feet.", "review_note": ""}
    return {**base, **kw}


def test_proposal_flags_set_status(dictionary):
    item = merge(raw_phrases(), dictionary)[1]
    raw, _ = proposal_to_entry(item, proposal(flags=["not_aussie"]), dictionary)
    assert raw["status"] == "omit"
    raw, _ = proposal_to_entry(item, proposal(flags=["fabricated"]), dictionary)
    assert raw["status"] == "gate"
    raw, notes = proposal_to_entry(item, proposal(concept=["NOPE"], new_concept={
        "id": "RUSHED", "description": "x", "trigger": "rushed"}), dictionary)
    assert raw["status"] == "gate" and "untagged" in raw["flags"] and any("RUSHED" in n for n in notes)


def test_copied_gloss_is_dropped(dictionary):
    item = merge(raw_phrases(), dictionary)[1]
    raw, notes = proposal_to_entry(item, proposal(gloss="Test meaning two."), dictionary)
    assert raw["gloss"] == "" and any("too close" in n for n in notes)


def test_tag_review_apply_round_trip(data_copy):
    data = data_copy
    d = load_dictionary(data_dir=data)
    staged = [s for s in merge(raw_phrases(), d)]
    fresh = [s for s in staged if not s.known_as]
    client = FakeClaude(*[json_reply(proposal()), *[json_reply(proposal(form=s.form, flags=["fabricated"]))
                                                    for s in fresh[1:]]])
    tagged = tag_all(staged, d, client=client, log=lambda m: None)
    assert len(client.calls) == len(fresh) and client.calls[0]["model"] == "claude-opus-5-5"
    assert client.calls[0]["output_config"]["format"]["type"] == "json_schema"

    plan = plan_review(yaml.safe_load(yaml.safe_dump(tagged)), d, data)
    diff = plan.diff()
    assert "+- id: busier-than-a-one-legged-man" in diff
    assert any(s.startswith("blocked (omitted): 'That'll do, pig' = thatll-do-pig") for s in plan.summary)
    assert any(s.startswith("already present (active): 'Flat out like a lizard drinking'") for s in plan.summary)
    assert "+flat-out-lizard:" in diff  # new source recorded in the overlay, not in idioms.yaml
    plan.apply()

    d2 = load_dictionary(data_dir=data)
    new = d2.entries["busier-than-a-one-legged-man"]
    assert new.status == "active" and new.sources == (URL_A, URL_B)
    assert d2.entries["flat-out-lizard"].sources == (URL_A, URL_B)
    assert (data / "entries" / "idioms.yaml").read_text() == (DATA_DIR / "entries" / "idioms.yaml").read_text()

    # a re-scrape + re-tag never resurrects or overrides; review is idempotent
    again = plan_review(yaml.safe_load(yaml.safe_dump(tagged)), d2, data)
    assert again.diff() == ""


def test_review_apply_validates_before_writing(data_copy):
    good = {"id": "zzfine", "form": "zzfine", "concept": ["TIRED"], "frame": "predicate_adj", "gloss": "Tired."}
    plan = plan_review([good], load_dictionary(data_dir=data_copy), data_copy)
    plan.new_scraped += "- {id: zzbroken, form: zzbroken, concept: [NOPE], frame: np}\n"   # a cross-file error
    before = (data_copy / "entries" / "scraped.yaml").read_text()
    with pytest.raises(SchemaError):
        plan.apply()
    assert (data_copy / "entries" / "scraped.yaml").read_text() == before


# --- tagging: what reaches Claude, and what a failed reply does ---------------------------------------------------

BUSIER = Staged(id="busier-than", form="busier than a one-legged man in a bum-kicking contest", sources=[URL_A],
                source_meanings=["Very busy."])
UP_A_GUM_TREE = Staged(id="up-a-gum-tree", form="up a gum tree", sources=[URL_B])


def test_tagging_sends_the_vocabulary_once_in_the_cached_system_prompt(dictionary):
    """The system prompt (with the vocabulary) is the same for every phrase, so it carries the cache marker; each
    phrase's prompt is new, so nothing after it does."""
    client = FakeClaude(json_reply(proposal()), json_reply(proposal()))
    tag_all([BUSIER, UP_A_GUM_TREE], dictionary, client=client, log=lambda m: None)
    first, second = client.calls
    [block] = first["system"]
    assert block["cache_control"] == {"type": "ephemeral"}
    assert block["text"].startswith(SYSTEM) and "\nBUSY: " in block["text"]
    assert second["system"] == first["system"]
    prompt = first["messages"][0]["content"]
    assert isinstance(prompt, str) and prompt.startswith(f"Phrase: {BUSIER.form}\n") and "BUSY" not in prompt
    assert "cache_control" not in first


def test_a_refused_or_bad_reply_gates_that_phrase_only(dictionary):
    log = []
    for failed in (json_reply({}, stop="refusal"), json_reply({"form": "x"})):   # declined; lacks required keys
        tagged = tag_all([UP_A_GUM_TREE, BUSIER], dictionary, client=FakeClaude(failed, json_reply(proposal())),
                         log=log.append)
        assert [(t["id"], t["status"]) for t in tagged] == [("up-a-gum-tree", "gate"), ("busier-than", "active")]
        assert tagged[0]["flags"] == ["untagged"] and "tagging failed" in tagged[0]["notes"]


def test_an_outage_stops_tagging(dictionary, api_error):
    """claude.Unavailable fails every later phrase too: it aborts (the CLI exits 2) rather than staging each phrase
    as untagged, which review --apply would then stage and later re-tags couldn't overwrite."""
    client = FakeClaude(json_reply(proposal()), api_error("overloaded"))
    with pytest.raises(claude.Unavailable, match="overloaded"):
        tag_all([BUSIER, UP_A_GUM_TREE, BUSIER], dictionary, client=client, log=lambda m: None)
    assert len(client.calls) == 2


def test_tagging_retry_reuses_validated_paid_work(dictionary, api_error, monkeypatch):
    first = FakeClaude(json_reply(proposal()), api_error("overloaded"))
    with pytest.raises(claude.Unavailable):
        tag_all([BUSIER, UP_A_GUM_TREE], dictionary, client=first, log=lambda m: None)
    retry = FakeClaude(json_reply(proposal()))
    tagged = tag_all([BUSIER, UP_A_GUM_TREE], dictionary, client=retry, log=lambda m: None)
    assert [t["id"] for t in tagged] == [BUSIER.id, UP_A_GUM_TREE.id]
    assert len(first.calls) == 2 and len(retry.calls) == 1
    monkeypatch.setattr(claude, "client", lambda: pytest.fail("a cache hit must work offline"))
    assert tag_all([BUSIER, UP_A_GUM_TREE], dictionary, log=lambda m: None) == tagged
    fresh = FakeClaude(json_reply(proposal()), json_reply(proposal()))
    tag_all([BUSIER, UP_A_GUM_TREE], dictionary, client=fresh, cache=False, log=lambda m: None)
    assert len(fresh.calls) == 2


def test_tagging_cache_tracks_model_and_item_context(dictionary):
    tag_all([BUSIER], dictionary, client=FakeClaude(json_reply(proposal())), log=lambda m: None)
    changed = Staged(BUSIER.id, BUSIER.form, sources=["https://new.example"])
    for items, model in (([BUSIER], "different-model"), ([changed], claude.DEFAULT_MODEL)):
        client = FakeClaude(json_reply(proposal()))
        result = tag_all(items, dictionary, client=client, model=model, log=lambda m: None)
        assert len(client.calls) == 1 and result[0]["sources"] == items[0].sources


# --- the reference-only gate ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("url", ["https://www.macquariedictionary.com.au/australian-word-map/",
                                 "https://MacquarieDictionary.com.au/x", "macquariedictionary.com.au/x",
                                 "macquariedictionary.com.au/a//b",
                                 "http://www.oed.com/view/Entry/1", "https://australiannationaldictionary.oup.com/x"])
def test_reference_only_sources_are_matched_by_host(url):
    assert reference_only(url)


@pytest.mark.parametrize("url", ["https://example.test/oed.com", "https://notoed.com/x",
                                 "https://example.test/?ref=macquariedictionary.com.au", "listicle.html"])
def test_other_sources_may_be_scraped(url):
    assert reference_only(url) is None


# --- fetching -----------------------------------------------------------------------------------------------------

def test_fetched_pages_are_cached_under_the_aussiefy_home(tmp_path, monkeypatch):
    import hashlib

    from aussiefy.scrape.fetch import fetch

    url = "https://example.test/slang"
    monkeypatch.setenv("AUSSIEFY_HOME", str(tmp_path / "home"))
    cached = tmp_path / "home" / "cache" / "scrape" / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    cached.parent.mkdir(parents=True)
    cached.write_text("<p>from the cache</p>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert fetch(url) == "<p>from the cache</p>"     # no network: a miss would need requests and a live site
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / cached.name).write_text("<p>overridden</p>", encoding="utf-8")
    assert fetch(url, cache_dir=other) == "<p>overridden</p>"
    assert not (tmp_path / ".cache").exists()
