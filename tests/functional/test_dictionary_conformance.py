"""Cross-surface invariants from the community dictionary design conformance review."""

from dataclasses import replace
from time import perf_counter

import pytest
import yaml

from aussiefy import Translator, bulldust, harness, load_dictionary, translate, translate_changes
from aussiefy.constructions import construction_matches
from aussiefy.evidence import Source, TermMetadata, Testimony as EvidenceTestimony, assess
from aussiefy.masks import profanity_rating
from aussiefy.semantic_checks import theme_issues


@pytest.mark.parametrize("kind", ["scholarly_dictionary", "slang_dictionary", "crowd_dictionary", "media", "testimony"])
def test_community_attribution_keeps_effective_evidence_counts(dictionary, kind):
    source = Source(kind, "An independent work", ("term",), url=None if kind == "testimony" else "https://example.org/word")
    summary = EvidenceTestimony(1, 1, 0, "2026-10-19", "2026-10-19", "2026-10-22") if kind == "testimony" else None
    term = TermMetadata(sources=(source,), testimony=summary)
    baseline = assess(term, dictionary.evidence_weights)
    community = replace(source, kind="community", basis=kind)
    wrapped = replace(term, sources=(community,))
    assert assess(wrapped, dictionary.evidence_weights) == baseline
    assert dict(baseline.attestation.counts) == {kind: 1}
    assert wrapped.sources[0].to_dict()["kind"] == "community"
    assert assess(replace(term, sources=(source, community)), dictionary.evidence_weights) == baseline


def test_rob_stem_confirmation_is_scoped_testimony_not_an_attested_label(dictionary):
    entry = dictionary.entries["bugger-me-sideways"]
    summary = entry.testimony
    assert (summary.people, summary.independent, summary.places) == (1, 1, 0)
    assert summary.first_date == summary.last_date == "2026-10-19"
    assert entry.evidence == "unverified"
    assert entry.attestation.score > assess(replace(entry, testimony=None), dictionary.evidence_weights).attestation.score
    assert any(s.kind == "testimony" and s.supports == ("australian_use",) for s in entry.sources)
    assert dictionary.entries["fuck-me-sideways"].testimony is None


def _catalogue(data_copy, *, template="{state} enough to {act}", slots=None, acts=None):
    raw = yaml.safe_load((data_copy / "constructions.yaml").read_text())
    raw["families"] = [next(row for row in raw["families"] if row["id"] == "hungry-enough-to")]
    raw["families"][0].update(template=template, slots=slots or {"state": "hunger-state", "act": "absurd-food-act"})
    if acts is not None:
        raw["ingredients"] = acts
    else:
        raw["ingredients"] = [{"id": "hungry", "kind": "hunger-state", "text": "hungry"},
                              {"id": "act", "kind": "absurd-food-act", "text": "eat like a fuckwit"}]
    (data_copy / "constructions.yaml").write_text(yaml.safe_dump(raw))
    return Translator(load_dictionary(data_dir=data_copy))


def test_literal_constructor_uses_known_compound_ratings(data_copy):
    tr = _catalogue(data_copy)
    assert not bulldust("HUNGRY", vulgarity=0, translator=tr)["results"]
    result = bulldust("HUNGRY", vulgarity=2, translator=tr)["results"][0]
    assert result["text"] == "hungry enough to eat like a fuckwit" and result["vulgarity"] == 2


def test_constructor_rates_new_words_formed_at_part_boundaries(data_copy):
    tr = _catalogue(data_copy, template="hungry enough to say {left}{right}", slots={"left": "left", "right": "right"},
                    acts=[{"id": "left", "kind": "left", "text": "fu"},
                          {"id": "right", "kind": "right", "text": "ck"}])
    assert not bulldust("HUNGRY", vulgarity=0, translator=tr)["results"]
    result = bulldust("HUNGRY", vulgarity=2, translator=tr)["results"][0]
    assert result["text"] == "hungry enough to say fuck" and result["vulgarity"] == 2


