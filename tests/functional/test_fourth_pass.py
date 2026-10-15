"""Wrong senses the fourth everyday pass found (research/fourth-pass-2026-10-14/FINDINGS.md and the yarn agents'
notes), fixed in the dictionary by the fourth-pass round (research/fourth-pass-round-2026-10-14/DECISIONS.md), each
pinned with the right sense that must still swap; and the round's new entries in and out of their sense."""

from pathlib import Path

import pytest

from aussiefy import harness, translate

ROOT = Path(__file__).resolve().parents[2]
EVERYDAY = ROOT / "tests" / "corpus" / "everyday"
FOURTH = ROOT / "research" / "fourth-pass-2026-10-14" / "texts"


def _seeds(translator, text, n=6, **kw):
    kw = {"level": 4, "embellishment": "dinkum", **kw}
    return [translator.translate(text, seed=s, **kw).text for s in range(n)]


@pytest.mark.parametrize("text, never", [
    # a legal designation and forestry terms of art aren't the bush
    ("Does Yellowstone include a federally designated wilderness? Cutting a tree improves forest health, and "
     "forest health experts pick the areas.", ["bush"]),
    # the US Congress acting, or named in an institution, isn't Parliament House
    ("Congress has not acted on the recommendation. The bill passed Congress. Members of Congress voted. The "
     "Library of Congress listed the song.", ["Parliament"]),
    # knocking together is building roughly: not relationships, an auction program, a threat that builds
    ("The program builds relationships. We build an auction. The threat builds. It is built on open "
     "infrastructure. They built a house of bricks.", ["knock"]),
    # brilliant coders are clever, brilliant colours bright
    ("We are thrilled to see brilliant young coders. What brilliant colours!", ["beaut", "ripper", "bonz", "grouse"]),
    # getting excited is getting worked up or enthused, not delighted
    ("At the end of the race she would get excited and desperate. Young coders get excited by learning.",
     ["rapt", "happy as Larry", "shot fox"]),
    # highs that struggle to climb aren't doing it tough
    ("Highs will likely struggle to get out of the 40s.", ["tough"]),
    # a talent and the fixed compounds aren't pressies
    ("She has a gift for languages. Buy a gift card at the gift shop.", ["pressie", "prezzie"]),
    # foods are counted kinds: "thick tucker are cooked" breaks the agreement
    ("When thick foods are cooked, the outer layers heat first. Processed foods keep longer.", ["tucker"]),
    # exact sums and the responsibility idioms aren't quid
    ("He never gets more than sixty cents on the dollar, but a dollar is worth one hundred cents to him. The "
     "buck stops here. They pass the buck.", ["quid"]),
    # things that turn up or show up don't rock up
    ("The lost keys turned up in a drawer. Your changes will show up correctly. The colouring shows up well.",
     ["rock", "lob", "front"]),
    # the jet stream and a forecast's northern stream are air
    ("A stronger northern stream trough will push east under the jet stream.", ["creek"]),
    # give a stuff about is negative: not an instruction to pay attention, or a company that cares
    ("Pay attention to the width of the flapper. We care about your privacy.", ["stuff", "hoots", "shit", "rat's"]),
    # counted loads and lots aren't heaps
    ("It takes the water for 60 loads of dishes. The parking lots were full.", ["heaps"]),
    # darts in a list read as the pub game
    ("Close dancing, Sunday baseball and cigarettes were among the objects of his zeal.", ["dart"]),
    # "not much of a" is a predicate; "nothing but" is only
    ("Not much of a housekeeper, would you say? There was nothing but the napkin.", ["bugger", "fuck all"]),
    # a full pair of hands, the adjective "fellow", remorse
    ("Farmers' wives have their hands full.", ["mitts"]),
    ("He thanked his fellow Texans and his fellow citizens.", ["bloke", "cove"]),
    ("Naturally, I felt terrible about stealing the blanket.", ["crook", "shocker", "shithouse"]),
    # a virtuous parson is a good man, not a champion
    ("He was the best exhorter about here, and a good man.", ["dead-set"]),
    # the horse has bolted (too late), bolting a shelf on, setting off with a destination, a project starting
    ("It's too late, the horse has bolted. They bolted the shelf onto the wall. The project is getting going at "
     "last. After lunch she heads off to the shops.", ["shot through", "shoots through", "clear", "frog and toad",
                                                       "piss"]),
    # things that stick out, overdoing the salt, unlikely luck
    ("A nail sticks out of the board. Don't go mad with the salt. You'd be lucky if it lasts a week.",
     ["sore thumb", "dunny", "troppo", "the plot", "lucky bugger"]),
    # war stories, battling to climb, rain that keeps going, a coin toss, packing papers
    ("He told war stories. Highs will battle to climb. The rain will keep going overnight. It came down to a coin "
     "toss. Bundle up the old newspapers.", ["stoush", "battle on", "chuck", "rug up"]),
    # people who aren't parents, the third person's "no idea", the whole lot of you, a dog's breakfast
    ("The folks at the agency were friendly. She had no idea the blanket was theirs. I mean the whole lot of you. "
     "It was a proper dog's breakfast.", ["oldies", "olds", "dunno", "box and dice", "brekkie"]),
    # a client dinner isn't tea; thick air isn't stupid; the verb "kid"; older kids aren't littlies
    ("We took the client out for dinner. The air is thick with vapour. Don't kid yourself. The high school kids "
     "are sixteen.", ["tea", "dilly", "ankle", "littlie", "tacker"]),
    # a noise isn't a lurk
    ("The mare raised a racket with her coughing.", ["lurk", "caper"]),
    # a plain "No" answering a question isn't an emphatic or a doubled no; reassurance isn't a reply to thanks
    ("Can I swim in the lake? No. The water is dangerously cold.", ["nelly", "Nah, nah"]),
    ("Don't worry, it won't explode, but it will make a mess.", ["All good", "all good"]),
])
def test_never(translator, text, never):
    for out in _seeds(translator, text):
        assert not any(bad in out for bad in never), out


