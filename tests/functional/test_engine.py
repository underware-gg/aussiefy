import re

import pytest

from aussiefy import Policy, UserError
from aussiefy.detect import Detection
from aussiefy.morph import inflect
from aussiefy.realise import realise
from aussiefy.text import tokenize

RANT = ("Good grief, are you crazy? You're overreacting, you're stupid and all talk, "
        "and I'm extremely busy cleaning up after you.")
CORPUS = [
    RANT,
    "Thanks for breakfast, my friend. I'm exhausted and the toilet is broken.",
    "Hello everyone! Grab your sunglasses, swimsuit and flip-flops, it's a very hot day.",
    "No problem, it will be fine. Calm down and stop complaining.",
    "He was ugly and very drunk, and he lost his temper at the barbecue.",
]


def substituted_spans(result):
    return {r.span for r in result.records if r.substituted}


def test_deterministic(translator):
    for level in range(1, 6):
        a = translator.translate(RANT, level=level, seed=42)
        b = translator.translate(RANT, level=level, seed=42)
        assert a.text == b.text and a.to_dict() == b.to_dict()


def test_seed_changes_output(translator):
    outs = {translator.translate(RANT, level=5, seed=s).text for s in range(6)}
    assert len(outs) > 3


def test_higher_levels_substitute_a_superset(translator):
    for text in CORPUS:
        for seed in range(5):
            prev = set()
            for level in range(1, 6):
                spans = substituted_spans(translator.translate(text, level=level, seed=seed, embedder="none"))
                core = {s for s in prev}
                # a span substituted at level n is still substituted (possibly by a wider clause idiom) at n+1
                assert all(any(a <= s[0] and s[1] <= b or s[0] <= a and b <= s[1] for a, b in spans)
                           for s in core), (text, seed, level)
                prev = spans


@pytest.mark.parametrize("level", range(1, 6))
def test_substitution_rolls_and_unrelated_choices_stay_local(translator, level):
    tail = "My friends had breakfast. I'm extremely busy. Are you crazy?"
    substituted = 0
    for seed in range(10):
        results = [translator.translate(prefix + tail, level=level, seed=seed, vulgarity=0)
                   for prefix in ("She was very tired. ", "The quarterly report is attached. ")]
        records = [[r for r in result.records if r.sentence > 0] for result in results]
        assert records[0]
        substituted += sum(r.substituted for r in records[0])
        def decisions(rows):
            return [(r.text, r.roll, r.p, r.chosen.entry.id if r.chosen else None, r.term) for r in rows]
        assert decisions(records[0]) == decisions(records[1])
    assert substituted


def test_repetition_changes_a_choice_without_changing_its_roll(translator):
    before = translator.translate("She was very tired. He was very tired.", level=3, seed=1, vulgarity=0)
    after = translator.translate("She felt fine. He was very tired.", level=3, seed=1, vulgarity=0)
    a, b = ([r for r in result.records if r.sentence == 1 and r.substituted] for result in (before, after))
    assert len(a) == len(b) == 1
    assert a[0].roll == b[0].roll and a[0].p == b[0].p
    assert a[0].chosen.entry.id != b[0].chosen.entry.id
    assert a[0].output != b[0].output


def test_repeated_names_can_prevent_level_nesting(translator):
    text = "My friend lives in the city. His friend lives in the city."
    # This catalogue's seed 10 exhibits the non-nesting caused by the first repeated city choice.
    results = [translator.translate(text, level=level, seed=10, embedder="none") for level in (4, 5)]
    cities = [[r for r in result.records if r.text == "the city"] for result in results]
    assert len(cities[0]) == len(cities[1]) == 2
    assert not cities[0][0].substituted and cities[0][1].substituted
    assert cities[1][0].substituted and not cities[1][1].substituted


def test_level_one_only_touches_single_words(translator):
    for text in CORPUS:
        for seed in range(10):
            r = translator.translate(text, level=1, seed=seed)
            for rec in r.records:
                if rec.substituted:
                    assert rec.chosen.entry.substitution_class == "lexical"
            assert not r.garnish and not r.phonetic


