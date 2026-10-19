"""Plural address and a quantified reference to everyone are different uses of a noun phrase."""

import pytest

from aussiefy import Translator, harness, translate_changes
from aussiefy.schema import SchemaError, parse_concept

PROFILE = {'phonetic': 0, 'substitution': {'lexical': 1, 'phrase': 1, 'idiom': 1}}
OPTIONS = dict(level=5, vulgarity=3, embellishment=0, embedder='none',
               document_config={'profile': PROFILE})
REFERENTIAL = {'every-bugger', 'every-bastard', 'every-cunt', 'every-man-and-his-dog',
               'every-bloke-and-sheila'}


@pytest.mark.parametrize('text', [
    'Hi everyone, the meeting this afternoon is cancelled.',
    'Hello, everybody!', 'Thanks everyone.', 'Thank you, everyone.',
    'Good morning everyone.', 'Everyone, please sit down.', 'Please sit down, everyone.',
    'Everyone, be quiet.', 'Have a seat, everyone.',
])
def test_direct_plural_address_has_no_distributive_candidates(dictionary, text):
    tr = Translator(dictionary, lookup_embedder=None)
    for seed in range(6):
        result = tr.translate(text, seed=seed, **OPTIONS)
        record = next(r for r in result.records if 'PLURAL_ADDRESS' in r.det.concepts)
        assert record.det.noun_use == 'address'
        assert {c.entry.id for c in record.eligible} == {'youse', 'you-mob'}
        assert record.substituted and record.output.lower() in {'youse', 'you mob'}
        assert not any(phrase in result.text.lower() for phrase in ['every bugger', 'every bastard',
                                                                  'every cunt', 'every man', 'every bloke'])


@pytest.mark.parametrize('text', ['Everyone came.', 'Everyone is ready.', 'I invited everyone.',
                                  'Did you invite everyone?', 'I told everyone, then left.'])
