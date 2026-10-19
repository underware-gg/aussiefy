from aussiefy.scrape.fragments import candidate_fragments, extract_fragments
from aussiefy.scrape.harvest import harvest, harvest_pairs


def test_fragments_find_buried_slang_and_skip_known(dictionary):
    frags = candidate_fragments("hit the frog and toad", set())
    assert "frog and toad" in frags
    staged = {s.form.lower(): s for s in extract_fragments(dictionary)}
    assert "dunny" not in staged          # already an entry
    assert "snags" not in staged          # plural of an entry
    assert "goog" not in staged           # added from the fragment pass
    for s in staged.values():
        assert all(src.startswith("fragment-of:") for src in s.sources)


def test_harvest_pairs_plain_with_slang():
    pairs = harvest_pairs("Our fathers arrived and built a new nation.",
                          "Our old fellas rocked up and knocked together a brand-spankin'-new mob.")
    assert ("fathers arrived", "old fellas rocked up") in [(a, b) for a, b, _ in pairs]


def test_harvest_skips_what_we_have(dictionary):
    staged = harvest("It was hard work and they arrived late.",
                     "It was hard yakka and they rocked up late, ya galah, like a shag on a rock.",
                     dictionary, "harvest:test")
    forms = [s.form for s in staged]
    assert "hard yakka" not in forms and "rocked up" not in forms
    assert any("shag on a rock" in f for f in forms)
    assert all(s.sources == ["harvest:test"] for s in staged)


def test_new_entries_from_fragments_and_harvest(translator):
    def outs(text, level=4, n=15, **kw):
        return {translator.translate(text, level=level, seed=s, **kw).text for s in range(n)}
    assert any("Righto" in o for o in outs("Okay, I'll grab a bottle of beer.", level=3))
    assert any("stubby" in o for o in outs("Okay, I'll grab a small bottle of beer.", level=3))
    assert not any("stubby" in o or "tinnie" in o for o in outs("Okay, I'll grab a bottle of beer.", level=3))
    assert any("rocked up" in o for o in outs("They arrived at the party."))
    assert any("every bloke's as good as the next" in o for o in outs("We believe all men are created equal."))
    assert any("God bloody willing" in o for o in outs("God willing, this nation will last.", level=5))
    assert not any("God bloody willing" in o or "by crikey" in o
                   for o in outs("This nation, under God, will last.", level=5))
    assert any("brand-spankin'-new" in o for o in outs("They built a new nation.", level=5))
    assert not any("spankin" in o for o in outs("She moved to New York.", level=5)), "names are left alone"
