"""Engine bugs the second everyday pass found (research/everyday-pass-2026-10-13/FINDINGS.md), each pinned."""

import re

import pytest

from aussiefy.translation import translate
from aussiefy.text import sentences, tokenize


def _words(text):
    return [t.text for t in tokenize(text)]


def test_a_number_with_its_punctuation_is_one_token():
    assert _words("Add 1/4 cup, 4.5 kg at 10:30. Then 4.1.2.") == [
        "Add", "1/4", "cup", ",", "4.5", "kg", "at", "10:30", ".", "Then", "4.1.2", "."]


def test_a_dialect_negative_stays_whole():
    assert _words("It warn't no war.") == ["It", "warn't", "no", "war", "."]
    assert _words("I didn't, ain't, mightn't.")[:6] == ["I", "did", "n't", ",", "ai", "n't"]


def test_a_blank_line_ends_a_sentence_unless_it_leads_in():
    def split(t):
        return [" ".join(x.text for x in s) for s in sentences(tokenize(t))]
    assert split("Minimizing the Risk\n\nGoing outside is fine.") == ["Minimizing the Risk", "Going outside is fine ."]
    assert len(split('He said to his wife,\n\n"What will become of us?"')) == 1


def _outs(translator, text, **kw):
    return [translate(text, translator=translator, level=5, seed=s, embellishment="troppo", **kw).text for s in range(10)]


def test_war_isnt_found_inside_warnt(translator):
    assert not any("stoushn't" in o for o in _outs(translator, "It warn't no war, I tell ya."))


def test_a_fraction_isnt_broken_up(translator):
    assert all("1/4 cup" in o for o in _outs(translator, "Add 1/4 cup of sugar and stir."))


def test_no_drawl_in_a_heading_or_a_links_text(translator):
    md = ("# Minimizing the Risk\n\nRead about [finding ways to stay cool](https://x.org/a) when going outside in "
          "the heat, because nothing is worse than getting sick.\n")
    for out in _outs(translator, md, markup="markdown"):
        assert "[finding ways to stay cool](https://x.org/a)" in out, out
    plain = "Minimizing the Risk\n\nGoing outside is nothing to worry about when the heat is going down.\n"
    for out in _outs(translator, plain):
        assert out.startswith("Minimizing the Risk\n"), out


@pytest.mark.parametrize("label", ["HALE", "MRS. PUTNAM"])
def test_no_opener_before_a_speaker_label(translator, label):
    play = ("Read about finding ways to stay cool when going outside in the heat, because nothing is worse than "
            f"getting sick.\n\n{label}: Good morning, Abigail.\nABIGAIL: Morning, sir.\n")
    for out in _outs(translator, play):
        assert f"\n{label}:" in out, out   # "So anyway, HALE:" before the fix


# --- the review's cases: what the fixes must not break ---------------------------------------------------

def test_a_one_line_message_isnt_a_heading(translator):
    outs = [translator.translate("I reckon we should go to the pub this arvo", level=5, seed=s,
                                 embellishment="troppo").text for s in range(6)]
    assert any(not o.startswith("I reckon") for o in outs)   # it still takes an opener


@pytest.mark.parametrize("text, kept", [
    ("I met *Candy* at the pub.", "*Candy*"),                        # emphasis isn't a position
    ("WASHINGTON, Dec. 27.—Candy Smith said so.", "Candy Smith"),    # a name after a dateline
])
def test_a_name_after_markup_or_a_dateline_is_kept(translator, text, kept):
    assert kept in translator.translate(text, level=3, english="us").text


def test_capitals_that_are_positional():
    from aussiefy.text import capital_is_positional
    def at(text, word):
        sent = sentences(tokenize(text))[-1]
        return capital_is_positional(sent, [t.text for t in sent].index(word))
    assert at("**Avoiding trouble:** Steering clear is good.", "Steering")
    assert at("MAMMOTH HOT SPRINGS, Wyo. – Effective Friday, it opens.", "Effective")
    assert not at("I met *Candy* at the pub.", "Candy")


