"""Construction fallback shares ordinary fit/realisation; public activation is coordinated with v3."""

from dataclasses import replace

import pytest

from aussiefy import Translator
from aussiefy.markup import mask


@pytest.fixture
def no_hunger_words(dictionary):
    # Keep dictionary recognition/evidence intact, but make all curated replacements unavailable.
    entries={key: replace(e,status='omit') if 'HUNGRY' in e.concept else e
             for key,e in dictionary.entries.items()}
    return replace(dictionary,entries=entries)


def run(dictionary,text='She is hungry.',**options):
    config={'garnish':[],'contextual_riffs':False,'profile':{'substitution':{'idiom':1},'stack':0}}
    options.setdefault('invention',False)
    return Translator(dictionary,lookup_embedder=None).translate(text,level=5,vulgarity=0,
        embellishment=2,english='none',embedder='none',document_config=config,**options)


def test_fallback_is_explicit_and_carries_constructor_and_part_provenance(no_hunger_words):
    original=run(no_hunger_words)
    made=run(no_hunger_words,invention=True)
    assert not any(r.substituted for r in original.records)
    record=next(r for r in made.records if r.chosen)
    construction=record.chosen.construction
    assert construction and construction.text in record.output
    assert construction.metadata.evidence=='bulldust' and construction.metadata.coined_by=='constructor'
    assert all(p.ingredient.metadata.evidence for p in construction.parts)
    serial=record.to_dict()
    assert serial['chosen']['entry'] is None
    assert serial['chosen']['construction']['construction_id']==construction.id
    assert all(c['entry'] is None and c['construction_id'] for c in serial['candidates'])


def test_curated_candidates_and_failed_rolls_never_try_construction(dictionary,monkeypatch):
    import aussiefy.engine as engine
    original_roll=engine.roll
    def no_generation(*args,**kwargs):
        raise AssertionError('construction must not be tried while a curated candidate fits')
    monkeypatch.setattr(engine,'generate',no_generation)
    monkeypatch.setattr(engine,'roll',lambda seed,kind,*args: 1 if kind=='substitute' else original_roll(seed,kind,*args))
    result=run(dictionary,invention=True)
    assert result.records and all(not r.chosen for r in result.records)
    assert any('roll' in r.decision for r in result.records)


@pytest.mark.parametrize('source',['She is hungry enough to eat a horse.',
                                  'She is so hungry that she could cry.',
                                  'She is too hungry to wait.',
                                  'The hungry visitors arrived.'])
def test_constructions_respect_dependent_results_and_frames(no_hunger_words,source):
    result=run(no_hunger_words,source,invention=True)
    assert not any(r.chosen and r.chosen.construction for r in result.records)


def test_opaque_markup_cannot_trigger_invention(no_hunger_words,monkeypatch):
    import aussiefy.engine as engine
    def no_generation(*args,**kwargs):
        raise AssertionError('an opaque span cannot trigger construction')
    monkeypatch.setattr(engine,'generate',no_generation)
    source='`She is hungry.`'
    result=run(no_hunger_words,source,invention=True,_protected=mask(source,'markdown'))
    assert result.text==source


def test_construction_text_is_opaque_to_template_slot_filling(no_hunger_words):
    catalog=no_hunger_words.construction_catalog
    catalog=replace(catalog,ingredients=tuple(replace(p,text=p.text+' {literal}')
        if p.kind=='absurd-food-act' else p for p in catalog.ingredients))
    result=run(replace(no_hunger_words,construction_catalog=catalog),invention=True)
    record=next(r for r in result.records if r.chosen and r.chosen.construction)
    assert '{literal}' in record.output


def test_generation_and_usage_repeat_for_the_same_request(no_hunger_words):
    source='She is hungry and he is hungry.'
    a=run(no_hunger_words,source,invention=True)
    b=run(no_hunger_words,source,invention=True)
    assert a.to_dict()==b.to_dict()
    choices=[r.chosen.construction.id for r in a.records if r.chosen and r.chosen.construction]
    assert len(choices)==2 and len(set(choices))==2


def test_real_fallback_graph_tracks_phonetic_part_edits(no_hunger_words):
    import json
    from jsonschema import Draft202012Validator
    from aussiefy import translate_changes
    from aussiefy.changes import SCHEMA
    from aussiefy.v3_contract import validate_response
    from aussiefy.constructions import Ingredient, template_fragments
    catalog = no_hunger_words.construction_catalog
    family = next(f for f in catalog.families if f.id == 'hungry-enough-to')
    slots = (*family.slots, ('address', 'fixture-address'))
    template = family.template + ', {address}'
    family = replace(family, slots=slots, template=template, fragments=template_fragments(template, slots))
    catalog = replace(catalog, families=(family,),
                      ingredients=(*catalog.ingredients, Ingredient('fixture-mate', 'fixture-address', 'mate',
                          metadata=next(p.metadata for p in catalog.ingredients if p.id == 'hungry'))))
    dictionary = replace(no_hunger_words, construction_catalog=catalog)
    tr = Translator(dictionary, lookup_embedder=None)
    schema = Draft202012Validator(json.loads(SCHEMA.read_text()))
    changed = False
    for seed in range(12):
        source = '🦘 She is hungry and he is hungry.'
        cs = translate_changes(source, translator=tr, level=5, vulgarity=0, seed=seed, embellishment=2,
             document_config={'garnish': [], 'contextual_riffs': False,
                              'profile': {'substitution': {'idiom': 1}, 'stack': 0}})
        schema.validate(cs.to_dict())
        validate_response(cs.to_dict(), source, dictionary, result_warnings=cs.result.warnings)
        for change in cs.changes:
            for owner in (change, *change['alternatives']):
                changed |= any('outta' in p['text'] for p in owner.get('parts', []))
                for part in owner.get('parts', []):
                    if part['role'] == 'address':
                        assert part['text'] == 'mate'
                    if part['role'] == 'act':
                        assert not part['text'].endswith(',')
    assert changed
