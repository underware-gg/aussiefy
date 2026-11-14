"""Immutable accepted r2 review artefacts; active emission is tested separately."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from aussiefy.v3_contract import entry_card, validate_response
from aussiefy.errors import SchemaError, WarningMessage, warning_details
from aussiefy.changes import VERSION, SCHEMA

ROOT=Path(__file__).resolve().parents[2]
DRAFT=ROOT/'docs/drafts/changes-v3'


@pytest.fixture(scope='module')
def bundle():
    return {name:json.loads((DRAFT/name).read_text()) for name in
            ['cards.schema.json','changes.schema.json','examples.json','lookup-cards.schema.json','lookup-examples.json']}


def validator(schema):
    return Draft202012Validator(schema,format_checker=FormatChecker())


def test_review_schemas_are_valid_local_and_share_the_same_card_definitions(bundle):
    cards,changes=(bundle[n] for n in ['cards.schema.json','changes.schema.json'])
    for schema in [cards,changes]:
        Draft202012Validator.check_schema(schema)
        assert 'REVIEW DRAFT' in schema['$comment']
        def refs(node):
            if isinstance(node,dict):
                if '$ref' in node: yield node['$ref']
                for child in node.values(): yield from refs(child)
            elif isinstance(node,list):
                for child in node: yield from refs(child)
        assert all(ref.startswith('#/$defs/') for ref in refs(schema))
    assert all(changes['$defs'][key]==value for key,value in cards['$defs'].items())
    assert changes['properties']['version'] == {'const': 3}
    assert VERSION == 4 and json.loads(SCHEMA.read_text())['properties']['version'] == {'const': 4}


def test_all_current_non_omitted_rich_entry_cards_fit_the_draft(bundle,translator):
    eff=translator.effective(level=5,vulgarity=3,registers=['current','dated','archaic'])
    v=validator(bundle['cards.schema.json'])
    for entry in translator.dictionary.entries.values():
        if entry.status=='omit': continue
        card=entry_card(entry,3,True,permitted_themes=eff.theme_policy,registers=eff.registers)
        card.pop('headword_key', None)
        card.pop('other_sense', None)
        v.validate(card)


def assert_graph(case,dictionary):
    warnings=[WarningMessage(d['message'],code=d['code']) for d in case['result_warning_details']]
    assert warnings==case['result_warnings']
    from dataclasses import replace
    archived = replace(dictionary, identity=case['response']['dictionary_id'])
    validate_response(case['response'],case['source'],archived,result_warnings=warnings)


def test_draft_examples_demonstrate_longer_alternatives_without_changing_the_replace_region(bundle):
    case=next(c for c in bundle['examples.json']['cases'] if c['name']=='construction-parts')
    change=case['response']['changes'][0]
    first,second=change['alternatives']
    assert len(first['rendered'])!=len(second['rendered'])
    assert first['out_span']==second['out_span']==change['out_span']
    assert any(part['out_span']!=other['out_span'] for part,other in zip(first['parts'],second['parts']))


@pytest.mark.parametrize('fault', ['missing_match','default_qualifier','unknown_qualifier','two_target_ids',
                                   'unlabelled_construction','missing_parts','negative_preference_count',
                                   'old_source_urls','omit_card','unsupported_kind'])
def test_draft_rejects_broken_contract_shapes(bundle,fault):
    cases=bundle['examples.json']['cases']
    body=deepcopy(cases[1 if fault in {'two_target_ids','unlabelled_construction','missing_parts'} else 0]['response'])
    change=body['changes'][0]
    if fault=='missing_match': del change['match']
    elif fault=='default_qualifier': change['match']['qualifiers']['degree']='unmarked'
    elif fault=='unknown_qualifier': change['match']['qualifiers']['tone']='solemn'
    elif fault=='two_target_ids': change['entry_id']='knackered'
    elif fault=='unlabelled_construction': change['evidence']='attested'
    elif fault=='missing_parts': del change['parts']
    elif fault=='negative_preference_count': body['tuning']['preferences']=-1
    elif fault=='old_source_urls': next(iter(body['entries'].values()))['sources']=['https://example.com/source']
    elif fault=='omit_card': next(iter(body['entries'].values()))['status']='omit'
    elif fault=='unsupported_kind': change['kind']='held'
    with pytest.raises(ValidationError): validator(bundle['changes.schema.json']).validate(body)



@pytest.mark.parametrize('index',range(6))
def test_review_examples_validate_and_preserve_graph_and_coordinate_invariants(bundle,dictionary,index):
    case=bundle['examples.json']['cases'][index]
    validator(bundle['changes.schema.json']).validate(case['response'])
    assert_graph(case,dictionary)


@pytest.mark.parametrize('fault', ['missing_card','wrong_root','part_bounds','riff_bounds','part_metadata','map_key'])
def test_graph_checks_reject_faults_json_schema_alone_cannot_express(bundle,dictionary,fault):
    index=1 if fault.startswith('part_') else 3 if fault=='riff_bounds' else 0
    case=deepcopy(bundle['examples.json']['cases'][index])
    body=case['response']
    change=body['changes'][0]
    if fault=='missing_card': body['entries'].clear()
    elif fault=='wrong_root': change['match']['root']=change['match']['root'].replace('HUNGRY','UNKNOWN')
    elif fault=='part_bounds': change['parts'][0]['out_span']=[0,1]
    elif fault=='riff_bounds': change['riffs'][0]['out_span']=[0,1]
    elif fault=='part_metadata': change['parts'][0]['coined_by']='person'
    elif fault=='map_key':
        key=next(iter(body['entries']))
        body['entries']['other-id']=body['entries'].pop(key)
    validator(bundle['changes.schema.json']).validate(body)
    with pytest.raises(SchemaError): assert_graph(case,dictionary)


@pytest.mark.parametrize('fault', ['alternative_duplicate', 'locked_duplicate', 'riff_duplicate',
                                   'selected_construction_absent', 'forged_construction_id',
                                   'duplicate_part_join', 'option_region', 'warnings_parity', 'warning_details'])
def test_r2_semantics_reject_ambiguous_keys_and_broken_joins(bundle,dictionary,fault):
    case=deepcopy(bundle['examples.json']['cases'][1 if fault in {
        'selected_construction_absent','forged_construction_id','duplicate_part_join'} else 3 if fault=='riff_duplicate' else 0])
    body=case['response']
    change=body['changes'][0]
    first=change['alternatives'][0]
    if fault in {'alternative_duplicate','riff_duplicate'}:
        copy=deepcopy(first)
        first['weight']/=2
        copy['weight']=first['weight']
        if fault=='riff_duplicate': copy['riffs']=[]  # Same entry with another riff is still the same option key.
        change['alternatives'].append(copy)
    elif fault=='locked_duplicate':
        copy=deepcopy(first)
        copy.pop('weight')
        copy['vulgarity']=max(1,copy['vulgarity'])
        change['locked'].append(copy)
    elif fault=='selected_construction_absent':
        change['alternatives']=change['alternatives'][1:]
        change['alternatives'][0]['weight']=1
    elif fault=='forged_construction_id':
        old=change['construction_id']
        new=old.rsplit('/',1)[0]+'/'+'0'*24
        card=body['constructions'].pop(old)
        card['construction_id']=new
        body['constructions'][new]=card
        for owner in [change,*change['alternatives']]:
            if owner['construction_id']==old: owner['construction_id']=new
    elif fault=='duplicate_part_join': change['parts'].append(deepcopy(change['parts'][0]))
    elif fault=='option_region': first['out_span']=[0,1]
    elif fault=='warnings_parity': body['warnings'].append('not a Result warning')
    elif fault=='warning_details': body['warning_details'][0]['code']='unknown_preference_term'
    validator(bundle['changes.schema.json']).validate(body)
    with pytest.raises(SchemaError): assert_graph(case,dictionary)


@pytest.mark.parametrize('missing',[False,True])
def test_every_bulldust_location_requires_a_non_null_maker(bundle,missing):
    def paths(value,path=()):
        if isinstance(value,dict):
            if value.get('evidence') in {'attested','unverified','bulldust'}: yield path
            for key,child in value.items(): yield from paths(child,(*path,key))
        elif isinstance(value,list):
            for index,child in enumerate(value): yield from paths(child,(*path,index))
    checked=set()
    for case in bundle['examples.json']['cases']:
        for path in paths(case['response']):
            body=deepcopy(case['response'])
            target=body
            for key in path: target=target[key]
            target['evidence']='bulldust'
            target['coined_by']=target.get('coined_by') or 'person'
            validator(bundle['changes.schema.json']).validate(body)
            if missing: target.pop('coined_by')
            else: target['coined_by']=None
            with pytest.raises(ValidationError): validator(bundle['changes.schema.json']).validate(body)
            checked.add(path[0])
    assert {'changes','entries','constructions','imagery'} <= checked


def test_bulldust_attribution_is_derived_without_rewriting_evidence(translator):
    from dataclasses import replace
    from aussiefy.evidence import TermMetadata, Search
    from aussiefy.v3_contract import metadata
    policy=translator.effective(level=5,vulgarity=3).theme_policy
    original=TermMetadata(evidence='bulldust',produced_by='agent',
                          searched=Search('2026-11-12','nothing_found'))
    assert metadata(original,policy)['coined_by']=='agent'
    assert original.coined_by is None and original.evidence=='bulldust'
    explicit=replace(original,coined_by='person')
    assert metadata(explicit,policy)['coined_by']=='person'
    recorded=replace(original,evidence='attested')
    assert 'coined_by' not in metadata(recorded,policy)
    with pytest.raises(SchemaError): metadata(replace(original,produced_by=None),policy)


def test_construction_ids_persist_across_sampling_order_and_reconstruction(bundle,dictionary,translator):
    from dataclasses import replace
    from aussiefy.constructions import compose, construction_identity, generate
    from aussiefy.genre import resolve_document
    eff=translator.effective(level=5,vulgarity=0)
    setting=resolve_document(None,config=dictionary.genres).setting(2)
    ingredients={p.id:p.resolve(dictionary.entries) for p in dictionary.construction_catalog.ingredients}
    families={f.id:f for f in dictionary.construction_catalog.families}
    stored=bundle['examples.json']['cases'][1]['response']['constructions']
    for cid,card in stored.items():
        family=families[card['family']]
        chosen={p['role']:ingredients[p['ingredient_id']] for p in reversed(card['parts'])}
        assert construction_identity(family,chosen)==cid
        assert compose(family,chosen,dictionary,eff).id==cid
        # Slot declaration order and weights are not content identity; rendering order is canonical.
        altered=replace(family,slots=tuple(reversed(family.slots)),weight=family.weight*2)
        assert construction_identity(altered,chosen)==cid
    sampled=[generate(dictionary,eff,setting,concept='HUNGRY',seed=n,limit=1).candidates[0] for n in range(8)]
    assert len({c.id for c in sampled})>1  # A persistent ID does not promise presence in an untuned result.
    for c in sampled:
        assert construction_identity(c.family,{p.role:p.ingredient for p in c.parts})==c.id


def test_local_occurrence_spans_survive_multiple_length_changing_swaps(bundle):
    # Apply two independent swaps, then re-offset document regions as a client does. Child spans never move.
    first=bundle['examples.json']['cases'][1]['response']['changes'][0]['alternatives'][1]
    second=bundle['examples.json']['cases'][3]['response']['changes'][0]
    source='😀 She is hungry; he is angry.'
    regions=[(source.index('hungry'),source.index('hungry')+len('hungry'),first['rendered'],first['parts']),
             (source.index('angry'),source.index('angry')+len('angry'),second['output'],second['riffs'])]
    pieces=[]
    last=0
    output_spans=[]
    for start,end,rendered,children in regions:
        pieces.append(source[last:start])
        offset=sum(map(len,pieces))
        pieces.append(rendered)
        output_spans.append((offset,offset+len(rendered)))
        for child in children: assert rendered[slice(*child['out_span'])]==child['text']
        last=end
    pieces.append(source[last:])
    output=''.join(pieces)
    for (_,_,rendered,children),(start,end) in zip(regions,output_spans):
        assert output[start:end]==rendered
        for child in children:
            a,b=child['out_span']
            assert output[start+a:start+b]==child['text']
    assert output_spans[1][0]!=regions[1][0]


@pytest.mark.parametrize('document',[False,True])
def test_coded_warning_projection_preserves_real_result_warnings(bundle,translator,document):
    from aussiefy.markdown import translate_document
    from aussiefy.policy import resolve
    from aussiefy.v3_contract import response_metadata
    key=bundle['examples.json']['cases'][0]['response']['changes'][0]['match']['key']
    tuning={'preferences':[{'match':key,'term':'missing','weight':2},
                           {'match':key.replace('HUNGRY','UNKNOWN'),'term':'peckish','weight':2}]}
    if document:
        pol=translator.policy(level=5,vulgarity=1,embellishment=0,embedder='none')
        result=translate_document('She is hungry.\n\nHe is hungry.',translator,pol,
                                  resolve(pol,translator.dictionary),_tuning=tuning)
    else:
        result=translator.translate('She is hungry.',level=5,vulgarity=1,embellishment=0,
                                    embedder='none',_tuning=tuning)
    projected=response_metadata(result,translator.dictionary)
    assert projected['warnings']==result.warnings
    assert [d['message'] for d in projected['warning_details']]==list(result.warnings)
    assert {'unknown_preference_term','unknown_preference_match'} <= {d['code'] for d in projected['warning_details']}
    assert all(isinstance(w,str) for w in result.warnings)
    assert json.loads(json.dumps(result.warnings))==list(result.warnings)
    assert warning_details(deepcopy(result.warnings))==projected['warning_details']


def test_lookup_projection_carries_version_even_without_results(bundle,dictionary):
    lookup_schema=bundle['lookup-cards.schema.json']
    Draft202012Validator.check_schema(lookup_schema)
    for case in bundle['lookup-examples.json']['cases']:
        body=case['response']
        validator(lookup_schema).validate(body)
        assert body['card_version']==3 and body['dictionary_id']==bundle['examples.json']['cases'][0]['response']['dictionary_id']
        broken=deepcopy(body)
        del broken['card_version']
        with pytest.raises(ValidationError): validator(lookup_schema).validate(broken)
    assert any(not case['response']['results'] for case in bundle['lookup-examples.json']['cases'])


def test_theme_shape_is_uniform_throughout_cards_and_projections(bundle):
    def walk(value):
        if isinstance(value,dict):
            if 'themes' in value:
                assert all(set(t)=={'name','tier'} and isinstance(t['name'],str) and type(t['tier']) is int
                           for t in value['themes'])
                assert 'minimum_vulgarity' in value
            for child in value.values(): walk(child)
        elif isinstance(value,list):
            for child in value: walk(child)
    walk(bundle['examples.json']['cases'])
    walk(bundle['lookup-examples.json']['cases'])



def test_all_imagery_and_sampled_construction_families_use_the_shared_card_contract(bundle,translator):
    from aussiefy.constructions import generate
    from aussiefy.genre import resolve_document
    from aussiefy.v3_contract import construction_card, imagery_card
    d=translator.dictionary
    eff=translator.effective(level=5,vulgarity=3,registers=['current','dated','archaic'])
    schema=bundle['cards.schema.json']
    def card_validator(name):
        return validator({**schema,'$ref':'#/$defs/'+name})
    for image in d.imagery:
        card=imagery_card(image,permitted_themes=eff.theme_policy)
        card_validator('imagery_card').validate(card)
    setting=resolve_document(None,config=d.genres).setting(2)
    for family in d.construction_catalog.families:
        candidates=generate(d,eff,setting,family=family.id,limit=20).candidates
        assert candidates
        for construction in candidates:
            card=construction_card(construction,d,permitted_themes=eff.theme_policy)
            card_validator('construction_card').validate(card)
            assert card['gloss']==d.concepts[family.concept].description
