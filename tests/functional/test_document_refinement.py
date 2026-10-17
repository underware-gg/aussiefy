"""Isolate grammar, placement and technical-fidelity failures found in published documentation."""

from dataclasses import replace

import pytest

from aussiefy import Translator, translate
from aussiefy.loader import load_dictionary
from aussiefy.schema import SchemaError


def loud_config(placements=("opener",)):
    return {"garnish": list(placements), "profile": {"garnish": {p: 1 for p in placements},
            "max_garnish": {p: 10 for p in placements}, "garnish_gap": 0}}


@pytest.mark.parametrize("source", [
    "You must use `dev` for changes.\n",
    "This is the **main** branch.\n",
    "You can read the [guide](https://example.org) for details.\n",
    "You can read this sentence\nand keep its meaning.\n",
])
def test_safe_source_start_can_take_one_opener_before_an_inline_boundary(source, translator):
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config())
    placed = [(i, g) for i, unit in enumerate(r.units) for g in unit.result.garnish if g.entry_id]
    assert len(placed) == 1 and placed[0][0] == 0
    assert all(source[slice(*p.source_span)] == r.text[slice(*p.output_span)] for p in r.protected)


def test_prefix_placement_uses_the_complete_sentence_context(translator):
    source = "This `setting` is useful.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config())
    # The local prefix is one word, so the conservative minimum still applies.
    assert not [g for u in r.units for g in u.result.garnish if g.entry_id]
    source = "The main `setting` is useful.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config())
    assert len([g for u in r.units for g in u.result.garnish if g.entry_id]) == 1


def test_no_suffix_or_riff_can_land_before_a_protected_inline_span(translator):
    source = "You must use `dev` for changes.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config(("opener", "tag", "tail", "riff")))
    placements = [g.placement for unit in r.units for g in unit.result.garnish if g.entry_id]
    assert placements == ["opener"]
    assert not any(x.riff for u in r.units for x in u.result.records)


@pytest.mark.parametrize("source", [
    "# You must use `dev` for changes\n",
    "- You must use `dev` for changes.\n",
    "| You must use `dev` for changes. |\n|---|\n",
    '"You must use `dev` for changes."\n',
])
def test_structural_and_quote_protection_still_exclude_prefix_garnish(source, translator):
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config={**loud_config(), "keep_quotes": True})
    assert not [g for u in r.units for g in u.result.garnish if g.entry_id]


def test_word_case_context_is_shared_across_markdown_units(translator):
    source = "The level stays the same.\n\nLevel and vulgarity are independent.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config())
    assert ", Level" not in r.text and ", level" in r.text


def test_source_start_proper_names_and_acronyms_keep_their_case(translator):
    source = "Smith is using `dev` for changes.\n\nAPI is the name of this `module`.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config())
    assert "Smith" in r.text and "API" in r.text
    assert ", smith" not in r.text and ", api" not in r.text


@pytest.mark.parametrize("source", ["See how hard it is to follow.", "I know how very difficult it is to use."])
def test_fronted_how_predicate_keeps_its_stressed_be(source, translator):
    rule = next(r for r in translator.dictionary.phonetic if r.id == "pronoun-be")
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    r = tr.translate(source, document_type="custom", document_config={"profile": {"frames": [], "phonetic": 1}})
    assert "it is" in r.text and "it's" not in r.text


@pytest.mark.parametrize("source,expected", [("It is to be expected.", "It's to be expected."),
    ("It is difficult to use.", "It's difficult to use."), ("She is ready.", "She's ready.")])
def test_ordinary_be_contractions_still_work(source, expected, translator):
    rule = next(r for r in translator.dictionary.phonetic if r.id == "pronoun-be")
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    r = tr.translate(source, document_type="custom", document_config={"profile": {"frames": [], "phonetic": 1}})
    assert r.text == expected


@pytest.mark.parametrize("bad", [False, "", "["])
def test_phonetic_context_guard_is_validated_at_load_boundary(data_copy, bad):
    import yaml
    p = data_copy / "phonetic.yaml"
    p.write_text(p.read_text() + yaml.safe_dump([{"id": "bad-context", "match": "it is", "replace": "it's",
                                                "unless_before": bad}]))
    with pytest.raises(SchemaError, match="phonetic rule"):
        load_dictionary(data_dir=data_copy)


def test_everything_relative_clause_keeps_its_pronoun_but_whole_lot_can_swap(translator):
    r = translator.translate("Everything a level does is read from data.", document_type="custom")
    assert not any(x.substituted and "EVERYTHING" in x.det.concepts for x in r.records)
    r = translator.translate("I packed everything.", document_type="custom")
    assert any(x.substituted and "EVERYTHING" in x.det.concepts for x in r.records)


def test_technical_liberty_is_not_a_fair_go(translator):
    r = translator.translate("The dial controls liberty in the telling.", document_type="custom",
                             document_config={"term_domains": ["technical"]})
    assert "liberty" in r.text and "fair go" not in r.text