def test_reference_keeps_distributive_meaning(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    records = [r for r in result.records if 'EVERYONE' in r.det.concepts]
    assert records
    for record in records:
        assert record.det.noun_use == 'reference'
        assert REFERENTIAL & {c.entry.id for c in record.eligible}
        assert 'you-mob' not in {c.entry.id for c in record.eligible}


@pytest.mark.parametrize('text', ['Everyone, including Sam, came.', 'Everyone!'])
def test_uncertain_detached_reference_stays_as_written(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert 'everyone' in result.text.lower()
    assert not any('PLURAL_ADDRESS' in r.det.concepts for r in result.records)


def test_friend_address_remains_available(dictionary):
    result = Translator(dictionary, lookup_embedder=None).translate('Hello friend, welcome.', **OPTIONS)
    friend = next(r for r in result.records if 'FRIEND' in r.det.concepts)
    assert any(c.entry.form == 'mate' for c in friend.eligible)


def test_plain_and_automatic_alternatives_share_address_reading(dictionary):
    tr = Translator(dictionary, lookup_embedder=None)
    source = 'Hi everyone, the meeting is cancelled.'
    result = translate_changes(source, translator=tr, **OPTIONS)
    changes = [c for c in result.changes if c['kind'] == 'substitution'
               and c.get('entry_id') in {'you-mob', 'youse'}]
    assert len(changes) == 1
    offered = {changes[0]['entry_id']} | {c['entry_id'] for c in changes[0]['alternatives'] + changes[0]['locked']}
    assert not offered & REFERENTIAL
    plan = harness.plan(source, translator=tr, **{k:v for k,v in OPTIONS.items() if k != 'embedder'})
    assert 'every bugger' not in str(plan).lower()


@pytest.mark.parametrize('bad', [None, True, [], 'vocative', 1])
def test_usage_restriction_is_validated(bad):
    with pytest.raises(SchemaError, match='noun_use'):
        parse_concept('EXAMPLE', {'noun_use': bad, 'triggers': {'np':['people']}})


@pytest.mark.parametrize('text', [
    'Everyone, come to think of it, was late.', 'Everyone, bless them, attended.',
    'Everyone, save Rob, came.', 'Everyone, come to think of it, actually was late.',
    'Everyone, save Rob, really came.', 'Everyone, bless them, arrived.',
    'Everyone, please sit down, then wait.', 'Absolutely everyone.', 'Absolutely, everyone!',
    'Hi everyone who arrived early, please sit down.', 'Hello, everyone is here.',
])
def test_parentheticals_and_quantifier_modifiers_do_not_certify_address(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert not any('PLURAL_ADDRESS' in r.det.concepts for r in result.records)
    assert 'you mob' not in result.text.lower() and 'youse' not in result.text.lower()


@pytest.mark.parametrize('bad', [None, 1, 'true', [], {}])
def test_addressee_capability_is_an_exact_boolean(bad):
    with pytest.raises(SchemaError, match='takes_addressee'):
        parse_concept('EXAMPLE', {'takes_addressee': bad, 'triggers': {'interjection':['hello']}})


@pytest.mark.parametrize('text', ['Hi Bob and everyone.', 'Hello Bob, Jane and everyone.',
                                  'Hi Bob and everyone who arrived early.',
                                  'Hi Bob and everyone, have a seat.',
                                  'Hello Bob and everyone, can you hear me?'])
def test_unresolved_coordinated_recipients_preserve_everyone(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert 'everyone' in result.text.lower()
    assert not any('EVERYONE' in r.det.concepts or 'PLURAL_ADDRESS' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('text', ['Hi Bob, everyone is here.', 'Hi Bob, I invited everyone.',
                                  'Hi Bob and Jane, everyone is here.'])
def test_recipient_list_does_not_absorb_a_following_reference_clause(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert any('EVERYONE' in r.det.concepts for r in result.records)
    assert not any('PLURAL_ADDRESS' in r.det.concepts for r in result.records)


def test_direct_entry_paraphrases_cannot_bypass_concept_usage(tmp_path):
    from aussiefy import load_dictionary
    extra = tmp_path / 'reference.yaml'
    extra.write_text('- {id: each-person-test, form: each person, concept: [EVERYONE], '
                     'frame: np, replaces: [everyone]}\n')
    tr = Translator(load_dictionary([extra]), lookup_embedder=None)
    addressed = tr.translate('Hi everyone, please sit down.', **OPTIONS)
    assert not any('EVERYONE' in r.det.concepts for r in addressed.records)
    referenced = tr.translate('Everyone came.', **OPTIONS)
    everyone = next(r for r in referenced.records if 'EVERYONE' in r.det.concepts)
    assert 'each-person-test' in {c.entry.id for c in everyone.eligible}


@pytest.mark.parametrize('text', [
    'Everyone here, please listen.', 'Please listen, everyone here.',
    'Hi dear everyone.', 'Hi absolutely everyone!',
    'Everyone who arrived early, please listen.',
])
def test_partial_qualified_recipient_keeps_an_unknown_role(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert 'everyone' in result.text.lower()
    assert not any('EVERYONE' in r.det.concepts or 'PLURAL_ADDRESS' in r.det.concepts for r in result.records)


def test_qualified_subject_with_attached_finite_predicate_remains_reference(dictionary):
    result = Translator(dictionary, lookup_embedder=None).translate('Everyone here is ready.', **OPTIONS)
    assert any('EVERYONE' in r.det.concepts for r in result.records)


@pytest.mark.parametrize('text', ['Listen everyone!', 'Hey Bob and everyone!', 'Invite everyone.',
                                  'Everyone listen up!', 'Everyone have a seat.',
                                  'Everyone put your hands up!'])
def test_unsupported_roles_stay_unknown_instead_of_assuming_reference(dictionary, text):
    result = Translator(dictionary, lookup_embedder=None).translate(text, **OPTIONS)
    assert 'everyone' in result.text.lower()
    assert not any('EVERYONE' in r.det.concepts or 'PLURAL_ADDRESS' in r.det.concepts for r in result.records)


def test_governed_object_keeps_reference_through_a_modal(dictionary):
    result = Translator(dictionary, lookup_embedder=None).translate('She will invite everyone.', **OPTIONS)
    assert any('EVERYONE' in r.det.concepts for r in result.records)
