"""Rich cards and semantic checks shared by the archived v3 and draft v4 contracts."""

from .cards import (CARD_VERSION, metadata, provenance as provenance, entry_card as entry_card)
from .constructions import construction_identity
from .errors import SchemaError, warning_details
from .match_keys import known_match, parse_match_key


def construction_card(construction, dictionary, *, permitted_themes):
    c = construction
    return {'construction_id': c.id, 'entry_id': None, 'family': c.family.id, 'text': c.text,
            'gloss': dictionary.concepts[c.family.concept].description, 'concepts': [c.family.concept],
            'frame': c.family.frame, 'level': c.level, 'vulgarity': c.vulgarity, 'cadence': c.cadence,
            **metadata(c.metadata, permitted_themes, vulgarity=c.vulgarity),
            'parts': [{'role': p.role, 'ingredient_id': p.ingredient.id, 'entry_id': p.ingredient.entry_id,
                       'text': p.ingredient.text, 'out_span': list(p.span), 'level': p.ingredient.level,
                       'vulgarity': p.ingredient.vulgarity,
                       **metadata(p.ingredient.metadata, permitted_themes, vulgarity=p.ingredient.vulgarity)}
                      for p in c.parts]}


def imagery_card(image, *, permitted_themes):
    return {**{name: getattr(image, name) for name in
                ('id', 'text', 'usage', 'form', 'subject', 'exaggeration', 'level', 'vulgarity', 'tone')},
            **{name: list(getattr(image, name)) for name in ('concepts', 'frames', 'related', 'unless_after')},
            **metadata(image, permitted_themes)}


def card_envelope(dictionary):
    return {'card_version': CARD_VERSION, 'dictionary_id': dictionary.identity}


def response_metadata(result, dictionary=None):
    header = card_envelope(dictionary) if dictionary is not None else {
        'card_version': CARD_VERSION, 'dictionary_id': result.dictionary_id}
    return {**header, 'tuning': result.tuning, 'personal_terms': result.personal_terms, 'warnings': list(result.warnings),
            'warning_details': warning_details(result.warnings)}


def option_key(option):
    return option.get('key') or option.get('option_key') or (
        'entry:' + option['entry_id'] if option.get('entry_id') else
        'construction:' + option['construction_id'] if option.get('construction_id') else None)


def _require(condition, message):
    if not condition:
        raise SchemaError('changes: ' + message)


def _slice(text, span, expected, where):
    a, b = span
    _require(0 <= a <= b <= len(text) and text[a:b] == expected, where + ' span/text mismatch')


def _maker(value, where):
    if value['evidence'] == 'bulldust':
        _require(value.get('coined_by') in {'agent', 'person', 'constructor'}, where + ' bulldust needs a maker')


def _same_provenance(occurrence, card, where):
    _require(occurrence['evidence'] == card['evidence'] and occurrence['coined_by'] == card.get('coined_by'),
             where + ' provenance differs from its card')


