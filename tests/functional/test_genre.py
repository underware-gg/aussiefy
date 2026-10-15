"""Genre: what kind of text this is, and what it lets the engine and yarn mode do beyond the words."""

from pathlib import Path

import pytest
import yaml

from aussiefy import harness
from aussiefy.yarn import brief as yarn_brief
from aussiefy.errors import UserError
from aussiefy.genre import GARNISH, GENRES, Genre, text_genre
from aussiefy.markup import mask
from aussiefy.loader import load_genres
from aussiefy.policy import Policy

CORPUS = Path(__file__).resolve().parents[1] / "corpus"
# the corpus manifests' own genre labels, by what each needs from the engine
LABELS = {"story": {"dialogue", "fable", "humour essay", "play"}, "personal": {"forum", "letter", "speech", "onboarding"},
          "news": {"community-news", "news", "notice", "obituary", "press-release", "sport", "weather"},
          "instructions": {"appliance", "diy", "faq", "food safety", "gardening", "park visitor guidance",
                           "product instructions", "public health", "recipe", "safety", "travel", "help-page"},
          "technical": {"readme", "release-notes", "tech-docs", "concept", "how-to", "landing", "overview",
                        "quickstart", "reference", "troubleshooting", "tutorial"},
          "official": {"encyclopedic", "job-ad", "marketing", "minutes", "policy", "terms-of-service", "legal"}}
TOLD = {"story", "personal"}   # the genres whose own embellishment takes a talker's garnish (dinkum, troppo)


def _labelled():
    out = []
    for manifest in (CORPUS / "everyday").glob("*.yaml"):
        if "remote" in manifest.name or "provenance" in manifest.name:
            continue
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        for item in data["items"] if isinstance(data, dict) else data:
            if item.get("file", True) is None:
                continue
            name = item.get("file") or item["name"] + ".mdx"
            path = CORPUS / "everyday" / (name if "/" in name else f"{manifest.stem}/{name}")
            label = item.get("genre") or item.get("kind")
            genre = next(g for g, labels in LABELS.items() if label in labels)
            out.append((path, genre))
    return out + [(p, "story") for p in (CORPUS / "classics").glob("*.txt") if "glossary" not in p.name] + [
        (p, "story") for p in (CORPUS / "reference").glob("*.txt")
        if p.stem not in ("declaration_of_independence", "gettysburg")] + [
        (CORPUS / "reference" / "declaration_of_independence.txt", "official")]


def test_the_corpus_reads_as_its_genre():
    """Whether a text takes a talker's garnish is what matters most: at least 90% right on that line. Read as
    the engine reads it, the prose with the markup masked. The cues were tuned on this corpus, so this is
    training accuracy: a floor against regressions, not a measure of how well it generalises."""
    pairs = _labelled()
    masks = [mask(p.read_text(encoding="utf-8"), "auto") for p, _ in pairs]
    got = [text_genre(m.prose(), m.source).name for m in masks]
    told = sum((name in TOLD) == (g in TOLD) for name, (_, g) in zip(got, pairs))
    exact = sum(name == g for name, (_, g) in zip(got, pairs))
    assert told / len(pairs) >= 0.95 and exact / len(pairs) >= 0.85, (told, exact, len(pairs))


@pytest.mark.parametrize("path, genre", [
    ("everyday/news/wilbur_crafts_obituary_1922.txt", "news"),           # "WASHINGTON, Dec. 27.—": a dateline
    ("everyday/conversational/fable_of_the_martyr.txt", "story"),        # Ade's Capitalised Nouns aren't names
    ("reference/the_raven.txt", "story"),                                # first person, but verse: a yarn
    ("classics/sentimental_bloke_intro.txt", "story"),
    ("everyday/workplace/tts_welcome_letter.md", "personal"),            # a letter speaking to "you" and "we"
    ("everyday/conversational/you_know_me_al_letter.txt", "personal"),
])
def test_the_second_pass_misreads(path, genre):
    m = mask((CORPUS / path).read_text(encoding="utf-8"), "auto")
    assert text_genre(m.prose(), m.source).name == genre


def test_the_declaration_is_not_told_as_a_yarn():
    """A founding document reads as news or official (news, as it happens): either way, no talker's garnish."""
    text = (CORPUS / "reference" / "declaration_of_independence.txt").read_text(encoding="utf-8")
    assert text_genre(text).name not in TOLD