def test_the_sentence_split_edge_cases():
    def split(t):
        return [" ".join(x.text for x in s) for s in sentences(tokenize(t))]
    assert split("Dear John,\n\nI hope you are well.") == ["Dear John ,", "I hope you are well ."]
    assert len(split("Over the\n\nhills and far away")) == 1          # a stanza's sentence going on
    assert split("Head\r\n\r\nGoing out is fine.") == ["Head", "Going out is fine ."]
    assert _words("At 10:30am on 12/25/2026.") == ["At", "10:30am", "on", "12/25/2026", "."]


def test_the_metre_rule(translator):
    out = translator.translate("If the meter changes, install a meter. Walk 5 meters, the 100-meter sprint, "
                               "twenty meters, hundreds of meters, a meter long, 3 kilometers.", level=1).text
    assert out.startswith("If the meter changes, install a meter.")
    assert all(x in out for x in ("5 metres", "100-metre", "twenty metres", "hundreds of metres", "a metre long",
                                  "3 kilometres"))


def test_kilometres_and_metres_are_one_american_spelling(translator):
    from aussiefy.dialect import text_english
    assert text_english("auto", "We ran 5 kilometers, then swam 200 meters. My pants were wet.",
                        translator.dictionary.us_spellings) is None


def _lint(text, **kw):
    from aussiefy import harness
    out = harness.lint(text, **kw)
    return {(i["kind"], i["phrase"]) for i in out["issues"]}, {(w["kind"], w["phrase"]) for w in out["warnings"]}


def test_lint_counts_a_plain_variant_as_no_use():
    _, warnings = _lint("The bus was full. The cup was full. The hall was full, and a bit full I was.")
    assert ("repeated", "a bit full") not in warnings


def test_lint_counts_the_originals_yall():
    o = 'He said: "Y\'all come back now." Then he left.'
    assert not _lint('He goes: "Y\'all come back now." Then he shot through.', original=o)[0]
    assert ("dialect", "y'all") in _lint("Y'all know it. Y'all come back.", original=o)[0]


def test_lint_leaves_a_plain_sense_alone_but_flags_a_doubtful_idiom():
    issues, _ = _lint("That is a bit rough. What a shame. He likes to chew the rag.")
    assert {p for _, p in issues} == {"chew the rag"}


@pytest.mark.parametrize("text, original", [
    ("Then Mr Gladden built a house, and old Mr Gladden was pleased.",
     "Then Mr. Gladden built a house, and old Mr. Gladden was pleased."),
    ("We had a big feed for Thanksgivin' with the family.", "We had a big dinner for Thanksgiving with the family."),
    ("**Steering clear of trouble:** Steering clear is good.", "**Avoiding trouble:** Avoiding it is good."),
])
def test_lint_names_match_as_written_either_way(text, original):
    _, warnings = _lint(text, original=original)
    assert not [w for w in warnings if w[0].startswith("name")], warnings


def test_a_sentence_end_doesnt_join_names():
    _, warnings = _lint("He went to Paris. Hilton was there.", original="He saw Paris Hilton there.")
    assert ("name_dropped", "Paris Hilton") in warnings


def test_repeated_phrase_still_catches_a_tic_and_excuses_a_dialect_swap():
    _, warnings = _lint("And he has a go at you. Then he has a go at you again. Later he has a go at you. "
                        "Then he has a go at you.", original="I go to work. We go home. They go out. You go first.")
    assert ("repeated_phrase", "he has a go at you") in warnings
    original = " ".join(f"Grease a skillet or a baking pan for batch {n}." for n in "abcd")
    said = " ".join(f"Grease a frying pan or a baking tin for batch {n}." for n in "abcd")
    assert not [w for w in _lint(said, original=original)[1] if w[0] == "repeated_phrase"]