@pytest.mark.parametrize("text, wanted", [
    ("We walked deep into the wilderness. The forest was dark.", ["bush"]),
    ("They threw together a shed out of old timber.", ["knocked together"]),
    ("It was a brilliant game.", ["beaut", "ripper", "bonzer", "grouse"]),
    ("She was thrilled with the result.", ["rapt", "stoked", "happy as Larry"]),
    ("Families are struggling.", ["doing it tough"]),
    ("She gave me a gift for my birthday.", ["pressie", "prezzie"]),
    ("We need food for the trip.", ["tucker"]),
    ("I need fifty bucks.", ["quid"]),
    ("He turned up at the party.", ["rocked up", "lobbed"]),
    ("We swam in the stream.", ["creek"]),
    ("I couldn't care less about the score.", ["give a stuff", "give two hoots", "give a shit", "rat's arse"]),
    ("We had loads of fun.", ["heaps"]),
    ("He lit a cigarette.", ["a dart", "ciggie", "durry"]),
    ("There was nothing in the fridge.", ["bugger all", "bugger-all"]),
    ("Keep your hands warm.", ["mitts"]),
    ("Some of these young fellows never work.", ["bloke", "cove"]),
    ("The fellow who hasn't got it.", ["bloke", "cove"]),
    ("The weather was terrible.", ["crook", "shocker", "shithouse"]),
    ("She's an absolute star.", ["dead-set legend", "a legend"]),
    ("He bolted.", ["shot through"]),
    ("We'd better head off.", ["shoot through", "clear out", "frog and toad", "piss off"]),
    ("She'll go mad if she finds out.", ["troppo", "the plot"]),
    ("Toss me the keys.", ["Chuck"]),
    ("Bundle up, it's cold.", ["Rug up"]),
    ("My folks are visiting.", ["oldies", "olds"]),
    ("I have no idea.", ["dunno"]),
    ("Dinner is ready.", ["Tea"]),
    ("They took the whole lot.", ["box and dice", "shebang", "bloody show"]),
    ("Keep going!", ["Battle on", "show goin'"]),
    ("No, no, that's not it.", ["Nah, nah"]),
    ("Thanks for the lift! No problem.", ["All good", "No worries", "No dramas", "She'll be right"]),
])
def test_the_right_sense_still_swaps(translator, text, wanted):
    outs = _seeds(translator, text, n=8, level=5)
    assert any(any(w in o for w in wanted) for o in outs), outs


def _texts(translator, path, n=3):
    text = path.read_text(encoding="utf-8")
    markup = "auto" if path.suffix in (".md", ".mdx") else "text"
    return [translate(text, translator=translator, level=lv, seed=s, markup=markup).text for lv in (2, 4) for s in range(n)]


def test_terms_of_art_in_their_genres(translator):
    # a gifts policy's "gift" and a policy's "nothing" are terms, an FOMC vote isn't reckoning it a goer
    for out in _texts(translator, FOURTH / "workplace__github_gifts_policy" / "original.md"):
        assert "pressie" not in out and "prezzie" not in out, out
    for out in _texts(translator, FOURTH / "workplace__fomc_minutes_policy_actions" / "original.txt"):
        assert "goer" not in out and "righto" not in out and "the nod" not in out, out
    # a news report's "the city" has no bush viewpoint
    for out in _texts(translator, EVERYDAY / "news" / "nashville_kurdish_community_anniversary.txt"):
        assert "Big Smoke" not in out, out
    # an obituary's fellow alumni are fellow members, not blokes
    for out in _texts(translator, EVERYDAY / "news" / "bob_weir_obituary.txt"):
        assert "bloke Grateful" not in out and "cove Grateful" not in out, out
    # the Yellowstone FAQ's Congress is the real one
    for out in _texts(translator, EVERYDAY / "instructions" / "nps_yellowstone_faq.txt"):
        assert "Parliament" not in out, out