@pytest.mark.parametrize("text, genre", [
    ("Once upon a time there were three bears.", "story"),          # a short text needs real evidence
    ("Go away, I'm busy.", "story"),
    ("Good grief, are you crazy? Nobody cares. Everyone said it was nonsense. " * 3, "story"),  # "said" repeated
    ("Place cold food in a cooler. Keep the lid closed. Wash your hands. Pack drinks separately.", "instructions"),
])
def test_short_and_clear_cases(text, genre):
    assert text_genre(text).name == genre


def test_every_genre_has_a_policy_and_neutral_people_are_flagged(translator):
    assert set(load_genres().policies) == set(GENRES) | {"general", "custom"}
    settings = load_genres().embellishments
    assert all(e.garnish <= set(GARNISH) for e in settings.values())
    assert {"SOMEONE", "CHILD", "DEAD_PEOPLE"} <= translator.dictionary.neutral_person_concepts
    assert settings[2].garnish == set(GARNISH) and not settings[0].garnish   # troppo all of it, deadset none
    assert settings[0].garnish < settings[1].garnish < settings[2].garnish
    assert Genre("story", {}, load_genres()).setting().name == "troppo"
    assert Genre("instructions", {}, load_genres()).setting().name == "deadset"
    assert Genre("instructions", {}, load_genres()).setting(2).name == "troppo"
    assert not load_genres().policies["technical"].person_swears


SAFETY = ("If someone is struck by lightning, call 911. Stay indoors. Avoid water and metal. Unplug electrical "
          "equipment before the storm arrives. Wait 30 minutes after the last thunder before going outside.")


def test_a_safety_notice_takes_no_garnish_and_no_one_is_a_mongrel(translator):
    for seed in range(8):
        r = translator.translate(SAFETY, level=5, seed=seed, vulgarity="tradie", document_type="auto")
        assert r.genre.name == "instructions"
        assert not [g for g in r.garnish if g.text], seed
        assert not any(w in r.text for w in ("mongrel", "bastard", "bugger", "cunt")), r.text