def test_an_address_block_isnt_verse():
    from aussiefy.genre import text_genre
    block = ("Contact us\n\nHead Office\nLevel 3, 100 George Street\nSydney NSW 2000\nPhone 02 9999 9999\n"
             "Email hello at example dot com\nOpening hours Monday to Friday\nNine to five on weekdays only\n"
             "Closed on public holidays and weekends\nCall ahead before you visit us\n"
             "Parking is available out the back\nAsk at the front desk for help")
    assert text_genre(block).name != "story"


def test_apply_phonetic_keeps_out_of_kept_spans(translator):
    from aussiefy.garnish import apply_phonetic
    eff = translator.effective(level=5)
    text = "You know you want it, and you know you do."
    rules = translator.dictionary.phonetic
    drawled = [s for s in range(20) if not apply_phonetic(text, rules, eff, s)[0].startswith("You know you")]
    assert drawled   # the drawl would reach the span ("Ya know ya want it")
    for s in drawled:
        out = apply_phonetic(text, rules, eff, s, keep=lambda t: [(0, 12)])[0]
        assert out.startswith("You know you"), out


# --- wrong senses and over-colour the pass found -------------------------------------------------------

def _seeds(translator, text, n=6, **kw):
    kw = {"level": 4, "embellishment": "deadset", **kw}
    return [translator.translate(text, seed=s, **kw).text for s in range(n)]


@pytest.mark.parametrize("text, never", [
    ("Many people came, and people who help were thanked.", ["punters"]),            # not any "people"
    ("Public sector workers and the public service met.", ["punters"]),
    ("Stay in the shade so your body stays cooler. It is cooler today.", ["esky"]),  # the comparative
    ("Pack the drinks in a cooler.", ["grogs", "in esky"]),                           # beverages; the article
    ("I'm afraid I can't come. Afraid so.", ["scared", "spooked"]),                   # "I'm afraid" = I suspect
    ("She was afraid of the dark.", ["spooked of"]),
    ("You are supposed to wait here.", ["reckoned to"]),
    ("Of course, the river was busy that day.", ["too right", "bloody oath", "Nah, yeah"]),
    ("Can I park here? Yes.", ["Righto"]),                                           # righto is "okay"
    ("It was very cold.", ["properly"]),
    ("The family of American musician Bob Weir announced it.", ["American a muso"]),
    ("His heart was broken. The record was broken. The silence was broken.", ["bung", "cactus", "stuffed"]),
    ("The pain was intense.", ["full-on"]),
    ("But really it was only a dry branch.", ["flamin' it", "dead it", "bloody it"]),   # the sentence adverb
    ("We are all done for the day. I'm done for now.", ["gurgler", "gone for six", "cooked", "toast"]),
])
def test_never(translator, text, never):
    for out in _seeds(translator, text):
        assert not any(bad in out for bad in never), out


def test_terms_of_art_stay_in_technical_text(translator):
    docs = ("Run the build command. The server sets a cookie in the browser. Each struct has a field for the "
            "user ID. If you build a new release, check the cache and the API key. A bug in the parser crashes "
            "the build.")
    for out in _seeds(translator, docs, level=5):
        assert not any(w in out for w in ("bickie", "bikkie", "paddock", "knock", "brand-spankin", "bug the")), out
    story = _seeds(translator, "Grandma baked a cookie. We built a new shed in the field.", level=4,
                   embellishment="troppo")
    assert any("paddock" in o for o in story)


def test_news_keeps_its_quotes_and_everyone_keeps_a_mentioned_word(translator):
    news = ('WASHINGTON (AP) — The senator said "the faucet is broken and the money is gone," officials reported '
            "Monday. Officials said the fund was very busy.")
    for out in _seeds(translator, news, english="us"):
        assert '"the faucet is broken and the money is gone,"' in out, out
    talk = 'I hate the word "guys" for a group. Americans call it a "faucet". He called me "mate".'
    for out in _seeds(translator, talk, english="us", embellishment="troppo"):
        assert all(w in out for w in ('"guys"', '"faucet"', '"mate"')), out