def _suggested(text, word):
    return [s for s in harness.lint(text, level=4)["suggestions"] if s["text"].lower() == word]


def test_lint_leaves_other_senses_alone():
    assert not _suggested("The lost keys turned up in a drawer.", "turned up")
    assert not _suggested("A nail sticks out of the board.", "sticks out")
    assert not _suggested("The buck stops here.", "buck")
    assert not _suggested("It came down to a coin toss.", "toss")
    assert not _suggested("The ciphertext bytes head off to Avail.", "head off")
    # and the plain senses are still suggested
    assert _suggested("He turned up at the party.", "turned up") and _suggested("I need fifty bucks.", "bucks")


@pytest.mark.parametrize("text, wanted", [
    ("Give me a shout when you get back.", "Give me a hoy"),
    ("Give me the lowdown on the new boss.", "the drum"),
    ("That's all.", "That's your lot"),
    ("Go ahead.", "Go for your life"),
    ("As sure as can be, he was late again.", "Sure as eggs"),
    ("Booking ahead is the way to go.", "is the go"),
    ("That's a tricky question.", "a curly"),
    ("It'll all turn out fine.", "come good"),
    ("The garage tried to overcharge us.", "sting us"),
    ("Let's split the bill fifty-fifty.", "go halves"),
    ("The workers walked off the job.", "downed tools"),
    ("We finally got it across the finish line.", "got it over the line"),
    ("We can sort that out somewhere down the line.", "down the track"),
    ("The update took forever.", "took longer than a wet week"),
    ("I wouldn't trust that crowd.", "that mob"),
    ("The kids were bouncing off the walls.", "red cordial"),
    ("The coach will give the new players the once-over.", "run the ruler over the new players"),
    ("Get out of the way!", "out of the road"),
    ("She won a medal for bravery.", "a gong"),
    ("I won't put up with it.", "cop it"),
    ("Old people love a chat.", "oldies"),
    ("It cost a lot of money.", "a fair whack"),
])
def test_the_rounds_new_entries(translator, text, wanted):
    assert any(wanted in o for o in _seeds(translator, text, n=8, level=5)), wanted


@pytest.mark.parametrize("text, never", [
    ("Go ahead and click Save. Help yourself to a plate.", ["for your life", "for yer life"]),
    ("That's all I know.", ["your lot", "yer lot"]),
    ("The way to go home is long. We have a long way to go.", ["the go"]),
    ("They worked out at the gym.", ["come good", "came good"]),
    ("Split the cost of the car with her.", ["halves of"]),
    ("We stopped work on the project.", ["tools"]),
    ("She lives down the road.", ["down the track"]),
    ("That outfit looks great. That lot is for sale.", ["mob"]),
    ("Get the paperwork out of the way first.", ["the road"]),
    ("An award of damages was made.", ["gong"]),
    ("I travel quite a lot.", ["fair whack"]),
    # "this crowd" pointed at here isn't "that mob" over there
    ("I don't trust this crowd at all.", ["that mob"]),
    # the drum is inside word passed on, not the real story behind a claim
    ("The real story is that the dam failed.", ["drum"]),
    # sting is irregular
    ("They overcharged us for parking.", ["stinged"]),
    # from the design review: a place down the road, a bill split in a chamber, a stop work order, a tossed salad
    ("The pub is further down the road on the left. Further down the line, the train stops at Penrith.",
     ["down the track"]),
    ("The Senate voted to split the bill into two parts.", ["halves"]),
    ("They issued a stop work order.", ["tools"]),
    ("Toss the salad with oil.", ["Chuck", "chuck"]),
])
def test_the_rounds_new_entries_keep_to_their_sense(translator, text, never):
    for out in _seeds(translator, text, n=8, level=5):
        assert not any(bad in out for bad in never), out


def test_lookup_finds_the_new_senses():
    def forms(q):
        return [r["form"] for r in harness.lookup(q)["results"]]
    assert "the drum" in forms("the drum")
    assert "cop {np}" in forms("cop")


def test_dialect_hire_and_per_cent(translator):
    out = translator.translate("About 50 percent of the rental cars were gone, so we rented a car in town.",
                               level=1, english="us").text
    assert "per cent" in out and "hire cars" in out and "hired a car" in out, out
    assert "rent a house" in translator.translate("They rent a house.", level=1, english="us").text


@pytest.mark.parametrize("text", [
    "They split the bill among six friends.", "We agreed to split the costs equally among the three of us.",
    "Three friends split the bill.", "We all went Dutch.", "They went Dutch and each paid for their own meal.",
])
def test_halves_need_two_equal_shares(translator, text):
    for out in _seeds(translator, text, n=3, level=5, embedder="none"):
        assert "halves" not in out


@pytest.mark.parametrize("text", ["Let's go fifty-fifty.", "We split the cost fifty-fifty."])
def test_two_equal_shares_still_offer_halves(translator, text):
    assert any("halves" in out for out in _seeds(translator, text, level=5, embedder="none"))