def validate_response(body, source, dictionary, *, result_warnings):
    """Semantic checks after structural validation; no JSON Schema dependency or I/O."""
    _require(body['dictionary_id'] == dictionary.identity, 'dictionary_id differs from the loaded dictionary')
    version = body['version']
    _require(version in {3, 4} and body['card_version'] == version, 'card_version mismatch')
    _require(body['warnings'] == list(result_warnings), 'warnings differ from Result.warnings')
    _require(body['warning_details'] == warning_details(result_warnings), 'warning details differ from their messages')
    entries, constructions, imagery = (body[key] for key in ('entries', 'constructions', 'imagery'))
    _require(len({c['id'] for c in body['changes']}) == len(body['changes']), 'duplicate change id')
    for eid, card in entries.items():
        _require(card['id'] == eid and card['status'] != 'omit', 'entry map key/status mismatch')
        if version == 4:
            from .terms import headword_key
            _require(card['headword_key'] == headword_key(dictionary.entries[eid].form), 'headword_key differs from engine ordering')
        _maker(card, 'entry')
        for riff in card.get('riffs', []):
            _maker(riff, 'entry riff')
    catalog = dictionary.construction_catalog
    families = {f.id: f for f in catalog.families} if catalog else {}
    ingredients = {p.id: p for p in catalog.ingredients} if catalog else {}
    for cid, card in constructions.items():
        _require(card['construction_id'] == cid, 'construction map key mismatch')
        _require(card['family'] in families, 'unknown construction family')
        family = families[card['family']]
        keys = [(p['role'], p['ingredient_id']) for p in card['parts']]
        _require(len(set(keys)) == len(keys), 'duplicate canonical part join')
        roles = [p['role'] for p in card['parts']]
        _require(len(set(roles)) == len(roles) and set(roles) == {name for name, _ in family.slots},
                 'construction roles differ')
        chosen = {}
        for part in card['parts']:
            _require(part['ingredient_id'] in ingredients, 'unknown ingredient')
            ingredient = ingredients[part['ingredient_id']].resolve(dictionary.entries)
            _require(part['text'] == ingredient.text and part['entry_id'] == ingredient.entry_id, 'ingredient differs from dictionary')
            _require(ingredient.kind == dict(family.slots)[part['role']], 'ingredient kind differs from slot')
            chosen[part['role']] = ingredient
            _slice(card['text'], part['out_span'], part['text'], 'canonical part')
            _maker(part, 'canonical part')
        _require(construction_identity(family, chosen) == cid, 'construction identity is not persistent content identity')
        text = ''.join(literal + (chosen[name].text if name is not None else '') for literal, name in family.fragments)
        _require(text == card['text'], 'canonical construction text differs')
        _maker(card, 'construction')
    for iid, card in imagery.items():
        _require(card['id'] == iid, 'imagery map key mismatch')
        _maker(card, 'imagery')
    for change in body['changes']:
        _slice(source, change['src_span'], change['original'], 'source')
        _slice(body['text'], change['out_span'], change['output'], 'output')
        if change['kind'] == 'substitution':
            match = change['match']
            _require(parse_match_key(match['key']).to_dict() == match and known_match(match['key'], dictionary),
                     'source match is not canonical/known')
        if version == 4:
            _reading(change['reading'], dictionary)
            _reading(change.get('selected_reading'), dictionary)
            if change.get('selected_reading'):
                selected_concept = change['selected_reading']['concept']
                _require(change['reading'] is not None and selected_concept != change['reading']['concept']
                         and selected_concept in {row['concept'] for row in change['ruled_out']},
                         'selected reading is not an offered alternate interpretation')
                _require(change.get('entry_id') in dictionary.entries
                         and selected_concept in dictionary.entries[change['entry_id']].concept
                         and not change.get('near'), 'selected word does not express its explicit reading')
            ruled = change['ruled_out']
            _require(len({row['concept'] for row in ruled}) == len(ruled), 'duplicate ruled-out reading')
            for row in ruled:
                _reading({'concept': row['concept'], 'plain': row['plain']}, dictionary)
                _require(change['reading'] is None or row['concept'] != change['reading']['concept'],
                         'inferred reading also labelled ruled out')
            if change['kind'] in {'kept', 'held'}:
                _require(change['output'] == change['original'] and not change['masks'], 'owned source wording changed or masked')
            if change['kind'] == 'held':
                _require(change['reading'] is not None and change['reading']['concept'] in dictionary.wordless_meanings,
                         'held reading has an exact word or no meaning')
                _require(not change['alternatives'] and not change['locked'] and change['option_key'] is None,
                         'held source has replacement choices')
            if change['kind'] == 'personal':
                _require(change['entry_id'] is None and change['evidence'] is None and change['coined_by'] is None,
                         'personal wording pretends to be a dictionary entry')
        options = change['alternatives'] + change['locked']
        keys = [option_key(option) for option in options]
        _require(all(keys) and len(set(keys)) == len(keys), 'duplicate/missing option key across alternatives and locked')
        selected = option_key(change)
        if selected:
            _require(selected in {option_key(o) for o in change['alternatives']}, 'selected key absent from alternatives')
        if change['alternatives']:
            _require(abs(sum(o['weight'] for o in change['alternatives']) - 1) <= 0.001, 'alternative weights do not sum to 1')
        if change['kind'] == 'substitution':
            for option in options:
                _require(option['out_span'] == change['out_span'], 'option replacement region differs from change')
        words = [word for row in change.get('ruled_out', []) for word in row['words']]
        for owner in (change, *options, *words):
            if version == 4:
                if owner is not change:
                    kind = owner['kind']
                    key = owner['key']
                    _require(key.startswith(kind + ':'), 'option key has the wrong kind prefix')
                    if kind in {'entry', 'source'}:
                        _require(key == kind + ':' + owner['entry_id'], 'entry/source key differs from entry identity')
                    elif kind == 'construction':
                        _require(key == 'construction:' + owner['construction_id'], 'construction key differs from identity')
                    else:
                        _require(owner['entry_id'] is None and owner['evidence'] is None and owner['coined_by'] is None,
                                 'literal option pretends to be a dictionary entry')
                    if kind == 'plain':
                        _require(owner.get('weight', 0) == 0, 'plain choice has an automatic weight')
                    if kind == 'source':
                        _require(not owner['masks'] and owner['rendered'] == change['original']
                                 and owner['out_span'] == change['out_span'], 'source choice differs from owned marker')
                if owner.get('near'):
                    _near(owner['near'], change['reading'], owner, dictionary)

            _maker(owner, 'rendering')
            rendered = owner.get('rendered', owner.get('output'))
            if owner.get('entry_id'):
                _require(owner['entry_id'] in entries, 'missing entry card')
                _same_provenance(owner, entries[owner['entry_id']], 'entry rendering')
            if owner.get('image_id'):
                _require(owner['image_id'] in imagery, 'missing imagery card')
                _same_provenance(owner, imagery[owner['image_id']], 'imagery rendering')
            if owner.get('construction_id'):
                _require(owner['construction_id'] in constructions, 'missing construction card')
                _same_provenance(owner, constructions[owner['construction_id']], 'construction rendering')
            joins = set()
            for part in owner.get('parts', []):
                join = (part['role'], part['ingredient_id'])
                _require(join not in joins, 'duplicate occurrence part join')
                joins.add(join)
                matches = [p for p in constructions[owner['construction_id']]['parts']
                           if (p['role'], p['ingredient_id']) == join]
                _require(len(matches) == 1, 'part join does not identify exactly one canonical part')
                _require(part['entry_id'] == matches[0]['entry_id'], 'part entry_id differs from canonical part')
                _slice(rendered, part['out_span'], part['text'], 'part occurrence')
                _same_provenance(part, matches[0], 'part occurrence')
            if owner.get('construction_id'):
                canonical_joins = {(p['role'], p['ingredient_id']) for p in constructions[owner['construction_id']]['parts']}
                _require(joins == canonical_joins, 'occurrence parts differ from canonical parts')
            for riff in owner.get('riffs', []):
                _slice(rendered, riff['out_span'], riff['text'], 'riff occurrence')
                if riff['kind'] == 'entry_riff':
                    _require(riff['entry_id'] in entries, 'missing riff entry card')
                    riffs = entries[riff['entry_id']].get('riffs', [])
                    _require(riff['riff_index'] < len(riffs), 'riff index does not resolve')
                    card = riffs[riff['riff_index']]
                else:
                    _require(riff['image_id'] in imagery, 'missing riff imagery card')
                    card = imagery[riff['image_id']]
                _same_provenance(riff, card, 'riff occurrence')


def _reading(reading, dictionary):
    if reading is None:
        return
    concept = dictionary.concepts.get(reading['concept'])
    _require(concept is not None and concept.plain == reading['plain'], 'reading differs from authored meaning')


def _near(near, reading, owner, dictionary):
    _require(reading is not None and reading['concept'] in dictionary.wordless_meanings,
             'near rendering does not start from a waiting meaning')
    relation = next((item for item in dictionary.concepts[reading['concept']].near
                     if item.concept == near['concept'] and item.differs == near['differs']), None)
    _require(relation is not None, 'near citation is not an authored relation')
    if owner.get('entry_id'):
        _require(near['concept'] in dictionary.entries[owner['entry_id']].concept,
                 'near word does not express the cited target meaning')