@pytest.mark.parametrize("source", ["Releases are on main.", "Optional heavy dependencies load lazily.",
    "Strict Markdown preserves syntax.", "Existing files stay intact.", "Ingesting a source requires a licence."])
def test_uncertain_first_word_case_does_not_make_an_awkward_prefix(source, translator):
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config=loud_config(("opener", "connective")))
    first = source.split()[0]
    assert ", " + first not in r.text


@pytest.mark.parametrize("source", ["Relative links point to other pages.", "A relative link points to another page."])
def test_relative_links_do_not_become_family_members(source, translator):
    r = translator.translate(source, document_type="custom")
    assert "rello" not in r.text and "relative" in r.text.lower()


def test_family_member_sense_of_relative_still_translates(translator):
    r = translator.translate("I met a relative.", document_type="custom")
    assert any(x.substituted and "RELATIVES" in x.det.concepts for x in r.records)


@pytest.mark.parametrize("source,contracted", [
    ("I know how tired you are today.", "you're"),
    ("I know how busy I am today.", "I'm"),
    ("We know where it is now.", "it's"),
    ("I know who she is today.", "she's"),
    ("I know what it is now.", "it's"),
    ("They are as strong as we are today.", "we're"),
    ("They look taller than we are now.", "we're"),
])
def test_fronted_predicate_corpus_preserves_stressed_be(source, contracted, translator):
    rules = [r for r in translator.dictionary.phonetic if r.id in ("pronoun-be", "pronoun-are", "i-am")]
    tr = Translator(replace(translator.dictionary, phonetic=rules))
    r = tr.translate(source, document_type="custom", document_config={"profile": {"frames": [], "phonetic": 1}})
    assert contracted not in r.text


@pytest.mark.parametrize("source,expected", [("We are ready.", "We're ready."),
    ("I am ready.", "I'm ready."), ("They are working.", "They're working."),
    ("She is running.", "She's running.")])
def test_unfronted_auxiliary_and_predicate_contractions_remain_available(source, expected, translator):
    rules = [r for r in translator.dictionary.phonetic if r.id in ("pronoun-be", "pronoun-are", "i-am")]
    tr = Translator(replace(translator.dictionary, phonetic=rules))
    assert tr.translate(source, document_type="custom", document_config={"profile": {"frames": [], "phonetic": 1}}).text == expected


@pytest.mark.parametrize("source", ["The browser uses cookies.", "The build succeeds.",
    "The river runs through the valley.", "When the browser fails, the engine reports an error.",
    "The package failed.", "Before the package fails, the engine reports an error.",
    "After the browser uses cookies, the package works.", "Until the package fails, the package works."])
def test_finite_present_declaratives_are_not_fragments(source):
    from aussiefy.context import sentence_contexts
    from aussiefy.text import tokenize
    assert "fragment" not in sentence_contexts(tokenize(source))


@pytest.mark.parametrize("source", ["Release notes", "Cookie settings", "Reading source files", "To use the package",
    "Red fields", "A build that passes validation", "If the build succeeds", "Failed builds",
    "The code for checking whether builds fail.", "The logs showing whether a package succeeds.",
    "Until the package fails.", "Before the package fails.", "After the browser uses cookies."])
def test_noun_gerund_infinitive_and_subordinate_fragments_stay_fragments(source):
    from aussiefy.context import sentence_contexts
    from aussiefy.text import tokenize
    assert "fragment" in sentence_contexts(tokenize(source))


def test_present_tense_source_context_enables_safe_colour_around_code(translator):
    source = "The browser uses `cookies` to retain state.\n"
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type="custom",
                  document_config={**loud_config(), "term_domains": ["technical"]})
    assert len([g for u in r.units for g in u.result.garnish if g.entry_id]) == 1
    assert "browser uses `cookies` to retain state" in r.text


@pytest.mark.parametrize('source', [
    "Doesn't my suit fit me marvellously?",
    "Can't the new server start?",
    "Didn't Mr. Smith finish?",
    "Won't the U.S. team win?",
])
def test_negative_questions_do_not_split_the_auxiliary_from_its_subject(source, translator):
    rule = replace(next(r for r in translator.dictionary.phonetic if r.id == 'infix-bloody-well'), prob=1)
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    r = tr.translate(source, vulgarity=1, document_type='custom', document_config={
        'garnish': ['infix'], 'profile': {'frames': [], 'swearing': {'infix': 1}}})
    assert r.text == source and not r.phonetic


@pytest.mark.parametrize('source,expected', [
    ("He won't go. Doesn't my suit fit?", "He won't bloody well go. Doesn't my suit fit?"),
    ("He doesn't enjoy this.", "He doesn't bloody well enjoy this."),
    ("Don't touch the wires.", "Don't bloody well touch the wires."),
])
def test_question_guard_leaves_statements_and_imperatives_available(source, expected, translator):
    rule = replace(next(r for r in translator.dictionary.phonetic if r.id == 'infix-bloody-well'), prob=1)
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    r = tr.translate(source, vulgarity=1, document_type='custom', document_config={
        'garnish': ['infix'], 'profile': {'frames': [], 'swearing': {'infix': 1}}})
    assert r.text == expected


