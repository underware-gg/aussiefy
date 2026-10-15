"""Reproduced lint and phrase-location failures, plus document-form guard coverage."""
from types import SimpleNamespace

import pytest

from aussiefy import harness, load_dictionary
from aussiefy.align import counterparts
from aussiefy.lint import _derived_from, _phrase_words
from aussiefy.schema import SchemaError
from aussiefy.yarn import _moved


def test_adjacent_reuse_does_not_move_a_phrase():
    source = 'The guide will examine the power supply before the system test.'
    session = SimpleNamespace(text=source, markup='text', plan={'planned': [
        {'aussie': 'have a look at', 'original': 'examine', 'span': [source.index('examine'), 22]}]})
    correct = ('The guide will have a look at the power supply before lunch. '
               'Examine the guide beside the system. Test the power supply before departure.')
    assert _moved(session, correct, ['have a look at']) == []
    moved = source + ' Have a look at the lunch menu.'
    assert _moved(session, moved, ['have a look at']) == [('have a look at', 'examine')]


def test_alignment_prefers_expected_position_when_words_tie():
    found = counterparts(['same words', 'same words'], ['same words', 'same words'], max_sentences=1)
    assert [(c.start, c.end) for c in found] == [(0, 1), (1, 2)]
    # Verification still permits a source sentence to become several sentences.
    assert counterparts(['alpha beta gamma delta'], ['alpha beta', 'gamma delta'])[0].end == 2


@pytest.mark.parametrize('drawled,plain', [
    ('I wanna leave.', 'I want to leave.'), ('We gotta leave.', 'We got to leave.'),
    ("I 'ave it.", 'I have it.'), ('I dunno why.', 'I do not know why.'),
    ("Left 'cause rain.", 'Left because rain.'), ("It prob’ly works.", 'It probably works.'),
    ("bread’n butter", 'bread and butter'), ('We oughta leave.', 'We ought to leave.'),
    ('Outta the place.', 'Out of the place.'), ("Straya has a lotta trees.", 'Australia has a lot of trees.'),
])
def test_refrain_comparison_reads_dictionary_drawl(drawled, plain, dictionary):
    assert _phrase_words(drawled, dictionary.drawl_readings) == _phrase_words(plain, dictionary.drawl_readings)


def test_custom_drawl_annotation_is_used(data_copy):
    path = data_copy / 'phonetic.yaml'
    path.write_text(path.read_text() + '\n- {id: zz-test, match: "business", replace: bizz, reads_as: business}\n')
    d = load_dictionary(data_dir=data_copy)
    assert _phrase_words('The bizz is open.', d.drawl_readings) == [['the', 'business', 'is', 'open']]


@pytest.mark.parametrize('replacement,reading', [(r'\1in', 'going'), ('word', False), ('word', 'NOT words'), ('word', '')])
def test_invalid_drawl_reading_fails_at_load(data_copy, replacement, reading):
    import yaml
    path = data_copy / 'phonetic.yaml'
    path.write_text(path.read_text() + yaml.safe_dump([{'id': 'zz-test', 'match': '(going)',
                                                        'replace': replacement, 'reads_as': reading}]))
    with pytest.raises(SchemaError, match='reads_as'):
        load_dictionary(data_dir=data_copy)


@pytest.mark.parametrize('original,draft', [
    ('The President, George Washington, spoke today.', 'President George Washington spoke today.'),
    ('We decorated Christmas Trees.', 'We decorated Chrissy trees.'),
])
def test_retained_names_and_known_dictionary_words(original, draft, translator):
    assert not [w for w in harness.fidelity(draft, original, translator=translator) if w['kind'].startswith('name_')]


def test_a_dictionary_swap_does_not_excuse_another_name(translator):
    warnings = harness.fidelity('We decorated Chrissy trees with George.',
                                'We decorated Christmas Trees with Washington.', translator=translator)
    assert ('name_dropped', 'Washington') in {(w['kind'], w['phrase']) for w in warnings}
    assert ('name_added', 'George') in {(w['kind'], w['phrase']) for w in warnings}


@pytest.mark.parametrize('name,base,want', [('Colombian','Colombia',True), ('Japanese','Japan',True),
    ('New Englanders','New England',True), ('Smithers','Smith',False), ('Theodore','Then',False)])
def test_name_derivation_is_bounded(name, base, want):
    assert _derived_from(name, {base}) is want


@pytest.mark.parametrize('document_type', ['news','instructions','technical','official'])
@pytest.mark.parametrize('embellishment', ['deadset','dinkum'])
def test_every_strict_preset_disables_swear_infixes(document_type, embellishment, translator):
    text = "This is a very good seal. Every single time it works. It is too hot. You can't use it."
    for seed in range(3):
        result = translator.translate(text, level=5, vulgarity=3, seed=seed,
                                      document_type=document_type, embellishment=embellishment)
        assert not result.embellishment.takes('infix')
        assert not [p for p in result.phonetic if p.rule.startswith('infix') or p.rule == 'as-fuck-intensifier']


@pytest.mark.parametrize('original,draft', [
    ('We met John Woods today.', 'We met John bush today.'),
    ('We met George Farmer today.', 'We met George cocky today.'),
    ('We met Bill Woods today.', 'We met Bill bush today.'),
])
def test_a_common_noun_inside_a_persons_name_is_no_dictionary_alias(original, draft, translator):
    assert [w for w in harness.fidelity(draft, original, translator=translator) if w['kind'] == 'name_dropped']


def test_capitalised_place_name_is_not_an_inferred_alias(translator):
    assert any(w['kind'] == 'name_dropped' for w in harness.fidelity(
        'We visited Chrissy island.', 'We visited Christmas Island.', translator=translator))


def test_drawl_comparison_folds_custom_replacement_spacing(data_copy):
    path = data_copy / 'phonetic.yaml'
    path.write_text(path.read_text() + "\n- {id: zz-space, match: 'a business', replace: 'a  bizz', reads_as: 'a business'}\n")
    d = load_dictionary(data_dir=data_copy)
    assert _phrase_words('A  bizz works.', d.drawl_readings) == [['a', 'business', 'works']]


def test_conflicting_drawl_annotations_are_rejected(data_copy):
    path = data_copy / 'phonetic.yaml'
    path.write_text(path.read_text() + "\n- {id: zz-conflict, match: you, replace: ya, reads_as: something}\n")
    with pytest.raises(SchemaError, match='reads_as conflicts'):
        load_dictionary(data_dir=data_copy)



@pytest.mark.parametrize('row', ['null', '42', 'word'])
def test_malformed_phonetic_rows_report_schema_errors(data_copy, row):
    path = data_copy / 'phonetic.yaml'
    path.write_text(path.read_text() + '\n- ' + row + '\n')
    with pytest.raises(SchemaError, match='expected a mapping'):
        load_dictionary(data_dir=data_copy)