def test_vulgarity_caps(translator):
    for text in CORPUS:
        for seed in range(15):
            for level in range(1, 6):
                r = translator.translate(text, level=level, seed=seed)
                cap = translator.dictionary.profiles[level].vulgarity
                used = [rec.chosen.entry for rec in r.records if rec.substituted]
                used += [translator.dictionary.entries[g.entry_id] for g in r.garnish if g.entry_id]
                assert all(e.vulgarity <= cap for e in used)
            clean = translator.translate(text, level=5, seed=seed, vulgarity=0)
            assert all(rec.chosen.entry.vulgarity == 0 for rec in clean.records if rec.substituted)


def test_level_and_vulgarity_are_independent_dials(translator):
    assert translator.translate(RANT, level=3, vulgarity="tradie").vulgarity == 3   # above the level's own
    assert translator.translate(RANT, level="swaggie", vulgarity="nan").vulgarity == 0
    assert translator.translate(RANT, level=4).vulgarity == translator.dictionary.profiles[4].vulgarity
    by_name = translator.translate(RANT, level="larrikin", vulgarity="dad", seed=3).text
    assert by_name == translator.translate(RANT, level=4, vulgarity=1, seed=3).text


def test_gated_entries_need_unlock(translator):
    def chosen(**kw):
        ids = set()
        for seed in range(40):
            r = translator.translate("You're all talk.", level=5, seed=seed, **kw)
            ids |= {rec.chosen.entry.id for rec in r.records if rec.substituted}
            ids |= {rec.stacked.entry.id for rec in r.records if rec.stacked}
        return ids
    assert "all-hat-and-no-cattle" not in chosen()
    assert "all-hat-and-no-cattle" in chosen(unlock=("not_aussie",))


def test_omitted_entries_never_fire(translator):
    for seed in range(30):
        r = translator.translate("Absolutely. That'll do.", level=5, seed=seed, unlock=("all",))
        assert "pig" not in r.text.lower()


def test_explain_reports_rejections(translator):
    r = translator.translate("I'm extremely busy.", level=2, seed=0)
    rec = next(x for x in r.records if "BUSY" in x.det.concepts)
    reasons = dict(rec.rejected)
    assert reasons["flat-out-lizard"] == "needs level 3"
    assert reasons["flat-chat"] == "frame predicate_adj not enabled at level 2"
    data = r.to_dict()["explain"][0]
    assert {"span", "concepts", "frame", "detected_by", "chosen", "candidates", "rejected"} <= set(data)


def test_level_requirement_reason(translator):
    r = translator.translate("Are you crazy?", level=3, seed=0)
    rec = r.records[0]
    assert dict(rec.rejected)["roos-top-paddock"] == "needs level 4"


def test_region_filter(translator):
    out = {translator.translate("Pack your swimsuit.", level=3, seed=s, regions=("qld",)).text for s in range(20)}
    assert any("togs" in o for o in out)
    assert not any("cozzie" in o or "bathers" in o for o in out)


def test_articles_follow_replacement(translator):
    texts = {translator.translate("I'd love a biscuit and an avocado.", level=2, seed=s).text for s in range(20)}
    assert "I'd love a bikkie and an avo." in texts


def test_plural_nouns(translator):
    texts = {translator.translate("The mosquitoes ate my friends.", level=2, seed=s).text for s in range(30)}
    assert "The mozzies ate my mates." in texts


def test_vp_inflection(translator):
    texts = {translator.translate("You're overreacting.", level=5, seed=s).text for s in range(10)}
    assert any("carryin" in t and "on like a pork chop" in t for t in texts)
    texts = {translator.translate("He lost his temper.", level=4, vulgarity="nan", seed=s).text for s in range(30)}
    assert any("He spat the dummy." == t for t in texts)
    assert any("He did his block." == t for t in texts)


def test_person_idioms_need_a_person(translator):
    for seed in range(20):
        r = translator.translate("The plan is crazy.", level=4, seed=seed)
        assert "paddock" not in r.text and "snake" not in r.text


def test_level_five_garnish_and_phonetics(translator):
    r = translator.translate(RANT, level=5, seed=3, embellishment="troppo")
    assert r.garnish and r.phonetic
    closer = [g for g in r.garnish if g.placement == "closer"]
    assert closer and closer[0].text
    said = closer[0].text[:1].upper() + closer[0].text[1:]   # the closer is its own last sentence
    assert r.text.rstrip().endswith(f" {said}."), r.text