def test_an_obituary_is_solemn_and_nobody_carks_it(translator):
    from aussiefy.context import text_mood
    from pathlib import Path
    obit = (Path(__file__).resolve().parents[1] / "corpus" / "everyday" / "news" / "wilbur_crafts_obituary_1922.txt").read_text()
    assert text_mood(obit) == "solemn"
    for out in _seeds(translator, obit, n=4, level=5):
        assert "cark" not in out.lower() and "the alley" not in out


def test_the_swearing_craft_goes_only_where_swearing_does(translator):
    from aussiefy import harness
    assert "Swear inside" not in harness.guide(level=4, vulgarity=0, embellishment="dinkum")["craft"]
    assert "Swear inside" in harness.guide(level=4, vulgarity=1, embellishment="dinkum")["craft"]


def test_an_exclusion_may_name_a_mark():
    from aussiefy.matcher import compile_pattern, match_at
    p = compile_pattern("of course !,", "interjection", ("X",), 3)
    assert match_at(p, tokenize("Of course, the river."), 0) is None
    assert match_at(p, tokenize("Of course."), 0) is not None


# --- the review's cases for the wrong-sense batch ------------------------------------------------------

def test_a_cooler_with_a_verb_after_it_is_still_an_esky(translator):
    text = "The cooler sits in the shade. Your cooler needs ice. My cooler broke. Grab the cooler!"
    outs = _seeds(translator, text, n=8)
    assert any("The esky sits" in o for o in outs) and any("My esky broke" in o for o in outs)
    assert not any("an esky" in o for o in outs)        # a definite cooler stays definite
    for out in _seeds(translator, "Your body stays cooler. It gets cooler at night. Cooler than yesterday."):
        assert "esky" not in out, out


def test_news_quotes_keep_their_words_and_their_grammar(translator):
    news = ('SYDNEY (AP) — Police said the case was closed on Monday. "We are going to find the guys who did '
            'this, and they are going to be very sorry," Inspector Jane Smith told reporters.')
    quote = '"We are going to find the guys who did this, and they are going to be very sorry,"'
    for out in _seeds(translator, news, level=5):
        assert quote in out, out
    single = news.replace('"', "'")
    for out in _seeds(translator, single, level=5):
        assert quote.replace('"', "'") in out, out


@pytest.mark.parametrize("text, held", [
    ('I hate the word "guys" for a group.', ["guys"]),
    ("Americans call it a 'faucet'.", ["faucet"]),
    ("a phrase like 'the faucet's broken'", ["the faucet's broken"]),
    ('She called "Help!" and ran.', []),                          # shouting, not naming
    ('Dad called, "Grab the cooler, mate!" and we ran', []),
    ("I call 'em mates' and that's that", []),                    # apostrophes aren't quotes
])
def test_mentioned_spans(text, held):
    from aussiefy.text import mentioned_spans
    assert [text[a:b] for a, b in mentioned_spans(text)] == held


def test_quoted_spans():
    from aussiefy.text import quoted_spans
    def q(t):
        return [t[a:b] for a, b in quoted_spans(t)]
    assert q("'We're gonna find them,' she said.") == ["'We're gonna find them,'"]
    assert q('a 6" pipe and "a quote" here') == ['"a quote"']   # an inch mark isn't a quote
    assert q("Don't say 'no' to them, it's rude.") == ["'no'"]
    assert q("It's 'cause they kept pursuin' it 'n that.") == []   # the drawl's own marks pair with nothing