def test_template_identifiers_are_not_spoken_words(data_copy):
    tr = _catalogue(data_copy, template="hungry enough to {fuck}", slots={"fuck": "act"},
                    acts=[{"id": "act", "kind": "act", "text": "eat a plain biscuit"}])
    result = bulldust("HUNGRY", vulgarity=0, translator=tr)["results"][0]
    assert result["text"] == "hungry enough to eat a plain biscuit" and result["vulgarity"] == 0


def test_constructor_rating_preserves_curated_whole_expressions_and_ordinary_substrings(dictionary, data_copy):
    for text in ("bloody hell", "Bloody hell", "BLOODY HELL"):
        assert profanity_rating(text, dictionary) == dictionary.entries["g-bloody-hell"].vulgarity == 0
    assert profanity_rating("cocktail in Scunthorpe with a cocky", dictionary) == 0
    tr = _catalogue(data_copy, template="{stem}, {act}", slots={"stem": "oath", "act": "act"},
                    acts=[{"id": "oath", "kind": "oath", "entry_id": "g-bloody-hell"},
                          {"id": "act", "kind": "act", "text": "hungry enough to eat a plain biscuit"}])
    result = bulldust("HUNGRY", vulgarity=0, translator=tr)["results"][0]
    assert result["vulgarity"] == 0 and result["parts"][0]["entry_id"] == "g-bloody-hell"


@pytest.mark.parametrize("wording,theme", [
    ("Bugger me sideways with a broomstick.", "sex"),
    ("Bugger me sideways'n call me the pope.", "religion"),
])
def test_reviewed_composites_share_lint_and_rewriter_theme_policy(translator, wording, theme):
    dad = translator.effective(vulgarity=1).theme_policy
    issues = theme_issues(wording, "Wow.", translator.dictionary, dad)
    assert len(issues) == 1 and issues[0]["themes"] == [theme]
    assert not theme_issues(wording, wording, translator.dictionary, dad)
    assert len(theme_issues(wording + " " + wording, wording, translator.dictionary, dad)) == 1
    assert not theme_issues("Bugger me sideways.", "Wow.", translator.dictionary, dad)
    allowed = translator.effective(vulgarity=1, document_config={"themes": {theme: True}}).theme_policy
    assert not theme_issues(wording, "Wow.", translator.dictionary, allowed)
    lint = harness.lint(wording, original="Wow.", vulgarity=1, suggest=False, translator=translator)
    assert any(issue["kind"] == "theme" for issue in lint["issues"])

    class Rewriter:
        model = "scripted"

        def rewrite(self, original, draft, planned, *, level, vulgarity, seed):
            return wording, "returned"

    source = "The river flows through the valley."
    result = translator.translate(source, vulgarity=1, rewriter=Rewriter(), rewrite_mode="all")
    assert result.rewrites[0].output is None and "forbidden themes" in result.rewrites[0].status
    permitted = translator.translate(source, vulgarity=1, rewriter=Rewriter(), rewrite_mode="all",
                                     document_config={"themes": {theme: True}})
    assert permitted.rewrites[0].output == wording


def _registered(translator, register, kind, allowed):
    d = translator.dictionary
    profiles = {**d.profiles, 5: replace(d.profiles[5], registers=allowed)}
    if kind == "riff":
        e = d.entries["wheelie-bin"]
        riff = replace(e.riffs[0], register=register)
        d = replace(d, entries={**d.entries, e.id: replace(e, riffs=(riff,))}, imagery=(), profiles=profiles)
        return Translator(d), "We put out the wheeled rubbish bins.", "wheelie bin", riff.text
    image = replace(next(i for i in d.imagery if i.id == "sandstorm-sweeper"), register=register)
    d = replace(d, imagery=(image,), profiles=profiles)
    return Translator(d), "He was working in vain.", "working in vain", image.text