def test_policy_is_a_value_object(translator):
    p = translator.policy(level=4, registers=["current", "dated"], unlock=["archaic"])
    assert p.registers == ("current", "dated") and p.unlock == ("archaic",) and hash(p)
    with pytest.raises(UserError, match="vulgarity must be 0 \\(nan\\)"):
        Policy(vulgarity=4)


@pytest.mark.parametrize("value, level", [(1, 1), ("1", 1), ("tourist", 1), ("Blow-in", 2), ("blow in", 2),
                                          ("BLOW_IN", 2), ("local", 3), ("larrikin", 4), ("swaggie", 5)])
def test_levels_by_number_or_name(value, level):
    from aussiefy.policy import parse_level

    assert parse_level(value) == level


@pytest.mark.parametrize("value, vulgarity", [(0, 0), ("nan", 0), ("dad", 1), ("uncle-bob", 2), ("Uncle Bob", 2),
                                              ("uncle_bob", 2), ("tradie", 3), ("3", 3)])
def test_vulgarity_by_number_or_name(value, vulgarity):
    from aussiefy.policy import parse_vulgarity

    assert parse_vulgarity(value) == vulgarity


@pytest.mark.parametrize("bad", ["drongo", 0, 6, True, "", None])
def test_bad_level_names_say_what_would_do(bad):
    from aussiefy.policy import parse_level

    with pytest.raises(UserError, match="swaggie"):
        parse_level(bad)


def test_empty_and_punctuation_only_input(translator):
    assert translator.translate("", level=5).text == ""
    assert translator.translate("  ...  ", level=5).text.strip() == "..."


def test_untouched_text_is_preserved(translator):
    text = "The quarterly report (v2) is attached; see section 4.1."
    for seed in range(10):
        out = translator.translate(text, level=5, seed=seed, embedder="none").text
        assert "uarterly report (v2) is attached; see section 4.1" in out


# --- realisation -------------------------------------------------------------------

def _det(text, question=False, frame="predicate_adj"):
    toks = tokenize(text)
    caps = {"subj": next(t for t in toks if t.norm in ("you", "he", "she", "they", "i")),
            "be": next(t for t in toks if t.norm in ("are", "is", "was", "were", "am"))}
    return Detection(0, len(toks), ("CRAZY",), frame, 3, "trigger", "crazy", captures=caps,
                     clause_start=0, question=question)


@pytest.mark.parametrize("text, question, expected", [
    ("you are crazy", False, "you have a kangaroo loose in your top paddock"),
    ("he is crazy", False, "he has a kangaroo loose in his top paddock"),
    ("she was crazy", False, "she had a kangaroo loose in her top paddock"),
    ("I am crazy", False, "I have a kangaroo loose in my top paddock"),
    ("are you crazy", True, "do you have a kangaroo loose in your top paddock"),
    ("is he crazy", True, "does he have a kangaroo loose in his top paddock"),
    ("were they crazy", True, "did they have a kangaroo loose in their top paddock"),
])
def test_clause_realisation(dictionary, text, question, expected):
    entry = dictionary.entries["roos-top-paddock"]
    assert realise(entry, entry.form, _det(text, question)) == expected


def test_be_clause_question(dictionary):
    entry = dictionary.entries["having-a-lend"]
    assert realise(entry, entry.form, _det("are you kidding", True, "clause")) == "are you having a lend"


def test_inflect():
    assert inflect("carry", "ing") == "carrying" and inflect("whinge", "ing") == "whingeing"
    assert inflect("spit", "past") == "spat" and inflect("do", "3sg") == "does"


def test_brief_sample_shape(translator):
    """With the gated sample entries unlocked, level 5 can produce the brief's flavour text."""
    hits = 0
    for seed in range(60):
        r = translator.translate(RANT, level=5, seed=seed, unlock=("not_aussie", "fabricated"))
        hits += "kangaroo loose in yer top paddock" in r.text and "pork chop" in r.text
    assert hits


# --- whole-idea rewrites with a captured noun phrase ------------------------------