@pytest.mark.parametrize("text, solemn", [
    ("Dad was 45 when he bought the boat. The engine died twice, and we nearly buried it in the mud. He "
     "mourned that boat for years, ha ha.", False),
    ("A man died after a fight in Parramatta. The man, who was 34, was found at 2am. The death is being "
     "investigated.", False),
    ("The score was 21 to 3, and the crowd died laughing.", False),
    ("Jane Smith died on Monday. She was 81. She is survived by her husband and two sons.", True),
])
def test_an_obituary_needs_a_death_an_age_and_rites_or_family(text, solemn):
    from aussiefy.context import text_mood
    assert (text_mood(text) == "solemn") is solemn


def test_really_still_intensifies_an_adjective(translator):
    outs = _seeds(translator, "It was really cold this morning. It was really hot, so we left.", n=8)
    assert any("really cold" not in o for o in outs) and any("really hot" not in o for o in outs)
    for out in _seeds(translator, "Do you really think so? But really it was only a branch."):
        assert "really think" in out or "really reckon" in out, out


def test_afraid_of_anything_is_the_same(translator):
    for obj in ("it", "you", "them"):
        assert any("afraid of" not in o for o in _seeds(translator, f"She was afraid of {obj}.", n=8)), obj


def test_the_public_keeps_its_verb(translator):
    for out in _seeds(translator, "The public is angry. The public was told to stay away.", n=8):
        assert "punters is" not in out and "punters was" not in out, out


def test_a_web_cookie_in_a_how_to(translator):
    howto = ("1. Open your browser settings. 2. Delete the session cookie for the site. 3. Clear your cookies "
             "and site data. 4. Accept cookies. 5. Enter your name in the field.")
    for out in _seeds(translator, howto, english="us"):
        assert not any(w in out for w in ("biscuit", "bickie", "bikkie", "paddock")), out
    assert any("bickies" in o or "biscuits" in o for o in _seeds(translator, "Grandma's cookies are the best.",
                                                                 english="us"))


def test_an_unknown_not_in_genre_is_refused():
    from aussiefy.schema import SchemaError, parse_concept
    with pytest.raises(SchemaError, match="not_in"):
        parse_concept("X", {"description": "x", "triggers": {"np": ["thing"]}, "not_in": ["blog"]})


@pytest.mark.parametrize("text, after", [
    ("the family of American musician Bob Weir", True),
    ("On Monday a musician came", False),        # the capital after a sentence start, not a modifier
    ("Mr Smith met a musician", False),
])
def test_after_proper_modifier(text, after):
    from aussiefy.realise import _after_proper_modifier
    toks = sentences(tokenize(text))[0]
    i = [t.text for t in toks].index("musician")
    assert _after_proper_modifier(toks, i) is after


# --- the last of the pass's findings ----------------------------------------------------------------------

@pytest.mark.parametrize("text, kept", [
    ("It is usually served as the bread portion of lunch or dinner (supper).", ""),   # tea (supper), or dinner (tea)
    ("He wore a sweater (pullover) to work.", "(pullover)"),
    ("Put the cookies (biscuits) in the jar.", "(biscuits)"),
    ("Take the elevator (lift) to the top.", "elevator (lift)"),       # the bracket already says it
    ("Buy candy (lollies) for the kids.", "candy (lollies)"),
])
def test_a_bracketed_gloss_doesnt_echo_its_word(translator, text, kept):
    for out in _seeds(translator, text, english="us"):
        assert kept in out and not re.search(r"\b(\w+) \(\1\)", out), out


def test_a_kept_gloss_isnt_a_lint_issue(translator):
    from aussiefy.yarn import brief, validate
    s = brief("Put the cookies (biscuits) in the jar. Then bake the cookies.", level=4, seed=2, english="us",
              embellishment="dinkum", translator=translator)
    assert not validate(s, s.plan["draft"])
    assert validate(s, s.plan["draft"] + " Eat the biscuits.")   # an unbracketed one still is


