"""Regenerate the coordinated v4 freeze bundle from real engine calls; review its diff."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

from jsonschema import Draft202012Validator
from aussiefy import Translator, list_concepts, list_entries, lookup, suggest_selection
from regen_changes_fixtures import CASES, build
from aussiefy.v3_contract import validate_response

SCHEMAS = ('changes', 'cards', 'lookup-cards', 'selection', 'discovery', 'personal-terms')
OUTPUT = ROOT / 'docs/contracts/v4'


def generate(output=OUTPUT):
    output.mkdir(parents=True, exist_ok=True)
    tr = Translator(lookup_embedder=None)
    def write(name, body):
        (output / name).write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n')
    schemas = {}
    for name in SCHEMAS:
        name += '.schema.json'
        shutil.copyfile(ROOT / 'aussiefy/data' / name, output / name)
        schemas[name] = json.loads((output / name).read_text())
        Draft202012Validator.check_schema(schemas[name])
    examples = []
    for name in CASES:
        fixture = build(name, tr)
        Draft202012Validator(schemas['changes.schema.json']).validate(fixture['response'])
        validate_response(fixture['response'], fixture['request']['text'], tr.dictionary,
                          result_warnings=fixture['response']['warnings'])
        examples.append({'name': name, **fixture})
    write('examples.json', {'examples': examples})
    base = {'level': 5, 'vulgarity': 0, 'embellishment': 0, 'embedder': 'none'}
    selections = []
    for source, span, options in [
        ('She is exhausted.', [8, 12], {'level': 1}),
        ("He's a bludger.", [7, 10], {}),
        ('A spreadsheet.', [4, 8], {'personal_terms': [{'phrase': 'spreadsheet', 'term': 'number wrangler'}]}),
        ('She wept.', [5, 7], {}), ('American football game', [0, 8], {}),
        ('🦘 A **spreadsheet**. `spreadsheet`', [9, 13], {'markdown': True,
            'personal_terms': [{'phrase': 'spreadsheet', 'term': 'number wrangler'}]}),
        ('She is exhausted and he is hungry.', [0, 31], {'level': 1}),
    ]:
        request = {'text': source, 'span': span, **base, **options}
        body = suggest_selection(translator=tr, **request)
        Draft202012Validator(schemas['selection.schema.json']).validate(body)
        selections.append({'request': request, 'response': body})
    write('selection-examples.json', {'examples': selections})
    discovery = {'concepts': list_concepts(limit=10, translator=tr),
                 'entries': list_entries(concept='TIRED', limit=10, translator=tr)}
    for body in discovery.values():
        Draft202012Validator(schemas['discovery.schema.json']).validate(body)
    write('discovery-examples.json', discovery)
    lookups = []
    for query in ('knackered', 'weep', 'wholeheartedly', 'American football', 'American football game'):
        request = {'query': query, 'level': 5, 'vulgarity': 0, 'embellishment': 0}
        body = lookup(translator=tr, **request)
        Draft202012Validator(schemas['lookup-cards.schema.json']).validate(body)
        lookups.append({'request': request, 'response': body})
    write('lookup-examples.json', {'examples': lookups})
    (output / 'README.md').write_text("""# Frozen Aussiefy v4 contract — 15 November 2026

Site-reviewed v4, with six packaged schemas and real emitter fixtures. This is a contract freeze on
dev, not a package release or deployment. The checkpoint report in the Brain gives its pushed commit
and full gate receipts. manifest.json records exact bytes and SHA-256 for every bundle file.

Each selection group has outcome and locked; outside_dials distinguishes unavailable words from a
waiting meaning. Near citations carry concept, plain and differs. All option regions are in actual
output; child masks, parts and riffs are local to their own rendering. Source duplicates are omitted.
Entry/construction keys are exactly the kind prefix plus their ID. Null substitution targets replay
plain:source literally. Other kept English choices need future pin coordination; personal choices
remain unshared. The host can raise or remove its personal hook cap; direct lists remain bounded.

Concept plain is final reader-facing en-AU wording; list_entries(concept=...) intersects the other
filters. other_sense is curator metadata, not reader copy. headword_key drops a leading article and a
terminal full stop, preserving internal punctuation/hyphens. No form or permanent ID was renamed.

Regenerate with scripts/regen_v4_contract.py and review the diff. Earlier draft bundles are historical
and remain untouched. These fixtures reflect the dictionary at the freeze; later curation may change
its dictionary_id without changing this frozen schema.
""")
    write('manifest.json', {p.name: {'bytes': p.stat().st_size,
                                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in sorted(output.iterdir()) if p.name != 'manifest.json'})
    return {'dictionary_id': tr.dictionary.identity, 'changes': len(examples),
            'selections': len(selections), 'lookups': len(lookups)}


if __name__ == '__main__':
    print(json.dumps(generate()))