def test_doubt_rewrites_whole_clause_with_np_and_tense(translator):
    text = "The Hare, believing her assertion to be simply impossible, assented to the proposal."
    outs = {translator.translate(text, level=5, seed=s).text for s in range(20)}
    assert any("reckonin' her assertion had Buckley's" in o or "reckoning her assertion had Buckley's" in o
               for o in outs)
    assert any("there was no bloody way her assertion would come off" in o for o in outs)
    assert all("simply impossible" not in o for o in outs)
    assert any("gave the proposal the nod" in o or "went along with the proposal" in o for o in outs)


def test_doubt_present_tense(translator):
    outs = {translator.translate("I believe it to be impossible.", level=4, seed=s).text for s in range(20)}
    assert "I reckon it has Buckley's." in outs
    assert any(o.startswith("I reckon there is no bloody way it") for o in outs)


def test_impossible_becomes_there_clause(translator):
    outs = {translator.translate("That's simply impossible.", level=5, seed=s, vulgarity=1).text
            for s in range(20)}
    assert any(o.startswith(("There's no bloody way.", "Strewth, there's no bloody way.")) or
               "there's no bloody way." in o for o in outs)
    q = {translator.translate("Is it impossible?", level=4, seed=s).text for s in range(20)}
    assert any(o.startswith("Is there") for o in q)


def test_trailing_np_runs_to_a_boundary(dictionary):
    from aussiefy.matcher import compile_pattern, match_at
    from aussiefy.text import tokenize
    p = compile_pattern("assent to {np}", "vp", ("GO_ALONG",), 3)
    toks = tokenize("assented to the new proposal; and then")
    m = match_at(p, toks, 0)
    assert m.captures["np"].text == "the new proposal" and toks[m.end].text == ";"


def test_australian_spelling_at_every_level(translator):
    for level in (1, 3, 5):
        out = translator.translate("Mom honored the neighbors and organized a gray color scheme.", level=level, seed=0).text
        for word in ("honoured", "neighbours", "organised", "grey", "colour"):
            assert word in out.lower(), (level, out)
    assert "Labor" in translator.translate("The Labor Party won.", level=1, seed=0).text


def test_swear_infixes_respect_the_cap(translator):
    text = "We can't dedicate this ground, it's a great big job, and we won't forget every word."
    loud = {translator.translate(text, level=5, seed=s).text for s in range(15)}
    assert any("bloody well" in o for o in loud) and any("bloody great" in o or "bloody big" in o for o in loud)
    clean = {translator.translate(text, level=5, seed=s, vulgarity=0).text for s in range(15)}
    assert not any("bloody" in o for o in clean)
    assert not any("bloody long" in o for o in loud)


def test_living_and_dead_is_not_the_verb(translator):
    for s in range(10):
        out = translator.translate("The brave men, living and dead, struggled here.", level=5, seed=s).text
        assert "kickin' and dead" not in out


def test_strong_tier_only_when_asked_for(translator):
    text = "Wow, he's a nice guy and that was absolutely a great game. Go away!"
    strong = ("cunt",)
    for level in range(1, 6):
        for s in range(15):
            out = translator.translate(text, level=level, seed=s).text.lower()
            assert not any(w in out for w in strong), (level, s, out)
    tradie = [translator.translate(text, level=5, seed=s, vulgarity="tradie").text.lower() for s in range(15)]
    assert any(any(w in o for w in strong) for o in tradie)
    level5 = [translator.translate(text, level=5, seed=s).text.lower() for s in range(15)]
    assert any("fuck" in o for o in level5), "the f-word is common-but-impolite: plain level 5 allows it"
    assert not any("fuck" in translator.translate(text, level=4, seed=s).text.lower() for s in range(15))


def test_mild_words_calibrated_for_australia(dictionary):
    assert dictionary.entries["brave-bastards"].vulgarity == 1
    assert dictionary.entries["donger"].vulgarity == 1
    assert dictionary.entries["a-good-cunt"].vulgarity == 3