def test_a_story_keeps_its_garnish(translator):
    story = (CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8")
    r = translator.translate(story, level=5, seed=1, document_type="auto")
    assert r.genre.name == "story" and [g for g in r.garnish if g.text]


def test_yarn_mode_reads_the_genre(translator):
    from aussiefy.yarn import brief

    s = brief(SAFETY, level=4, translator=translator, document_type="auto", embellishment="dinkum")
    assert s.payload["GENRE"]["name"] == "instructions" and "step" in s.payload["GENRE"]["guidance"]
    assert s.payload["OPENINGS"] == []
    told = brief((CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8"), translator=translator, document_type="auto", embellishment="dinkum")
    assert told.payload["OPENINGS"]
    assert s.payload["EMBELLISHMENT"]["name"] == "dinkum" and "ENGINE_DRAFT" in s.payload   # a retelling's
    assert told.payload["EMBELLISHMENT"]["name"] == "dinkum"
    performed = brief((CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8"), embellishment="troppo",
                      translator=translator)
    assert "ENGINE_DRAFT" not in performed.payload and performed.payload["OPENINGS"]
    assert "perform it" not in harness.guide(level=5, embellishment="dinkum", translator=translator)["craft"]
    assert "perform it" in harness.guide(level=2, embellishment="troppo", translator=translator)["craft"]


def test_the_caller_sets_the_embellishment(translator):
    """A safety notice told troppo takes the garnish (the caller asked for it), but still names nobody a mongrel:
    that's the genre's form, not the setting's liberty."""
    told = [translator.translate(SAFETY, level=5, seed=s, vulgarity="tradie", embellishment="troppo", document_type="auto")
            for s in range(8)]
    assert all(r.embellishment.name == "troppo" for r in told) and any(g.text for r in told for g in r.garnish)
    assert not any(w in r.text for r in told for w in ("mongrel", "bastard", "cunt"))
    story = (CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8")
    straight = translator.translate(story, level=5, seed=1, embellishment="deadset", document_type="auto")
    assert not [g for g in straight.garnish if g.text]


@pytest.mark.parametrize("value", ["troppo", "TROPPO", 2, "2"])
def test_embellishment_names_and_numbers(value):
    assert Policy(embellishment=value).embellishment == 2


def test_an_unknown_embellishment_is_refused():
    with pytest.raises(UserError, match="deadset"):
        Policy(embellishment="laid-back")


def test_dinkum_takes_a_voice_but_no_asides_or_closers():
    assert load_genres().embellishments[1].garnish == {"connective", "opener", "tag", "tail", "riff", "infix", "insult"}


def test_a_bad_embellishments_section_is_refused():
    import yaml
    from aussiefy.loader import DATA_DIR
    from aussiefy.genre import GenreConfig
    from aussiefy.schema import SchemaError

    good = yaml.safe_load((DATA_DIR / "genres.yaml").read_text())
    good["embellishments"]["dinkum"]["garnish"] = ["closr"]
    with pytest.raises(SchemaError, match="closr"):
        GenreConfig.from_mapping(good)


def test_the_length_limit_follows_the_embellishment(translator):
    original = SAFETY
    padded = original + " " + " ".join(["Keep well clear of the water and stay inside."] * 5)
    kinds = lambda **kw: {w["kind"] for w in harness.lint(padded, original=original, translator=translator,
                                                            **kw, document_type="auto")["warnings"]}
    assert "too_long" in kinds()                                # instructions: deadset, 1.3x
    assert "too_long" not in kinds(embellishment="troppo")      # the caller's setting wins
    problems = lambda **kw: {p["kind"] for p in harness.verify(padded, original=original, translator=translator,
                                                                **kw, document_type="auto")["problems"]}
    assert "too_long" in problems() and "too_long" not in problems(embellishment="troppo")


def test_troppo_takes_the_planned_phrases_as_vocabulary(translator):
    from aussiefy.yarn import YarnSession, validate

    planned = ["battlers", "the pollies", "a fair shake", "the joint"]
    s = YarnSession(text="x", level=5, seed=0, vulgarity=2, translator=translator, plan={"planned": []}, planned=planned,
                    system="", payload={}, embellishment=load_genres().embellishments[2])
    assert not any("kept only" in p for p in validate(s, "Every bloke deserves a go."))


def test_the_yarn_cache_key_covers_the_setting(translator, tmp_path):
    from aussiefy.yarn import yarn

    seen = []   # max_turns=0: the run looks the key up, then keeps the draft without calling the API
    import aussiefy.claude as claude
    real = claude.Cache.key
    try:
        claude.Cache.key = staticmethod(lambda *parts: seen.append(real(*parts)) or seen[-1])
        for e in ("deadset", "troppo"):
            yarn("She was very tired.", embellishment=e, cache_dir=str(tmp_path),
                 translator=translator, max_turns=0)
    finally:
        claude.Cache.key = real
    assert len(seen) == 2 and seen[0] != seen[1]


def test_general_defaults_to_dinkum_and_auto_uses_the_detected_type(translator):
    g = harness.guide(level=5, translator=translator)
    assert g["embellishment_name"] == "dinkum" and "perform it" not in g["craft"]
    assert "perform it" in harness.guide(level=5, embellishment="troppo", translator=translator)["craft"]
    assert harness.guide(level=5, embellishment="deadset", translator=translator)["embellishment_name"] == "deadset"
    notice = (CORPUS / "everyday" / "instructions" / "fda_picnic_food_safety.txt").read_text(encoding="utf-8")
    assert harness.translate(notice, level=4, translator=translator, document_type="auto")["embellishment_name"] == "deadset"
    assert harness.plan(notice, level=4, translator=translator, document_type="auto")["embellishment_name"] == "deadset"
    assert yarn_brief(notice, level=4, translator=translator, document_type="auto").embellishment.name == "deadset"
    assert harness.plan(notice, level=4, embellishment="deadset", translator=translator, document_type="auto")["embellishment_name"] == "deadset"


def test_results_report_the_embellishment(translator):
    d = translator.translate(SAFETY, level=4, embellishment="dinkum", document_type="auto").to_dict()
    assert d["embellishment"] == 1 and d["embellishment_name"] == "dinkum"
    assert harness.translate(SAFETY, translator=translator, document_type="auto")["embellishment_name"] == "deadset"


def test_a_form_narrows_dinkum_and_its_openings_at_every_setting(translator):
    """The third pass: the engine's dinkum garnish called a safety notice's reader a galah and opened recipe
    steps with "Anyway,". Below troppo a genre's form decides the garnish; troppo performs whatever the text, but
    at every setting the form decides the openings."""
    bears = (CORPUS / "everyday" / "instructions" / "nps_bear_safety.txt").read_text(encoding="utf-8")
    for seed in range(3):
        r = translator.translate(bears, level=5, seed=seed, embellishment="dinkum", document_type="auto")
        assert r.genre.name == "instructions" and r.embellishment.name == "dinkum"
        assert not [g for g in r.garnish if g.text and g.placement in ("opener", "connective", "tag")]
    assert not translator.translate(bears, level=5, embellishment="dinkum", document_type="auto").embellishment.openings
    assert harness.plan(bears, level=5, translator=translator, document_type="auto")["openings"] == []
    # a storyteller's openings follow the form at every setting (the fourth pass: troppo opened an obituary with
    # "Fair dinkum, this happened."), and so do swear infixes below troppo
    assert harness.plan(bears, level=5, embellishment="troppo", translator=translator, document_type="auto")["openings"] == []
    assert not translator.translate(bears, level=5, embellishment="dinkum", document_type="auto").embellishment.takes("infix")
    story = (CORPUS / "reference" / "goldilocks.txt").read_text(encoding="utf-8")
    assert harness.plan(story, level=5, embellishment="troppo", translator=translator, document_type="auto")["openings"]
    assert translator.translate(bears, level=5, embellishment="troppo", document_type="auto").embellishment.takes("opener")
    assert translator.translate(story, level=5, embellishment="dinkum", document_type="auto").embellishment.takes("opener")


def test_no_name_calling_where_the_form_rules_it_out():
    from aussiefy.engine import resolve
    from aussiefy.garnish import pick_garnish
    from aussiefy.loader import load_dictionary

    d = load_dictionary()
    eff = resolve(Policy(level=5, vulgarity=3), d)
    for seed in range(40):
        entry, _, _ = pick_garnish("tag", d.garnish, eff, seed, ("k", seed), {}, {"second_person"}, insults=False)
        assert entry is None or not entry.insult
    picked = {pick_garnish("tag", d.garnish, eff, s, ("k", s), {}, {"second_person"})[0].id for s in range(40)}
    assert picked & {"g-ya-galah", "g-ya-drongo", "g-ya-mug", "g-ya-old-bastard"}


def test_a_dateline_takes_no_opener_even_at_troppo(translator):
    text = (CORPUS / "everyday" / "news" / "ford_square_dance_1925.txt").read_text(encoding="utf-8")
    for seed in range(4):
        r = translator.translate(text, level=5, seed=seed, embellishment="troppo", document_type="auto")
        assert r.text.lstrip().startswith("DETROIT")


def test_a_held_quote_takes_no_garnish(translator):
    text = "\n\n".join(['The minister spoke on Tuesday about the figures. "Productivity growth is strong. We are '
                        'very pleased with it. Wages are rising," the statement said.'] * 4)
    seen = []
    for seed in range(8):
        r = translator.translate(text, level=5, seed=seed, embellishment="troppo", document_type="auto")
        assert r.genre.name == "news"
        assert r.text.count('"Productivity growth is strong. We are very pleased with it. Wages are rising,"') == 4
        seen += [g for g in r.garnish if g.text]
    assert seen   # troppo still garnishes the reporter's own sentences


def test_a_command_is_lowered_after_an_opener(translator):
    text = (CORPUS / "everyday" / "instructions" / "wikibooks_southern_cornbread.txt").read_text(encoding="utf-8")
    import re

    for seed in range(4):
        out = translator.translate(text, level=4, seed=seed, embellishment="troppo", document_type="auto").text
        assert not re.search(r"\b(?:Well|Now|Anyway), (?:Pour|Bake|Beat|Stir|Preheat)\b", out)


@pytest.mark.parametrize("path,value", [
    (("embellishments", "deadset", "openings"), "false"),
    (("embellishments", "deadset", "max_length"), "nan"),
    (("embellishments", "deadset", "max_length"), float("nan")),
    (("embellishments", "deadset", "keep_share"), True),
    (("embellishments", "deadset", "guidance"), 7),
    (("embellishments", "deadset", "garnish"), None),
    (("embellishments", "deadset"), []),
    (("embellishments",), []),
    (("genres", "news", "keep_quotes"), "false"),
    (("genres", "news", "guidance"), None),
    (("genres", "news", "embellishment"), []),
])
def test_genre_configuration_rejects_wrong_types(path, value):
    from aussiefy.genre import GenreConfig
    from aussiefy.schema import SchemaError

    data = yaml.safe_load((Path("aussiefy/data/genres.yaml")).read_text())
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(SchemaError, match="genres.yaml"):
        GenreConfig.from_mapping(data)


@pytest.mark.parametrize("content", ["null", "[broken", "embellishments: []"])
def test_genre_file_errors_are_collected_with_dictionary_errors(tmp_path, content):
    from aussiefy.loader import load_dictionary
    from aussiefy.schema import SchemaError

    (tmp_path / "genres.yaml").write_text(content)
    with pytest.raises(SchemaError, match="dictionary failed validation") as exc:
        load_dictionary(data_dir=tmp_path)
    assert "genres.yaml" in str(exc.value) and "profiles.yaml" in str(exc.value)
