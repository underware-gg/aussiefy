"""Lookup recognises grammar slots and inflection without borrowing an unrelated sense."""
import pytest

from aussiefy import lookup


@pytest.mark.parametrize('query', ['give them a bell', 'give him a bell', 'give her a bell', 'give Bob a bell', 'give them a bell.', '(give them a bell)'])
def test_filled_object_slot_finds_the_telephone_sense(query, translator):
    results = lookup(query, translator=translator)['results']
    assert results and any('bell' in f for f in results[0].get('variants', []))
    assert not any(any(word in r['form'] for word in ['hiding', 'arse', 'towel']) for r in results)


def test_shouted_does_not_inflect_a_drinks_noun(translator):
    results = lookup('shouted', translator=translator)['results']
    assert not any('shout' in r['form'] for r in results)


@pytest.mark.parametrize('query,form', [('coves', 'cove'), ('chucked a sickie', 'chuck a sickie'),
                                      ('playing up', 'play up')])
def test_real_noun_and_head_verb_inflections_still_work(query, form, translator):
    assert form in [r['form'] for r in lookup(query, translator=translator)['results']]


@pytest.mark.parametrize('query,form', [
    ('drink', 'flat out like a lizard drinking'), ('bushwalk', 'bushwalking'),
    ('pull', '{subj} {be} pulling a swifty'), ('kip', "been kippin' in"),
])
def test_partial_lookup_handles_standard_and_dropped_g(query, form, dictionary):
    from aussiefy import Translator

    results = lookup(query, translator=Translator(dictionary, lookup_embedder=None), limit=100)['results']
    assert any(r['form'] == form and r['match'] == 'part of a phrase' for r in results)


def test_negated_model_meaning_needs_a_shared_anchor(translator):
    bad = {'OUT_OF_LINE', 'DANGEROUS', 'SCOUNDREL'}
    assert all(not bad.intersection(r['concepts']) for r in lookup('harmless', translator=translator)['results'])


def test_slots_cannot_cross_trailing_words(translator):
    out = lookup('give them a bell then', translator=translator)['results']
    assert all(r['match'] != 'slang term' for r in out)


def test_slot_only_custom_form_is_rejected_at_dictionary_boundary(tmp_path):
    from aussiefy import load_dictionary
    from aussiefy.schema import SchemaError

    path = tmp_path / 'slot-only.yaml'
    path.write_text('- {id: zz-slot-only, form: "{obj}", concept: [TIRED], frame: vp}\n')
    with pytest.raises(SchemaError, match='needs at least one required literal word'):
        load_dictionary([path])