def test_asides_only_at_chant_stanza_ends_and_after_questions(translator):
    chant = "\n\n".join(["Moloch! Filth! Ugliness! Dollars! Moloch the loveless! Moloch the prison!"] * 4)
    asides = []
    for seed in range(20):
        r = translator.translate(chant, level=5, seed=seed, embellishment="troppo")
        asides += [g for g in r.garnish if g.placement == "aside" and g.entry_id]
        assert not any(g.placement == "opener" and g.entry_id for g in r.garnish)   # openers break a chant
    assert asides and all(g.sentence % 6 == 5 for g in asides)   # the last line of a stanza
    story = ("The dog ran down the road. The cat sat on the fence. The farmer chased the dog. "
             "The rain came down hard. \"Get back here!\" he yelled. The dog hid under the shed.")
    for seed in range(20):
        assert not any(g.placement == "aside" and g.entry_id for g in translator.translate(story, level=5, seed=seed, embellishment="troppo").garnish)
    # level 4 has no asides of its own; a sweary one (the vulgarity's) still keeps to stanza ends
    assert not any(g.placement == "aside" for s in range(10)
                   for g in translator.translate(chant, level=4, vulgarity="nan", seed=s, embellishment="troppo").garnish)
    sweary = [g for s in range(10) for g in translator.translate(chant, level=4, seed=s, embellishment="troppo").garnish
              if g.placement == "aside" and g.entry_id]
    assert all(g.sentence % 6 == 5 and translator.dictionary.entries[g.entry_id].vulgarity for g in sweary)


def test_tail_rounds_off_a_closing_list(translator):
    text = "The thief stole their money and jewels."
    tails = {g.text for s in range(20) for g in translator.translate(text, level=5, seed=s).garnish
             if g.placement == "tail" and g.entry_id}
    assert tails
    out = next(translator.translate(text, level=5, seed=s).text for s in range(20)
               if any(g.placement == "tail" and g.entry_id for g in translator.translate(text, level=5, seed=s).garnish))
    assert re.search(r"jewels, the (lot|whole)", out)


def test_infix_skips_ya(translator):
    r = translator.translate("So she went inside. Wouldn't ya know it.", level=5, seed=0)
    assert "bloody well ya" not in r.text


def test_riffs_attach_once_per_sentence_where_a_clause_ends(translator):
    text = "Ashcans and dollars! The ashcans were full. Ashcans everywhere!"
    seen = []
    for seed in range(20):
        r = translator.translate(text, level=5, seed=seed)
        riffs = [x for x in r.records if x.riff]
        assert len(riffs) <= translator.dictionary.profiles[5].max_garnish["riff"]
        assert len({x.span for x in riffs}) == len(riffs)
        seen += [x.output for x in riffs]
    assert any("bin chickens" in o for o in seen)
    assert not any(x.riff for s in range(10) for x in translator.translate(text, level=4, seed=s).records)


def test_riff_mood_is_a_lean_not_a_rule(translator):
    from aussiefy.context import riff_weight, text_mood

    solemn = ("We are met to dedicate this ground. We consecrate and hallow it with devotion, for those who "
              "perished here in the war.")
    light = "The happy children ran off into the forest."
    assert text_mood(solemn) == "solemn" and text_mood(light) == "light"
    assert riff_weight("comic", "solemn") < riff_weight("grim", "solemn") == riff_weight("plain", "solemn")
    assert 0 < riff_weight("grim", "light") < riff_weight("comic", "light")
    tones = {r.text: r.tone for e in translator.dictionary.entries.values() for r in e.riffs}
    picked = [tones[x.riff] for s in range(60) for x in translator.translate(light, level=5, seed=s).records
              if x.riff]
    assert picked and picked.count("grim") < len(picked) / 2   # leaning away, not banned


def test_multiword_names_said_once(translator):
    text = "They walked into the city. The city was loud. Everyone in the city slept."
    for seed in range(10):
        out = translator.translate(text, level=5, seed=seed).text
        assert out.lower().count("the big smoke") <= 1


def test_variety_one_always_picks_the_best_fit():
    from aussiefy.engine import Translator

    tr = Translator()
    text = "She was very tired. He was furious. They were really scared."
    cut = 0
    for seed in range(6):
        wide = tr.translate(text, level=5, seed=seed)
        r = tr.translate(text, level=5, seed=seed, variety=1)
        best = {rec.span: max(c.weight for c in rec.eligible) for rec in wide.records if rec.eligible}
        for rec in r.records:
            if rec.chosen is not None:
                assert rec.eligible == [rec.chosen] and rec.chosen.weight == best[rec.span]
                cut += sum("variety 1" in why for _, why in rec.rejected)
    assert cut   # some slot had more than one eligible term


