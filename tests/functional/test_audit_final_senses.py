"""Source-reviewed audit corrections retain action, force, arguments and noun subtype."""

import pytest

from aussiefy import Translator, load_dictionary

PROFILE = {
    "phonetic": 0,
    "substitution": {"lexical": 1, "phrase": 1, "idiom": 1},
    "garnish": {"riff": 0},
    "swearing": {"infix": 0, "exclaim": 0, "closer": 0},
}


def render(tr, text, seed=0):
    return tr.translate(
        text,
        level=5,
        vulgarity=3,
        seed=seed,
        embellishment=0,
        embedder="none",
        registers=["current", "dated", "archaic"],
        unlock=["all"],
        document_type="custom",
        document_config={"profile": PROFILE},
    )


def offered(result):
    return {c.entry.id for r in result.records for c in r.eligible}


@pytest.mark.parametrize(
    "text,forbidden",
    [
        ("She went to the bathroom to wash her hands.", {"point-percy"}),
        ("I doubt the plan would work, but it might.", {"reckon-no-bloody-way", "reckon-had-buckleys"}),
        ("They carried on the work but did not finish it.", {"see-the-job-through"}),
        ("I tasted the soup.", {"have-a-crack-at", "have-a-lash", "give-it-a-burl"}),
        ("He wept silently.", {"bawl", "blubber", "bawl-eyes-out", "have-a-sook"}),
        ("He wept quietly at the funeral.", {"bawl", "blubber", "bawl-eyes-out", "have-a-sook"}),
        ("She attends a vocational college.", {"uni"}),
        ("The old ice box was a kitchen refrigerator.", {"esky"}),
        ("The refugee sought asylum from persecution.", {"loony-bin"}),
        ("The fox slept in its den.", {"lounge-room"}),
        ("We watched a glossy ibis wading in the marsh.", {"bin-chicken"}),
        ("The small rubbish bin had no wheels.", {"wheelie-bin"}),
        ("The aircraft landed on the runway pavement.", {"footpath"}),
        ("The ant waved its antennae.", {"aerial"}),
        ("The painting is unfinished work.", {"hard-yakka"}),
        ("It was an easy chore.", {"hard-yakka", "yakka"}),
        ("She is a decent person.", {"top-bloke"}),
        ("I don't think so, but I might be wrong.", {"no-bloody-way", "no-fuckin-way"}),
        ("I have been eating.", {"been-at"}),
        ("I have been eating every day.", {"been-at"}),
        ("I have been eating at dawn.", {"been-at"}),
        ("I have been eating quickly.", {"been-at"}),
        ("He is a comedian, but not funny.", {"a-funny-cunt", "a-funny-bugger"}),
        ("Who knows the answer?", {"no-fuckin-idea"}),
        ("Most certainly not in any way whatsoever.", {"is-it-buggery"}),
        ("We walked the dog.", {"hoof-it"}),
        ("She went into labour at dawn.", {"hard-yakka", "yakka"}),
        ("The gallery displays her work of art.", {"hard-yakka", "yakka"}),
        ("He peed blood.", {"point-percy"}),
        ("He peed himself.", {"point-percy"}),
        ("I have been eating a lot.", {"been-at"}),
        ("I have been eating a little.", {"been-at"}),
        ("I have been eating quite a lot.", {"been-at"}),
        ("I have been eating a fair bit.", {"been-at"}),
        ("I have been eating a great deal.", {"been-at"}),
    ],
)
def test_does_not_invent_a_sense_or_argument(translator, text, forbidden):
    assert not offered(render(translator, text)) & forbidden


@pytest.mark.parametrize(
    "text,expected",
    [
        ("He urinated.", "point-percy"),
        ("I believe the plan could never happen.", "reckon-had-buckleys"),
        ("They completed the job.", "see-the-job-through"),
        ("I tried the new tool.", "have-a-crack-at"),
        ("He cried loudly.", "bawl"),
        ("He cried loudly and uncontrollably.", "bawl-eyes-out"),
        ("He sulked about losing.", "have-a-sook"),
        ("She attends a university.", "uni"),
        ("She packed a portable ice box.", "esky"),
        ("The mental hospital is old.", "loony-bin"),
        ("The living room is bright.", "lounge-room"),
        ("We saw a white ibis.", "bin-chicken"),
        ("The wheeled rubbish bin is outside.", "wheelie-bin"),
        ("She walked along the pavement.", "footpath"),
        ("The radio antennae are broken.", "aerial"),
        ("It was hard work.", "hard-yakka"),
        ("He is a good man.", "top-bloke"),
        ("Absolutely not!", "no-bloody-way"),
        ("I have been eating the biscuits.", "been-at"),
        ("I have been eating the little biscuits.", "been-at"),
        ("I have been eating a lot of biscuits.", "been-at"),
        ("He is a funny person.", "a-funny-bugger"),
        ("Who knows?", "no-fuckin-idea"),
        ("We walked home.", "hoof-it"),
    ],
)
def test_explicit_meaning_remains_available(translator, text, expected):
    assert expected in offered(render(translator, text))


def test_destination_and_progressive_object_survive_rendering(translator):
    assert render(translator, "We walked home.").text == "We hoofed it home."
    assert render(translator, "We walked there.").text == "We hoofed it there."
    out = render(translator, "I have been eating the biscuits.")
    assert "been at the" in out.text and out.text.endswith(("biscuits.", "bikkies."))


def test_lookup_only_replaces_cannot_reenable_automatic_mapping(tmp_path):
    p = tmp_path / "lookup.yaml"
    p.write_text("""format: aussiefy-dictionary-overlay/v1
add_concepts:
  TEST_LOOKUP:
    description: A writer-only expression.
    lookup_only: true
    triggers: {interjection: [indeed]}
add_entries:
- id: lookup-test
  form: whoop
  concept: [TEST_LOOKUP]
  frame: interjection
  replaces: [absolutely]
""")
    dictionary = load_dictionary([p])
    tr = Translator(dictionary, lookup_embedder=None)
    assert not any("TEST_LOOKUP" in p.concepts for p in dictionary.patterns)
    assert "lookup-test" not in offered(render(tr, "Absolutely!"))
    assert any(p.entry_id == "lookup-test" for p in dictionary.form_index.patterns)


@pytest.mark.parametrize("qualifier", ["radio", "TV", "television", "car", "wireless", "broadcast", "satellite"])
@pytest.mark.parametrize("noun", ["antenna", "antennas", "antennae"])
def test_electronic_antenna_keeps_its_qualifier_and_number(translator, qualifier, noun):
    out = render(translator, f"The {qualifier} {noun} broke.")
    record = next(r for r in out.records if "ANTENNA" in r.det.concepts)
    assert record.text == noun
    expected = "aerial" if noun == "antenna" else "aerials"
    assert expected in out.text
    assert qualifier in out.text or qualifier == "radio" and "wireless" in out.text


def test_general_yakka_discovery_does_not_claim_only_hard_work(translator):
    assert "WORK" in translator.dictionary.entries["yakka"].concept
    assert "yakka" in offered(render(translator, "It was hard work."))