def test_other_grammatical_question_infixes_remain_available(translator):
    rule = replace(next(r for r in translator.dictionary.phonetic if r.id == 'as-fuck-intensifier'), prob=1)
    tr = Translator(replace(translator.dictionary, phonetic=[rule]))
    r = tr.translate('Is that very good?', vulgarity=2, document_type='custom', document_config={
        'garnish': ['infix'], 'profile': {'frames': [], 'swearing': {'infix': 1}}})
    assert r.text == 'Is that good as fuck?'


@pytest.mark.parametrize('bad', ['true', 1, None, []])
def test_question_guard_requires_a_real_boolean(data_copy, bad):
    import yaml
    p = data_copy / 'phonetic.yaml'
    p.write_text(p.read_text() + yaml.safe_dump([{
        'id': 'bad-question', 'match': 'word', 'replace': 'word', 'unless_question': bad}]))
    with pytest.raises(SchemaError, match='unless_question must be a boolean'):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize('word', ['Australian', 'English', 'French', 'Python'])
def test_prefixes_cannot_lower_a_capital_only_because_it_is_dictionary_plain_text(word, translator):
    source = f'{word} spelling is enabled.\n'
    r = translate(source, markdown=True, translator=translator, vulgarity=0, document_type='custom',
                  document_config=loud_config())
    assert word in r.text and f', {word.lower()}' not in r.text
    # With no lower-case evidence, the existing conservative placement rule declines the prefix.
    assert not [g for u in r.units for g in u.result.garnish if g.entry_id]


@pytest.mark.parametrize('source,lowered', [
    ('Residents said the river rose.\n', 'residents'),
    ('Cook the beans before serving.\n', 'cook'),
])
def test_ordinary_words_and_explicit_commands_can_still_take_prefixes(source, lowered, translator):
    r = translate('We waited. ' + source, markdown=True, translator=translator, vulgarity=0, document_type='custom',
                  document_config={**loud_config(('connective',)), 'command_context': True})
    assert f', {lowered}' in r.text


def test_declining_a_question_does_not_shift_a_later_statements_roll(translator):
    rule = next(r for r in translator.dictionary.phonetic if r.id == 'infix-bloody-well')
    guarded = Translator(replace(translator.dictionary, phonetic=[rule]))
    unguarded = Translator(replace(translator.dictionary, phonetic=[replace(rule, unless_question=False)]))
    source = "Doesn't my suit fit? He won't go."
    config = {'garnish': ['infix'], 'profile': {'frames': [], 'swearing': {'infix': 1}}}
    for seed in range(10):
        outputs = [tr.translate(source, seed=seed, vulgarity=1, document_type='custom',
                                document_config=config).text for tr in (guarded, unguarded)]
        assert outputs[0].split('?')[1] == outputs[1].split('?')[1]


@pytest.mark.parametrize('closing', ['"', '”', '’', '”)'])
@pytest.mark.parametrize('punctuation', ['?', '!', '.'])
def test_continued_dialogue_tag_precedes_terminal_punctuation_and_closers(closing, punctuation):
    from aussiefy.garnish import tag_edit
    source = f'Are you ready{punctuation}{closing}  '
    assert tag_edit(source, 'mate')[0] == f'Are you ready, mate{punctuation}{closing}  '


def test_continued_curly_dialogue_keeps_its_tag_inside_the_quote(translator):
    from aussiefy.schema import Entry
    entry = Entry('test-tag', 'mate', (), 'interjection', type='garnish', placement='tag',
                  when=('question',))
    tr = Translator(replace(translator.dictionary, entries={
        **{e.id: e for e in translator.dictionary.entries.values() if e.type != 'garnish'}, entry.id: entry},
        phonetic=[]))
    r = tr.translate('She asked, “We waited.\n\nAre you ready?”', vulgarity=0, document_type='custom',
                     document_config=loud_config(('tag',)))
    assert 'Are you ready, mate?”' in r.text
    assert '?”, mate' not in r.text


@pytest.mark.parametrize('lowercase_evidence', [False, True])
def test_plain_word_inventory_preserves_source_case_and_lowercase_inflections(dictionary, lowercase_evidence):
    from aussiefy.matcher import compile_pattern
    from aussiefy.schema import Concept
    triggers = {'np': ('English person', 'quuxwidget'), 'vp': ('arrive',)}
    concept = Concept('CASE', 'An english alias.' if lowercase_evidence else 'A neutral description.', triggers)
    patterns = [compile_pattern(text, frame, ('CASE',), 1) for frame, texts in triggers.items() for text in texts]
    d = replace(dictionary, entries={}, concepts={'CASE': concept}, patterns=patterns)
    assert {'person', 'quuxwidget', 'quuxwidgets', 'arrive', 'arrived'} <= d.plain_words
    assert ('english' in d.plain_words) == lowercase_evidence