def test_variety_zero_is_the_default():
    from aussiefy.engine import Translator

    tr = Translator()
    text = "Goldilocks was very tired and hungry, so she ate the porridge."
    assert tr.translate(text, level=4, seed=3).text == tr.translate(text, level=4, seed=3, variety=0).text


def test_tag_after_a_closing_quote_is_judged_on_the_narration():
    from aussiefy.context import sentence_contexts
    from aussiefy.engine import Translator
    from aussiefy.text import tokenize

    tr = Translator()
    text = ('"O you fool," said she, "then we must all four die of hunger; you may as well plane the planks for '
            'our coffins,"--and she left him no peace until he consented.')
    for seed in range(12):
        out = tr.translate(text, level=5, seed=seed, embellishment="troppo").text
        assert not any(out.rstrip().split(".")[0].endswith(t) for t in (", ya drongo", ", mate", ", ya mug"))
    assert "action_end" in sentence_contexts(tokenize("And she left him no peace until he consented."))
    for t in ("His only ambition was to be always well dressed.", "She knocked, and nobody answered.",
              "And then the old man died."):
        assert "action_end" not in sentence_contexts(tokenize(t))


SWEARY = " ".join([
    "Good grief, are you crazy? You're overreacting and I'm extremely busy. Nobody cares, go away.",
    "It was very cold and the whole thing was broken. Everyone said it was nonsense.",
    "The kids were stupid and the dog was useless, but the dinner was very good.",
] * 3)


def _swears(translator, **kw):
    d = translator.dictionary
    outs = [translator.translate(SWEARY, seed=s, **kw).text.lower() for s in range(8)]
    return [d.swear_strength(w) for o in outs for w in re.findall(r"[a-z']+", o) if d.swear_strength(w)]


def test_swearing_follows_the_vulgarity_not_the_level(translator):
    """The dials are orthogonal: a tourist can swear like a tradie, and a swaggie can talk like your nan."""
    for level in (1, 3, 5):
        assert not _swears(translator, level=level, vulgarity="nan"), level
        assert _swears(translator, level=level, vulgarity="tradie"), level
    tourist, swaggie = (len(_swears(translator, level=lv, vulgarity="uncle-bob")) for lv in ("tourist", "swaggie"))
    assert tourist >= swaggie / 3, (tourist, swaggie)   # the level changes how much is Aussified, not how vulgar


def test_each_vulgarity_sounds_like_its_tier(translator):
    dad, tradie = _swears(translator, level=5, vulgarity="dad"), _swears(translator, level=5, vulgarity="tradie")
    assert max(dad) == 1 and 3 in tradie
    assert sum(s >= 2 for s in tradie) / len(tradie) > 0.4    # tradie leans to its own tiers, not "bugger"


def test_an_opener_lowers_a_word_the_text_writes_in_lower_case(translator):
    """'Install' isn't a name when the text also says 'installed': an opener lowers it."""
    text = ("She kept watering the roses while he was weeding the beds. Watering them was the best part of her "
            "day, she said. Weeding was his. He told her she was mad, and she laughed at him.")
    outs = [translator.translate(text, level=5, seed=s).text for s in range(40)]
    assert not any(re.search(r"\b\w+, (?:Watering|Weeding)\b", o) for o in outs)
    assert any(re.search(r"\w, (?:watering|weeding) (?:them|was)", o) for o in outs)


