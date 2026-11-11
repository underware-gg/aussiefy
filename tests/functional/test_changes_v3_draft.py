"""Offline review artefacts; the active changes-v2 emitter remains unchanged."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from aussiefy.cards import full_entry_card
from aussiefy.changes import VERSION, SCHEMA
from aussiefy.match_keys import parse_match_key, known_match

ROOT=Path(__file__).resolve().parents[2]
DRAFT=ROOT/'docs/drafts/changes-v3'


@pytest.fixture(scope='module')
def bundle():
    return {name:json.loads((DRAFT/name).read_text()) for name in
            ['cards.schema.json','changes.schema.json','examples.json']}


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
    assert VERSION==2 and json.loads(SCHEMA.read_text())['properties']['version']=={'const':2}


def test_all_current_non_omitted_rich_entry_cards_fit_the_draft(bundle,translator):
    eff=translator.effective(level=5,vulgarity=3,registers=['current','dated','archaic'])
    v=validator(bundle['cards.schema.json'])
    for entry in translator.dictionary.entries.values():
        if entry.status=='omit': continue
        card=full_entry_card(entry,3,True,permitted_themes=eff.theme_policy,registers=eff.registers)
        v.validate(card)


def assert_graph(case,dictionary):
    body=case['response']
    assert len({c['id'] for c in body['changes']})==len(body['changes'])
    for eid,card in body['entries'].items(): assert card['id']==eid and card['status']!='omit'
    for cid,card in body['constructions'].items():
        assert card['construction_id']==cid
        for part in card['parts']:
            a,b=part['out_span']
            assert 0 <= a <= b <= len(card['text']) and card['text'][a:b]==part['text']
    for iid,card in body['imagery'].items(): assert card['id']==iid
    for change in body['changes']:
        a,b=change['src_span']
        assert 0 <= a <= b <= len(case['source']) and case['source'][a:b]==change['original']
        a,b=change['out_span']
        assert 0 <= a <= b <= len(body['text']) and body['text'][a:b]==change['output']
        if change['kind']=='substitution':
            match=change['match']
            parsed=parse_match_key(match['key'])
            assert parsed.to_dict()==match and known_match(match['key'],dictionary)
        if change['alternatives']: assert sum(o['weight'] for o in change['alternatives'])==pytest.approx(1)
        for owner in [change,*change['alternatives'],*change['locked']]:
            text=owner.get('rendered',owner.get('output'))
            start=owner['out_span'][0]
            if owner.get('entry_id'):
                assert owner['entry_id'] in body['entries']
                card=body['entries'][owner['entry_id']]
                assert owner['evidence']==card['evidence'] and owner['coined_by']==card.get('coined_by')
            if owner.get('image_id'):
                card=body['imagery'][owner['image_id']]
                assert owner['evidence']==card['evidence'] and owner['coined_by']==card.get('coined_by')
            for part in owner.get('parts',[]):
                canonical=next(p for p in body['constructions'][owner['construction_id']]['parts']
                               if p['role']==part['role'] and p['ingredient_id']==part['ingredient_id'])
                x,y=part['out_span']
                assert 0 <= x-start <= y-start <= len(text) and text[x-start:y-start]==part['text']
                assert part['evidence']==canonical['evidence'] and part['coined_by']==canonical.get('coined_by')
            for riff in owner.get('riffs',[]):
                x,y=riff['out_span']
                assert 0 <= x-start <= y-start <= len(text) and text[x-start:y-start]==riff['text']
                metadata=(body['entries'][riff['entry_id']]['riffs'][riff['riff_index']]
                          if riff['kind']=='entry_riff' else body['imagery'][riff['image_id']])
                assert riff['evidence']==metadata['evidence'] and riff['coined_by']==metadata.get('coined_by')


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
    with pytest.raises(AssertionError): assert_graph(case,dictionary)