@pytest.mark.parametrize("register", ["dated", "archaic"])
@pytest.mark.parametrize("kind", ["riff", "image"])
@pytest.mark.parametrize("mode", ["translate", "markdown", "plan", "changes", "lookup"])
def test_resolved_register_filter_reaches_selection_offers_and_cards(translator, register, kind, mode):
    config = {"garnish": ["riff"], "entry_riffs": kind == "riff", "contextual_riffs": kind == "image",
              "riff_exaggeration": 2, "profile": {"garnish": {"riff": 1}, "max_garnish": {"riff": 1}, "phonetic": 0}}
    observed = []
    for allowed in (("current",), ("current", register)):
        tr, source, query, image = _registered(translator, register, kind, allowed)
        opts = {"translator": tr, "vulgarity": 0, "document_type": "custom", "document_config": config}
        if mode == "lookup":
            result = harness.lookup(query, **opts)
            texts = ([r["text"] for card in result["results"] for r in card.get("riffs", [])] if kind == "riff" else
                     [i["text"] for i in result.get("imagery", [])])
        elif mode == "plan":
            result = harness.plan(source, registers=list(allowed), **opts)
            texts = [r["text"] for group in result["riffs"] for r in group["riffs"]]
        elif mode == "changes":
            result = translate_changes(source, registers=list(allowed), **opts)
            texts = ([r["text"] for card in result.entries.values() for r in card.get("riffs", [])] if kind == "riff" else
                     [g.text for g in result.result.garnish if g.image_id])
        else:
            result = translate(source, registers=list(allowed), markdown=mode == "markdown", **opts)
            texts = [result.text]
        observed.append(any(image in text for text in texts))
    assert observed == [False, True]


@pytest.mark.parametrize("left", [
    [{"id": "long", "kind": "left", "text": "foo", "themes": ["sex"]},
     {"id": "short", "kind": "left", "text": "fo"}],
    [{"id": "long", "kind": "left", "text": "foo"},
     {"id": "short", "kind": "left", "text": "fo", "themes": ["sex"]}],
])
def test_composite_recognition_keeps_any_allowed_slot_partition(data_copy, left):
    tr = _catalogue(data_copy, template="{left}{right}", slots={"left": "left", "right": "right"}, acts=left + [
        {"id": "right-short", "kind": "right", "text": "bar"},
        {"id": "right-long", "kind": "right", "text": "obar"}])
    policy = tr.effective(vulgarity=0).theme_policy
    readings = list(construction_matches("foobar", tr.dictionary, policy))
    assert readings and not theme_issues("foobar", "", tr.dictionary, policy)
    assert not readings[0][2].themes


@pytest.mark.parametrize("letter", ["İ", "ı", "ſ"])
def test_composite_recognition_preserves_unicode_offsets_without_case_key_lookups(translator, letter):
    word = "Bugger me sideways".replace("i" if letter != "ſ" else "s", letter, 1)
    text = "🦘 " + word + " with a broomstick."
    issues = theme_issues(text, "", translator.dictionary, translator.effective(vulgarity=1).theme_policy)
    assert len(issues) == 1 and issues[0]["phrase"] == text[2:-1] and issues[0]["themes"] == ["sex"]


def test_composite_recognition_does_not_expand_overlapping_cartesian_pools(data_copy):
    slots = {f"part{i}": "prefix" for i in range(8)}
    tr = _catalogue(data_copy, template="".join("{" + name + "}" for name in slots) + "X", slots=slots,
                    acts=[{"id": f"prefix-{i}", "kind": "prefix", "text": "a" * i} for i in range(1, 21)])
    policy = tr.effective(vulgarity=0).theme_policy
    started = perf_counter()
    assert not list(construction_matches("a" * 60 + "Y", tr.dictionary, policy))
    matches = list(construction_matches("a" * 60 + "X", tr.dictionary, policy))
    assert [(a, b) for a, b, _ in matches] == [(0, 61)]
    assert perf_counter() - started < 2  # Generous bound: 20**8 full combinations are never visited.


@pytest.mark.parametrize("left,right", [("foo ", "bar"), ("foo", " bar"), ("foo ", " bar ")])
def test_composite_recognition_preserves_authored_whitespace_at_joins(data_copy, left, right):
    tr = _catalogue(data_copy, template="{left} {right}", slots={"left": "left", "right": "right"}, acts=[
        {"id": "left", "kind": "left", "text": left, "themes": ["sex"]},
        {"id": "right", "kind": "right", "text": right}])
    text = left + " " + right
    issues = theme_issues(text, "", tr.dictionary, tr.effective(vulgarity=0).theme_policy)
    assert issues and max(len(issue["phrase"]) for issue in issues) == len(text)