@pytest.mark.parametrize("text, wrong", [
    ("We are working on getting him glasses.", ["stuffed", "cactus"]),     # not a fragment of "not working"
    ("He will be under the management of Tex.", ["crook"]),                # nor of "under the weather"
    ("Mixing is still less certain this far out.", ["half-cut", "maggoted", "rotten"]),  # "less" isn't "legless"
    ("The United Nations designated the park.", ["mob"]),                  # a word inside a name
    ("He studied at Boston University.", ["uni"]),
    ("The U.S. Food and Drug Administration approved it.", ["tucker", "Tucker", "S. Stone", "S. Crikey"]),
    ("What makes a children's game fun is chance.", ["littlies", "fellas"]),  # a possessive plural
    ("The gasoline tank may be drained by opening the cock.", ["rooted", "knackered", "stuffed"]),  # people only
    ("See that the water jackets are full.", ["stuffed"]),
    ("This should be done in any case.", ["stuffed", "knackered"]),
    ("A good many people came along.", ["beaut"]),
    ("Add a few drops of food coloring to the tank.", ["tucker"]),
    ("The show is at 10 a.m. on Monday. Fans meet Lorie K. Logan there.", ["m. Now", "K. Anyway", "K. Strewth",
                                                                           "m. Crikey", "K. Crikey"]),
])
def test_everyday_pass_wrong_senses_stay_plain(translator, text, wrong):
    """Wrong senses the everyday pass found (research/everyday-pass-2026-10-12/FINDINGS.md)."""
    for seed in range(6):
        out = translator.translate(text, level=5, seed=seed, vulgarity="nan").text
        assert not any(w in out for w in wrong), (seed, out)


def test_misspellings_and_people_still_swap(translator):
    out = " ".join(translator.translate(t, level=5, seed=s, vulgarity="nan").text for s in range(4) for t in (
        "He was exhaustedd after the walk.", "I am so full.", "She was drained after work.",
        "The hikers were exhausted.", "Have a merry Christmas, my friend!"))
    assert "exhaustedd" not in out and "I'm so full" not in out and "hikers were exhausted" not in out
    assert "Chrissie" in out


def test_one_syllable_verbs_double_their_consonant():
    from aussiefy import morph

    assert [morph.inflect(v, "past") for v in ("lob", "chat", "visit", "rain", "win")] == [
        "lobbed", "chatted", "visited", "rained", "won"]
    assert morph.inflect("lob", "ing") == "lobbing"


# --- rails that rejected good swaps ----------------------------------------------------------------------------

def _all(translator, text, level=4, seeds=range(12)):
    return [translator.translate(text, level=level, seed=s).text for s in seeds]


def test_a_possessive_or_article_is_kept_or_dropped_to_fit_the_term(translator):
    outs = _all(translator, "His wife was cooking.") + _all(translator, "We mourn the dead.") \
        + _all(translator, "They camped by the waterhole.")
    assert any("missus was cooking" in o for o in outs)                 # his wife -> the/his missus
    assert any("the poor buggers" in o for o in outs)                   # the dead keeps its article
    assert any("the billabong" in o for o in outs)                      # the term's own "a" goes
    assert not any(bad in o for o in outs for bad in ("the a ", "His the", "the the"))


def test_a_plural_trigger_keeps_the_plural(translator):
    outs = _all(translator, "The wild horses ran past.")
    assert any("brumbies" in o for o in outs) and not any("brumby ran" in o for o in outs)


def test_a_phrase_that_goes_on_past_the_swap_is_left(translator):
    # "the poor" as a noun ("the poor are hungry") isn't "the poor old minister"
    for o in _all(translator, "The poor old minister tried his best. I pity the poor children."):
        assert "battlers old" not in o and "battlers children" not in o, o


def test_a_term_that_carries_its_own_negation_takes_no_extra_one(translator):
    assert not any("no Buckley's" in o for o in _all(translator, "You have no chance of winning."))


def test_the_subject_is_found_past_the_verb_chain(translator):
    outs = _all(translator, "You are not going to get rich that way.")
    assert any("rich" not in o for o in outs)                            # a person's idiom can go in
    for o in _all(translator, "The tank may be drained."):
        assert "drained" in o, o                                         # a tank still isn't a person


def test_a_subject_pronoun_fills_a_verb_phrases_possessive(translator):
    outs = {translator.translate(t, level=4, seed=s).text for s in range(12)
            for t in ("They sat down to rest.", "He sat down to rest.")}
    assert any("plonked themselves down" in o for o in outs) and any("plonked himself down" in o for o in outs)
    assert not any(bad in o for o in outs for bad in ("theirself", "hisself"))