def test_lint_in_yarn_mode_doesnt_offer_a_declined_phrase_again(translator):
    from aussiefy.yarn import brief, dispatch_tool
    s = brief("The kids were very tired after the long day at the shops.", level=4, seed=0, translator=translator)
    offered = lambda: {o for x in dispatch_tool(s, "lint", {"text": s.text})[0]["suggestions"] for o in x["options"]}
    planned = next(p for p in s.planned if p in offered())
    dispatch_tool(s, "submit", {"text": s.text, "declined": [{"phrase": "not planned", "reason": "x"},
                                                             {"phrase": planned, "reason": ""}]})
    assert planned in offered()                  # unplanned or without a reason: not a decline
    dispatch_tool(s, "submit", {"text": s.text, "declined": [{"phrase": planned, "reason": "wrong sense"}]})
    assert planned not in offered()


def test_yarn_tools_lint_takes_the_declined_file(tmp_path):
    import json
    import subprocess
    import sys
    src, draft, declined = tmp_path / "o.txt", tmp_path / "d.txt", tmp_path / "x.yaml"
    src.write_text("The kids were very tired after the long day at the shops.")
    draft.write_text("The kids were very tired after the long day at the shops.")
    run = lambda *extra: json.loads(subprocess.run(
        [sys.executable, "-m", "aussiefy.cli", "yarn-tools", "lint", str(src), str(draft), "-l", "4", "-s", "0",
         *extra], capture_output=True, text=True).stdout)   # -s 0: "zonked" is planned and offered
    first = run()
    options = {o for x in first["suggestions"] for o in x["options"]}
    from aussiefy.yarn import brief
    planned = next(p for p in brief(src.read_text(), level=4, seed=0).planned if p in options)
    declined.write_text(f"- {{phrase: {planned}, reason: wrong sense}}\n")
    assert planned not in {o for x in run("--declined", str(declined))["suggestions"] for o in x["options"]}


def test_a_planned_phrase_put_somewhere_else_is_sent_back(translator):
    from aussiefy.yarn import brief, validate
    text = "When the stranger turned up at the camp he was very tired. Smiley bet on anything that turned up."
    s = brief(text, level=4, seed=1, embellishment="dinkum", translator=translator)
    moved = text + " He lobbed later."
    assert [p for p in validate(s, moved) if "somewhere else" in p and "lobbed" in p]


def test_the_engines_own_draft_is_never_a_moved_phrase(translator):
    """The phrase's own words ("new" in "brand-spankin'-new") and a quoted original ('boys') aren't the original
    still standing: the plan's own draft passes, across the corpus."""
    from pathlib import Path
    from aussiefy.yarn import brief, validate
    corpus = Path(__file__).resolve().parents[1] / "corpus" / "everyday"
    texts = sorted(p for p in corpus.glob("*/*.txt"))[:24]
    for path in texts:
        for setting in ("deadset", "dinkum"):
            s = brief(path.read_text(encoding="utf-8"), level=4, seed=0, embellishment=setting, translator=translator)
            assert not [p for p in validate(s, s.plan["draft"]) if "somewhere else" in p], (path.name, setting)


def test_the_original_word_again_in_the_writers_own_words_is_no_move(translator):
    """The third pass: "a look" for "Examine" was sent back because "examine" came up again elsewhere in the
    writer's own wording. Only the spot a phrase was planned for counts."""
    from aussiefy.yarn import brief, validate
    text = "When the stranger turned up at the camp he was very tired. Nobody knew where he came from."
    s = brief(text, level=4, seed=0, embellishment="dinkum", translator=translator)
    planned = next(p for p in s.plan["planned"] if p["original"] == "turned up")["aussie"]
    yarned = (f"When the stranger {planned} at the camp he was very tired. Nobody knew where he'd turned up "
              f"from.")
    assert not [p for p in validate(s, yarned) if "somewhere else" in p]
    stayed = f"When the stranger turned up at the camp he was very tired. Nobody knew where he {planned} from."
    assert [p for p in validate(s, stayed) if "somewhere else" in p and planned in p]
